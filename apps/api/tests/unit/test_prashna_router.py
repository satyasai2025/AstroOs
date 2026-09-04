"""
Unit / Router tests for Prashna (Horary) FastAPI router endpoints.
"""

from __future__ import annotations
from datetime import datetime, timezone
import uuid
import pytest
from starlette.testclient import TestClient

from apps.api.main import app
from apps.api.dependencies import get_current_user_from_bearer, get_ephemeris_wrapper
from apps.api.domain.user import User, UserId, UserRole, UserStatus
from apps.api.services.ephemeris_wrapper import EphemerisWrapper

now = datetime.now(timezone.utc)
mock_user = User(
    id=UserId(uuid.UUID("00000000-0000-0000-0000-000000000001")),
    email="test@astroos.local",
    display_name="Test Researcher",
    hashed_password="mock_hashed_pw",
    role=UserRole.RESEARCHER,
    status=UserStatus.ACTIVE,
    created_at=now,
    updated_at=now,
)

@pytest.fixture
def client():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    app.dependency_overrides[get_current_user_from_bearer] = lambda: mock_user
    app.dependency_overrides[get_ephemeris_wrapper] = lambda: wrapper
    c = TestClient(app, raise_server_exceptions=True)
    yield c
    app.dependency_overrides.pop(get_current_user_from_bearer, None)
    app.dependency_overrides.pop(get_ephemeris_wrapper, None)


def test_prashna_arudha_endpoint_249(client: TestClient):
    res = client.get("/api/v1/prashna/arudha?seed_number=14&system=kp_249")
    assert res.status_code == 200
    data = res.json()
    assert data["seed_number"] == 14
    assert data["system"] == "kp_249"
    assert data["rashi"] == "aries"
    assert len(data["sign_lord"]) > 0


def test_prashna_arudha_endpoint_2193(client: TestClient):
    res = client.get("/api/v1/prashna/arudha?seed_number=108&system=kp_2193")
    assert res.status_code == 200
    data = res.json()
    assert data["seed_number"] == 108
    assert data["system"] == "kp_2193"
    assert len(data["sub_sub_lord"]) > 0


def test_prashna_arabic_parts_endpoint(client: TestClient):
    res = client.get("/api/v1/prashna/arabic-parts?latitude=18.52&longitude=73.85")
    assert res.status_code == 200
    parts = res.json()
    assert len(parts) >= 30
    names = [p["name"] for p in parts]
    assert "Fortuna" in names
    assert "Spirit" in names


def test_prashna_calculate_endpoint(client: TestClient):
    payload = {
        "name": "Kunal",
        "gender": "Male",
        "question": "Will I get selected for this job?",
        "moment_utc": datetime(2026, 8, 22, 12, 22, 0, tzinfo=timezone.utc).isoformat(),
        "latitude": 18.5204,
        "longitude": 73.8567,
        "place_name": "Pune, Maharashtra, India",
        "timezone_offset": 5.5,
        "horary_number": 14,
        "horary_system": "kp_249",
        "ayanamsa": "lahiri",
    }
    res = client.post("/api/v1/prashna/calculate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["planets"]) >= 7
    assert len(data["cusps"]) == 12
    assert len(data["ruling_planets_ct"]["entries"]) >= 4
    assert len(data["arabic_parts"]) >= 30
    assert data["judgement"]["verdict"] in ("YES", "NO", "MIXED")
    assert 0 <= data["judgement"]["confidence_percentage"] <= 100
