"""
AstroOS — Unit Tests for Priority 30: Research Publication & Cryptographic Audit Report Engine
"""

import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import require_authenticated
from apps.api.domain.research_publication import (
    MANDATORY_PUBLICATION_NON_CAUSAL_DECLARATION,
    PublicationStatus,
    ReportSectionType,
)
from apps.api.main import app
from apps.api.services.research_publication_engine import ResearchPublicationEngine
from apps.api.services.cohort_validation_engine import CohortValidationEngine
from apps.api.services.evidence_intelligence_engine import EvidenceIntelligenceEngine
from apps.api.services.calibration_engine import CalibrationEngine
from apps.api.services.hypothesis_mining_engine import HypothesisMiningEngine
from apps.api.services.prospective_validation_engine import ProspectiveValidationEngine
from apps.api.services.research_data_governance_engine import ResearchDataGovernanceEngine
from apps.api.services.research_reproducibility_engine import ResearchReproducibilityEngine
from apps.api.services.decision_synthesis_engine import ResearchDecisionSynthesisEngine
from apps.api.services.research_knowledge_graph_engine import ResearchKnowledgeGraphEngine
from apps.api.services.decision_action_engine import ResearchDecisionActionEngine
from apps.api.services.portfolio_planner_engine import ResearchPortfolioPlannerEngine
from apps.api.services.longitudinal_tracking_engine import LongitudinalTrackingEngine
from apps.api.services.adaptive_research_engine import AdaptiveResearchEngine
from apps.api.services.benchmark_expansion_engine import BenchmarkExpansionEngine
from apps.api.services.explainability_engine import PredictionExplainabilityEngine
from apps.api.services.experiment_service import ExperimentRegistry


@pytest.fixture
def api_client():
    app.dependency_overrides[require_authenticated] = lambda: {"sub": "p30_tester", "role": "researcher"}
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def _build_engine() -> ResearchPublicationEngine:
    """Assemble a fully-wired engine for P30 testing."""
    exp_reg = ExperimentRegistry.get_instance()
    calibration = CalibrationEngine.get_instance()
    cohort = CohortValidationEngine()
    evidence = EvidenceIntelligenceEngine(cohort_engine=cohort, calibration_engine=calibration)
    mining = HypothesisMiningEngine(cohort_engine=cohort, evidence_engine=evidence, experiment_registry=exp_reg)
    prospective = ProspectiveValidationEngine(mining_engine=mining, evidence_engine=evidence, experiment_registry=exp_reg)
    data_gov = ResearchDataGovernanceEngine(experiment_registry=exp_reg)
    repro = ResearchReproducibilityEngine(
        experiment_registry=exp_reg,
        cohort_engine=cohort,
        mining_engine=mining,
        prospective_engine=prospective,
        data_gov_engine=data_gov,
    )
    explain = PredictionExplainabilityEngine(evidence_engine=evidence, calibration_engine=calibration)
    decision = ResearchDecisionSynthesisEngine(
        cohort_engine=cohort, evidence_engine=evidence, explain_engine=explain,
        mining_engine=mining, prospective_engine=prospective,
        data_gov_engine=data_gov, repro_engine=repro, experiment_registry=exp_reg,
    )
    graph = ResearchKnowledgeGraphEngine(
        experiment_registry=exp_reg, cohort_engine=cohort, evidence_engine=evidence,
        mining_engine=mining, prospective_engine=prospective,
        repro_engine=repro, data_gov_engine=data_gov,
    )
    action = ResearchDecisionActionEngine(
        experiment_registry=exp_reg, cohort_engine=cohort, evidence_engine=evidence,
        mining_engine=mining, prospective_engine=prospective,
        data_gov_engine=data_gov, repro_engine=repro,
        decision_engine=decision, graph_engine=graph,
    )
    planner = ResearchPortfolioPlannerEngine(
        experiment_registry=exp_reg, cohort_engine=cohort, evidence_engine=evidence,
        mining_engine=mining, prospective_engine=prospective,
        data_gov_engine=data_gov, repro_engine=repro,
        graph_engine=graph, action_engine=action,
    )
    longitudinal = LongitudinalTrackingEngine(
        prospective_engine=prospective, planner_engine=planner, experiment_registry=exp_reg,
    )
    adaptive = AdaptiveResearchEngine(
        planner_engine=planner, longitudinal_engine=longitudinal, experiment_registry=exp_reg,
    )
    benchmark = BenchmarkExpansionEngine(experiment_registry=exp_reg)

    return ResearchPublicationEngine(
        experiment_registry=exp_reg,
        cohort_engine=cohort,
        evidence_engine=evidence,
        mining_engine=mining,
        prospective_engine=prospective,
        data_gov_engine=data_gov,
        repro_engine=repro,
        decision_engine=decision,
        graph_engine=graph,
        action_engine=action,
        planner_engine=planner,
        longitudinal_engine=longitudinal,
        adaptive_engine=adaptive,
        benchmark_engine=benchmark,
    )


