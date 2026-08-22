"""
AstroOS — Research Decision & Evidence Synthesis Schemas (Priority 23)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SynthesizeDecisionRequest(BaseModel):
    target_objective: str = Field(default="marriage", description="Target research outcome")
    include_lineage: bool = Field(default=True, description="Whether to include full P1-P22 lineage trace")


class TechniqueStrengthResponse(BaseModel):
    technique_name: str
    epistemic_type: str
    evidence_grade: str
    holdout_replicated: bool
    prospective_supported: bool
    empirical_lift: float
    brier_score: float
    usable_for_prediction: bool
    arbitration_note: str


class EvidenceConflictResponse(BaseModel):
    conflict_id: str
    technique_a: str
    technique_b: str
    conflict_type: str
    conflict_description: str
    resolution_recommendation: str
    epistemic_arbitration: str


class ResearchDecisionConclusionResponse(BaseModel):
    conclusion_id: str
    target_objective: str
    synthesized_confidence_score: float
    confidence_tier: str
    strongest_techniques: List[TechniqueStrengthResponse]
    replicated_hypotheses_count: int
    prospective_lifecycle_summary: str
    conflicts_detected: List[EvidenceConflictResponse]
    recommended_prediction_factors: List[str]
    counterfactual_stability_rating: str
    p1_to_p22_lineage_trace: Dict[str, str]
    defensible_scientific_summary: str
    synthesized_at: datetime
