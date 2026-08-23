"""
AstroOS — Research Knowledge State Pydantic Schemas (Priority 36)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StudyEvidenceEntrySchema(BaseModel):
    study_id: str
    study_type: str
    title: str
    sample_size: int
    metric_name: str
    observed_metric: float
    variance: float
    is_prospective: bool
    is_independent: bool
    weight: float


class MetaAnalysisResultSchema(BaseModel):
    pooled_effect_size: float
    pooled_variance: float
    confidence_interval: List[float]
    i_squared_heterogeneity: float
    heterogeneity_level: str
    tau_squared: float
    p_value: float
    total_samples: int
    forest_plot_data: Dict[str, Any]


class KnowledgeStateTransitionSchema(BaseModel):
    transition_id: str
    from_state: str
    to_state: str
    trigger_study_id: str
    reason: str
    timestamp: str


class ResearchKnowledgeStateRecordSchema(BaseModel):
    state_id: str
    state_version: str
    target_objective: str
    current_state: str
    evidence_grade: str
    certainty_score: float
    meta_analysis: MetaAnalysisResultSchema
    accumulated_studies: List[StudyEvidenceEntrySchema]
    transitions: List[KnowledgeStateTransitionSchema]
    superseded_state_id: Optional[str]
    created_at: str


class SynthesizeKnowledgeStateRequest(BaseModel):
    target_objective: str = Field(default="marriage")
    superseded_state_id: Optional[str] = Field(default=None)
    override_replication_falsified: bool = Field(default=False)
    override_low_sample: bool = Field(default=False)


class KnowledgeStateSynthesisAssessmentResponse(BaseModel):
    assessment_id: str
    knowledge_state: ResearchKnowledgeStateRecordSchema
    overall_verdict: str
    verdict_explanation: List[str]
    limitations: List[str]
    warnings: List[str]
    knowledge_state_fingerprint: str
    knowledge_snapshot_id: str
    created_at: str
    non_causal_disclosure: str


class ResearchKnowledgeSnapshotResponse(BaseModel):
    snapshot_id: str
    state_id: str
    state_version: str
    canonical_payload_hash: str
    created_at: str
    non_causal_disclosure: str


class KnowledgeStateAuditEventResponse(BaseModel):
    audit_event_id: str
    state_id: str
    operation: str
    actor_type: str
    timestamp: str
    details_hash: str
    reason: str
