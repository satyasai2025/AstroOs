"""
AstroOS — Research Knowledge & Evidence Intelligence Schemas (Priority 16)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class ContextualConditionRuleItem(BaseModel):
    condition_id: str
    technique_id: str
    condition_expression: str
    description: str
    condition_type: str  # AMPLIFIER or ATTENUATOR
    baseline_hit_rate: float
    conditional_hit_rate: float
    effect_delta_percent: float
    sample_size_n: int
    confidence_score: float


class TechniqueEvidenceItem(BaseModel):
    technique_id: str
    technique_name: str
    target_objective: str
    historical_sample_size_n: int
    empirical_hit_rate: float
    baseline_rate: float
    odds_ratio: float
    p_value: float
    brier_score: float
    roc_auc: float
    confidence_grade: str
    amplifying_conditions: list[ContextualConditionRuleItem] = Field(default_factory=list)
    attenuating_conditions: list[ContextualConditionRuleItem] = Field(default_factory=list)
    classical_provenance: str
    epistemic_summary: str


class CombinationSynergyItem(BaseModel):
    synergy_id: str
    target_objective: str
    technique_a_id: str
    technique_a_name: str
    technique_b_id: str
    technique_b_name: str
    technique_a_hit_rate: float
    technique_b_hit_rate: float
    joint_synergistic_hit_rate: float
    synergy_multiplier: float
    statistical_lift_percent: float
    sample_size_n: int
    p_value: float
    is_synergy_confirmed: bool
    explanation: str


class EvidenceQueryRequest(BaseModel):
    target_objective: str = Field(default="marriage", description="Event objective: 'marriage', 'career', 'health', 'wealth'")
    min_confidence_grade: Optional[str] = Field(default=None, description="Optional minimum grade: GRADE_A_RIGOROUS, GRADE_B_MODERATE, etc.")


class EvidenceIntelligenceReportResponse(BaseModel):
    report_id: str
    target_objective: str
    timestamp: datetime
    total_techniques_evaluated: int
    grade_a_count: int
    grade_b_count: int
    grade_c_count: int
    grade_d_count: int
    ranked_techniques: list[TechniqueEvidenceItem]
    top_synergies: list[CombinationSynergyItem]
    key_condition_rules: list[ContextualConditionRuleItem]
    epistemic_synthesis: str
    methodological_provenance: str
