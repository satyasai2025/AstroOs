"""
AstroOS — Research Portfolio & Experiment Planner Router (Priority 26)

Endpoints for generating research experiment portfolio plans, ranking candidate hypotheses
via EvidencePriorityScore, and optimizing scientific compute budget distributions.
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from apps.api.dependencies import require_authenticated
from apps.api.schemas.portfolio_planner import (
    PlannedExperimentPackageResponse,
    PortfolioPlanRequest,
)
from apps.api.services.portfolio_planner_engine import ResearchPortfolioPlannerEngine

router = APIRouter(
    prefix="/api/v1/research/portfolio-planner",
    tags=["Research Portfolio Planner"],
    dependencies=[Depends(require_authenticated)],
)


@router.post("/plan", response_model=PlannedExperimentPackageResponse)
def plan_research_portfolio(request: PortfolioPlanRequest):
    """
    Generate an authoritative experiment portfolio plan and dynamic compute allocation.
    """
    plan = ResearchPortfolioPlannerEngine.get_instance().plan_research_portfolio(
        target_objective=request.target_objective,
        total_compute_charts_budget=request.total_compute_charts_budget,
        max_parallel_workers=request.max_parallel_workers,
        snapshot_id=request.snapshot_id,
    )

    return PlannedExperimentPackageResponse(
        plan_id=plan.plan_id,
        target_objective=plan.target_objective,
        total_hypotheses_ranked=plan.total_hypotheses_ranked,
        ranked_candidates=[
            {
                "hypothesis_id": c.hypothesis_id,
                "rule_name": c.rule_name,
                "target_objective": c.target_objective,
                "formula_expression": c.formula_expression,
                "discovery_lift": c.discovery_lift,
                "fdr_q_value": c.fdr_q_value,
                "reproducibility_score_percent": c.reproducibility_score_percent,
                "knowledge_graph_centrality": c.knowledge_graph_centrality,
                "sample_deficit": c.sample_deficit,
                "evidence_priority_score": c.evidence_priority_score,
                "priority_rank": c.priority_rank,
                "assigned_tier": c.assigned_tier.value,
                "required_sample_size_target": c.required_sample_size_target,
                "statistical_power_estimate": c.statistical_power_estimate,
                "epistemic_rationale": c.epistemic_rationale,
            }
            for c in plan.ranked_candidates
        ],
        budget_plan={
            "total_compute_charts_budget": plan.budget_plan.total_compute_charts_budget,
            "tier_allocations": [
                {
                    "tier": t.tier.value,
                    "allocated_chart_evaluations": t.allocated_chart_evaluations,
                    "allocation_percentage": t.allocation_percentage,
                    "target_studies_count": t.target_studies_count,
                    "recommended_worker_concurrency": t.recommended_worker_concurrency,
                    "estimated_throughput_charts_per_sec": t.estimated_throughput_charts_per_sec,
                }
                for t in plan.budget_plan.tier_allocations
            ],
            "max_parallel_workers": plan.budget_plan.max_parallel_workers,
            "ephemeris_cache_target_hit_rate_pct": plan.budget_plan.ephemeris_cache_target_hit_rate_pct,
            "budget_utilization_percent": plan.budget_plan.budget_utilization_percent,
        },
        p11_lineage_snapshot_id=plan.p11_lineage_snapshot_id,
        plan_provenance_hash=plan.plan_provenance_hash,
        epistemic_non_causal_statement=plan.epistemic_non_causal_statement,
        planned_at=plan.planned_at.isoformat(),
    )


@router.get("/latest", response_model=PlannedExperimentPackageResponse)
def get_latest_portfolio_plan(target_objective: str = Query("marriage")):
    """
    Get or evaluate the latest research portfolio plan for the target objective.
    """
    plan = ResearchPortfolioPlannerEngine.get_instance().plan_research_portfolio(
        target_objective=target_objective
    )

    return PlannedExperimentPackageResponse(
        plan_id=plan.plan_id,
        target_objective=plan.target_objective,
        total_hypotheses_ranked=plan.total_hypotheses_ranked,
        ranked_candidates=[
            {
                "hypothesis_id": c.hypothesis_id,
                "rule_name": c.rule_name,
                "target_objective": c.target_objective,
                "formula_expression": c.formula_expression,
                "discovery_lift": c.discovery_lift,
                "fdr_q_value": c.fdr_q_value,
                "reproducibility_score_percent": c.reproducibility_score_percent,
                "knowledge_graph_centrality": c.knowledge_graph_centrality,
                "sample_deficit": c.sample_deficit,
                "evidence_priority_score": c.evidence_priority_score,
                "priority_rank": c.priority_rank,
                "assigned_tier": c.assigned_tier.value,
                "required_sample_size_target": c.required_sample_size_target,
                "statistical_power_estimate": c.statistical_power_estimate,
                "epistemic_rationale": c.epistemic_rationale,
            }
            for c in plan.ranked_candidates
        ],
        budget_plan={
            "total_compute_charts_budget": plan.budget_plan.total_compute_charts_budget,
            "tier_allocations": [
                {
                    "tier": t.tier.value,
                    "allocated_chart_evaluations": t.allocated_chart_evaluations,
                    "allocation_percentage": t.allocation_percentage,
                    "target_studies_count": t.target_studies_count,
                    "recommended_worker_concurrency": t.recommended_worker_concurrency,
                    "estimated_throughput_charts_per_sec": t.estimated_throughput_charts_per_sec,
                }
                for t in plan.budget_plan.tier_allocations
            ],
            "max_parallel_workers": plan.budget_plan.max_parallel_workers,
            "ephemeris_cache_target_hit_rate_pct": plan.budget_plan.ephemeris_cache_target_hit_rate_pct,
            "budget_utilization_percent": plan.budget_plan.budget_utilization_percent,
        },
        p11_lineage_snapshot_id=plan.p11_lineage_snapshot_id,
        plan_provenance_hash=plan.plan_provenance_hash,
        epistemic_non_causal_statement=plan.epistemic_non_causal_statement,
        planned_at=plan.planned_at.isoformat(),
    )
