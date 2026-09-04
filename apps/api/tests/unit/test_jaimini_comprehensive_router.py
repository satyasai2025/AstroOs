"""
AstroOS — Integration & Route Tests for Jaimini Comprehensive Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import require_authenticated
from apps.api.main import app


@pytest.fixture
def client():
    app.dependency_overrides[require_authenticated] = lambda: {"sub": "jaimini_tester"}
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()


_PAYLOAD = {
    "birth_datetime_utc": "1990-05-15T08:30:00Z",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "ayanamsa": "lahiri",
    "house_system": "W",
    "scheme": "sapta_karaka",
    "max_dasha_depth": 2,
    "include_karakamsa": True,
}


def test_upapada_endpoint(client):
    res = client.post("/api/v1/jaimini/upapada", json=_PAYLOAD)
    assert res.status_code == 200
    data = res.json()
    assert "upapada_rashi" in data
    assert "second_house_status" in data
    assert "relationship_longevity_score" in data


def test_shoola_dasha_endpoint(client):
    res = client.post("/api/v1/jaimini/shoola-dasha", json=_PAYLOAD)
    assert res.status_code == 200
    data = res.json()
    assert data["system"] == "shoola"
    assert len(data["periods"]) == 12


def test_mandooka_dasha_endpoint(client):
    res = client.post("/api/v1/jaimini/mandooka-dasha", json=_PAYLOAD)
    assert res.status_code == 200
    data = res.json()
    assert data["system"] == "mandooka"
    assert len(data["periods"]) == 12


def test_expanded_yogas_endpoint(client):
    res = client.post("/api/v1/jaimini/expanded-yogas", json=_PAYLOAD)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 5


def test_event_timing_endpoint(client):
    res = client.post("/api/v1/jaimini/event-timing", json=_PAYLOAD)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_comprehensive_endpoint(client):
    res = client.post("/api/v1/jaimini/comprehensive", json=_PAYLOAD)
    assert res.status_code == 200
    data = res.json()
    assert "chara_karaka" in data
    assert "arudha" in data
    assert "shoola_dasha" in data
    assert "mandooka_dasha" in data
    assert "upapada_analysis" in data
    assert "expanded_yogas" in data
    assert "event_timing_windows" in data
