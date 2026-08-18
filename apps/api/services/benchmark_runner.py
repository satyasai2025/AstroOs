"""
AstroOS — Benchmark Runner & Profile Comparison Engine

Orchestrates multi-profile benchmark comparisons on locked dataset splits:
  1. Partitions locked benchmark corpus ONCE using a fixed seed (e.g. 70/30)
  2. Ensures every evaluated profile receives the EXACT same train and holdout IDs
  3. Fits calibration curves strictly on Train split per profile
  4. Evaluates discrimination, calibration, and timing metrics strictly on Holdout split
  5. Computes delta improvements against baseline predictive profile
"""

from __future__ import annotations

import math
import statistics
import uuid
from datetime import datetime
from typing import Optional, Sequence

from apps.api.domain.benchmark_dataset import (
    BenchmarkComparisonReport,
    BenchmarkProfileComparisonRow,
    LockedBenchmarkCorpus,
)
from apps.api.domain.benchmark_experiment import (
    BaselineComparison,
    BenchmarkExperiment,
    ExperimentProvenance,
    LockedDatasetSplit,
)
from apps.api.domain.prediction_orchestration import ConsensusProfile
from apps.api.domain.research_calibration import (
    BenchmarkDataset,
    TemporalMatchStatus,
)
from apps.api.domain.statistical_testing import ProfileSignificanceReport
from apps.api.services.calibration_engine import CalibrationEngine
from apps.api.services.research_engine import ResearchEngine
from apps.api.services.significance_engine import SignificanceEngine


