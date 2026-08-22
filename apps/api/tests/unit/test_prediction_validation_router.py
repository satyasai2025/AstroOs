"""
Router integration tests for Prediction Validation & Backtesting API endpoints (Module 22, Priority 7)
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.services.prediction_validation_service import PredictionValidationService


@pytest.fixture(autouse=True)
def clean_service():
    svc = PredictionValidationService()
    svc.reset_for_tests()
    return svc


client = TestClient(app)


def test_create_and_get_prediction_endpoint():
    payload = {
        "chart_id": "chart_router_01",
        "subject_name": "Test Router Native",
        "technique": "KP_CSL",
        "category": "career",
        "predicted_event": "New Job Offer",
        "expected_direction": "POSITIVE_FRUCTIFICATION",
        "prediction_timestamp": datetime.now(timezone.utc).isoformat(),
        "horizon_days": 60,
        "expected_date_start": "2025-06-01T00:00:00Z",
        "expected_date_end": "2025-07-31T23:59:59Z",
        "evidence_ids": ["ev_10th_csl"],
        "dasha_evidence": {"dasha": "Mercury"},
        "transit_evidence": {},
        "kp_evidence": {},
        "sbc_evidence": {},
        "classical_rule_evidence": {},
        "varga_evidence": {},
        "ashtakavarga_evidence": {},
        "calculation_snapshot": {},
    }
    create_res = client.post("/api/v1/prediction-validation/predictions", json=payload)
    assert create_res.status_code == 201
    data = create_res.json()
    assert data["chart_id"] == "chart_router_01"
    assert len(data["evidence_hash"]) == 64

    pid = data["prediction_id"]
    get_res = client.get(f"/api/v1/prediction-validation/predictions/{pid}")
    assert get_res.status_code == 200
    assert get_res.json()["prediction_id"] == pid


def test_list_predictions_endpoint():
    res = client.get("/api/v1/prediction-validation/predictions")
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 2


def test_register_and_list_outcomes_endpoint():
    payload = {
        "chart_id": "chart_router_01",
        "subject_name": "Test Router Native",
        "category": "career",
        "observed_date": "2025-06-15T12:00:00Z",
        "actual_outcome_description": "Accepted Senior Architect position",
        "observed_direction": "POSITIVE_FRUCTIFICATION",
        "verification_status": "VERIFIED_HISTORICAL",
        "source_reference": "Offer Letter",
        "notes": "Verified",
    }
    create_res = client.post("/api/v1/prediction-validation/outcomes", json=payload)
    assert create_res.status_code == 201
    data = create_res.json()
    assert data["chart_id"] == "chart_router_01"
    assert len(data["outcome_hash"]) == 64

    list_res = client.get("/api/v1/prediction-validation/outcomes")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 2


def test_match_and_backtest_endpoints():
    # 1. Match endpoint on seeded Raman prediction
    match_res = client.post("/api/v1/prediction-validation/match", json={
        "prediction_id": "pred_raman_1936",
        "outcome_id": "out_raman_1936",
    })
    assert match_res.status_code == 200
    m_data = match_res.json()
    assert m_data["verdict"] == "MATCHED"
    assert m_data["category_matched"] is True

    # 2. Backtest endpoint
    bkt_res = client.post("/api/v1/prediction-validation/backtest", json={
        "dataset_name": "API Test Cohort",
        "temporal_split": "VALIDATION",
    })
    assert bkt_res.status_code == 200
    b_data = bkt_res.json()
    assert b_data["total_predictions"] >= 2
    assert b_data["matched_count"] >= 2
    assert "precision" in b_data["confusion_matrix"]
    assert len(b_data["confidence_interval_95"]) == 2

    # 3. Techniques endpoint
    tech_res = client.get("/api/v1/prediction-validation/techniques")
    assert tech_res.status_code == 200
    assert len(tech_res.json()) >= 2

    # 4. Audit endpoint
    audit_res = client.get("/api/v1/prediction-validation/audit/pred_raman_1936")
    assert audit_res.status_code == 200
    a_data = audit_res.json()
    assert a_data["prediction"]["prediction_id"] == "pred_raman_1936"
    assert a_data["verdict_trace"]["verdict"] == "MATCHED"
