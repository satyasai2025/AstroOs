"""
AstroOS — Unit Tests for Priority 24: Evidence-Weighted Research Knowledge Graph
"""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import require_authenticated
from apps.api.domain.experiment_lineage import (
    CalibrationProvenanceSnapshot,
    DatasetProvenanceSnapshot,
    ExperimentMetrics,
    OrchestratorConfigSnapshot,
    TechniqueProvenanceSnapshot,
)
from apps.api.domain.hypothesis_mining import (
    AstrologicalPatternPrimitive,
    DiscoveredHypothesis,
    HypothesisStatus,
    PatternDimension,
    ReplicationRecord,
)
from apps.api.domain.research_knowledge_graph import (
    EvidenceRelationshipType,
    ResearchNodeType,
)
from apps.api.main import app
from apps.api.services.cohort_validation_engine import CohortValidationEngine
from apps.api.services.evidence_intelligence_engine import EvidenceIntelligenceEngine
from apps.api.services.experiment_service import ExperimentRegistry
from apps.api.services.hypothesis_mining_engine import HypothesisMiningEngine
from apps.api.services.prospective_validation_engine import ProspectiveValidationEngine
from apps.api.services.research_data_governance_engine import ResearchDataGovernanceEngine
from apps.api.services.research_knowledge_graph_engine import (
    ResearchKnowledgeGraphEngine,
    compute_deterministic_evidence_weight,
)
from apps.api.services.research_reproducibility_engine import ResearchReproducibilityEngine


@pytest.fixture
def api_client():
    app.dependency_overrides[require_authenticated] = lambda: {"sub": "p24_tester", "role": "researcher"}
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_deterministic_evidence_weight_formula():
    """
    Verifies that edge weight W is strictly deterministic, closed-form, and within [0, 1].
    """
    # Max evidence scenario
    w_max = compute_deterministic_evidence_weight(
        empirical_lift=3.0,
        brier_score=0.0,
        prospective_supported=True,
        reproducibility_score=100.0,
    )
    # L_norm=1.0 (0.35), B_norm=1.0 (0.25), P_supp=1.0 (0.20), R_score=1.0 (0.20) -> 1.000
    assert w_max == 1.0

    # Baseline scenario
    w_base = compute_deterministic_evidence_weight(
        empirical_lift=1.0,
        brier_score=0.25,
        prospective_supported=False,
        reproducibility_score=0.0,
    )
    # L_norm=0.0 (0.0), B_norm=0.0 (0.0), P_supp=0.0 (0.0), R_score=0.0 (0.0) -> 0.000
    assert w_base == 0.0

    # Intermediate scenario
    w_mid = compute_deterministic_evidence_weight(
        empirical_lift=1.60,
        brier_score=0.038,
        prospective_supported=True,
        reproducibility_score=100.0,
    )
    assert 0.70 <= w_mid <= 0.75


def test_dynamic_knowledge_graph_generation_and_non_causal_guarantee():
    """
    Verifies genuine dynamic multi-domain graph generation from upstream engines,
    strict non-causal disclosures, and cross-hypothesis clustering.
    """
    exp_reg = ExperimentRegistry.get_instance()
    cohort_engine = CohortValidationEngine()
    evidence_engine = EvidenceIntelligenceEngine(cohort_engine=cohort_engine)
    mining_engine = HypothesisMiningEngine.get_instance()
    prospective_engine = ProspectiveValidationEngine.get_instance()
    repro_engine = ResearchReproducibilityEngine.get_instance()

    engine = ResearchKnowledgeGraphEngine(
        experiment_registry=exp_reg,
        cohort_engine=cohort_engine,
        evidence_engine=evidence_engine,
        mining_engine=mining_engine,
        prospective_engine=prospective_engine,
        repro_engine=repro_engine,
    )

    graph = engine.build_research_knowledge_graph(target_objective="marriage")

    # 1. Node Topology coverage
    node_types = {n.node_type for n in graph.nodes}
    assert ResearchNodeType.GRAHA in node_types
    assert ResearchNodeType.BHAVA in node_types
    assert ResearchNodeType.DASHA in node_types
    assert ResearchNodeType.TRANSIT in node_types
    assert ResearchNodeType.YOGA in node_types
    assert ResearchNodeType.VARGA in node_types
    assert ResearchNodeType.HYPOTHESIS in node_types
    assert ResearchNodeType.TECHNIQUE in node_types
    assert ResearchNodeType.EVENT_OUTCOME in node_types

    # 2. Strict Non-Causal Epistemic Guarantee
    assert graph.is_fully_non_causal is True
    for edge in graph.edges:
        assert edge.is_causal_claimed is False
        assert "ASSOCIATIONAL_ONLY" in edge.epistemic_disclosure
        assert 0.0 <= edge.evidence_weight <= 1.0
        assert len(edge.provenance_hash) > 0

    # 3. Dynamic Synergies from P16
    assert len(graph.technique_interactions) > 0
    ti = graph.technique_interactions[0]
    assert ti.synergy_delta > 0
    assert ti.epistemic_label in ("OBSERVED_POSITIVE_CONFLUENCE", "OBSERVED_NEUTRAL_INTERACTION")


