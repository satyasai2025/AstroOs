"""
AstroOS — Varshaphal Router (Stage 1: Varsha Pravesh chart + Muntha;
Stage 2: Tajika aspects; Stage 3: Year Lord; Stage 4: Sahams)

Endpoints
---------
POST /api/v1/varshaphal   — Annual (solar-return) chart + Muntha + Tajika
                            aspects + Year Lord + Sahams (Punya, Vidya)

No business logic lives here — computation is delegated to VarshaphalEngine.
Not yet exposed: the other 34 Sahams, Mudda/Patyayini Dasha — see
services/varshaphal_engine.py's module docstring.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.domain.ephemeris import EphemerisResult, SiderealPosition
from apps.api.domain.varshaphal import (
    MunthaInfo,
    SahamInfo,
    TajikaAspect,
    VarshaphalResult,
    YearLordInfo,
)
from apps.api.schemas.horoscope import (
    KaranaSchema,
    NakshatraInfoSchema,
    PanchangaSchema,
    TithiSchema,
    VaraSchema,
    YogaSchema,
)
from apps.api.schemas.varshaphal import (
    MunthaSchema,
    SahamSchema,
    TajikaAspectSchema,
    VarshaAscendantSchema,
    VarshaHouseCuspSchema,
    VarshaPlanetPositionSchema,
    VarshaphalRequest,
    VarshaphalResponse,
    YearLordSchema,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper, jd_to_datetime
from apps.api.services.varshaphal_engine import VarshaphalEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/varshaphal", tags=["Varshaphal"])


def _get_varshaphal_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> VarshaphalEngine:
    return VarshaphalEngine(wrapper)


def _serialise_panchanga(chart: EphemerisResult) -> PanchangaSchema:
    p = chart.panchanga
    return PanchangaSchema(
        tithi=TithiSchema(
            number=p.tithi.number, name=p.tithi.name,
            paksha=p.tithi.paksha, completion_percent=p.tithi.completion_percent,
        ),
        nakshatra=NakshatraInfoSchema(
            nakshatra=p.nakshatra.nakshatra, nakshatra_number=p.nakshatra.nakshatra_number,
            pada=p.nakshatra.pada, lord=p.nakshatra.lord,
            degree_in_nakshatra=p.nakshatra.degree_in_nakshatra,
            degree_in_pada=p.nakshatra.degree_in_pada,
        ),
        yoga=YogaSchema(
            number=p.yoga.number, name=p.yoga.name, completion_percent=p.yoga.completion_percent,
        ),
        karana=KaranaSchema(number=p.karana.number, name=p.karana.name, is_fixed=p.karana.is_fixed),
        vara=VaraSchema(number=p.vara.number, name=p.vara.name, lord=p.vara.lord),
        julian_day=p.julian_day,
        ayanamsa_deg=p.ayanamsa_deg,
    )


def _serialise_planet(pl: SiderealPosition) -> VarshaPlanetPositionSchema:
    return VarshaPlanetPositionSchema(
        planet=pl.planet, sidereal_longitude=pl.sidereal_longitude,
        rashi=pl.rashi, rashi_degree=pl.rashi_degree, house_number=pl.house_number,
        nakshatra=pl.nakshatra, pada=pl.pada, is_retrograde=pl.is_retrograde,
        is_combust=pl.is_combust, dignity=pl.dignity.value if pl.dignity else None,
    )


def _serialise_muntha(m: MunthaInfo) -> MunthaSchema:
    return MunthaSchema(rashi=m.rashi, rashi_index=m.rashi_index, house_number=m.house_number)


def _serialise_tajika_aspect(a: TajikaAspect) -> TajikaAspectSchema:
    return TajikaAspectSchema(
        planet_a=a.planet_a, planet_b=a.planet_b, aspect_angle=a.aspect_angle,
        current_orb_deg=a.current_orb_deg, is_applying=a.is_applying,
        is_ithasala=a.is_ithasala, is_isharpha=a.is_isharpha, days_to_exact=a.days_to_exact,
    )


def _serialise_year_lord(y: YearLordInfo) -> YearLordSchema:
    return YearLordSchema(
        candidates=list(y.candidates), selected=y.selected, selection_method=y.selection_method,
    )


def _serialise_saham(s: SahamInfo) -> SahamSchema:
    return SahamSchema(name=s.name, sidereal_longitude=s.sidereal_longitude, rashi=s.rashi)


def _serialise_result(r: VarshaphalResult) -> VarshaphalResponse:
    chart = r.varsha_chart
    return VarshaphalResponse(
        varsha_year=r.varsha_year,
        solar_return_utc=jd_to_datetime(r.solar_return_jd),
        ascendant=VarshaAscendantSchema(
            longitude=chart.ascendant.longitude,
            sidereal_longitude=chart.ascendant.sidereal_longitude,
            rashi=chart.ascendant.rashi, rashi_degree=chart.ascendant.rashi_degree,
            nakshatra=chart.ascendant.nakshatra, pada=chart.ascendant.pada,
            nakshatra_lord=chart.ascendant.nakshatra_lord,
        ),
        houses=[
            VarshaHouseCuspSchema(
                house_number=h.house_number, sidereal_longitude=h.sidereal_longitude, rashi=h.rashi,
            )
            for h in chart.house_cusps
        ],
        planets=[_serialise_planet(pl) for pl in chart.planet_positions],
        panchanga=_serialise_panchanga(chart),
        muntha=_serialise_muntha(r.muntha),
        tajika_aspects=[_serialise_tajika_aspect(a) for a in r.tajika_aspects],
        year_lord=_serialise_year_lord(r.year_lord),
        sahams=[_serialise_saham(s) for s in r.sahams],
    )


@router.post(
    "",
    response_model=VarshaphalResponse,
    summary="Varsha Pravesh (solar-return) chart + Muntha for a given year",
)
async def get_varshaphal(
    body: VarshaphalRequest,
    engine: VarshaphalEngine = Depends(_get_varshaphal_engine),
) -> VarshaphalResponse:
    try:
        # Blocking pyswisseph calls (solver + two full chart computations) —
        # offload to a worker thread so the event loop isn't blocked.
        result = await asyncio.to_thread(
            engine.calculate,
            birth_dt=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            varsha_year=body.varsha_year,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error computing Varshaphal chart: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute Varshaphal chart.",
        )

    return _serialise_result(result)
