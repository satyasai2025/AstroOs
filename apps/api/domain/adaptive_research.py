"""
AstroOS — Adaptive Research & Sequential Experiment Engine Domain Models (Priority 28)

Defines domain dataclasses for:
  - Configurable Alpha Spending Function Methods (LAN_DEMETS_OBRIEN_FLEMING, LAN_DEMETS_POCOCK, HWANG_SHI_DECANI)
  - Immutable Pre-Trial Commitments (Anti-HARKing / Rule-Freezing / Pre-trial Strata Specifications)
  - Predefined Adaptive Cohort Stratification (Frozen prior to outcome inspection)
  - Sequential Interim Analysis & Stopping Boundaries (Efficacy Stop, Futility Stop, Continue)
  - Information-Blind Sample Size Re-estimation
  - Complete Adaptive Research Reports with P11 Snapshot DAG Lineage
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class AlphaSpendingMethod(str, Enum):
    LAN_DEMETS_OBRIEN_FLEMING = "LAN_DEMETS_OBRIEN_FLEMING" # O'Brien-Fleming type alpha spending: alpha*(t) = 2 - 2*Phi(z_alpha/2 / sqrt(t))
    LAN_DEMETS_POCOCK = "LAN_DEMETS_POCOCK"                 # Pocock type alpha spending: alpha*(t) = alpha * ln(1 + (e-1)*t)
    HWANG_SHI_DECANI = "HWANG_SHI_DECANI"                   # Gamma spending function


class AdaptiveTrialPhase(str, Enum):
    COMMITMENT_FROZEN = "COMMITMENT_FROZEN"
    PREDEFINED_COHORT_SELECTION = "PREDEFINED_COHORT_SELECTION"
    INTERIM_SEQUENTIAL_ANALYSIS = "INTERIM_SEQUENTIAL_ANALYSIS"
    EARLY_STOP_EFFICACY = "EARLY_STOP_EFFICACY"
    EARLY_STOP_FUTILITY = "EARLY_STOP_FUTILITY"
    TRIAL_COMPLETED = "TRIAL_COMPLETED"


class InterimDecisionVerdict(str, Enum):
    CONTINUE_TRIAL = "CONTINUE_TRIAL"
    EARLY_STOP_EFFICACY = "EARLY_STOP_EFFICACY"
    EARLY_STOP_FUTILITY = "EARLY_STOP_FUTILITY"


@dataclass(frozen=True)
class PredefinedStratumDefinition:
    """A stratum specification defined and frozen prior to trial cohort ingestion."""
    stratum_id: str
    stratum_name: str
    feature_dimension: str
    inclusion_criteria: str
    target_sample_allocation_pct: float
    observed_sample_count: int


@dataclass(frozen=True)
class ImmutableTrialCommitment:
    """
    Cryptographic pre-trial commitment manifest freezing rule definition, parameter space,
    spending function, sample size policy, and strata prior to outcome inspection.
    """
    commitment_id: str
    target_objective: str
    candidate_hypothesis_id: str
    frozen_rule_name: str
    frozen_formula_expression: str
    frozen_parameter_thresholds: Dict[str, float]
    alpha_spending_method: AlphaSpendingMethod
    overall_alpha_budget: float                    # Nominal alpha, e.g. 0.05
    overall_beta_budget: float                     # Nominal beta (1 - power), e.g. 0.20
    planned_maximum_sample_size: int
    permit_outcome_dependent_adaptation: bool      # False = Blinded sample size re-estimation only
    predefined_strata: Tuple[PredefinedStratumDefinition, ...]
    p11_lineage_snapshot_id: str
    commitment_provenance_hash: str
    committed_at: datetime


@dataclass(frozen=True)
class SequentialInterimAnalysis:
    """Interim analysis at information fraction t with alpha spending boundaries."""
    interim_look_number: int                       # Look k (e.g. 1, 2, 3)
    total_planned_looks: int
    accumulated_sample_size: int
    information_fraction_t: float                  # t = n / N_max (0 < t <= 1.0)
    cumulative_alpha_spent: float
    efficacy_boundary_z: float                     # Upper stopping boundary z_alpha(t)
    futility_boundary_z: float                     # Lower stopping boundary z_beta(t)
    observed_interim_z_score: float
    interim_decision: InterimDecisionVerdict
    is_information_blind: bool
    reestimated_sample_size: int
    interim_rationale: str
    analyzed_at: datetime


@dataclass(frozen=True)
class AdaptiveExperimentReport:
    """Authoritative scientific report of the adaptive trial cycle."""
    adaptive_trial_id: str
    target_objective: str
    trial_phase: AdaptiveTrialPhase
    commitment: ImmutableTrialCommitment
    latest_interim_analysis: SequentialInterimAnalysis
    interim_history: Tuple[SequentialInterimAnalysis, ...]
    predefined_strata: Tuple[PredefinedStratumDefinition, ...]
    p11_snapshot_id: str
    report_provenance_hash: str
    epistemic_non_causal_statement: str
    generated_at: datetime
