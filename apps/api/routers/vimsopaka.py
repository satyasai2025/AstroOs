"""
AstroOS — Vimsopaka Bala Router

POST /api/v1/vimsopaka/all — Vimsopaka Bala across 4 Parashari Varga schemes
(Shadvarga, Saptavarga, Dasavarga, Shodasavarga) for every classical planet.

Compute-only endpoint (no persistence — delegates to VimsopakaEngine & DivisionalEngine).
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.domain.horoscope import D1Chart
from apps.api.schemas.shadbala import ShadbalaRequest
from apps.api.schemas.vimsopaka import (
    VargaDignityScoreResponse,
    VimsopakaListResponse,
    VimsopakaPlanetResponse,
    VimsopakaSchemeResponse,
)
from apps.api.services.divisional_engine import DivisionalEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.vimsopaka_engine import VimsopakaEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vimsopaka", tags=["Vimsopaka"])


def _get_horoscope_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> HoroscopeEngine:
    return HoroscopeEngine(wrapper)


def _get_divisional_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> DivisionalEngine:
    return DivisionalEngine(wrapper)


async def _build_chart(
    horoscope_engine: HoroscopeEngine, body: ShadbalaRequest
) -> D1Chart:
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
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except Exception as exc:
        logger.exception("Error building D1 chart for Vimsopaka Bala: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to build birth chart for Vimsopaka computation.",
        ) from exc


@router.post(
    "/all",
    response_model=VimsopakaListResponse,
    summary="Compute Vimsopaka Bala across 4 Varga schemes for every planet",
    description=(
        "Vimsopaka Bala (20-point divisional strength scale) for the 7 classical grahas "
        "across Shadvarga (6 vargas), Saptavarga (7 vargas), Dasavarga (10 vargas), "
        "and Shodasavarga (16 vargas) schemes."
    ),
)
async def compute_vimsopaka(
    body: ShadbalaRequest,
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    divisional_engine: DivisionalEngine = Depends(_get_divisional_engine),
) -> VimsopakaListResponse:
    chart = await _build_chart(horoscope_engine, body)
    engine = VimsopakaEngine(divisional_engine)

    try:
        res = await asyncio.to_thread(
            engine.compute_all,
            chart,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
    except Exception as exc:
        logger.exception("Error computing Vimsopaka Bala: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute Vimsopaka Bala.",
        ) from exc

    planet_responses = []
    for p in res.planets:
        def _scheme_to_response(s) -> VimsopakaSchemeResponse:
            return VimsopakaSchemeResponse(
                scheme_name=s.scheme_name,
                total_weight=s.total_weight,
                vimsopaka_score=s.vimsopaka_score,
                category=s.category,
                varga_breakdown=[
                    VargaDignityScoreResponse(
                        varga=v.varga,
                        varga_rashi=v.varga_rashi,
                        dignity=v.dignity,
                        weight=v.weight,
                        base_points=v.base_points,
                        weighted_points=v.weighted_points,
                    )
                    for v in s.varga_breakdown
                ],
            )

        planet_responses.append(
            VimsopakaPlanetResponse(
                planet=p.planet,
                shadvarga=_scheme_to_response(p.shadvarga),
                saptavarga=_scheme_to_response(p.saptavarga),
                dasavarga=_scheme_to_response(p.dasavarga),
                shodasavarga=_scheme_to_response(p.shodasavarga),
            )
        )

    return VimsopakaListResponse(planets=planet_responses)
