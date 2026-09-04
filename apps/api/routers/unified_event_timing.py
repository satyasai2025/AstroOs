"""
AstroOS — Unified Multi-System Event Timing API Router

Endpoints:
  POST /api/v1/event-timing/analyze — Full multi-system timing window scan + time-series + snapshot
  POST /api/v1/event-timing/moment  — Instant single moment snapshot for time-travel date slider
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.schemas.unified_event_timing import (
    DashaEvidenceSchema,
    DashaPeriodItemSchema,
    GocharaEvidenceSchema,
    GocharaTransitItemSchema,
    KPEvidenceSchema,
    KPTransitTriggerItemSchema,
    SBCVedhaEvidenceSchema,
    SBCVedhaHitItemSchema,
    TimelineSamplePointSchema,
    UnifiedEventTimingAnalyzeRequest,
    UnifiedEventTimingAnalyzeResponse,
    UnifiedEventTimingWindowSchema,
    UnifiedMomentEvaluationRequest,
    UnifiedMomentEvaluationResponse,
    UnifiedTimingSnapshotSchema,
)
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.unified_event_timing_engine import UnifiedEventTimingEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/event-timing", tags=["Unified Event Timing"])


def _get_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> UnifiedEventTimingEngine:
    return UnifiedEventTimingEngine(wrapper)


def _serialize_snapshot(snap) -> UnifiedTimingSnapshotSchema:
    return UnifiedTimingSnapshotSchema(
        evaluated_datetime_utc=snap.evaluated_datetime_utc.isoformat() if isinstance(snap.evaluated_datetime_utc, datetime) else str(snap.evaluated_datetime_utc),
        event_type=snap.event_type,
        dasha=DashaEvidenceSchema(
            active_chain=[
                DashaPeriodItemSchema(
                    level=p["level"],
                    lord=p["lord"],
                    start_date=p["start_date"],
                    end_date=p["end_date"],
                )
                for p in snap.dasha.active_chain
            ],
            significator_lords=snap.dasha.significator_lords,
            is_dasha_active=snap.dasha.is_dasha_active,
            active_level=snap.dasha.active_level,
            active_lord=snap.dasha.active_lord,
            score=snap.dasha.score,
            detail=snap.dasha.detail,
        ),
        gochara=GocharaEvidenceSchema(
            key_transits=[
                GocharaTransitItemSchema(
                    planet=t["planet"],
                    rashi=t["rashi"],
                    house_from_lagna=t["house_from_lagna"],
                    house_from_moon=t["house_from_moon"],
                    is_retrograde=t["is_retrograde"],
                    is_favorable=t["is_favorable"],
                    aspects=t.get("aspects", []),
                )
                for t in snap.gochara.key_transits
            ],
            gochara_vedha_clear=snap.gochara.gochara_vedha_clear,
            ashtakavarga_support=snap.gochara.ashtakavarga_support,
            sade_sati_status=snap.gochara.sade_sati_status,
            score=snap.gochara.score,
            detail=snap.gochara.detail,
        ),
        sbc=SBCVedhaEvidenceSchema(
            janma_hits=[
                SBCVedhaHitItemSchema(
                    transiting_planet=h["transiting_planet"],
                    ray_direction=h["ray_direction"],
                    from_nakshatra=h["from_nakshatra"],
                    target_point=h["target_point"],
                    target_name=h["target_name"],
                    nature=h["nature"],
                    impact=h["impact"],
                )
                for h in snap.sbc.janma_hits
            ],
            relevant_sangya_hits=[
                SBCVedhaHitItemSchema(
                    transiting_planet=h["transiting_planet"],
                    ray_direction=h["ray_direction"],
                    from_nakshatra=h["from_nakshatra"],
                    target_point=h["target_point"],
                    target_name=h["target_name"],
                    nature=h["nature"],
                    impact=h["impact"],
                )
                for h in snap.sbc.relevant_sangya_hits
            ],
            benefic_count=snap.sbc.benefic_count,
            malefic_count=snap.sbc.malefic_count,
            net_protection=snap.sbc.net_protection,
            score=snap.sbc.score,
            detail=snap.sbc.detail,
        ),
        kp=KPEvidenceSchema(
            primary_cusp=snap.kp.primary_cusp,
            csl=snap.kp.csl,
            csl_star_lord=snap.kp.csl_star_lord,
            csl_signifies=snap.kp.csl_signifies,
            required_houses=snap.kp.required_houses,
            active_transit_triggers=[
                KPTransitTriggerItemSchema(
                    transit_planet=tt["transit_planet"],
                    transit_sign=tt["transit_sign"],
                    transit_nakshatra_lord=tt["transit_nakshatra_lord"],
                    transit_sub_lord=tt["transit_sub_lord"],
                    trigger_type=tt["trigger_type"],
                    significator_matched=tt["significator_matched"],
                    detail=tt["detail"],
                )
                for tt in snap.kp.active_transit_triggers
            ],
            rp_triggers=[
                f"{rp.get('rp', '')} ({rp.get('rpSource', '')}): {rp.get('detail', '')}"
                if isinstance(rp, dict)
                else str(rp)
                for rp in snap.kp.rp_triggers
            ],
            dusthana_veto=snap.kp.dusthana_veto,
            fructification=snap.kp.fructification,
            score=snap.kp.score,
            detail=snap.kp.detail,
        ),
        confluence_score=snap.confluence_score,
        confidence_tier=snap.confidence_tier.value,
        system_weights=snap.system_weights,
        primary_positive_triggers=snap.primary_positive_triggers,
        primary_inhibiting_factors=snap.primary_inhibiting_factors,
        summary_narrative=snap.summary_narrative,
    )


@router.post(
    "/analyze",
    response_model=UnifiedEventTimingAnalyzeResponse,
    summary="Multi-system candidate timing window scan and continuous timeline",
)
async def analyze_event_timing(
    body: UnifiedEventTimingAnalyzeRequest,
    engine: UnifiedEventTimingEngine = Depends(_get_engine),
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> UnifiedEventTimingAnalyzeResponse:
    try:
        birth_dt = datetime.fromisoformat(body.birth_datetime_utc.replace("Z", "+00:00"))
        if birth_dt.tzinfo is None:
            birth_dt = birth_dt.replace(tzinfo=timezone.utc)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid birth_datetime_utc: {e}",
        )

    horoscope_eng = HoroscopeEngine(wrapper)
    chart = horoscope_eng.generate_d1(
        birth_datetime_utc=birth_dt,
        latitude=body.latitude,
        longitude=body.longitude,
        ayanamsa=body.ayanamsa or "lahiri",
        house_system=body.house_system or "P",
    )

    dasha_eng = DashaEngine(wrapper)
    dasha_tree = dasha_eng.compute_vimshottari(
        birth_datetime_utc=birth_dt,
        latitude=body.latitude,
        longitude=body.longitude,
        ayanamsa=body.ayanamsa or "lahiri",
        house_system=body.house_system or "P",
        max_depth=3,
    )

    today = datetime.now(timezone.utc).date()
    start_d = date.fromisoformat(body.start_date) if body.start_date else today
    end_d = date.fromisoformat(body.end_date) if body.end_date else date(today.year + 3, today.month, today.day)

    eval_dt = (
        datetime.fromisoformat(body.evaluation_datetime_utc.replace("Z", "+00:00"))
        if body.evaluation_datetime_utc
        else datetime.now(timezone.utc)
    )

    scan_result = engine.scan_event_windows(
        chart=chart,
        dasha_tree=dasha_tree,
        event_type=body.event_type,
        start_date=start_d,
        end_date=end_d,
        step_days=body.step_days or 15,
        evaluation_datetime_utc=eval_dt,
        chart_id=body.chart_id,
    )

    return UnifiedEventTimingAnalyzeResponse(
        chart_id=scan_result.chart_id,
        event_type=scan_result.event_type,
        start_date=scan_result.start_date.isoformat(),
        end_date=scan_result.end_date.isoformat(),
        evaluated_moment_snapshot=_serialize_snapshot(scan_result.evaluated_moment_snapshot),
        candidate_windows=[
            UnifiedEventTimingWindowSchema(
                window_id=w.window_id,
                event_type=w.event_type,
                start_date=w.start_date.isoformat(),
                end_date=w.end_date.isoformat(),
                peak_date=w.peak_date.isoformat(),
                peak_score=w.peak_score,
                confluence_status=w.confluence_status.value,
                system_scores=w.system_scores,
                primary_drivers=w.primary_drivers,
                inhibiting_factors=w.inhibiting_factors,
                narrative=w.narrative,
            )
            for w in scan_result.candidate_windows
        ],
        time_series=[
            TimelineSamplePointSchema(
                date=pt.date,
                confluence_score=pt.confluence_score,
                dasha_score=pt.dasha_score,
                gochara_score=pt.gochara_score,
                sbc_score=pt.sbc_score,
                kp_score=pt.kp_score,
                peak_flag=pt.peak_flag,
            )
            for pt in scan_result.time_series
        ],
        confluence_summary=scan_result.confluence_summary,
    )


@router.post(
    "/moment",
    response_model=UnifiedMomentEvaluationResponse,
    summary="Instant multi-system snapshot for time-travel slider",
)
async def evaluate_moment_snapshot(
    body: UnifiedMomentEvaluationRequest,
    engine: UnifiedEventTimingEngine = Depends(_get_engine),
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> UnifiedMomentEvaluationResponse:
    try:
        birth_dt = datetime.fromisoformat(body.birth_datetime_utc.replace("Z", "+00:00"))
        if birth_dt.tzinfo is None:
            birth_dt = birth_dt.replace(tzinfo=timezone.utc)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid birth_datetime_utc: {e}",
        )

    try:
        target_dt = datetime.fromisoformat(body.target_datetime_utc.replace("Z", "+00:00"))
        if target_dt.tzinfo is None:
            target_dt = target_dt.replace(tzinfo=timezone.utc)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid target_datetime_utc: {e}",
        )

    horoscope_eng = HoroscopeEngine(wrapper)
    chart = horoscope_eng.generate_d1(
        birth_datetime_utc=birth_dt,
        latitude=body.latitude,
        longitude=body.longitude,
        ayanamsa=body.ayanamsa or "lahiri",
        house_system=body.house_system or "P",
    )

    dasha_eng = DashaEngine(wrapper)
    dasha_tree = dasha_eng.compute_vimshottari(
        birth_datetime_utc=birth_dt,
        latitude=body.latitude,
        longitude=body.longitude,
        ayanamsa=body.ayanamsa or "lahiri",
        house_system=body.house_system or "P",
        max_depth=3,
    )

    snap = engine.evaluate_moment(
        chart=chart,
        dasha_tree=dasha_tree,
        event_type=body.event_type,
        target_datetime_utc=target_dt,
    )

    return UnifiedMomentEvaluationResponse(
        chart_id=body.chart_id,
        event_type=body.event_type,
        snapshot=_serialize_snapshot(snap),
    )
