"""
AstroOS — Knowledge Validation & Promotion Domain Models

Defines:
- ValidationDecisionRecord: the governed validation decision for knowledge items
- ValidationStatus: the decision outcome
- PromotionTarget: where validated knowledge can be promoted to
- ValidationAuditEntry: audit trail entry
- LifecycleTransitionError: invalid transition detection

Pure Python dataclasses — no ORM or framework dependencies.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ── Enums ──────────────────────────────────────────────────────────────────────

class ValidationStatus(str, Enum):
    """Outcome of a single validation event."""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_REVISION = "NEEDS_REVISION"


@dataclass(frozen=True)
class ValidationCheckResult:
    """Result of one validation criterion check."""
    criterion: str
    passed: bool
    evidence_summary: str
    recommendation: str = ""


class PromotionTarget(str, Enum):
    """Allowed destinations for promoted knowledge."""
    GOVERNED_RULE_REGISTRY = "governed_rule_registry"
    EMBEDDING_STORE = "embedding_store"
    RETRIEVAL_INDEX = "retrieval_index"
    TECHNIQUE_SPECIFIC_RULESET = "technique_specific_ruleset"
    DOCUMENT_ONLY = "document_only"


# ── Domain Dataclasses ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ValidationAuditEntry:
    """Single entry in the audit trail for validation/promotion events."""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    actor_role: str = ""
    actor_id: Optional[uuid.UUID] = None
    action: str = ""
    previous_state: str = ""
    new_state: str = ""
    reason: str = ""
    source_reference: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationDecisionRecord:
    """
    Governed validation decision for a knowledge item (document or chunk).

    This is the primary governed record that must be created before any
    knowledge item can move to VALIDATED or beyond.
    """
    validation_id: uuid.UUID
    knowledge_item_id: uuid.UUID
    knowledge_item_type: str  # "document" or "chunk"
    validator_id: uuid.UUID
    validator_role: str  # ActorRole value
    validation_status: str  # ValidationStatus value
    validated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # ── Validation criteria assessments ──────────────────────────────────────
    source_identity_verified: bool = False
    source_provenance_verified: bool = False
    tradition_framework_verified: bool = False
    passage_reference_verified: bool = False
    text_integrity_verified: bool = False
    interpretation_verified: bool = False
    technique_applicability_verified: bool = False
    contradiction_conflict_status_checked: bool = False

    # ── Technique classification ──────────────────────────────────────────────
    technique_framework: str = "Parashari"
    is_cross_technique: bool = False
    cross_technique_note: str = ""

    # ── Decision details ─────────────────────────────────────────────────────
    validation_notes: str = ""
    validation_decision: str = ""  # Human-readable rationale
    evidence_checks: List[Dict[str, Any]] = field(default_factory=list)

    # ── Promotion eligibility ────────────────────────────────────────────────
    is_eligible_for_promotion: bool = False
    eligible_promotion_targets: List[str] = field(default_factory=list)

    # ── Audit trail (owned by this record, not merged with source) ────────────
    audit_entries: List[ValidationAuditEntry] = field(default_factory=list)

    # ── Provenance preservation (never empty after validation) ───────────────
    preserved_provenance: Dict[str, Any] = field(default_factory=dict)

    def add_audit_entry(self, entry: ValidationAuditEntry) -> ValidationDecisionRecord:
        """Return a new record with the audit entry appended (immutable pattern)."""
        new_entries = list(self.audit_entries) + [entry]
        return ValidationDecisionRecord(
            validation_id=self.validation_id,
            knowledge_item_id=self.knowledge_item_id,
            knowledge_item_type=self.knowledge_item_type,
            validator_id=self.validator_id,
            validator_role=self.validator_role,
            validation_status=self.validation_status,
            validated_at=self.validated_at,
            source_identity_verified=self.source_identity_verified,
            source_provenance_verified=self.source_provenance_verified,
            tradition_framework_verified=self.tradition_framework_verified,
            passage_reference_verified=self.passage_reference_verified,
            text_integrity_verified=self.text_integrity_verified,
            interpretation_verified=self.interpretation_verified,
            technique_applicability_verified=self.technique_applicability_verified,
            contradiction_conflict_status_checked=self.contradiction_conflict_status_checked,
            technique_framework=self.technique_framework,
            is_cross_technique=self.is_cross_technique,
            cross_technique_note=self.cross_technique_note,
            validation_notes=self.validation_notes,
            validation_decision=self.validation_decision,
            evidence_checks=self.evidence_checks,
            is_eligible_for_promotion=self.is_eligible_for_promotion,
            eligible_promotion_targets=self.eligible_promotion_targets,
            audit_entries=new_entries,
            preserved_provenance=self.preserved_provenance,
        )


# ── Lifecycle transition rules ─────────────────────────────────────────────────

VALID_TRANSITIONS: Dict[str, List[str]] = {
    "DOCUMENTED": ["UNVALIDATED"],
    "UNVALIDATED": ["VALIDATED", "REJECTED"],
    "REJECTED": ["UNVALIDATED"],  # Resubmission after revision
    "VALIDATED": ["PROMOTED", "CONTRADICTED"],
    "PROMOTED": ["REVIEWED"],
    "REVIEWED": ["VALIDATED", "CONTRADICTED"],
    "CONTRADICTED": ["DOCUMENTED"],
    "UNKNOWN": ["DOCUMENTED"],
}

# Configurable: who can perform which transitions
ROLE_TRANSITION_MATRIX: Dict[str, List[str]] = {
    "validator": ["DOCUMENTED", "UNVALIDATED", "REJECTED"],
    "reviewer": ["REVIEWED", "VALIDATED", "CONTRADICTED"],
    "promoter": ["PROMOTED"],
    "admin": ["DOCUMENTED", "UNVALIDATED", "REJECTED", "VALIDATED", "PROMOTED",
               "REVIEWED", "CONTRADICTED"],
}


# ── Exceptions ─────────────────────────────────────────────────────────────────

class InvalidLifecycleTransitionError(Exception):
    """Raised when a lifecycle transition is not permitted by governance rules."""
    def __init__(self, current: str, requested: str) -> None:
        self.current = current
        self.requested = requested
        super().__init__(
            f"Transition {current!r} → {requested!r} is not allowed by governance rules."
        )


class UnauthorizedLifecycleTransitionError(Exception):
    """Raised when the actor role is not allowed to perform a transition."""
    def __init__(self, role: str, transition: str) -> None:
        self.role = role
        self.transition = transition
        super().__init__(
            f"Actor role {role!r} is not authorized to perform transition → {transition!r}."
        )


class ValidationPolicyViolationError(Exception):
    """Raised when a validation policy check fails."""
    def __init__(self, policy: str, detail: str) -> None:
        self.policy = policy
        self.detail = detail
        super().__init__(f"Validation policy {policy!r} violated: {detail}")


class ContaminationForbiddenError(Exception):
    """Raised when a contamination-invariant operation is attempted."""
    def __init__(self, operation: str, detail: str) -> None:
        self.operation = operation
        self.detail = detail
        super().__init__(f"Contamination forbidden: {operation}: {detail}")


class TechniqueIsolationError(Exception):
    """Raised when cross-technique constraints are violated during promotion."""
    def __init__(self, source_framework: str, target_framework: str) -> None:
        self.source_framework = source_framework
        self.target_framework = target_framework
        super().__init__(
            f"Technique isolation violation: {source_framework} knowledge "
            f"cannot be directly promoted to {target_framework} ruleset."
        )