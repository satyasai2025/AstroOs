"""
AstroOS — Adaptive Research & Sequential Experiment Schemas (Priority 28)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PredefinedStratumSchema(BaseModel):
    stratum_id: str
    stratum_name: str
    feature_dimension: str
    inclusion_criteria: str
    target_sample_allocation_pct: float
    observed_sample_count: int


class ImmutableTrialCommitmentSchema(BaseModel):
    commitment_id: str
    target_objective: str
    candidate_hypothesis_id: str
    frozen_rule_name: str
    frozen_formula_expression: str
    frozen_parameter_thresholds: Dict[str, float]
    alpha_spending_method: str
    overall_alpha_budget: float
    overall_beta_budget: float
    planned_maximum_sample_size: int
    permit_outcome_dependent_adaptation: bool
    predefined_strata: List[PredefinedStratumSchema]
    p11_lineage_snapshot_id: str
    commitment_provenance_hash: str
    committed_at: str


class SequentialInterimAnalysisSchema(BaseModel):
    interim_look_number: int
    total_planned_looks: int
    accumulated_sample_size: int
    information_fraction_t: float
    cumulative_alpha_spent: float
    efficacy_boundary_z: float
    futility_boundary_z: float
    observed_interim_z_score: float
    interim_decision: str
    is_information_blind: bool
    reestimated_sample_size: int
    interim_rationale: str
    analyzed_at: str


class AdaptiveExperimentReportResponse(BaseModel):
    adaptive_trial_id: str
    target_objective: str
    trial_phase: str
    commitment: ImmutableTrialCommitmentSchema
    latest_interim_analysis: SequentialInterimAnalysisSchema
    interim_history: List[SequentialInterimAnalysisSchema]
    predefined_strata: List[PredefinedStratumSchema]
    p11_snapshot_id: str
    report_provenance_hash: str
    epistemic_non_causal_statement: str
    generated_at: str


class CreateCommitmentRequest(BaseModel):
    target_objective: str = Field(default="marriage", description="Research target objective")
    hypothesis_id: Optional[str] = Field(default=None, description="Optional candidate hypothesis ID")
    alpha_spending_method: str = Field(default="LAN_DEMETS_OBRIEN_FLEMING", description="Alpha spending function method")
    overall_alpha_budget: float = Field(default=0.05, description="Nominal alpha budget")
    overall_beta_budget: float = Field(default=0.20, description="Nominal beta budget")
    planned_maximum_sample_size: int = Field(default=300, description="Maximum planned sample size")
    permit_outcome_dependent_adaptation: bool = Field(default=False, description="Whether outcome-dependent sample size adaptation is permitted")
    snapshot_id: Optional[str] = Field(default=None, description="Optional P11 snapshot ID")


class EvaluateInterimRequest(BaseModel):
    commitment_id: Optional[str] = Field(default=None, description="Optional pre-existing commitment ID")
    target_objective: str = Field(default="marriage", description="Target objective")
    interim_look_number: int = Field(default=1, description="Interim look index")
    total_planned_looks: int = Field(default=2, description="Total planned interim looks")
    current_sample_size: int = Field(default=150, description="Current accumulated sample size n")
    snapshot_id: Optional[str] = Field(default=None, description="Optional P11 snapshot ID")
