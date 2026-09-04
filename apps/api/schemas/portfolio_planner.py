"""
AstroOS — Research Portfolio & Experiment Planner Schemas (Priority 26)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CandidateHypothesisRankingSchema(BaseModel):
    hypothesis_id: str
    rule_name: str
    target_objective: str
    formula_expression: str
    discovery_lift: float
    fdr_q_value: float
    reproducibility_score_percent: float
    knowledge_graph_centrality: float
    sample_deficit: int
    evidence_priority_score: float
    priority_rank: int
    assigned_tier: str
    required_sample_size_target: int
    statistical_power_estimate: float
    epistemic_rationale: str


class ExperimentBudgetTierAllocationSchema(BaseModel):
    tier: str
    allocated_chart_evaluations: int
    allocation_percentage: float
    target_studies_count: int
    recommended_worker_concurrency: int
    estimated_throughput_charts_per_sec: float


class ResearchPortfolioBudgetPlanSchema(BaseModel):
    total_compute_charts_budget: int
    tier_allocations: List[ExperimentBudgetTierAllocationSchema]
    max_parallel_workers: int
    ephemeris_cache_target_hit_rate_pct: float
    budget_utilization_percent: float


class PlannedExperimentPackageResponse(BaseModel):
    plan_id: str
    target_objective: str
    total_hypotheses_ranked: int
    ranked_candidates: List[CandidateHypothesisRankingSchema]
    budget_plan: ResearchPortfolioBudgetPlanSchema
    p11_lineage_snapshot_id: str
    plan_provenance_hash: str
    epistemic_non_causal_statement: str
    planned_at: str


class PortfolioPlanRequest(BaseModel):
    target_objective: str = Field(default="marriage", description="Research target objective, e.g. 'marriage', 'career'")
    total_compute_charts_budget: int = Field(default=5000, description="Total chart evaluation compute capacity")
    max_parallel_workers: int = Field(default=4, description="Max parallel worker concurrency")
    snapshot_id: Optional[str] = Field(default=None, description="Optional P11 snapshot to anchor against")
