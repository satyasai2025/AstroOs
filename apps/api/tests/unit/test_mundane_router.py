"""
AstroOS — Unit & Integration Tests for Mundane Astrology Router
"""

import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import require_authenticated
from apps.api.main import app


@pytest.fixture
def client():
    app.dependency_overrides[require_authenticated] = lambda: {"sub": "mundane_tester"}
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()


def test_chaitra_pratipada_endpoint(client):
    payload = {
        "country_name": "India",
        "capital_city": "New Delhi",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "year": 2026,
        "ayanamsa": "lahiri",
    }
    res = client.post("/api/v1/research/mundane/chaitra-pratipada", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["country_name"] == "India"
    assert "ascendant_rashi" in data
    assert "tenth_house_rashi" in data


def test_planetary_cabinet_endpoint(client):
    res = client.get("/api/v1/research/mundane/planetary-cabinet/2026")
    assert res.status_code == 200
    data = res.json()
    assert data["year"] == 2026
    assert len(data["ministers"]) == 9
    assert "overall_balance_score" in data


def test_eclipses_endpoint(client):
    res = client.get("/api/v1/research/mundane/eclipses/2026")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_kurma_chakra_endpoint(client):
    res = client.get("/api/v1/research/mundane/kurma-chakra")
    assert res.status_code == 200
    data = res.json()
    assert len(data["sectors"]) == 9
    assert "summary" in data


def test_national_forecast_endpoint(client):
    payload = {
        "country_name": "India",
        "capital_city": "New Delhi",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "year": 2026,
        "ayanamsa": "lahiri",
    }
    res = client.post("/api/v1/research/mundane/national-forecast", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["country_name"] == "India"
    assert len(data["bhava_evaluations"]) == 12
    assert "economic_index" in data
    assert "defense_security_index" in data
    assert "political_stability_index" in data
    assert "public_health_index" in data
