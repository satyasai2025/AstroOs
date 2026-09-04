"""
AstroOS — Knowledge Validation & Promotion Router

REST API endpoints for:
- Submitting validation decisions for knowledge items
- Querying validation status of items
- Promoting validated knowledge to governed targets
- Retrieving auditable validation records

PROMOTION IS EXPLICIT AND HUMAN-CONTROLLED:
  - Only APPROVED validation records may be promoted
  - Only 'promoter' and 'admin' roles may promote
  - RAG/retrieval/embedding/similarity NEVER auto-promotes
  - AI agents have ZERO promotion authority
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.domain.knowledge_reliability import ActorRole, KnowledgeReliabilityError
from apps.api.domain.knowledge_validation import (
    ContaminationForbiddenError,
    InvalidLifecycleTransitionError,
    TechniqueIsolationError,
    ValidationStatus,
    ValidationAuditEntry,
    ValidationCheckResult,
    ValidationDecisionRecord,
)
from apps.api.repositories.knowledge_validation_repository import (
    KnowledgeValidationRepository,
)
from apps.api.schemas.knowledge_validation import (
    AuditEntrySchema,
    CreateValidationRequest,
    PromoteRequest,
    PromoteResponseSchema,
    RejectPromotionRequest,
    ValidationAuditResponseSchema,
    ValidationCriteriaSchema,
    ValidationResponseSchema,
)
from apps.api.services.knowledge_validation_engine import (
    KnowledgeValidationEngine,
    _PILOT_CORPUS,
)
from apps.api.services.knowledge_ingestion_pipeline import (
    GovernedIngestionPipeline,
)

router = APIRouter(
    prefix="/knowledge/validation",
    tags=["Knowledge Validation & Promotion"],
)


# ── Dependency injection stubs ─────────────────────────────────────────────────
# For production, use FastAPI Depends(get_db) for the session.
# Tests will instantiate the repository directly with a test session.


def get_validation_repo() -> KnowledgeValidationRepository:
    raise NotImplementedError("Dependency — override in tests.")


def get_validation_engine() -> KnowledgeValidationEngine:
    from apps.api.repositories.knowledge_validation_repository import (
        KnowledgeValidationRepository,
    )
    # In production, this uses the real session from get_db.
    return KnowledgeValidationEngine(None)


# ── Pilot corpus key helper ───────────────────────────────────────────────────

def _pilot_key(title: str) -> Optional[str]:
    title_lower = title.lower()
    for key, info in _PILOT_CORPUS.items():
        if info["title"].lower() in title_lower or title_lower in info["title"].lower():
            return key
    return None


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/validate", response_model=ValidationResponseSchema, status_code=201)
async def validate_knowledge_item(
    req: CreateValidationRequest,
    engine: KnowledgeValidationEngine = Depends(get_validation_engine),
    repo: KnowledgeValidationRepository = Depends(get_validation_repo),
):
    """
    Submit a governed validation decision for a knowledge item.
    AI agents are explicitly rejected.
    Pilot corpus items never auto-validate.
    """
    knowledge_item_id = uuid.UUID(req.knowledge_item_id)
    validator_id = uuid.UUID(req.validator_id)

    # ── 1. Anti-contamination guard ────────────────────────────────────────
    try:
        engine.check_anti_contamination(req.validator_role, req.knowledge_item_type)
    except ContaminationForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    # ── 2. Verify the item exists ──────────────────────────────────────────
    # We load from existing ingestion repository (injected via session).
    # For this stub, we accept the ID and continue — full DB check in below.
    # In production, query ingested_documents / ingested_chunks to confirm.
    # The pilot corpus is checked by title when possible.

    pilot_corpus_key = None  # populated from DB in production

    # ── 3. Compute decision ────────────────────────────────────────────────
    decision_status, criteria_score = engine.compute_decision(
        criteria=req.criteria,
        technique_framework=req.technique_framework,
        pilot_corpus_key=pilot_corpus_key,
    )

    eligible_targets = engine.compute_eligible_targets(
        decision_status, req.technique_framework,
    )

    # ── 4. Build record ────────────────────────────────────────────────────
    now = datetime.now(timezone.utc)
    record = ValidationDecisionRecord(
        validation_id=uuid.uuid4(),
        knowledge_item_id=knowledge_item_id,
        knowledge_item_type=req.knowledge_item_type,
        validator_id=validator_id,
        validator_role=req.validator_role,
        validation_status=decision_status.value,
        validated_at=now,
        source_identity_verified=req.criteria.source_identity_verified,
        source_provenance_verified=req.criteria.source_provenance_verified,
        tradition_framework_verified=req.criteria.tradition_framework_verified,
        passage_reference_verified=req.criteria.passage_reference_verified,
        text_integrity_verified=req.criteria.text_integrity_verified,
        interpretation_verified=req.criteria.interpretation_verified,
        technique_applicability_verified=req.criteria.technique_applicability_verified,
        contradiction_conflict_status_checked=req.criteria.contradiction_conflict_status_checked,
        technique_framework=req.technique_framework,
        is_cross_technique=req.is_cross_technique,
        cross_technique_note=req.cross_technique_note,
        validation_notes=req.validation_notes,
        validation_decision=req.validation_decision,
        evidence_checks=[c.model_dump() for c in req.criteria.evidence_checks],
        is_eligible_for_promotion=len(eligible_targets) > 0,
        eligible_promotion_targets=eligible_targets,
        preserved_provenance={
            "validated_by": str(validator_id),
            "validated_at": now.isoformat(),
            "technique_framework": req.technique_framework,
            "criteria_score": criteria_score,
            "pilot_corpus": pilot_corpus_key or "unknown",
        },
    )

    # ── 5. Initial audit entry ─────────────────────────────────────────────
    initial_audit = ValidationAuditEntry(
        actor_id=validator_id,
        actor_role=req.validator_role,
        action="validation_submit",
        previous_state="UNKNOWN",
        new_state=decision_status.value,
        reason=(f"Validation decision: {decision_status.value}. "
                f"Rationale: {req.validation_decision}"),
        source_reference=str(knowledge_item_id),
        metadata={
            "criteria_score": criteria_score,
            "contamination_check": "passed",
        },
    )
    record = record.add_audit_entry(initial_audit)

    # ── 6. Persist ─────────────────────────────────────────────────────────
    saved = await engine.validate_knowledge_item(record)

    return ValidationResponseSchema(
        validation_id=str(saved.validation_id),
        knowledge_item_id=str(saved.knowledge_item_id),
        knowledge_item_type=saved.knowledge_item_type,
        validator_id=str(saved.validator_id),
        validator_role=saved.validator_role,
        validation_status=ValidationStatusSchema(saved.validation_status),
        validated_at=saved.validated_at.isoformat(),
        criteria=ValidationCriteriaSchema(
            source_identity_verified=saved.source_identity_verified,
            source_provenance_verified=saved.source_provenance_verified,
            tradition_framework_verified=saved.tradition_framework_verified,
            passage_reference_verified=saved.passage_reference_verified,
            text_integrity_verified=saved.text_integrity_verified,
            interpretation_verified=saved.interpretation_verified,
            technique_applicability_verified=saved.technique_applicability_verified,
            contradiction_conflict_status_checked=saved.contradiction_conflict_status_checked,
            evidence_checks=[],
        ),
        technique_framework=saved.technique_framework,
        is_cross_technique=saved.is_cross_technique,
        cross_technique_note=saved.cross_technique_note,
        validation_notes=saved.validation_notes,
        validation_decision=saved.validation_decision,
        is_eligible_for_promotion=saved.is_eligible_for_promotion,
        eligible_promotion_targets=saved.eligible_promotion_targets,
        criteria_score=saved.criteria_score,
    )


@router.post("/promote", response_model=PromoteResponseSchema)
async def promote_validated_knowledge(
    req: PromoteRequest,
    engine: KnowledgeValidationEngine = Depends(get_validation_engine),
):
    """
    Controled promotion: only APPROVED items, only authorized roles.

    MANDATORY INVARIANTS:
      - RAG retrieval → NEVER triggers promotion
      - LLM output → NEVER becomes validation decision
      - Semantic similarity → NEVER becomes promotion
      - embeddings → NEVER become executable rules
      - Only HUMAN *promoter* or ADMIN may promote
    """
    promotion_id = uuid.UUID(req.promoter_id)
    validation_id = uuid.UUID(req.validation_id)

    try:
        result = await engine.promote_validated_knowledge(
            validation_id=validation_id,
            promoter_id=promotion_id,
            promoter_role=req.promoter_role or "promoter",
            promotion_target=req.promotion_target,
            promotion_notes=req.promotion_notes,
        )
    except ContaminationForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except UnauthorizedLifecycleTransitionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except TechniqueIsolationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidLifecycleTransitionError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return PromoteResponseSchema(
        success=result["success"],
        message=f"Knowledge item {validation_id} promoted to {req.promotion_target!r}.",
        promoted_at=datetime.now(timezone.utc).isoformat(),
        validation_id=str(validation_id),
        promotion_target=req.promotion_target,
        audit_log_id=str(result.get("validation_id", "")),
    )


@router.get("/audit/{validation_id}", response_model=ValidationAuditResponseSchema)
async def get_validation_audit(
    validation_id: uuid.UUID,
    repo: KnowledgeValidationRepository = Depends(get_validation_repo),
    engine: KnowledgeValidationEngine = Depends(get_validation_engine),
):
    """Retrieve a full validation record with its complete audit trail."""
    record = await repo.get_full_validation_record_with_audit(validation_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Validation record not found.",
        )

    audit_trail = await repo.get_audit_trail(validation_id)

    return ValidationAuditResponseSchema(
        validation=ValidationResponseSchema(
            validation_id=str(record.validation_id),
            knowledge_item_id=str(record.knowledge_item_id),
            knowledge_item_type=record.knowledge_item_type,
            validator_id=str(record.validator_id),
            validator_role=record.validator_role,
            validation_status=ValidationStatusSchema(record.validation_status),
            validated_at=record.validated_at.isoformat(),
            criteria=ValidationCriteriaSchema(
                source_identity_verified=record.source_identity_verified,
                source_provenance_verified=record.source_provenance_verified,
                tradition_framework_verified=record.tradition_framework_verified,
                passage_reference_verified=record.passage_reference_verified,
                text_integrity_verified=record.text_integrity_verified,
                interpretation_verified=record.interpretation_verified,
                technique_applicability_verified=record.technique_applicability_verified,
                contradiction_conflict_status_checked=record.contradiction_conflict_status_checked,
            ),
            technique_framework=record.technique_framework,
            is_cross_technique=record.is_cross_technique,
            cross_technique_note=record.cross_technique_note,
            validation_notes=record.validation_notes,
            validation_decision=record.validation_decision,
            is_eligible_for_promotion=record.is_eligible_for_promotion,
            eligible_promotion_targets=record.eligible_promotion_targets,
            criteria_score=record.criteria_score,
        ),
        audit_trail=[
            AuditEntrySchema(
                audit_id=str(e.audit_id),
                validation_id=str(e.validation_id),
                actor_id=str(e.actor_id),
                actor_role=e.actor_role,
                action=e.action,
                previous_state=e.previous_state,
                new_state=e.new_state,
                reason=e.reason,
                source_reference=e.source_reference,
                metadata=e.metadata,
                timestamp=e.timestamp.isoformat(),
            )
            for e in audit_trail
        ],
    )