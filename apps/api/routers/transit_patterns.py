"""
AstroOS — Transit Patterns Router

Endpoints
---------
POST /api/v1/transit/patterns — Detect classical transit patterns
    (Sade Sati, Ashtama Shani, planetary returns, transit aspects)
    for a given birth chart and transit moment.

Extends the existing /transit/current endpoint with pattern-level
analysis — configurable orbs, phase detection, and date estimation.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.schemas.transit_patterns import (
    AshtamaShaniResponse,
    ReturnPeriodResponse,
    SadeSatiResponse,
    TransitAspectResponse,
    TransitPatternsRequest,
    TransitPatternsResponse,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.transit_patterns import (
    AshtamaShaniInfo,
    ReturnPeriodInfo,
    SadeSatiInfo,
    TransitAspectInfo,
    TransitPatternDetector,
    TransitPatternResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transit", tags=["Transit"])


# ── DI ────────────────────────────────────────────────────────────────────────


def _get_horoscope_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> HoroscopeEngine:
    """Build a HoroscopeEngine using the process-wide EphemerisWrapper singleton."""
    return HoroscopeEngine(wrapper)


def _get_pattern_detector(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> TransitPatternDetector:
    """Build a TransitPatternDetector using the process-wide EphemerisWrapper."""
    return TransitPatternDetector(wrapper)


# ── Serialisation ──────────────────────────────────────────────────────────────


def _serialise_sade_sati(info: SadeSatiInfo) -> SadeSatiResponse:
    return SadeSatiResponse(
        is_active=info.is_active,
        phase=info.phase,
        house_from_moon=info.house_from_moon,
        start_date=info.start_date,
        end_date=info.end_date,
    )


def _serialise_ashtama_shani(info: AshtamaShaniInfo) -> AshtamaShaniResponse:
    return AshtamaShaniResponse(
        is_active=info.is_active,
        house_from_moon=info.house_from_moon,
        start_date=info.start_date,
        end_date=info.end_date,
    )


def _serialise_return_period(rp: ReturnPeriodInfo) -> ReturnPeriodResponse:
    return ReturnPeriodResponse(
        planet=rp.planet,
        is_at_return=rp.is_at_return,
        orb=round(rp.orb, 4),
        estimated_return_date=rp.estimated_return_date,
    )


def _serialise_aspect(a: TransitAspectInfo) -> TransitAspectResponse:
    return TransitAspectResponse(
        aspect_type=a.aspect_type,
        transiting_planet=a.transiting_planet,
        natal_planet=a.natal_planet,
        orb=round(a.orb, 4),
    )


def _serialise_result(result: TransitPatternResult) -> TransitPatternsResponse:
    return TransitPatternsResponse(
        transit_datetime_utc=result.transit_datetime_utc,
        natal_moon_rashi=result.natal_moon_rashi,
        sade_sati=_serialise_sade_sati(result.sade_sati),
        ashtama_shani=_serialise_ashtama_shani(result.ashtama_shani),
        return_periods=[_serialise_return_period(rp) for rp in result.return_periods],
        aspects=[_serialise_aspect(a) for a in result.aspects],
    )


# ── Routes ────────────────────────────────────────────────────────────────────


@router.post(
    "/patterns",
    response_model=TransitPatternsResponse,
    summary="Detect classical transit patterns",
    description=(
        "Builds a D1 chart from the given birth data, then detects classical "
        "Vedic transit patterns at the specified transit moment (or now if "
        "omitted).  Returns Sade Sati phase, Ashtama Shani, planetary return "
        "periods, and transit aspects (conjunction / opposition / trine / "
        "square / sextile) between transiting and natal planets.  Aspect "
        "and return orbs are configurable.\n\n"
        "All calculations are deterministic — no AI or external API calls."
    ),
)
async def detect_transit_patterns(
    body: TransitPatternsRequest,
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    pattern_detector: TransitPatternDetector = Depends(_get_pattern_detector),
) -> TransitPatternsResponse:
    transit_datetime_utc = body.resolved_transit_datetime_utc()

    try:
        # Blocking pyswisseph — offload to worker thread
        natal_chart = await asyncio.to_thread(
            horoscope_engine.generate_d1,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
        result = await asyncio.to_thread(
            pattern_detector.detect_patterns,
            natal_chart=natal_chart,
            transit_datetime_utc=transit_datetime_utc,
            aspect_orb=body.aspect_orb,
            return_orb=body.return_orb,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("Error detecting transit patterns: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to detect transit patterns.",
        )

    return _serialise_result(result)
