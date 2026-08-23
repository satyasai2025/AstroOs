"""
AstroOS — Research Generalization Pydantic Schemas (Priority 35)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExternalDomainSchema(BaseModel):
    domain_id: str
    domain_name: str
    is_source: bool
    population_dimension: str
    time_dimension: str
    dataset_dimension: str
    context_dimension: str
    created_at: str


class DistributionShiftAnalysisSchema(BaseModel):
    source_domain_id: str
    target_domain_id: str
    shift_type: str
    feature_drift_score: float
    outcome_drift_score: float
    baseline_drift_score: float
    is_significant_shift: bool
    details: Dict[str, Any]


class DomainBoundarySchema(BaseModel):
    boundary_id: str
    dimension_name: str
    valid_range: str
    failure_threshold: str
    degradation_rate: float


class FailureRegionSchema(BaseModel):
    region_id: str
    region_type: str
    affected_dimension: str
    trigger_condition: str
    severity: str


class GeneralizationMatrixCellSchema(BaseModel):
    source_domain_id: str
    target_domain_id: str
    target_domain_name: str
    status: str
    target_metric: float
    target_baseline: float
    baseline_lift: float
    is_baseline_superior: bool


class TransportabilityAssessmentSchema(BaseModel):
    source_domain_id: str
    target_domain_id: str
    status: str
    transfer_loss: float
    reasons: List[str]


class AssessGeneralizationRequest(BaseModel):
    target_objective: str = Field(default="marriage")
    source_replication_id: str = Field(default="repl-study-default")
    override_inferior_target: bool = Field(default=False)
    override_direction_reversal: bool = Field(default=False)
    override_performance_collapse: bool = Field(default=False)
    override_severe_shift: bool = Field(default=False)
    override_insufficient_sample: bool = Field(default=False)


class GeneralizationAssessmentResponse(BaseModel):
    assessment_id: str
    target_objective: str
    source_domain: ExternalDomainSchema
    target_domains: List[ExternalDomainSchema]
    source_replication_id: str
    methodology_version: str
    shift_analyses: List[DistributionShiftAnalysisSchema]
    boundaries: List[DomainBoundarySchema]
    failure_regions: List[FailureRegionSchema]
    matrix_cells: List[GeneralizationMatrixCellSchema]
    transportability: TransportabilityAssessmentSchema
    overall_verdict: str
    verdict_explanation: List[str]
    limitations: List[str]
    warnings: List[str]
    generalization_fingerprint: str
    generalization_snapshot_id: str
    created_at: str
    non_causal_disclosure: str


class GeneralizationSnapshotResponse(BaseModel):
    snapshot_id: str
    assessment_id: str
    source_replication_id: str
    methodology_version: str
    canonical_payload_hash: str
    created_at: str
    non_causal_disclosure: str


class GeneralizationAuditEventResponse(BaseModel):
    audit_event_id: str
    assessment_id: str
    operation: str
    actor_type: str
    timestamp: str
    details_hash: str
    reason: str
