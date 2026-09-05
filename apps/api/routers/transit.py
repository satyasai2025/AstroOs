"""
AstroOS — Transit (Gochara) Router

Endpoints
---------
POST /api/v1/transit/current — Compute current (or specified) planetary
                                transits against a natal chart.
POST /api/v1/transit/timeline — Compute transit timeline for animated visualization.
POST /api/v1/transit/exact   — Get exact planetary position at a specific timestamp.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.domain.transit import TransitPlanetResult
from apps.api.schemas.transit import (
    TransitPlanetResponse,
    TransitRequest,
    TransitResponse,
    TransitTimelineRequest,
    TransitTimelineResponse,
)
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.ephemeris_wrapper import (
    EphemerisWrapper,
    datetime_to_jd,
    longitude_to_nakshatra,
    longitude_to_rashi,
)
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.transit_engine import TransitEngine
from apps.api.services.transit_timeline_engine import TransitTimelineEngine
from apps.api.services.vedha_calculator import VedhaCalculator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transit", tags=["Transit"])


# ── DI ────────────────────────────────────────────────────────────────────────


def _get_horoscope_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> HoroscopeEngine:
    return HoroscopeEngine(wrapper)


def _get_transit_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> TransitEngine:
    return TransitEngine(
        wrapper,
        ashtakavarga_engine=AshtakavargaEngine(),
        vedha_calculator=VedhaCalculator(),
    )


def _get_transit_timeline_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> TransitTimelineEngine:
    transit_engine = TransitEngine(
        wrapper,
        ashtakavarga_engine=AshtakavargaEngine(),
        vedha_calculator=VedhaCalculator(),
    )
    return TransitTimelineEngine(
        wrapper=wrapper,
        transit_engine=transit_engine,
    )


# ── Serialisation ──────────────────────────────────────────────────────────────


def _serialise_planet(result: TransitPlanetResult) -> TransitPlanetResponse:
    return TransitPlanetResponse(
        planet=result.planet,
        transit_rashi=result.transit_rashi,
        house_from_natal_moon=result.house_from_natal_moon,
        house_from_natal_ascendant=result.house_from_natal_ascendant,
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


@router.post(
    "/timeline",
    response_model=TransitTimelineResponse,
    summary="Compute transit timeline for animated visualization",
    description=(
        "Computes a series of transit keyframes over a time range for "
        "animated visualization. Returns adaptive keyframes with events, "
        "Panchanga, Navamsha, combustion, and dignity data."
    ),
)
async def compute_transit_timeline(
    body: TransitTimelineRequest,
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    timeline_engine: TransitTimelineEngine = Depends(_get_transit_timeline_engine),
) -> TransitTimelineResponse:
    try:
        natal_chart = await asyncio.to_thread(
            horoscope_engine.generate_d1,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )

        result = await asyncio.to_thread(
            timeline_engine.compute_timeline,
            natal_chart=natal_chart,
            start_datetime_utc=body.start_datetime_utc,
            end_datetime_utc=body.end_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            interval_minutes=body.interval_minutes,
            adaptive=body.adaptive,
            include_panchanga=body.include_panchanga,
            include_navamsha=body.include_navamsha,
            include_combustion=body.include_combustion,
            include_dignity=body.include_dignity,
            planets=body.planets,
        )

        return TransitTimelineResponse(
            request={
                "start_datetime_utc": body.start_datetime_utc.isoformat(),
                "end_datetime_utc": body.end_datetime_utc.isoformat(),
                "interval_minutes": body.interval_minutes,
                "adaptive": body.adaptive,
            },
            keyframes=result["keyframes"],
            events=result["events"],
            computed_range=result["computed_range"],
            actual_intervals=result.get("actual_intervals"),
        )

    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error computing transit timeline: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute transit timeline.",
        )


# ── Exact Position (for Planet Intelligence) ──────────────────────────────────


class ExactPositionRequest(BaseModel):
    """Request for exact planetary position at a specific timestamp."""
    birth_datetime_utc: datetime
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    ayanamsa: str = "lahiri"
    house_system: str = "W"
    transit_datetime_utc: datetime
    planet: str

    @field_validator("birth_datetime_utc", "transit_datetime_utc")
    @classmethod
    def must_be_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("datetime fields must be timezone-aware.")
        return v


class ExactPositionResponse(BaseModel):
    """Exact planetary position at a specific timestamp."""
    planet: str
    datetime_utc: datetime
    sidereal_longitude: float
    rashi: str
    rashi_degree: float
    rashi_minute: int
    rashi_second: int
    is_direct: bool
    is_station: bool
    speed_deg_per_day: float
    nakshatra: str
    pada: int
    degree_in_nakshatra: float
    navamsha_rashi: str
    navamsha_lord: str
    is_combust: bool
    combustion_orb: Optional[float]
    dignity: Optional[str]
    house_from_natal_moon: int
    house_from_natal_ascendant: int
    aspects: list[str]


@router.post(
    "/exact",
    response_model=ExactPositionResponse,
    summary="Get exact planetary position at a specific timestamp",
    description=(
        "Returns the exact astrological position for a single planet "
        "at an exact datetime. Used by Planet Intelligence panel."
    ),
)
async def get_exact_position(
    body: ExactPositionRequest,
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    transit_engine: TransitEngine = Depends(_get_transit_engine),
    timeline_engine: TransitTimelineEngine = Depends(_get_transit_timeline_engine),
) -> ExactPositionResponse:
    try:
        natal_chart = await asyncio.to_thread(
            horoscope_engine.generate_d1,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )

        transit_results = await asyncio.to_thread(
            transit_engine.compute_transit,
            natal_chart=natal_chart,
            transit_datetime_utc=body.transit_datetime_utc,
        )

        result = next((p for p in transit_results if p.planet == body.planet), None)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Planet {body.planet} not found",
            )

        sidereal_lon = timeline_engine._get_sidereal_longitude(body.planet, body.transit_datetime_utc)
        degree_in_nak = timeline_engine._get_degree_in_nakshatra(body.planet, body.transit_datetime_utc)
        navamsha_rashi = timeline_engine._get_navamsha(body.planet, body.transit_datetime_utc)

        return ExactPositionResponse(
            planet=result.planet,
            datetime_utc=body.transit_datetime_utc,
            sidereal_longitude=sidereal_lon,
            rashi=result.transit_rashi,
            rashi_degree=result.transit_rashi_degree,
            rashi_minute=int((result.transit_rashi_degree % 1) * 60),
            rashi_second=int(((result.transit_rashi_degree % 1) * 60 % 1) * 60),
            is_direct=not result.is_retrograde,
            is_station=abs(result.speed_deg_per_day) < 0.1,
            speed_deg_per_day=result.speed_deg_per_day,
            nakshatra=result.transit_nakshatra,
            pada=result.transit_pada,
            degree_in_nakshatra=degree_in_nak,
            navamsha_rashi=navamsha_rashi,
            navamsha_lord="",
            is_combust=getattr(result, 'is_combust', False),
            combustion_orb=getattr(result, 'combustion_orb', None),
            dignity=getattr(result, 'dignity', None),
            house_from_natal_moon=result.house_from_natal_moon,
            house_from_natal_ascendant=result.house_from_natal_ascendant,
            aspects=[],
        )

    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error computing exact position: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute exact position.",
        )


# ── Live Sky Transit Endpoint ──────────────────────────────────────────────────


class LiveSkyRequest(BaseModel):
    datetime_utc: Optional[datetime] = None
    latitude: Optional[float] = 28.6139
    longitude: Optional[float] = 77.2090
    ayanamsa: Optional[str] = "lahiri"


class LiveSkyPlanetResponse(BaseModel):
    symbol: str
    name: str
    is_lunar_node: bool
    sidereal_longitude: float
    rashi: str
    rashi_sanskrit: str
    degree_in_sign: float
    degree_formatted: str
    speed_deg_per_day: float
    is_retrograde: bool
    is_combust: bool
    nakshatra: str
    pada: int
    nakshatra_lord: str
    kakshya_index: int
    kakshya_lord: str
    kakshya_range: str
    color: str


class LiveSkyResponse(BaseModel):
    planets: list[LiveSkyPlanetResponse]
    ayanamsa: str
    ayanamsa_value_deg: float


_PLANET_SYMBOLS = {
    "sun": "☉", "moon": "☽", "mars": "♂", "mercury": "☿",
    "jupiter": "♃", "venus": "♀", "saturn": "♄", "rahu": "☊", "ketu": "☋",
}
_PLANET_DISPLAY_NAMES = {
    "sun": "Sun", "moon": "Moon", "mars": "Mars", "mercury": "Mercury",
    "jupiter": "Jupiter", "venus": "Venus", "saturn": "Saturn", "rahu": "Rahu", "ketu": "Ketu",
}
_PLANET_COLORS = {
    "sun": "#f59e0b", "moon": "#e2e8f0", "mars": "#ef4444", "mercury": "#10b981",
    "jupiter": "#eab308", "venus": "#ec4899", "saturn": "#6366f1", "rahu": "#8b5cf6", "ketu": "#a855f7",
}
_RASHI_SANSKRIT = {
    "aries": "Mesha", "taurus": "Vrishabha", "gemini": "Mithuna", "cancer": "Karka",
    "leo": "Simha", "virgo": "Kanya", "libra": "Tula", "scorpio": "Vrischika",
    "sagittarius": "Dhanu", "capricorn": "Makara", "aquarius": "Kumbha", "pisces": "Meena",
}
_KAKSHYA_LORDS = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon", "Lagna"]
_KAKSHYA_RANGES = [
    "00° 00' - 03° 45'", "03° 45' - 07° 30'", "07° 30' - 11° 15'", "11° 15' - 15° 00'",
    "15° 00' - 18° 45'", "18° 45' - 22° 30'", "22° 30' - 26° 15'", "26° 15' - 30° 00'",
]
_COMBUSTION_ORBS = {
    "moon": 12.0, "mars": 17.0, "mercury": 14.0, "jupiter": 11.0,
    "venus": 10.0, "saturn": 15.0,
}


def _calculate_live_sky(
    dt: datetime,
    ayanamsa_name: str,
    wrapper: EphemerisWrapper,
) -> LiveSkyResponse:
    jd = datetime_to_jd(dt)
    ayan_deg = wrapper.get_ayanamsa(jd)

    sun_pos = wrapper.get_planet_position("sun", jd)
    sun_sid_lon = wrapper.to_sidereal(sun_pos.longitude, ayan_deg)

    planets_out: list[LiveSkyPlanetResponse] = []
    graha_order = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]

    for graha in graha_order:
        pos = wrapper.get_planet_position(graha, jd)
        sid_lon = wrapper.to_sidereal(pos.longitude, ayan_deg)
        rashi_name, deg_in_rashi = longitude_to_rashi(sid_lon)
        nak_info = longitude_to_nakshatra(sid_lon)

        # Kakshya (8 divisions of 3°45' per sign)
        k_idx = min(7, max(0, int(deg_in_rashi / 3.75)))
        k_lord = _KAKSHYA_LORDS[k_idx]
        k_range = _KAKSHYA_RANGES[k_idx]

        # Combustion check against Sun
        is_combust = False
        if graha not in ("sun", "rahu", "ketu"):
            dist = abs(sid_lon - sun_sid_lon) % 360.0
            if dist > 180.0:
                dist = 360.0 - dist
            max_orb = _COMBUSTION_ORBS.get(graha, 10.0)
            if graha == "mercury":
                max_orb = 14.0 if pos.is_retrograde else 12.0
            elif graha == "venus":
                max_orb = 8.0 if pos.is_retrograde else 10.0
            is_combust = dist <= max_orb

        deg_whole = int(deg_in_rashi)
        deg_min = int((deg_in_rashi - deg_whole) * 60)
        formatted = f"{deg_whole}° {deg_min:02d}'"

        planets_out.append(
            LiveSkyPlanetResponse(
                symbol=_PLANET_SYMBOLS[graha],
                name=_PLANET_DISPLAY_NAMES[graha],
                is_lunar_node=graha in ("rahu", "ketu"),
                sidereal_longitude=round(sid_lon, 4),
                rashi=rashi_name.capitalize(),
                rashi_sanskrit=_RASHI_SANSKRIT.get(rashi_name.lower(), rashi_name.capitalize()),
                degree_in_sign=round(deg_in_rashi, 4),
                degree_formatted=formatted,
                speed_deg_per_day=round(pos.speed_deg_per_day, 4),
                is_retrograde=pos.is_retrograde,
                is_combust=is_combust,
                nakshatra=nak_info.nakshatra.replace("_", " ").title(),
                pada=nak_info.pada,
                nakshatra_lord=nak_info.lord.capitalize(),
                kakshya_index=k_idx,
                kakshya_lord=k_lord,
                kakshya_range=k_range,
                color=_PLANET_COLORS[graha],
            )
        )

    return LiveSkyResponse(
        planets=planets_out,
        ayanamsa=ayanamsa_name.capitalize(),
        ayanamsa_value_deg=round(ayan_deg, 4),
    )


@router.post(
    "/live-sky",
    response_model=LiveSkyResponse,
    summary="Real-time astronomical sky transit positions from Swiss Ephemeris",
)
async def post_live_sky(
    body: Optional[LiveSkyRequest] = None,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> LiveSkyResponse:
    dt = body.datetime_utc if body and body.datetime_utc else datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    ayan_name = body.ayanamsa if body and body.ayanamsa else "lahiri"
    return await asyncio.to_thread(_calculate_live_sky, dt, ayan_name, wrapper)


@router.get(
    "/live-sky",
    response_model=LiveSkyResponse,
    summary="Real-time astronomical sky transit positions from Swiss Ephemeris",
)
async def get_live_sky_route(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> LiveSkyResponse:
    dt = datetime.now(timezone.utc)
    return await asyncio.to_thread(_calculate_live_sky, dt, "lahiri", wrapper)