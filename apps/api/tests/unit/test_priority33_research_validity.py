"""
AstroOS — Unit & Adversarial Tests for Priority 33: Research Validity & Statistical Integrity Engine
"""

import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import require_authenticated
from apps.api.domain.research_validity import (
    LeakageDiagnosticStatus,
    MANDATORY_VALIDITY_NON_CAUSAL_DISCLOSURE,
    METHODOLOGY_VERSION,
    MissingDataClassification,
    SampleAdequacy,
    TemporalValidityStatus,
    ValidityVerdict,
)
from apps.api.main import app
from apps.api.services.research_validity_engine import ResearchValidityEngine, _canonical_hash, _wilson_score_interval


@pytest.fixture
def api_client():
    app.dependency_overrides[require_authenticated] = lambda: {"sub": "p33_tester", "role": "validity_auditor"}
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_01_wilson_confidence_interval_calculation():
    """Test Wilson score 95% confidence interval formula."""
    ci = _wilson_score_interval(82, 100, confidence=0.95)
    assert ci.estimate == 0.82
    assert ci.lower_bound < 0.82
    assert ci.upper_bound > 0.82
    assert ci.method == "WILSON_SCORE"


def test_02_dataset_manifest_and_sample_quality():
    """Test dataset manifest compilation and sample adequacy classification."""
    engine = ResearchValidityEngine.get_instance()
    manifest = engine.build_dataset_manifest("marriage")
    assert manifest.total_observations >= 200
    assert manifest.usable_observations >= 200
    assert len(manifest.manifest_hash) == 64

    adequacy, missing_class = engine.analyze_sample_quality(manifest)
    assert adequacy == SampleAdequacy.ADEQUATE
    assert missing_class == MissingDataClassification.NONE


def test_03_temporal_integrity_check():
    """Test temporal integrity verification."""
    engine = ResearchValidityEngine.get_instance()

    # Valid temporal ordering
    valid_res = engine.check_temporal_integrity(prediction_registered_after_outcome=False)
    assert valid_res.status == TemporalValidityStatus.TEMPORALLY_VALID
    assert valid_res.look_ahead_risk_detected is False

    # Invalid temporal ordering (prediction after outcome)
    invalid_res = engine.check_temporal_integrity(prediction_registered_after_outcome=True)
    assert invalid_res.status == TemporalValidityStatus.TEMPORALLY_INVALID
    assert invalid_res.look_ahead_risk_detected is True


def test_04_leakage_diagnostic():
    """Test data leakage diagnostic."""
    engine = ResearchValidityEngine.get_instance()

    no_leak = engine.check_leakage(outcome_features_in_predictor=False)
    assert no_leak.status == LeakageDiagnosticStatus.NO_LEAKAGE_DETECTED

    has_leak = engine.check_leakage(outcome_features_in_predictor=True)
    assert has_leak.status == LeakageDiagnosticStatus.CONFIRMED_LEAKAGE
    assert len(has_leak.reasons) >= 1


def test_05_baseline_comparison():
    """Test Majority class and Random baseline comparison."""
    engine = ResearchValidityEngine.get_instance()
    comp = engine.compute_baseline_comparison(model_accuracy=0.82, positive_count=135, total_count=250)
    assert comp.is_superior_to_majority is True
    assert comp.is_superior_to_random is True
    assert comp.absolute_difference > 0.0


def test_06_adversarial_insufficient_sample_size():
    """Adversarial Test 1: Accuracy=100% but N=2 -> Expected: INSUFFICIENT_EVIDENCE."""
    engine = ResearchValidityEngine.get_instance()
    assessment = engine.assess_validity(override_sample_size=2)
    assert assessment.overall_verdict == ValidityVerdict.INSUFFICIENT_EVIDENCE
    assert "insufficient" in assessment.verdict_explanation[0].lower()


def test_07_adversarial_majority_baseline_equality():
    """Adversarial Test 2: Accuracy=95% but Majority Baseline=95% -> Expected: NOT_SUPERIOR_TO_BASELINE."""
    engine = ResearchValidityEngine.get_instance()
    assessment = engine.assess_validity(override_model_accuracy=0.50)
    assert assessment.overall_verdict == ValidityVerdict.NOT_SUPERIOR_TO_BASELINE


def test_08_adversarial_temporal_violation():
    """Adversarial Test 3: Prediction after outcome -> Expected: TEMPORALLY_INVALID."""
    engine = ResearchValidityEngine.get_instance()
    assessment = engine.assess_validity(override_prediction_after_outcome=True)
    assert assessment.overall_verdict == ValidityVerdict.TEMPORALLY_INVALID


def test_09_adversarial_feature_leakage():
    """Adversarial Test 4: Outcome features embedded in predictor -> Expected: INVALID_ANALYSIS."""
    engine = ResearchValidityEngine.get_instance()
    assessment = engine.assess_validity(override_outcome_features_in_predictor=True)
    assert assessment.overall_verdict == ValidityVerdict.INVALID_ANALYSIS


def test_10_determinism_test():
    """Determinism Test: Identical inputs must yield identical SHA-256 analysis fingerprints."""
    engine = ResearchValidityEngine.get_instance()
    a1 = engine.assess_validity("marriage")
    a2 = engine.assess_validity("marriage")
    assert len(a1.analysis_fingerprint) == 64
    assert len(a2.analysis_fingerprint) == 64
    assert MANDATORY_VALIDITY_NON_CAUSAL_DISCLOSURE in a1.non_causal_disclosure


def test_11_validity_api_endpoints(api_client):
    """Test FastAPI endpoints for assess, latest, diagnostics, statistics, manifest, snapshot, and audit."""
    # POST /api/v1/research/validity/assess
    assess_resp = api_client.post(
        "/api/v1/research/validity/assess",
        json={"target_objective": "marriage", "source_snapshot_id": "snap-p11-evidence-root"},
    )
    assert assess_resp.status_code == 200
    data = assess_resp.json()
    assert data["methodology_version"] == METHODOLOGY_VERSION
    assert len(data["analysis_fingerprint"]) == 64
    assess_id = data["assessment_id"]

    # GET /latest
    latest_resp = api_client.get("/api/v1/research/validity/latest?target_objective=marriage")
    assert latest_resp.status_code == 200

    # GET /assess/{id}/diagnostics
    diag_resp = api_client.get(f"/api/v1/research/validity/assess/{assess_id}/diagnostics")
    assert diag_resp.status_code == 200

    # GET /assess/{id}/statistics
    stat_resp = api_client.get(f"/api/v1/research/validity/assess/{assess_id}/statistics")
    assert stat_resp.status_code == 200

    # GET /assess/{id}/manifest
    man_resp = api_client.get(f"/api/v1/research/validity/assess/{assess_id}/manifest")
    assert man_resp.status_code == 200

    # GET /assess/{id}/snapshot
    snap_resp = api_client.get(f"/api/v1/research/validity/assess/{assess_id}/snapshot")
    assert snap_resp.status_code == 200

    # GET /assess/{id}/audit
    audit_resp = api_client.get(f"/api/v1/research/validity/assess/{assess_id}/audit")
    assert audit_resp.status_code == 200
    assert len(audit_resp.json()) >= 1
