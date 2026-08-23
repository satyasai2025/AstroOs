"""
AstroOS — KP Analysis API Schemas

Pydantic request/response models for the backend KP Analysis + Evidence
engine (POST /api/v1/kp/analyze). The response shapes mirror what the
KP Analysis Center consumes on the frontend — the analysis that used to
be computed client-side now arrives pre-computed from the backend.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

# ── Request ───────────────────────────────────────────────────────────────────


class KPAnalysisRequest(BaseModel):
    """One birth-data submission drives the whole KP analysis. Mirrors the
    workflow request's core fields — the same payload the frontend already
    holds, reused as-is."""

    birth_datetime_utc: datetime = Field(
        description="UTC birth datetime (ISO-8601, must include timezone offset)."
    )
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    ayanamsa: str = "lahiri"
    house_system: str = "P"  # KP is classically Placidus-cusp-specific — matches every other KP schema in this file
    transit_datetime_utc: Optional[datetime] = Field(
        default=None,
        description="Defaults to now (UTC) if omitted — the 'current transits' moment used for KP timing triggers.",
    )


# ── Response ──────────────────────────────────────────────────────────────────


class KPCuspResponse(BaseModel):
    house_number: int
    longitude: float
    rashi: str
    sign_lord: Optional[str] = None
    star_lord: str = ""
    sub_lord: str = ""
    sub_sub_lord: str = ""
    csl_signifies: list[int] = []
    csl_houses: list[int] = []
    interlinked_cusps: list[int] = []


class KPPlanetProfileResponse(BaseModel):
    planet: str
    rashi: str
    house_number: int
    rashi_house_number: int
    longitude: float
    sign_lord: Optional[str] = None
    star_lord: str = ""
    sub_lord: str = ""
    sub_sub_lord: str = ""
    is_retrograde: bool
    is_combust: bool
    dignity: Optional[str] = None
    occupied_house: int
    owned_houses: list[int] = []
    star_lord_houses: list[int] = []
    sub_lord_houses: list[int] = []
    signifies: list[int] = []
    csl_of: list[int] = []


class PlanetSignificatorResponse(BaseModel):
    planet: str
    grades: list[str] = []


class HouseSignificatorsResponse(BaseModel):
    houseNumber: int
    rashi: Optional[str] = None
    lord: Optional[str] = None
    occupants: list[str] = []
    significators: list[PlanetSignificatorResponse] = []


class RulingPlanetResponse(BaseModel):
    planet: str
    source: str
    priority: int


class CSLVerdictResponse(BaseModel):
    cusp: int
    csl: str
    csl_star_lord: str
    csl_signifies: list[int] = []
    required_houses: list[int] = []
    prohibited_houses: list[int] = []
    verdict: Literal["STRONG", "PARTIAL", "WEAK"]
    detail: str


class EventSignificatorResponse(BaseModel):
    planet: str
    grade: str
    housesSignified: list[int] = []


class EventPromiseResponse(BaseModel):
    eventKey: str
    label: str
    houses: list[int] = []
    primary_cusp: int
    csl_verdict: CSLVerdictResponse
    significators: list[EventSignificatorResponse] = []
    promise: Literal["POSITIVE", "PARTIAL", "WEAK"]


class SpecialFactorResponse(BaseModel):
    name: str
    category: Literal["CORE KP", "EXTENDED KP", "SUPPLEMENTARY"]
    value: str
    status: Literal["positive", "neutral", "caution"]
    evidence: str


class TransitPositionResponse(BaseModel):
    planet: str
    transit_rashi: str
    transit_rashi_degree: float
    transit_nakshatra: str
    is_retrograde: bool
    longitude: float
    star_lord: str
    sub_lord: str
    transit_rashi_house: Optional[int] = None


class TransitTriggerResponse(BaseModel):
    transit_planet: str
    transit_rashi: str
    transit_sub_lord: str
    transit_star_lord: str
    type: Literal["STAR", "SUB", "GURU", "CUSP"]
    activated: str
    note: str


class RulingPlanetTriggerResponse(BaseModel):
    rp: str
    rpSource: str
    matched_significator: str
    note: str


class DashaPeriodLinkResponse(BaseModel):
    lord: str
    level: str
    start: str
    end: str


class DashaLinkResponse(BaseModel):
    active: bool
    chain: list[DashaPeriodLinkResponse] = []
    significator_level: Optional[DashaPeriodLinkResponse] = None
    next_significator_period: Optional[DashaPeriodLinkResponse] = None


class EventTimingAnalysisResponse(BaseModel):
    eventKey: str
    label: str
    promise: Literal["POSITIVE", "PARTIAL", "WEAK"]
    significators: list[str] = []
    dasha_link: DashaLinkResponse
    transit_triggers: list[TransitTriggerResponse] = []
    rp_triggers: list[RulingPlanetTriggerResponse] = []
    fructification: Literal["OPEN", "PARTIAL", "CLOSED"]
    summary: str


class EvidenceStepResponse(BaseModel):
    label: str
    value: str


class EventEvidenceResponse(BaseModel):
    eventKey: str
    label: str
    houses: list[int] = []
    primary_cusp: int
    csl_verdict: CSLVerdictResponse
    significators: list[EventSignificatorResponse] = []
    promise: Literal["POSITIVE", "PARTIAL", "WEAK"]
    top_significator: Optional[str] = None
    fruitful_rp_intersection: list[str] = []
    active_dasha_level: Optional[str] = None
    steps: list[EvidenceStepResponse] = []
    verdict_detail: str


class KPAnalysisResponse(BaseModel):
    """The complete KP analysis + evidence for one chart at one transit
    moment — everything the KP Analysis Center renders, pre-computed."""

    cusps: list[KPCuspResponse]
    planet_profiles: list[KPPlanetProfileResponse]
    house_significators: list[HouseSignificatorsResponse]
    ruling_planets: list[RulingPlanetResponse]
    event_promises: list[EventPromiseResponse]
    special_factors: list[SpecialFactorResponse]
    timing: list[EventTimingAnalysisResponse]
    evidence: list[EventEvidenceResponse]
    transit_positions: list[TransitPositionResponse]
    transit_datetime_utc: datetime


# ── 1. KP Events & Custom Event Schemas ────────────────────────────────────────

class KPEventDefinitionResponse(BaseModel):
    id: str
    name: str
    category: str
    polarity: Literal["BENEFICIAL", "ADVERSE"] = "BENEFICIAL"
    primary_cusp: int
    required_houses: list[int] = []
    supporting_houses: list[int] = []
    adverse_houses: list[int] = []
    supporting_planets: list[str] = []
    supporting_signs: list[str] = []
    notes: str = ""


class KPEvaluateEventRequest(BaseModel):
    birth_datetime_utc: datetime
    latitude: float
    longitude: float
    ayanamsa: str = "lahiri"
    house_system: str = "P"
    transit_datetime_utc: Optional[datetime] = None
    event_id: Optional[str] = None
    custom_event: Optional[KPEventDefinitionResponse] = None


class KPEvaluateEventResponse(BaseModel):
    event: KPEventDefinitionResponse
    csl_verdict: CSLVerdictResponse
    promise: Literal["POSITIVE", "PARTIAL", "WEAK", "ADVERSE_RISK"]
    is_adverse: bool
    summary_verdict: str
    active_dasha_fructification: str
    timing_window: str
    audit_chain: list[str]


# ── 2. KP Birth Time Rectification (BTR) Schemas ──────────────────────────────

class KPBTRRectifyRequest(BaseModel):
    nominal_datetime_utc: datetime = Field(
        description="Recorded/approximate birth time to rectify."
    )
    latitude: float
    longitude: float
    window_minutes: int = Field(default=15, ge=1, le=120)
    step_seconds: int = Field(default=10, ge=1, le=60)
    gender: Optional[Literal["male", "female", "m", "f"]] = None
    ayanamsa: str = "lahiri"
    house_system: str = "P"
    top_k: int = Field(default=5, ge=1, le=20)


class KPBTRCandidateResponse(BaseModel):
    candidate_datetime_utc: datetime
    offset_seconds: int
    ascendant_degree: float
    ascendant_rashi: str
    ascendant_sign_lord: str
    ascendant_star_lord: str
    ascendant_sub_lord: str
    ascendant_sub_sub_lord: str
    moon_star_lord: str
    score: float
    rule_1_moon_star_match: bool
    rule_2_gender_match: bool
    rule_3_rp_agreement: bool
    audit_trail: list[str] = []


class KPBTRScanResponse(BaseModel):
    nominal_datetime_utc: datetime
    window_minutes: int
    step_seconds: int
    gender: Optional[str]
    total_candidates_scanned: int
    best_candidate: Optional[KPBTRCandidateResponse]
    top_candidates: list[KPBTRCandidateResponse] = []


# ── 3. Real-Time Ruling Planets (RP) Schemas ──────────────────────────────────

class KPRulingPlanetsRequest(BaseModel):
    query_datetime_utc: Optional[datetime] = Field(
        default=None, description="Defaults to current UTC time if omitted."
    )
    latitude: float
    longitude: float
    ayanamsa: str = "lahiri"
    house_system: str = "P"


class KPRulingPlanetItemResponse(BaseModel):
    planet: str
    role: str
    priority: int
    is_node: bool
    represented_planet: Optional[str] = None
    note: str = ""


class KPRulingPlanetsResponse(BaseModel):
    query_datetime_utc: datetime
    day_lord: str
    ascendant_sign_lord: str
    ascendant_star_lord: str
    ascendant_sub_lord: str
    moon_sign_lord: str
    moon_star_lord: str
    moon_sub_lord: str
    ruling_planets_ordered: list[KPRulingPlanetItemResponse]
    raw_ruling_planets: list[str]
    node_representations: dict[str, list[str]]


# ── 4. Sub-Sub Lord (SSL) Reference Table Schemas ─────────────────────────────

class KPSSLSliceResponse(BaseModel):
    sign: str
    sign_lord: str
    nakshatra: str
    star_lord: str
    sub_lord: str
    sub_sub_lord: str
    start_degree: float
    end_degree: float
    span_degree: float
    formatted_start: str
    formatted_end: str


class KPSSLTableResponse(BaseModel):
    total_sub_sub_lords: int = 2193
    slices: list[KPSSLSliceResponse]

