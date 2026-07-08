"""
AstroOS — Horoscope Router (Task 4)

Exposes the D1 chart generation endpoint.
All business logic lives in HoroscopeEngine; this file handles only
HTTP concerns: input validation, response serialisation, error mapping.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.dependencies import get_ephemeris_service
from apps.api.domain.ephemeris import DignityType
from apps.api.domain.horoscope import D1Chart
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
from apps.api.services.ephemeris_service import EphemerisService
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/horoscope", tags=["Horoscope"])


def _get_horoscope_engine(
    ephe_svc: EphemerisService = Depends(get_ephemeris_service),
) -> HoroscopeEngine:
    """
    Build a HoroscopeEngine using the EphemerisWrapper singleton.

    EphemerisWrapper shares the same underlying swe path as EphemerisService.
    """
    from apps.api.config import get_settings
    settings = get_settings()
    wrapper = EphemerisWrapper(
        ephemeris_path=settings.EPHEMERIS_PATH,
        ayanamsa="lahiri",
    )
    return HoroscopeEngine(wrapper)


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
        chart = engine.generate_d1(
            birth_datetime_utc=request.birth_datetime_utc,
            latitude=request.latitude,
            longitude=request.longitude,
            ayanamsa=request.ayanamsa,
            house_system=request.house_system,
        )
        return _chart_to_response(chart)
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
