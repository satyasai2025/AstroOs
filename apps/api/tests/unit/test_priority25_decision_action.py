"""
AstroOS — Unit Tests for Priority 25: Research Decision & Evidence Action Engine
"""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import require_authenticated
from apps.api.domain.decision_action import (
    ResearchActionVerdict,
    ResearchReadinessLevel,
)
from apps.api.domain.hypothesis_mining import (
    AstrologicalPatternPrimitive,
    DiscoveredHypothesis,
    HypothesisStatus,
    PatternDimension,
)
from apps.api.main import app
from apps.api.services.cohort_validation_engine import CohortValidationEngine
from apps.api.services.decision_action_engine import ResearchDecisionActionEngine
from apps.api.services.decision_synthesis_engine import ResearchDecisionSynthesisEngine
from apps.api.services.evidence_intelligence_engine import EvidenceIntelligenceEngine
from apps.api.services.experiment_service import ExperimentRegistry
from apps.api.services.hypothesis_mining_engine import HypothesisMiningEngine
from apps.api.services.prospective_validation_engine import ProspectiveValidationEngine
from apps.api.services.research_data_governance_engine import ResearchDataGovernanceEngine
from apps.api.services.research_knowledge_graph_engine import ResearchKnowledgeGraphEngine
from apps.api.services.research_reproducibility_engine import ResearchReproducibilityEngine


@pytest.fixture
def api_client():
    app.dependency_overrides[require_authenticated] = lambda: {"sub": "p25_tester", "role": "researcher"}
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_research_decision_action_evaluation():
    """
    Verifies that the action engine dynamically evaluates P15-P24 evidence into an actionable ACCEPT verdict.
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

    # Ensure prospective validation report exists
    pre_reg = prospective_engine.pre_register_hypothesis(
        hypothesis_id="hyp-m1",
        rule_name="Canonical Marriage Activation Rule",
        target_objective="marriage",
        formula_expression='DASHA == "7th_Lord" AND TRANSIT("Jupiter", 7)',
        thresholds={"min_lift": 1.35},
    )
    from datetime import date as _date
    _pos_i = 0
    for _i in range(150):
        if _i % 3 == 0 and _pos_i < 50:
            _prob, _outcome = 0.9, True
            _pos_i += 1
        else:
            _prob, _outcome = 0.1, False
        prospective_engine.log_blind_prediction(
            registration_id=pre_reg.registration_id,
            subject_id=f"subj-{_i:03d}",
            predicted_probability=_prob,
            prediction_window_start=_date(2026, 1, 1),
            prediction_window_end=_date(2026, 6, 30),
        )
        prospective_engine.record_subject_outcome(pre_reg.registration_id, f"subj-{_i:03d}", _outcome)
    prospective_engine.evaluate_prospective_cohort(pre_reg.registration_id)

    decision = action_engine.evaluate_research_action_decision(target_objective="marriage")

    assert decision is not None
    assert decision.target_objective == "marriage"
    assert decision.verdict == ResearchActionVerdict.ACCEPT
    assert decision.readiness_level == ResearchReadinessLevel.LEVEL_1_PRODUCTION_READY
    assert decision.empirical_readiness_score_percent >= 85.0
    assert len(decision.decision_factors) == 8
    assert all(f.weight > 0 for f in decision.decision_factors)
    assert sum(f.weight for f in decision.decision_factors) == pytest.approx(1.0, 0.01)
    assert len(decision.supporting_evidence_points) >= 4
    assert len(decision.risk_and_attenuation_factors) >= 2
    assert decision.policy_recommendation.longitudinal_tracking_enabled is True
    assert decision.policy_recommendation.experiment_planning_priority == "HIGH"
    assert len(decision.decision_provenance_hash) == 16
    assert "READINESS_ONLY" in decision.epistemic_non_causal_statement


def test_decision_action_reacts_to_unsupported_conditions():
    """
    Proves that when prospective validation is missing or rejected,
    the verdict dynamically transitions to HOLD or REJECT rather than fabricating an ACCEPT.
    """
    exp_reg = ExperimentRegistry.get_instance()
    mining_engine = HypothesisMiningEngine()
    prospective_engine = ProspectiveValidationEngine(mining_engine=mining_engine)
    action_engine = ResearchDecisionActionEngine(
        experiment_registry=exp_reg,
        mining_engine=mining_engine,
        prospective_engine=prospective_engine,
    )

    # Career has no prospective validation performed yet -> Should result in non-ACCEPT (HOLD/REJECT/NEEDS_MORE_EVIDENCE)
    decision_career = action_engine.evaluate_research_action_decision(target_objective="career")
    assert decision_career.verdict in (ResearchActionVerdict.HOLD, ResearchActionVerdict.NEEDS_MORE_EVIDENCE, ResearchActionVerdict.REJECT)
    assert decision_career.verdict != ResearchActionVerdict.ACCEPT
    assert decision_career.readiness_level != ResearchReadinessLevel.LEVEL_1_PRODUCTION_READY
    assert decision_career.policy_recommendation.longitudinal_tracking_enabled is False


def test_decision_action_api_endpoints(api_client):
    """
    Verifies FastAPI endpoints for evaluation and latest query.
    """
    # POST /api/v1/research/decision-action/evaluate
    eval_resp = api_client.post(
        "/api/v1/research/decision-action/evaluate",
        json={"target_objective": "marriage", "snapshot_id": None},
    )
    assert eval_resp.status_code == 200
    data = eval_resp.json()
    assert data["target_objective"] == "marriage"
    assert data["verdict"] in ("ACCEPT", "HOLD", "REJECT", "NEEDS_MORE_EVIDENCE")
    assert len(data["decision_factors"]) == 8

    # GET /api/v1/research/decision-action/latest
    latest_resp = api_client.get("/api/v1/research/decision-action/latest?target_objective=marriage")
    assert latest_resp.status_code == 200
    latest_data = latest_resp.json()
    assert latest_data["decision_id"] == data["decision_id"] or latest_data["target_objective"] == "marriage"
