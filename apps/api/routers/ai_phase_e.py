"""
AstroOS — Phase E AI Router

HTTP adapter layer over the Phase E AI components: chart comparison,
research assistant, hypothesis generation, and enhanced QA.

All endpoints require authentication (any role).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.dependencies import get_ephemeris_wrapper, get_knowledge_engine
from apps.api.schemas.ai_phase_e import (
    AvailableDomainResponse,
    AvailableDomainsResponse,
    ChartComparisonRequest,
    ChartComparisonResponse,
    ComparisonDimensionResponse,
    EnhancedQuestionRequest,
    GeneratedHypothesisResponse,
    HypothesisGenerateRequest,
    HypothesisListResponse,
    HypothesisTemplateResponse,
    HypothesisTemplatesResponse,
    ResearchAnswerResponse,
    ResearchEvidenceResponse,
    ResearchQueryRequest,
)
from apps.api.schemas.ai import AIResponseSchema, CitationResponse
from apps.api.services.chart_comparison_engine import ChartComparisonEngine
from apps.api.services.research_assistant_engine import ResearchAssistantEngine
from apps.api.services.hypothesis_generator import HypothesisGenerator
from apps.api.services.enhanced_qa_engine import EnhancedQAResponder
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.knowledge_engine import KnowledgeEngine
from apps.api.services.yoga_engine import YogaEngine
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.transit_engine import TransitEngine
from apps.api.services.shadbala_engine import ShadbalaEngine
from apps.api.domain.ai_phase_e import ResearchQuery

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI (Phase E)"])


async def _build_chart(body, wrapper: EphemerisWrapper):
    """Build a D1 chart from birth data."""
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
        logger.exception("Error computing chart for Phase E endpoint: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute chart.",
        )


def _ai_response(r) -> AIResponseSchema:
    return AIResponseSchema(
        response_type=r.response_type, title=r.title, summary=r.summary, body=r.body,
        citations=[
            CitationResponse(source=c.source, reference=c.reference, text=c.text, relevance=c.relevance)
            for c in r.citations
        ],
        sources=list(r.sources), recommendations=list(r.recommendations),
        confidence=r.confidence, version=r.version,
    )


# ── Chart Comparison ──────────────────────────────────────────────────────────

@router.post("/compare-charts", response_model=ChartComparisonResponse)
async def compare_charts(
    body: ChartComparisonRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> ChartComparisonResponse:
    """
    Compare two birth charts side-by-side across ascendant, planets,
    houses, and yogas. Returns similarity scores and compatibility insights.
    """
    # Build Chart A.
    chart_a = await _build_chart(
        _BirthDataProxy(
            birth_datetime_utc=body.birth_datetime_utc_a,
            latitude=body.latitude_a,
            longitude=body.longitude_a,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        ),
        wrapper,
    )
    # Build Chart B.
    chart_b = await _build_chart(
        _BirthDataProxy(
            birth_datetime_utc=body.birth_datetime_utc_b,
            latitude=body.latitude_b,
            longitude=body.longitude_b,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        ),
        wrapper,
    )

    # Compute yogas for both charts.
    yoga_engine = YogaEngine()
    yogas_a = await asyncio.to_thread(yoga_engine.evaluate_all, chart_a)
    yogas_b = await asyncio.to_thread(yoga_engine.evaluate_all, chart_b)

    # Run comparison.
    result = ChartComparisonEngine.compare(
        chart_a, chart_b,
        yogas_a=yogas_a, yogas_b=yogas_b,
        style=body.style,
    )

    return ChartComparisonResponse(
        summary=result.summary,
        overall_similarity=result.overall_similarity,
        key_differences=[
            ComparisonDimensionResponse(
                dimension=d.dimension, chart_a_value=d.chart_a_value,
                chart_b_value=d.chart_b_value, similarity=d.similarity,
                significance=d.significance, commentary=d.commentary,
            ) for d in result.key_differences
        ],
        key_similarities=[
            ComparisonDimensionResponse(
                dimension=d.dimension, chart_a_value=d.chart_a_value,
                chart_b_value=d.chart_b_value, similarity=d.similarity,
                significance=d.significance, commentary=d.commentary,
            ) for d in result.key_similarities
        ],
        compatibility_notes=result.compatibility_notes,
        relationship_potential=result.relationship_potential,
        timing_synergies=result.timing_synergies,
    )


# ── Research Assistant ────────────────────────────────────────────────────────

@router.post("/research-query", response_model=ResearchAnswerResponse)
async def research_query(
    body: ResearchQueryRequest,
    knowledge_engine: KnowledgeEngine = Depends(get_knowledge_engine),
) -> ResearchAnswerResponse:
    """
    Ask a natural language research question over the knowledge base.
    Searches books, verses, rules, karakatvas, and doctrinal conflicts.
    """
    query = ResearchQuery(
        question=body.question,
        domain_filter=body.domain_filter,
        tradition_filter=body.tradition_filter,
        max_results=body.max_results,
    )
    answer = await ResearchAssistantEngine.query(query, knowledge_engine)

    return ResearchAnswerResponse(
        question=answer.question,
        summary=answer.summary,
        body=answer.body,
        evidence=[
            ResearchEvidenceResponse(
                source=e.source, reference=e.reference, text=e.text,
                relevance=e.relevance, entity_type=e.entity_type,
                tradition=e.tradition,
            ) for e in answer.evidence
        ],
        related_conflicts=list(answer.related_conflicts),
        confidence=answer.confidence,
        unanswered_aspects=list(answer.unanswered_aspects),
    )


@router.get("/research-domains", response_model=AvailableDomainsResponse)
async def list_research_domains() -> AvailableDomainsResponse:
    """List all available research domains for the Research Assistant."""
    domains = ResearchAssistantEngine.available_domains()
    return AvailableDomainsResponse(
        domains=[
            AvailableDomainResponse(id=d["id"], name=d["name"], description=d["description"])
            for d in domains
        ]
    )


# ── Hypothesis Generation ─────────────────────────────────────────────────────

@router.get("/hypothesis-templates", response_model=HypothesisTemplatesResponse)
async def list_hypothesis_templates() -> HypothesisTemplatesResponse:
    """List all available hypothesis templates."""
    templates = HypothesisGenerator.get_templates()
    return HypothesisTemplatesResponse(
        templates=[
            HypothesisTemplateResponse(
                hypothesis_id=t.hypothesis_id, title=t.title,
                description=t.description, domain=t.domain,
                conditions=list(t.conditions),
                expected_outcome=t.expected_outcome,
                test_method=t.test_method,
                classical_references=list(t.classical_references),
                priority=t.priority,
            ) for t in templates
        ],
        total=len(templates),
    )


@router.post("/generate-hypotheses", response_model=HypothesisListResponse)
async def generate_hypotheses(
    body: HypothesisGenerateRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> HypothesisListResponse:
    """
    Generate testable astrological hypotheses from a birth chart.
    Each hypothesis includes chart-specific evidence and a falsifiable prediction.
    """
    chart = await _build_chart(body, wrapper)

    # Compute yogas for context.
    yoga_engine = YogaEngine()
    yogas = await asyncio.to_thread(yoga_engine.evaluate_all, chart)

    hypotheses = HypothesisGenerator.generate_for_chart(
        chart, yogas=yogas,
        domain_filter=body.domain_filter,
        max_hypotheses=body.max_hypotheses,
    )

    return HypothesisListResponse(
        hypotheses=[
            GeneratedHypothesisResponse(
                hypothesis_id=h.hypothesis_id, title=h.title,
                description=h.description, domain=h.domain,
                supporting_evidence=list(h.supporting_evidence),
                contradicting_evidence=list(h.contradicting_evidence),
                testable_prediction=h.testable_prediction,
                suggested_dataset=h.suggested_dataset,
                priority=h.priority,
                related_rules=list(h.related_rules),
                related_yogas=list(h.related_yogas),
                confidence=h.confidence,
            ) for h in hypotheses
        ],
        total=len(hypotheses),
    )


# ── Enhanced QA ───────────────────────────────────────────────────────────────

@router.post("/enhanced-qa", response_model=AIResponseSchema)
async def enhanced_qa(
    body: EnhancedQuestionRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> AIResponseSchema:
    """
    Enhanced natural-language Q&A with full chart context.
    Answers questions about ascendant, planets, yogas, dashas, transits,
    strengths, aspects, houses, nakshatras, and more.
    """
    chart = await _build_chart(body, wrapper)

    # Compute optional context based on request flags.
    yogas = None
    dasha_tree = None
    transits = None
    shadbala_totals = None

    if body.include_yogas:
        yoga_engine = YogaEngine()
        yogas = await asyncio.to_thread(yoga_engine.evaluate_all, chart)

    if body.include_dashas:
        dasha_engine = DashaEngine(wrapper)
        dasha_tree = await asyncio.to_thread(
            dasha_engine.compute_vimshottari,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )

    if body.include_transits:
        transit_engine = TransitEngine(wrapper)
        transit_dt = datetime.now(timezone.utc)
        transits = await asyncio.to_thread(
            transit_engine.compute_transit, chart, transit_dt
        )

    if body.include_strengths:
        shadbala_engine = ShadbalaEngine()
        phase1 = shadbala_engine.compute_phase1_components(chart)
        phase2 = shadbala_engine.compute_phase2_components(chart)
        sthana = shadbala_engine.compute_sthana_bala_components(chart)
        shadbala_components = {**phase1, **phase2, **sthana}
        _CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
        _SHASHTIAMSAS_PER_RUPA = 60.0
        totals = {p: 0.0 for p in _CLASSICAL_SEVEN}
        for component_results in shadbala_components.values():
            for r in component_results:
                totals[r.planet] += r.value_shashtiamsas
        shadbala_totals = {
            p: round(v / _SHASHTIAMSAS_PER_RUPA, 4) for p, v in totals.items()
        }

    result = EnhancedQAResponder.generate(
        question=body.question,
        chart=chart,
        yogas=yogas,
        dasha_tree=dasha_tree,
        transits=transits,
        shadbala_totals=shadbala_totals,
    )

    return _ai_response(result)


# ── Helper: proxy object to reuse _build_chart ────────────────────────────────

class _BirthDataProxy:
    """Minimal proxy to make _build_chart work with different field names."""
    def __init__(self, birth_datetime_utc, latitude, longitude, ayanamsa, house_system):
        self.birth_datetime_utc = birth_datetime_utc
        self.latitude = latitude
        self.longitude = longitude
        self.ayanamsa = ayanamsa
        self.house_system = house_system