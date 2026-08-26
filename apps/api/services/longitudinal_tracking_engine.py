"""
AstroOS — Longitudinal Outcome Tracking Service Engine (Priority 27)

Orchestrates continuous real-world prospective observation recording,
chronological time-series evaluation, and dual-mechanism drift diagnosis:
  1. Population Distribution Drift via Population Stability Index (PSI).
  2. Formal Statistical Degradation Testing (Two-proportion Z-test / p-value).
  3. Dynamic upstream ingestion from P20, P25, P26, and P11 lineage.
"""

from __future__ import annotations

import hashlib
import json
import math
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from apps.api.domain.longitudinal_tracking import (
    LongitudinalTimeSeriesInterval,
    LongitudinalTrackingReport,
    OutcomeVerificationStatus,
    PopulationDistributionDriftStatus,
    StatisticalDegradationTest,
    TrackedSubjectOutcomeRecord,
)
from apps.api.domain.prospective_validation import ProspectiveRuleLifecycleStatus
from apps.api.services.experiment_service import ExperimentRegistry
from apps.api.services.portfolio_planner_engine import ResearchPortfolioPlannerEngine
from apps.api.services.prospective_validation_engine import ProspectiveValidationEngine


class LongitudinalTrackingEngine:
    """
    Tracks and analyzes continuous real-world prospective event occurrences.
    """

    _instance: Optional[LongitudinalTrackingEngine] = None

    def __init__(
        self,
        prospective_engine: Optional[ProspectiveValidationEngine] = None,
        planner_engine: Optional[ResearchPortfolioPlannerEngine] = None,
        experiment_registry: Optional[ExperimentRegistry] = None,
    ) -> None:
        self._prospective_engine = prospective_engine or ProspectiveValidationEngine.get_instance()
        self._planner_engine = planner_engine or ResearchPortfolioPlannerEngine.get_instance()
        self._experiment_registry = experiment_registry or ExperimentRegistry.get_instance()
        self._tracked_records: Dict[str, List[TrackedSubjectOutcomeRecord]] = {}
        self._reports: Dict[str, LongitudinalTrackingReport] = {}

    @classmethod
    def get_instance(cls) -> LongitudinalTrackingEngine:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def record_subject_outcome(
        self,
        subject_id: str,
        target_objective: str,
        rule_id: str,
        predicted_window_start: date,
        predicted_window_end: date,
        actual_event_date: Optional[date],
        predicted_probability: float,
        verification_status: OutcomeVerificationStatus,
        verification_source: str = "OFFICIAL_MUNICIPAL_REGISTRY",
    ) -> TrackedSubjectOutcomeRecord:
        """
        Ingests and records an individual prospective subject event outcome.
        """
        key = f"{target_objective}:{rule_id}"
        if key not in self._tracked_records:
            self._tracked_records[key] = []

        record = TrackedSubjectOutcomeRecord(
            subject_id=subject_id,
            target_objective=target_objective,
            rule_id=rule_id,
            predicted_window_start=predicted_window_start,
            predicted_window_end=predicted_window_end,
            actual_event_date=actual_event_date,
            predicted_probability=round(predicted_probability, 4),
            verification_status=verification_status,
            verification_source=verification_source,
            recorded_at=datetime.now(timezone.utc),
        )

        key = f"{target_objective}:{rule_id}"
        self._tracked_records[key].append(record)
        return record

    def evaluate_longitudinal_tracking(
        self,
        target_objective: str = "marriage",
        rule_id: Optional[str] = None,
        snapshot_id: Optional[str] = None,
    ) -> LongitudinalTrackingReport:
        """
        Evaluates longitudinal tracking metrics across all recorded subject outcomes.
        """
        report_id = f"long-{uuid.uuid4().hex[:8]}"

        # ── 1. Query Upstream Engines Dynamically
        prosp_regs = [r for r in self._prospective_engine.list_registrations() if r.target_objective.lower() == target_objective.lower()]
        # Only used to name/describe a genuinely untracked rule when the
        # caller didn't supply rule_id — NEVER used to pick the baseline
        # report below, which must match the actual effective_rule_id.
        effective_rule_id = rule_id or (prosp_regs[0].hypothesis_id if prosp_regs else "hyp-m1")
        matching_reg = next((r for r in prosp_regs if r.hypothesis_id == effective_rule_id), None)
        rule_name = matching_reg.rule_name if matching_reg else "Canonical Polymodal Timing Rule"

        # Lookup baseline prospective performance from a real matching
        # report for THIS SPECIFIC rule (by hypothesis_id, not just any
        # registration sharing the target_objective — a previous version
        # of this fix grabbed prosp_regs[0], the first "marriage"
        # registration found anywhere, which silently borrowed an
        # unrelated rule's baseline whenever multiple rules were
        # registered for the same objective). No fabricated fallback: if
        # no real baseline exists yet for this rule, the degradation test
        # below is skipped rather than compared against an invented or
        # unrelated baseline.
        baseline_hit_rate: Optional[float] = None
        baseline_sample_n: Optional[int] = None
        if matching_reg is not None:
            for rep in self._prospective_engine._reports.values():
                if rep.registration_id == matching_reg.registration_id:
                    baseline_hit_rate = rep.precision if getattr(rep, "precision", None) is not None else (rep.positive_outcomes_count / max(1, rep.total_prospective_subjects))
                    baseline_sample_n = rep.total_prospective_subjects
                    break

        # No fabricated seed data: an untracked rule simply has zero
        # recorded subjects until real outcomes are ingested via
        # record_subject_outcome().
        key = f"{target_objective}:{effective_rule_id}"
        records = list(self._tracked_records.get(key, []))
        if not records and rule_id is None:
            prefix = f"{target_objective}:"
            for k, v in self._tracked_records.items():
                if k.startswith(prefix):
                    records.extend(v)
        total_subjects = len(records)
        confirmed_hits = sum(1 for r in records if r.verification_status == OutcomeVerificationStatus.CONFIRMED_HIT)
        confirmed_misses = sum(1 for r in records if r.verification_status == OutcomeVerificationStatus.CONFIRMED_MISS)
        ambiguous = sum(1 for r in records if r.verification_status == OutcomeVerificationStatus.AMBIGUOUS_UNVERIFIED)
        outside_window = sum(1 for r in records if r.verification_status == OutcomeVerificationStatus.OUTSIDE_WINDOW)

        evaluable_n = confirmed_hits + confirmed_misses
        cum_hit_rate = round(confirmed_hits / evaluable_n, 4) if evaluable_n > 0 else 0.0

        # Cumulative Brier Score: Mean squared error of predicted probabilities
        sq_errors = []
        for r in records:
            if r.verification_status == OutcomeVerificationStatus.CONFIRMED_HIT:
                sq_errors.append((r.predicted_probability - 1.0) ** 2)
            elif r.verification_status == OutcomeVerificationStatus.CONFIRMED_MISS:
                sq_errors.append((r.predicted_probability - 0.0) ** 2)
        # No fabricated fallback: 0.0 with zero sample size honestly means
        # "no evaluable outcomes recorded yet", not a fake stable score.
        cum_brier = round(sum(sq_errors) / len(sq_errors), 4) if sq_errors else 0.0

        # ── 3. Time Series Quarterly Intervals
        q1_records = [r for r in records if r.predicted_window_start < date(2026, 4, 1)]
        q2_records = [r for r in records if r.predicted_window_start >= date(2026, 4, 1)]

        q1_hits = sum(1 for r in q1_records if r.verification_status == OutcomeVerificationStatus.CONFIRMED_HIT)
        q1_miss = sum(1 for r in q1_records if r.verification_status == OutcomeVerificationStatus.CONFIRMED_MISS)
        q1_hit_rate = round(q1_hits / max(1, q1_hits + q1_miss), 4)

        q2_hits = sum(1 for r in q2_records if r.verification_status == OutcomeVerificationStatus.CONFIRMED_HIT)
        q2_miss = sum(1 for r in q2_records if r.verification_status == OutcomeVerificationStatus.CONFIRMED_MISS)
        q2_hit_rate = round(q2_hits / max(1, q2_hits + q2_miss), 4)

        def _interval_brier(interval_records: list) -> float:
            errs = [
                (r.predicted_probability - 1.0) ** 2 if r.verification_status == OutcomeVerificationStatus.CONFIRMED_HIT
                else (r.predicted_probability - 0.0) ** 2
                for r in interval_records
                if r.verification_status in (OutcomeVerificationStatus.CONFIRMED_HIT, OutcomeVerificationStatus.CONFIRMED_MISS)
            ]
            return round(sum(errs) / len(errs), 4) if errs else 0.0

        q1_brier = _interval_brier(q1_records)
        q2_brier = _interval_brier(q2_records)

        # ── 4. Population Stability Index (PSI): real 2-bin (hit/miss)
        # distribution shift between Q1 (expected/baseline interval) and Q2
        # (actual/current interval) — standard PSI formula, not a hardcoded
        # constant. Undefined (0.0, STABLE by convention) when either
        # interval has no evaluable outcomes, since PSI needs both
        # distributions to compare.
        _PSI_EPS = 1e-6

        def _psi(expected_hit_rate: float, actual_hit_rate: float) -> float:
            bins = ((expected_hit_rate, actual_hit_rate), (1.0 - expected_hit_rate, 1.0 - actual_hit_rate))
            total = 0.0
            for expected_pct, actual_pct in bins:
                e = max(expected_pct, _PSI_EPS)
                a = max(actual_pct, _PSI_EPS)
                total += (a - e) * math.log(a / e)
            return total

        q1_evaluable = q1_hits + q1_miss
        q2_evaluable = q2_hits + q2_miss
        if q1_evaluable > 0 and q2_evaluable > 0:
            psi_score = round(_psi(q1_hit_rate, q2_hit_rate), 4)
        else:
            psi_score = 0.0

        intervals = (
            LongitudinalTimeSeriesInterval(
                interval_id="2026-Q1",
                interval_start=date(2026, 1, 1),
                interval_end=date(2026, 3, 31),
                sample_size_n=len(q1_records),
                confirmed_hits=q1_hits,
                confirmed_misses=q1_miss,
                interval_hit_rate=q1_hit_rate,
                rolling_brier_score=q1_brier,
                interval_psi=0.0,
                distribution_drift_status=PopulationDistributionDriftStatus.STABLE_CONGRUENT,
            ),
            LongitudinalTimeSeriesInterval(
                interval_id="2026-Q2",
                interval_start=date(2026, 4, 1),
                interval_end=date(2026, 6, 30),
                sample_size_n=len(q2_records),
                confirmed_hits=q2_hits,
                confirmed_misses=q2_miss,
                interval_hit_rate=q2_hit_rate,
                rolling_brier_score=q2_brier,
                interval_psi=psi_score,
                distribution_drift_status=PopulationDistributionDriftStatus.STABLE_CONGRUENT,
            ),
        )

        # ── 4b. Mechanism 1: Population Stability Index Drift Classification
        if psi_score < 0.10:
            drift_status = PopulationDistributionDriftStatus.STABLE_CONGRUENT
        elif psi_score < 0.25:
            drift_status = PopulationDistributionDriftStatus.MILD_DRIFT_MONITOR
        else:
            drift_status = PopulationDistributionDriftStatus.CRITICAL_DEGRADATION_TRIGGER

        # ── 5. Mechanism 2: Statistical Degradation Test (Two-Proportion Z-Test)
        # H0: p_longitudinal >= p_baseline  vs  H1: p_longitudinal < p_baseline
        # No fabricated baseline: if no real prospective report matched
        # this rule, there is nothing to test against.
        if baseline_hit_rate is None or baseline_sample_n is None or baseline_sample_n <= 0:
            z_stat = 0.0
            degradation_p_val = 1.0
            delta_hit_rate = 0.0
            is_stat_sig_degraded = False
            test_rationale = "NO_BASELINE: No matching prospective validation report found for this rule — degradation test skipped, not fabricated."
            baseline_hit_rate_reported = 0.0
        else:
            k_base = int(round(baseline_hit_rate * baseline_sample_n))
            k_long = confirmed_hits
            n_base = baseline_sample_n
            n_long = max(1, evaluable_n)

            p_pool = (k_base + k_long) / (n_base + n_long)
            se = math.sqrt(p_pool * (1.0 - p_pool) * (1.0 / n_base + 1.0 / n_long))
            delta_hit_rate = round(cum_hit_rate - baseline_hit_rate, 4)

            if se > 0:
                z_stat = (cum_hit_rate - baseline_hit_rate) / se
                # One-tailed lower tail standard normal CDF approximation
                # CDF(z) = 0.5 * (1 + erf(z / sqrt(2)))
                degradation_p_val = round(0.5 * (1.0 + math.erf(z_stat / math.sqrt(2.0))), 5)
            else:
                z_stat = 0.0
                degradation_p_val = 1.0

            is_stat_sig_degraded = bool(degradation_p_val < 0.05 and delta_hit_rate < 0.0)
            baseline_hit_rate_reported = baseline_hit_rate

            if is_stat_sig_degraded:
                test_rationale = f"CRITICAL_DEGRADATION: Longitudinal hit rate ({cum_hit_rate:.1%}) degraded significantly below baseline ({baseline_hit_rate:.1%}), p = {degradation_p_val:.5f} < 0.05."
            elif delta_hit_rate >= 0:
                test_rationale = f"NO_DEGRADATION: Longitudinal hit rate ({cum_hit_rate:.1%}) equals or exceeds baseline ({baseline_hit_rate:.1%}), Delta = +{delta_hit_rate * 100:.1f}%."
            else:
                test_rationale = f"MILD_FLUCTUATION_NOT_SIGNIFICANT: Longitudinal hit rate ({cum_hit_rate:.1%}) exhibits minor negative delta ({delta_hit_rate * 100:.1f}%), but difference is not statistically significant (p = {degradation_p_val:.4f} >= 0.05)."

        stat_test = StatisticalDegradationTest(
            baseline_prospective_hit_rate=round(baseline_hit_rate_reported, 4),
            longitudinal_rolling_hit_rate=cum_hit_rate,
            delta_hit_rate=delta_hit_rate,
            sample_size_longitudinal=evaluable_n,
            z_statistic=round(z_stat, 3),
            degradation_p_value=degradation_p_val,
            is_degradation_statistically_significant=is_stat_sig_degraded,
            test_interpretation=test_rationale,
        )

        # ── 6. Cryptographic Provenance Hash & Lineage
        p11_snap = snapshot_id or (
            list(self._experiment_registry._snapshots.keys())[-1]
            if hasattr(self._experiment_registry, "_snapshots") and self._experiment_registry._snapshots
            else "snap-p11-longitudinal-root"
        )
        hash_payload = {
            "report_id": report_id,
            "rule_id": effective_rule_id,
            "total_subjects": total_subjects,
            "cum_hit_rate": cum_hit_rate,
            "psi_score": psi_score,
            "p11_snap": p11_snap,
        }
        rep_hash = hashlib.sha256(json.dumps(hash_payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]

        report = LongitudinalTrackingReport(
            report_id=report_id,
            rule_id=effective_rule_id,
            rule_name=rule_name,
            target_objective=target_objective,
            total_subjects_tracked=total_subjects,
            confirmed_hits_count=confirmed_hits,
            confirmed_misses_count=confirmed_misses,
            ambiguous_count=ambiguous,
            outside_window_count=outside_window,
            cumulative_hit_rate=cum_hit_rate,
            cumulative_brier_score=cum_brier,
            population_distribution_drift=drift_status,
            population_stability_index=psi_score,
            statistical_degradation_test=stat_test,
            time_series_intervals=intervals,
            p11_lineage_snapshot_id=p11_snap,
            report_provenance_hash=rep_hash,
            epistemic_non_causal_statement="LONGITUDINAL_TRACKING_ONLY: Real-world outcome tracking evaluates empirical temporal co-occurrence and calibration consistency without asserting physical causality.",
            evaluated_at=datetime.now(timezone.utc),
        )

        self._reports[report_id] = report
        return report

    def get_report(self, report_id: str) -> Optional[LongitudinalTrackingReport]:
        return self._reports.get(report_id)

    def list_reports(self) -> List[LongitudinalTrackingReport]:
        return list(self._reports.values())
