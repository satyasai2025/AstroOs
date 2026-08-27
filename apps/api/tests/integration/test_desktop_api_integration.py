import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from fastapi import status

@pytest_asyncio.fixture
async def async_client():
    """
    Create an async client for testing FastAPI app endpoints.
    Uses ASGITransport to communicate directly with the app without HTTP.
    """
    from apps.api.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

@pytest.mark.asyncio
async def test_run_health_check(async_client):
    response = await async_client.get("/api/healthz")
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
@pytest.mark.skip(
    reason="Requires a live, authenticated desktop-app run: POST /api/v1/horoscope/d1 "
    "is behind JWT auth (401 without a token) and the old /api/v1/worker/shutdown "
    "endpoint no longer exists (worker pools are now in-process, not a shuttable "
    "HTTP worker). This file is a desktop smoke test for a running install, not a "
    "self-contained DB integration test — left skipped so it never misreports."
)
async def test_run_chart_generation_desktop_requires_auth(async_client):
    response = await async_client.post("/api/v1/horoscope/d1", json={
        "date": "1990-01-01",
        "time": "12:00:00",
        "latitude": 12.97,
        "longitude": 77.59,
        "timezone": "Asia/Kolkata"
    })
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_202_ACCEPTED]

@pytest.mark.asyncio
@pytest.mark.skip(
    reason="POST /api/v1/worker/shutdown does not exist — worker pools were replaced "
    "by in-process pools per the local-first architecture, so there is no HTTP worker "
    "shutdown endpoint to call. The desktop app's own shutdown is a process-level "
    "concern. Keeping the test to document the removed route, marking it skipped."
)
async def test_run_worker_shutdown_route_removed(async_client):
    response = await async_client.post("/api/v1/worker/shutdown")
    assert response.status_code == status.HTTP_200_OK

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])