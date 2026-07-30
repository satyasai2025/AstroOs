"""
AstroOS — Transit (Gochara) Router

Endpoints
---------
POST /api/v1/transit/current — Compute current (or specified) planetary
                                transits against a natal chart.

Genuinely different request shape from Dasha/Divisional: TransitEngine
needs the natal D1 chart (built here via HoroscopeEngine, same as
horoscope.py's /d1 endpoint) PLUS an independent moment in time
("transit_datetime_utc") to compute transiting positions against — see
services/transit_engine.py's docstring.

Transit is also reachable embedded inside Events (fact_builder.py), but
that path requires a saved event. This endpoint is standalone: birth
data and a transit moment in, results out, no event required.

TransitEngine has no persistence layer (same scope discipline as every
engine before it — see its docstring), so this endpoint computes and
returns without saving anything. No repositories are constructed here
for that reason.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.domain.transit import TransitPlanetResult
from apps.api.schemas.transit import TransitPlanetResponse, TransitRequest, TransitResponse
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.transit_engine import TransitEngine
from apps.api.services.vedha_calculator import VedhaCalculator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transit", tags=["Transit"])


# ── DI ────────────────────────────────────────────────────────────────────────


def _get_horoscope_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> HoroscopeEngine:
    """
    Build a HoroscopeEngine using the process-wide EphemerisWrapper
    singleton, to compute the natal D1 chart Transit is read against.

    Does NOT construct a new EphemerisWrapper — see get_ephemeris_wrapper's
    docstring for why that would reintroduce a global-state race condition.
    No repositories are passed in: this router never calls persist_d1.
    """
    return HoroscopeEngine(wrapper)


def _get_transit_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> TransitEngine:
    """
    TransitEngine needs the same process-wide EphemerisWrapper singleton
    (to compute transiting positions independently of the natal chart),
    plus an AshtakavargaEngine and VedhaCalculator — both stateless and
    cheap to construct per-request (see services/transit_engine.py).
    """
    return TransitEngine(
        wrapper,
        ashtakavarga_engine=AshtakavargaEngine(),
        vedha_calculator=VedhaCalculator(),
    )


# ── Serialisation ──────────────────────────────────────────────────────────────


def _serialise_planet(result: TransitPlanetResult) -> TransitPlanetResponse:
    return TransitPlanetResponse(
        planet=result.planet,
        transit_rashi=result.transit_rashi,
        house_from_natal_moon=result.house_from_natal_moon,
        ashtakavarga_bindus=result.ashtakavarga_bindus,
        is_sade_sati=result.is_sade_sati,
        is_ashtama_shani=result.is_ashtama_shani,
        is_favorable_house=result.is_favorable_house,
        has_vedha=result.has_vedha,
        has_vipreet_vedha=result.has_vipreet_vedha,
        vedha_planet=result.vedha_planet,
        transit_nakshatra_sbc=result.transit_nakshatra_sbc,
        has_nakshatra_vedha=result.has_nakshatra_vedha,
        nakshatra_vedha_planet=result.nakshatra_vedha_planet,
        nakshatra_vedha_type=result.nakshatra_vedha_type,
        nakshatra_vedha_target=result.nakshatra_vedha_target,
        rule_version=result.rule_version,
        transit_rashi_degree=result.transit_rashi_degree,
        transit_nakshatra=result.transit_nakshatra,
        transit_pada=result.transit_pada,
        is_retrograde=result.is_retrograde,
        speed_deg_per_day=result.speed_deg_per_day,
        gati=result.gati,
    )


# ── Routes ────────────────────────────────────────────────────────────────────


@router.post(
    "/current",
    response_model=TransitResponse,
    summary="Compute current (or specified) transits against a natal chart",
    description=(
        "Builds a D1 chart from the given birth data, then computes each "
        "of the nine grahas' Gochara (transit) read — transiting rashi, "
        "house from natal Moon, Ashtakavarga bindus, Sade Sati/Ashtama "
        "Shani flags, and Vedha/Vipreet Vedha obstruction — at "
        "transit_datetime_utc (defaults to now, UTC, if omitted)."
    ),
)
async def compute_current_transit(
    body: TransitRequest,
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    transit_engine: TransitEngine = Depends(_get_transit_engine),
) -> TransitResponse:
    transit_datetime_utc = body.resolved_transit_datetime_utc()

    try:
        # Blocking pyswisseph calls — offload to a worker thread so they
        # do not freeze the event loop. See horoscope.py's
        # generate_d1_chart for the full rationale.
        natal_chart = await asyncio.to_thread(
            horoscope_engine.generate_d1,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
        planet_results = await asyncio.to_thread(
            transit_engine.compute_transit,
            natal_chart=natal_chart,
            transit_datetime_utc=transit_datetime_utc,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error computing transit: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute transit.",
        )

    natal_moon_rashi = next(p.rashi for p in natal_chart.planets if p.planet == "moon")

    return TransitResponse(
        transit_datetime_utc=transit_datetime_utc,
        natal_moon_rashi=natal_moon_rashi,
        planets=[_serialise_planet(r) for r in planet_results],
    )
