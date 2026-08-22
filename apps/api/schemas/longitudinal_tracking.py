"""
AstroOS — Longitudinal Outcome Tracking Schemas (Priority 27)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StatisticalDegradationTestSchema(BaseModel):
    baseline_prospective_hit_rate: float
    longitudinal_rolling_hit_rate: float
    delta_hit_rate: float
    sample_size_longitudinal: int
    z_statistic: float
    degradation_p_value: float
    is_degradation_statistically_significant: bool
    test_interpretation: str


class LongitudinalTimeSeriesIntervalSchema(BaseModel):
    interval_id: str
    interval_start: str
    interval_end: str
    sample_size_n: int
    confirmed_hits: int
    confirmed_misses: int
    interval_hit_rate: float
    rolling_brier_score: float
    interval_psi: float
    distribution_drift_status: str


class LongitudinalTrackingReportResponse(BaseModel):
    report_id: str
    rule_id: str
    rule_name: str
    target_objective: str
    total_subjects_tracked: int
    confirmed_hits_count: int
    confirmed_misses_count: int
    ambiguous_count: int
    outside_window_count: int
    cumulative_hit_rate: float
    cumulative_brier_score: float
    population_distribution_drift: str
    population_stability_index: float
    statistical_degradation_test: StatisticalDegradationTestSchema
    time_series_intervals: List[LongitudinalTimeSeriesIntervalSchema]
    p11_lineage_snapshot_id: str
    report_provenance_hash: str
    epistemic_non_causal_statement: str
    evaluated_at: str


class RecordSubjectOutcomeRequest(BaseModel):
    subject_id: str = Field(description="Unique subject identifier")
    target_objective: str = Field(default="marriage", description="Target objective")
    rule_id: str = Field(description="Rule or hypothesis identifier")
    predicted_window_start: str = Field(description="ISO date string: YYYY-MM-DD")
    predicted_window_end: str = Field(description="ISO date string: YYYY-MM-DD")
    actual_event_date: Optional[str] = Field(default=None, description="Optional actual event date")
    predicted_probability: float = Field(default=0.85, description="Model predicted probability")
    verification_status: str = Field(description="CONFIRMED_HIT, CONFIRMED_MISS, AMBIGUOUS_UNVERIFIED, OUTSIDE_WINDOW")
    verification_source: str = Field(default="MUNICIPAL_REGISTRY", description="Verification data source")


class EvaluateTrackingRequest(BaseModel):
    target_objective: str = Field(default="marriage", description="Research target objective")
    rule_id: Optional[str] = Field(default=None, description="Optional rule ID")
    snapshot_id: Optional[str] = Field(default=None, description="Optional P11 snapshot ID")
