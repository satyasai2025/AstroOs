"""
AstroOS — Visualization Router (Module 22 — HTTP surface)

HTTP adapter layer over VisualizationEngine. Builds the raw domain
objects VisualizationEngine.visualize() expects (D1Chart, Distribution,
Crosstab, snapshot tuples) via the same engines/repositories the other
routers use, then dispatches through VisualizationEngine so all
theme/adapter logic stays centralized in the engine, not duplicated here.

See schemas/visualization.py's module docstring for the one type
(`timeline`) intentionally not wired yet.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import get_db_session, get_ephemeris_wrapper
from apps.api.domain.visualization import VisualizationRequest
from apps.api.repositories.research_repository import ResearchRepository
from apps.api.schemas.visualization import (
    AvailableVisualizationResponse,
    AvailableVisualizationsResponse,
    ChartWheelRequest,
    CrosstabVisualizationRequest,
    DistributionVisualizationRequest,
    SnapshotGroupVisualizationRequest,
    VisualizationResultResponse,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.statistics_engine import StatisticsEngine
from apps.api.services.visualization_engine import VisualizationEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/visualization", tags=["Visualization"])

_WIRED_TYPES = {
    "chart_wheel", "distribution", "crosstab", "snapshot_comparison", "relationship_graph",
}


def _result_response(result) -> VisualizationResultResponse:
    return VisualizationResultResponse(
        visualization_type=result.visualization_type,
        renderer=result.renderer,
        version=result.version,
        theme=result.theme,
        data=result.data,
        metadata=result.metadata,
        generated_at=result.generated_at,
    )


def _dispatch(visualization_type: str, source_data: dict, opts) -> VisualizationResultResponse:
    request = VisualizationRequest(
        visualization_type=visualization_type,
        source_data=source_data,
        theme_name=opts.theme_name,
        width=opts.width,
        height=opts.height,
    )
    try:
        result = VisualizationEngine.visualize(request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return _result_response(result)


@router.get("/types", response_model=AvailableVisualizationsResponse, summary="List visualization types")
async def list_visualization_types() -> AvailableVisualizationsResponse:
    return AvailableVisualizationsResponse(
        visualizations=[
            AvailableVisualizationResponse(**v, wired=v["type"] in _WIRED_TYPES)
            for v in VisualizationEngine.available_visualizations()
        ]
    )


@router.post("/chart-wheel", response_model=VisualizationResultResponse)
async def visualize_chart_wheel(
    body: ChartWheelRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> VisualizationResultResponse:
    horoscope_engine = HoroscopeEngine(wrapper)
    try:
        chart = await asyncio.to_thread(
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
        logger.exception("Error computing chart for chart-wheel visualization: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute chart for visualization.",
        )
    return _dispatch("chart_wheel", {"chart": chart}, body)


@router.post("/distribution", response_model=VisualizationResultResponse)
async def visualize_distribution(
    body: DistributionVisualizationRequest,
    session: AsyncSession = Depends(get_db_session),
) -> VisualizationResultResponse:
    repo = ResearchRepository(session)
    snapshots = await repo.list_snapshots(body.project_id)

    if body.distribution_type == "planet-house":
        dist = StatisticsEngine.compute_planet_house_distribution(snapshots, body.planet)
    elif body.distribution_type == "planet-rashi":
        dist = StatisticsEngine.compute_planet_rashi_distribution(snapshots, body.planet)
    elif body.distribution_type == "yoga":
        dist = StatisticsEngine.compute_yoga_distribution(snapshots)
    else:
        dist = StatisticsEngine.compute_verification_strength_distribution(snapshots)

    return _dispatch("distribution", {"distribution": dist}, body)


@router.post("/crosstab", response_model=VisualizationResultResponse)
async def visualize_crosstab(
    body: CrosstabVisualizationRequest,
    session: AsyncSession = Depends(get_db_session),
) -> VisualizationResultResponse:
    repo = ResearchRepository(session)
    snapshots = await repo.list_snapshots(body.project_id)
    crosstab = StatisticsEngine.compute_crosstab(snapshots, body.row_field, body.col_field)
    return _dispatch("crosstab", {"crosstab": crosstab}, body)


@router.post("/snapshot-comparison", response_model=VisualizationResultResponse)
async def visualize_snapshot_comparison(
    body: SnapshotGroupVisualizationRequest,
    session: AsyncSession = Depends(get_db_session),
) -> VisualizationResultResponse:
    repo = ResearchRepository(session)
    snapshots = await repo.list_snapshots(body.project_id)
    return _dispatch("snapshot_comparison", {"snapshots": snapshots}, body)


@router.post("/relationship-graph", response_model=VisualizationResultResponse)
async def visualize_relationship_graph(
    body: SnapshotGroupVisualizationRequest,
    session: AsyncSession = Depends(get_db_session),
) -> VisualizationResultResponse:
    repo = ResearchRepository(session)
    snapshots = await repo.list_snapshots(body.project_id)
    return _dispatch("relationship_graph", {"snapshots": snapshots}, body)
