"""
Unit & Integration Tests for Priority 14 — Inverse Natal Profiling & Chart Rectification Engine
"""

import pytest
from datetime import datetime, timezone, date
from fastapi.testclient import TestClient

from apps.api.domain.rectification import EventType, LifeEventRecord
from apps.api.main import app
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.rectification_engine import RectificationEngine


def test_rectification_engine_search():
    """Verify RectificationEngine searches temporal candidates and scores event likelihood."""
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    engine = RectificationEngine(wrapper=wrapper)

    base_dt = datetime(1990, 5, 15, 8, 30, tzinfo=timezone.utc)
    events = [
        LifeEventRecord(
            event_id="evt-1",
            event_type=EventType.MARRIAGE,
            event_date=date(2018, 11, 25),
            significance_weight=1.5,
            description="Marriage milestone",
        ),
        LifeEventRecord(
            event_id="evt-2",
            event_type=EventType.CAREER_RISE,
            event_date=date(2021, 4, 1),
            significance_weight=1.2,
            description="VP Promotion",
        ),
    ]

    result = engine.search_rectification(
        base_datetime_utc=base_dt,
        latitude=13.0827,
        longitude=80.2707,
        events=events,
        window_minutes=5,
        step_seconds=60,
        ayanamsa="lahiri",
    )

    assert result.total_candidates_evaluated == 11  # -5 to +5 mins at 1 min steps
    assert len(result.top_candidates) > 0
    assert result.best_candidate is not None
    assert result.best_candidate.composite_posterior_probability > 0.0
    assert len(result.best_candidate.event_evaluations) == 2


def test_rectification_fastapi_endpoints():
    """Verify FastAPI router endpoints for Rectification search and metadata."""
    client = TestClient(app)

    # 1. Test /api/v1/research/rectification/event-types
    res_types = client.get("/api/v1/research/rectification/event-types")
    assert res_types.status_code == 200
    types_data = res_types.json()
    assert len(types_data["event_types"]) >= 7

    # 2. Test /api/v1/research/rectification/search
    req = {
        "base_datetime_utc": "1990-05-15T08:30:00Z",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "window_minutes": 2,
        "step_seconds": 60,
        "ayanamsa": "lahiri",
        "events": [
            {
                "event_id": "evt-1",
                "event_type": "marriage",
                "event_date": "2018-11-25",
                "significance_weight": 1.5,
                "description": "Marriage",
            }
        ],
    }
    res_search = client.post("/api/v1/research/rectification/search", json=req)
    assert res_search.status_code == 200
    data = res_search.json()
    assert data["total_candidates_evaluated"] == 5
    assert len(data["top_candidates"]) > 0
    assert data["best_candidate"] is not None
    assert data["best_candidate"]["composite_posterior_probability"] > 0.0
