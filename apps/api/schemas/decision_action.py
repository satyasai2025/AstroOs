"""
AstroOS — Research Decision & Evidence Action Engine Schemas (Priority 25)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DecisionActionFactorSchema(BaseModel):
    factor_id: str
    factor_name: str
    source_priority: str
    measured_metric: str
    raw_score: float
    weight: float
    is_criterion_satisfied: bool
    epistemic_rationale: str


class ActionPolicyRecommendationSchema(BaseModel):
    recommended_action: str
    experiment_planning_priority: str
    target_sample_size_expansion: Optional[int] = None
    longitudinal_tracking_enabled: bool
    suggested_experiment_budget_tier: str
    policy_summary: str


class ActionableResearchDecisionResponse(BaseModel):
    decision_id: str
    target_objective: str
    verdict: str
    readiness_level: str
    synthesized_confidence_score: float
    empirical_readiness_score_percent: float
    decision_factors: List[DecisionActionFactorSchema]
    supporting_evidence_points: List[str]
    risk_and_attenuation_factors: List[str]
    policy_recommendation: ActionPolicyRecommendationSchema
    p11_lineage_snapshot_id: str
    decision_provenance_hash: str
    epistemic_non_causal_statement: str
    decided_at: str


class DecisionEvaluateRequest(BaseModel):
    target_objective: str = Field(default="marriage", description="Research target objective, e.g. 'marriage', 'career'")
    snapshot_id: Optional[str] = Field(default=None, description="Optional P11 snapshot to evaluate against")
