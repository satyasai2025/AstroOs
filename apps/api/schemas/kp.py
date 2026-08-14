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
    house_system: str = "W"
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
