"""
AstroOS — Divisional Chart Router (Task 5)

Endpoints
---------
POST /api/v1/divisional/{varga}   — Compute a single varga chart (D2 … D60)
POST /api/v1/divisional/all       — Compute all 15 varga charts in one call

No business logic lives here — all computation is delegated to DivisionalEngine.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import get_db_session, get_ephemeris_wrapper
from apps.api.domain.divisional import VargaChart
from apps.api.repositories.birth_chart_repository import BirthChartRepository
from apps.api.repositories.divisional_chart_repository import DivisionalChartRepository
from apps.api.repositories.divisional_planet_repository import DivisionalPlanetRepository
from apps.api.schemas.divisional import (
    AllVargaChartsResponse,
    VargaAscendantResponse,
    VargaChartRequest,
    VargaChartResponse,
    VargaPlanetResponse,
)
from apps.api.services.divisional_engine import SUPPORTED_VARGAS, DivisionalEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/divisional", tags=["Divisional Charts"])

_VALID_VARGAS = sorted(SUPPORTED_VARGAS)


# ── DI helper ────────────────────────────────────────────────────────────────


def _get_divisional_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
    session: AsyncSession = Depends(get_db_session),
) -> DivisionalEngine:
    """
    Build a DivisionalEngine using the process-wide EphemerisWrapper singleton,
    plus request-scoped repositories for persistence.

    Does NOT construct a new EphemerisWrapper — see get_ephemeris_wrapper's
    docstring for why that would reintroduce a global-state race condition.
    """
    return DivisionalEngine(
        wrapper,
        birth_chart_repo=BirthChartRepository(session),
        divisional_chart_repo=DivisionalChartRepository(session),
        divisional_planet_repo=DivisionalPlanetRepository(session),
    )


# ── Serialisation helper ──────────────────────────────────────────────────────


def _serialise_chart(chart: VargaChart) -> VargaChartResponse:
    return VargaChartResponse(
        varga=chart.varga,
        divisor=chart.divisor,
        ascendant=VargaAscendantResponse(
            d1_sidereal_longitude=chart.ascendant.d1_sidereal_longitude,
            d1_rashi=chart.ascendant.d1_rashi,
            d1_rashi_degree=round(chart.ascendant.d1_rashi_degree, 6),
            varga_rashi=chart.ascendant.varga_rashi,
            varga_rashi_degree=round(chart.ascendant.varga_rashi_degree, 6),
        ),
        planet_positions=[
            VargaPlanetResponse(
                planet=p.planet,
                d1_sidereal_longitude=p.d1_sidereal_longitude,
                d1_rashi=p.d1_rashi,
                d1_rashi_degree=p.d1_rashi_degree,
                varga_rashi=p.varga_rashi,
                varga_rashi_degree=p.varga_rashi_degree,
                varga_house_number=p.varga_house_number,
                nakshatra=p.nakshatra,
                pada=p.pada,
                is_retrograde=p.is_retrograde,
                is_combust=p.is_combust,
            )
            for p in chart.planet_positions
        ],
        ayanamsa_system=chart.ayanamsa_system,
        julian_day=chart.julian_day,
    )


# ── Routes ────────────────────────────────────────────────────────────────────


@router.post(
    "/all",
    response_model=AllVargaChartsResponse,
    summary="Compute all 15 divisional charts",
    description=(
        "Computes D2 through D60 in a single ephemeris call. "
        "Returns a map of varga code → chart."
    ),
)
async def compute_all_vargas(
    body: VargaChartRequest,
    engine: DivisionalEngine = Depends(_get_divisional_engine),
) -> AllVargaChartsResponse:
    try:
        # Blocking pyswisseph call — offload to a worker thread so it does
        # not freeze the event loop. See horoscope.py's generate_d1_chart
        # for the full rationale.
        all_charts = await asyncio.to_thread(
            engine.compute_all,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error computing all vargas: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute divisional charts.",
        )

    try:
        await engine.persist_all(
            all_charts,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
    except SQLAlchemyError as exc:
        logger.exception("Failed to persist divisional charts: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Charts were computed successfully but could not be saved. "
                "Please retry."
            ),
        ) from exc

    serialised = {code: _serialise_chart(chart) for code, chart in all_charts.items()}
    # Pick any chart for shared metadata
    sample = next(iter(all_charts.values()))
    return AllVargaChartsResponse(
        charts=serialised,
        julian_day=sample.julian_day,
        ayanamsa_system=sample.ayanamsa_system,
    )


@router.post(
    "/{varga}",
    response_model=VargaChartResponse,
    summary="Compute a single divisional chart",
    description=(
        "Compute one of the 15 supported varga charts: "
        + ", ".join(_VALID_VARGAS)
        + "."
    ),
)
async def compute_varga(
    body: VargaChartRequest,
    engine: DivisionalEngine = Depends(_get_divisional_engine),
    varga: str = Path(
        ...,
        description=f"Divisional chart code. One of: {', '.join(_VALID_VARGAS)}.",
    ),
) -> VargaChartResponse:
    varga_upper = varga.upper()
    if varga_upper not in SUPPORTED_VARGAS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown varga '{varga}'. Supported: {_VALID_VARGAS}",
        )

    try:
        # Blocking pyswisseph call — offload to a worker thread so it does
        # not freeze the event loop. See horoscope.py's generate_d1_chart
        # for the full rationale.
        chart = await asyncio.to_thread(
            engine.compute,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            varga=varga_upper,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error computing %s: %s", varga_upper, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute {varga_upper} chart.",
        )

    try:
        await engine.persist_chart(
            chart,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
    except SQLAlchemyError as exc:
        logger.exception("Failed to persist %s chart: %s", varga_upper, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"{varga_upper} chart was computed successfully but could "
                "not be saved. Please retry."
            ),
        ) from exc

    return _serialise_chart(chart)
