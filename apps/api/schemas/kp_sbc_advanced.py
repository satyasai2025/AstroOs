"""
AstroOS — Advanced KP & SBC Analysis Schemas (Module 19, Phase 4)

Pydantic models for:
  POST /api/v1/kp/cuspal-decision-tree
  POST /api/v1/sbc/sangya-ray-matrix
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


# ── KP Schemas ────────────────────────────────────────────────────────────────

class KPTierSignificatorsSchema(BaseModel):
    house_number: int
    tier_a_planets: list[str] = Field(description="Planets in star of occupant (Tier A - Strongest)")
    tier_b_planets: list[str] = Field(description="Planets occupying house (Tier B)")
    tier_c_planets: list[str] = Field(description="Planets in star of house sign lord (Tier C)")
    tier_d_planets: list[str] = Field(description="House sign lord (Tier D)")


class KPCuspalSubLordDecisionNodeSchema(BaseModel):
    house_number: int
    cusp_degree: float
    cusp_rashi: str
    sign_lord: str
    star_lord: str
    sub_lord: str
    sub_sub_lord: str
    sub_lord_star_lord: str
    primary_houses_signified: list[int]
    supporting_houses_signified: list[int]
    negating_houses_signified: list[int]
    is_veto_active: bool
    verdict: str
    verdict_explanation: str
    audit_chain: list[str]


class KPEventDecisionTreeResultSchema(BaseModel):
    event_domain: str
    primary_cusp: int
    supporting_cusps: list[int]
    negating_cusps: list[int]
    cusp_node: KPCuspalSubLordDecisionNodeSchema
    supporting_significators: list[str]
    ruling_planets_agreement: list[str]
    fructification_verdict: str
    summary_verdict: str
    technical_calculation_steps: list[str]


class KPCuspalDecisionTreeRequest(BaseModel):
    chart: dict[str, Any]
    house_numbers: Optional[list[int]] = None
    event_domain: Optional[str] = None  # "Career", "Marriage", "Finance", "Health", "All"


class KPCuspalDecisionTreeResponse(BaseModel):
    four_tier_significator_matrix: list[KPTierSignificatorsSchema]
    cuspal_decision_nodes: list[KPCuspalSubLordDecisionNodeSchema]
    event_decision_trees: list[KPEventDecisionTreeResultSchema]
    total_cusps_evaluated: int


# ── SBC Schemas ───────────────────────────────────────────────────────────────

class SBCGridCoordinateSchema(BaseModel):
    row: int
    col: int
    cell_id: int
    element_type: str
    element_name: str
    element_value: str


class SBCRayCollisionSchema(BaseModel):
    transit_planet: str
    is_retrograde: bool
    speed_deg_day: float
    ray_direction: str
    source_cell: SBCGridCoordinateSchema
    target_cell: SBCGridCoordinateSchema
    target_sangya: Optional[str] = None
    nature: str
    raw_impact_score: float
    ray_path_coordinates: list[list[int]]


class SangyaVedhaStatusSchema(BaseModel):
    sangya_key: str
    sangya_name: str
    domain: str
    natal_nakshatra: str
    natal_nakshatra_number: int
    grid_coord: SBCGridCoordinateSchema
    benefic_hits: list[SBCRayCollisionSchema]
    malefic_hits: list[SBCRayCollisionSchema]
    net_score: float
    is_obstructed: bool
    verdict: str
    audit_trace: list[str]


class SBCSangyaRayMatrixRequest(BaseModel):
    natal_chart: dict[str, Any]
    transit_planets: Optional[list[dict[str, Any]]] = None
    transit_datetime_iso: Optional[str] = None


class SBCSangyaRayMatrixResponse(BaseModel):
    natal_moon_nakshatra: str
    transit_datetime_iso: str
    sangya_statuses: list[SangyaVedhaStatusSchema]
    all_ray_collisions: list[SBCRayCollisionSchema]
    overall_sbc_confluence_score: float
    kp_cross_link_summary: str
    audit_trail: list[str]
