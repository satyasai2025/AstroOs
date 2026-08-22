"""
AstroOS — Research Decision & Evidence Synthesis Domain Models (Priority 23)

Defines domain dataclasses for:
  - Epistemic Rule Classification (CLASSICAL_CANONICAL_RULE, DISCOVERED_HYPOTHESIS, EMPIRICALLY_SUPPORTED_PROSPECTIVE_RULE)
  - Evidence Confidence Tiers (TIER_1_PUBLICATION_GRADE, TIER_2_EMPIRICALLY_PROMISING, TIER_3_EXPLORATORY, TIER_4_REFUTED)
  - Evidence Conflicts & Epistemic Arbitration
  - Defensible Research Decision Conclusions with End-to-End P1 -> P22 Lineage
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple


class EpistemicRuleType(str, Enum):
    CLASSICAL_CANONICAL_RULE = "CLASSICAL_CANONICAL_RULE"
    DISCOVERED_HYPOTHESIS = "DISCOVERED_HYPOTHESIS"
    EMPIRICALLY_SUPPORTED_PROSPECTIVE_RULE = "EMPIRICALLY_SUPPORTED_PROSPECTIVE_RULE"


class EvidenceConfidenceTier(str, Enum):
    TIER_1_PUBLICATION_GRADE = "TIER_1_PUBLICATION_GRADE"     # Replicated Holdout + Prospective Supported + High Lift + Clean Data
    TIER_2_EMPIRICALLY_PROMISING = "TIER_2_EMPIRICALLY_PROMISING" # Replicated Holdout + Pending Prospective
    TIER_3_EXPLORATORY_DISCOVERY = "TIER_3_EXPLORATORY_DISCOVERY" # Candidate Discovery Only (Unreplicated)
    TIER_4_REFUTED_OR_INCONCLUSIVE = "TIER_4_REFUTED_OR_INCONCLUSIVE" # Failed Holdout or Prospective Refuted


@dataclass(frozen=True)
class EvidenceConflictItem:
    """Detailed diagnosis of contradictory evidence between techniques or classical vs empirical models."""
    conflict_id: str
    technique_a: str
    technique_b: str
    conflict_type: str  # e.g., "CLASSICAL_PROMISE_VS_NEGATIVE_DASHA", "HIGH_LIFT_VS_HIGH_PSI_DRIFT"
    conflict_description: str
    resolution_recommendation: str
    epistemic_arbitration: str


@dataclass(frozen=True)
class TechniqueStrengthEvaluation:
    """Individual astrological technique empirical strength profile."""
    technique_name: str
    epistemic_type: EpistemicRuleType
    evidence_grade: str  # e.g., "Grade A", "Grade B", "Grade C"
    holdout_replicated: bool
    prospective_supported: bool
    empirical_lift: float
    brier_score: float
    usable_for_prediction: bool
    arbitration_note: str


@dataclass(frozen=True)
class ResearchDecisionConclusion:
    """Final, defensible research decision conclusion synthesizing P1 through P22 evidence layers."""
    conclusion_id: str
    target_objective: str
    synthesized_confidence_score: float
    confidence_tier: EvidenceConfidenceTier
    strongest_techniques: List[TechniqueStrengthEvaluation]
    replicated_hypotheses_count: int
    prospective_lifecycle_summary: str
    conflicts_detected: List[EvidenceConflictItem]
    recommended_prediction_factors: List[str]
    counterfactual_stability_rating: str
    p1_to_p22_lineage_trace: Dict[str, str]
    defensible_scientific_summary: str
    synthesized_at: datetime
