"""
AstroOS — Research Knowledge & Evidence Intelligence Domain Models (Priority 16)

Defines domain dataclasses for:
  - Epistemic Evidence Grades (Grade A, B, C, D)
  - Technique Evidence Records (hit rates, odds ratios, p-values, condition attribution)
  - Multi-Technique Pairwise Combination Synergies & Lift Multipliers
  - Contextual Condition Rules (Amplifiers vs Attenuators)
  - Unified Evidence Intelligence Reports & Epistemic Synthesis
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class EvidenceGrade(str, Enum):
    GRADE_A_RIGOROUS = "GRADE_A_RIGOROUS"          # N >= 200, p < 0.001, ROC-AUC >= 0.85, Brier < 0.05
    GRADE_B_MODERATE = "GRADE_B_MODERATE"          # N >= 50, p < 0.05, lift > 1.25x
    GRADE_C_CLASSICAL_HEURISTIC = "GRADE_C_CLASSICAL_HEURISTIC"  # Classical consensus, small N (<50)
    GRADE_D_INCONCLUSIVE = "GRADE_D_INCONCLUSIVE"  # Insufficient data or counter-evidentiary (p >= 0.05)


@dataclass(frozen=True)
class ContextualConditionRule:
    """A specific astrological context that significantly amplifies or attenuates technique effectiveness."""
    condition_id: str
    technique_id: str
    condition_expression: str
    description: str
    condition_type: str  # "AMPLIFIER" or "ATTENUATOR"
    baseline_hit_rate: float
    conditional_hit_rate: float
    effect_delta_percent: float  # e.g. +22.5% or -18.0%
    sample_size_n: int
    confidence_score: float  # 0.0 to 1.0


@dataclass(frozen=True)
class TechniqueEvidenceRecord:
    """Empirical performance and epistemological evidence record for an astrological technique."""
    technique_id: str
    technique_name: str
    target_objective: str  # "marriage", "career", "health", "wealth"
    historical_sample_size_n: int
    empirical_hit_rate: float
    baseline_rate: float
    odds_ratio: float
    p_value: float
    brier_score: float
    roc_auc: float
    confidence_grade: EvidenceGrade
    amplifying_conditions: tuple[ContextualConditionRule, ...] = field(default_factory=tuple)
    attenuating_conditions: tuple[ContextualConditionRule, ...] = field(default_factory=tuple)
    classical_provenance: str = ""
    epistemic_summary: str = ""


@dataclass(frozen=True)
class CombinationSynergyRecord:
    """Pairwise or multi-technique synergistic interaction matrix."""
    synergy_id: str
    target_objective: str
    technique_a_id: str
    technique_a_name: str
    technique_b_id: str
    technique_b_name: str
    technique_a_hit_rate: float
    technique_b_hit_rate: float
    joint_synergistic_hit_rate: float
    synergy_multiplier: float  # Joint / Expected Independent (e.g. 1.45x)
    statistical_lift_percent: float  # (Joint - max(A, B)) / max(A, B) * 100
    sample_size_n: int
    p_value: float
    is_synergy_confirmed: bool  # True if synergistic multiplier > 1.15 and p < 0.05
    explanation: str = ""


@dataclass(frozen=True)
class EvidenceIntelligenceReport:
    """Comprehensive evidence layer intelligence report for a given research objective."""
    report_id: str
    target_objective: str
    timestamp: datetime
    total_techniques_evaluated: int
    grade_a_count: int
    grade_b_count: int
    grade_c_count: int
    grade_d_count: int
    ranked_techniques: tuple[TechniqueEvidenceRecord, ...]
    top_synergies: tuple[CombinationSynergyRecord, ...]
    key_condition_rules: tuple[ContextualConditionRule, ...]
    epistemic_synthesis: str
    methodological_provenance: str
