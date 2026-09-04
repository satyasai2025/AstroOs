"""
AstroOS — Knowledge Validation & Promotion Pydantic Schemas
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ValidationStatusSchema(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_REVISION = "NEEDS_REVISION"


class ValidationCheckItemSchema(BaseModel):
    criterion: str
    passed: bool
    evidence: str
    recommendation: str = ""


class ValidationCriteriaSchema(BaseModel):
    source_identity_verified: bool = False
    source_provenance_verified: bool = False
    tradition_framework_verified: bool = False
    passage_reference_verified: bool = False
    text_integrity_verified: bool = False
    interpretation_verified: bool = False
    technique_applicability_verified: bool = False
    contradiction_conflict_status_checked: bool = False

    evidence_checks: List[ValidationCheckItemSchema] = Field(default_factory=list)


class CreateValidationRequest(BaseModel):
    knowledge_item_id: str
    knowledge_item_type: str = Field(
        ..., description="'document' or 'chunk'"
    )
    validator_id: str
    validator_role: str = Field(
        "validator", description="Actor role performing the validation."
    )
    technique_framework: str = Field(
        "Parashari", description="Belongs to which technique framework."
    )
    is_cross_technique: bool = False
    cross_technique_note: str = ""
    validation_notes: str = ""
    validation_decision: str = Field(
        ..., description="Human-readable rationale for the decision."
    )
    criteria: ValidationCriteriaSchema


class ValidationResponseSchema(BaseModel):
    validation_id: str
    knowledge_item_id: str
    knowledge_item_type: str
    validator_id: str
    validator_role: str
    validation_status: ValidationStatusSchema
    validated_at: str
    criteria: ValidationCriteriaSchema
    technique_framework: str
    is_cross_technique: bool
    cross_technique_note: str
    validation_notes: str
    validation_decision: str
    is_eligible_for_promotion: bool
    eligible_promotion_targets: List[str]
    criteria_score: float


class PromoteRequest(BaseModel):
    validation_id: str
    promter_id: str = Field(...)
    promter_role: str = Field(..., description="Must be 'promoter' or 'admin'")
    promotion_target: str = Field(
        ...,
        description=(
            "Allowed: governed_rule_registry, embedding_store, "
            "retrieval_index, technique_specific_ruleset, document_only"
        ),
    )
    promotion_notes: str = ""

    @field_validator("promotion_target")
    @classmethod
    def validate_target(cls, v: str) -> str:
        allowed = {
            "governed_rule_registry",
            "embedding_store",
            "retrieval_index",
            "technique_specific_ruleset",
            "document_only",
        }
        v_lower = v.lower().strip().replace(" ", "_").replace("-", "_")
        if v_lower not in allowed:
            raise ValueError(
                f"promotion_target must be one of: {sorted(allowed)}, got {v!r}"
            )
        return v_lower


class PromoteResponseSchema(BaseModel):
    success: bool
    message: str
    promoted_at: str
    validation_id: str
    promotion_target: str
    audit_log_id: str


class RejectPromotionRequest(BaseModel):
    validation_id: str
    actor_id: str
    actor_role: str
    reason: str = ""


class AuditEntrySchema(BaseModel):
    audit_id: str
    validation_id: str
    actor_id: str
    actor_role: str
    action: str
    previous_state: str
    new_state: str
    reason: str
    source_reference: str
    metadata: Dict[str, Any]
    timestamp: str


class ValidationAuditResponseSchema(BaseModel):
    validation: ValidationResponseSchema
    audit_trail: List[AuditEntrySchema]