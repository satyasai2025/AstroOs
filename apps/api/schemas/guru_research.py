"""
AstroOS — Guru Research Schemas

Pydantic schemas for Guru Research Layer API endpoints.
"""

from __future__ import annotations

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class PlanetPositionInput(BaseModel):
    planet: str = Field(..., description="Name of the planet (e.g., 'sun', 'mars')")
    rashi: str = Field(..., description="Rashi name (e.g., 'aries', 'taurus')")
    degree_in_rashi: float = Field(..., ge=0.0, le=30.0, description="Degree within rashi (0.0 to 30.0)")


class ChartEvaluationRequest(BaseModel):
    positions: List[PlanetPositionInput] = Field(..., description="Planetary positions to evaluate")
    custom_rules: Optional[Dict[str, Any]] = Field(None, description="Optional custom rules override")


class PlanetEvaluationResponse(BaseModel):
    planet: str
    rashi: str
    degree_in_rashi: float
    classical_dignity: Optional[str]
    guru_zone_name: str
    guru_zone_type: str
    guru_zone_lord: str
    guru_zone_range: str
    is_ruler_match: bool
    is_dignity_agreement: bool
    notes: str


class GuruChartEvaluationResponse(BaseModel):
    evaluations: List[PlanetEvaluationResponse]
    agreements_count: int
    deviations_count: int
    summary_insights: List[str]


class GuruRuleResponse(BaseModel):
    start_deg: float
    end_deg: float
    zone_type: str
    ruling_planet: str
    description: str
    strength_weight: float


class GuruRulesRegistryResponse(BaseModel):
    partitions: Dict[str, List[GuruRuleResponse]]
