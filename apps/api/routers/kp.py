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
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.schemas.kp import KPAnalysisRequest, KPAnalysisResponse
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.kp_engine import KPEngine
from apps.api.services.transit_engine import TransitEngine
from apps.api.services.vedha_calculator import VedhaCalculator

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
