"""
AstroOS — Unified Event Timing Router Tests
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from apps.api.config import get_settings
from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.routers.unified_event_timing import router as timing_router
from apps.api.services.ephemeris_wrapper import EphemerisWrapper


@pytest_asyncio.fixture
async def app() -> FastAPI:
    application = FastAPI()
    settings = get_settings()
    wrapper = EphemerisWrapper(ephemeris_path=settings.EPHEMERIS_PATH, ayanamsa="lahiri")
    application.dependency_overrides[get_ephemeris_wrapper] = lambda: wrapper
    application.include_router(timing_router, prefix="/api/v1")
    yield application
    application.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app: FastAPI):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_analyze_event_timing_endpoint(client: AsyncClient):
    payload = {
        "birth_datetime_utc": "1992-10-24T14:30:00Z",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "ayanamsa": "lahiri",
        "house_system": "P",
        "event_type": "career",
        "start_date": "2026-01-01",
        "end_date": "2027-01-01",
        "step_days": 30,
        "chart_id": "test-chart-integration",
    }

    response = await client.post("/api/v1/event-timing/analyze", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["event_type"] == "career"
    assert data["chart_id"] == "test-chart-integration"
    assert "evaluated_moment_snapshot" in data
    assert "dasha" in data["evaluated_moment_snapshot"]
    assert "gochara" in data["evaluated_moment_snapshot"]
    assert "sbc" in data["evaluated_moment_snapshot"]
    assert "kp" in data["evaluated_moment_snapshot"]
    assert 0.0 <= data["evaluated_moment_snapshot"]["confluence_score"] <= 100.0
    assert len(data["time_series"]) > 0


@pytest.mark.asyncio
async def test_evaluate_moment_snapshot_endpoint(client: AsyncClient):
    payload = {
        "birth_datetime_utc": "1988-03-12T06:15:00Z",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "ayanamsa": "lahiri",
        "house_system": "P",
        "event_type": "marriage",
        "target_datetime_utc": "2026-11-20T18:00:00Z",
        "chart_id": "test-chart-moment",
    }

    response = await client.post("/api/v1/event-timing/moment", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["event_type"] == "marriage"
    assert data["chart_id"] == "test-chart-moment"
    snap = data["snapshot"]
    assert snap["event_type"] == "marriage"
    assert snap["kp"]["primary_cusp"] == 7
    assert 0.0 <= snap["confluence_score"] <= 100.0
