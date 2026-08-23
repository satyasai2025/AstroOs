"""
AstroOS — Unit Tests for Priority 31: Research Forensic & Evidence Reconstruction Engine
"""

import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import require_authenticated
from apps.api.domain.research_forensics import (
    EvidenceOrigin,
    ForensicVerdict,
    MANDATORY_FORENSIC_NON_CAUSAL_DISCLOSURE,
    MANDATORY_SYNTHETIC_EPISTEMIC_DISCLOSURE,
)
from apps.api.main import app
from apps.api.services.research_forensic_engine import ResearchForensicEngine, _canonical_hash


@pytest.fixture
def api_client():
    app.dependency_overrides[require_authenticated] = lambda: {"sub": "p31_tester", "role": "forensic_auditor"}
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_canonical_hashing_deterministic():
    """1. Test deterministic canonical SHA-256 hashing."""
    payload1 = {"b": 2, "a": 1, "c": [3, 4]}
    payload2 = {"a": 1, "c": [3, 4], "b": 2}
    hash1 = _canonical_hash(payload1)
    hash2 = _canonical_hash(payload2)
    assert hash1 == hash2
    assert len(hash1) == 64


def test_evidence_origin_classification_and_synthetic_detection():
    """2 & 3. Test evidence origin classification and explicit synthetic data detection."""
    engine = ResearchForensicEngine.get_instance()
    chain = engine.collect_evidence_chain("marriage")

    # Check synthetic detection for ds-marriage-28
    synthetic_items = [item for item in chain if item.origin == EvidenceOrigin.SYNTHETIC_GENERATED_EVIDENCE]
    assert len(synthetic_items) >= 2
    assert any("ds-marriage-28" in item.source_identifier for item in synthetic_items)
    assert any("ds-prospective" in item.source_identifier for item in synthetic_items)

    # Check classical reference evidence
    classical_items = [item for item in chain if item.origin == EvidenceOrigin.CLASSICAL_REFERENCE_EVIDENCE]
    assert len(classical_items) >= 1
    assert any("BPHS" in item.source_identifier for item in classical_items)


def test_zero_drift_reconstruction_and_seal_generation():
    """4, 10, 11, 12, 13. Test zero-drift reconstruction, seal generation, P11/P30 linkage, and disclosures."""
    engine = ResearchForensicEngine.get_instance()
    result = engine.reconstruct_research_result("marriage")

    assert result is not None
    assert result.verdict == ForensicVerdict.RECONSTRUCTED_WITH_ZERO_DRIFT
    assert result.hash_match is True
    assert result.numerical_drift == 0.0
    assert result.provenance_intact is True
    assert result.p11_lineage_snapshot_id == "snap-p11-publication-root"
    assert result.p30_publication_seal is not None
    assert MANDATORY_FORENSIC_NON_CAUSAL_DISCLOSURE in result.non_causal_disclosure
    assert MANDATORY_SYNTHETIC_EPISTEMIC_DISCLOSURE in result.synthetic_data_disclosure

    report = engine.generate_forensic_audit_report("marriage")
    assert report.p31_forensic_seal is not None
    assert len(report.p31_forensic_seal) == 64
    assert len(report.p30_publication_seal) == 64


def test_modified_evidence_and_provenance_break_detection():
    """7 & 8. Test detection of modified evidence and provenance breaks."""
    engine = ResearchForensicEngine.get_instance()

    # Modified evidence simulation
    mod_result = engine.reconstruct_research_result("marriage", simulate_modified_evidence=True)
    assert mod_result.verdict == ForensicVerdict.MODIFIED_EVIDENCE_DETECTED
    assert len(mod_result.failed_checks) >= 1
    assert "MODIFIED_EVIDENCE_DETECTED" in mod_result.failed_checks[0]

    # Provenance break simulation
    break_result = engine.reconstruct_research_result("marriage", simulate_provenance_break=True)
    assert break_result.verdict == ForensicVerdict.PROVENANCE_BREAK
    assert break_result.provenance_intact is False
    assert len(break_result.failed_checks) >= 1
    assert "PROVENANCE_BREAK" in break_result.failed_checks[0]


def test_no_fabricated_fallback_evidence_and_incomplete_handling():
    """9 & 14. Test that evidence completeness is reported honestly without fabricated artifacts."""
    engine = ResearchForensicEngine.get_instance()
    result = engine.reconstruct_research_result("marriage")
    assert result.evidence_completeness > 0.0
    assert len(result.evidence_items) == 7  # Exactly collected items without inventing missing ones


def test_forensic_api_endpoints(api_client):
    """Test FastAPI endpoints for reconstruct, verify, report, timeline, evidence, and latest."""
    # POST /api/v1/research/forensics/reconstruct
    recon_resp = api_client.post(
        "/api/v1/research/forensics/reconstruct",
        json={"target_objective": "marriage", "snapshot_id": None, "simulate_modified_evidence": False},
    )
    assert recon_resp.status_code == 200
    recon_data = recon_resp.json()
    assert recon_data["verdict"] == "RECONSTRUCTED_WITH_ZERO_DRIFT"
    assert recon_data["hash_match"] is True
    assert len(recon_data["evidence_items"]) >= 5

    # POST /api/v1/research/forensics/verify
    verify_resp = api_client.post(
        "/api/v1/research/forensics/verify",
        json={"target_objective": "marriage"},
    )
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["verdict"] == "RECONSTRUCTED_WITH_ZERO_DRIFT"
    assert len(verify_data["p31_forensic_seal"]) == 64

    # GET /api/v1/research/forensics/latest
    latest_resp = api_client.get("/api/v1/research/forensics/latest?target_objective=marriage")
    assert latest_resp.status_code == 200

    # GET /api/v1/research/forensics/evidence/latest
    ev_resp = api_client.get("/api/v1/research/forensics/evidence/latest")
    assert ev_resp.status_code == 200
    assert len(ev_resp.json()) >= 5

    # GET /api/v1/research/forensics/timeline/latest
    tl_resp = api_client.get("/api/v1/research/forensics/timeline/latest")
    assert tl_resp.status_code == 200
    assert len(tl_resp.json()) >= 5
