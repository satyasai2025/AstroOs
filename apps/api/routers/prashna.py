"""
AstroOS — Prashna (Horary) Router

Endpoints
---------
GET  /api/v1/prashna/arudha    — Prashna Arudha for a seed number (1-249), no ephemeris
POST /api/v1/prashna/sphutas   — The six Sphutas for a query/birth moment + location

No business logic lives here — computation is delegated to PrashnaEngine.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.domain.prashna import PrashnaArudhaResult, PrashnaSphutaResult, SphutaPosition
from apps.api.schemas.prashna import (
    PrashnaArudhaResponse,
    PrashnaSphutaRequest,
    PrashnaSphutaResponse,
    SphutaPositionResponse,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.prashna_engine import PrashnaEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prashna", tags=["Prashna"])


def _get_prashna_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> PrashnaEngine:
    return PrashnaEngine(wrapper)


def _serialise_arudha(r: PrashnaArudhaResult) -> PrashnaArudhaResponse:
    return PrashnaArudhaResponse(
        seed_number=r.seed_number,
        sidereal_longitude=r.sidereal_longitude,
        rashi=r.rashi,
        rashi_degree=r.rashi_degree,
        nakshatra=r.nakshatra,
        sign_lord=r.sign_lord,
        star_lord=r.star_lord,
        sub_lord=r.sub_lord,
        arc_start_degree=r.arc_start_degree,
        arc_end_degree=r.arc_end_degree,
    )


def _serialise_sphuta(s: SphutaPosition) -> SphutaPositionResponse:
    return SphutaPositionResponse(
        name=s.name,
        sidereal_longitude=s.sidereal_longitude,
        rashi=s.rashi,
        rashi_degree=s.rashi_degree,
        nakshatra=s.nakshatra,
        pada=s.pada,
        nakshatra_lord=s.nakshatra_lord,
        house_number=s.house_number,
    )


def _serialise_sphuta_result(r: PrashnaSphutaResult) -> PrashnaSphutaResponse:
    return PrashnaSphutaResponse(
        sphutas=[_serialise_sphuta(s) for s in r.sphutas],
        ascendant_longitude=r.ascendant_longitude,
        gulika_longitude=r.gulika_longitude,
    )


@router.get(
    "/arudha",
    response_model=PrashnaArudhaResponse,
    summary="Prashna Arudha for a horary seed number (1-249)",
)
async def get_prashna_arudha(
    seed_number: int = Query(..., ge=1, le=249, description="Horary number chosen by the querent."),
    engine: PrashnaEngine = Depends(_get_prashna_engine),
) -> PrashnaArudhaResponse:
    try:
        result = engine.arudha_from_seed(seed_number)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    return _serialise_arudha(result)


@router.post(
    "/sphutas",
    response_model=PrashnaSphutaResponse,
    summary="Trisphuta/Chatursphuta/Panchasphuta/Pranasphuta/Dehasphuta/Mrityusphuta for a moment + location",
)
async def get_prashna_sphutas(
    body: PrashnaSphutaRequest,
    engine: PrashnaEngine = Depends(_get_prashna_engine),
) -> PrashnaSphutaResponse:
    try:
        result = engine.compute_sphutas(
            body.moment_utc, body.latitude, body.longitude, body.ayanamsa
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    return _serialise_sphuta_result(result)
