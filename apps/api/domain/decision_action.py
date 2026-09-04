"""
AstroOS — Research Decision & Evidence Action Engine Domain Models (Priority 25)

Defines domain dataclasses for:
  - Research Action Verdict (ACCEPT, HOLD, REJECT, NEEDS_MORE_EVIDENCE)
  - Action Readiness Level (READINESS_LEVEL_1_PRODUCTION_DEPLOYABLE, READINESS_LEVEL_2_REPLICATION_CANDIDATE, READINESS_LEVEL_3_EXPLORATORY_HOLD, READINESS_LEVEL_4_REFUTED_REJECTED)
  - Decision Action Factors & Source Priority Contributions
  - Actionable Research Decision Records with Complete Cryptographic Provenance
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence


class ResearchActionVerdict(str, Enum):
    ACCEPT = "ACCEPT"                              # Publication/Deployment ready, fully replicated and prospectively supported
    HOLD = "HOLD"                                  # Replicated on holdout, but prospective trial or sample size target in progress
    REJECT = "REJECT"                              # Counter-evidentiary, rejected by FDR control, reproducibility drifted, or refuted
    NEEDS_MORE_EVIDENCE = "NEEDS_MORE_EVIDENCE"    # Insufficient observations (N < 100) or high statistical uncertainty


class ResearchReadinessLevel(str, Enum):
    LEVEL_1_PRODUCTION_READY = "LEVEL_1_PRODUCTION_READY"          # All empirical criteria passed with zero drift
    LEVEL_2_REPLICATION_CANDIDATE = "LEVEL_2_REPLICATION_CANDIDATE" # Mined & holdout validated, ready for prospective trials
    LEVEL_3_EXPLORATORY_HOLD = "LEVEL_3_EXPLORATORY_HOLD"          # Preliminary pattern, pending formal pre-registration
    LEVEL_4_REFUTED_REJECTED = "LEVEL_4_REFUTED_REJECTED"          # Disproven or failed reproducibility audit


@dataclass(frozen=True)
class DecisionActionFactor:
    """An individual contributing empirical factor evaluated by the Action Engine."""
    factor_id: str
    factor_name: str
    source_priority: str  # e.g. "P15", "P16", "P19", "P20", "P21", "P22", "P23", "P24"
    measured_metric: str  # e.g. "ROC-AUC: 0.895", "Repro: 100.0%", "Graph Weight: 0.717"
    raw_score: float      # Normalized [0.0, 1.0]
    weight: float         # Contribution weight in decision synthesis
    is_criterion_satisfied: bool
    epistemic_rationale: str


@dataclass(frozen=True)
class ActionPolicyRecommendation:
    """Actionable scientific next step policy based on the decision verdict."""
    recommended_action: str
    experiment_planning_priority: str  # e.g. "HIGH", "MEDIUM", "LOW", "DEPRECATE"
    target_sample_size_expansion: Optional[int]
    longitudinal_tracking_enabled: bool
    suggested_experiment_budget_tier: str  # "TIER_A_PRIORITY", "TIER_B_MONITOR", "TIER_C_ARCHIVED"
    policy_summary: str


@dataclass(frozen=True)
class ActionableResearchDecision:
    """The final actionable scientific decision record synthesizing P19-P24 evidence."""
    decision_id: str
    target_objective: str
    verdict: ResearchActionVerdict
    readiness_level: ResearchReadinessLevel
    synthesized_confidence_score: float  # [0.0, 1.0]
    empirical_readiness_score_percent: float  # [0.0, 100.0]
    decision_factors: tuple[DecisionActionFactor, ...]
    supporting_evidence_points: tuple[str, ...]
    risk_and_attenuation_factors: tuple[str, ...]
    policy_recommendation: ActionPolicyRecommendation
    p11_lineage_snapshot_id: str
    decision_provenance_hash: str
    epistemic_non_causal_statement: str
    decided_at: datetime
