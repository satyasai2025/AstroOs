"""
AstroOS — Longitudinal Outcome Tracking Router (Priority 27)

Endpoints for recording real-world prospective event occurrences, evaluating rolling hit rates,
and performing dual-mechanism PSI distribution drift & statistical degradation testing.
"""

from __future__ import annotations

from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from apps.api.dependencies import require_authenticated
from apps.api.domain.longitudinal_tracking import OutcomeVerificationStatus
from apps.api.schemas.longitudinal_tracking import (
    EvaluateTrackingRequest,
    LongitudinalTrackingReportResponse,
    RecordSubjectOutcomeRequest,
)
from apps.api.services.longitudinal_tracking_engine import LongitudinalTrackingEngine

router = APIRouter(
    prefix="/api/v1/research/longitudinal-tracking",
    tags=["Research Longitudinal Tracking"],
    dependencies=[Depends(require_authenticated)],
)


@router.post("/record")
def record_subject_outcome(request: RecordSubjectOutcomeRequest):
    """
    Record an individual prospective subject event observation.
    """
    status_enum = OutcomeVerificationStatus(request.verification_status)
    pred_start = date.fromisoformat(request.predicted_window_start)
    pred_end = date.fromisoformat(request.predicted_window_end)
    actual_dt = date.fromisoformat(request.actual_event_date) if request.actual_event_date else None

    record = LongitudinalTrackingEngine.get_instance().record_subject_outcome(
        subject_id=request.subject_id,
        target_objective=request.target_objective,
        rule_id=request.rule_id,
        predicted_window_start=pred_start,
        predicted_window_end=pred_end,
        actual_event_date=actual_dt,
        predicted_probability=request.predicted_probability,
        verification_status=status_enum,
        verification_source=request.verification_source,
    )

    return {
        "status": "RECORDED",
        "subject_id": record.subject_id,
        "verification_status": record.verification_status.value,
        "recorded_at": record.recorded_at.isoformat(),
    }


@router.post("/evaluate", response_model=LongitudinalTrackingReportResponse)
def evaluate_longitudinal_tracking(request: EvaluateTrackingRequest):
    """
    Evaluate longitudinal outcome tracking metrics, time-series intervals, PSI, and statistical degradation.
    """
    rep = LongitudinalTrackingEngine.get_instance().evaluate_longitudinal_tracking(
        target_objective=request.target_objective,
        rule_id=request.rule_id,
        snapshot_id=request.snapshot_id,
    )

    return LongitudinalTrackingReportResponse(
        report_id=rep.report_id,
        rule_id=rep.rule_id,
        rule_name=rep.rule_name,
        target_objective=rep.target_objective,
        total_subjects_tracked=rep.total_subjects_tracked,
        confirmed_hits_count=rep.confirmed_hits_count,
        confirmed_misses_count=rep.confirmed_misses_count,
        ambiguous_count=rep.ambiguous_count,
        outside_window_count=rep.outside_window_count,
        cumulative_hit_rate=rep.cumulative_hit_rate,
        cumulative_brier_score=rep.cumulative_brier_score,
        population_distribution_drift=rep.population_distribution_drift.value,
        population_stability_index=rep.population_stability_index,
        statistical_degradation_test={
            "baseline_prospective_hit_rate": rep.statistical_degradation_test.baseline_prospective_hit_rate,
            "longitudinal_rolling_hit_rate": rep.statistical_degradation_test.longitudinal_rolling_hit_rate,
            "delta_hit_rate": rep.statistical_degradation_test.delta_hit_rate,
            "sample_size_longitudinal": rep.statistical_degradation_test.sample_size_longitudinal,
            "z_statistic": rep.statistical_degradation_test.z_statistic,
            "degradation_p_value": rep.statistical_degradation_test.degradation_p_value,
            "is_degradation_statistically_significant": rep.statistical_degradation_test.is_degradation_statistically_significant,
            "test_interpretation": rep.statistical_degradation_test.test_interpretation,
        },
        time_series_intervals=[
            {
                "interval_id": i.interval_id,
                "interval_start": i.interval_start.isoformat(),
                "interval_end": i.interval_end.isoformat(),
                "sample_size_n": i.sample_size_n,
                "confirmed_hits": i.confirmed_hits,
                "confirmed_misses": i.confirmed_misses,
                "interval_hit_rate": i.interval_hit_rate,
                "rolling_brier_score": i.rolling_brier_score,
                "interval_psi": i.interval_psi,
                "distribution_drift_status": i.distribution_drift_status.value,
            }
            for i in rep.time_series_intervals
        ],
        p11_lineage_snapshot_id=rep.p11_lineage_snapshot_id,
        report_provenance_hash=rep.report_provenance_hash,
        epistemic_non_causal_statement=rep.epistemic_non_causal_statement,
        evaluated_at=rep.evaluated_at.isoformat(),
    )


@router.get("/latest", response_model=LongitudinalTrackingReportResponse)
def get_latest_tracking_report(target_objective: str = Query("marriage")):
    """
    Get or evaluate the latest longitudinal tracking report for the target objective.
    """
    rep = LongitudinalTrackingEngine.get_instance().evaluate_longitudinal_tracking(
        target_objective=target_objective
    )

    return LongitudinalTrackingReportResponse(
        report_id=rep.report_id,
        rule_id=rep.rule_id,
        rule_name=rep.rule_name,
        target_objective=rep.target_objective,
        total_subjects_tracked=rep.total_subjects_tracked,
        confirmed_hits_count=rep.confirmed_hits_count,
        confirmed_misses_count=rep.confirmed_misses_count,
        ambiguous_count=rep.ambiguous_count,
        outside_window_count=rep.outside_window_count,
        cumulative_hit_rate=rep.cumulative_hit_rate,
        cumulative_brier_score=rep.cumulative_brier_score,
        population_distribution_drift=rep.population_distribution_drift.value,
        population_stability_index=rep.population_stability_index,
        statistical_degradation_test={
            "baseline_prospective_hit_rate": rep.statistical_degradation_test.baseline_prospective_hit_rate,
            "longitudinal_rolling_hit_rate": rep.statistical_degradation_test.longitudinal_rolling_hit_rate,
            "delta_hit_rate": rep.statistical_degradation_test.delta_hit_rate,
            "sample_size_longitudinal": rep.statistical_degradation_test.sample_size_longitudinal,
            "z_statistic": rep.statistical_degradation_test.z_statistic,
            "degradation_p_value": rep.statistical_degradation_test.degradation_p_value,
            "is_degradation_statistically_significant": rep.statistical_degradation_test.is_degradation_statistically_significant,
            "test_interpretation": rep.statistical_degradation_test.test_interpretation,
        },
        time_series_intervals=[
            {
                "interval_id": i.interval_id,
                "interval_start": i.interval_start.isoformat(),
                "interval_end": i.interval_end.isoformat(),
                "sample_size_n": i.sample_size_n,
                "confirmed_hits": i.confirmed_hits,
                "confirmed_misses": i.confirmed_misses,
                "interval_hit_rate": i.interval_hit_rate,
                "rolling_brier_score": i.rolling_brier_score,
                "interval_psi": i.interval_psi,
                "distribution_drift_status": i.distribution_drift_status.value,
            }
            for i in rep.time_series_intervals
        ],
        p11_lineage_snapshot_id=rep.p11_lineage_snapshot_id,
        report_provenance_hash=rep.report_provenance_hash,
        epistemic_non_causal_statement=rep.epistemic_non_causal_statement,
        evaluated_at=rep.evaluated_at.isoformat(),
    )
