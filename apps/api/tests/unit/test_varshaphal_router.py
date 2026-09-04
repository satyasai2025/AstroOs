import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import require_authenticated
from apps.api.main import app


@pytest.fixture
def client():
    app.dependency_overrides[require_authenticated] = lambda: {"sub": "unified_platform_tester"}
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()


def test_varshaphal_endpoint_returns_complete_tajaka_payload(client):
    payload = {
        "birth_datetime_utc": "1990-05-15T10:30:00Z",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "varsha_year": 36,
        "ayanamsa": "lahiri",
        "house_system": "W",
    }
    response = client.post("/api/v1/varshaphal", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["varsha_year"] == 36
    assert "ascendant" in data
    assert "houses" in data
    assert len(data["houses"]) == 12
    assert "planets" in data
    assert "panchanga" in data
    assert "muntha" in data
    assert "tajika_aspects" in data
    assert "year_lord" in data
    assert "sahams" in data
    assert len(data["sahams"]) == 36

    # Verify new Classical Tajika additions
    assert "panchavargiya_bala" in data
    assert len(data["panchavargiya_bala"]) == 7
    for bala in data["panchavargiya_bala"]:
        assert "planet" in bala
        assert "visheshika_bala" in bala
        assert "strength_category" in bala

    assert "tajika_yogas" in data
    assert isinstance(data["tajika_yogas"], list)

    assert "mudda_dasha" in data
    assert len(data["mudda_dasha"]) > 0

    assert "patyayini_dasha" in data
    assert len(data["patyayini_dasha"]) > 0


def test_masa_pravesh_endpoint_all_12_months(client):
    payload = {
        "birth_datetime_utc": "1990-05-15T10:30:00Z",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "varsha_year": 36,
    }
    response = client.post("/api/v1/varshaphal/masa-pravesh", json=payload)
    assert response.status_code == 200
    months = response.json()

    assert len(months) == 12
    for idx, m in enumerate(months, start=1):
        assert m["month_number"] == idx
        assert "ascendant" in m
        assert "planets" in m
        assert "muntha_rashi" in m
        assert "masa_lord" in m

