"""
AstroOS — Unit Tests for Priority 28: Adaptive Research & Sequential Experiment Engine
"""

from datetime import date, datetime, timezone
import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import require_authenticated
from apps.api.domain.adaptive_research import (
    AdaptiveTrialPhase,
    AlphaSpendingMethod,
    InterimDecisionVerdict,
)
from apps.api.main import app
from apps.api.services.adaptive_research_engine import AdaptiveResearchEngine
from apps.api.services.experiment_service import ExperimentRegistry
from apps.api.services.longitudinal_tracking_engine import LongitudinalTrackingEngine
from apps.api.services.portfolio_planner_engine import ResearchPortfolioPlannerEngine


@pytest.fixture
def api_client():
    app.dependency_overrides[require_authenticated] = lambda: {"sub": "p28_tester", "role": "researcher"}
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_immutable_trial_commitment_and_alpha_spending():
    """
    Verifies that the engine freezes pre-trial commitments with explicit alpha spending methods,
    immutable rule definitions, and predefined strata prior to outcome inspection.
    """
    planner_engine = ResearchPortfolioPlannerEngine.get_instance()
    longitudinal_engine = LongitudinalTrackingEngine.get_instance()
    exp_reg = ExperimentRegistry.get_instance()

    engine = AdaptiveResearchEngine(
        planner_engine=planner_engine,
        longitudinal_engine=longitudinal_engine,
        experiment_registry=exp_reg,
    )

    commit = engine.create_immutable_trial_commitment(
        target_objective="marriage",
        alpha_spending_method=AlphaSpendingMethod.LAN_DEMETS_OBRIEN_FLEMING,
        overall_alpha_budget=0.05,
        planned_maximum_sample_size=300,
        permit_outcome_dependent_adaptation=False,
    )

    assert commit is not None
    assert commit.target_objective == "marriage"
    assert commit.alpha_spending_method == AlphaSpendingMethod.LAN_DEMETS_OBRIEN_FLEMING
    assert commit.overall_alpha_budget == 0.05
    assert commit.planned_maximum_sample_size == 300
    assert commit.permit_outcome_dependent_adaptation is False
    assert len(commit.predefined_strata) == 3
    assert commit.predefined_strata[0].stratum_id == "strat-01-shadbala-high"
    assert len(commit.commitment_provenance_hash) == 16


def test_sequential_interim_evaluation_and_early_stopping():
    """
    Verifies sequential interim analysis at information fraction t=0.50,
    calculates alpha spent, stopping boundaries, and information-blind sample size re-estimation.
    """
    engine = AdaptiveResearchEngine.get_instance()

    report = engine.evaluate_sequential_interim(
        target_objective="marriage",
        interim_look_number=1,
        total_planned_looks=2,
        current_sample_size=150,
    )

    assert report is not None
    assert report.target_objective == "marriage"
    assert report.latest_interim_analysis.information_fraction_t == 0.50
    assert report.latest_interim_analysis.cumulative_alpha_spent > 0.0
    assert report.latest_interim_analysis.cumulative_alpha_spent <= 0.05
    assert report.latest_interim_analysis.efficacy_boundary_z > 2.0
    assert report.latest_interim_analysis.is_information_blind is True
    assert report.latest_interim_analysis.reestimated_sample_size >= 300
    assert len(report.predefined_strata) == 3
    assert "ADAPTIVE_RESEARCH_ONLY" in report.epistemic_non_causal_statement


def test_adaptive_research_api_endpoints(api_client):
    """
    Verifies FastAPI endpoints for commitment creation, interim evaluation, and latest reports.
    """
    # POST /api/v1/research/adaptive-experiment/commit
    commit_resp = api_client.post(
        "/api/v1/research/adaptive-experiment/commit",
        json={
            "target_objective": "marriage",
            "hypothesis_id": "hyp-m1",
            "alpha_spending_method": "LAN_DEMETS_OBRIEN_FLEMING",
            "overall_alpha_budget": 0.05,
            "overall_beta_budget": 0.20,
            "planned_maximum_sample_size": 300,
            "permit_outcome_dependent_adaptation": False,
            "snapshot_id": None,
        },
    )
    assert commit_resp.status_code == 200
    commit_data = commit_resp.json()
    assert commit_data["target_objective"] == "marriage"
    assert commit_data["alpha_spending_method"] == "LAN_DEMETS_OBRIEN_FLEMING"
    assert len(commit_data["predefined_strata"]) == 3

    # POST /api/v1/research/adaptive-experiment/interim-evaluate
    interim_resp = api_client.post(
        "/api/v1/research/adaptive-experiment/interim-evaluate",
        json={
            "commitment_id": commit_data["commitment_id"],
            "target_objective": "marriage",
            "interim_look_number": 1,
            "total_planned_looks": 2,
            "current_sample_size": 150,
            "snapshot_id": None,
        },
    )
    assert interim_resp.status_code == 200
    interim_data = interim_resp.json()
    assert interim_data["target_objective"] == "marriage"
    assert interim_data["latest_interim_analysis"]["information_fraction_t"] == 0.50

    # GET /api/v1/research/adaptive-experiment/latest
    latest_resp = api_client.get("/api/v1/research/adaptive-experiment/latest?target_objective=marriage")
    assert latest_resp.status_code == 200
    latest_data = latest_resp.json()
    assert latest_data["target_objective"] == "marriage"
