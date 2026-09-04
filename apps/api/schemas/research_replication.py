"""
AstroOS — Research Replication Pydantic Schemas (Priority 34)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CreateClaimRequest(BaseModel):
    research_question: str = Field(default="Does 7th Lord Dasha + Jupiter Aspect predict marriage timing?")
    hypothesis: str = Field(default="7th Lord Dasha with Jupiter transit aspect increases marriage incidence probability above 61% baseline.")
    target_objective: str = Field(default="marriage")
    original_assessment_id: str = Field(default="val-assess-default")
    claim_version: str = Field(default="v1.0")


class ResearchClaimSchema(BaseModel):
    claim_id: str
    claim_version: str
    research_question: str
    hypothesis: str
    predictor_definition: str
    outcome_definition: str
    population_definition: str
    evaluation_metric: str
    baseline_definition: str
    original_assessment_id: str
    created_at: str
    claim_hash: str


class CreateProtocolRequest(BaseModel):
    claim_id: str
    replication_metric: str = Field(default="ACCURACY")


class ReplicationProtocolSchema(BaseModel):
    protocol_id: str
    claim_id: str
    claim_version: str
    dataset_requirements: str
    inclusion_criteria: List[str]
    exclusion_criteria: List[str]
    predictors: List[str]
    outcome: str
    statistical_methodology: str
    baseline_definition: str
    replication_metric: str
    stopping_conditions: str
    falsification_criteria: List[str]
    methodology_version: str
    status: str
    created_at: str
    protocol_hash: str


class ReproductionAssessmentSchema(BaseModel):
    assessment_id: str
    source_validity_assessment_id: str
    source_snapshot_id: str
    source_manifest_id: str
    methodology_version: str
    software_version: str
    analysis_definition_hash: str
    input_fingerprint: str
    output_fingerprint: str
    expected_metrics: Dict[str, float]
    reproduced_metrics: Dict[str, float]
    metric_deltas: Dict[str, float]
    reproduction_status: str
    created_at: str


class ReplicationDatasetManifestSchema(BaseModel):
    dataset_id: str
    source_snapshot_id: str
    evidence_count: int
    usable_count: int
    excluded_count: int
    prospective_count: int
    retrospective_count: int
    verification_distribution: Dict[str, int]
    outcome_distribution: Dict[str, int]
    time_range: str
    geographic_scope: str
    population_scope: str
    dataset_fingerprint: str
    independence_status: str


class NegativeControlResultSchema(BaseModel):
    status: str
    control_target: str
    observed_effect: float
    expected_effect: float
    reason: str


class NullModelResultSchema(BaseModel):
    null_model_type: str
    iterations: int
    seed: int
    observed_metric: float
    mean_null_metric: float
    median_null_metric: float
    null_percentile: float
    p_value: float
    extreme_count: int


class SensitivityVariantSchema(BaseModel):
    variant_name: str
    variant_definition: str
    variant_result: float
    metric_delta: float
    verdict_changed: bool


class FalsificationExperimentSchema(BaseModel):
    experiment_id: str
    claim_id: str
    negative_control: NegativeControlResultSchema
    null_model: NullModelResultSchema
    sensitivity_variants: List[SensitivityVariantSchema]
    falsification_result: str
    tests_passed: List[str]
    tests_failed: List[str]
    created_at: str


class StressTestResultsSchema(BaseModel):
    test_id: str
    parameter_sensitivity: str
    subgroup_stability: str
    temporal_stability: str
    dataset_stability: str
    metric_stability: str
    effect_direction: str
    details: Dict[str, Any]


class AssessReplicationRequest(BaseModel):
    claim_id: Optional[str] = Field(default=None)
    protocol_id: Optional[str] = Field(default=None)
    override_dataset_changed: bool = Field(default=False)
    override_same_dataset_reused: bool = Field(default=False)
    override_negative_control_failed: bool = Field(default=False)
    override_effect_reversed: bool = Field(default=False)
    override_leakage: bool = Field(default=False)
    override_param_sensitive: bool = Field(default=False)
    override_null_model_strong: bool = Field(default=False)


class ReplicationStudyAssessmentResponse(BaseModel):
    replication_id: str
    claim: ResearchClaimSchema
    protocol: ReplicationProtocolSchema
    reproduction: ReproductionAssessmentSchema
    replication_dataset: ReplicationDatasetManifestSchema
    falsification: FalsificationExperimentSchema
    stress_tests: StressTestResultsSchema
    original_metric: float
    replication_metric: float
    absolute_delta: float
    relative_delta: float
    baseline_delta: float
    overall_verdict: str
    verdict_explanation: List[str]
    limitations: List[str]
    warnings: List[str]
    replication_fingerprint: str
    replication_snapshot_id: str
    created_at: str
    non_causal_disclosure: str


class ReplicationSnapshotResponse(BaseModel):
    snapshot_id: str
    claim_id: str
    protocol_id: str
    source_assessment_id: str
    replication_manifest_id: str
    falsification_results: Dict[str, Any]
    stress_test_results: Dict[str, Any]
    verdict: str
    methodology_version: str
    canonical_payload_hash: str
    created_at: str
    non_causal_disclosure: str


class ReplicationAuditEventResponse(BaseModel):
    audit_event_id: str
    replication_id: str
    operation: str
    actor_type: str
    timestamp: str
    details_hash: str
    reason: str
