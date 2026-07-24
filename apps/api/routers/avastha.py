"""
AstroOS — Avastha Router

POST /api/v1/avastha/all — Baladi + Deeptadi Avastha for every planet.

Compute-only, same pattern as routers/shadbala.py (no persistence, no
business logic here — delegates to AvasthaEngine). See
services/avastha_engine.py's module docstring for exactly which
Avastha systems are implemented and why Jagradadi Avastha is not.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.domain.horoscope import D1Chart
from apps.api.schemas.avastha import AvasthaListResponse, AvasthaResponse
from apps.api.schemas.shadbala import ShadbalaRequest
from apps.api.services.avastha_engine import AvasthaEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/avastha", tags=["Avastha"])


def _get_horoscope_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> HoroscopeEngine:
    return HoroscopeEngine(wrapper)


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
        logger.exception("Error building D1 chart for Avastha: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to build birth chart for Avastha computation.",
        ) from exc


@router.post(
    "/all",
    response_model=AvasthaListResponse,
    summary="Compute Baladi + Deeptadi Avastha for every planet",
    description=(
        "Baladi (degree-based 5-fold) and Deeptadi (dignity-based) "
        "planetary states. Jagradadi Avastha is not implemented — see "
        "'not_implemented' in the response and services/avastha_engine.py's "
        "module docstring for why."
    ),
)
async def compute_avastha(
    body: ShadbalaRequest,
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
) -> AvasthaListResponse:
    chart = await _build_chart(horoscope_engine, body)
    engine = AvasthaEngine()
    try:
        results = await asyncio.to_thread(engine.compute_all, chart.planets)
    except Exception as exc:
        logger.exception("Error computing Avastha: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute Avastha.",
        ) from exc

    return AvasthaListResponse(
        avasthas=[
            AvasthaResponse(
                planet=r.planet,
                baladi_avastha=r.baladi_avastha,
                baladi_trace=list(r.baladi_trace),
                deeptadi_avastha=r.deeptadi_avastha,
                deeptadi_trace=list(r.deeptadi_trace),
            )
            for r in results
        ],
    )