def test_graph_reacts_dynamically_to_upstream_research_changes():
    """
    Proves that when upstream research data in P19 (mined hypothesis) or P20 (prospective study)
    is added or updated, the knowledge graph dynamically ingests and reflects the new nodes,
    epistemic grades, and clusters.
    """
    exp_reg = ExperimentRegistry.get_instance()
    mining_engine = HypothesisMiningEngine()
    prospective_engine = ProspectiveValidationEngine(mining_engine=mining_engine)
    engine = ResearchKnowledgeGraphEngine(
        experiment_registry=exp_reg,
        mining_engine=mining_engine,
        prospective_engine=prospective_engine,
    )

    # Initial graph
    graph1 = engine.build_research_knowledge_graph(target_objective="marriage")
    initial_node_count = len(graph1.nodes)

    # Inject a new discovered hypothesis directly into P19
    custom_hypo_id = "hyp-custom-career-elevation"
    custom_hypo = DiscoveredHypothesis(
        hypothesis_id=custom_hypo_id,
        name="Custom Navamsha D9 Sun In 10th House",
        target_objective="career",
        pattern_primitives=(
            AstrologicalPatternPrimitive(PatternDimension.DIVISIONAL_VARGA, "D9", "Sun", "HOUSE_10"),
        ),
        discovery_dataset_id="ds-career-founders",
        discovery_sample_size=300,
        discovery_support_percent=25.0,
        discovery_confidence_percent=85.0,
        discovery_statistical_lift=1.85,
        discovery_raw_p_value=0.005,
        discovery_fdr_q_value=0.012,
        status=HypothesisStatus.REPLICATED_VALIDATED,
        replication_records=(),
        lineage_snapshot_id="snap-p11-custom",
        discovered_at=datetime.now(timezone.utc),
        classical_provenance_note="Canonical career elevation principle.",
    )
    mining_engine._discovered_hypotheses[custom_hypo_id] = custom_hypo

    # Pre-register and prospectively support this rule in P20
    pre_reg = prospective_engine.pre_register_hypothesis(
        hypothesis_id=custom_hypo_id,
        rule_name="Custom Navamsha D9 Sun Rule",
        target_objective="career",
        formula_expression='VARGA("D9", "Sun") == "HOUSE_10"',
        thresholds={"min_lift": 1.50},
    )
    prospective_engine.evaluate_prospective_cohort(pre_reg.registration_id, total_subjects=100)

    # Re-build knowledge graph for career objective
    graph_career = engine.build_research_knowledge_graph(target_objective="career")

    # Verify that the newly injected P19/P20 hypothesis appears dynamically in graph nodes
    career_node_ids = [n.node_id for n in graph_career.nodes]
    assert f"node-hyp-{custom_hypo_id}" in career_node_ids

    # Verify that its epistemic grade is elevated to EMPIRICALLY_SUPPORTED_PROSPECTIVE_RULE
    custom_node = next(n for n in graph_career.nodes if n.node_id == f"node-hyp-{custom_hypo_id}")
    assert custom_node.epistemic_grade == "EMPIRICALLY_SUPPORTED_PROSPECTIVE_RULE"
    assert custom_node.properties["lift"] == 1.85

    # Verify that an edge is dynamically attached to this new hypothesis
    hypo_edges = [e for e in graph_career.edges if e.source_node_id == f"node-hyp-{custom_hypo_id}" or e.target_node_id == f"node-hyp-{custom_hypo_id}"]
    assert len(hypo_edges) >= 1
    assert hypo_edges[0].is_causal_claimed is False
    assert hypo_edges[0].empirical_lift == 1.85


def test_research_knowledge_graph_api_endpoints(api_client):
    """
    Verifies FastAPI query, clusters, and interactions endpoints.
    """
    # POST /api/v1/research/knowledge-graph/query
    query_resp = api_client.post(
        "/api/v1/research/knowledge-graph/query",
        json={"target_objective": "marriage", "min_weight_threshold": 0.5, "node_type_filter": None},
    )
    assert query_resp.status_code == 200
    data = query_resp.json()
    assert data["target_objective"] == "marriage"
    assert data["is_fully_non_causal"] is True
    assert len(data["nodes"]) >= 9
    assert all(e["evidence_weight"] >= 0.5 for e in data["edges"])

    # GET /api/v1/research/knowledge-graph/clusters
    clusters_resp = api_client.get("/api/v1/research/knowledge-graph/clusters?target_objective=marriage")
    assert clusters_resp.status_code == 200
    clusters = clusters_resp.json()
    assert isinstance(clusters, list)

    # GET /api/v1/research/knowledge-graph/interactions
    interactions_resp = api_client.get("/api/v1/research/knowledge-graph/interactions?target_objective=marriage")
    assert interactions_resp.status_code == 200
    interactions = interactions_resp.json()
    assert isinstance(interactions, list)
