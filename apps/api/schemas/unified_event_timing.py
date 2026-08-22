"""
AstroOS — Unified Multi-System Event Timing Engine Schemas
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class DashaPeriodItemSchema(BaseModel):
    level: str
    lord: str
    start_date: str
    end_date: str


class DashaEvidenceSchema(BaseModel):
    active_chain: list[DashaPeriodItemSchema]
    significator_lords: list[str]
    is_dasha_active: bool
    active_level: Optional[str] = None
    active_lord: Optional[str] = None
    score: float
    detail: str


class GocharaTransitItemSchema(BaseModel):
    planet: str
    rashi: str
    house_from_lagna: int
    house_from_moon: int
    is_retrograde: bool
    is_favorable: bool
    aspects: list[str] = Field(default_factory=list)


class GocharaEvidenceSchema(BaseModel):
    key_transits: list[GocharaTransitItemSchema]
    gochara_vedha_clear: bool
    ashtakavarga_support: float
    sade_sati_status: Optional[str] = None
    score: float
    detail: str


class SBCVedhaHitItemSchema(BaseModel):
    transiting_planet: str
    ray_direction: str
    from_nakshatra: str
    target_point: str
    target_name: str
    nature: str  # benefic | malefic
    impact: str


class SBCVedhaEvidenceSchema(BaseModel):
    janma_hits: list[SBCVedhaHitItemSchema]
    relevant_sangya_hits: list[SBCVedhaHitItemSchema]
    benefic_count: int
    malefic_count: int
    net_protection: float
    score: float
    detail: str


class KPTransitTriggerItemSchema(BaseModel):
    transit_planet: str
    transit_sign: str
    transit_nakshatra_lord: str
    transit_sub_lord: str
    trigger_type: str  # STAR | SUB | GURU | CUSP
    significator_matched: str
    detail: str


class KPEvidenceSchema(BaseModel):
    primary_cusp: int
    csl: str
    csl_star_lord: str
    csl_signifies: list[int]
    required_houses: list[int]
    active_transit_triggers: list[KPTransitTriggerItemSchema]
    rp_triggers: list[str]
    dusthana_veto: bool
    fructification: str  # OPEN | PARTIAL | CLOSED
    score: float
    detail: str


class UnifiedTimingSnapshotSchema(BaseModel):
    evaluated_datetime_utc: str
    event_type: str
    dasha: DashaEvidenceSchema
    gochara: GocharaEvidenceSchema
    sbc: SBCVedhaEvidenceSchema
    kp: KPEvidenceSchema
    confluence_score: float
    confidence_tier: str  # VERY_HIGH | HIGH | MODERATE | LOW | UNFAVORABLE
    system_weights: dict[str, float]
    primary_positive_triggers: list[str]
    primary_inhibiting_factors: list[str]
    summary_narrative: str


class TimelineSamplePointSchema(BaseModel):
    date: str
    confluence_score: float
    dasha_score: float
    gochara_score: float
    sbc_score: float
    kp_score: float
    peak_flag: bool = False


class UnifiedEventTimingWindowSchema(BaseModel):
    window_id: str
    event_type: str
    start_date: str
    end_date: str
    peak_date: str
    peak_score: float
    confluence_status: str  # HIGH_CONFLUENCE | MODERATE_CONFLUENCE | PARTIAL_WINDOW | INHIBITED
    system_scores: dict[str, float]
    primary_drivers: list[str]
    inhibiting_factors: list[str]
    narrative: str


# ── Request / Response Envelopes ─────────────────────────────────────────────


class UnifiedEventTimingAnalyzeRequest(BaseModel):
    birth_datetime_utc: str
    latitude: float
    longitude: float
    ayanamsa: Optional[str] = "lahiri"
    house_system: Optional[str] = "P"  # Placidus for KP cusps
    event_type: str = "marriage"  # marriage | career | wealth | property | foreign_travel | health | childbirth | education
    start_date: Optional[str] = None  # YYYY-MM-DD, defaults to today
    end_date: Optional[str] = None    # YYYY-MM-DD, defaults to +3 years
    evaluation_datetime_utc: Optional[str] = None  # Specific moment for snapshot; defaults to now
    step_days: Optional[int] = 15     # Interval for timeline scanning (default: 15 days)
    chart_id: Optional[str] = None


class UnifiedEventTimingAnalyzeResponse(BaseModel):
    chart_id: Optional[str] = None
    event_type: str
    start_date: str
    end_date: str
    evaluated_moment_snapshot: UnifiedTimingSnapshotSchema
    candidate_windows: list[UnifiedEventTimingWindowSchema]
    time_series: list[TimelineSamplePointSchema]
    confluence_summary: str


class UnifiedMomentEvaluationRequest(BaseModel):
    birth_datetime_utc: str
    latitude: float
    longitude: float
    ayanamsa: Optional[str] = "lahiri"
    house_system: Optional[str] = "P"
    event_type: str = "marriage"
    target_datetime_utc: str  # The scrubbed time-travel moment
    chart_id: Optional[str] = None


class UnifiedMomentEvaluationResponse(BaseModel):
    chart_id: Optional[str] = None
    event_type: str
    snapshot: UnifiedTimingSnapshotSchema
