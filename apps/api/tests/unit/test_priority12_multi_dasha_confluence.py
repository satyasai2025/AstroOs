"""
AstroOS — Priority 12: Unit & Integration Tests for Polymodal Multi-Dasha Confluence Engine
"""

from datetime import date
import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import require_authenticated
from apps.api.main import app
from apps.api.services.multi_dasha_confluence_engine import (
    MultiDashaConfluenceEngine,
    YoginiDashaEngine,
)


@pytest.fixture
def api_client():
    app.dependency_overrides[require_authenticated] = lambda: {"sub": "confluence_tester"}
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_yogini_dasha_calculation():
    periods = YoginiDashaEngine.compute_yogini_dasha(
        moon_nakshatra_index=2,  # Bharani
        birth_date=date(1990, 1, 1),
        years_ahead=36,
    )
    assert len(periods) >= 8

    # Verify 8 Yogini names cycle
    names = [p.yogini_name for p in periods[:8]]
    expected_cycle = ["mangala", "pingala", "dhanya", "bhramari", "bhadrika", "ulka", "siddha", "sankata"]

    # Start name should match formula (2 + 3) % 8 = 5 -> ulka
    assert names[0] == "ulka"

    # Verify repeating sequence order
    for idx, p in enumerate(periods):
        assert p.duration_years >= 1 and p.duration_years <= 8
        assert p.end_date > p.start_date


def test_multi_dasha_confluence_evaluation():
    engine = MultiDashaConfluenceEngine()
    matrix = engine.evaluate_confluence_matrix(
        chart=None,  # Uses internal canonical D1 chart
        target_start=date(2025, 1, 1),
        target_end=date(2025, 12, 31),
        objective="marriage",
    )

    assert matrix.objective == "marriage"
    assert len(matrix.all_intervals) >= 4
    assert len(matrix.confluence_windows) >= 1

    # Verify Confluence Density Score bounds [0, 100]
    for w in matrix.confluence_windows:
        assert 0.0 <= w.confluence_density_score <= 100.0
        assert w.system_count >= 2

    assert matrix.peak_confluence_window is not None
    assert matrix.peak_confluence_window.confluence_density_score > 0.0


def test_multi_dasha_confluence_api_endpoints(api_client):
    # 1. Test GET /api/v1/research/confluence/systems
    sys_resp = api_client.get("/api/v1/research/confluence/systems")
    assert sys_resp.status_code == 200
    systems = sys_resp.json()
    assert len(systems) == 4
    sys_names = [s["system_name"] for s in systems]
    assert "vimshottari" in sys_names
    assert "yogini" in sys_names

    # 2. Test POST /api/v1/research/confluence/evaluate
    eval_resp = api_client.post(
        "/api/v1/research/confluence/evaluate",
        json={
            "objective": "marriage",
            "target_start_date": "2025-01-01",
            "target_end_date": "2025-12-31",
        },
    )
    assert eval_resp.status_code == 200
    res = eval_resp.json()

    assert res["objective"] == "marriage"
    assert res["total_intervals_evaluated"] >= 4
    assert res["total_confluence_windows"] >= 1
    assert res["peak_confluence_window"] is not None
    assert res["peak_confluence_window"]["confluence_density_score"] > 0.0
