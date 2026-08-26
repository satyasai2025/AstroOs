"""
AstroOS — Knowledge Reliability Router

REST API endpoints for:
- Registering / querying source reliability records
- Documenting rules with complete provenance chains
- Controlled lifecycle state transitions
- Validation policy management
- Calculating independent confirmations (anti-double counting)
- Querying provenance traces and validation records
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import get_db_session
from apps.api.repositories.knowledge_reliability_repository import (
    KnowledgeReliabilityRepository,
)

from apps.api.domain.knowledge_reliability import (
    ActorRole,
    EvidenceLevel,
    KnowledgeReliabilityError,
    ReviewStatus,
    RuleLifecycleState,
    RuleValidationSummary,
    ScholarlyEvaluation,
    SourceProvenance,
    SourceReliabilityTier,
    TechniqueFramework,
    UnauthorizedLifecycleTransitionError,
    ValidationPolicy,
    ValidationPolicyViolationError,
)
from apps.api.schemas.knowledge_reliability import (
    DocumentRuleRequest,
    EvidenceFamilyRegisterRequest,
    EvidenceFamilyResponse,
    IndependentConfirmationsRequest,
    IndependentConfirmationsResponse,
    RegisterSourceRequest,
    RuleProvenanceSchema,
    RuleReliabilityResponse,
    RuleValidationSummarySchema,
    ScholarlyEvaluationSchema,
    SourceProvenanceSchema,
    SourceReliabilityResponse,
    TransitionLifecycleRequest,
    ValidationPolicySchema,
)
from apps.api.services.knowledge_reliability_engine import KnowledgeReliabilityEngine

router = APIRouter(prefix="/knowledge/reliability", tags=["Knowledge Reliability"])

# Engine singleton instance for runtime operations
_engine = KnowledgeReliabilityEngine()


def get_reliability_engine() -> KnowledgeReliabilityEngine:
    return _engine


# ── Serializers ──────────────────────────────────────────────────────────────

def _serialize_source(r) -> SourceReliabilityResponse:
    return SourceReliabilityResponse(
        source_id=r.source_id,
        source_name=r.source_name,
        tier=r.tier.value,
        provenance=SourceProvenanceSchema(
            edition_title=r.provenance.edition_title,
            publisher=r.provenance.publisher,
            publication_year=r.provenance.publication_year,
            editor_or_translator=r.provenance.editor_or_translator,
            manuscript_lineage=r.provenance.manuscript_lineage,
            is_critical_edition=r.provenance.is_critical_edition,
        ),
        scholarly_eval=ScholarlyEvaluationSchema(
            tradition=r.scholarly_eval.tradition,
            methodology_clarity_notes=r.scholarly_eval.methodology_clarity_notes,
            primary_commentaries=list(r.scholarly_eval.primary_commentaries),
            known_disputed_passages=list(r.scholarly_eval.known_disputed_passages),
        ),
        review_status=r.review_status.value,
        empirical_citations=list(r.empirical_citations),
        known_failures_or_contradictions=list(r.known_failures_or_contradictions),
        audit_log=list(r.audit_log),
    )


def _serialize_rule(r) -> RuleReliabilityResponse:
    val_schema = None
    if r.validation_summary:
        v = r.validation_summary
        val_schema = RuleValidationSummarySchema(
            policy_id=v.policy_id,
            cases_tested=v.cases_tested,
            applicable_cases=v.applicable_cases,
            supported_outcomes=v.supported_outcomes,
            unsupported_outcomes=v.unsupported_outcomes,
            indeterminate_cases=v.indeterminate_cases,
            counterexamples=list(v.counterexamples),
            empirical_hit_rate=v.empirical_hit_rate,
            brier_score=v.brier_score,
            dataset_id=v.dataset_id,
            dataset_version=v.dataset_version,
            benchmark_experiment_id=v.benchmark_experiment_id,
            validated_at=v.validated_at.isoformat(),
            validated_by_actor_id=v.validated_by_actor_id,
        )

    return RuleReliabilityResponse(
        rule_id=r.rule_id,
        rule_name=r.rule_name,
        technique_framework=r.technique_framework.value,
        provenance=RuleProvenanceSchema(
            source_id=r.provenance.source_id,
            passage_reference=r.provenance.passage_reference,
            original_text_excerpt=r.provenance.original_text_excerpt,
            extraction_method=r.provenance.extraction_method,
            extracted_by_actor_id=r.provenance.extracted_by_actor_id,
            extracted_by_role=r.provenance.extracted_by_role.value,
            rule_definition_id=r.provenance.rule_definition_id,
            source_name=r.provenance.source_name,
            extracted_at=r.provenance.extracted_at.isoformat(),
        ),
        evidence_family_id=r.evidence_family_id,
        lifecycle_state=r.lifecycle_state.value,
        evidence_level=r.evidence_level.value,
        validation_summary=val_schema,
        conflict_ids=list(r.conflict_ids),
        review_history=list(r.review_history),
        canonical_signoff_by=r.canonical_signoff_by,
        canonical_signoff_at=r.canonical_signoff_at.isoformat() if r.canonical_signoff_at else None,
    )


# ── Endpoints: Sources ───────────────────────────────────────────────────────

@router.post("/sources/register", response_model=SourceReliabilityResponse, status_code=status.HTTP_201_CREATED)
def register_source(
    req: RegisterSourceRequest,
    engine: KnowledgeReliabilityEngine = Depends(get_reliability_engine),
):
    """Registers a multidimensional source reliability record."""
    try:
        tier_enum = SourceReliabilityTier(req.tier)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid source reliability tier: {req.tier}")

    try:
        status_enum = ReviewStatus(req.review_status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid review status: {req.review_status}")

    prov = SourceProvenance(
        edition_title=req.provenance.edition_title,
        publisher=req.provenance.publisher,
        publication_year=req.provenance.publication_year,
        editor_or_translator=req.provenance.editor_or_translator,
        manuscript_lineage=req.provenance.manuscript_lineage,
        is_critical_edition=req.provenance.is_critical_edition,
    )
    scholarly = ScholarlyEvaluation(
        tradition=req.scholarly_eval.tradition,
        methodology_clarity_notes=req.scholarly_eval.methodology_clarity_notes,
        primary_commentaries=tuple(req.scholarly_eval.primary_commentaries),
        known_disputed_passages=tuple(req.scholarly_eval.known_disputed_passages),
    )

    rec = engine.register_source(
        source_id=req.source_id,
        source_name=req.source_name,
        tier=tier_enum,
        provenance=prov,
        scholarly_eval=scholarly,
        review_status=status_enum,
        empirical_citations=req.empirical_citations,
        known_failures_or_contradictions=req.known_failures_or_contradictions,
    )
    return _serialize_source(rec)


@router.get("/sources", response_model=List[SourceReliabilityResponse])
async def list_sources(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    tier: str | None = Query(None, description="Filter by SourceReliabilityTier value."),
    review_status: str | None = Query(None, description="Filter by ReviewStatus value."),
    session: AsyncSession = Depends(get_db_session),
) -> List[SourceReliabilityResponse]:
    """
    List registered sources from the DATABASE.

    Deliberately DB-backed rather than reading the in-memory
    KnowledgeReliabilityEngine: sources registered by seed scripts live in
    `knowledge_source_reliabilities`, and the process-local engine cannot see
    them. Without this, a registered source was undiscoverable over HTTP —
    `GET /sources/{id}` required already knowing the id.

    Tier and review_status are returned AS STORED; this endpoint never
    re-rates a source.
    """
    repo = KnowledgeReliabilityRepository(session)
    records = await repo.list_source_reliabilities(
        limit=limit, offset=offset, tier=tier, review_status=review_status
    )
    return [_serialize_source(r) for r in records]


@router.get("/sources/{source_id}", response_model=SourceReliabilityResponse)
async def get_source(
    source_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    engine: KnowledgeReliabilityEngine = Depends(get_reliability_engine),
):
    """
    Fetch one source. Checks the in-memory engine first (so records registered
    in-process during this run, and test fixtures, keep working), then falls
    back to the database for persisted records.
    """
    rec = engine.get_source(source_id)
    if not rec:
        rec = await KnowledgeReliabilityRepository(session).get_source_reliability(
            source_id
        )
    if not rec:
        raise HTTPException(status_code=404, detail="Source reliability record not found.")
    return _serialize_source(rec)


# ── Endpoints: Rules & Provenance ─────────────────────────────────────────────

@router.post("/rules/document", response_model=RuleReliabilityResponse, status_code=status.HTTP_201_CREATED)
def document_rule(
    req: DocumentRuleRequest,
    engine: KnowledgeReliabilityEngine = Depends(get_reliability_engine),
):
    """Documents an extracted rule with complete provenance lineage."""
    try:
        framework_enum = TechniqueFramework(req.technique_framework)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid technique framework: {req.technique_framework}")

    try:
        actor_role_enum = ActorRole(req.extracted_by_role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid actor role: {req.extracted_by_role}")

    try:
        rec = engine.document_rule(
            rule_id=req.rule_id,
            rule_name=req.rule_name,
            technique_framework=framework_enum,
            source_id=req.source_id,
            passage_reference=req.passage_reference,
            original_text_excerpt=req.original_text_excerpt,
            extracted_by_actor_id=req.extracted_by_actor_id,
            extracted_by_role=actor_role_enum,
            rule_definition_id=req.rule_definition_id,
            extraction_method=req.extraction_method,
            evidence_family_id=req.evidence_family_id,
            source_name=req.source_name,
        )
        return _serialize_rule(rec)
    except KnowledgeReliabilityError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rules/{rule_id}", response_model=RuleReliabilityResponse)
def get_rule(
    rule_id: str,
    engine: KnowledgeReliabilityEngine = Depends(get_reliability_engine),
):
    rec = engine.get_rule(rule_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Rule reliability record not found.")
    return _serialize_rule(rec)


# ── Endpoints: Lifecycle Transitions ──────────────────────────────────────────

@router.post("/rules/{rule_id}/transition", response_model=RuleReliabilityResponse)
def transition_lifecycle(
    rule_id: str,
    req: TransitionLifecycleRequest,
    engine: KnowledgeReliabilityEngine = Depends(get_reliability_engine),
):
    """Executes a governed state transition on a rule."""
    try:
        target_state_enum = RuleLifecycleState(req.target_state)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid target lifecycle state: {req.target_state}")

    try:
        actor_role_enum = ActorRole(req.actor_role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid actor role: {req.actor_role}")

    val_summary = None
    if req.validation_summary:
        vs = req.validation_summary
        val_summary = RuleValidationSummary(
            rule_id=rule_id,
            policy_id=vs.policy_id,
            cases_tested=vs.cases_tested,
            applicable_cases=vs.applicable_cases,
            supported_outcomes=vs.supported_outcomes,
            unsupported_outcomes=vs.unsupported_outcomes,
            indeterminate_cases=vs.indeterminate_cases,
            counterexamples=tuple(vs.counterexamples),
            empirical_hit_rate=vs.empirical_hit_rate,
            brier_score=vs.brier_score,
            dataset_id=vs.dataset_id,
            dataset_version=vs.dataset_version,
            benchmark_experiment_id=vs.benchmark_experiment_id,
            validated_by_actor_id=vs.validated_by_actor_id,
        )

    try:
        rec = engine.transition_lifecycle(
            rule_id=rule_id,
            target_state=target_state_enum,
            actor_id=req.actor_id,
            actor_role=actor_role_enum,
            notes=req.notes,
            validation_summary=val_summary,
            policy_id=req.policy_id,
        )
        return _serialize_rule(rec)
    except UnauthorizedLifecycleTransitionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except KnowledgeReliabilityError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Endpoints: Evidence Families & Anti-Double Counting ───────────────────────

@router.post("/families/register", response_model=EvidenceFamilyResponse, status_code=status.HTTP_201_CREATED)
def register_family(
    req: EvidenceFamilyRegisterRequest,
    engine: KnowledgeReliabilityEngine = Depends(get_reliability_engine),
):
    try:
        tradition_enum = TechniqueFramework(req.tradition)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid tradition: {req.tradition}")

    fam = engine.register_evidence_family(
        family_id=req.family_id,
        name=req.name,
        underlying_principle=req.underlying_principle,
        tradition=tradition_enum,
        member_rule_ids=req.member_rule_ids,
        max_independent_dof=req.max_independent_dof,
    )
    return EvidenceFamilyResponse(
        family_id=fam.family_id,
        name=fam.name,
        underlying_principle=fam.underlying_principle,
        tradition=fam.tradition.value,
        member_rule_ids=list(fam.member_rule_ids),
        max_independent_dof=fam.max_independent_dof,
    )


@router.post("/families/independent-confirmations", response_model=IndependentConfirmationsResponse)
def calculate_independent_confirmations(
    req: IndependentConfirmationsRequest,
    engine: KnowledgeReliabilityEngine = Depends(get_reliability_engine),
):
    res = engine.calculate_independent_confirmations(req.rule_ids)
    return IndependentConfirmationsResponse(**res)


# ── Endpoints: Traceability & Querying ────────────────────────────────────────

@router.get("/rules/{rule_id}/provenance-trace")
def get_rule_provenance_trace(
    rule_id: str,
    engine: KnowledgeReliabilityEngine = Depends(get_reliability_engine),
):
    try:
        return engine.get_rule_provenance_trace(rule_id)
    except KnowledgeReliabilityError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/rules/{rule_id}/validation-status")
def get_rule_validation_status(
    rule_id: str,
    engine: KnowledgeReliabilityEngine = Depends(get_reliability_engine),
):
    try:
        return engine.get_rule_validation_status(rule_id)
    except KnowledgeReliabilityError as e:
        raise HTTPException(status_code=404, detail=str(e))
