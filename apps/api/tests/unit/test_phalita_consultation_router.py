"""
Unit / Functional test for Phalita Prediction & Complete Consultation Router.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from apps.api.routers.phalita_prediction import router as phalita_router

app = FastAPI()
app.include_router(phalita_router)
client = TestClient(app)


def test_phalita_consultation_endpoint():
    payload = {
        "birth_date_iso": "1950-09-17T05:30:00+00:00",
        "latitude": 23.7833,
        "longitude": 72.6333,
        "native_name": "Canonical Native Profile",
        "scan_start_year": 2012,
        "scan_end_year": 2016,
        "domain": "career",
        "evaluation_target_date_iso": "2014-05-16",
    }

    response = client.post("/api/v1/phalita/consultation", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["status"] == "SUCCESS"
    assert data["native_name"] == "Canonical Native Profile"
    assert "bhrigu_bindu" in data
    assert "varga_fusion" in data
    assert "sapta_nadi_chakra" in data
    assert "sudarshana_chakra" in data
    assert data["sudarshana_chakra"]["lagna_rashi"] is not None
    assert "current_scd" in data["sudarshana_chakra"]
    assert "graha_alignments" in data["sudarshana_chakra"]
    assert "decision_timeline" in data
    assert len(data["decision_timeline"]) > 0

    assert "professional_archetypes" in data
    arch = data["professional_archetypes"]
    assert "dominant_archetype_key" in arch
    assert "dominant_score" in arch
    assert arch["dominant_score"] >= 0.0
    assert "archetype_affinities" in arch
    assert len(arch["archetype_affinities"]) == 5
    assert "total_yogas_verified" in arch

    first_win = data["decision_timeline"][0]
    assert "decision_tier" in first_win
    assert "polarity" in first_win
    assert "polarity_logic" in first_win
    assert "varga_fusion_score" in first_win
    assert "scd_annual_house" in first_win
    assert "sav_10th_bindus" in first_win
    assert "double_transit" in first_win
