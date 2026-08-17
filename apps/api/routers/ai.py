"""
AstroOS — AI Router (Module 24 — HTTP surface)

HTTP adapter layer over AIEngine's template-based generators. AIEngine
itself never calls another engine — this router computes the domain
object each generator needs (D1Chart, YogaResult, DashaPeriod, transit
readings) the same way the other routers do, then calls the generator
directly (AIEngine.chart_summary / explain_yoga / interpret_dasha /
read_transit / answer_question) rather than round-tripping through the
ExplanationRequest/source_data dispatcher, which exists for callers that
already hold the domain object in hand.

See schemas/ai.py's module docstring for the three generators
(verification_report, research_insight, recommendation) intentionally
left unwired.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import get_db_session, get_ephemeris_wrapper
from apps.api.schemas.ai import (
    AIResponseSchema,
    ChartSummaryRequest,
    CitationResponse,
    DashaInterpretationRequest,
    ExplainRuleRequest,
    KnowledgeQuestionRequest,
    QuestionRequest,
    TransitReadingRequest,
    YogaExplanationRequest,
)
from apps.api.schemas.explanation import ExplanationResponse
from apps.api.services.ai_engine import AIEngine
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.dasha_lookup import find_active_dasha_chain
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.explanation_engine import ExplanationEngine
from apps.api.services.fact_builder import FactBuilder
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.knowledge_retrieval import answer_from_knowledge_base
from apps.api.services.rule_engine import RuleEngine
from apps.api.services.transit_engine import TransitEngine
from apps.api.services.yoga_engine import YogaEngine
from apps.api.services.yoga_registry import get_yoga

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI"])


def _response(r) -> AIResponseSchema:
    return AIResponseSchema(
        response_type=r.response_type, title=r.title, summary=r.summary, body=r.body,
        citations=[
            CitationResponse(source=c.source, reference=c.reference, text=c.text, relevance=c.relevance)
            for c in r.citations
        ],
        sources=list(r.sources), recommendations=list(r.recommendations),
        confidence=r.confidence, version=r.version,
    )


async def _build_chart(body, wrapper: EphemerisWrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    try:
        return await asyncio.to_thread(
            horoscope_engine.generate_d1,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error computing chart for AI endpoint: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute chart.",
        )


@router.post("/chart-summary", response_model=AIResponseSchema)
async def chart_summary(
    body: ChartSummaryRequest, wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper)
) -> AIResponseSchema:
    chart = await _build_chart(body, wrapper)
    return _response(AIEngine.chart_summary(chart, style=body.style))


@router.post("/explain-yoga/{yoga_id}", response_model=AIResponseSchema)
async def explain_yoga(
    body: YogaExplanationRequest,
    yoga_id: str,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> AIResponseSchema:
    if get_yoga(yoga_id) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown yoga_id '{yoga_id}'. See GET /yoga/catalog for valid IDs.",
        )
    chart = await _build_chart(body, wrapper)
    try:
        result = await asyncio.to_thread(YogaEngine().evaluate_one, chart, yoga_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error evaluating yoga %s for AI endpoint: %s", yoga_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate yoga {yoga_id}.",
        )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Yoga {yoga_id} evaluator returned no result.",
        )
    return _response(AIEngine.explain_yoga(result))


@router.post("/interpret-dasha", response_model=AIResponseSchema)
async def interpret_dasha(
    body: DashaInterpretationRequest, wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper)
) -> AIResponseSchema:
    dasha_engine = DashaEngine(wrapper)
    compute_fn = getattr(dasha_engine, f"compute_{body.system}")
    try:
        tree = await asyncio.to_thread(
            compute_fn,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error computing dasha tree for AI endpoint: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute dasha tree.",
        )

    target = body.target_date or date.today()
    chain = find_active_dasha_chain(tree, target)
    if not chain:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No active {body.system} period found for {target}.",
        )

    chart = await _build_chart(body, wrapper)
    return _response(AIEngine.interpret_dasha(chain[-1], chart))


@router.post("/read-transit", response_model=AIResponseSchema)
async def read_transit(
    body: TransitReadingRequest, wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper)
) -> AIResponseSchema:
    chart = await _build_chart(body, wrapper)
    transit_dt = body.transit_datetime_utc or datetime.now(timezone.utc)
    try:
        transits = await asyncio.to_thread(
            TransitEngine(wrapper).compute_transit, chart, transit_dt
        )
    except Exception as exc:
        logger.exception("Error computing transits for AI endpoint: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute transits.",
        )
    return _response(AIEngine.read_transit(tuple(transits)))


@router.post("/answer-question", response_model=AIResponseSchema)
async def answer_question(
    body: QuestionRequest, wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper)
) -> AIResponseSchema:
    chart = await _build_chart(body, wrapper)
    return _response(AIEngine.answer_question(body.question, chart))


@router.post("/knowledge-qa", response_model=AIResponseSchema)
async def knowledge_qa(
    body: KnowledgeQuestionRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AIResponseSchema:
    """
    Answer a general astrology knowledge question (not tied to a
    specific birth chart) grounded in AstroOS's own classical-text
    knowledge base (Phase IV, IV.3.1 — RAG). Requires AI_BACKEND=
    local_llm and at least one embedded verse/rule (see
    scripts/backfill_embeddings.py); otherwise returns an explicit
    "no matching source found" response rather than an ungrounded
    guess — see docs/rag-knowledge-search.md.
    """
    return _response(await answer_from_knowledge_base(session, body.question))


@router.post("/explain-rule/{rule_id}", response_model=ExplanationResponse)
async def explain_rule(
    rule_id: str,
    body: ExplainRuleRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> ExplanationResponse:
    """
    Explain why a specific rule fired or didn't fire. Computes the chart,
    builds facts, evaluates the single rule, returns structured explanation.
    """
    RULE_ALIAS_MAP = {
        "GAJA-001": "RULE-YOGA-003",
        "DHANA-001": "RULE-YOGA-008",
        "RAJA-001": "RULE-YOGA-004",
        "BUDHA-001": "RULE-YOGA-007",
        "EYE-001": "RULE-HOUSE-002",
        "TRN-SJ-001": "RULE-TRANSIT-001",
    }
    normalized_rule_id = rule_id.upper().strip()
    target_rule_id = RULE_ALIAS_MAP.get(normalized_rule_id, rule_id)

    rule_def = get_rule_def(target_rule_id) or get_rule_def(rule_id)
    if rule_def is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown rule_id '{rule_id}'.",
        )

    chart = await _build_chart(body, wrapper)
    transit_dt = datetime.now(timezone.utc)

    from apps.api.services.shadbala_engine import ShadbalaEngine
    from apps.api.services.ashtakavarga_engine import AshtakavargaEngine

    facts = FactBuilder(
        shadbala_engine=ShadbalaEngine(),
        ashtakavarga_engine=AshtakavargaEngine(),
        transit_engine=TransitEngine(wrapper),
    ).build_facts(chart, transit_dt)

    rule_result = RuleEngine().evaluate(rule_def.rule_id, facts)

    explanation = ExplanationEngine.explain_rule_result(rule_result, facts)
    from apps.api.schemas.explanation import (
        ConditionExplanationResponse, ExplanationResponse as ExpResp,
    )
    return ExplanationResponse(
        rule_id=explanation.rule_id,
        rule_name=explanation.rule_name,
        rule_category=explanation.rule_category,
        summary=explanation.summary,
        matched=explanation.matched,
        conditions=[
            ConditionExplanationResponse(
                condition_text=c.condition_text,
                satisfied=c.satisfied,
                fact_key=c.fact_key,
                actual_value=str(c.actual_value),
                expected_value=str(c.expected_value),
                operator=c.operator,
            ) for c in explanation.conditions
        ],
        derived_facts=dict(explanation.derived_facts),
        derived_fact_sources=dict(explanation.derived_fact_sources),
        locked_facts=list(explanation.locked_facts),
        confidence=explanation.confidence,
        explanation_text=explanation.explanation_text,
    )
