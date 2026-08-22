"""AstroOS — Prashna (Horary) API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PrashnaArudhaRequest(BaseModel):
    seed_number: int = Field(..., ge=1, le=2193, description="Horary number chosen by the querent (1-249 or 1-2193).")
    system: Literal["kp_249", "kp_2193"] = Field("kp_249", description="KP Arudha division system.")


class PrashnaArudhaResponse(BaseModel):
    seed_number: int
    system: str
    sidereal_longitude: float
    rashi: str
    rashi_degree: float
    nakshatra: str
    sign_lord: str
    star_lord: str
    sub_lord: str
    sub_sub_lord: str = ""
    arc_start_degree: float
    arc_end_degree: float


class PrashnaSphutaRequest(BaseModel):
    moment_utc: datetime = Field(..., description="Query/birth moment, UTC.")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    ayanamsa: str = Field("lahiri", description="Ayanamsa system to use.")


class SphutaPositionResponse(BaseModel):
    name: str
    sidereal_longitude: float
    rashi: str
    rashi_degree: float
    nakshatra: str
    pada: int
    nakshatra_lord: str
    house_number: int


class PrashnaSphutaResponse(BaseModel):
    sphutas: list[SphutaPositionResponse]
    ascendant_longitude: float
    gulika_longitude: float


class RulingPlanetEntryResponse(BaseModel):
    point_name: str
    sign_lord: str
    star_lord: str
    sub_lord: str
    sub_sub_lord: str
    as_aspecting: str = ""
    is_conjunction: str = ""


class RulingPlanetsSnapshotResponse(BaseModel):
    casting_time: str
    hora_lord: str
    day_lord: str
    entries: list[RulingPlanetEntryResponse]


class ArabicPartComputedResponse(BaseModel):
    name: str
    category: str
    formula_used: str
    is_day_formula: bool
    sidereal_longitude: float
    rashi: str
    rashi_degree_str: str
    sign_lord: str
    star_lord: str
    sub_lord: str
    sub_sub_lord: str
    description: str


class KeyEvidenceResponse(BaseModel):
    factor: str
    indication: str
    explanation: str
    weight: int


class RelevantHouseResponse(BaseModel):
    house: int
    sign: str
    lord: str
    strength: str
    note: str


class TimingIndicationResponse(BaseModel):
    likely_window: str
    dasha_mahadasha: str
    antardasha: str
    transit_support: str
    moon_cycle: str


class RuleTriggeredResponse(BaseModel):
    rule_id: str
    rule_principle: str
    reference: str
    triggered: str
    weight: int


class ContradictionResponse(BaseModel):
    title: str
    description: str
    advice: str


class PrashnaJudgementResponse(BaseModel):
    verdict: str
    confidence_percentage: int
    strength_label: str
    summary: str
    key_evidences: list[KeyEvidenceResponse]
    relevant_houses: list[RelevantHouseResponse]
    timing: TimingIndicationResponse
    conclusions: list[str]
    supporting_rules: list[RuleTriggeredResponse]
    contradictions: list[ContradictionResponse]


class HoraryPlanetPosition(BaseModel):
    planet: str
    sign: str
    degree_str: str
    degree_float: float
    nakshatra: str
    pada: int
    own_houses: list[int] = Field(default_factory=list)
    sign_lord: str
    star_lord: str
    sub_lord: str
    sub_sub_lord: str
    csl: str = ""
    cstl: str = ""
    aspects: list[str] = Field(default_factory=list)
    conjunctions: list[str] = Field(default_factory=list)


class HoraryHouseCusp(BaseModel):
    house: int
    sign: str
    degree_str: str
    degree_float: float
    nakshatra: str
    pada: int
    occupants: list[str] = Field(default_factory=list)
    sign_lord: str
    star_lord: str
    sub_lord: str
    sub_sub_lord: str
    aspects: list[str] = Field(default_factory=list)
    conjunctions: list[str] = Field(default_factory=list)


class PrashnaFullCalculationRequest(BaseModel):
    name: str = "Querent"
    gender: str = "Male"
    question: str = "Will I get this job?"
    moment_utc: datetime = Field(default_factory=datetime.utcnow)
    latitude: float = 18.5204
    longitude: float = 73.8567
    place_name: str = "Pune, Maharashtra, India"
    timezone_offset: float = 5.5
    horary_number: int | None = None
    horary_system: Literal["kp_249", "kp_2193"] = "kp_249"
    ayanamsa: str = "lahiri"


class PrashnaFullCalculationResponse(BaseModel):
    name: str
    gender: str
    question: str
    moment_utc: datetime
    place_name: str
    latitude: float
    longitude: float
    timezone_offset: float
    ayanamsa: str
    horary_number: int | None
    horary_system: str
    arudha: PrashnaArudhaResponse | None
    planets: list[HoraryPlanetPosition]
    cusps: list[HoraryHouseCusp]
    ruling_planets_ct: RulingPlanetsSnapshotResponse
    ruling_planets_rt: RulingPlanetsSnapshotResponse
    arabic_parts: list[ArabicPartComputedResponse]
    sphutas: list[SphutaPositionResponse]
    judgement: PrashnaJudgementResponse
