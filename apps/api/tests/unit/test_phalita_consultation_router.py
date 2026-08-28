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
        "native_name": "Narendra Modi",
        "scan_start_year": 2012,
        "scan_end_year": 2016,
        "domain": "career",
        "evaluation_target_date_iso": "2014-05-16",
    }

    response = client.post("/api/v1/phalita/consultation", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["status"] == "SUCCESS"
    assert data["native_name"] == "Narendra Modi"
    assert "bhrigu_bindu" in data
    assert "sarvato_bhadra_chakra" in data
    assert "decision_timeline" in data
    assert len(data["decision_timeline"]) > 0

    first_win = data["decision_timeline"][0]
    assert "decision_tier" in first_win
    assert "explanation_hi" in first_win
    assert "explanation_en" in first_win
    assert "sav_10th_bindus" in first_win
    assert "double_transit" in first_win
