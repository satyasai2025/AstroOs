"""
AstroOS — Dasha Router (Task 6)

Endpoints
---------
GET  /api/v1/dasha/systems       — list registered dasha systems (id/label/category)
POST /api/v1/dasha/vimshottari   — 120-year Parashara cycle
POST /api/v1/dasha/yogini        — 36-year Yogini cycle
POST /api/v1/dasha/ashtottari    — 108-year Ashtottari cycle
POST /api/v1/dasha/kalachakra    — 100-year Kalachakra cycle
POST /api/v1/dasha/chara         — Jaimini Chara (D1-based sign cycle)
POST /api/v1/dasha/narayana      — Jaimini Narayana (D9-based sign cycle)

All POST endpoints accept the same DashaRequest body and return DashaTreeResponse.
Routes are generated from the dasha registry (apps/api/services/dasha_registry.py)
rather than hardcoded here, and dispatch through DashaOrchestrator. No business
logic (dasha math or persistence) lives in this file.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import get_db_session, get_ephemeris_wrapper
from apps.api.domain.dasha import DashaTree
from apps.api.repositories.birth_chart_repository import BirthChartRepository
from apps.api.repositories.dasha_repository import DashaRepository
from apps.api.schemas.dasha import (
    DashaRequest,
    DashaPeriodResponse,
    DashaSystemInfo,
    DashaTreeResponse,
)
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.dasha_orchestrator import DashaOrchestrator
from apps.api.services.dasha_registry import DashaEngineDescriptor, all_dasha_engines
from apps.api.services.ephemeris_wrapper import EphemerisWrapper

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dasha", tags=["Dasha"])


# ── DI ────────────────────────────────────────────────────────────────────────


def _get_dasha_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
    session: AsyncSession = Depends(get_db_session),
) -> DashaEngine:
    """
    Build a DashaEngine using the process-wide EphemerisWrapper singleton,
    plus request-scoped repositories for persistence.

    Does NOT construct a new EphemerisWrapper — see get_ephemeris_wrapper's
    docstring for why that would reintroduce a global-state race condition.
    """
    return DashaEngine(
        wrapper,
        birth_chart_repo=BirthChartRepository(session),
        dasha_repo=DashaRepository(session),
    )


def _get_dasha_orchestrator(
    engine: DashaEngine = Depends(_get_dasha_engine),
) -> DashaOrchestrator:
    return DashaOrchestrator(engine)


# ── Serialisation ──────────────────────────────────────────────────────────────


def _serialise_period(p) -> DashaPeriodResponse:
    dur = getattr(p, "duration_days", 0)
    if isinstance(dur, float):
        dur = round(dur, 4)
    return DashaPeriodResponse(
        lord=p.lord,
        start_date=p.start_date,
        end_date=p.end_date,
        duration_days=dur,
        level=p.level,
        sub_periods=[_serialise_period(s) for s in p.sub_periods],
    )


def _serialise_tree(tree: DashaTree) -> DashaTreeResponse:
    return DashaTreeResponse(
        system=tree.system,
        birth_date=tree.birth_date,
        trigger_planet=tree.trigger_planet,
        trigger_nakshatra=tree.trigger_nakshatra,
        trigger_nakshatra_number=tree.trigger_nakshatra_number,
        mahadashas=[_serialise_period(m) for m in tree.mahadashas],
        max_depth=tree.max_depth,
        total_cycle_years=tree.total_cycle_years,
    )


def _make_endpoint(descriptor: DashaEngineDescriptor):
    """
    Factory that builds an async FastAPI endpoint for one dasha system,
    dispatching through DashaOrchestrator. Avoids repeating the same
    try/except boilerplate once per registered system.
    """

    async def endpoint(
        body: DashaRequest,
        orchestrator: DashaOrchestrator = Depends(_get_dasha_orchestrator),
    ) -> DashaTreeResponse:
        # Compute and persist are two distinct failure modes with distinct
        # HTTP semantics, so they're split into two orchestrator calls
        # (persist=False then a dedicated persist step) even though
        # DashaOrchestrator.run can do both in one call.
        try:
            tree = await orchestrator.run(
                descriptor.system,
                birth_datetime_utc=body.birth_datetime_utc,
                latitude=body.latitude,
                longitude=body.longitude,
                ayanamsa=body.ayanamsa,
                house_system=body.house_system,
                max_depth=body.max_depth,
                persist=False,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            )
        except Exception as exc:
            logger.exception("Error computing %s: %s", descriptor.compute_method, exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to compute dasha: {exc}",
            )

        if body.persist:
            try:
                await orchestrator.persist(
                    tree,
                    birth_datetime_utc=body.birth_datetime_utc,
                    latitude=body.latitude,
                    longitude=body.longitude,
                    ayanamsa=body.ayanamsa,
                    house_system=body.house_system,
                )
            except SQLAlchemyError as exc:
                logger.exception(
                    "Failed to persist %s dasha tree: %s", descriptor.compute_method, exc
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=(
                        "Dasha tree was computed successfully but could not be "
                        "saved. Please retry."
                    ),
                ) from exc

        return _serialise_tree(tree)

    endpoint.__name__ = descriptor.compute_method
    endpoint.__doc__ = descriptor.description
    return endpoint


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get(
    "/systems",
    response_model=list[DashaSystemInfo],
    summary="List registered dasha systems",
)
def list_dasha_systems() -> list[DashaSystemInfo]:
    return [
        DashaSystemInfo(system=d.system, label=d.label, category=d.category)
        for d in all_dasha_engines()
    ]


for _descriptor in all_dasha_engines():
    router.add_api_route(
        f"/{_descriptor.system}",
        _make_endpoint(_descriptor),
        methods=["POST"],
        response_model=DashaTreeResponse,
        summary=_descriptor.summary,
    )
