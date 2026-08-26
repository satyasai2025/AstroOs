"""AstroOS — Varshaphal (Tajika annual chart) API schemas — Complete Classical Standard."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from apps.api.schemas.common import BirthDataInput
from apps.api.schemas.horoscope import PanchangaSchema


class VarshaphalRequest(BirthDataInput):
    """Birth data + the target solar-return year (1 = first birthday)."""
    varsha_year: int = Field(ge=1, description="Nth solar return since birth")


class MasaPraveshRequest(BirthDataInput):
    """Birth data + target solar return year + optional specific month number (1..12)."""
    varsha_year: int = Field(ge=1, description="Nth solar return since birth")
    month_number: Optional[int] = Field(None, ge=1, le=12, description="Specific month (1..12), or None for all 12")


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
    deeptamsha_orb_limit: float = 12.0
    within_deeptamsha: bool = True


class PanchavargiyaBalaSchema(BaseModel):
    planet: str
    kshetra_bala: float
    uchcha_bala: float
    hadda_bala: float
    drekkana_bala: float
    navamsha_bala: float
    total_score: float
    visheshika_bala: float
    strength_category: str
    hadda_lord: str = ""
    drekkana_lord: str = ""
    navamsha_lord: str = ""


class TajikaYogaSchema(BaseModel):
    yoga_name: str
    category: str
    planets: list[str]
    is_formed: bool
    description: str
    details: dict[str, Any] = {}


class MuddaDashaPeriodSchema(BaseModel):
    planet: str
    start_jd: float
    end_jd: float
    duration_days: float
    start_date: str
    end_date: str
    antardashas: list[MuddaDashaPeriodSchema] = []


class PatyayiniDashaPeriodSchema(BaseModel):
    planet: str
    start_jd: float
    end_jd: float
    duration_days: float
    krishnamsha_deg: float
    start_date: str
    end_date: str


class YearLordSchema(BaseModel):
    candidates: list[str]
    selected: str
    selection_method: str = Field(
        ..., description="'panchavargiya_bala' | 'benefic_aspect' | 'malefic_aspect' | 'fallback_first_candidate'"
    )
    candidate_balas: Optional[dict[str, float]] = None


class SahamSchema(BaseModel):
    name: str
    sidereal_longitude: float
    rashi: str


class MasaPraveshSchema(BaseModel):
    month_number: int
    solar_longitude_target: float
    solar_return_jd: float
    solar_return_date: str
    ascendant: VarshaAscendantSchema
    houses: list[VarshaHouseCuspSchema]
    planets: list[VarshaPlanetPositionSchema]
    panchanga: PanchangaSchema
    muntha_rashi: str
    masa_lord: str


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
    panchavargiya_bala: list[PanchavargiyaBalaSchema] = []
    tajika_yogas: list[TajikaYogaSchema] = []
    mudda_dasha: list[MuddaDashaPeriodSchema] = []
    patyayini_dasha: list[PatyayiniDashaPeriodSchema] = []
