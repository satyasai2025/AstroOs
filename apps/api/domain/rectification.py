"""
AstroOS — Inverse Natal Profiling & Chart Rectification Domain Models (Priority 14)

Defines domain dataclasses for:
  - Life Event Records (Marriage, Career, Progeny, Relocation, Medical)
  - Discretized Candidate Birth Moments
  - Dasha-Transit-Event Bayesian Likelihood Scoring
  - Classical Tattva & Kunda Shodhana Alignment
  - Rectification Evaluation Result Matrix
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional


class EventType(str, Enum):
    MARRIAGE = "marriage"
    CAREER_RISE = "career_rise"
    PROGENY = "progeny"
    RELOCATION = "relocation"
    HEALTH_SURGERY = "health_surgery"
    FINANCIAL_WINDFALL = "financial_windfall"
    MAJOR_BEREAVEMENT = "major_bereavement"


@dataclass(frozen=True)
class LifeEventRecord:
    """Historical life event used to compute inverse posterior chart likelihood."""
    event_id: str
    event_type: EventType
    event_date: date
    significance_weight: float  # 0.5 to 2.0
    description: str


@dataclass(frozen=True)
class EventEvaluationDetail:
    """Per-event diagnostic score for a candidate chart moment."""
    event_id: str
    event_type: EventType
    event_date: date
    dasha_activation_score: float  # 0.0 to 100.0
    transit_activation_score: float  # 0.0 to 100.0
    house_relevance_score: float  # 0.0 to 100.0
    event_composite_score: float  # 0.0 to 100.0
    active_dasha_lords: tuple[str, ...]
    transiting_planets_activated: tuple[str, ...]
    explanation: str


@dataclass(frozen=True)
class RectificationCandidate:
    """A discretized candidate birth moment evaluated against all life events."""
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
    composite_posterior_probability: float  # Normalized 0.0 to 100.0
    matched_events_count: int
    event_evaluations: tuple[EventEvaluationDetail, ...]
    audit_trail: str


@dataclass(frozen=True)
class RectificationResult:
    """Complete inverse chart reconstruction search result."""
    query_id: str
    base_datetime_utc: datetime
    search_window_start: datetime
    search_window_end: datetime
    step_seconds: int
    total_candidates_evaluated: int
    life_events_count: int
    top_candidates: tuple[RectificationCandidate, ...]
    best_candidate: Optional[RectificationCandidate]
    bayesian_prior_used: str
    methodology_provenance: str
