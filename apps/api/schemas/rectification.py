"""
AstroOS — Inverse Natal Profiling & Chart Rectification Schemas (Priority 14)
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class LifeEventInput(BaseModel):
    event_id: str = Field(default="evt-1", description="Unique event identifier")
    event_type: str = Field(description="Event type e.g. 'marriage', 'career_rise', 'progeny', 'relocation', 'health_surgery'")
    event_date: date = Field(description="Date of the historical event")
    significance_weight: float = Field(default=1.0, ge=0.1, le=5.0)
    description: str = Field(default="", description="Context of the event")


class RectificationSearchRequest(BaseModel):
    base_datetime_utc: datetime = Field(description="Reported base birth moment in UTC")
    latitude: float = Field(default=13.0827, ge=-90.0, le=90.0)
    longitude: float = Field(default=80.2707, ge=-180.0, le=180.0)
    window_minutes: int = Field(default=15, ge=1, le=120)
    step_seconds: int = Field(default=60, ge=15, le=300)
    events: list[LifeEventInput] = Field(default_factory=list)
    ayanamsa: str = Field(default="lahiri")


class EventEvaluationDetailItem(BaseModel):
    event_id: str
    event_type: str
    event_date: date
    dasha_activation_score: float
    transit_activation_score: float
    house_relevance_score: float
    event_composite_score: float
    active_dasha_lords: list[str]
    transiting_planets_activated: list[str]
    explanation: str


class RectificationCandidateItem(BaseModel):
    candidate_id: str
    proposed_birth_datetime_utc: datetime
    offset_seconds: int
    ascendant_rashi: str
    ascendant_longitude: float
    ascendant_nakshatra: str
    ascendant_pada: int
    d9_ascendant_rashi: str
    dasha_event_score: float
    transit_event_score: float
    tattva_shodhana_score: float
    composite_posterior_probability: float
    matched_events_count: int
    event_evaluations: list[EventEvaluationDetailItem]
    audit_trail: str


class RectificationSearchResponse(BaseModel):
    query_id: str
    base_datetime_utc: datetime
    search_window_start: datetime
    search_window_end: datetime
    step_seconds: int
    total_candidates_evaluated: int
    life_events_count: int
    top_candidates: list[RectificationCandidateItem]
    best_candidate: Optional[RectificationCandidateItem]
    bayesian_prior_used: str
    methodology_provenance: str
