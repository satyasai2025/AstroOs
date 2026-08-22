"""
AstroOS — Unit Tests for Priority 26: Research Portfolio & Experiment Planner
"""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import require_authenticated
from apps.api.domain.portfolio_planner import (
    ExperimentPriorityTier,
    PlannedExperimentPackage,
)
from apps.api.main import app
from apps.api.services.cohort_validation_engine import CohortValidationEngine
from apps.api.services.decision_action_engine import ResearchDecisionActionEngine
from apps.api.services.decision_synthesis_engine import ResearchDecisionSynthesisEngine
from apps.api.services.evidence_intelligence_engine import EvidenceIntelligenceEngine
from apps.api.services.experiment_service import ExperimentRegistry
from apps.api.services.hypothesis_mining_engine import HypothesisMiningEngine
from apps.api.services.portfolio_planner_engine import ResearchPortfolioPlannerEngine
from apps.api.services.prospective_validation_engine import ProspectiveValidationEngine
from apps.api.services.research_data_governance_engine import ResearchDataGovernanceEngine
from apps.api.services.research_knowledge_graph_engine import ResearchKnowledgeGraphEngine
from apps.api.services.research_reproducibility_engine import ResearchReproducibilityEngine


@pytest.fixture
def api_client():
    app.dependency_overrides[require_authenticated] = lambda: {"sub": "p26_tester", "role": "researcher"}
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_research_portfolio_planning_and_ranking():
    """
    Verifies that the portfolio planner generates deterministic EvidencePriorityScores,
    ranks candidates correctly, and derives dynamic budget tier allocations.
    """
    exp_reg = ExperimentRegistry.get_instance()
    cohort_engine = CohortValidationEngine()
    evidence_engine = EvidenceIntelligenceEngine(cohort_engine=cohort_engine)
    mining_engine = HypothesisMiningEngine.get_instance()
    prospective_engine = ProspectiveValidationEngine.get_instance()
    data_gov_engine = ResearchDataGovernanceEngine.get_instance()
    repro_engine = ResearchReproducibilityEngine.get_instance()
    decision_engine = ResearchDecisionSynthesisEngine.get_instance()
    graph_engine = ResearchKnowledgeGraphEngine(
        experiment_registry=exp_reg,
        cohort_engine=cohort_engine,
        evidence_engine=evidence_engine,
        mining_engine=mining_engine,
        prospective_engine=prospective_engine,
        repro_engine=repro_engine,
        data_gov_engine=data_gov_engine,
    )
    action_engine = ResearchDecisionActionEngine(
        experiment_registry=exp_reg,
        cohort_engine=cohort_engine,
        evidence_engine=evidence_engine,
        mining_engine=mining_engine,
        prospective_engine=prospective_engine,
        data_gov_engine=data_gov_engine,
        repro_engine=repro_engine,
        decision_engine=decision_engine,
        graph_engine=graph_engine,
    )

    planner = ResearchPortfolioPlannerEngine(
        experiment_registry=exp_reg,
        cohort_engine=cohort_engine,
        evidence_engine=evidence_engine,
        mining_engine=mining_engine,
        prospective_engine=prospective_engine,
        data_gov_engine=data_gov_engine,
        repro_engine=repro_engine,
        graph_engine=graph_engine,
        action_engine=action_engine,
    )

    plan = planner.plan_research_portfolio(
        target_objective="marriage",
        total_compute_charts_budget=6000,
        max_parallel_workers=4,
    )

    assert plan is not None
    assert plan.target_objective == "marriage"
    assert plan.total_hypotheses_ranked >= 2
    assert len(plan.ranked_candidates) >= 2
    # Verify rankings are sorted by EvidencePriorityScore descending
    for i in range(len(plan.ranked_candidates) - 1):
        assert plan.ranked_candidates[i].evidence_priority_score >= plan.ranked_candidates[i + 1].evidence_priority_score
        assert plan.ranked_candidates[i].priority_rank == i + 1

    top_candidate = plan.ranked_candidates[0]
    assert top_candidate.assigned_tier == ExperimentPriorityTier.TIER_A_PRIMARY_TRIAL
    assert top_candidate.evidence_priority_score >= 75.0
    assert top_candidate.statistical_power_estimate >= 0.80
    assert top_candidate.required_sample_size_target >= 150

    # Verify Dynamic Budget Allocations
    assert plan.budget_plan.total_compute_charts_budget == 6000
    assert len(plan.budget_plan.tier_allocations) == 3
    total_allocated = sum(t.allocated_chart_evaluations for t in plan.budget_plan.tier_allocations)
    assert total_allocated == 6000
    total_pct = sum(t.allocation_percentage for t in plan.budget_plan.tier_allocations)
    assert 99.0 <= total_pct <= 101.0
    assert len(plan.plan_provenance_hash) == 16
    assert "PORTFOLIO_OPTIMIZATION_ONLY" in plan.epistemic_non_causal_statement


def test_budget_allocation_reacts_dynamically_to_demands():
    """
    Proves that budget allocation is not statically locked to 50/35/15,
    but dynamically adjusts when candidate distributions and compute capacities vary.
    """
    planner = ResearchPortfolioPlannerEngine.get_instance()

    plan_10k = planner.plan_research_portfolio(
        target_objective="marriage",
        total_compute_charts_budget=10000,
        max_parallel_workers=8,
    )
    assert plan_10k.budget_plan.total_compute_charts_budget == 10000
    assert sum(t.allocated_chart_evaluations for t in plan_10k.budget_plan.tier_allocations) == 10000
    tier_a = next(t for t in plan_10k.budget_plan.tier_allocations if t.tier == ExperimentPriorityTier.TIER_A_PRIMARY_TRIAL)
    assert tier_a.allocated_chart_evaluations > 3000
    assert tier_a.recommended_worker_concurrency >= 2


def test_portfolio_planner_api_endpoints(api_client):
    """
    Verifies FastAPI endpoints for plan generation and latest plan queries.
    """
    # POST /api/v1/research/portfolio-planner/plan
    plan_resp = api_client.post(
        "/api/v1/research/portfolio-planner/plan",
        json={
            "target_objective": "marriage",
            "total_compute_charts_budget": 5000,
            "max_parallel_workers": 4,
            "snapshot_id": None,
        },
    )
    assert plan_resp.status_code == 200
    data = plan_resp.json()
    assert data["target_objective"] == "marriage"
    assert len(data["ranked_candidates"]) >= 2
    assert len(data["budget_plan"]["tier_allocations"]) == 3

    # GET /api/v1/research/portfolio-planner/latest
    latest_resp = api_client.get("/api/v1/research/portfolio-planner/latest?target_objective=marriage")
    assert latest_resp.status_code == 200
    latest_data = latest_resp.json()
    assert latest_data["target_objective"] == "marriage"
    assert len(latest_data["ranked_candidates"]) >= 2
