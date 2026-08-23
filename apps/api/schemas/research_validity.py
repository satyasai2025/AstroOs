"""
AstroOS — Research Validity Pydantic Schemas (Priority 33)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AssessValidityRequest(BaseModel):
    target_objective: str = Field(default="marriage")
    source_snapshot_id: str = Field(default="snap-p11-evidence-root")
    override_prediction_after_outcome: bool = Field(default=False)
    override_outcome_features_in_predictor: bool = Field(default=False)
    override_sample_size: Optional[int] = Field(default=None)
    override_model_accuracy: Optional[float] = Field(default=None)


class DatasetManifestSchema(BaseModel):
    manifest_id: str
    source_snapshot_id: str
    total_observations: int
    usable_observations: int
    excluded_observations: int
    missing_observations: int
    duplicate_count: int
    prospective_count: int
    retrospective_count: int
    unknown_timing_count: int
    verification_distribution: Dict[str, int]
    domain_distribution: Dict[str, int]
    methodology_version: str
    manifest_hash: str


class BaselineComparisonSchema(BaseModel):
    metric_name: str
    model_metric: float
    majority_baseline: float
    random_baseline: float
    permutation_baseline: Optional[float] = None
    absolute_difference: float
    relative_difference: float
    is_superior_to_majority: bool
    is_superior_to_random: bool


class ConfidenceIntervalSchema(BaseModel):
    estimate: float
    confidence_level: float
    lower_bound: float
    upper_bound: float
    method: str


class StatisticalResultSchema(BaseModel):
    metric_name: str
    value: float
    method: str
    sample_size: int
    confidence_interval: Optional[ConfidenceIntervalSchema] = None
    p_value: Optional[float] = None
    adjusted_p_value: Optional[float] = None
    multiple_testing_method: str


class EffectSizeSchema(BaseModel):
    metric_name: str
    value: float
    interpretation: str
    is_practically_meaningful: bool


class BiasDiagnosticSchema(BaseModel):
    diagnostic_name: str
    risk_level: str
    reason: str
    evidence_details: Dict[str, Any]


class TemporalIntegritySchema(BaseModel):
    status: str
    predictions_registered_before_outcome: bool
    look_ahead_risk_detected: bool
    details: Dict[str, Any]


class LeakageDiagnosticSchema(BaseModel):
    status: str
    outcome_derived_features_detected: bool
    future_timestamps_detected: bool
    reasons: List[str]


class ValidityAssessmentResponse(BaseModel):
    assessment_id: str
    target_objective: str
    source_snapshot_id: str
    methodology_version: str
    dataset_manifest: DatasetManifestSchema
    sample_adequacy: str
    missing_data_classification: str
    temporal_integrity: TemporalIntegritySchema
    leakage_diagnostic: LeakageDiagnosticSchema
    selection_bias_diagnostic: BiasDiagnosticSchema
    cherry_picking_diagnostic: BiasDiagnosticSchema
    baseline_comparison: BaselineComparisonSchema
    statistical_results: List[StatisticalResultSchema]
    effect_sizes: List[EffectSizeSchema]
    overall_verdict: str
    verdict_explanation: List[str]
    limitations: List[str]
    warnings: List[str]
    analysis_fingerprint: str
    validity_snapshot_id: str
    created_at: str
    non_causal_disclosure: str


class ValiditySnapshotResponse(BaseModel):
    snapshot_id: str
    assessment_id: str
    source_snapshot_id: str
    methodology_version: str
    canonical_payload_hash: str
    created_at: str
    non_causal_disclosure: str


class ValidityAuditEventResponse(BaseModel):
    audit_event_id: str
    assessment_id: str
    operation: str
    actor_type: str
    timestamp: str
    details_hash: str
    reason: str
