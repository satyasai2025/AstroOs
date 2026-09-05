"""
AstroOS — Muhurta and Panchanga Router

Endpoints
---------
GET /api/v1/muhurta — Complete Panchanga, Horas, Choghadiyas, Auspicious Windows,
                      Tarabala, Chandrabala, Panchaka, and Activity Playbook.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.domain.muhurta import (
    ActivitySuitabilityDetail,
    AuspiciousWindowPeriod,
    CelestialBodiesInfo,
    ChandrabalaDetailInfo,
    ChoghadiyaPeriod,
    HoraPeriod,
    InauspiciousPeriod,
    KaranaLimbInfo,
    MuhurtaResult,
    NakshatraLimbInfo,
    PanchakaDetailInfo,
    SamvatsaraMasaLimbInfo,
    TarabalaDetailInfo,
    TithiLimbInfo,
    VaraLimbInfo,
    YogaLimbInfo,
)
from apps.api.schemas.muhurta import (
    ActivitySuitabilityResponse,
    AuspiciousWindowResponse,
    CelestialBodiesResponse,
    ChandrabalaDetailResponse,
    ChoghadiyaResponse,
    HoraResponse,
    InauspiciousPeriodResponse,
    KaranaLimbResponse,
    MuhurtaResponse,
    NakshatraLimbResponse,
    PanchakaDetailResponse,
    SamvatsaraMasaResponse,
    TarabalaDetailResponse,
    TithiLimbResponse,
    VaraLimbResponse,
    YogaLimbResponse,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper, datetime_to_jd, jd_to_datetime
from apps.api.services.muhurta_engine import MuhurtaEngine
from packages.shared.enums import AyanamsaSystem

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/muhurta", tags=["Muhurta"])


def _get_muhurta_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> MuhurtaEngine:
    return MuhurtaEngine(wrapper)


def _serialise_hora(h: HoraPeriod) -> HoraResponse:
    return HoraResponse(
        index=h.index, lord=h.lord,
        start=jd_to_datetime(h.start_jd), end=jd_to_datetime(h.end_jd),
        is_day=h.is_day,
    )


def _serialise_period(p: InauspiciousPeriod) -> InauspiciousPeriodResponse:
    return InauspiciousPeriodResponse(
        name=p.name, start=jd_to_datetime(p.start_jd), end=jd_to_datetime(p.end_jd),
    )


def _serialise_window(w: AuspiciousWindowPeriod) -> AuspiciousWindowResponse:
    return AuspiciousWindowResponse(
        name=w.name, start=jd_to_datetime(w.start_jd), end=jd_to_datetime(w.end_jd),
        is_auspicious=w.is_auspicious, description=w.description,
    )


def _serialise_choghadiya(c: ChoghadiyaPeriod) -> ChoghadiyaResponse:
    return ChoghadiyaResponse(
        index=c.index, name=c.name, nature=c.nature,
        start=jd_to_datetime(c.start_jd), end=jd_to_datetime(c.end_jd),
        is_day=c.is_day, lord=c.lord,
    )


def _serialise_result(r: MuhurtaResult) -> MuhurtaResponse:
    tithi_resp = None
    if r.tithi:
        tithi_resp = TithiLimbResponse(
            number=r.tithi.number, name=r.tithi.name, paksha=r.tithi.paksha,
            completion_percent=r.tithi.completion_percent,
            end_time=jd_to_datetime(r.tithi.end_jd) if r.tithi.end_jd else None,
            lord=r.tithi.lord, group=r.tithi.group,
        )

    vara_resp = None
    if r.vara:
        vara_resp = VaraLimbResponse(
            number=r.vara.number, name=r.vara.name, lord=r.vara.lord, nature=r.vara.nature,
        )

    nakshatra_resp = None
    if r.nakshatra:
        nakshatra_resp = NakshatraLimbResponse(
            number=r.nakshatra.number, name=r.nakshatra.name, pada=r.nakshatra.pada,
            lord=r.nakshatra.lord, degree_in_nakshatra=r.nakshatra.degree_in_nakshatra,
            completion_percent=r.nakshatra.completion_percent,
            end_time=jd_to_datetime(r.nakshatra.end_jd) if r.nakshatra.end_jd else None,
            quality=r.nakshatra.quality,
        )

    yoga_resp = None
    if r.yoga:
        yoga_resp = YogaLimbResponse(
            number=r.yoga.number, name=r.yoga.name,
            completion_percent=r.yoga.completion_percent,
            end_time=jd_to_datetime(r.yoga.end_jd) if r.yoga.end_jd else None,
            meaning=r.yoga.meaning,
        )

    karana_resp = None
    if r.karana:
        karana_resp = KaranaLimbResponse(
            number=r.karana.number, name=r.karana.name, is_fixed=r.karana.is_fixed,
            completion_percent=r.karana.completion_percent,
            end_time=jd_to_datetime(r.karana.end_jd) if r.karana.end_jd else None,
            nature=r.karana.nature,
        )

    calendar_resp = None
    if r.calendar:
        calendar_resp = SamvatsaraMasaResponse(
            shaka_year=r.calendar.shaka_year, shaka_samvatsara=r.calendar.shaka_samvatsara,
            vikram_year=r.calendar.vikram_year, vikram_samvatsara=r.calendar.vikram_samvatsara,
            amanta_masa=r.calendar.amanta_masa, purnimanta_masa=r.calendar.purnimanta_masa,
            is_adhika=r.calendar.is_adhika,
        )

    celestial_resp = None
    if r.celestial:
        celestial_resp = CelestialBodiesResponse(
            sun_sign=r.celestial.sun_sign.replace("_", " ").title(),
            sun_sign_degree=r.celestial.sun_sign_degree,
            sun_longitude=r.celestial.sun_longitude,
            moon_sign=r.celestial.moon_sign.replace("_", " ").title(),
            moon_sign_degree=r.celestial.moon_sign_degree,
            moon_longitude=r.celestial.moon_longitude,
            ascendant_sign=r.celestial.ascendant_sign.replace("_", " ").title(),
            ascendant_degree=r.celestial.ascendant_degree,
            moonrise=jd_to_datetime(r.celestial.moonrise_jd) if r.celestial.moonrise_jd else None,
            moonset=jd_to_datetime(r.celestial.moonset_jd) if r.celestial.moonset_jd else None,
        )

    abhijit_resp = _serialise_window(r.abhijit_muhurta) if r.abhijit_muhurta else None
    brahma_resp = _serialise_window(r.brahma_muhurta) if r.brahma_muhurta else None
    dur_muhurtas_resp = [_serialise_period(d) for d in r.dur_muhurta] if r.dur_muhurta else []
    amrit_resp = _serialise_window(r.amrit_kaal) if r.amrit_kaal else None

    tarabala_resp = None
    if r.tarabala:
        tarabala_resp = TarabalaDetailResponse(
            tara_number=r.tarabala.tara_number, tara_name=r.tarabala.tara_name,
            is_auspicious=r.tarabala.is_auspicious, score=r.tarabala.score,
            description=r.tarabala.description,
        )

    chandrabala_resp = None
    if r.chandrabala:
        chandrabala_resp = ChandrabalaDetailResponse(
            house_from_natal_moon=r.chandrabala.house_from_natal_moon,
            status=r.chandrabala.status, is_auspicious=r.chandrabala.is_auspicious,
            score=r.chandrabala.score, description=r.chandrabala.description,
        )

    panchaka_resp = None
    if r.panchaka:
        panchaka_resp = PanchakaDetailResponse(
            remainder=r.panchaka.remainder, panchaka_name=r.panchaka.panchaka_name,
            description=r.panchaka.description, has_dosha=r.panchaka.has_dosha,
            score=r.panchaka.score,
        )

    activities_resp = [
        ActivitySuitabilityResponse(
            activity_id=a.activity_id, name=a.name, score=a.score,
            verdict=a.verdict, points=a.points,
        )
        for a in r.activities
    ]

    return MuhurtaResponse(
        sunrise=jd_to_datetime(r.sunrise_jd),
        sunset=jd_to_datetime(r.sunset_jd),
        next_sunrise=jd_to_datetime(r.next_sunrise_jd),
        horas=[_serialise_hora(h) for h in r.horas],
        rahukalam=_serialise_period(r.rahukalam),
        gulikalam=_serialise_period(r.gulikalam),
        yamagandam=_serialise_period(r.yamagandam),
        choghadiya=[_serialise_choghadiya(c) for c in r.choghadiya],
        tithi=tithi_resp,
        vara=vara_resp,
        nakshatra=nakshatra_resp,
        yoga=yoga_resp,
        karana=karana_resp,
        calendar=calendar_resp,
        celestial=celestial_resp,
        abhijit_muhurta=abhijit_resp,
        brahma_muhurta=brahma_resp,
        dur_muhurta=dur_muhurtas_resp,
        amrit_kaal=amrit_resp,
        tarabala=tarabala_resp,
        chandrabala=chandrabala_resp,
        panchaka=panchaka_resp,
        activities=activities_resp,
    )


@router.get(
    "",
    response_model=MuhurtaResponse,
    summary="Comprehensive Panchanga and Muhurta calculations for a date, time, and location",
)
async def get_muhurta(
    local_date: date = Query(..., description="Calendar date (local)."),
    local_time_str: Optional[str] = Query(default=None, alias="local_time", description="Local time HH:MM or HH:MM:SS"),
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    utc_offset_minutes: int = Query(
        ..., description="UTC offset in minutes for the location on this date (e.g. IST = 330)."
    ),
    ayanamsa: str = Query(default="lahiri", description="Ayanamsa system (lahiri, raman, kp)"),
    natal_nakshatra: Optional[int] = Query(default=None, ge=1, le=27, description="Birth Nakshatra number for Tarabala"),
    natal_moon_sign: Optional[int] = Query(default=None, ge=1, le=12, description="Birth Moon Rashi number for Chandrabala"),
    engine: MuhurtaEngine = Depends(_get_muhurta_engine),
) -> MuhurtaResponse:
    parsed_time = time(12, 0)
    if local_time_str:
        try:
            parts = [int(p) for p in local_time_str.split(":")]
            if len(parts) >= 2:
                parsed_time = time(parts[0], parts[1], parts[2] if len(parts) > 2 else 0)
        except Exception:
            parsed_time = time(12, 0)

    target_dt = datetime.combine(local_date, parsed_time).replace(
        tzinfo=timezone(timedelta(minutes=utc_offset_minutes))
    )
    jd = datetime_to_jd(target_dt)

    ayanamsa_slug = ayanamsa.lower().strip()
    if ayanamsa_slug in ["krishnamurti", "kp"]:
        ayanamsa_slug = "kp"
    elif ayanamsa_slug in ["raman"]:
        ayanamsa_slug = "raman"
    else:
        ayanamsa_slug = "lahiri"

    eff_natal_nak = int(natal_nakshatra) if (natal_nakshatra is not None and isinstance(natal_nakshatra, (int, float, str)) and str(natal_nakshatra).isdigit()) else None
    eff_natal_moon = int(natal_moon_sign) if (natal_moon_sign is not None and isinstance(natal_moon_sign, (int, float, str)) and str(natal_moon_sign).isdigit()) else None

    try:
        result = engine.calculate(
            jd=jd,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa_slug,
            natal_nakshatra=eff_natal_nak,
            natal_moon_sign=eff_natal_moon,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    return _serialise_result(result)


from pydantic import BaseModel, Field
from apps.api.services.muhurta_samskara_engine import MuhurtaSamskaraEngine


class SamskaraEvaluateRequest(BaseModel):
    samskara_code: str = Field(..., description="Samskara code, e.g., 'E17_Vivaah', 'E21_GrihPravesh', 'E19_Upnayan'")
    datetime_utc: datetime = Field(..., description="Target UTC datetime for evaluation")
    latitude: float = Field(default=28.6139, description="Observer latitude")
    longitude: float = Field(default=77.2090, description="Observer longitude")
    ayanamsa: str = Field(default="lahiri", description="Ayanamsa system")


@router.get("/samskaras", summary="List All 35 Classical Samskaras & Elections (E01–E35)")
def list_classical_samskaras():
    """Returns the full suite of classical Shodasha Samskaras and Muhurta elections."""
    return {"count": len(MuhurtaSamskaraEngine.list_samskaras()), "samskaras": MuhurtaSamskaraEngine.list_samskaras()}


@router.post("/samskara/evaluate", summary="Evaluate Timestamp for a Classical Samskara")
def evaluate_samskara_muhurta(
    req: SamskaraEvaluateRequest,
    ephem: EphemerisWrapper = Depends(get_ephemeris_wrapper),
):
    """
    Evaluates whether a given timestamp and location is auspicious for a specific Samskara (E01-E35),
    checking Tithi shuddhi, Nakshatra compatibility, Ascendant strength, and classical doshas.
    """
    try:
        res = MuhurtaSamskaraEngine.evaluate(
            samskara_code=req.samskara_code,
            dt=req.datetime_utc,
            lat=req.latitude,
            lon=req.longitude,
            ephem=ephem,
        )
        return {
            "samskara_code": res.samskara_code,
            "samskara_name": res.samskara_name,
            "category": res.category,
            "timestamp": res.timestamp.isoformat(),
            "suitability_score": res.suitability_score,
            "is_auspicious": res.is_auspicious,
            "tithi": {"name": res.tithi_name, "number": res.tithi_number, "status": res.tithi_status},
            "nakshatra": {"name": res.nakshatra_name, "status": res.nakshatra_status},
            "lagna": {"rashi": res.lagna_rashi, "status": res.lagna_status},
            "dosha_flags": res.dosha_flags,
            "positive_factors": res.positive_factors,
            "shastric_recommendation": res.shastric_recommendation,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Samskara evaluation failed: {e}")
