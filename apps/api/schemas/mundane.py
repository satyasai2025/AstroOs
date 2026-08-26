"""
AstroOS — Mundane Astrology (Medini Jyotisha) Schemas
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class IngressMomentSchema(BaseModel):
    ingress_type: str
    timestamp_utc: datetime
    sun_longitude: float
    moon_longitude: float
    weekday: str
    weekday_lord: str


class IngressChartRequest(BaseModel):
    country_name: str = Field(default="India")
    capital_city: str = Field(default="New Delhi")
    latitude: float = Field(default=28.6139, ge=-90.0, le=90.0)
    longitude: float = Field(default=77.2090, ge=-180.0, le=180.0)
    year: int = Field(default=2026, ge=1900, le=2100)
    ayanamsa: str = Field(default="lahiri")


class IngressChartResponse(BaseModel):
    ingress_moment: IngressMomentSchema
    country_name: str
    capital_city: str
    ascendant_rashi: str
    ascendant_lord: str
    tenth_house_rashi: str
    tenth_house_lord: str


class CabinetMinisterSchema(BaseModel):
    portfolio: str
    planet: str
    basis_ingress: str
    is_benefic: bool
    impact_summary: str


class PlanetaryCabinetResponse(BaseModel):
    year: int
    ministers: list[CabinetMinisterSchema]
    overall_balance_score: float
    governance_climate: str
    classical_summary: str


class MundaneEclipseSchema(BaseModel):
    eclipse_type: str
    peak_utc: datetime
    eclipsed_rashi: str
    eclipsed_nakshatra: str
    node_involved: str
    duration_hours: float
    impact_duration_months: float
    afflicted_directions: list[str]
    impact_summary: str


class KurmaSectorStatusSchema(BaseModel):
    direction: str
    nakshatras: list[str]
    traditional_regions: list[str]
    transiting_malefics: list[str]
    transiting_benefics: list[str]
    is_afflicted: bool
    severity: str
    risk_summary: str


class KurmaChakraResponse(BaseModel):
    evaluated_at: datetime
    sectors: list[KurmaSectorStatusSchema]
    highest_risk_directions: list[str]
    summary: str


class MundaneBhavaEvaluationSchema(BaseModel):
    house_number: int
    signification: str
    rashi: str
    lord: str
    occupants: list[str]
    strength_score: float
    outlook: str


class NationalForecastResponse(BaseModel):
    country_name: str
    capital_city: str
    year: int
    planetary_cabinet: PlanetaryCabinetResponse
    active_eclipses: list[MundaneEclipseSchema]
    kurma_state: KurmaChakraResponse
    bhava_evaluations: list[MundaneBhavaEvaluationSchema]
    economic_index: float
    defense_security_index: float
    political_stability_index: float
    public_health_index: float
    executive_summary: str
