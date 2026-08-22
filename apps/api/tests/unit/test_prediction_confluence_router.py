"""
Unit Tests for Priority 8 — Prediction Confluence API Endpoints (Module 23)

Verifies:
- POST /api/v1/predictions/confluence/synthesize
- POST /api/v1/predictions/confluence/scan
- POST /api/v1/predictions/confluence/freeze-to-p7
"""

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_synthesize_endpoint_success(client):
    payload = {
        "chart_id": "test_chart_raman",
        "category": "career",
        "horizon_months": 12,
    }
    response = client.post("/api/v1/predictions/confluence/synthesize", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "synthesis" in data
    syn = data["synthesis"]
    assert syn["category"] == "career"
    assert "confluence_matrix" in syn
    assert syn["confluence_matrix"]["total_systems"] == 6
    assert len(syn["system_contributions"]) == 6
    assert "synthesized_timing_window" in syn
    assert "empirical_track_record" in syn
    assert "provenance_breakdown" in syn
    assert syn["synthesis_hash"] != ""


def test_scan_domains_endpoint_success(client):
    payload = {
        "chart_id": "test_chart_raman",
        "horizon_months": 12,
    }
    response = client.post("/api/v1/predictions/confluence/scan", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["chart_id"] == "test_chart_raman"
    assert len(data["scanned_domains"]) == 4
    categories = [d["category"] for d in data["scanned_domains"]]
    assert "career" in categories
    assert "marriage" in categories
    assert "finance" in categories
    assert "health" in categories


def test_freeze_to_p7_endpoint_success(client):
    # 1. First synthesize to generate cached synthesis
    synth_res = client.post(
        "/api/v1/predictions/confluence/synthesize",
        json={"chart_id": "test_chart_raman", "category": "career"},
    )
    assert synth_res.status_code == 200
    syn_data = synth_res.json()["synthesis"]
    synthesis_id = syn_data["synthesis_id"]

    # 2. Freeze to P7
    freeze_payload = {
        "synthesis_id": synthesis_id,
        "synthesis_payload": syn_data,
        "target_split_type": "VALIDATION",
    }
    freeze_res = client.post("/api/v1/predictions/confluence/freeze-to-p7", json=freeze_payload)
    assert freeze_res.status_code == 201

    f_data = freeze_res.json()
    assert f_data["status"] == "FROZEN_IMMUTABLE"
    assert f_data["prediction_id"].startswith("pred_")
    assert f_data["evidence_hash"] != ""
    assert f_data["technique"] == "UNIFIED_MULTI_SYSTEM_CONFLUENCE"
