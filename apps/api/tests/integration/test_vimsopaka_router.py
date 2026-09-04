"""
AstroOS — Vimsopaka Router Integration Test

Exercises POST /api/v1/vimsopaka/all end-to-end.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from apps.api.routers.vimsopaka import router as vimsopaka_router
from apps.api.services.ephemeris_wrapper import EphemerisWrapper

_EPHE_PATH = "data/ephemeris"


@pytest_asyncio.fixture
async def app() -> FastAPI:
    app = FastAPI()
    # The router's get_ephemeris_wrapper dependency reads request.app.state
    # — it must be populated (same as main.py does at startup) or the
    # endpoint errors with KeyError.
    app.state.ephemeris_wrapper = EphemerisWrapper(ephemeris_path=_EPHE_PATH)
    app.include_router(vimsopaka_router, prefix="/api/v1")
    return app


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestVimsopakaRouter:
    async def test_compute_vimsopaka_endpoint(self, client):
        """Test POST /api/v1/vimsopaka/all with valid birth data."""
        payload = {
            "birth_datetime_utc": "1990-05-15T12:00:00Z",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "ayanamsa": "lahiri",
            "house_system": "W",
        }
        response = await client.post("/api/v1/vimsopaka/all", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "planets" in data
        assert len(data["planets"]) == 7

        planet_names = {p["planet"] for p in data["planets"]}
        assert planet_names == {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"}

        sun_res = next(p for p in data["planets"] if p["planet"] == "sun")
        assert "shadvarga" in sun_res
        assert "saptavarga" in sun_res
        assert "dasavarga" in sun_res
        assert "shodasavarga" in sun_res

        shadvarga = sun_res["shadvarga"]
        assert shadvarga["scheme_name"] == "shadvarga"
        assert shadvarga["total_weight"] == 20.0
        assert 0.0 <= shadvarga["vimsopaka_score"] <= 20.0
        assert shadvarga["category"] in ["Ati Purna", "Purna", "Madhya", "Alpa"]
        assert len(shadvarga["varga_breakdown"]) == 6

        shodasavarga = sun_res["shodasavarga"]
        assert shodasavarga["scheme_name"] == "shodasavarga"
        assert shodasavarga["total_weight"] == 20.0
        assert len(shodasavarga["varga_breakdown"]) == 16
