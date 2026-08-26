"""
AstroOS — Knowledge Reliability API Schemas

Pydantic request and response models for:
- Source reliability assessment
- Rule documentation and provenance
- Lifecycle state transitions
- Validation policies and summaries
- Evidence family degrees of freedom calculations
- Traceability queries
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Source Reliability ───────────────────────────────────────────────────────

class SourceProvenanceSchema(BaseModel):
    edition_title: str
    publisher: str
    publication_year: Optional[int] = None
    editor_or_translator: Optional[str] = None
    manuscript_lineage: Optional[str] = None
    is_critical_edition: bool = False


class ScholarlyEvaluationSchema(BaseModel):
    tradition: str
    methodology_clarity_notes: str = ""
    primary_commentaries: List[str] = Field(default_factory=list)
    known_disputed_passages: List[str] = Field(default_factory=list)


class RegisterSourceRequest(BaseModel):
    source_id: uuid.UUID
    source_name: str = Field(min_length=1, max_length=300)
    tier: str  # SourceReliabilityTier
    provenance: SourceProvenanceSchema
    scholarly_eval: ScholarlyEvaluationSchema
    review_status: str = "UNREVIEWED"
    empirical_citations: List[str] = Field(default_factory=list)
    known_failures_or_contradictions: List[str] = Field(default_factory=list)


class SourceReliabilityResponse(BaseModel):
    source_id: uuid.UUID
    source_name: str
    tier: str
    provenance: SourceProvenanceSchema
    scholarly_eval: ScholarlyEvaluationSchema
    review_status: str
    empirical_citations: List[str]
    known_failures_or_contradictions: List[str]
    audit_log: List[str]


# ── Rule Documentation & Provenance ──────────────────────────────────────────

class DocumentRuleRequest(BaseModel):
    rule_id: str = Field(min_length=1, max_length=100)
    rule_name: str = Field(min_length=1, max_length=300)
    technique_framework: str  # TechniqueFramework
    source_id: uuid.UUID
    passage_reference: str = Field(min_length=1)
    original_text_excerpt: str = Field(min_length=1)
    extracted_by_actor_id: str
    extracted_by_role: str  # ActorRole
    rule_definition_id: str = Field(min_length=1)
    extraction_method: str = "MANUAL_SCHOLARLY_TRANSCRIPTION"
    evidence_family_id: Optional[str] = None
    source_name: Optional[str] = None


class RuleProvenanceSchema(BaseModel):
    source_id: uuid.UUID
    passage_reference: str
    original_text_excerpt: str
    extraction_method: str
    extracted_by_actor_id: str
    extracted_by_role: str
    rule_definition_id: str
    source_name: Optional[str] = None
    extracted_at: str


class RuleValidationSummarySchema(BaseModel):
    policy_id: str
    cases_tested: int
    applicable_cases: int
    supported_outcomes: int
    unsupported_outcomes: int
    indeterminate_cases: int
    counterexamples: List[str] = Field(default_factory=list)
    empirical_hit_rate: float
    brier_score: Optional[float] = None
    dataset_id: str
    dataset_version: str = "1.0.0"
    benchmark_experiment_id: Optional[str] = None
    validated_at: str
    validated_by_actor_id: str = "SYSTEM"


class RuleReliabilityResponse(BaseModel):
    rule_id: str
    rule_name: str
    technique_framework: str
    provenance: RuleProvenanceSchema
    evidence_family_id: Optional[str] = None
    lifecycle_state: str
    evidence_level: str
    validation_summary: Optional[RuleValidationSummarySchema] = None
    conflict_ids: List[str] = Field(default_factory=list)
    review_history: List[str] = Field(default_factory=list)
    canonical_signoff_by: Optional[str] = None
    canonical_signoff_at: Optional[str] = None


# ── Lifecycle Transition Request ─────────────────────────────────────────────

class TransitionLifecycleRequest(BaseModel):
    target_state: str  # RuleLifecycleState
    actor_id: str
    actor_role: str  # ActorRole
    notes: str = ""
    policy_id: Optional[str] = None
    validation_summary: Optional[RuleValidationSummarySchema] = None


# ── Validation Policy ────────────────────────────────────────────────────────

class ValidationPolicySchema(BaseModel):
    policy_id: str
    name: str
    min_applicable_cases: int = 30
    min_holdout_cases: int = 100
    min_hit_rate: float = 0.60
    max_brier_score: float = 0.25
    max_counterexample_ratio: float = 0.15
    require_independent_replication: bool = True
    require_holdout_split: bool = True


# ── Evidence Families & Independence ─────────────────────────────────────────

class EvidenceFamilyRegisterRequest(BaseModel):
    family_id: str
    name: str
    underlying_principle: str
    tradition: str
    member_rule_ids: List[str] = Field(default_factory=list)
    max_independent_dof: int = 1


class EvidenceFamilyResponse(BaseModel):
    family_id: str
    name: str
    underlying_principle: str
    tradition: str
    member_rule_ids: List[str]
    max_independent_dof: int


class IndependentConfirmationsRequest(BaseModel):
    rule_ids: List[str]


class IndependentConfirmationsResponse(BaseModel):
    total_rules_matched: int
    independent_confirmations_dof: int
    standalone_rules_count: int
    standalone_rule_ids: List[str]
    family_breakdown: Dict[str, Any]
