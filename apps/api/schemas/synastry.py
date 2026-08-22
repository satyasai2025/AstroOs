"""
AstroOS — Inter-Chart Synastry, Ashta-Kuta & Confluence Schemas (Priority 13)
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class BirthInput(BaseModel):
    name: str = Field(default="Partner", description="Display name of the subject")
    datetime_utc: datetime = Field(description="ISO 8601 UTC birth datetime")
    latitude: float = Field(default=13.0827, ge=-90.0, le=90.0)
    longitude: float = Field(default=80.2707, ge=-180.0, le=180.0)
    ayanamsa: str = Field(default="lahiri")


class AshtaKutaEvaluateRequest(BaseModel):
    partner_a_rashi: str = Field(description="Partner A Moon Rashi (e.g., 'aries')")
    partner_a_nakshatra: str = Field(description="Partner A Moon Nakshatra (e.g., 'ashwini')")
    partner_a_pada: int = Field(default=1, ge=1, le=4)
    partner_b_rashi: str = Field(description="Partner B Moon Rashi (e.g., 'leo')")
    partner_b_nakshatra: str = Field(description="Partner B Moon Nakshatra (e.g., 'magha')")
    partner_b_pada: int = Field(default=1, ge=1, le=4)


class KutaEvaluationItem(BaseModel):
    kuta: str
    label: str
    obtained_points: float
    max_points: float
    partner_a_attribute: str
    partner_b_attribute: str
    raw_relationship: str
    is_mitigated: bool
    cancellation_reason: Optional[str]
    description: str
    classical_source: str


class DoshaPariharaItem(BaseModel):
    dosha_name: str
    is_present: bool
    is_cancelled: bool
    parihara_rule: Optional[str]
    classical_reference: str
    explanation: str


class AshtaKutaResponse(BaseModel):
    evaluations: list[KutaEvaluationItem]
    total_guna_obtained: float
    max_guna_possible: float
    guna_percentage: float
    dosha_pariharas: list[DoshaPariharaItem]
    summary: str


class SynastryMatrixEvaluateRequest(BaseModel):
    chart_a_birth: BirthInput
    chart_b_birth: BirthInput
    target_start_date: Optional[date] = Field(default=None)
    target_end_date: Optional[date] = Field(default=None)
    objective: str = Field(default="marriage")


class InterChartAspectItem(BaseModel):
    planet_a: str
    planet_b: str
    longitude_a: float
    longitude_b: float
    angle_degrees: float
    aspect_type: str
    orb_degrees: float
    is_harmonious: bool
    interpretation: str


class CrossHouseOverlayItem(BaseModel):
    planet_a: str
    chart_a_house: int
    chart_b_house_occupied: int
    rashi_in_chart_b: str
    functional_impact: str


class JointConfluenceWindowItem(BaseModel):
    start_date: date
    end_date: date
    chart_a_density_score: float
    chart_b_density_score: float
    joint_confluence_density: float
    chart_a_active_systems: list[str]
    chart_b_active_systems: list[str]
    objective: str
    synthesis_notes: str


class SynastryMatrixResponse(BaseModel):
    chart_a_name: str
    chart_b_name: str
    evaluated_at: datetime
    ashta_kuta_evaluations: list[KutaEvaluationItem]
    total_guna_obtained: float
    max_guna_possible: float
    guna_percentage: float
    dosha_pariharas: list[DoshaPariharaItem]
    inter_chart_aspects: list[InterChartAspectItem]
    cross_house_overlays: list[CrossHouseOverlayItem]
    joint_confluence_windows: list[JointConfluenceWindowItem]
    structural_summary: str
    timing_summary: str
    provenance_notes: str
