"""
AstroOS - Unit & Integration Tests for Synastry & Compatibility Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import require_authenticated
from apps.api.main import app


@pytest.fixture
def client():
    app.dependency_overrides[require_authenticated] = lambda: {"sub": "synastry_tester"}
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_payload():
    return {
        "chart_a_birth": {
            "name": "Rohan",
            "datetime_utc": "1990-05-15T08:30:00Z",
            "latitude": 13.0827,
            "longitude": 80.2707,
            "ayanamsa": "lahiri",
        },
        "chart_b_birth": {
            "name": "Priya",
            "datetime_utc": "1992-08-20T14:15:00Z",
            "latitude": 18.5204,
            "longitude": 73.8567,
            "ayanamsa": "lahiri",
        },
        "relationship_type": "marriage",
    }


def test_dasa_kuta_endpoint(client):
    payload = {
        "girl_rashi": "aries",
        "girl_nakshatra": "ashwini",
        "boy_rashi": "leo",
        "boy_nakshatra": "magha",
    }
    response = client.post("/api/v1/research/synastry/dasa-kuta", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10
    assert "is_rajju_compatible" in data
    assert "is_vedha_compatible" in data


def test_kuja_dosha_endpoint(client, sample_payload):
    response = client.post("/api/v1/research/synastry/kuja-dosha", json=sample_payload)
    assert response.status_code == 200
    data = response.json()
    assert "partner_a" in data
    assert "partner_b" in data
    assert "is_balanced" in data


def test_upapada_endpoint(client, sample_payload):
    response = client.post("/api/v1/research/synastry/upapada", json=sample_payload)
    assert response.status_code == 200
    data = response.json()
    assert "ul_rashi_a" in data
    assert "jaimini_compatibility_score" in data


def test_navamsha_endpoint(client, sample_payload):
    response = client.post("/api/v1/research/synastry/navamsha", json=sample_payload)
    assert response.status_code == 200
    data = response.json()
    assert "d9_lagna_a" in data
    assert "navamsha_harmony_score" in data


def test_composite_endpoint(client, sample_payload):
    response = client.post("/api/v1/research/synastry/composite", json=sample_payload)
    assert response.status_code == 200
    data = response.json()
    assert "composite_ascendant" in data
    assert len(data["composite_planets"]) == 9


def test_full_compatibility_endpoint(client, sample_payload):
    response = client.post("/api/v1/research/synastry/full-compatibility", json=sample_payload)
    assert response.status_code == 200
    data = response.json()
    assert "ashta_kuta" in data
    assert "dasa_kuta" in data
    assert "kuja_dosha" in data
    assert "upapada_compatibility" in data
    assert "navamsha_synastry" in data
    assert "composite_chart" in data
    assert "overall_compatibility_index" in data
