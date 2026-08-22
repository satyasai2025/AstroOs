from __future__ import annotations

import pytest
import pytest_asyncio
from datetime import datetime, timezone
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from apps.api.config import get_settings
from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.routers.kp import router as kp_router
from apps.api.security.jwt import create_access_token
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.transit_engine import TransitEngine
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.vedha_calculator import VedhaCalculator
from apps.api.services.kp_engine import KPEngine


@pytest_asyncio.fixture
async def test_app() -> FastAPI:
    application = FastAPI()
    settings = get_settings()
    wrapper = EphemerisWrapper(ephemeris_path=settings.EPHEMERIS_PATH, ayanamsa="lahiri")
    application.dependency_overrides[get_ephemeris_wrapper] = lambda: wrapper
    application.include_router(kp_router, prefix="/api/v1")
    yield application
    application.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_client(test_app: FastAPI):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def test_kp_engine_analyze_direct():
    settings = get_settings()
    wrapper = EphemerisWrapper(ephemeris_path=settings.EPHEMERIS_PATH, ayanamsa="lahiri")
    horoscope_engine = HoroscopeEngine(wrapper)
    dasha_engine = DashaEngine(wrapper)
    transit_engine = TransitEngine(
        wrapper,
        ashtakavarga_engine=AshtakavargaEngine(),
        vedha_calculator=VedhaCalculator(),
    )
    kp_engine = KPEngine()

    birth = datetime(1985, 5, 15, 8, 30, tzinfo=timezone.utc)
    transit_dt = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)

    chart = horoscope_engine.generate_d1(birth, 13.0827, 80.2707, ayanamsa="lahiri", house_system="P")
    dasha_tree = dasha_engine.compute_vimshottari(birth, 13.0827, 80.2707, ayanamsa="lahiri", house_system="P")
    transit_results = transit_engine.compute_transit(natal_chart=chart, transit_datetime_utc=transit_dt)

    result = kp_engine.analyze(chart, dasha_tree, transit_results, transit_dt)

    assert result is not None
    assert len(result.cusps) == 12
    assert len(result.timing) > 0
    assert len(result.evidence) > 0

    # Ensure dasha links have valid level strings
    for t in result.timing:
        dlink = t["dasha_link"]
        for item in dlink["chain"]:
            assert "level" in item
            assert len(item["level"]) > 0


@pytest.mark.asyncio
async def test_kp_analyze_api_endpoint(test_client: AsyncClient):
    token, _ = create_access_token("bc50cc61-9ade-49af-b301-89a66465367e", "researcher")
    response = await test_client.post(
        "/api/v1/kp/analyze",
        json={
            "birth_datetime_utc": "1985-05-15T08:30:00Z",
            "latitude": 13.0827,
            "longitude": 80.2707,
            "ayanamsa": "lahiri",
            "house_system": "P",
            "transit_datetime_utc": "2025-01-01T12:00:00Z",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "cusps" in data
    assert len(data["cusps"]) == 12
    assert "timing" in data
    assert "evidence" in data
