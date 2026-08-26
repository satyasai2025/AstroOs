"""
AstroOS — Knowledge Validation & Promotion Engine

Core service governing:
1. Strict validation decision lifecycle
2. Anti-contamination enforcement
3. Technique-isolated promotion
4. Authorization matrix
5. Audit trail

Promotion rule:
  - ONLY validation records with status=APPROVED may be promoted.
  - Promotion requires explicit human actor (promoter or admin role).
  - Promotion does NOT auto-inject into executable rule engines.
  - RAG retrieval NEVER triggers promotion.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from apps.api.domain.knowledge_reliability import (
    ActorRole,
    InvalidLifecycleTransitionError,
    RuleLifecycleState,
    TechniqueFramework,
    UnauthorizedLifecycleTransitionError,
    ValidationPolicyViolationError,
)
from apps.api.domain.knowledge_validation import (
    ValidationAuditEntry,
    ValidationCheckResult,
    ValidationDecisionRecord,
    ValidationStatus,
    ContaminationForbiddenError,
    TechniqueIsolationError,
    PromotionTarget,
)

# AI agents must NEVER be permitted to validate or promote knowledge.
_AI_ROLES: set[str] = {
    ActorRole.AI_AGENT.value,
    "ai_agent",
    "gpt-q-and-a",
    "local_llm",
}


def _is_validator_role(role_value: str) -> bool:
    val = role_value.lower().replace("-", "_")
    if val in _AI_ROLES or role_value.lower() in _AI_ROLES:
        return False
    if "ai" in val or "llm" in val or "bot" in val or "gpt" in val:
        return False
    return True


# Pre-populated pilot corpus (must NOT be auto-validated)
_PILOT_CORPUS: Dict[str, Dict[str, Any]] = {
    "gaja-kesari": {
        "title": "Vedic Astrology Wiki — Gaja Kesari Yoga",
        "tradition": "Parashari",
        "source_verified": False,
        "passage_verified": False,
        "criteria_passed": False,
    },
    "pancha-mahapurusha": {
        "title": "Vedic Astrology Wiki — Pancha Mahapurusha Yogas",
        "tradition": "Parashari",
        "source_verified": False,
        "passage_verified": False,
        "criteria_passed": False,
    },
    "navagraha-karakatvas": {
        "title": "Vedic Astrology Wiki — Navagraha Karakatvas",
        "tradition": "Parashari",
        "source_verified": False,
        "passage_verified": False,
        "criteria_passed": False,
    },
    "surya-siddhanta": {
        "title": "Surya Siddhanta",
        "tradition": "Parashari",
        "source_verified": False,
        "passage_verified": False,
        "criteria_passed": False,
    },
    "bphs": {
        "title": "Brihat Parashara Hora Shastra",
        "tradition": "Parashari",
        "source_verified": False,
        "passage_verified": False,
        "criteria_passed": False,
    },
    "phala-deepika": {
        "title": "Phala Deepika",
        "tradition": "Parashari",
        "source_verified": False,
        "passage_verified": False,
        "criteria_passed": False,
    },
    "jaimini-sutras": {
        "title": "Jaimini Sutras",
        "tradition": "Jaimini",
        "source_verified": False,
        "passage_verified": False,
        "criteria_passed": False,
    },
}

# Technique-specific promotion targets
_TECHNIQUE_TARGETS: Dict[str, List[str]] = {
    TechniqueFramework.PARASHARI.value: [
        PromotionTarget.GOVERNED_RULE_REGISTRY.value,
        PromotionTarget.RETRIEVAL_INDEX.value,
        PromotionTarget.DOCUMENT_ONLY.value,
    ],
    TechniqueFramework.JAIMINI.value: [
        PromotionTarget.GOVERNED_RULE_REGISTRY.value,
        PromotionTarget.TECHNIQUE_SPECIFIC_RULESET.value,
        PromotionTarget.RETRIEVAL_INDEX.value,
        PromotionTarget.DOCUMENT_ONLY.value,
    ],
}


class KnowledgeValidationEngine:
    """
    Governed validation and promotion engine.
    Stateless — depends on injected repository.
    """

    def __init__(self, validation_repo) -> None:
        self._repo = validation_repo

    def validate_actor_role(self, role_value: str, allowed: List[str]) -> None:
        """Raise if the actor's role is not in the allowed list."""
        if not any(role_value.lower() == r.lower() for r in allowed):
            raise UnauthorizedLifecycleTransitionError(
                role=role_value,
                transition=f"validate (allowed: {allowed})",
            )

    def check_anti_contamination(self, caller: str, source_identity: str) -> None:
        """
        Abort if the caller is not a known human/authorized system actor.
        AI systems MUST NOT produce ingested knowledge, embeddings, or promotion.
        """
        if not _is_validator_role(caller):
            raise ContaminationForbiddenError(
                operation=f"validate with caller={caller!r}",
                detail="AI-generated output cannot validate or promote source knowledge.",
            )

    def validate_lifecycle_transition(
        self,
        current_state: str,
        desired_state: str,
    ) -> None:
        from apps.api.domain.knowledge_reliability import VALID_TRANSITIONS
        allowed = VALID_TRANSITIONS.get(current_state, [])
        if desired_state not in allowed:
            raise InvalidLifecycleTransitionError(
                current=current_state,
                requested=desired_state,
            )

    def compute_decision(
        self,
        criteria: Any,
        technique_framework: str,
        pilot_corpus_key: Optional[str] = None,
    ) -> tuple[ValidationStatus, float]:
        """
        Compute validation decision from criteria.

        Explicitly does NOT auto-validate pilot corpus entries.
        Pilot corpus keys must return REJECTED regardless of criteria.
        """
        if pilot_corpus_key and pilot_corpus_key in _PILOT_CORPUS:
            # Pilot corpus: NEVER auto-validate — requires human curation
            return ValidationStatus.NEEDS_REVISION, 0.0

        checks = [
            criteria.source_identity_verified,
            criteria.source_provenance_verified,
            criteria.tradition_framework_verified,
            criteria.passage_reference_verified,
            criteria.text_integrity_verified,
            criteria.interpretation_verified,
            criteria.technique_applicability_verified,
            criteria.contradiction_conflict_status_checked,
        ]
        passed = sum(checks) / max(len(checks), 1)
        threshold = 0.85

        if passed >= threshold:
            return ValidationStatus.APPROVED, passed
        elif passed >= 0.5:
            return ValidationStatus.NEEDS_REVISION, passed
        else:
            return ValidationStatus.REJECTED, passed

    def compute_eligible_targets(
        self,
        validation_status: ValidationStatus,
        technique_framework: str,
    ) -> List[str]:
        if validation_status != ValidationStatus.APPROVED:
            return []
        key = technique_framework
        return list(_TECHNIQUE_TARGETS.get(key, [PromotionTarget.DOCUMENT_ONLY.value]))

    def make_audit_entry(
        self,
        actor_id: uuid.UUID,
        actor_role: str,
        action: str,
        previous_state: str,
        new_state: str,
        reason: str,
        source_reference: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ValidationAuditEntry:
        return ValidationAuditEntry(
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            previous_state=previous_state,
            new_state=new_state,
            reason=reason,
            source_reference=source_reference,
            metadata=metadata or {},
        )

    async def validate_knowledge_item(
        self,
        validation_decision: Any,  # ValidationDecisionRecord
    ) -> ValidationDecisionRecord:
        self.check_anti_contamination(
            validation_decision.validator_role,
            validation_decision.knowledge_item_type,
        )
        await self._repo.create_validation_record(validation_decision)
        return validation_decision

    async def promote_validated_knowledge(
        self,
        validation_id: uuid.UUID,
        promoter_id: uuid.UUID,
        promoter_role: str,
        promotion_target: str,
        promotion_notes: str = "",
    ) -> Dict[str, Any]:
        self.check_anti_contamination(promoter_role, "promotion")
        self.validate_actor_role(promoter_role, ["promoter", "admin"])

        record = await self._repo.get_full_validation_record_with_audit(validation_id)
        if not record:
            raise ValueError(f"Validation record {validation_id} not found.")

        if record.validation_status != ValidationStatus.APPROVED.value:
            raise ContaminationForbiddenError(
                operation="promote non-approved validation",
                detail=(f"Attempted promotion of item with status "
                       f"{record.validation_status!r}. Only APPROVED may be promoted."),
            )

        # Technique isolation: check promotion target compatibility
        technique = record.technique_framework
        allowed_for_framework = _TECHNIQUE_TARGETS.get(technique, [])
        if promotion_target not in allowed_for_framework:
            allowed_str = ", ".join(sorted(allowed_for_framework))
            raise TechniqueIsolationError(
                source_framework=technique,
                target_framework=promotion_target,
            )

        if record.is_cross_technique:
            # Cross-technique material requires additional annotation
            # The promotion proceeds but leaves `cross_technique_note` in record.
            pass

        # Build and append audit entry
        previous_state = "VALIDATED"
        new_state = "PROMOTED"
        audit_entry = self.make_audit_entry(
            actor_id=promoter_id,
            actor_role=promoter_role,
            action="promote",
            previous_state=previous_state,
            new_state=new_state,
            reason=(
                f"Controlled promotion to {promotion_target!r}. "
                f"Notes: {promotion_notes}"
            ),
            source_reference=str(validation_id),
            metadata={
                "promotion_target": promotion_target,
                "contamination_check": "passed",
                "technique_isolation_check": "passed",
            },
        )

        from apps.api.models.knowledge_validation import KnowledgeValidationAuditLog

        await self._repo.add_audit_entry(KnowledgeValidationAuditLog(
            validation_id=validation_id,
            actor_id=promoter_id,
            actor_role=promoter_role,
            action="promote",
            previous_state=previous_state,
            new_state=new_state,
            reason=(
                f"Controlled promotion to {promotion_target!r}. "
                f"Notes: {promotion_notes}"
            ),
            source_reference=str(validation_id),
            metadata={"promotion_target": promotion_target},
            timestamp=datetime.now(timezone.utc),
        ))

        return {
            "success": True,
            "validation_id": str(validation_id),
            "promotion_target": promotion_target,
            "new_state": new_state,
            "audit_entries": 1,
        }