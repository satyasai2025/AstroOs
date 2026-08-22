"""
AstroOS — Research & Prediction Explainability Schemas (Priority 17)
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class AtomicEvidenceFactorItem(BaseModel):
    factor_id: str
    name: str
    layer: str
    raw_value: float
    calibrated_weight: float
    contribution_percent: float
    attribution_type: str  # ASSOCIATIONAL_ATTRIBUTION
    direction: str
    classical_citation: str
    citation_verified: bool
    epistemic_grade: str
    description: str


class CounterfactualScenarioItem(BaseModel):
    scenario_id: str
    perturbed_parameter: str
    parameter_value: str
    baseline_score: float
    simulated_score: float
    score_delta_percent: float
    divergence_reason: str
    recalculation_engine_used: str


class ExplainPredictionRequest(BaseModel):
    target_objective: str = Field(default="marriage", description="Event objective: 'marriage', 'career', 'health', 'wealth'")
    event_window_start: Optional[date] = Field(default=None, description="Start date of the prediction window")
    event_window_end: Optional[date] = Field(default=None, description="End date of the prediction window")


class PredictionExplanationResponse(BaseModel):
    explanation_id: str
    target_objective: str
    event_window_start: date
    event_window_end: date
    composite_confidence_score: float
    plain_summary: str
    classical_justification: str
    empirical_synthesis: str
    provenance_lineage: list[str]
    atomic_factors: list[AtomicEvidenceFactorItem]
    counterfactuals: list[CounterfactualScenarioItem]
    generated_at: datetime


class CounterfactualSimulationRequest(BaseModel):
    target_objective: str = Field(default="marriage")
    perturbed_parameter: str = Field(..., description="Parameter to perturb (e.g. 'birth_time_shift_minutes', 'dasha_lord_combustion')")
    parameter_value: str = Field(..., description="New value for parameter (e.g. '+2 min', 'TRUE')")
