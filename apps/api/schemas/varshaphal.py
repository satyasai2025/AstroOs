"""AstroOS — Varshaphal (Tajika annual chart) API schemas — Stage 1."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from apps.api.schemas.common import BirthDataInput
from apps.api.schemas.horoscope import PanchangaSchema


class VarshaphalRequest(BirthDataInput):
    """Birth data + the target solar-return year (1 = first birthday)."""
    varsha_year: int = Field(ge=1, description="Nth solar return since birth")


class VarshaAscendantSchema(BaseModel):
    longitude: float
    sidereal_longitude: float
    rashi: str
    rashi_degree: float
    nakshatra: str
    pada: int
    nakshatra_lord: str = ""


class VarshaHouseCuspSchema(BaseModel):
    house_number: int = Field(ge=1, le=12)
    sidereal_longitude: float
    rashi: str


class VarshaPlanetPositionSchema(BaseModel):
    planet: str
    sidereal_longitude: float
    rashi: str
    rashi_degree: float
    house_number: int
    nakshatra: str
    pada: int
    is_retrograde: bool
    is_combust: bool
    dignity: Optional[str] = None


class MunthaSchema(BaseModel):
    rashi: str
    rashi_index: int = Field(ge=0, le=11)
    house_number: int = Field(ge=1, le=12)


class TajikaAspectSchema(BaseModel):
    planet_a: str
    planet_b: str
    aspect_angle: int
    current_orb_deg: float
    is_applying: bool
    is_ithasala: bool = Field(..., description="Applying and perfects before either planet leaves its sign")
    is_isharpha: bool = Field(..., description="Separating, having perfected the aspect within the last day")
    days_to_exact: Optional[float] = None


class YearLordSchema(BaseModel):
    candidates: list[str]
    selected: str
    selection_method: str = Field(
        ..., description="'benefic_aspect' | 'malefic_aspect' | 'fallback_first_candidate'"
    )


class SahamSchema(BaseModel):
    name: str
    sidereal_longitude: float
    rashi: str


class VarshaphalResponse(BaseModel):
    varsha_year: int
    solar_return_utc: datetime
    ascendant: VarshaAscendantSchema
    houses: list[VarshaHouseCuspSchema]
    planets: list[VarshaPlanetPositionSchema]
    panchanga: PanchangaSchema
    muntha: MunthaSchema
    tajika_aspects: list[TajikaAspectSchema]
    year_lord: YearLordSchema
    sahams: list[SahamSchema]
