"""
AstroOS — Sensitive timeline Router

Endpoints
---------
POST /api/v1/sensitive-timeline/report   — Reading surface. Past windows
                                            the native can check against
                                            their own life, plus future
                                            alerts, each carrying the
                                            policy governing what may be
                                            said about it.
POST /api/v1/sensitive-timeline/validate — Research surface. The same
                                            windows scored against events
                                            the native actually reported:
                                            coverage-adjusted lift, hits,
                                            and — first-class — the misses.

Neither endpoint names a predicted event. Windows report a life *domain*
and a confidence-qualified period; whether a specific event may be named
is decided by ``packages/shared/temporal_stance.py`` and returned on
each window as ``policy``.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.routers.sbc import _serialise_match, _serialise_policy
from apps.api.schemas.sensitive_timeline import (
    DisclosedEventResponse,
    EventOutcomeResponse,
    EventSignatureResponse,
    IndicatorResponse,
    RetrodictionValidationRequest,
    SensitiveTimelineRequest,
    SensitiveTimelineResponse,
    SensitiveWindowResponse,
    TechniqueScoreResponse,
    WindowNarrativeResponse,
    ValidationMetricsResponse,
    ValidationReportResponse,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.latta_engine import LattaEngine
from apps.api.services.retrodiction_validation_engine import (
    RetrodictionValidationEngine,
    ValidationReport,
)
from apps.api.services.sbc_report_service import SBCReportService
from apps.api.services.sensitive_narrative import render_window
from apps.api.services.sensitive_timeline_service import (
    SensitiveTimeline,
    SensitiveTimelineService,
    SensitiveWindow,
)
from packages.shared.disclosed_events import DisclosedEvent, EventValence, LifeDomain
from packages.shared.sensitive_convergence import ConvergenceGrade
from packages.shared.temporal_stance import SubjectStatus

router = APIRouter(prefix="/sensitive-timeline", tags=["Sensitive Timeline"])


def _get_timeline_service(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> SensitiveTimelineService:
    return SensitiveTimelineService(SBCReportService(wrapper), LattaEngine(wrapper))


def _to_events(request: SensitiveTimelineRequest) -> list[DisclosedEvent]:
    return [
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


def _build(
    service: SensitiveTimelineService,
    request: SensitiveTimelineRequest,
) -> SensitiveTimeline:
    return service.build_timeline(
        janma_nakshatra=request.janma_nakshatra,
        birth_datetime_utc=request.birth_datetime_utc,
        start_utc=request.start_utc,
        end_utc=request.end_utc,
        sbc_janma_nakshatra=request.sbc_janma_nakshatra,
        step_days=request.step_days,
        now_utc=request.now_utc,
        disclosed_events=_to_events(request),
        subject_status=SubjectStatus(request.subject_status),
        min_grade=ConvergenceGrade(request.min_grade),
        min_techniques=request.min_techniques,
    )


def _serialise_signature(signature, direction) -> EventSignatureResponse | None:
    if signature is None:
        return None
    return EventSignatureResponse(
        sangya_key=signature.sangya_key,
        sangya_name=signature.sangya_name,
        graha=signature.graha,
        nature=signature.nature,
        described=signature.describe(direction),
    )


def _serialise_event(event: DisclosedEvent) -> DisclosedEventResponse:
    return DisclosedEventResponse(
        event_id=event.event_id,
        domain=event.domain.value,
        description=event.description,
        occurred_start_utc=event.occurred_start_utc,
        occurred_end_utc=event.occurred_end_utc,
        significance=event.significance,
    )


def _serialise_window(window: SensitiveWindow, now_utc: datetime) -> SensitiveWindowResponse:
    narrative = render_window(window, now_utc)
    return SensitiveWindowResponse(
        start_utc=window.start_utc,
        end_utc=window.end_utc,
        duration_days=window.duration_days,
        temporal_direction=window.temporal_direction.value,
        verdict=window.verdict,
        techniques_agreeing=window.techniques_agreeing,
        polarity=window.polarity.value,
        grade=window.grade.value,
        lead_time_days=window.lead_time_days(now_utc),
        domains=sorted(d.value for d in window.domains),
        domains_all=sorted(d.value for d in window.domains_all),
        indicators=[
            IndicatorResponse(
                technique=i.technique.value,
                detail=i.detail,
                domains=sorted(d.value for d in i.domains),
                is_severe=i.is_severe,
                verification=i.verification.value,
                polarity=i.polarity.value,
                signature=_serialise_signature(i.signature, window.policy.direction),
            )
            for i in window.indicators
        ],
        techniques=window.techniques,
        verification=window.verification.value,
        policy=_serialise_policy(window.policy),
        narrative=WindowNarrativeResponse(
            headline=narrative.headline,
            body=narrative.body,
            categories=narrative.categories,
            qualifier=narrative.qualifier,
            invitation=narrative.invitation,
            redactions=narrative.redactions,
        ),
        event_matches=[_serialise_match(m) for m in window.event_matches],
        confirmed_by_disclosure=window.is_confirmed_by_disclosure,
    )


def _serialise_timeline(timeline: SensitiveTimeline) -> SensitiveTimelineResponse:
    now = timeline.now_utc
    return SensitiveTimelineResponse(
        janma_nakshatra=timeline.janma_nakshatra,
        start_utc=timeline.start_utc,
        end_utc=timeline.end_utc,
        now_utc=now,
        step_days=timeline.step_days,
        past_windows=[_serialise_window(w, now) for w in timeline.past_windows],
        present_windows=[_serialise_window(w, now) for w in timeline.present_windows],
        future_alerts=[_serialise_window(w, now) for w in timeline.future_alerts],
        unchecked_techniques=timeline.unchecked_techniques,
        unexplained_events=[_serialise_event(e) for e in timeline.unexplained_events],
    )


def _serialise_validation(report: ValidationReport) -> ValidationReportResponse:
    m = report.metrics
    return ValidationReportResponse(
        janma_nakshatra=report.janma_nakshatra,
        scanned_start_utc=report.scanned_start_utc,
        scanned_end_utc=report.scanned_end_utc,
        metrics=ValidationMetricsResponse(
            total_events=m.total_events,
            hits=m.hits,
            misses=m.misses,
            overlapped_wrong_domain=m.overlapped_wrong_domain,
            polarity_mismatch=m.polarity_mismatch,
            coverage=m.coverage,
            recall=m.recall,
            lift=m.lift,
            precision=m.precision,
            precision_note=m.precision_note,
            windows_examined=m.windows_examined,
            windows_with_a_disclosed_event=m.windows_with_a_disclosed_event,
            is_better_than_chance=m.is_better_than_chance,
        ),
        outcomes=[
            EventOutcomeResponse(
                event=_serialise_event(o.event),
                is_hit=o.is_hit,
                overlapped_wrong_domain=o.overlapped_wrong_domain,
                polarity_mismatch=o.polarity_mismatch,
                matched_window_start=o.matched_window_start,
                matched_grade=o.matched_grade.value if o.matched_grade else None,
                techniques_present=list(o.techniques_present),
            )
            for o in report.outcomes
        ],
        technique_scores=[
            TechniqueScoreResponse(
                technique=s.technique,
                hits_contributed=s.hits_contributed,
                total_hits=s.total_hits,
                share=s.share,
            )
            for s in report.technique_scores
        ],
        unchecked_techniques=report.unchecked_techniques,
        missed_events=[_serialise_event(e) for e in report.missed_events],
        caveats=report.caveats,
    )


@router.post("/report", response_model=SensitiveTimelineResponse)
async def get_sensitive_timeline(
    request: SensitiveTimelineRequest,
    service: SensitiveTimelineService = Depends(_get_timeline_service),
) -> SensitiveTimelineResponse:
    return _serialise_timeline(_build(service, request))


@router.post("/validate", response_model=ValidationReportResponse, tags=["Research"])
async def validate_retrodiction(
    request: RetrodictionValidationRequest,
    service: SensitiveTimelineService = Depends(_get_timeline_service),
) -> ValidationReportResponse:
    """Score computed windows against the native's own reported events.

    Read ``metrics.lift`` before ``metrics.recall``: a technique whose windows
    blanket half a life will show excellent recall while being no better than
    marking dates at random.
    """
    timeline = _build(service, request)
    report = RetrodictionValidationEngine().validate(
        timeline,
        events=_to_events(request),
        events_are_exhaustive=request.events_are_exhaustive,
    )
    return _serialise_validation(report)
