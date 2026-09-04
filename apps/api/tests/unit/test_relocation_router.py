"""AstroOS — Relocation analyze endpoint tests."""

import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import require_authenticated
from apps.api.main import app
from apps.api.services.technique_engine import TechniqueEngine
from apps.api.services.techniques import (  # noqa: F401
    harmonic_interpretation,
    midpoints_to_angles,
    paran_crossings,
    sun_angular,
)

PROVO_BODY = {
    "birth_utc": "1936-08-19T03:02:00Z",
    "birth_lat": 34.0195,
    "birth_lon": -118.4912,
    "target_lat": 40.2338,
    "target_lon": -111.6585,
    "ayanamsa": "tropical",
}


@pytest.fixture(autouse=True)
def ensure_fixtures_and_auth():
    paran_crossings.init_paran_crossings()
    sun_angular.init_sun_angular()
    midpoints_to_angles.init_midpoints_to_angles()
    harmonic_interpretation.init_harmonic_interpretation()
    app.dependency_overrides[require_authenticated] = lambda: {"sub": "test_user"}
    yield
    app.dependency_overrides.clear()


def test_relocation_analyze_happy_path():
    client = TestClient(app)
    response = client.post("/api/v1/relocation/analyze", json=PROVO_BODY)
    assert response.status_code == 200
    data = response.json()
    assert data["birth"]["lat"] == 34.0195
    assert data["target"]["lon"] == -111.6585
    tech_ids = {t["technique_id"] for t in data["techniques"]}
    assert {"paran_crossings", "sun_angular", "midpoints_to_angles",
            "harmonic_interpretation"} <= tech_ids
    any_triggered = any(
        t["status"] == "triggered"
        for tech in data["techniques"]
        for t in tech["triggers"]
    )
    assert any_triggered


def test_relocation_analyze_requires_auth():
    client = TestClient(app)
    app.dependency_overrides.clear()
    response = client.post("/api/v1/relocation/analyze", json=PROVO_BODY)
    assert response.status_code in (401, 403)


def test_relocation_analyze_422_on_bad_coords():
    client = TestClient(app)
    bad = dict(PROVO_BODY, target_lat=95.0)
    response = client.post("/api/v1/relocation/analyze", json=bad)
    assert response.status_code == 422


def test_relocation_recommend_happy_path():
    client = TestClient(app)
    req = {
        "birth_utc": "1990-01-01T12:00:00Z",
        "birth_lat": 28.6139,
        "birth_lon": 77.2090,
        "ayanamsa": "lahiri",
        "objective": "career",
        "region": "worldwide",
    }
    response = client.post("/api/v1/relocation/recommend", json=req)
    assert response.status_code == 200
    data = response.json()
    assert data["objective"] == "career"
    assert len(data["cities"]) > 5
    top_city = data["cities"][0]
    assert "overall_score" in top_city
    assert "domain_scores" in top_city
    assert "key_influences" in top_city
    assert "why_points" in top_city
    assert top_city["overall_score"] >= 50

