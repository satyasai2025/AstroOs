"""
Jaimini router integration tests (routers/jaimini.py).

Exercises the router end-to-end via FastAPI's TestClient against a real
EphemerisWrapper (real Swiss Ephemeris data, no mocking) — same approach
as apps/api/tests/integration/test_ephemeris_wrapper_concurrency.py. No
database is involved: every Jaimini engine is stateless by design (see
jaimini_orchestrator.py's module docstring), so this router needs no DB
session override, only get_ephemeris_wrapper.

The router itself applies no auth — routers/jaimini.py has no
dependencies of its own; require_authenticated is only wired in at
main.py's app.include_router(..., dependencies=_authenticated) call, so
a router mounted directly (as here) needs no auth override either.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.config import get_settings
from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.routers.jaimini import router as jaimini_router
from apps.api.services.ephemeris_wrapper import EphemerisWrapper

_SETTINGS = get_settings()
_WRAPPER = EphemerisWrapper(ephemeris_path=_SETTINGS.EPHEMERIS_PATH)

_BODY = {
    "birth_datetime_utc": "1990-06-15T08:30:00Z",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "ayanamsa": "lahiri",
    "house_system": "W",
}


@pytest.fixture
def client():
    app = FastAPI()
    app.dependency_overrides[get_ephemeris_wrapper] = lambda: _WRAPPER
    app.include_router(jaimini_router, prefix="/api/v1")
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestJaiminiBundle:
    def test_returns_200_with_full_bundle(self, client):
        response = client.post("/api/v1/jaimini/bundle", json=_BODY)
        assert response.status_code == 200
        body = response.json()

        assert body["chara_karaka"]["scheme"] == "sapta_karaka"
        assert len(body["chara_karaka"]["karakas"]) == 7
        assert body["chara_karaka"]["atmakaraka"]["rank"] == 1
        assert body["chara_karaka"]["darakaraka"]["rank"] == 7

        assert len(body["arudha"]["padas"]) == 12
        assert body["arudha"]["arudha_lagna"]["pada_name"] == "A1"
        assert body["arudha"]["upapada_lagna"]["pada_name"] == "A12"

        assert set(body["rashi_aspect"]["matrix"].keys()) == {
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
        }

        assert body["karakamsa"] is not None
        assert len(body["karakamsa"]["relative_houses"]) == 12

        assert body["chara_dasha"]["system"] == "chara"
        assert body["narayana_dasha"]["system"] == "narayana"
        assert len(body["chara_dasha"]["periods"]) == 12
        # Narayana Dasha is a TWO-CYCLE walk (144 fixed years → 24 periods),
        # unlike Chara Dasha's single 12-sign cycle — see jaimini_orchestrator.
        assert len(body["narayana_dasha"]["periods"]) == 24

        assert len(body["yogas"]) == 5
        for yoga in body["yogas"]:
            assert "rule_id" in yoga["rule"]
            assert isinstance(yoga["is_matched"], bool)

    def test_include_karakamsa_false_omits_it(self, client):
        response = client.post("/api/v1/jaimini/bundle", json={**_BODY, "include_karakamsa": False})
        assert response.status_code == 200
        assert response.json()["karakamsa"] is None

    def test_ashta_karaka_scheme_returns_8_karakas(self, client):
        response = client.post("/api/v1/jaimini/bundle", json={**_BODY, "scheme": "ashta_karaka"})
        assert response.status_code == 200
        body = response.json()
        assert body["chara_karaka"]["scheme"] == "ashta_karaka"
        assert len(body["chara_karaka"]["karakas"]) == 8

    def test_max_dasha_depth_respected(self, client):
        response = client.post("/api/v1/jaimini/bundle", json={**_BODY, "max_dasha_depth": 1})
        assert response.status_code == 200
        body = response.json()
        assert body["chara_dasha"]["max_depth"] == 1
        assert all(len(p["sub_periods"]) == 0 for p in body["chara_dasha"]["periods"])

    def test_naive_datetime_rejected(self, client):
        response = client.post("/api/v1/jaimini/bundle", json={**_BODY, "birth_datetime_utc": "1990-06-15T08:30:00"})
        assert response.status_code == 422

    def test_latitude_out_of_range_rejected(self, client):
        response = client.post("/api/v1/jaimini/bundle", json={**_BODY, "latitude": 200.0})
        assert response.status_code == 422


class TestJaiminiArgala:
    def test_returns_200_with_4_pairs(self, client):
        response = client.post("/api/v1/jaimini/argala", json={**_BODY, "reference": "aries"})
        assert response.status_code == 200
        body = response.json()
        assert body["reference_rashi"] == "aries"
        assert body["reference_label"] == "aries"
        assert len(body["pairs"]) == 4
        assert {p["argala_house"] for p in body["pairs"]} == {2, 4, 5, 11}
        assert {p["virodhargala_house"] for p in body["pairs"]} == {12, 10, 9, 3}

    def test_planet_reference_resolves_to_its_rashi(self, client):
        bundle = client.post("/api/v1/jaimini/bundle", json=_BODY).json()
        moon_rashi = next(
            k["rashi"] for k in bundle["chara_karaka"]["karakas"] if k["planet"] == "moon"
        )
        response = client.post("/api/v1/jaimini/argala", json={**_BODY, "reference": "moon"})
        assert response.status_code == 200
        assert response.json()["reference_rashi"] == moon_rashi

    def test_unknown_reference_rejected(self, client):
        response = client.post("/api/v1/jaimini/argala", json={**_BODY, "reference": "not-a-sign"})
        assert response.status_code == 422
