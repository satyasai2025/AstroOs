"""
AstroOS — Sarvatobhadra Chakra (SBC) Router

Endpoints
---------
POST /api/v1/sbc/report — Full 9x9 grid snapshot (all 9 grahas' current
                           SBC nakshatra/cell) at a moment, plus
                           (optionally) the Vedha result onto a
                           specified Janma element.
POST /api/v1/sbc/scan   — Scan a date range for every day a Janma
                           element receives a benefic Vedha hit (see
                           sbc_scan_engine.py's granularity caveat).
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.schemas.sbc import (
    SBCEventMatchResponse,
    SBCGridPlanetResponse,
    SBCScanWindowResponse,
    SBCStancePolicyResponse,
    SBCNatalAttributesResponse,
    SBCProtectionItemResponse,
    SBCRawVedhaHitResponse,
    SBCReportRequest,
    SBCReportResponse,
    SBCRiskItemResponse,
    SBCScanHitResponse,
    SBCScanRequest,
    SBCScanResponse,
    SBCSensitivePointResponse,
    SBCSynthesisResponse,
    SBCVedhaEntryResponse,
    SBCVedhaHitResponse,
    SBCVedhaResultResponse,
)
from apps.api.schemas.ai import AISBCAnalysisRequest, AISBCAnalysisResponse
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.sbc_ai_analyzer import SBCAIAnalyzer
from apps.api.services.sbc_report_service import SBCReport, SBCReportService
from apps.api.services.sbc_scan_engine import SBCScanEngine, group_into_windows
from packages.shared.disclosed_events import (
    DisclosedEvent,
    EventMatch,
    EventValence,
    LifeDomain,
)
from packages.shared.temporal_stance import StancePolicy, SubjectStatus


def _serialise_policy(policy: StancePolicy | None) -> SBCStancePolicyResponse | None:
    if policy is None:
        return None
    return SBCStancePolicyResponse(
        direction=policy.direction.value,
        voice=policy.voice.value,
        may_name_specific_event=policy.may_name_specific_event,
        requires_invitation_to_confirm=policy.requires_invitation_to_confirm,
        requires_confidence_qualifier=policy.requires_confidence_qualifier,
        longevity_formula_allowed=policy.longevity_formula_allowed,
        prohibited_categories=sorted(c.value for c in policy.prohibited_categories),
        rationale=policy.rationale,
    )


def _serialise_match(match: EventMatch) -> SBCEventMatchResponse:
    return SBCEventMatchResponse(
        event_id=match.event.event_id,
        domain=match.event.domain.value,
        description=match.event.description,
        overlap_days=match.overlap_days,
        domain_matches=match.domain_matches,
        matched_sangyas=list(match.matched_sangyas),
        is_confirmation=match.is_confirmation,
    )


router = APIRouter(prefix="/sbc", tags=["Sarvatobhadra Chakra"])


def _get_sbc_report_service(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> SBCReportService:
    return SBCReportService(wrapper)


def _get_sbc_scan_engine(
    service: SBCReportService = Depends(_get_sbc_report_service),
) -> SBCScanEngine:
    return SBCScanEngine(service)


def _serialise(report: SBCReport) -> SBCReportResponse:
    vedha_response = None
    if report.vedha_result is not None:
        vedha_response = SBCVedhaResultResponse(
            hits=[
                SBCVedhaHitResponse(
                    planet=h.planet,
                    direction=h.direction,
                    from_nakshatra=h.from_nakshatra,
                    score=h.score,
                )
                for h in report.vedha_result.hits
            ],
            total_score=report.vedha_result.total_score,
            zeroed_by_malefic_conjunction=report.vedha_result.zeroed_by_malefic_conjunction,
        )

    natal_attr_response = None
    if report.natal_attributes is not None:
        natal_attr_response = SBCNatalAttributesResponse(
            nama_akshara=report.natal_attributes.nama_akshara,
            janma_rashi=report.natal_attributes.janma_rashi,
            janma_rashi_icon=report.natal_attributes.janma_rashi_icon,
            tithi_name=report.natal_attributes.tithi_name,
            tithi_group=report.natal_attributes.tithi_group,
            tithi_number=report.natal_attributes.tithi_number,
            vara_name=report.natal_attributes.vara_name,
            vara_lord=report.natal_attributes.vara_lord,
        )

    sensitive_points_response = [
        SBCSensitivePointResponse(
            key=pt.key,
            name=pt.name,
            nakshatra_number=pt.nakshatra_number,
            nakshatra_token=pt.nakshatra_token,
            nakshatra_name=pt.nakshatra_name,
            status=pt.status,
            vedhas_received=pt.vedhas_received,
            benefic_hits=pt.benefic_hits,
            malefic_hits=pt.malefic_hits,
        )
        for pt in report.sensitive_points
    ]

    benefic_vedhas_response = [
        SBCVedhaEntryResponse(
            planet=v.planet,
            direction=v.direction,
            from_nakshatra=v.from_nakshatra,
            target_points=v.target_points,
            score=v.score,
            nature=v.nature,
            strength_factors=v.strength_factors,
        )
        for v in report.benefic_vedhas
    ]

    malefic_vedhas_response = [
        SBCVedhaEntryResponse(
            planet=v.planet,
            direction=v.direction,
            from_nakshatra=v.from_nakshatra,
            target_points=v.target_points,
            score=v.score,
            nature=v.nature,
            strength_factors=v.strength_factors,
        )
        for v in report.malefic_vedhas
    ]

    raw_hits_response = [
        SBCRawVedhaHitResponse(
            planet=rh.planet,
            direction=rh.direction,
            from_nakshatra=rh.from_nakshatra,
            target_type=rh.target_type,
            target_key=rh.target_key,
            target_name=rh.target_name,
            nature=rh.nature,
            strength_factors=rh.strength_factors,
            source_convention=rh.source_convention,
        )
        for rh in report.raw_hits
    ]

    synthesis_response = None
    if report.synthesis:
        synthesis_response = SBCSynthesisResponse(
            high_risk_areas=[
                SBCRiskItemResponse(
                    sangya_key=r.sangya_key,
                    sangya_name=r.sangya_name,
                    sangya_offset=r.sangya_offset,
                    nakshatra_name=r.nakshatra_name,
                    transiting_planet=r.transiting_planet,
                    transiting_nakshatra=r.transiting_nakshatra,
                    aspect_ray=r.aspect_ray,
                    domain=r.domain,
                    impact=r.impact,
                )
                for r in report.synthesis.high_risk_areas
            ],
            protective_shields=[
                SBCProtectionItemResponse(
                    sangya_key=p.sangya_key,
                    sangya_name=p.sangya_name,
                    sangya_offset=p.sangya_offset,
                    nakshatra_name=p.nakshatra_name,
                    transiting_planet=p.transiting_planet,
                    transiting_nakshatra=p.transiting_nakshatra,
                    aspect_ray=p.aspect_ray,
                    domain=p.domain,
                    impact=p.impact,
                )
                for p in report.synthesis.protective_shields
            ],
            executive_summary=report.synthesis.executive_summary,
            saving_grace=report.synthesis.saving_grace,
            practical_advice=report.synthesis.practical_advice,
        )

    return SBCReportResponse(
        moment_utc=report.moment_utc,
        tithi_number=report.tithi_number,
        positions=[
            SBCGridPlanetResponse(
                planet=p.planet,
                nakshatra=p.nakshatra,
                pada=p.pada,
                cellnum=p.cellnum,
                rashi=p.rashi,
                rashi_degree=p.rashi_degree,
                is_retrograde=p.is_retrograde,
                is_combust=p.is_combust,
                speed_deg_per_day=p.speed_deg_per_day,
                motion=p.motion,
                ray_direction=p.ray_direction,
            )
            for p in report.positions
        ],
        janma_nakshatra=report.janma_nakshatra,
        natal_attributes=natal_attr_response,
        sensitive_points=sensitive_points_response,
        benefic_vedhas=benefic_vedhas_response,
        malefic_vedhas=malefic_vedhas_response,
        raw_hits=raw_hits_response,
        synthesis=synthesis_response,
        convention_used=report.convention_used,
        total_benefic_score=report.total_benefic_score,
        total_malefic_score=report.total_malefic_score,
        vedha_result=vedha_response,
    )




@router.post("/report", response_model=SBCReportResponse)
async def get_sbc_report(
    request: SBCReportRequest,
    service: SBCReportService = Depends(_get_sbc_report_service),
) -> SBCReportResponse:
    moment_utc = request.moment_utc or datetime.now(timezone.utc)
    report = service.build_report(
        moment_utc,
        janma_nakshatra=request.janma_nakshatra,
        birth_datetime_utc=request.birth_datetime_utc,
        birth_latitude=request.birth_latitude,
        birth_longitude=request.birth_longitude,
        ayanamsa=request.ayanamsa or "lahiri",
    )
    return _serialise(report)



@router.post("/scan", response_model=SBCScanResponse)
async def scan_sbc(
    request: SBCScanRequest,
    engine: SBCScanEngine = Depends(_get_sbc_scan_engine),
) -> SBCScanResponse:
    events = [
        DisclosedEvent(
            event_id=e.event_id,
            domain=LifeDomain(e.domain),
            occurred_start_utc=e.occurred_start_utc,
            occurred_end_utc=e.occurred_end_utc,
            description=e.description,
            valence=EventValence(e.valence),
            significance=e.significance,
        )
        for e in request.disclosed_events
    ]

    hits = engine.scan(
        request.janma_nakshatra,
        request.start_utc,
        request.end_utc,
        step_days=request.step_days,
        now_utc=request.now_utc,
        disclosed_events=events,
        subject_status=SubjectStatus(request.subject_status),
    )
    windows = group_into_windows(hits, max_gap_days=request.window_gap_days)

    return SBCScanResponse(
        janma_nakshatra=request.janma_nakshatra,
        start_utc=request.start_utc,
        end_utc=request.end_utc,
        step_days=request.step_days,
        hits=[
            SBCScanHitResponse(
                moment_utc=h.moment_utc,
                vedha_result=_serialise(h.report).vedha_result,
                temporal_direction=h.temporal_direction.value,
                tier=h.tier.value,
                afflicted_sangyas=list(h.afflicted_sangyas),
                activated_sangyas=list(h.activated_sangyas),
                policy=_serialise_policy(h.policy),
                event_matches=[_serialise_match(m) for m in h.event_matches],
            )
            for h in hits
        ],
        windows=[
            SBCScanWindowResponse(
                start_utc=w.start_utc,
                end_utc=w.end_utc,
                duration_days=w.duration_days,
                hit_count=len(w.hits),
                temporal_direction=w.temporal_direction.value,
                tier=w.tier.value,
                afflicted_sangyas=list(w.afflicted_sangyas),
                policy=_serialise_policy(w.policy),
                event_matches=[_serialise_match(m) for m in w.event_matches],
                confirmed_by_disclosure=w.is_confirmed_by_disclosure,
            )
            for w in windows
        ],
    )


@router.post("/ai-analysis", response_model=AISBCAnalysisResponse)
async def analyze_sbc_ai(
    request: AISBCAnalysisRequest,
) -> AISBCAnalysisResponse:
    """
    Generate event-driven AI astrological insights from active Sarvatobhadra Chakra
    Vedhas and 10 Sangyas (Markets, Major Life Events, Muhurta/Protection).
    """
    return SBCAIAnalyzer.analyze(request)

