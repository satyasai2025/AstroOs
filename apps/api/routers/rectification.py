"""
AstroOS — Inverse Natal Profiling & Chart Rectification Router (Priority 14)

Endpoints:
  - POST /api/v1/research/rectification/search
  - GET  /api/v1/research/rectification/event-types
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.domain.rectification import EventType, LifeEventRecord
from apps.api.schemas.rectification import (
    EventEvaluationDetailItem,
    RectificationCandidateItem,
    RectificationSearchRequest,
    RectificationSearchResponse,
)
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.rectification_engine import RectificationEngine

router = APIRouter(prefix="/research/rectification", tags=["Research: Inverse Natal Profiling & Rectification"])


@router.post("/search", response_model=RectificationSearchResponse, status_code=status.HTTP_200_OK)
def search_rectification(
    req: RectificationSearchRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> RectificationSearchResponse:
    """Execute Bayesian inverse natal chart reconstruction across search window."""
    horoscope_engine = HoroscopeEngine(wrapper)
    dasha_engine = DashaEngine(wrapper)
    engine = RectificationEngine(
        wrapper=wrapper,
        horoscope_engine=horoscope_engine,
        dasha_engine=dasha_engine,
    )

    domain_events = [
        LifeEventRecord(
            event_id=e.event_id,
            event_type=EventType(e.event_type.lower()) if e.event_type.lower() in [et.value for et in EventType] else EventType.CAREER_RISE,
            event_date=e.event_date,
            significance_weight=e.significance_weight,
            description=e.description,
        )
        for e in req.events
    ]

    result = engine.search_rectification(
        base_datetime_utc=req.base_datetime_utc,
        latitude=req.latitude,
        longitude=req.longitude,
        events=domain_events,
        window_minutes=req.window_minutes,
        step_seconds=req.step_seconds,
        ayanamsa=req.ayanamsa,
    )

    def _map_candidate(c) -> RectificationCandidateItem:
        return RectificationCandidateItem(
            candidate_id=c.candidate_id,
            proposed_birth_datetime_utc=c.proposed_birth_datetime_utc,
            offset_seconds=c.offset_seconds,
            ascendant_rashi=c.ascendant_rashi,
            ascendant_longitude=c.ascendant_longitude,
            ascendant_nakshatra=c.ascendant_nakshatra,
            ascendant_pada=c.ascendant_pada,
            d9_ascendant_rashi=c.d9_ascendant_rashi,
            dasha_event_score=c.dasha_event_score,
            transit_event_score=c.transit_event_score,
            tattva_shodhana_score=c.tattva_shodhana_score,
            composite_posterior_probability=c.composite_posterior_probability,
            matched_events_count=c.matched_events_count,
            event_evaluations=[
                EventEvaluationDetailItem(
                    event_id=ee.event_id,
                    event_type=ee.event_type.value,
                    event_date=ee.event_date,
                    dasha_activation_score=ee.dasha_activation_score,
                    transit_activation_score=ee.transit_activation_score,
                    house_relevance_score=ee.house_relevance_score,
                    event_composite_score=ee.event_composite_score,
                    active_dasha_lords=list(ee.active_dasha_lords),
                    transiting_planets_activated=list(ee.transiting_planets_activated),
                    explanation=ee.explanation,
                )
                for ee in c.event_evaluations
            ],
            audit_trail=c.audit_trail,
        )

    return RectificationSearchResponse(
        query_id=result.query_id,
        base_datetime_utc=result.base_datetime_utc,
        search_window_start=result.search_window_start,
        search_window_end=result.search_window_end,
        step_seconds=result.step_seconds,
        total_candidates_evaluated=result.total_candidates_evaluated,
        life_events_count=result.life_events_count,
        top_candidates=[_map_candidate(c) for c in result.top_candidates],
        best_candidate=_map_candidate(result.best_candidate) if result.best_candidate else None,
        bayesian_prior_used=result.bayesian_prior_used,
        methodology_provenance=result.methodology_provenance,
    )


@router.get("/event-types", status_code=status.HTTP_200_OK)
def list_event_types() -> dict[str, Any]:
    """Lists supported life event types and their primary classical house governances."""
    return {
        "event_types": [
            {"type": "marriage", "label": "Marriage / Relationship Milestone", "primary_houses": [7, 11, 2]},
            {"type": "career_rise", "label": "Major Career Rise / Promotion", "primary_houses": [10, 11, 6, 1]},
            {"type": "progeny", "label": "Child Birth / Progeny", "primary_houses": [5, 9, 2]},
            {"type": "relocation", "label": "Foreign Relocation / House Change", "primary_houses": [4, 9, 12, 3]},
            {"type": "health_surgery", "label": "Major Surgery / Health Event", "primary_houses": [6, 8, 12, 1]},
            {"type": "financial_windfall", "label": "Financial Windfall / Wealth Influx", "primary_houses": [2, 11, 5, 9]},
            {"type": "major_bereavement", "label": "Major Bereavement / Family Loss", "primary_houses": [8, 12, 2, 7]},
        ]
    }
