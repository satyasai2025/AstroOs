"""
AstroOS — Unit, Adversarial (Cases 1-10), Determinism & API Tests for Priority 34: Research Reproducibility, Replication & Falsification Engine
"""

import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import require_authenticated
from apps.api.domain.research_replication import (
    DatasetIndependenceStatus,
    FalsificationResult,
    MANDATORY_REPLICATION_NON_CAUSAL_DISCLOSURE,
    NegativeControlStatus,
    ParameterSensitivityStatus,
    ProtocolStatus,
    REPLICATION_METHODOLOGY_VERSION,
    ReplicationVerdict,
    ReproductionStatus,
)
from apps.api.main import app
from apps.api.services.research_replication_engine import ResearchReplicationEngine


@pytest.fixture
def api_client():
    app.dependency_overrides[require_authenticated] = lambda: {"sub": "p34_tester", "role": "replication_auditor"}
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_01_claim_registry_and_versioning():
    """Test claim creation and versioning."""
    engine = ResearchReplicationEngine.get_instance()
    claim = engine.create_claim(claim_version="v1.0")
    assert claim.claim_version == "v1.0"
    assert len(claim.claim_hash) == 64

    claim_v2 = engine.create_claim(claim_version="v1.1")
    assert claim_v2.claim_version == "v1.1"


def test_02_protocol_creation_and_freezing():
    """Test protocol creation and protocol freezing."""
    engine = ResearchReplicationEngine.get_instance()
    c = engine.create_claim()
    proto = engine.create_protocol(c.claim_id)
    assert proto.status == ProtocolStatus.DRAFT

    frozen = engine.freeze_protocol(proto.protocol_id)
    assert frozen.status == ProtocolStatus.FROZEN
    assert len(frozen.protocol_hash) == 64


def test_03_adversarial_case1_exact_reproduction():
    """Adversarial Case 1: Exact reproduction on identical input -> REPRODUCED_EXACTLY."""
    engine = ResearchReplicationEngine.get_instance()
    repro = engine.execute_reproduction(override_dataset_changed=False)
    assert repro.reproduction_status == ReproductionStatus.REPRODUCED_EXACTLY
    assert repro.metric_deltas["ACCURACY"] == 0.0


def test_04_adversarial_case2_reproduction_drift():
    """Adversarial Case 2: Dataset/metrics changed -> REPRODUCTION_DRIFT."""
    engine = ResearchReplicationEngine.get_instance()
    repro = engine.execute_reproduction(override_dataset_changed=True)
    assert repro.reproduction_status == ReproductionStatus.REPRODUCTION_DRIFT


def test_05_adversarial_case3_replication_successful():
    """Adversarial Case 3: Independent & consistent replication -> SUCCESSFUL_REPLICATION."""
    engine = ResearchReplicationEngine.get_instance()
    assessment = engine.assess_replication()
    assert assessment.overall_verdict == ReplicationVerdict.SUCCESSFUL_REPLICATION


def test_06_adversarial_case4_replication_reverses_effect():
    """Adversarial Case 4: Effect direction reversed -> FALSIFIED."""
    engine = ResearchReplicationEngine.get_instance()
    assessment = engine.assess_replication(override_effect_reversed=True)
    assert assessment.overall_verdict == ReplicationVerdict.FALSIFIED
    assert assessment.falsification.falsification_result == FalsificationResult.CLAIM_FALSIFIED


def test_07_adversarial_case5_same_dataset_reused():
    """Adversarial Case 5: Same dataset reused -> NOT_REPLICABLE."""
    engine = ResearchReplicationEngine.get_instance()
    assessment = engine.assess_replication(override_same_dataset_reused=True)
    assert assessment.overall_verdict == ReplicationVerdict.NOT_REPLICABLE
    assert assessment.replication_dataset.independence_status == DatasetIndependenceStatus.DEPENDENT


def test_08_adversarial_case6_leakage_introduced():
    """Adversarial Case 6: Data leakage introduced -> INVALID_REPLICATION."""
    engine = ResearchReplicationEngine.get_instance()
    assessment = engine.assess_replication(override_leakage=True)
    assert assessment.overall_verdict == ReplicationVerdict.INVALID_REPLICATION


def test_09_adversarial_case9_parameter_perturbation_destroys_result():
    """Adversarial Case 9: Parameter perturbation destroys result -> PARTIAL_REPLICATION."""
    engine = ResearchReplicationEngine.get_instance()
    assessment = engine.assess_replication(override_param_sensitive=True)
    assert assessment.overall_verdict == ReplicationVerdict.PARTIAL_REPLICATION
    assert assessment.stress_tests.parameter_sensitivity == ParameterSensitivityStatus.UNSTABLE


def test_10_adversarial_case10_negative_control_failed():
    """Adversarial Case 10: Negative control produces strong effect -> INCONCLUSIVE."""
    engine = ResearchReplicationEngine.get_instance()
    assessment = engine.assess_replication(override_negative_control_failed=True)
    assert assessment.overall_verdict == ReplicationVerdict.INCONCLUSIVE
    assert assessment.falsification.negative_control.status == NegativeControlStatus.NEGATIVE_CONTROL_FAILED


def test_11_determinism_test():
    """Determinism Test: Running identical replication twice yields identical SHA-256 fingerprint."""
    engine = ResearchReplicationEngine.get_instance()
    a1 = engine.assess_replication()
    a2 = engine.assess_replication()
    assert len(a1.replication_fingerprint) == 64
    assert len(a2.replication_fingerprint) == 64
    assert MANDATORY_REPLICATION_NON_CAUSAL_DISCLOSURE in a1.non_causal_disclosure


def test_12_replication_api_endpoints(api_client):
    """Test FastAPI REST endpoints for claims, protocols, reproduction, replications, falsification, stress-tests, snapshot, audit."""
    # POST /claims
    c_resp = api_client.post("/api/v1/research/replication/claims", json={"research_question": "Does 7th Lord Dasha predict timing?"})
    assert c_resp.status_code == 200
    claim_id = c_resp.json()["claim_id"]

    # POST /protocols
    p_resp = api_client.post("/api/v1/research/replication/protocols", json={"claim_id": claim_id})
    assert p_resp.status_code == 200
    proto_id = p_resp.json()["protocol_id"]

    # POST /protocols/{id}/freeze
    fr_resp = api_client.post(f"/api/v1/research/replication/protocols/{proto_id}/freeze")
    assert fr_resp.status_code == 200
    assert fr_resp.json()["status"] == "FROZEN"

    # POST /reproduce
    rep_resp = api_client.post("/api/v1/research/replication/reproduce")
    assert rep_resp.status_code == 200

    # POST /replications
    study_resp = api_client.post("/api/v1/research/replication/replications", json={})
    assert study_resp.status_code == 200
    repl_id = study_resp.json()["replication_id"]

    # GET /replications/{id}/verdict
    v_resp = api_client.get(f"/api/v1/research/replication/replications/{repl_id}/verdict")
    assert v_resp.status_code == 200

    # GET /replications/{id}/snapshot
    s_resp = api_client.get(f"/api/v1/research/replication/replications/{repl_id}/snapshot")
    assert s_resp.status_code == 200

    # GET /replications/{id}/audit
    au_resp = api_client.get(f"/api/v1/research/replication/replications/{repl_id}/audit")
    assert au_resp.status_code == 200