class BenchmarkRunner:
    """Orchestrates multi-profile evaluation against locked benchmark corpora."""

    def __init__(
        self,
        research_engine: Optional[ResearchEngine] = None,
        calibration_engine: Optional[CalibrationEngine] = None,
        significance_engine: Optional[SignificanceEngine] = None,
    ) -> None:
        self._research = research_engine or ResearchEngine()
        self._calibration = calibration_engine or CalibrationEngine()
        self._significance = significance_engine or SignificanceEngine(calibration_engine=self._calibration)

    def compare_profiles(
        self,
        corpus: LockedBenchmarkCorpus,
        profiles: Sequence[ConsensusProfile],
        tolerance_days: int = 30,
        seed: int = 42,
        train_ratio: float = 0.70,
    ) -> BenchmarkComparisonReport:
        """
        Executes an apples-to-apples comparison of multiple predictive profiles
        across a locked benchmark dataset with strictly identical train/holdout splits.
        """
        benchmark_dataset = BenchmarkDataset(
            dataset_id=corpus.benchmark_id,
            name=corpus.definition.name,
            event_type=corpus.event_type,
            version=corpus.version,
            description=corpus.definition.description,
            events=corpus.events,
        )

        # 1. Single Locked Split (Identical events for all profiles)
        split = self._research.split_dataset(benchmark_dataset, train_ratio=train_ratio, seed=seed)
        train_events = split.train_events
        holdout_events = split.holdout_events
        n_holdout = len(holdout_events)

        rows: list[BenchmarkProfileComparisonRow] = []

        for prof in profiles:
            # 2. Backtest & Calibrate strictly on TRAIN
            train_outcomes = self._research.run_backtest(train_events, profile=prof, tolerance_days=tolerance_days)
            calib_model = self._calibration.fit_isotonic_calibration(
                train_outcomes=train_outcomes,
                dataset_id=corpus.benchmark_id,
                dataset_version=corpus.version,
                event_type=corpus.event_type,
                profile_id=prof.profile_id,
                split_seed=seed,
                split_train_ratio=train_ratio,
                tolerance_days=tolerance_days,
            )

            # 3. Evaluate strictly on HOLDOUT
            holdout_outcomes = self._research.run_backtest(holdout_events, profile=prof, tolerance_days=tolerance_days)

            tp = sum(
                1 for o in holdout_outcomes
                if o.match_status in (TemporalMatchStatus.WINDOW_EXACT_HIT, TemporalMatchStatus.WINDOW_TOLERANCE_HIT)
            )
            fp = sum(
                1 for o in holdout_outcomes
                if o.match_status == TemporalMatchStatus.TEMPORAL_MISS and o.predicted_window_start is not None
            )
            fn = sum(
                1 for o in holdout_outcomes
                if o.match_status == TemporalMatchStatus.TEMPORAL_MISS and o.predicted_window_start is None
            )

            precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
            recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
            f1 = round((2 * precision * recall) / (precision + recall), 4) if (precision + recall) > 0 else 0.0
            hit_rate_pct = round((tp / n_holdout) * 100.0, 1) if n_holdout > 0 else 0.0

            # 4. Holdout-only Brier score
            brier_sum = 0.0
            for o in holdout_outcomes:
                p_cal = self._calibration.predict_probability_for_score(o.deterministic_score, calib_model)
                y_act = 1.0 if o.match_status in (TemporalMatchStatus.WINDOW_EXACT_HIT, TemporalMatchStatus.WINDOW_TOLERANCE_HIT) else 0.0
                brier_sum += (p_cal - y_act) ** 2

            holdout_brier = round(brier_sum / n_holdout, 4) if n_holdout > 0 else 0.0

            # 5. Timing Error Metrics on Holdout candidate predictions
            offsets = [abs(o.peak_offset_days) for o in holdout_outcomes if o.peak_offset_days is not None]
            if offsets:
                mae = round(statistics.mean(offsets), 1)
                med = round(float(statistics.median(offsets)), 1)
                sorted_off = sorted(offsets)
                p90_idx = int(math.ceil(0.90 * len(sorted_off))) - 1
                p90 = float(sorted_off[min(p90_idx, len(sorted_off) - 1)])
            else:
                mae, med, p90 = 0.0, 0.0, 0.0

            rows.append(
                BenchmarkProfileComparisonRow(
                    profile_id=prof.profile_id,
                    profile_name=prof.name,
                    calibration_sample_size_n=len(train_events),
                    holdout_sample_size_n=n_holdout,
                    holdout_precision=precision,
                    holdout_recall=recall,
                    holdout_f1_score=f1,
                    holdout_hit_rate_pct=hit_rate_pct,
                    holdout_brier_score=holdout_brier,
                    holdout_mae_peak_days=mae,
                    holdout_median_peak_offset_days=med,
                    holdout_p90_peak_offset_days=p90,
                    calibration_method="isotonic_regression",
                )
            )

        return BenchmarkComparisonReport(
            benchmark_id=corpus.benchmark_id,
            benchmark_version=corpus.version,
            content_hash_sha256=corpus.content_hash_sha256,
            split_seed=seed,
            split_train_ratio=train_ratio,
            tolerance_days=tolerance_days,
            total_benchmark_events=len(corpus.events),
            train_events_count=len(train_events),
            holdout_events_count=n_holdout,
            rows=tuple(rows),
        )

    def run_experiment(
        self,
        corpus: LockedBenchmarkCorpus,
        profiles: Sequence[ConsensusProfile],
        baseline_profile_id: str = "parashari_standard_v1",
        tolerance_days: int = 30,
        seed: int = 42,
        train_ratio: float = 0.70,
    ) -> BenchmarkExperiment:
        """Runs a complete reproducible benchmark experiment with baseline comparison."""
        report = self.compare_profiles(
            corpus=corpus,
            profiles=profiles,
            tolerance_days=tolerance_days,
            seed=seed,
            train_ratio=train_ratio,
        )

        benchmark_dataset = BenchmarkDataset(
            dataset_id=corpus.benchmark_id,
            name=corpus.definition.name,
            event_type=corpus.event_type,
            version=corpus.version,
            description=corpus.definition.description,
            events=corpus.events,
        )
        split = self._research.split_dataset(benchmark_dataset, train_ratio=train_ratio, seed=seed)

        locked_split = LockedDatasetSplit(
            benchmark_id=corpus.benchmark_id,
            version=corpus.version,
            content_hash_sha256=corpus.content_hash_sha256,
            split_seed=seed,
            train_ratio=train_ratio,
            train_event_ids=tuple(e.event_id for e in split.train_events),
            holdout_event_ids=tuple(e.event_id for e in split.holdout_events),
        )

        results_hash = BenchmarkExperiment.compute_results_hash(report)
        exp_id = f"EXP-{corpus.benchmark_id}-{seed}-{results_hash[:8]}"

        provenance = ExperimentProvenance(
            experiment_id=exp_id,
            benchmark_id=corpus.benchmark_id,
            benchmark_version=corpus.version,
            content_hash_sha256=corpus.content_hash_sha256,
            split_seed=seed,
            train_ratio=train_ratio,
            tolerance_days=tolerance_days,
            profile_ids=tuple(p.profile_id for p in profiles),
            calibration_method="isotonic_regression",
            software_version="2.0.0",
            timestamp=datetime.now(),
            results_hash=results_hash,
        )

        # Baseline comparison & statistical significance testing
        baseline_profile = next((p for p in profiles if p.profile_id == baseline_profile_id), profiles[0])
        baseline_row = next((r for r in report.rows if r.profile_id == baseline_profile_id), None)

        train_events = split.train_events
        holdout_events = split.holdout_events

        # Precompute baseline outcomes and calibration model
        base_train_outcomes = self._research.run_backtest(train_events, profile=baseline_profile, tolerance_days=tolerance_days)
        base_calib_model = self._calibration.fit_isotonic_calibration(
            train_outcomes=base_train_outcomes,
            dataset_id=corpus.benchmark_id,
            dataset_version=corpus.version,
            event_type=corpus.event_type,
            profile_id=baseline_profile.profile_id,
            split_seed=seed,
            split_train_ratio=train_ratio,
            tolerance_days=tolerance_days,
        )
        base_holdout_outcomes = self._research.run_backtest(holdout_events, profile=baseline_profile, tolerance_days=tolerance_days)

        comparisons: list[BaselineComparison] = []
        significance_reports: list[ProfileSignificanceReport] = []

        for p in profiles:
            if p.profile_id == baseline_profile.profile_id:
                continue

            cand_train_outcomes = self._research.run_backtest(train_events, profile=p, tolerance_days=tolerance_days)
            cand_calib_model = self._calibration.fit_isotonic_calibration(
                train_outcomes=cand_train_outcomes,
                dataset_id=corpus.benchmark_id,
                dataset_version=corpus.version,
                event_type=corpus.event_type,
                profile_id=p.profile_id,
                split_seed=seed,
                split_train_ratio=train_ratio,
                tolerance_days=tolerance_days,
            )
            cand_holdout_outcomes = self._research.run_backtest(holdout_events, profile=p, tolerance_days=tolerance_days)

            sig_report = self._significance.evaluate_profile_significance(
                candidate_profile_id=p.profile_id,
                baseline_profile_id=baseline_profile.profile_id,
                candidate_outcomes=cand_holdout_outcomes,
                baseline_outcomes=base_holdout_outcomes,
                candidate_model=cand_calib_model,
                baseline_model=base_calib_model,
                n_bootstraps=1000,
                seed=seed,
            )
            significance_reports.append(sig_report)

            superior = sig_report.verdict == "STATISTICALLY_SIGNIFICANT_SUPERIOR" or (
                sig_report.delta_hit_rate_pct > 0 and sig_report.delta_brier_score <= 0
            )

            comparisons.append(
                BaselineComparison(
                    profile_id=p.profile_id,
                    baseline_profile_id=baseline_profile.profile_id,
                    delta_hit_rate_pct=sig_report.delta_hit_rate_pct,
                    delta_brier_score=sig_report.delta_brier_score,
                    delta_f1_score=round(
                        (next(r.holdout_f1_score for r in report.rows if r.profile_id == p.profile_id) - (baseline_row.holdout_f1_score if baseline_row else 0.0)),
                        4
                    ),
                    delta_mae_peak_days=sig_report.delta_mae_peak_days,
                    is_statistically_superior=superior,
                    p_value=sig_report.mcnemar_test.p_value,
                    odds_ratio=sig_report.mcnemar_test.odds_ratio,
                    verdict=sig_report.verdict,
                )
            )

        return BenchmarkExperiment(
            provenance=provenance,
            split=locked_split,
            report=report,
            baseline_comparisons=tuple(comparisons),
            significance_reports=tuple(significance_reports),
        )