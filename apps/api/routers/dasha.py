"""
AstroOS — Dasha Router (Task 6)

Endpoints
---------
POST /api/v1/dasha/vimshottari   — 120-year Parashara cycle
POST /api/v1/dasha/yogini        — 36-year Yogini cycle
POST /api/v1/dasha/ashtottari    — 108-year Ashtottari cycle
POST /api/v1/dasha/kalachakra    — 100-year Kalachakra cycle
POST /api/v1/dasha/chara         — Jaimini Chara (D1-based sign cycle)
POST /api/v1/dasha/narayana      — Jaimini Narayana (D9-based sign cycle)

All endpoints accept the same DashaRequest body and return DashaTreeResponse.
No business logic lives here.
"""

from __future__ import annotations

import asyncio
import functools
import logging
from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import get_db_session, get_ephemeris_wrapper
from apps.api.domain.dasha import DashaTree
from apps.api.repositories.birth_chart_repository import BirthChartRepository
from apps.api.repositories.dasha_repository import DashaRepository
from apps.api.schemas.dasha import DashaRequest, DashaPeriodResponse, DashaTreeResponse
from apps.api.services.dasha_engine import DashaEngine
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


# ── Serialisation ──────────────────────────────────────────────────────────────


def _serialise_period(p) -> DashaPeriodResponse:
    return DashaPeriodResponse(
        lord=p.lord,
        start_date=p.start_date,
        end_date=p.end_date,
        duration_days=p.duration_days,
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


def _make_endpoint(compute_fn_name: str, summary: str, description: str):
    """
    Factory that builds an async FastAPI endpoint for one dasha system.
    Avoids repeating the same try/except boilerplate 6 times.
    """
    async def endpoint(
        body: DashaRequest,
        engine: DashaEngine = Depends(_get_dasha_engine),
    ) -> DashaTreeResponse:
        try:
            compute_fn: Callable = getattr(engine, compute_fn_name)
            # Blocking pyswisseph call — offload to a worker thread so it
            # does not freeze the event loop. See horoscope.py's
            # generate_d1_chart for the full rationale.
            tree = await asyncio.to_thread(
                functools.partial(
                    compute_fn,
                    birth_datetime_utc=body.birth_datetime_utc,
                    latitude=body.latitude,
                    longitude=body.longitude,
                    ayanamsa=body.ayanamsa,
                    house_system=body.house_system,
                    max_depth=body.max_depth,
                )
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            )
        except Exception as exc:
            logger.exception("Error computing %s: %s", compute_fn_name, exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to compute dasha: {exc}",
            )

        try:
            await engine.persist_tree(
                tree,
                birth_datetime_utc=body.birth_datetime_utc,
                latitude=body.latitude,
                longitude=body.longitude,
                ayanamsa=body.ayanamsa,
                house_system=body.house_system,
            )
        except SQLAlchemyError as exc:
            logger.exception("Failed to persist %s dasha tree: %s", compute_fn_name, exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Dasha tree was computed successfully but could not be "
                    "saved. Please retry."
                ),
            ) from exc

        return _serialise_tree(tree)

    endpoint.__name__ = compute_fn_name
    endpoint.__doc__ = description
    return endpoint


# ── Routes ────────────────────────────────────────────────────────────────────


router.add_api_route(
    "/vimshottari",
    _make_endpoint(
        "compute_vimshottari",
        "Vimshottari Dasha",
        "120-year Parashara cycle based on Moon's nakshatra. Returns Mahadasha through Prana.",
    ),
    methods=["POST"],
    response_model=DashaTreeResponse,
    summary="Vimshottari Dasha",
)

router.add_api_route(
    "/yogini",
    _make_endpoint(
        "compute_yogini",
        "Yogini Dasha",
        "36-year cycle. Eight Yogini lords cycle through Moon's nakshatra sequence.",
    ),
    methods=["POST"],
    response_model=DashaTreeResponse,
    summary="Yogini Dasha",
)

router.add_api_route(
    "/ashtottari",
    _make_endpoint(
        "compute_ashtottari",
        "Ashtottari Dasha",
        "108-year cycle. Applied when Rahu occupies a Kendra or Trikona from Lagna.",
    ),
    methods=["POST"],
    response_model=DashaTreeResponse,
    summary="Ashtottari Dasha",
)

router.add_api_route(
    "/kalachakra",
    _make_endpoint(
        "compute_kalachakra",
        "Kalachakra Dasha",
        "100-year sign-based cycle derived from Moon's Navamsha (D9) position.",
    ),
    methods=["POST"],
    response_model=DashaTreeResponse,
    summary="Kalachakra Dasha",
)

router.add_api_route(
    "/chara",
    _make_endpoint(
        "compute_chara",
        "Chara Dasha (Jaimini)",
        "Sign-based Jaimini dasha. Duration computed from D1 sign-lord placements.",
    ),
    methods=["POST"],
    response_model=DashaTreeResponse,
    summary="Chara Dasha",
)

router.add_api_route(
    "/narayana",
    _make_endpoint(
        "compute_narayana",
        "Narayana Dasha (Jaimini)",
        "Sign-based Jaimini dasha using Navamsha (D9) sign-lord placements.",
    ),
    methods=["POST"],
    response_model=DashaTreeResponse,
    summary="Narayana Dasha",
)
