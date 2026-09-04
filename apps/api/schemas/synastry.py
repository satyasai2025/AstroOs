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


# ── 1. Kuja Dosha Schemas ──────────────────────────────────────────────────────


class KujaDoshaProfileSchema(BaseModel):
    chart_name: str
    has_dosha: bool
    severity: str
    house_from_lagna: Optional[int]
    house_from_moon: Optional[int]
    house_from_venus: Optional[int]
    raw_dosha_points: float
    effective_dosha_score: float
    pariharas_applied: list[str]
    is_cancelled: bool
    explanation: str


class KujaDoshaComparisonSchema(BaseModel):
    partner_a: KujaDoshaProfileSchema
    partner_b: KujaDoshaProfileSchema
    is_balanced: bool
    dosha_difference: float
    compatibility_verdict: str
    classical_mitigation_notes: str


# ── 2. Dasa Kuta Schemas ───────────────────────────────────────────────────────


class DasaKutaEvaluateRequest(BaseModel):
    girl_rashi: str = Field(description="Girl Moon Rashi (e.g. 'aries')")
    girl_nakshatra: str = Field(description="Girl Moon Nakshatra (e.g. 'ashwini')")
    boy_rashi: str = Field(description="Boy Moon Rashi (e.g. 'leo')")
    boy_nakshatra: str = Field(description="Boy Moon Nakshatra (e.g. 'magha')")


class DasaKutaItemSchema(BaseModel):
    name: str
    label: str
    is_compatible: bool
    obtained_score: float
    max_score: float
    partner_a_value: str
    partner_b_value: str
    description: str
    classical_source: str


class DasaKutaResponse(BaseModel):
    items: list[DasaKutaItemSchema]
    total_score: float
    max_total_score: float
    compatibility_percentage: float
    is_rajju_compatible: bool
    is_vedha_compatible: bool
    is_mahendra_present: bool
    is_stree_deergha_present: bool
    verdict: str
    summary: str


# ── 3. Upapada & Navamsha Schemas ──────────────────────────────────────────────


class UpapadaCompatibilitySchema(BaseModel):
    ul_rashi_a: str
    ul_rashi_b: str
    lagna_rashi_a: str
    lagna_rashi_b: str
    moon_rashi_a: str
    moon_rashi_b: str
    alignment_type: str
    is_harmonious: bool
    second_from_ul_status_a: str
    second_from_ul_status_b: str
    jaimini_compatibility_score: float
    explanation: str


class NavamshaSynastrySchema(BaseModel):
    d9_lagna_a: str
    d9_lagna_b: str
    lagna_relationship: str
    d9_moon_a: str
    d9_moon_b: str
    d9_venus_a: str
    d9_venus_b: str
    mutual_d9_trines: list[str]
    navamsha_harmony_score: float
    verdict: str
    explanation: str


# ── 4. Composite Chart Schemas ────────────────────────────────────────────────


class CompositePlanetSchema(BaseModel):
    planet: str
    sidereal_longitude: float
    rashi: str
    rashi_degree: float
    house_number: int


class CompositeChartResponse(BaseModel):
    chart_a_name: str
    chart_b_name: str
    composite_ascendant: CompositePlanetSchema
    composite_planets: list[CompositePlanetSchema]
    relationship_purpose_summary: str


# ── 5. Full Synastry & Compatibility Bundle ───────────────────────────────────


class FullCompatibilityRequest(BaseModel):
    chart_a_birth: BirthInput
    chart_b_birth: BirthInput
    relationship_type: str = Field(default="marriage")


class FullCompatibilityResponse(BaseModel):
    chart_a_name: str
    chart_b_name: str
    ashta_kuta: AshtaKutaResponse
    dasa_kuta: DasaKutaResponse
    kuja_dosha: KujaDoshaComparisonSchema
    upapada_compatibility: UpapadaCompatibilitySchema
    navamsha_synastry: NavamshaSynastrySchema
    composite_chart: CompositeChartResponse
    overall_compatibility_index: float
    overall_verdict: str
    executive_summary: str
