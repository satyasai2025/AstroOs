"""
AstroOS — Benchmark Intelligence & Descriptive Trend Analytics Service

Computes observational longitudinal performance trajectories, composite stability indices,
profile summary statistics, and corpus demographic distributions.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Optional

from apps.api.domain.benchmark_intelligence import (
    BenchmarkIntelligenceReport,
    CorpusEvolutionSummary,
    PerformanceTrendPoint,
    ProfileEvolutionSummary,
    StabilityIndexBreakdown,
)
from apps.api.repositories.benchmark_experiment_repository import BenchmarkExperimentRepository
from apps.api.repositories.continuous_monitoring_repository import ContinuousMonitoringRepository
from apps.api.repositories.production_governance_repository import ProductionGovernanceRepository
from apps.api.services.benchmark_corpus_loader import BenchmarkCorpusLoader
from apps.api.services.benchmark_registry import BenchmarkRegistry
from apps.api.services.benchmark_runner import BenchmarkRunner


class IntelligenceAnalyticsService:
    """Service providing observational trend analytics and stability reporting."""

    def __init__(
        self,
        experiment_repo: Optional[BenchmarkExperimentRepository] = None,
        governance_repo: Optional[ProductionGovernanceRepository] = None,
        monitoring_repo: Optional[ContinuousMonitoringRepository] = None,
        registry: Optional[BenchmarkRegistry] = None,
        runner: Optional[BenchmarkRunner] = None,
    ) -> None:
        self._exp_repo = experiment_repo or BenchmarkExperimentRepository()
        self._gov_repo = governance_repo or ProductionGovernanceRepository()
        self._mon_repo = monitoring_repo or ContinuousMonitoringRepository()
        self._registry = registry or BenchmarkRegistry()
        self._runner = runner or BenchmarkRunner()
        self._corpus_loader = BenchmarkCorpusLoader(registry=self._registry)

    @staticmethod
    def calculate_stability_index(
        hit_rates: list[float],
        brier_scores: list[float],
        regression_flags: list[bool],
    ) -> StabilityIndexBreakdown:
        """
        Computes the mathematical System Stability Index in [0.0, 1.0] using the formula:
          Stability Index = 0.40 * S_hit + 0.30 * S_brier + 0.30 * S_clean
        where:
          S_hit   = max(0.0, 1.0 - std_hit / 15.0)
          S_brier = max(0.0, 1.0 - std_brier / 0.08)
          S_clean = regression_free_runs / total_runs
        """
        n = len(hit_rates)
        if n == 0:
            return StabilityIndexBreakdown(
                hit_rate_stability_component=1.0,
                brier_stability_component=1.0,
                regression_free_component=1.0,
                composite_stability_index=1.0,
                total_runs_evaluated=0,
                std_hit_rate=0.0,
                std_brier=0.0,
                regression_free_runs_ratio=1.0,
            )

        if n == 1:
            r_clean = 0.0 if (regression_flags and regression_flags[0]) else 1.0
            comp = round(0.40 * 1.0 + 0.30 * 1.0 + 0.30 * r_clean, 3)
            return StabilityIndexBreakdown(
                hit_rate_stability_component=1.0,
                brier_stability_component=1.0,
                regression_free_component=r_clean,
                composite_stability_index=comp,
                total_runs_evaluated=1,
                std_hit_rate=0.0,
                std_brier=0.0,
                regression_free_runs_ratio=r_clean,
            )

        # Sample standard deviations
        mean_hit = sum(hit_rates) / n
        var_hit = sum((x - mean_hit) ** 2 for x in hit_rates) / (n - 1)
        std_hit = round(math.sqrt(var_hit), 2)

        mean_brier = sum(brier_scores) / n
        var_brier = sum((y - mean_brier) ** 2 for y in brier_scores) / (n - 1)
        std_brier = round(math.sqrt(var_brier), 4)

        clean_count = sum(1 for reg in regression_flags if not reg)
        r_clean = round(clean_count / n, 3)

        s_hit = max(0.0, min(1.0, round(1.0 - (std_hit / 15.0), 3)))
        s_brier = max(0.0, min(1.0, round(1.0 - (std_brier / 0.08), 3)))
        s_clean = r_clean

        composite = max(0.0, min(1.0, round(0.40 * s_hit + 0.30 * s_brier + 0.30 * s_clean, 3)))

        return StabilityIndexBreakdown(
            hit_rate_stability_component=s_hit,
            brier_stability_component=s_brier,
            regression_free_component=s_clean,
            composite_stability_index=composite,
            total_runs_evaluated=n,
            std_hit_rate=std_hit,
            std_brier=std_brier,
            regression_free_runs_ratio=r_clean,
        )

    async def generate_intelligence_report(self, benchmark_id: str) -> BenchmarkIntelligenceReport:
        """Generates a comprehensive descriptive intelligence report for a benchmark."""
        # Ensure canonical corpus is loaded
        corpus = self._registry.get_locked_corpus(benchmark_id, "1.0.0")
        if not corpus:
            self._corpus_loader.load_and_lock_all_canonical_corpora()
            corpus = self._registry.get_locked_corpus(benchmark_id, "1.0.0")
            if not corpus:
                raise ValueError(f"Corpus '{benchmark_id}' not found.")

        # Active baseline
        active_base = await self._gov_repo.get_active_baseline_profile(benchmark_id)
        base_id = active_base.profile_id if active_base else "parashari_standard_v1"

        # Load historical experiments
        exp_models = await self._exp_repo.list_by_benchmark_id(benchmark_id, limit=50)

        # Build longitudinal profile trajectories
        profile_trajectories: dict[str, list[PerformanceTrendPoint]] = {}
        profile_names: dict[str, str] = {}

        hit_rates_baseline: list[float] = []
        brier_scores_baseline: list[float] = []
        regression_flags: list[bool] = []

        for m in reversed(exp_models):  # Chronological order
            summary = m.results_summary or {}
            rows = summary.get("rows", [])
            base_comps = m.baseline_comparisons or []
            sig_reports = summary.get("significance_reports", [])

            for r in rows:
                p_id = r.get("profile_id", "")
                p_name = r.get("profile_name", p_id)
                profile_names[p_id] = p_name

                # Look up delta and significance
                b_comp = next((b for b in base_comps if b.get("profile_id") == p_id), {})
                sig = next((s for s in sig_reports if s.get("profile_id") == p_id), {})

                pt = PerformanceTrendPoint(
                    experiment_id=m.experiment_id,
                    timestamp=m.completed_at or datetime.now(timezone.utc),
                    profile_id=p_id,
                    profile_name=p_name,
                    tolerance_days=m.tolerance_days,
                    split_seed=m.split_seed,
                    holdout_sample_size_n=r.get("holdout_sample_size_n", 0),
                    holdout_hit_rate_pct=r.get("holdout_hit_rate_pct", 0.0),
                    holdout_brier_score=r.get("holdout_brier_score", 0.0),
                    holdout_mae_days=r.get("holdout_mae_peak_days", 0.0),
                    holdout_f1_score=r.get("holdout_f1_score", 0.0),
                    delta_hit_rate_pct=b_comp.get("delta_hit_rate_pct", 0.0),
                    delta_brier_score=b_comp.get("delta_brier_score", 0.0),
                    p_value=b_comp.get("p_value") or (sig.get("mcnemar_test", {}).get("p_value")),
                    verdict=b_comp.get("verdict") or sig.get("verdict"),
                )

                if p_id not in profile_trajectories:
                    profile_trajectories[p_id] = []
                profile_trajectories[p_id].append(pt)

                if p_id == base_id or (not hit_rates_baseline and p_id == rows[0].get("profile_id")):
                    hit_rates_baseline.append(r.get("holdout_hit_rate_pct", 0.0))
                    brier_scores_baseline.append(r.get("holdout_brier_score", 0.0))

            # Check if this run had regressions flagged
            has_reg = any(b.get("delta_hit_rate_pct", 0.0) < -3.0 or b.get("delta_brier_score", 0.0) > 0.02 for b in base_comps)
            regression_flags.append(has_reg)

        # Compute ProfileEvolutionSummary per profile
        summaries: dict[str, ProfileEvolutionSummary] = {}
        for p_id, pts in profile_trajectories.items():
            n_eval = len(pts)
            hits = [p.holdout_hit_rate_pct for p in pts]
            briers = [p.holdout_brier_score for p in pts]
            maes = [p.holdout_mae_days for p in pts]
            f1s = [p.holdout_f1_score for p in pts]

            m_hit = round(sum(hits) / n_eval, 1)
            m_brier = round(sum(briers) / n_eval, 4)
            m_mae = round(sum(maes) / n_eval, 1)
            m_f1 = round(sum(f1s) / n_eval, 3)

            std_h = round(math.sqrt(sum((x - m_hit) ** 2 for x in hits) / (n_eval - 1)), 2) if n_eval > 1 else 0.0
            std_b = round(math.sqrt(sum((y - m_brier) ** 2 for y in briers) / (n_eval - 1)), 4) if n_eval > 1 else 0.0

            summaries[p_id] = ProfileEvolutionSummary(
                profile_id=p_id,
                profile_name=profile_names.get(p_id, p_id),
                total_evaluations=n_eval,
                mean_hit_rate_pct=m_hit,
                mean_brier_score=m_brier,
                mean_mae_days=m_mae,
                mean_f1_score=m_f1,
                std_hit_rate_pct=std_h,
                std_brier_score=std_b,
                min_hit_rate_pct=min(hits),
                max_hit_rate_pct=max(hits),
                min_brier_score=min(briers),
                max_brier_score=max(briers),
                trajectory=tuple(pts),
            )

        # Calculate composite stability index
        stability_breakdown = self.calculate_stability_index(
            hit_rates=hit_rates_baseline,
            brier_scores=brier_scores_baseline,
            regression_flags=regression_flags,
        )

        # Corpus demographics
        birth_conf_dist: dict[str, int] = {}
        verif_dist: dict[str, int] = {}
        date_conf_dist: dict[str, int] = {}

        for ev in corpus.events:
            b_conf = ev.birth_confidence.value if hasattr(ev.birth_confidence, "value") else str(ev.birth_confidence)
            birth_conf_dist[b_conf] = birth_conf_dist.get(b_conf, 0) + 1

            v_type = ev.event_verification.value if hasattr(ev.event_verification, "value") else str(ev.event_verification)
            verif_dist[v_type] = verif_dist.get(v_type, 0) + 1

            d_conf = ev.event_date_confidence.value if hasattr(ev.event_date_confidence, "value") else str(ev.event_date_confidence)
            date_conf_dist[d_conf] = date_conf_dist.get(d_conf, 0) + 1

        corpus_demographics = CorpusEvolutionSummary(
            benchmark_id=corpus.benchmark_id,
            current_version=corpus.version,
            total_verified_events=len(corpus.events),
            content_hash_sha256=corpus.content_hash_sha256,
            birth_confidence_distribution=birth_conf_dist,
            event_verification_distribution=verif_dist,
            date_confidence_distribution=date_conf_dist,
        )

        # Alerts summary
        alerts = await self._mon_repo.list_alerts(benchmark_id=benchmark_id)
        alert_freq: dict[str, int] = {}
        for a in alerts:
            sev = a.severity.value if hasattr(a.severity, "value") else str(a.severity)
            alert_freq[sev] = alert_freq.get(sev, 0) + 1

        return BenchmarkIntelligenceReport(
            benchmark_id=benchmark_id,
            active_baseline_profile_id=base_id,
            total_experiments=len(exp_models),
            stability=stability_breakdown,
            profile_summaries=summaries,
            corpus_demographics=corpus_demographics,
            alert_frequency_summary=alert_freq,
        )