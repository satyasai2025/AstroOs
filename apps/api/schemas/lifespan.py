from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from packages.shared.enums import AyanamsaSystem


class LifespanRequest(BaseModel):
    birth_datetime_utc: datetime = Field(..., description="UTC birth datetime in ISO-8601 format.")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Birth latitude in degrees.")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Birth longitude in degrees.")
    ayanamsa: str = Field(default=AyanamsaSystem.LAHIRI.value, description="Ayanamsa system to use.")
    house_system: str = Field(default="W", description="House system ('W' for Whole Sign).")


class PlanetaryAyurContributionSchema(BaseModel):
    planet: str
    base_years: float
    shatrukshetra_reduction: float
    astangata_reduction: float
    chakrapata_reduction: float
    bharana_enhancement: float
    net_years: float


class MethodLifespanSchema(BaseModel):
    method_name: str
    planetary_contributions: List[PlanetaryAyurContributionSchema]
    lagna_contribution: float
    total_years: float
    category: str


class MarakaVulnerabilitySchema(BaseModel):
    primary_maraka_lords: List[str]
    secondary_maraka_lords: List[str]
    badhaka_lord: str
    badhaka_house: int
    is_saturn_maraka_absorber: bool
    saturn_maraka_reason: str
    d30_afflicted_planets: List[str]
    high_risk_dasha_lords: List[str]
    vulnerability_index: float


class TriLifespanResponse(BaseModel):
    pindayu: MethodLifespanSchema
    amshayu: MethodLifespanSchema
    nisargayu: MethodLifespanSchema
    mean_lifespan_years: float
    consensus_category: str
    maraka_assessment: MarakaVulnerabilitySchema
    shastric_notes: List[str]
