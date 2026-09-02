"""
Unit & Integration tests for Phalita Canonical REST API endpoints (Phase 9).
"""

from fastapi.testclient import TestClient
import pytest
from apps.api.dependencies import require_authenticated
from apps.api.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def auth_override():
    app.dependency_overrides[require_authenticated] = lambda: {"sub": "phalita_tester", "email": "test@astroos.io"}
    yield
    app.dependency_overrides.clear()


def test_canonical_synthesis_endpoint():
    payload = {
        "birth_date_iso": "1971-06-29T23:27:40Z",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "target_year": 2025,
    }
    resp = client.post("/api/v1/phalita/canonical-synthesis", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    # 1. Verify Vishamabhava Bhaavachalita houses
    assert "houses" in data
    assert len(data["houses"]) == 12
    assert "lagna_madhya_deg" in data
    assert "madhya_lagna_deg" in data

    # 2. Verify Sudarshana Chakra
    assert "sudarshana_chakra" in data
    sc = data["sudarshana_chakra"]
    assert sc["lagna_rashi"] == "Gemini"
    assert "Mercury" in sc["profiles"]

    # 3. Verify D10 Divisional Synthesis
    assert "divisional_synthesis_d10" in data
    assert "Venus" in data["divisional_synthesis_d10"]
    assert data["divisional_synthesis_d10"]["Venus"]["verdict"] == "REINFORCING"

    # 4. Verify VPC Solar Return
    assert "vpc_solar_return" in data
    vpc = data["vpc_solar_return"]
    assert vpc["target_year"] == 2025
    assert vpc["scd_annual_house"] == 7  # Age 54 SCD House H7
    assert len(vpc["monthly_entries"]) == 12

    # 5. Verify TPhalitCore Signed State
    assert "tphalit_signed_state" in data
    assert "deterministic_score" in data["tphalit_signed_state"]


def test_vpc_timeline_endpoint():
    payload = {
        "birth_date_iso": "1971-06-29T23:27:40Z",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "start_year": 2024,
        "end_year": 2027,
    }
    resp = client.post("/api/v1/phalita/vpc-timeline", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "solar_returns" in data
    assert len(data["solar_returns"]) == 4


def test_noise_diagnostics_endpoint():
    payload = {
        "latitude": 28.6139,
        "longitude": 77.2090,
        "deterministic_score": 2.5,
        "planet_block_total": 1.8,
        "residual_error": 0.3,
        "varga_opposition_index": 0.1,
    }
    resp = client.post("/api/v1/phalita/noise-diagnostics", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "dominant_noise_category" in data
    assert "is_prediction_trustworthy" in data
    assert data["dominant_noise_category"] == "CLEAN"
