"""
AstroOS — Horoscope Router (Task 4)

Exposes the D1 chart generation endpoint.
All business logic lives in HoroscopeEngine; this file handles only
HTTP concerns: input validation, response serialisation, error mapping.
"""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import get_db_session, get_ephemeris_wrapper
from apps.api.domain.ephemeris import DignityType
from apps.api.domain.horoscope import D1Chart
from apps.api.repositories.birth_chart_repository import BirthChartRepository
from apps.api.repositories.house_repository import HouseRepository
from apps.api.repositories.planet_position_repository import PlanetPositionRepository
from apps.api.schemas.horoscope import (
    AscendantSchema,
    AspectSchema,
    D1ChartRequest,
    D1ChartResponse,
    HouseCuspSchema,
    KaranaSchema,
    NakshatraInfoSchema,
    PanchangaSchema,
    PlanetPositionSchema,
    PlanetStrengthSchema,
    TithiSchema,
    VaraSchema,
    YogaSchema,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/horoscope", tags=["Horoscope"])


def _get_horoscope_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
    session: AsyncSession = Depends(get_db_session),
) -> HoroscopeEngine:
    """
    Build a HoroscopeEngine using the process-wide EphemerisWrapper singleton,
    plus request-scoped repositories for persistence.

    Does NOT construct a new EphemerisWrapper — see get_ephemeris_wrapper's
    docstring for why that would reintroduce a global-state race condition.
    The repositories, unlike the wrapper, are cheap and request-scoped —
    each request gets its own, bound to that request's DB session.
    """
    return HoroscopeEngine(
        wrapper,
        birth_chart_repo=BirthChartRepository(session),
        planet_position_repo=PlanetPositionRepository(session),
        house_repo=HouseRepository(session),
    )


def _chart_to_response(chart: D1Chart) -> D1ChartResponse:
    """Convert a D1Chart domain object to the HTTP response schema."""

    ascendant = AscendantSchema(
        longitude=chart.ascendant.longitude,
        sidereal_longitude=chart.ascendant.sidereal_longitude,
        rashi=chart.ascendant.rashi,
        rashi_degree=round(chart.ascendant.rashi_degree, 6),
        nakshatra=chart.ascendant.nakshatra,
        pada=chart.ascendant.pada,
    )

    houses = [
        HouseCuspSchema(
            house_number=h.house_number,
            longitude=round(h.longitude, 6),
            sidereal_longitude=round(h.sidereal_longitude, 6),
            rashi=h.rashi,
        )
        for h in chart.houses
    ]

    planets = [
        PlanetPositionSchema(
            planet=p.planet,
            sidereal_longitude=round(p.sidereal_longitude, 6),
            rashi=p.rashi,
            rashi_degree=round(p.rashi_degree, 6),
            house_number=p.house_number,
            nakshatra=p.nakshatra,
            pada=p.pada,
            is_retrograde=p.is_retrograde,
            is_combust=p.is_combust,
            combustion_orb=round(p.combustion_orb, 6) if p.combustion_orb is not None else None,
            dignity=p.dignity.value if p.dignity else None,
        )
        for p in chart.planets
    ]

    aspects = [
        AspectSchema(
            from_planet=a.from_planet,
            to_planet=a.to_planet,
            aspect_type=a.aspect_type,
            orb_degrees=a.orb_degrees,
            is_applying=a.is_applying,
        )
        for a in chart.aspects
    ]

    strengths = [
        PlanetStrengthSchema(
            planet=s.planet,
            dignity=s.dignity.value if s.dignity else None,
            is_retrograde=s.is_retrograde,
            is_combust=s.is_combust,
            house_number=s.house_number,
            is_in_own_sign=s.is_in_own_sign,
            is_exalted=s.is_exalted,
            is_debilitated=s.is_debilitated,
            is_in_kendra=s.is_in_kendra,
            is_in_trikona=s.is_in_trikona,
            is_in_dusthana=s.is_in_dusthana,
            strength_score=s.strength_score,
        )
        for s in chart.planet_strengths
    ]

    panchanga = chart.panchanga
    pan_schema = PanchangaSchema(
        tithi=TithiSchema(
            number=panchanga.tithi.number,
            name=panchanga.tithi.name,
            paksha=panchanga.tithi.paksha,
            completion_percent=panchanga.tithi.completion_percent,
        ),
        nakshatra=NakshatraInfoSchema(
            nakshatra=panchanga.nakshatra.nakshatra,
            nakshatra_number=panchanga.nakshatra.nakshatra_number,
            pada=panchanga.nakshatra.pada,
            lord=panchanga.nakshatra.lord,
            degree_in_nakshatra=round(panchanga.nakshatra.degree_in_nakshatra, 6),
            degree_in_pada=round(panchanga.nakshatra.degree_in_pada, 6),
        ),
        yoga=YogaSchema(
            number=panchanga.yoga.number,
            name=panchanga.yoga.name,
            completion_percent=panchanga.yoga.completion_percent,
        ),
        karana=KaranaSchema(
            number=panchanga.karana.number,
            name=panchanga.karana.name,
            is_fixed=panchanga.karana.is_fixed,
        ),
        vara=VaraSchema(
            number=panchanga.vara.number,
            name=panchanga.vara.name,
            lord=panchanga.vara.lord,
        ),
        julian_day=panchanga.julian_day,
        ayanamsa_deg=round(panchanga.ayanamsa_deg, 8),
    )

    return D1ChartResponse(
        ascendant=ascendant,
        houses=houses,
        planets=planets,
        aspects=aspects,
        planet_strengths=strengths,
        panchanga=pan_schema,
        ayanamsa_system=chart.ayanamsa_system,
        house_system=chart.house_system,
        julian_day=chart.ephemeris.julian_day,
        ayanamsa_value=round(chart.ephemeris.ayanamsa_value, 8),
    )


