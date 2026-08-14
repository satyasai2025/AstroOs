"""
AstroOS — Full Report Router

Endpoints
---------
POST /api/v1/report/full — the complete astrology report: one birth-data
submission drives the entire Unified Analysis Pipeline (Chart -> Vargas
-> Dasha -> Yoga -> Shadbala -> Ashtakavarga -> Transit -> Rule Engine ->
Knowledge -> Verification -> Report) plus the KP (Krishnamurti Paddhati)
Analysis + Evidence layer, and returns everything as a single document
for a printable / shareable report page.

This is a composition endpoint — it owns no business logic. It builds
the same WorkflowOrchestrator as routers/workflow.py via DI, runs the
pipeline with persist=false (the full report never writes a
birth_charts row — it recomputes deterministically from raw birth data,
so no saved chart or user_id is required), then feeds the already-
computed chart / dasha tree / transit results into KPEngine exactly as
routers/kp.py does — but reusing the pipeline's work instead of
recomputing the astronomy.

The response mirrors WorkflowAnalysisResponse and appends a
`kp_analysis` section, so the frontend renders it with the existing
workflow + KP panels on a continuous page.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import (
    get_current_user_from_bearer,
    get_db_session,
    get_ephemeris_wrapper,
    get_knowledge_engine,
)
from apps.api.domain.user import User
from apps.api.repositories.birth_chart_repository import BirthChartRepository
from apps.api.repositories.divisional_chart_repository import DivisionalChartRepository
from apps.api.repositories.divisional_planet_repository import DivisionalPlanetRepository
from apps.api.repositories.event_repository import EventRepository
from apps.api.repositories.house_repository import HouseRepository
from apps.api.repositories.planet_position_repository import PlanetPositionRepository
from apps.api.repositories.research_repository import ResearchRepository
from apps.api.routers.kp import _to_response as _kp_to_response
from apps.api.routers.workflow import _result_to_response
from apps.api.schemas.workflow import FullReportRequest, FullReportResponse, WorkflowAnalysisRequest
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.knowledge_engine import KnowledgeEngine
from apps.api.services.kp_engine import KPEngine
from apps.api.services.workflow_orchestrator import WorkflowOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/report", tags=["Report"])


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


@router.post(
    "/full",
    response_model=FullReportResponse,
    summary="Complete astrology report — full analysis pipeline + KP in one call",
    description=(
        "Run the entire Unified Analysis Pipeline for one birth-data "
        "submission — chart, vargas, dasha, yogas, shadbala, "
        "ashtakavarga, transits, rule engine, knowledge citations, "
        "verification, and the composed report — then append the KP "
        "(Krishnamurti Paddhati) analysis and evidence sections. The "
        "report never persists a birth chart: it recomputes the chart "
        "deterministically from the submitted birth data, so a saved "
        "chart is not required. Response is a single document the "
        "frontend renders as a continuous printable report page."
    ),
)
async def build_full_report(
    body: FullReportRequest,
    current_user: User = Depends(get_current_user_from_bearer),
    orchestrator: WorkflowOrchestrator = Depends(_get_orchestrator),
) -> FullReportResponse:
    transit_datetime_utc = body.transit_datetime_utc or datetime.now(timezone.utc)

    # persist=false + chart_id=None: the pipeline recomputes the chart
    # deterministically without writing a birth_charts row. The schema
    # validator normally forbids (persist=False, chart_id=None), so we
    # construct the request with model_construct to bypass that
    # guardrail — this endpoint is intentionally the anonymous-recompute
    # path (no saved chart exists yet for a brand-new birth data).
    request = WorkflowAnalysisRequest.model_construct(
        birth_datetime_utc=body.birth_datetime_utc,
        latitude=body.latitude,
        longitude=body.longitude,
        ayanamsa=body.ayanamsa,
        house_system=body.house_system,
        dasha_system=body.dasha_system,
        transit_datetime_utc=transit_datetime_utc,
        include_vargas=body.include_vargas,
        subject_name=body.subject_name,
        generated_by=body.generated_by,
        persist=False,
        chart_id=None,
        research_project_id=None,
    )

    try:
        result = await orchestrator.analyze(request, user_id=current_user.id.value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error running full report pipeline: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run the full analysis pipeline.",
        )

    kp_response = None
    if body.include_kp:
        try:
            kp_result = await asyncio.to_thread(
                KPEngine().analyze,
                result.chart,
                result.dasha_tree,
                result.transit_results,
                result.transit_datetime_utc,
            )
            kp_response = _kp_to_response(kp_result, result.transit_datetime_utc)
        except Exception as exc:
            logger.exception("Error running KP analysis for full report: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to compute KP analysis: {exc}",
            )

    response = _result_to_response(
        result,
        response_cls=FullReportResponse,
        chart_id=None,
        extra_kwargs={
            "title": body.title,
            "subject_name": body.subject_name,
            "generated_at": datetime.now(timezone.utc),
            "kp_analysis": kp_response,
        },
    )
    return response
