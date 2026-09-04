"""
AstroOS — Research Portfolio & Experiment Planner Domain Models (Priority 26)

Defines domain dataclasses for:
  - Experiment Priority Tiers (TIER_A_PRIMARY_TRIAL, TIER_B_REPLICATION_STUDY, TIER_C_EXPLORATORY_SCAN)
  - Candidate Hypothesis Prioritization & EvidencePriorityScore
  - Dynamic Sample & Compute Budget Allocation constrained by P25 verdicts and P21 datasets
  - Pre-Registration Experiment Execution Packages with Complete Lineage
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ExperimentPriorityTier(str, Enum):
    TIER_A_PRIMARY_TRIAL = "TIER_A_PRIMARY_TRIAL"           # Top candidate for blind prospective trials
    TIER_B_REPLICATION_STUDY = "TIER_B_REPLICATION_STUDY"   # Independent cohort replication candidate
    TIER_C_EXPLORATORY_SCAN = "TIER_C_EXPLORATORY_SCAN"     # Preliminary exploratory combinatorial scan


@dataclass(frozen=True)
class CandidateHypothesisRanking:
    """An individual candidate hypothesis ranked by deterministic EvidencePriorityScore."""
    hypothesis_id: str
    rule_name: str
    target_objective: str
    formula_expression: str
    discovery_lift: float
    fdr_q_value: float
    reproducibility_score_percent: float
    knowledge_graph_centrality: float
    sample_deficit: int
    evidence_priority_score: float  # [0.0, 100.0] - deterministic multi-factor prioritization metric
    priority_rank: int
    assigned_tier: ExperimentPriorityTier
    required_sample_size_target: int
    statistical_power_estimate: float  # e.g. 0.85
    epistemic_rationale: str


@dataclass(frozen=True)
class ExperimentBudgetTierAllocation:
    """Compute and sample budget allocated dynamically to a specific experiment tier."""
    tier: ExperimentPriorityTier
    allocated_chart_evaluations: int
    allocation_percentage: float  # Dynamically derived from candidate requirements
    target_studies_count: int
    recommended_worker_concurrency: int
    estimated_throughput_charts_per_sec: float


@dataclass(frozen=True)
class ResearchPortfolioBudgetPlan:
    """Complete portfolio compute and sample budget distribution constrained dynamically."""
    total_compute_charts_budget: int
    tier_allocations: Tuple[ExperimentBudgetTierAllocation, ...]
    max_parallel_workers: int
    ephemeris_cache_target_hit_rate_pct: float
    budget_utilization_percent: float


@dataclass(frozen=True)
class PlannedExperimentPackage:
    """The authoritative pre-registration execution plan for the active research portfolio."""
    plan_id: str
    target_objective: str
    total_hypotheses_ranked: int
    ranked_candidates: Tuple[CandidateHypothesisRanking, ...]
    budget_plan: ResearchPortfolioBudgetPlan
    p11_lineage_snapshot_id: str
    plan_provenance_hash: str
    epistemic_non_causal_statement: str
    planned_at: datetime
