import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import require_authenticated
from apps.api.main import app


@pytest.fixture
def client():
    app.dependency_overrides[require_authenticated] = lambda: {"sub": "lifespan_tester"}
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()


def test_lifespan_endpoint_computes_tri_ayurdaya(client):
    payload = {
        "birth_datetime_utc": "1990-05-15T10:30:00Z",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "ayanamsa": "lahiri",
        "house_system": "W",
    }
    response = client.post("/api/v1/lifespan/tri-ayurdaya", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "pindayu" in data
    assert "amshayu" in data
    assert "nisargayu" in data
    assert "mean_lifespan_years" in data
    assert data["mean_lifespan_years"] > 10.0
    assert "consensus_category" in data
    assert data["consensus_category"] in ("ALPAYU", "MADHYAYU", "PURNAYU")

    assert "maraka_assessment" in data
    maraka = data["maraka_assessment"]
    assert "primary_maraka_lords" in maraka
    assert len(maraka["primary_maraka_lords"]) >= 1
    assert "badhaka_lord" in maraka
    assert "is_saturn_maraka_absorber" in maraka
    assert "vulnerability_index" in maraka

    assert "shastric_notes" in data
    assert len(data["shastric_notes"]) >= 3