@router.post(
    "/d1",
    response_model=D1ChartResponse,
    summary="Generate D1 (Rashi) birth chart",
    description=(
        "Calculates the complete Rashi chart (D1) for the given birth data. "
        "Returns all nine Graha positions, house cusps, aspects, planet strengths, "
        "and the Panchanga (Tithi, Nakshatra, Yoga, Karana, Vara)."
    ),
    status_code=status.HTTP_200_OK,
)
async def generate_d1_chart(
    request: D1ChartRequest,
    engine: HoroscopeEngine = Depends(_get_horoscope_engine),
) -> D1ChartResponse:
    """
    Generate a D1 (Rashi) birth chart.

    - **birth_datetime_utc**: UTC birth datetime (must include timezone, e.g. `2000-01-01T05:30:00+00:00`)
    - **latitude**: Decimal degrees (+N / -S)
    - **longitude**: Decimal degrees (+E / -W)
    - **ayanamsa**: `lahiri` (default) | `kp` | `raman` | `yukteshwar` | `fagan_bradley` | `true_chitra`
    - **house_system**: `W` = Whole Sign (default) | `P` = Placidus | `K` = Koch | `E` = Equal
    """
    try:
        # generate_d1 is a blocking, CPU-bound call into pyswisseph's C
        # library. Running it directly inside this async handler would
        # freeze the event loop for every other in-flight request (auth,
        # health checks, everything) for the duration of the calculation.
        # asyncio.to_thread offloads it to a worker thread; the wrapper's
        # internal lock (see EphemerisWrapper.calculate) still serializes
        # access to pyswisseph's process-global state across those threads.
        chart = await asyncio.to_thread(
            engine.generate_d1,
            birth_datetime_utc=request.birth_datetime_utc,
            latitude=request.latitude,
            longitude=request.longitude,
            ayanamsa=request.ayanamsa,
            house_system=request.house_system,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        logger.exception("Swiss Ephemeris calculation error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ephemeris calculation failed. Check server logs.",
        ) from exc

    # Persistence step. The calculation above already succeeded and its
    # result is what we return either way — but if saving it fails, that
    # is reported as an error rather than silently returned as if nothing
    # was persisted. get_db_session's session (see apps/api/dependencies.py)
    # rolls back automatically once this exception propagates out of the
    # request, so a failed persist never leaves a partial chart committed.
    try:
        await engine.persist_d1(
            chart,
            birth_datetime_utc=request.birth_datetime_utc,
            latitude=request.latitude,
            longitude=request.longitude,
            ayanamsa=request.ayanamsa,
            house_system=request.house_system,
        )
    except SQLAlchemyError as exc:
        logger.exception("Failed to persist D1 chart: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Chart was computed successfully but could not be saved. "
                "Please retry."
            ),
        ) from exc

    return _chart_to_response(chart)
