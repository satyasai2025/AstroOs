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
async def test_run_chart_generation(async_client):
    response = await async_client.post("/api/v1/horoscope/d1", json={
        "date": "1990-01-01",
        "time": "12:00:00",
        "latitude": 12.97,
        "longitude": 77.59,
        "timezone": "Asia/Kolkata"
    })
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_202_ACCEPTED]

@pytest.mark.asyncio
async def test_run_worker_shutdown(async_client):
    response = await async_client.post("/api/v1/worker/shutdown")
    assert response.status_code == status.HTTP_200_OK

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])