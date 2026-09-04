"""
AstroOS — Workflow Orchestrator Router (v2 Phase A)

Endpoints
---------
POST /api/v1/workflow/analyze — the Unified Analysis Pipeline: one birth
data submission drives Chart -> Vargas -> Dasha -> Yoga -> Shadbala ->
Ashtakavarga -> Transit -> Rule Engine -> Knowledge -> Verification ->
Report in a single request.

All orchestration logic lives in WorkflowOrchestrator
(apps/api/services/workflow_orchestrator.py) — this file only builds
that orchestrator via DI, calls analyze(), and serializes the result.
Serialization reuses each engine's own existing router-level serializer
function (imported from routers/horoscope.py, divisional.py, dasha.py,
yoga.py, ashtakavarga.py, transit.py, report.py) rather than
re-deriving them — same reuse pattern routers/export.py already
established this session for report.py's placeholder builders.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import (
    get_current_user_from_bearer,
    get_db_session,
    get_ephemeris_wrapper,
    get_knowledge_engine,
)
from apps.api.middleware.rate_limit import limiter
from apps.api.domain.user import User
from apps.api.repositories.birth_chart_repository import BirthChartRepository
from apps.api.repositories.divisional_chart_repository import DivisionalChartRepository
from apps.api.repositories.divisional_planet_repository import DivisionalPlanetRepository
from apps.api.repositories.event_repository import EventRepository
from apps.api.repositories.house_repository import HouseRepository
from apps.api.repositories.planet_position_repository import PlanetPositionRepository
from apps.api.repositories.research_repository import ResearchRepository
from apps.api.routers.ashtakavarga import _serialise_bhinna, _serialise_sarva
from apps.api.routers.dasha import _serialise_tree
from apps.api.routers.divisional import _serialise_chart
from apps.api.routers.horoscope import _chart_to_response
from apps.api.routers.report import _metadata_response, _sections_response
from apps.api.routers.transit import _serialise_planet
from apps.api.routers.yoga import _serialise_result
from apps.api.schemas.ashtakavarga import AllAshtakavargaResponse
from apps.api.schemas.divisional import AllVargaChartsResponse
from apps.api.schemas.knowledge import KnowledgeSearchResultResponse
from apps.api.schemas.report import ChartReportResponse
from apps.api.schemas.transit import TransitResponse
from apps.api.schemas.workflow import (
    BenchmarkResponse,
    BulkImportRequest,
    BulkImportResponse,
    BulkImportRowResult,
    PlanetBenchmarkResponse,
    RuleResultResponse,
    ShadbalaTotalResponse,
    VerificationPairSummaryResponse,
    VerificationSummaryResponse,
    WorkflowAnalysisRequest,
    WorkflowAnalysisResponse,
    WorkflowDuplicateCheckRequest,
    WorkflowDuplicateCheckResponse,
)
from apps.api.schemas.yoga import YogaEvaluationResponse
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.knowledge_engine import KnowledgeEngine
from apps.api.services.rule_registry import get_rule
from apps.api.services.workflow_orchestrator import WorkflowAnalysisResult, WorkflowOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflow", tags=["Workflow"])


def _get_orchestrator(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
    session: AsyncSession = Depends(get_db_session),
    knowledge_engine: KnowledgeEngine = Depends(get_knowledge_engine),
) -> WorkflowOrchestrator:
    return WorkflowOrchestrator(
        wrapper,
        birth_chart_repo=BirthChartRepository(session),
        planet_position_repo=PlanetPositionRepository(session),
        house_repo=HouseRepository(session),
        divisional_chart_repo=DivisionalChartRepository(session),
        divisional_planet_repo=DivisionalPlanetRepository(session),
        event_repo=EventRepository(session),
        knowledge_engine=knowledge_engine,
        research_repo=ResearchRepository(session),
    )


def _rule_result_response(result) -> RuleResultResponse:
    definition = get_rule(result.rule_id)
    return RuleResultResponse(
        rule_id=result.rule_id,
        rule_name=definition.rule_name if definition else result.rule_id,
        rule_category=definition.category if definition else "unknown",
        matched=result.matched,
        matched_conditions=list(result.matched_conditions),
        failed_conditions=list(result.failed_conditions),
        explanation=result.explanation,
        priority=result.priority,
        evaluation_trace=list(result.evaluation_trace),
        derived_facts=dict(result.derived_facts),
    )


def _verification_response(findings) -> VerificationSummaryResponse:
    return VerificationSummaryResponse(
        total_events=findings.total_events,
        total_rules_evaluated=findings.total_rules_evaluated,
        total_pairs=findings.total_pairs,
        pairs=[
            VerificationPairSummaryResponse(
                rule_id=p.rule_id, rule_name=p.rule_name, event_id=p.event_id,
                event_title=p.event_title, event_date=p.event_date,
                alignment=p.alignment.value, strength=p.strength.value,
            )
            for p in findings.verification_pairs
        ],
        confidence_score=getattr(findings, "confidence_score", 0.0),
    )


def _result_to_response(
    result: WorkflowAnalysisResult,
    *,
    response_cls: type = WorkflowAnalysisResponse,
    chart_id: Optional[uuid.UUID] = None,
    extra_kwargs: Optional[dict] = None,
) -> WorkflowAnalysisResponse:
    vargas_response = None
    if result.vargas is not None:
        serialised = {code: _serialise_chart(chart) for code, chart in result.vargas.items()}
        sample = next(iter(result.vargas.values()))
        vargas_response = AllVargaChartsResponse(
            charts=serialised, julian_day=sample.julian_day, ayanamsa_system=sample.ayanamsa_system,
        )

    yogas_response = YogaEvaluationResponse(
        results=[_serialise_result(r) for r in result.yoga_results],
        total_evaluated=len(result.yoga_results),
        total_present=sum(1 for r in result.yoga_results if r.is_present),
    )

    knowledge_citations = [
        KnowledgeSearchResultResponse(
            entity_type=c.entity_type, entity_id=c.entity_id, title=c.title,
            snippet=c.snippet, relevance=c.relevance, book_title=c.book_title,
            tradition=c.tradition,
        )
        for c in result.knowledge_citations
    ]

    # ── Benchmark serialization ────────────────────────────────────────
    if result.benchmark_result is not None and result.benchmark_result.reference_id != "unknown":
        benchmark = BenchmarkResponse(
            status="passed" if result.benchmark_result.passed else "failed",
            reference_id=result.benchmark_result.reference_id,
            reference_name=result.benchmark_result.reference_name,
            chart_count=len(result.benchmark_result.planets),
            mean_error=result.benchmark_result.mean_error,
            max_error=result.benchmark_result.max_error,
            tolerance=result.benchmark_result.tolerance,
            planets=[
                PlanetBenchmarkResponse(
                    planet=p.planet, computed_longitude=p.computed_longitude,
                    expected_longitude=p.expected_longitude,
                    error_degrees=p.error_degrees,
                    within_tolerance=p.within_tolerance,
                )
                for p in result.benchmark_result.planets
            ],
        )
    else:
        benchmark = BenchmarkResponse(
            status="not_applicable",
            detail=(
                "Benchmark validation only runs against AstroOS's 5 internal "
                "reference charts (used to verify calculation accuracy) — "
                "this isn't one of them, so there's nothing to validate here."
            ),
        )

    _id = chart_id if chart_id is not None else result.chart_id
    kwargs = dict(
        chart_id=_id,
        chart=_chart_to_response(result.chart),
        vargas=vargas_response,
        dasha=_serialise_tree(result.dasha_tree),
        yogas=yogas_response,
        shadbala=[
            ShadbalaTotalResponse(planet=p, total_rupas=v)
            for p, v in result.shadbala_totals_rupas.items()
        ],
        ashtakavarga=AllAshtakavargaResponse(
            bhinnashtakavarga=[_serialise_bhinna(r) for r in result.bhinna_results],
            bhinnashtakavarga_reduced=[_serialise_bhinna(r) for r in result.bhinna_reduced_results],
            sarvashtakavarga=_serialise_sarva(result.sarva_result, result.sarva_checksum_valid),
        ),
        transits=TransitResponse(
            transit_datetime_utc=result.transit_datetime_utc,
            natal_moon_rashi=result.natal_moon_rashi,
            planets=[_serialise_planet(r) for r in result.transit_results],
        ),
        rule_results=[_rule_result_response(r) for r in result.rule_results],
        knowledge_citations=knowledge_citations,
        verification=(
            _verification_response(result.verification_findings)
            if result.verification_findings is not None else None
        ),
        benchmark=benchmark,
        report=ChartReportResponse(
            metadata=_metadata_response(result.report.metadata),
            title=result.report.title,
            subject_name=result.report.subject_name,
            sections=_sections_response(result.report.sections),
        ),
        research_snapshot_id=result.research_snapshot_id,
    )
    if extra_kwargs:
        kwargs.update(extra_kwargs)
    return response_cls(**kwargs)


@router.post(
    "/analyze",
    response_model=WorkflowAnalysisResponse,
    summary="Unified Analysis Pipeline — Chart through Report in one call",
    description=(
        "The v2 Phase A vertical slice: computes the D1 chart, all 15 "
        "divisional charts (optional), the requested Dasha system, Yoga "
        "detection, Shadbala, Ashtakavarga, and current transits; builds "
        "Facts and evaluates the Rule Engine; best-effort correlates "
        "detected yogas against the Knowledge base; verifies rule "
        "predictions against any events already recorded for this chart "
        "(POST /events) — omitted if none exist yet; and composes a "
        "report with Knowledge citations merged into its own sections. "
        "If research_project_id is supplied, the full computed result is "
        "also captured as an AstrologicalSnapshot into that Research "
        "project. Benchmark validation is an explicit not-implemented "
        "placeholder (v2 Phase C has not started)."
    ),
)
@limiter.limit("6/minute")
async def analyze_workflow(
    request: Request,
    body: WorkflowAnalysisRequest,
    current_user: User = Depends(get_current_user_from_bearer),
    orchestrator: WorkflowOrchestrator = Depends(_get_orchestrator),
) -> WorkflowAnalysisResponse:
    try:
        result = await orchestrator.analyze(body, user_id=current_user.id.value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error running workflow analysis: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run the analysis pipeline.",
        )
    return _result_to_response(result)


@router.post(
    "/check-existing",
    response_model=WorkflowDuplicateCheckResponse,
    summary="Check whether a saved chart already matches this exact birth data",
    description=(
        "Looks up whether this user already has a saved chart matching "
        "(birth_datetime_utc, latitude, longitude, ayanamsa, house_system) "
        "exactly — the same natural key POST /workflow/analyze dedups on "
        "when persist=true. Two different people can share an exact birth "
        "moment and location (e.g. a coincidence, or precision-matched "
        "coordinates), so a match here does not mean 'this is the same "
        "person' — it's a prompt for the caller to ask the user whether to "
        "open the existing chart or save a new one anyway with force_new=true."
    ),
)
@limiter.limit("30/minute")
async def check_existing_chart(
    request: Request,
    body: WorkflowDuplicateCheckRequest,
    current_user: User = Depends(get_current_user_from_bearer),
    session: AsyncSession = Depends(get_db_session),
) -> WorkflowDuplicateCheckResponse:
    repo = BirthChartRepository(session)
    existing = await repo.find_existing(
        birth_datetime_utc=body.birth_datetime_utc,
        latitude=body.latitude,
        longitude=body.longitude,
        ayanamsa=body.ayanamsa,
        house_system=body.house_system,
        user_id=current_user.id.value,
    )
    if existing is None:
        return WorkflowDuplicateCheckResponse(exists=False)
    return WorkflowDuplicateCheckResponse(
        exists=True,
        chart_id=existing.id,
        subject_name=existing.subject_name,
        saved_at=existing.created_at,
    )


@router.post(
    "/bulk-import",
    response_model=BulkImportResponse,
    summary="Bulk-import saved charts from birth-data rows (e.g. a CSV/JSON upload)",
    description=(
        "Creates one saved chart per row by running each through the same "
        "analysis pipeline as POST /workflow/analyze (persist=true, "
        "divisional charts skipped for speed). Rows are processed "
        "independently in one request — an invalid row is reported in "
        "the response, not raised as an error that fails the whole batch. "
        "Capped at 100 rows per call."
    ),
)
@limiter.limit("5/hour")
async def bulk_import(
    request: Request,
    body: BulkImportRequest,
    current_user: User = Depends(get_current_user_from_bearer),
    orchestrator: WorkflowOrchestrator = Depends(_get_orchestrator),
    session: AsyncSession = Depends(get_db_session),
) -> BulkImportResponse:
    results: list[BulkImportRowResult] = []
    chart_repo = BirthChartRepository(session)

    for i, row in enumerate(body.rows):
        try:
            matched_existing = False
            if not row.force_new:
                existing = await chart_repo.find_existing(
                    birth_datetime_utc=row.birth_datetime_utc,
                    latitude=row.latitude,
                    longitude=row.longitude,
                    ayanamsa=row.ayanamsa,
                    house_system=row.house_system,
                    user_id=current_user.id.value,
                )
                matched_existing = existing is not None

            analyze_request = WorkflowAnalysisRequest(
                birth_datetime_utc=row.birth_datetime_utc,
                latitude=row.latitude,
                longitude=row.longitude,
                ayanamsa=row.ayanamsa,
                house_system=row.house_system,
                dasha_system="vimshottari",
                include_vargas=False,
                subject_name=row.subject_name,
                place_name=row.place_name,
                persist=True,
                force_new=row.force_new,
            )
            result = await orchestrator.analyze(analyze_request, user_id=current_user.id.value)
            results.append(
                BulkImportRowResult(
                    row_index=i,
                    subject_name=row.subject_name,
                    success=True,
                    chart_id=result.chart_id,
                    matched_existing=matched_existing,
                )
            )
        except ValueError as exc:
            results.append(
                BulkImportRowResult(
                    row_index=i, subject_name=row.subject_name, success=False, error=str(exc),
                )
            )
        except Exception as exc:
            logger.exception("Bulk import row %d failed: %s", i, exc)
            results.append(
                BulkImportRowResult(
                    row_index=i,
                    subject_name=row.subject_name,
                    success=False,
                    error="Failed to compute this chart.",
                )
            )

    succeeded = sum(1 for r in results if r.success)
    return BulkImportResponse(
        total=len(results),
        succeeded=succeeded,
        failed=len(results) - succeeded,
        results=results,
    )
