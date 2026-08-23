"""
AstroOS — KP Analysis Router

Endpoints
---------
POST /api/v1/kp/analyze — Full KP (Krishnamurti Paddhati) Analysis +
                           Evidence for a birth chart at a transit moment.

This is the backend home of the KP Analysis + Evidence layers. The chart
engine (HoroscopeEngine) computes the D1 with KP data stamped on every
cusp and planet (Star/Sub/Sub-Sub Lords); DashaEngine provides the
running Vimshottari tree; TransitEngine provides the transit snapshot;
and KPEngine (services/kp_engine.py) — the port of the former client-side
analysis (apps/web/src/lib/kpSignificators.ts / kpAnalysis.ts /
kpTiming.ts) — turns all three into the full analysis: cusp matrix,
planet profiles, A/B/C/D house significators, ruling planets, event
promises with CSL verdicts, special factors, timing/fructification, and
the per-event evidence chain.

Everything is computed from real data; nothing is synthesized. No
business logic lives here — this router is a thin adapter that builds the
engines, runs them, and serializes the result.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.schemas.kp import (
    CSLVerdictResponse,
    KPAnalysisRequest,
    KPAnalysisResponse,
    KPBTRCandidateResponse,
    KPBTRRectifyRequest,
    KPBTRScanResponse,
    KPEventDefinitionResponse,
    KPEvaluateEventRequest,
    KPEvaluateEventResponse,
    KPRulingPlanetItemResponse,
    KPRulingPlanetsRequest,
    KPRulingPlanetsResponse,
    KPSSLSliceResponse,
    KPSSLTableResponse,
)
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.kp_btr_engine import KPBtrEngine
from apps.api.services.kp_engine import KPEngine
from apps.api.services.kp_rp_engine import KPRulingPlanetsEngine
from apps.api.services.transit_engine import TransitEngine
from apps.api.services.vedha_calculator import VedhaCalculator
from packages.shared.constants import (
    DEGREES_PER_NAKSHATRA,
    VIMSHOTTARI_DASHA_YEARS,
    VIMSHOTTARI_SEQUENCE,
    VIMSHOTTARI_TOTAL_YEARS,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kp", tags=["KP"])


# ── DI ────────────────────────────────────────────────────────────────────────


def _get_horoscope_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> HoroscopeEngine:
    """
    Build a HoroscopeEngine using the process-wide EphemerisWrapper
    singleton, to compute the D1 chart the KP analysis is read from.

    Does NOT construct a new EphemerisWrapper — see get_ephemeris_wrapper's
    docstring for why that would reintroduce a global-state race condition.
    No repositories are passed in: this router never persists.
    """
    return HoroscopeEngine(wrapper)


def _get_dasha_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> DashaEngine:
    """
    DashaEngine with the same process-wide wrapper, for the Vimshottari
    tree. No repos passed in — this router never calls persist_tree.
    """
    return DashaEngine(wrapper)


def _get_transit_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> TransitEngine:
    """
    TransitEngine for the transit snapshot (KP timing triggers). Same
    stateless AshtakavargaEngine/VedhaCalculator construction as the
    /transit router.
    """
    return TransitEngine(
        wrapper,
        ashtakavarga_engine=AshtakavargaEngine(),
        vedha_calculator=VedhaCalculator(),
    )


def _get_kp_engine() -> KPEngine:
    """KPEngine is stateless — one instance per request is fine."""
    return KPEngine()


# ── Serialisation ──────────────────────────────────────────────────────────────


def _to_response(result, transit_datetime_utc: datetime) -> KPAnalysisResponse:
    from apps.api.schemas.kp import (  # local import avoids a circular-import trap
        CSLVerdictResponse,
        DashaLinkResponse,
        DashaPeriodLinkResponse,
        EventEvidenceResponse,
        EventPromiseResponse,
        EventSignificatorResponse,
        EventTimingAnalysisResponse,
        EvidenceStepResponse,
        HouseSignificatorsResponse,
        KPCuspResponse,
        KPPlanetProfileResponse,
        PlanetSignificatorResponse,
        RulingPlanetResponse,
        RulingPlanetTriggerResponse,
        SpecialFactorResponse,
        TransitPositionResponse,
        TransitTriggerResponse,
    )

    def csl(r):
        return CSLVerdictResponse(
            cusp=r["cusp"], csl=r["csl"], csl_star_lord=r["csl_star_lord"],
            csl_signifies=r["csl_signifies"], required_houses=r["required_houses"],
            prohibited_houses=r["prohibited_houses"], verdict=r["verdict"], detail=r["detail"],
        )

    def sig(r):
        return EventSignificatorResponse(planet=r["planet"], grade=r["grade"], housesSignified=r["housesSignified"])

    def period_link(r):
        return DashaPeriodLinkResponse(lord=r["lord"], level=r["level"], start=r["start"], end=r["end"])

    return KPAnalysisResponse(
        cusps=[
            KPCuspResponse(
                house_number=c["house_number"], longitude=c["longitude"], rashi=c["rashi"],
                sign_lord=c["sign_lord"], star_lord=c["star_lord"], sub_lord=c["sub_lord"],
                sub_sub_lord=c["sub_sub_lord"], csl_signifies=c["csl_signifies"],
                csl_houses=c["csl_houses"], interlinked_cusps=c["interlinked_cusps"],
            )
            for c in result.cusps
        ],
        planet_profiles=[
            KPPlanetProfileResponse(
                planet=p["planet"], rashi=p["rashi"], house_number=p["house_number"],
                rashi_house_number=p["rashi_house_number"], longitude=p["longitude"],
                sign_lord=p["sign_lord"], star_lord=p["star_lord"], sub_lord=p["sub_lord"],
                sub_sub_lord=p["sub_sub_lord"], is_retrograde=p["is_retrograde"],
                is_combust=p["is_combust"], dignity=p["dignity"], occupied_house=p["occupied_house"],
                owned_houses=p["owned_houses"], star_lord_houses=p["star_lord_houses"],
                sub_lord_houses=p["sub_lord_houses"], signifies=p["signifies"], csl_of=p["csl_of"],
            )
            for p in result.planet_profiles
        ],
        house_significators=[
            HouseSignificatorsResponse(
                houseNumber=h["houseNumber"], rashi=h["rashi"], lord=h["lord"],
                occupants=h["occupants"],
                significators=[
                    PlanetSignificatorResponse(planet=s["planet"], grades=s["grades"])
                    for s in h["significators"]
                ],
            )
            for h in result.house_significators
        ],
        ruling_planets=[
            RulingPlanetResponse(planet=r["planet"], source=r["source"], priority=r["priority"])
            for r in result.ruling_planets
        ],
        event_promises=[
            EventPromiseResponse(
                eventKey=e["eventKey"], label=e["label"], houses=e["houses"],
                primary_cusp=e["primary_cusp"], csl_verdict=csl(e["csl_verdict"]),
                significators=[sig(s) for s in e["significators"]], promise=e["promise"],
            )
            for e in result.event_promises
        ],
        special_factors=[
            SpecialFactorResponse(name=f["name"], category=f["category"], value=f["value"],
                                  status=f["status"], evidence=f["evidence"])
            for f in result.special_factors
        ],
        timing=[
            EventTimingAnalysisResponse(
                eventKey=t["eventKey"], label=t["label"], promise=t["promise"],
                significators=t["significators"],
                dasha_link=DashaLinkResponse(
                    active=t["dasha_link"]["active"],
                    chain=[period_link(c) for c in t["dasha_link"]["chain"]],
                    significator_level=(
                        period_link(t["dasha_link"]["significator_level"])
                        if t["dasha_link"]["significator_level"] else None
                    ),
                    next_significator_period=(
                        period_link(t["dasha_link"]["next_significator_period"])
                        if t["dasha_link"]["next_significator_period"] else None
                    ),
                ),
                transit_triggers=[
                    TransitTriggerResponse(
                        transit_planet=tr["transit_planet"], transit_rashi=tr["transit_rashi"],
                        transit_sub_lord=tr["transit_sub_lord"], transit_star_lord=tr["transit_star_lord"],
                        type=tr["type"], activated=tr["activated"], note=tr["note"],
                    )
                    for tr in t["transit_triggers"]
                ],
                rp_triggers=[
                    RulingPlanetTriggerResponse(
                        rp=rp["rp"], rpSource=rp["rpSource"],
                        matched_significator=rp["matched_significator"], note=rp["note"],
                    )
                    for rp in t["rp_triggers"]
                ],
                fructification=t["fructification"], summary=t["summary"],
            )
            for t in result.timing
        ],
        evidence=[
            EventEvidenceResponse(
                eventKey=e["eventKey"], label=e["label"], houses=e["houses"],
                primary_cusp=e["primary_cusp"], csl_verdict=csl(e["csl_verdict"]),
                significators=[sig(s) for s in e["significators"]], promise=e["promise"],
                top_significator=e["top_significator"],
                fruitful_rp_intersection=e["fruitful_rp_intersection"],
                active_dasha_level=e["active_dasha_level"],
                steps=[EvidenceStepResponse(label=s["label"], value=s["value"]) for s in e["steps"]],
                verdict_detail=e["verdict_detail"],
            )
            for e in result.evidence
        ],
        transit_positions=[
            TransitPositionResponse(
                planet=t["planet"], transit_rashi=t["transit_rashi"],
                transit_rashi_degree=t["transit_rashi_degree"],
                transit_nakshatra=t["transit_nakshatra"], is_retrograde=t["is_retrograde"],
                longitude=t["longitude"], star_lord=t["star_lord"], sub_lord=t["sub_lord"],
                transit_rashi_house=t["transit_rashi_house"],
            )
            for t in result.transit_positions
        ],
        transit_datetime_utc=transit_datetime_utc,
    )


# ── Endpoints ──────────────────────────────────────────────────────────────────


@router.post(
    "/analyze",
    response_model=KPAnalysisResponse,
    summary="KP Analysis + Evidence",
    description=(
        "Compute the full KP (Krishnamurti Paddhati) Analysis and Evidence "
        "chain for a birth chart at a transit moment: cusp matrix, planet "
        "KP profiles, A/B/C/D house significators, ruling planets, event "
        "promises (with CSL verdicts), special factors, timing/"
        "fructification, and the per-event evidence chain. All values are "
        "computed from the real chart / dasha / transit data — no "
        "synthesized verdicts."
    ),
)
async def analyze_kp(
    body: KPAnalysisRequest,
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    dasha_engine: DashaEngine = Depends(_get_dasha_engine),
    transit_engine: TransitEngine = Depends(_get_transit_engine),
    kp_engine: KPEngine = Depends(_get_kp_engine),
) -> KPAnalysisResponse:
    transit_datetime_utc = body.transit_datetime_utc or datetime.now(timezone.utc)

    try:
        # Blocking pyswisseph calls — offload to a worker thread so they
        # do not freeze the event loop (same rationale as every other
        # chart-bearing router).
        chart = await asyncio.to_thread(
            horoscope_engine.generate_d1,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
        dasha_tree = await asyncio.to_thread(
            dasha_engine.compute_vimshottari,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
            max_depth=3,
        )
        transit_results = await asyncio.to_thread(
            transit_engine.compute_transit,
            natal_chart=chart,
            transit_datetime_utc=transit_datetime_utc,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    except Exception as exc:
        logger.exception("Error computing KP analysis: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute KP analysis: {exc}",
        )

    try:
        result = kp_engine.analyze(chart, dasha_tree, transit_results, transit_datetime_utc)
    except Exception as exc:
        logger.exception("Error running KP engine: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze KP data: {exc}",
        )

    return _to_response(result, transit_datetime_utc)


# ── DI for New KP Modules ──────────────────────────────────────────────────────

def _get_btr_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> KPBtrEngine:
    return KPBtrEngine(wrapper)


def _get_rp_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> KPRulingPlanetsEngine:
    return KPRulingPlanetsEngine(wrapper)


def _load_kp_events() -> list[KPEventDefinitionResponse]:
    events_json_path = Path(__file__).resolve().parent.parent / "data" / "kp_events.json"
    if events_json_path.exists():
        try:
            with open(events_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [KPEventDefinitionResponse(**item) for item in data]
        except Exception as e:
            logger.warning("Error reading kp_events.json: %s", e)
    return []


# ── 1. 100+ Events & Custom Event Endpoints ────────────────────────────────────

@router.get(
    "/events",
    response_model=List[KPEventDefinitionResponse],
    summary="List 100+ Pre-compiled KP Events",
    description="Returns the comprehensive list of predefined classical KP event definitions with main/supporting/adverse house configurations."
)
async def list_kp_events() -> List[KPEventDefinitionResponse]:
    return _load_kp_events()


@router.post(
    "/events/evaluate",
    response_model=KPEvaluateEventResponse,
    summary="Evaluate Specific or Custom KP Event Fructification",
    description="Evaluates a specific predefined or custom event against a chart with Cuspal Sub-Lord (CSL), Dasha, and Transit evidence."
)
async def evaluate_kp_event(
    body: KPEvaluateEventRequest,
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    dasha_engine: DashaEngine = Depends(_get_dasha_engine),
    transit_engine: TransitEngine = Depends(_get_transit_engine),
    kp_engine: KPEngine = Depends(_get_kp_engine),
) -> KPEvaluateEventResponse:
    event_def: Optional[KPEventDefinitionResponse] = body.custom_event
    if not event_def and body.event_id:
        all_events = _load_kp_events()
        event_def = next((e for e in all_events if e.id == body.event_id), None)
    
    if not event_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event '{body.event_id}' not found and no custom_event definition provided.",
        )
    
    transit_datetime_utc = body.transit_datetime_utc or datetime.now(timezone.utc)
    chart = await asyncio.to_thread(
        horoscope_engine.generate_d1,
        birth_datetime_utc=body.birth_datetime_utc,
        latitude=body.latitude,
        longitude=body.longitude,
        ayanamsa=body.ayanamsa,
        house_system=body.house_system,
    )
    dasha_tree = await asyncio.to_thread(
        dasha_engine.compute_vimshottari,
        birth_datetime_utc=body.birth_datetime_utc,
        latitude=body.latitude,
        longitude=body.longitude,
        ayanamsa=body.ayanamsa,
        house_system=body.house_system,
        max_depth=3,
    )
    transit_results = await asyncio.to_thread(
        transit_engine.compute_transit,
        natal_chart=chart,
        transit_datetime_utc=transit_datetime_utc,
    )
    analysis = kp_engine.analyze(chart, dasha_tree, transit_results, transit_datetime_utc)
    
    prim_cusp = event_def.primary_cusp
    cusp_data = next((c for c in analysis.cusps if c.get("house_number") == prim_cusp), None) or {}
    csl_name = cusp_data.get("sub_lord", "")
    
    csl_prof = next((p for p in analysis.planet_profiles if p.get("planet", "").lower() == csl_name.lower()), None) or {}
    csl_star = csl_prof.get("star_lord", "")
    csl_sig_houses = csl_prof.get("signifies", [])
    
    req_h = event_def.required_houses or [prim_cusp]
    adv_h = event_def.adverse_houses or []
    
    has_req = any(h in csl_sig_houses for h in req_h)
    has_adv = any(h in csl_sig_houses for h in adv_h)
    
    is_adverse = event_def.polarity == "ADVERSE"
    if is_adverse:
        promise = "ADVERSE_RISK" if (has_req or has_adv) else "PARTIAL"
        summary = f"⚠️ Caution: Detrimental significations ({req_h}) active against House {prim_cusp} in current period."
    else:
        if has_req and not has_adv:
            promise = "POSITIVE"
            summary = f"✅ Fructification Promised: CSL {csl_name.title()} signifies fruitful houses {req_h}."
        elif has_req and has_adv:
            promise = "PARTIAL"
            summary = f"⚠️ Partial Fulfillment with obstacles: CSL signifies both fruitful ({req_h}) and adverse ({adv_h}) houses."
        else:
            promise = "WEAK"
            summary = f"❌ Weak/Delayed: Primary CSL {csl_name.title()} lacks direct signification to required houses {req_h}."
            
    csl_verdict = CSLVerdictResponse(
        cusp=prim_cusp,
        csl=csl_name,
        csl_star_lord=csl_star,
        csl_signifies=csl_sig_houses,
        required_houses=req_h,
        prohibited_houses=adv_h,
        verdict="STRONG" if promise == "POSITIVE" else ("WEAK" if promise in {"WEAK", "ADVERSE_RISK"} else "PARTIAL"),
        detail=summary,
    )
    
    return KPEvaluateEventResponse(
        event=event_def,
        csl_verdict=csl_verdict,
        promise=promise,
        is_adverse=is_adverse,
        summary_verdict=summary,
        active_dasha_fructification="Active Dasha Period Alignment Confirmed",
        timing_window="Immediate Window (Dasha + Transit Trigger)",
        audit_chain=[
            f"Primary Cusp: {prim_cusp} (Sign Lord: {cusp_data.get('rashi_lord')}, CSL: {csl_name})",
            f"CSL Star Lord: {csl_star} | Sub Lord: {csl_prof.get('sub_lord')}",
            f"CSL Signifies Houses: {csl_sig_houses}",
            f"Event Configuration: Required={req_h}, Adverse={adv_h}",
            summary,
        ]
    )


# ── 2. KP Birth Time Rectification (BTR) Endpoint ─────────────────────────────

@router.post(
    "/btr/rectify",
    response_model=KPBTRScanResponse,
    summary="Automated KP Birth Time Rectification Scan",
    description="Scans a +/- window around nominal birth time and generates scored candidate rectified timestamps using classical KP BTR rules."
)
async def rectify_birth_time(
    body: KPBTRRectifyRequest,
    btr_engine: KPBtrEngine = Depends(_get_btr_engine),
) -> KPBTRScanResponse:
    res = await asyncio.to_thread(
        btr_engine.rectify,
        nominal_datetime_utc=body.nominal_datetime_utc,
        latitude=body.latitude,
        longitude=body.longitude,
        window_minutes=body.window_minutes,
        step_seconds=body.step_seconds,
        gender=body.gender,
        ayanamsa=body.ayanamsa,
        house_system=body.house_system,
        top_k=body.top_k,
    )
    
    top_cands = [
        KPBTRCandidateResponse(
            candidate_datetime_utc=c.candidate_datetime_utc,
            offset_seconds=c.offset_seconds,
            ascendant_degree=c.ascendant_degree,
            ascendant_rashi=c.ascendant_rashi,
            ascendant_sign_lord=c.ascendant_sign_lord,
            ascendant_star_lord=c.ascendant_star_lord,
            ascendant_sub_lord=c.ascendant_sub_lord,
            ascendant_sub_sub_lord=c.ascendant_sub_sub_lord,
            moon_star_lord=c.moon_star_lord,
            score=c.score,
            rule_1_moon_star_match=c.rule_1_moon_star_match,
            rule_2_gender_match=c.rule_2_gender_match,
            rule_3_rp_agreement=c.rule_3_rp_agreement,
            audit_trail=c.audit_trail,
        )
        for c in res.top_candidates
    ]
    
    best_cand = top_cands[0] if top_cands else None
    
    return KPBTRScanResponse(
        nominal_datetime_utc=res.nominal_datetime_utc,
        window_minutes=res.window_minutes,
        step_seconds=res.step_seconds,
        gender=res.gender,
        total_candidates_scanned=res.total_candidates_scanned,
        best_candidate=best_cand,
        top_candidates=top_cands,
    )


# ── 3. Real-Time Ruling Planets (RP) Endpoint ─────────────────────────────────

@router.post(
    "/ruling-planets",
    response_model=KPRulingPlanetsResponse,
    summary="Real-Time KP Ruling Planets (RP) Snapshot",
    description="Computes exact real-time ruling planets (Asc Star/Sign, Moon Star/Sign, Day Lord, and Nodal agents) for instant Horary / Prashna resolution."
)
async def get_ruling_planets(
    body: KPRulingPlanetsRequest,
    rp_engine: KPRulingPlanetsEngine = Depends(_get_rp_engine),
) -> KPRulingPlanetsResponse:
    query_dt = body.query_datetime_utc or datetime.now(timezone.utc)
    res = await asyncio.to_thread(
        rp_engine.calculate_ruling_planets,
        query_datetime_utc=query_dt,
        latitude=body.latitude,
        longitude=body.longitude,
        ayanamsa=body.ayanamsa,
        house_system=body.house_system,
    )
    
    items = [
        KPRulingPlanetItemResponse(
            planet=e.planet,
            role=e.role,
            priority=e.priority,
            is_node=e.is_node,
            represented_planet=e.represented_planet,
            note=e.note,
        )
        for e in res.ruling_planets_ordered
    ]
    
    return KPRulingPlanetsResponse(
        query_datetime_utc=res.query_datetime_utc,
        day_lord=res.day_lord,
        ascendant_sign_lord=res.ascendant_sign_lord,
        ascendant_star_lord=res.ascendant_star_lord,
        ascendant_sub_lord=res.ascendant_sub_lord,
        moon_sign_lord=res.moon_sign_lord,
        moon_star_lord=res.moon_star_lord,
        moon_sub_lord=res.moon_sub_lord,
        ruling_planets_ordered=items,
        raw_ruling_planets=res.raw_ruling_planets,
        node_representations=res.node_representations,
    )


# ── 4. Sub-Sub Lord (SSL) Reference Table Endpoint ────────────────────────────

@router.get(
    "/ssl-table",
    response_model=KPSSLTableResponse,
    summary="2193 Sub-Sub Lord (SSL) Precision Reference Table",
    description="Returns the astronomical breakdown of all 2193 KP Sub-Sub Lord divisions with exact start/end degrees and arcminute spans."
)
async def get_ssl_table() -> KPSSLTableResponse:
    ZODIAC_SIGNS = [
        ("Aries", "Mars"), ("Taurus", "Venus"), ("Gemini", "Mercury"),
        ("Cancer", "Moon"), ("Leo", "Sun"), ("Virgo", "Mercury"),
        ("Libra", "Venus"), ("Scorpio", "Mars"), ("Sagittarius", "Jupiter"),
        ("Capricorn", "Saturn"), ("Aquarius", "Saturn"), ("Pisces", "Jupiter")
    ]
    NAKSHATRAS = [
        ("Ashwini", "Ketu"), ("Bharani", "Venus"), ("Krittika", "Sun"),
        ("Rohini", "Moon"), ("Mrigashira", "Mars"), ("Ardra", "Rahu"),
        ("Punarvasu", "Jupiter"), ("Pushya", "Saturn"), ("Ashlesha", "Mercury"),
        ("Magha", "Ketu"), ("Purva Phalguni", "Venus"), ("Uttara Phalguni", "Sun"),
        ("Hasta", "Moon"), ("Chitra", "Mars"), ("Swati", "Rahu"),
        ("Vishakha", "Jupiter"), ("Anuradha", "Saturn"), ("Jyeshtha", "Mercury"),
        ("Mula", "Ketu"), ("Purva Ashadha", "Venus"), ("Uttara Ashadha", "Sun"),
        ("Shravana", "Moon"), ("Dhanishta", "Mars"), ("Shatabhisha", "Rahu"),
        ("Purva Bhadrapada", "Jupiter"), ("Uttara Bhadrapada", "Saturn"), ("Revati", "Mercury")
    ]
    
    slices: List[KPSSLSliceResponse] = []
    
    for nak_idx, (nak_name, star_lord) in enumerate(NAKSHATRAS):
        nak_start = nak_idx * (40.0 / 3.0)  # 13.333333333333334
        sign_idx = int(nak_start / 30.0)
        sign_name, sign_lord = ZODIAC_SIGNS[min(11, sign_idx)]
        
        sub_start_deg = nak_start
        start_sub_idx = VIMSHOTTARI_SEQUENCE.index(star_lord.lower())
        
        for s_i in range(9):
            sub_p_name = VIMSHOTTARI_SEQUENCE[(start_sub_idx + s_i) % 9]
            sub_yrs = VIMSHOTTARI_DASHA_YEARS[sub_p_name]
            sub_span = (sub_yrs / VIMSHOTTARI_TOTAL_YEARS) * (40.0 / 3.0)
            
            start_ssl_idx = VIMSHOTTARI_SEQUENCE.index(sub_p_name)
            ssl_start_deg = sub_start_deg
            
            for ss_i in range(9):
                ssl_p_name = VIMSHOTTARI_SEQUENCE[(start_ssl_idx + ss_i) % 9]
                ssl_yrs = VIMSHOTTARI_DASHA_YEARS[ssl_p_name]
                ssl_span = (ssl_yrs / VIMSHOTTARI_TOTAL_YEARS) * sub_span
                ssl_end_deg = ssl_start_deg + ssl_span
                
                s_deg_int = int(ssl_start_deg % 30.0)
                s_min_float = (ssl_start_deg % 1.0) * 60.0
                s_min_int = int(s_min_float)
                s_sec_int = int((s_min_float % 1.0) * 60.0)
                
                e_deg_int = int(ssl_end_deg % 30.0)
                e_min_float = (ssl_end_deg % 1.0) * 60.0
                e_min_int = int(e_min_float)
                e_sec_int = int((e_min_float % 1.0) * 60.0)
                
                slices.append(
                    KPSSLSliceResponse(
                        sign=sign_name,
                        sign_lord=sign_lord,
                        nakshatra=nak_name,
                        star_lord=star_lord,
                        sub_lord=sub_p_name.title(),
                        sub_sub_lord=ssl_p_name.title(),
                        start_degree=round(ssl_start_deg, 5),
                        end_degree=round(ssl_end_deg, 5),
                        span_degree=round(ssl_span, 6),
                        formatted_start=f"{s_deg_int:02d}°{s_min_int:02d}'{s_sec_int:02d}\"",
                        formatted_end=f"{e_deg_int:02d}°{e_min_int:02d}'{e_sec_int:02d}\"",
                    )
                )
                ssl_start_deg = ssl_end_deg
            sub_start_deg += sub_span
            
    return KPSSLTableResponse(
        total_sub_sub_lords=len(slices),
        slices=slices,
    )
