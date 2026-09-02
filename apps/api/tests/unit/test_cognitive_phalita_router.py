"""
AstroOS — Unit & API Tests for Cognitive Phalita MoE & Event Prediction REST API
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_moe_synthesize_endpoint():
    payload = {
        "birth_datetime": "1995-01-01T12:00:00Z",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "ayanamsa": "lahiri",
        "target_dasha": {
            "md": "Venus",
            "ad": "Jupiter",
            "pd": "Venus",
            "sk": "Venus",
            "pr": "Jupiter",
        },
    }

    response = client.post("/api/v1/phalita/moe/synthesize?domain=marriage", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["domain"] == "marriage"
    assert 0.0 <= data["final_cognitive_score"] <= 9.0
    assert "NatalStructuralExpert" in data["expert_breakdown"]
    assert "TemporalDashaExpert" in data["expert_breakdown"]
    assert "gating_weights" in data
    assert "conflict_resolution" in data


def test_predict_marriage_endpoint():
    payload = {
        "birth_datetime": "1990-05-15T12:00:00Z",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "ayanamsa": "lahiri",
    }
    response = client.post("/api/v1/phalita/cognitive/predict/marriage", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["event_type"] == "marriage"
    assert 0.0 <= data["cognitive_score"] <= 9.0
    assert len(data["level_assessments"]) == 5


def test_predict_career_endpoint():
    payload = {
        "birth_datetime": "1985-11-20T08:30:00Z",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "ayanamsa": "lahiri",
    }
    response = client.post("/api/v1/phalita/cognitive/predict/career", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["event_type"] == "career"
    assert 0.0 <= data["cognitive_score"] <= 9.0


def test_predict_health_endpoint():
    payload = {
        "birth_datetime": "1975-03-10T14:45:00Z",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "ayanamsa": "lahiri",
    }
    response = client.post("/api/v1/phalita/cognitive/predict/health", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["event_type"] == "health"
    assert 0.0 <= data["cognitive_score"] <= 9.0


def test_predict_accident_endpoint():
    payload = {
        "birth_datetime": "2000-08-25T22:15:00Z",
        "latitude": 22.5726,
        "longitude": 88.3639,
        "ayanamsa": "lahiri",
    }
    response = client.post("/api/v1/phalita/cognitive/predict/accident", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["event_type"] == "accident"
    assert 0.0 <= data["cognitive_score"] <= 9.0