def test_publication_report_structure_and_non_causal_compliance():
    """
    Verifies that the generated publication report has all required sections,
    cryptographic audit chain entries, and is non-causal compliant throughout.
    """
    engine = _build_engine()
    report = engine.generate_publication_report(target_objective="marriage")

    assert report is not None
    assert report.total_pipeline_stages_covered == 29
    assert len(report.report_sha256_seal) == 64
    assert MANDATORY_PUBLICATION_NON_CAUSAL_DECLARATION in report.publication_non_causal_declaration

    # Verify all required section types are present
    section_types = {s.section_type for s in report.sections}
    assert ReportSectionType.ABSTRACT in section_types
    assert ReportSectionType.METHODOLOGY in section_types
    assert ReportSectionType.DATA_GOVERNANCE in section_types
    assert ReportSectionType.HYPOTHESIS_REGISTRY in section_types
    assert ReportSectionType.STATISTICAL_FORMULAS in section_types
    assert ReportSectionType.RESULTS in section_types
    assert ReportSectionType.REPRODUCIBILITY_AUDIT in section_types
    assert ReportSectionType.EPISTEMIC_LIMITATIONS in section_types
    assert ReportSectionType.CRYPTOGRAPHIC_SEAL in section_types

    # All sections must be non-causal compliant
    assert all(s.is_non_causal_compliant for s in report.sections)

    # Cryptographic audit chain
    assert len(report.cryptographic_audit_chain) >= 10
    for entry in report.cryptographic_audit_chain:
        assert len(entry.sha256_hash) == 64


def test_cryptographic_seal_changes_with_different_objective():
    """
    Verifies that the report SHA-256 seal is deterministically different for
    different objectives — ensuring no seal reuse across distinct reports.
    """
    engine = _build_engine()
    r1 = engine.generate_publication_report(target_objective="marriage")
    r2 = engine.generate_publication_report(target_objective="career")

    assert r1.report_sha256_seal != r2.report_sha256_seal
    assert r1.target_objective != r2.target_objective


def test_publication_api_endpoints(api_client):
    """
    Verifies FastAPI endpoints for report generation, latest, and list.
    """
    # POST /api/v1/research/publication/generate
    gen_resp = api_client.post(
        "/api/v1/research/publication/generate",
        json={"target_objective": "marriage", "status": "PEER_REVIEW_READY", "snapshot_id": None},
    )
    assert gen_resp.status_code == 200
    data = gen_resp.json()
    assert data["target_objective"] == "marriage"
    assert data["status"] == "PEER_REVIEW_READY"
    assert data["total_pipeline_stages_covered"] == 29
    assert len(data["sections"]) >= 9
    assert len(data["cryptographic_audit_chain"]) >= 10
    assert len(data["report_sha256_seal"]) == 64

    # GET /api/v1/research/publication/latest
    latest_resp = api_client.get("/api/v1/research/publication/latest?target_objective=marriage")
    assert latest_resp.status_code == 200
    latest_data = latest_resp.json()
    assert latest_data["target_objective"] == "marriage"

    # GET /api/v1/research/publication/list
    list_resp = api_client.get("/api/v1/research/publication/list")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert len(list_data) >= 2
