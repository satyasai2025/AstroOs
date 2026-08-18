"""
AstroOS — Technique Intelligence Router

Adapter-only HTTP surface over the generic Technique framework. It validates
input, orchestrates the pipeline/engine/repository, and maps domain objects to
HTTP — no astrology and no rule logic live here.

Endpoints
---------
  GET    /techniques                    list current techniques (code + persisted)
  GET    /techniques/{id}               one technique (rules, provenance, sources)
  POST   /techniques/import             import a technique through the pipeline
  POST   /techniques/{id}/execute       run a technique against supplied Facts

Techniques come from two places, unified here: in-code fixtures (registered on
import of services.techniques, e.g. Eye Health) and rows persisted in
PostgreSQL by the import pipeline. `_ensure_loaded` reconstructs the persisted
ones into the runtime registries so the untouched RuleEngine/TechniqueEngine can
execute them with no per-technique Python module.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import get_db_session
from apps.api.domain.facts import Fact
from apps.api.domain.technique import TechniqueDefinition
from apps.api.domain.technique_import import SourceType, TechniqueSource
from apps.api.repositories.technique_repository import TechniqueRepository
from apps.api.schemas.prediction_evidence import (
    PredictionConfidenceSchema,
    PredictionEvidenceSchema,
    PredictionReasonSchema,
    PredictionRuleSchema,
)
from apps.api.schemas.technique import (
    InputAvailabilitySchema,
    RuleRefSchema,
    TechniqueDetail,
    TechniqueEvaluateChartRequest,
    TechniqueEvaluateChartResponse,
    TechniqueEvaluationItem,
    TechniqueExecuteRequest,
    TechniqueExecuteResponse,
    TechniqueImportRequest,
    TechniqueImportResponse,
    TechniqueListResponse,
    TechniqueSummary,
    TriggerSchema,
    ValidationCaseSchema,
)
from apps.api.services import technique_registry
from apps.api.services.ai_engine import AIEngine
from apps.api.services.fact_registry import FactRegistry
from apps.api.services.technique_engine import TechniqueEngine, to_prediction_evidence
from apps.api.services.technique_resolver import TechniqueResolver
from apps.api.services.technique_import_pipeline import (
    TechniqueImportPipeline,
    ValidationSample,
    persist_import,
)
# Importing this registers the bundled code fixtures (Eye Health) + their rules.
import apps.api.services.techniques  # noqa: F401

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/techniques", tags=["techniques"])


# ── mappers ───────────────────────────────────────────────────────────────────


def _summary(t: TechniqueDefinition) -> TechniqueSummary:
    return TechniqueSummary(
        technique_id=t.technique_id, name=t.name, version=t.version,
        tradition=t.tradition, objective=t.objective,
        provenance=t.provenance.value, status=t.status,
        rule_count=len(t.rule_refs),
    )


def _detail(t: TechniqueDefinition) -> TechniqueDetail:
    return TechniqueDetail(
        **_summary(t).model_dump(),
        description=t.description,
        source_references=list(t.source_references),
        required_inputs=list(t.required_inputs),
        dependencies=list(t.dependencies),
        unresolved_inconsistencies=list(t.unresolved_inconsistencies),
        rules=[
            RuleRefSchema(
                rule_id=r.rule_id, rule_version=r.rule_version, role=r.role.value,
                provenance=r.provenance.value, weight=r.weight,
                source_reference=r.source_reference, active=r.active,
            )
            for r in t.rule_refs
        ],
    )


# ── endpoints ─────────────────────────────────────────────────────────────────


@router.get("", response_model=TechniqueListResponse)
async def list_techniques(
    session: AsyncSession = Depends(get_db_session),
) -> TechniqueListResponse:
    repo = TechniqueRepository(session)
    # Load persisted techniques (and their rule bodies) into the registry.
    for persisted in await repo.list_current():
        if technique_registry.get_technique(persisted.technique_id, persisted.version) is None:
            model = await repo.get_current_model(persisted.technique_id)
            if model is not None:
                # register_from_model wires rules + technique into registries
                from apps.api.repositories.technique_repository import register_from_model
                register_from_model(model)
    # Unified, current-version-only view.
    latest: dict[str, TechniqueDefinition] = {}
    for t in technique_registry.all_techniques():
        cur = latest.get(t.technique_id)
        if cur is None or t.version > cur.version:
            latest[t.technique_id] = t
    return TechniqueListResponse(
        techniques=sorted(
            (_summary(t) for t in latest.values()), key=lambda s: s.technique_id
        )
    )


async def _load_technique(
    technique_id: str, session: AsyncSession, version: int | None = None
) -> TechniqueDefinition:
    """Registry first (code fixtures); fall back to reconstructing from DB."""
    t = technique_registry.get_technique(technique_id, version)
    if t is not None:
        return t
    repo = TechniqueRepository(session)
    if version is None:
        t = await repo.load_and_register_current(technique_id)
    else:
        t = await repo.get_version(technique_id, version)
    if t is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Technique {technique_id!r} not found.",
        )
    return t


@router.get("/{technique_id}", response_model=TechniqueDetail)
async def get_technique(
    technique_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> TechniqueDetail:
    return _detail(await _load_technique(technique_id, session))


@router.post("/import", response_model=TechniqueImportResponse)
async def import_technique(
    body: TechniqueImportRequest,
    session: AsyncSession = Depends(get_db_session),
) -> TechniqueImportResponse:
    try:
        source_type = SourceType(body.source_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown source_type {body.source_type!r}.",
        )
    source = TechniqueSource(
        source_type=source_type, reference=body.reference,
        excerpt=body.excerpt, payload=body.payload,
    )
    samples = tuple(
        ValidationSample(
            label=s.label,
            facts=_facts_from_dict(s.facts),
            expect_triggered=s.expect_triggered,
        )
        for s in body.samples
    )
    try:
        result = TechniqueImportPipeline().run(source, samples=samples)
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Import failed: {exc}",
        )

    persisted_id: uuid.UUID | None = None
    if body.persist:
        model = await persist_import(session, result)
        persisted_id = model.id

    return TechniqueImportResponse(
        technique=_detail(result.technique),
        persisted=body.persist,
        persisted_id=persisted_id,
        validation=[
            ValidationCaseSchema(
                label=v.label, triggered_primary=v.triggered_primary,
                match_status=v.match_status, confidence=v.confidence,
            )
            for v in result.validation
        ],
    )


@router.post("/{technique_id}/execute", response_model=TechniqueExecuteResponse)
async def execute_technique(
    technique_id: str,
    body: TechniqueExecuteRequest,
    session: AsyncSession = Depends(get_db_session),
) -> TechniqueExecuteResponse:
    technique = await _load_technique(technique_id, session, body.version)
    facts = _facts_from_dict(body.facts)
    result = TechniqueEngine().execute(technique, facts)
    return TechniqueExecuteResponse(
        technique_id=result.technique_id,
        technique_version=result.technique_version,
        confidence=result.confidence,
        confidence_basis=result.confidence_basis,
        triggers=[
            TriggerSchema(
                rule_id=t.rule_id, rule_name=t.rule_name, role=t.role.value,
                status=t.status.value, provenance=t.provenance.value,
                matched_conditions=list(t.matched_conditions),
                failed_conditions=list(t.failed_conditions),
                missing_facts=list(t.missing_facts),
                explanation=t.explanation,
            )
            for t in result.triggers
        ],
        inputs=[
            InputAvailabilitySchema(fact_key=i.fact_key, availability=i.availability.value)
            for i in result.inputs
        ],
        evidence=list(result.evidence),
        unresolved_inconsistencies=list(result.unresolved_inconsistencies),
        prediction=_prediction_schema(technique, result),
    )


@router.post("/evaluate-chart", response_model=TechniqueEvaluateChartResponse)
async def evaluate_chart(
    body: TechniqueEvaluateChartRequest,
) -> TechniqueEvaluateChartResponse:
    """Evaluate all applicable techniques against supplied facts (from an active chart)."""
    facts = _facts_from_dict(body.facts)
    resolver = TechniqueResolver()
    techniques = resolver.resolve_applicable(facts, objective=body.objective)
    engine = TechniqueEngine()

    evaluations: list[TechniqueEvaluationItem] = []
    for tech in techniques:
        result = engine.execute(tech, facts)
        prediction = to_prediction_evidence(tech, result)
        ai_resp = AIEngine.explain_technique(tech, result)

        evaluations.append(
            TechniqueEvaluationItem(
                technique_id=tech.technique_id,
                technique_name=tech.name,
                tradition=tech.tradition,
                objective=tech.objective,
                version=tech.version,
                confidence=result.confidence,
                confidence_basis=result.confidence_basis,
                is_matched=prediction.is_matched,
                triggers=[
                    TriggerSchema(
                        rule_id=t.rule_id,
                        rule_name=t.rule_name,
                        role=t.role.value,
                        status=t.status.value,
                        provenance=t.provenance.value,
                        matched_conditions=list(t.matched_conditions),
                        failed_conditions=list(t.failed_conditions),
                        missing_facts=list(t.missing_facts),
                        explanation=t.explanation,
                    )
                    for t in result.triggers
                ],
                evidence=list(result.evidence),
                ai_explanation={
                    "title": ai_resp.title,
                    "summary": ai_resp.summary,
                    "body": ai_resp.body,
                },
            )
        )

    evaluations.sort(key=lambda e: (e.is_matched, e.confidence), reverse=True)

    return TechniqueEvaluateChartResponse(
        evaluations=evaluations,
        total_evaluated=len(evaluations),
    )


def _prediction_schema(technique: TechniqueDefinition, result) -> PredictionEvidenceSchema:
    evidence = to_prediction_evidence(technique, result)
    return PredictionEvidenceSchema(
        rule=PredictionRuleSchema(
            rule_id=evidence.rule.rule_id, name=evidence.rule.name,
            sutra_reference=evidence.rule.sutra_reference,
            rule_version=evidence.rule.rule_version,
            requires=list(evidence.rule.requires),
        ),
        is_matched=evidence.is_matched,
        triggering_conditions=list(evidence.triggering_conditions),
        reasons=[
            PredictionReasonSchema(
                description=r.description, matched_objects=list(r.matched_objects),
                is_satisfied=r.is_satisfied,
            )
            for r in evidence.reasons
        ],
        confidence=PredictionConfidenceSchema(
            score=evidence.confidence.score,
            satisfied_conditions=evidence.confidence.satisfied_conditions,
            total_conditions=evidence.confidence.total_conditions,
            basis=evidence.confidence.basis,
        ),
        explanation=evidence.explanation,
    )


def _facts_from_dict(facts: dict) -> FactRegistry:
    reg = FactRegistry()
    for key, value in facts.items():
        reg.add_fact(Fact(key=key, value=value, source="api"))
    return reg
