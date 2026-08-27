"""
AstroOS — Latta Dosha Router

Endpoints
---------
POST /api/v1/latta/report — Which transiting grahas are currently
                             kicking a given nakshatra, the life
                             domains struck, and the temporal-stance
                             policy governing what may be said about it.

The response reports life *domains*, never a specific predicted event:
Latta's classical wording is the bluntest in this area of the tradition
and is not reproduced here. See ``packages/shared/latta.py`` for the
sourcing tier of the offset table, which the response also carries.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.routers.sbc import _serialise_match, _serialise_policy
from apps.api.schemas.latta import (
    LattaHitResponse,
    LattaReportRequest,
    LattaReportResponse,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.latta_engine import LattaEngine, LattaReport
from packages.shared.disclosed_events import DisclosedEvent, EventValence, LifeDomain
from packages.shared.temporal_stance import SubjectStatus

router = APIRouter(prefix="/latta", tags=["Latta Dosha"])


def _get_latta_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> LattaEngine:
    return LattaEngine(wrapper)


def _serialise(report: LattaReport) -> LattaReportResponse:
    return LattaReportResponse(
        janma_nakshatra=report.janma_nakshatra,
        moment_utc=report.moment_utc,
        is_afflicted=report.is_afflicted,
        hits=[
            LattaHitResponse(
                planet=h.planet,
                from_nakshatra=h.from_nakshatra,
                struck_nakshatra=h.struck_nakshatra,
                offset=h.offset,
                direction=h.direction.value,
                is_malefic=h.is_malefic,
                is_severe=h.is_severe,
                domains=sorted(d.value for d in h.domains),
                verification=h.verification.value,
            )
            for h in report.hits
        ],
        severe_hit_count=len(report.severe_hits),
        transit_nakshatras=dict(report.transit_nakshatras),
        domains_struck=sorted(d.value for d in report.domains_struck),
        policy=_serialise_policy(report.policy),
        event_matches=[_serialise_match(m) for m in report.event_matches],
        confirmed_by_disclosure=report.is_confirmed_by_disclosure,
        verification=report.verification.value,
        named_combinations_status={
            "status": report.named_combinations_status["status"].value,
            "names": list(report.named_combinations_status["names"]),
            "blocked_on": report.named_combinations_status["blocked_on"],
            "note": report.named_combinations_status["note"],
        },
    )


@router.post("/report", response_model=LattaReportResponse)
async def get_latta_report(
    request: LattaReportRequest,
    engine: LattaEngine = Depends(_get_latta_engine),
) -> LattaReportResponse:
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

    report = engine.build_report(
        janma_nakshatra=request.janma_nakshatra,
        moment_utc=request.moment_utc or datetime.now(timezone.utc),
        now_utc=request.now_utc,
        disclosed_events=events,
        subject_status=SubjectStatus(request.subject_status),
    )
    return _serialise(report)
