"""
Unit tests for AstroOS KP Superpowers:
1. 100+ KP Event Master & Custom Event Evaluation
2. KP Birth Time Rectification (BTR) Engine
3. KP Real-time Ruling Planets (RP) Engine
4. 2193 Sub-Sub Lord (SSL) Reference Table
"""

from __future__ import annotations

from datetime import datetime, timezone
import pytest

from apps.api.config import get_settings
from apps.api.schemas.kp import (
    KPBTRRectifyRequest,
    KPEvaluateEventRequest,
    KPRulingPlanetsRequest,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.kp_btr_engine import KPBtrEngine
from apps.api.services.kp_rp_engine import KPRulingPlanetsEngine


@pytest.fixture(scope="module")
def ephemeris() -> EphemerisWrapper:
    settings = get_settings()
    return EphemerisWrapper(ephemeris_path=settings.EPHEMERIS_PATH, ayanamsa="lahiri")


def test_btr_rectification_engine(ephemeris: EphemerisWrapper):
    btr_engine = KPBtrEngine(ephemeris)
    nominal_dt = datetime(1990, 5, 15, 10, 30, 0, tzinfo=timezone.utc)
    
    res = btr_engine.rectify(
        nominal_datetime_utc=nominal_dt,
        latitude=28.6139,
        longitude=77.2090,
        window_minutes=5,
        step_seconds=30,
        gender="male",
        top_k=3,
    )
    
    assert res.total_candidates_scanned > 0
    assert len(res.top_candidates) <= 3
    assert res.best_candidate is not None
    assert 0.0 <= res.best_candidate.score <= 100.0
    assert len(res.best_candidate.audit_trail) > 0


def test_ruling_planets_engine(ephemeris: EphemerisWrapper):
    rp_engine = KPRulingPlanetsEngine(ephemeris)
    query_dt = datetime(2026, 8, 23, 12, 0, 0, tzinfo=timezone.utc)
    
    res = rp_engine.calculate_ruling_planets(
        query_datetime_utc=query_dt,
        latitude=19.0760,
        longitude=72.8777,
    )
    
    assert res.day_lord != ""
    assert res.ascendant_sign_lord != ""
    assert res.ascendant_star_lord != ""
    assert res.moon_sign_lord != ""
    assert res.moon_star_lord != ""
    assert len(res.ruling_planets_ordered) >= 4
    assert len(res.raw_ruling_planets) >= 3


def test_ssl_reference_table_generation():
    from apps.api.routers.kp import get_ssl_table
    import asyncio
    
    table = asyncio.run(get_ssl_table())
    assert table.total_sub_sub_lords > 2000
    assert len(table.slices) == table.total_sub_sub_lords
    
    # Check first slice (Aries / Ashwini / Ketu-Ketu-Ketu)
    first = table.slices[0]
    assert first.sign == "Aries"
    assert first.nakshatra == "Ashwini"
    assert first.star_lord == "Ketu"
    assert first.sub_lord == "Ketu"
    assert first.sub_sub_lord == "Ketu"
    assert first.start_degree == 0.0


@pytest.mark.asyncio
async def test_kp_superpowers_endpoints_integration(ephemeris: EphemerisWrapper):
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient
    from apps.api.routers.kp import router as kp_router
    from apps.api.dependencies import get_ephemeris_wrapper

    app = FastAPI()
    app.dependency_overrides[get_ephemeris_wrapper] = lambda: ephemeris
    app.include_router(kp_router, prefix="/api/v1")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Test GET /api/v1/kp/events
        resp = await client.get("/api/v1/kp/events")
        assert resp.status_code == 200
        events = resp.json()
        assert len(events) >= 400
        assert any(e["id"] == "break_in_service" and e["polarity"] == "ADVERSE" for e in events)
        assert any(e["id"] == "adopt_a_child" and e["polarity"] == "BENEFICIAL" for e in events)

        # 2. Test POST /api/v1/kp/events/evaluate
        eval_payload = {
            "birth_datetime_utc": "1990-05-15T10:30:00Z",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "event_id": "break_in_service"
        }
        resp = await client.post("/api/v1/kp/events/evaluate", json=eval_payload)
        assert resp.status_code == 200
        eval_res = resp.json()
        assert eval_res["is_adverse"] is True
        assert eval_res["promise"] in {"ADVERSE_RISK", "PARTIAL", "WEAK"}

        # 3. Test POST /api/v1/kp/btr/rectify
        btr_payload = {
            "nominal_datetime_utc": "1990-05-15T10:30:00Z",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "window_minutes": 5,
            "step_seconds": 30,
            "gender": "male"
        }
        resp = await client.post("/api/v1/kp/btr/rectify", json=btr_payload)
        assert resp.status_code == 200
        btr_res = resp.json()
        assert btr_res["total_candidates_scanned"] > 0
        assert btr_res["best_candidate"] is not None

        # 4. Test POST /api/v1/kp/ruling-planets
        rp_payload = {
            "query_datetime_utc": "2026-08-23T12:00:00Z",
            "latitude": 19.0760,
            "longitude": 72.8777
        }
        resp = await client.post("/api/v1/kp/ruling-planets", json=rp_payload)
        assert resp.status_code == 200
        rp_res = resp.json()
        assert rp_res["day_lord"] != ""
        assert len(rp_res["ruling_planets_ordered"]) >= 4

        # 5. Test GET /api/v1/kp/ssl-table
        resp = await client.get("/api/v1/kp/ssl-table")
        assert resp.status_code == 200
        ssl_res = resp.json()
        assert ssl_res["total_sub_sub_lords"] > 2000

