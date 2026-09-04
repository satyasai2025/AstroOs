"""
AstroOS — Prashna (Horary) Router

Endpoints:
- GET  /api/v1/prashna/arudha       — KP Arudha for seed number (1-249 or 1-2193)
- POST /api/v1/prashna/sphutas      — Six Sphutas for query/birth moment + location
- GET  /api/v1/prashna/arabic-parts — Catalogue and calculated Arabic Parts / Sahams
- POST /api/v1/prashna/calculate    — Complete Prashna Analysis (Chart, Cusps, RP, Arabic Parts, Judgement)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.domain.prashna import (
    PrashnaArudhaResult,
    PrashnaSphutaResult,
    SphutaPosition,
    RulingPlanetsSnapshot,
    ArabicPartComputed,
    PrashnaJudgement,
)
from apps.api.schemas.prashna import (
    PrashnaArudhaResponse,
    PrashnaSphutaRequest,
    PrashnaSphutaResponse,
    SphutaPositionResponse,
    RulingPlanetEntryResponse,
    RulingPlanetsSnapshotResponse,
    ArabicPartComputedResponse,
    KeyEvidenceResponse,
    RelevantHouseResponse,
    TimingIndicationResponse,
    RuleTriggeredResponse,
    ContradictionResponse,
    PrashnaJudgementResponse,
    HoraryPlanetPosition,
    HoraryHouseCusp,
    PrashnaFullCalculationRequest,
    PrashnaFullCalculationResponse,
)
from apps.api.services.ephemeris_wrapper import (
    EphemerisWrapper,
    datetime_to_jd,
    longitude_to_nakshatra,
    longitude_to_rashi,
)
from apps.api.services.prashna_engine import PrashnaEngine, _deg_to_dms
from packages.shared.rashi_offset import house_offset

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prashna", tags=["Prashna"])


def _get_prashna_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> PrashnaEngine:
    return PrashnaEngine(wrapper)


def _serialise_arudha(r: PrashnaArudhaResult) -> PrashnaArudhaResponse:
    return PrashnaArudhaResponse(
        seed_number=r.seed_number,
        system=r.system,
        sidereal_longitude=r.sidereal_longitude,
        rashi=r.rashi,
        rashi_degree=r.rashi_degree,
        nakshatra=r.nakshatra,
        sign_lord=r.sign_lord,
        star_lord=r.star_lord,
        sub_lord=r.sub_lord,
        sub_sub_lord=r.sub_sub_lord,
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


def _serialise_rp(rp: RulingPlanetsSnapshot) -> RulingPlanetsSnapshotResponse:
    return RulingPlanetsSnapshotResponse(
        casting_time=rp.casting_time,
        hora_lord=rp.hora_lord,
        day_lord=rp.day_lord,
        entries=[
            RulingPlanetEntryResponse(
                point_name=e.point_name,
                sign_lord=e.sign_lord.capitalize() if e.sign_lord else "",
                star_lord=e.star_lord.capitalize() if e.star_lord else "",
                sub_lord=e.sub_lord.capitalize() if e.sub_lord else "",
                sub_sub_lord=e.sub_sub_lord.capitalize() if e.sub_sub_lord else "",
                as_aspecting=e.as_aspecting,
                is_conjunction=e.is_conjunction,
                planet=e.planet.capitalize() if e.planet else (e.sign_lord.capitalize() if e.sign_lord else ""),
                source=e.source,
                reason=e.reason,
                priority=e.priority,
                relationship_to_judgement=e.relationship_to_judgement,
            )
            for e in rp.entries
        ],
    )


def _serialise_arabic_part(p: ArabicPartComputed) -> ArabicPartComputedResponse:
    return ArabicPartComputedResponse(
        name=p.name,
        category=p.category,
        formula_used=p.formula_used,
        is_day_formula=p.is_day_formula,
        sidereal_longitude=p.sidereal_longitude,
        rashi=p.rashi,
        rashi_degree_str=p.rashi_degree_str,
        sign_lord=p.sign_lord,
        star_lord=p.star_lord,
        sub_lord=p.sub_lord,
        sub_sub_lord=p.sub_sub_lord,
        description=p.description,
    )


def _serialise_judgement(j: PrashnaJudgement) -> PrashnaJudgementResponse:
    return PrashnaJudgementResponse(
        verdict=j.verdict,
        confidence_percentage=j.confidence_percentage,
        strength_label=j.strength_label,
        summary=j.summary,
        key_evidences=[
            KeyEvidenceResponse(
                factor=e.factor,
                indication=e.indication,
                explanation=e.explanation,
                weight=e.weight,
            )
            for e in j.key_evidences
        ],
        relevant_houses=[
            RelevantHouseResponse(
                house=h.house,
                sign=h.sign,
                lord=h.lord,
                strength=h.strength,
                note=h.note,
            )
            for h in j.relevant_houses
        ],
        timing=TimingIndicationResponse(
            likely_window=j.timing.likely_window,
            dasha_mahadasha=j.timing.dasha_mahadasha,
            antardasha=j.timing.antardasha,
            transit_support=j.timing.transit_support,
            moon_cycle=j.timing.moon_cycle,
        ),
        conclusions=list(j.conclusions),
        supporting_rules=[
            RuleTriggeredResponse(
                rule_id=r.rule_id,
                rule_principle=r.rule_principle,
                reference=r.reference,
                triggered=r.triggered,
                weight=r.weight,
                rule_name=r.rule_name,
                result=r.result,
                evidence=r.evidence,
                supporting_factors=list(r.supporting_factors),
                contradicting_factors=list(r.contradicting_factors),
            )
            for r in j.supporting_rules
        ],
        contradictions=[
            ContradictionResponse(
                title=c.title,
                description=c.description,
                advice=c.advice,
                source_factor=c.source_factor,
            )
            for c in j.contradictions
        ],
    )


@router.get(
    "/arudha",
    response_model=PrashnaArudhaResponse,
    summary="Prashna Arudha for a horary seed number (1-249 or 1-2193)",
)
async def get_prashna_arudha(
    seed_number: int = Query(..., description="Horary number chosen by the querent."),
    system: Literal["kp_249", "kp_2193"] = Query("kp_249", description="KP Arudha division system."),
    engine: PrashnaEngine = Depends(_get_prashna_engine),
) -> PrashnaArudhaResponse:
    try:
        result = engine.arudha_from_seed(seed_number, system)
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
        result = engine.sphutas_for_chart(
            body.moment_utc, body.latitude, body.longitude, body.ayanamsa
        )
    except Exception as exc:
        logger.error("Failed to compute sphutas: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sphuta calculation failed: {exc}",
        )

    return PrashnaSphutaResponse(
        sphutas=[_serialise_sphuta(s) for s in result.sphutas],
        ascendant_longitude=result.ascendant_longitude,
        gulika_longitude=result.gulika_longitude,
    )


@router.get(
    "/arabic-parts",
    response_model=list[ArabicPartComputedResponse],
    summary="Get 50+ calculated Arabic Parts / Sahams / Event Combinations",
)
async def get_arabic_parts(
    moment_iso: str | None = Query(None, description="ISO timestamp of query moment (defaults to now)"),
    latitude: float = Query(18.5204, ge=-90.0, le=90.0),
    longitude: float = Query(73.8567, ge=-180.0, le=180.0),
    ayanamsa: str = Query("lahiri"),
    engine: PrashnaEngine = Depends(_get_prashna_engine),
) -> list[ArabicPartComputedResponse]:
    try:
        dt = datetime.fromisoformat(moment_iso) if moment_iso else datetime.now(timezone.utc)
        parts = engine.calculate_arabic_parts(dt, latitude, longitude, ayanamsa)
        return [_serialise_arabic_part(p) for p in parts]
    except Exception as exc:
        logger.error("Failed to compute arabic parts: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Arabic parts calculation failed: {exc}",
        )


@router.post(
    "/calculate",
    response_model=PrashnaFullCalculationResponse,
    summary="Full Prashna (Horary) Analysis with Chart, RP, Arabic Parts & Judgement",
)
async def calculate_prashna(
    body: PrashnaFullCalculationRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
    engine: PrashnaEngine = Depends(_get_prashna_engine),
) -> PrashnaFullCalculationResponse:
    try:
        dt = body.moment_utc
        lat = body.latitude
        lon = body.longitude
        ayanamsa = body.ayanamsa
        jd = datetime_to_jd(dt)

        # 1. Arudha if seed number provided
        arudha_res = None
        arudha_dto = None
        if body.horary_number:
            try:
                arudha_res = engine.arudha_from_seed(body.horary_number, body.horary_system)
                arudha_dto = _serialise_arudha(arudha_res)
            except Exception as exc:
                logger.warning("Could not calculate Arudha for seed %s: %s", body.horary_number, exc)

        # 2. Ascendant & Cusps
        trop_asc, trop_cusps = wrapper.get_ascendant_and_cusps(jd, lat, lon, "P")  # Placidus cusps for KP
        ayan_val = wrapper.get_ayanamsa(jd)
        sid_asc = wrapper.to_sidereal(trop_asc, ayan_val)
        if arudha_res:
            sid_asc = arudha_res.sidereal_longitude

        # 3. Planets
        planet_names = ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu")
        planets_data: list[HoraryPlanetPosition] = []
        asc_rashi_idx = ("aries", "taurus", "gemini", "cancer", "leo", "virgo",
                         "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces").index(longitude_to_rashi(sid_asc)[0])

        for p_name in planet_names:
            p_pos = wrapper.get_planet_position(p_name, jd)
            sid_lon = wrapper.to_sidereal(p_pos.longitude, ayan_val)
            r_name, r_deg = longitude_to_rashi(sid_lon)
            nak = longitude_to_nakshatra(sid_lon)
            lords = engine.get_kp_lords_for_longitude(sid_lon)
            p_rashi_idx = ("aries", "taurus", "gemini", "cancer", "leo", "virgo",
                           "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces").index(r_name)
            p_house = house_offset(asc_rashi_idx, p_rashi_idx)

            planets_data.append(
                HoraryPlanetPosition(
                    planet=p_name.capitalize(),
                    sign=r_name.capitalize(),
                    degree_str=_deg_to_dms(r_deg),
                    degree_float=r_deg,
                    nakshatra=nak.nakshatra,
                    pada=nak.pada,
                    house_number=p_house,
                    sign_lord=lords["sign_lord"].capitalize(),
                    star_lord=lords["star_lord"].capitalize(),
                    sub_lord=lords["sub_lord"].capitalize(),
                    sub_sub_lord=lords["sub_sub_lord"].capitalize(),
                )
            )

        # 4. Cusps (12 houses)
        cusps_data: list[HoraryHouseCusp] = []
        for i in range(12):
            raw_cusp = trop_cusps[i] if i < len(trop_cusps) else (trop_asc + i * 30.0) % 360.0
            sid_cusp_lon = wrapper.to_sidereal(raw_cusp, ayan_val)
            if arudha_res and i == 0:
                sid_cusp_lon = arudha_res.sidereal_longitude
            elif arudha_res:
                sid_cusp_lon = (arudha_res.sidereal_longitude + (sid_cusp_lon - wrapper.to_sidereal(trop_asc, ayan_val))) % 360.0

            r_name, r_deg = longitude_to_rashi(sid_cusp_lon)
            nak = longitude_to_nakshatra(sid_cusp_lon)
            lords = engine.get_kp_lords_for_longitude(sid_cusp_lon)

            # Check which planets occupy this house
            occ_list: list[str] = []
            for p in planets_data:
                # Placidus or sign based house offset
                p_rashi_idx = ("aries", "taurus", "gemini", "cancer", "leo", "virgo",
                               "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces").index(p.sign.lower())
                asc_rashi_idx = ("aries", "taurus", "gemini", "cancer", "leo", "virgo",
                                 "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces").index(longitude_to_rashi(sid_asc)[0])
                if house_offset(asc_rashi_idx, p_rashi_idx) == (i + 1):
                    occ_list.append(p.planet)

            cusps_data.append(
                HoraryHouseCusp(
                    house=i + 1,
                    sign=r_name.capitalize(),
                    degree_str=_deg_to_dms(r_deg),
                    degree_float=r_deg,
                    nakshatra=nak.nakshatra,
                    pada=nak.pada,
                    occupants=occ_list,
                    sign_lord=lords["sign_lord"].capitalize(),
                    star_lord=lords["star_lord"].capitalize(),
                    sub_lord=lords["sub_lord"].capitalize(),
                    sub_sub_lord=lords["sub_sub_lord"].capitalize(),
                )
            )

        # 5. Ruling Planets (CT and RT)
        rp_ct = engine.get_ruling_planets(dt, lat, lon, ayanamsa)
        rp_rt = engine.get_ruling_planets(datetime.now(timezone.utc), lat, lon, ayanamsa)

        # 6. Arabic Parts
        parts = engine.calculate_arabic_parts(dt, lat, lon, ayanamsa)

        # 7. Sphutas
        sphutas_res = engine.sphutas_for_chart(dt, lat, lon, ayanamsa)

        # 8. Judgement
        judgement = engine.evaluate_judgement(body.question, dt, lat, lon, body.horary_number, ayanamsa)

        return PrashnaFullCalculationResponse(
            name=body.name,
            gender=body.gender,
            question=body.question,
            moment_utc=dt,
            place_name=body.place_name,
            latitude=lat,
            longitude=lon,
            timezone_offset=body.timezone_offset,
            ayanamsa=ayanamsa,
            horary_number=body.horary_number,
            horary_system=body.horary_system,
            arudha=arudha_dto,
            planets=planets_data,
            cusps=cusps_data,
            ruling_planets_ct=_serialise_rp(rp_ct),
            ruling_planets_rt=_serialise_rp(rp_rt),
            arabic_parts=[_serialise_arabic_part(p) for p in parts],
            sphutas=[_serialise_sphuta(s) for s in sphutas_res.sphutas],
            judgement=_serialise_judgement(judgement),
        )

    except Exception as exc:
        logger.error("Failed full prashna calculation: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prashna calculation failed: {exc}",
        )
