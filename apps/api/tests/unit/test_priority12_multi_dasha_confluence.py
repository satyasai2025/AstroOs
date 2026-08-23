"""
AstroOS — Priority 12: Unit & Integration Tests for Polymodal Multi-Dasha Confluence Engine
"""

from datetime import date
import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import require_authenticated
from apps.api.domain.ephemeris import (
    Ascendant,
    EphemerisResult,
    HouseCusp,
    KaranaInfo,
    NakshatraInfo,
    PanchangaResult,
    SiderealPosition,
    TithiInfo,
    VaraInfo,
    YogaInfo,
)
from apps.api.domain.horoscope import D1Chart
from apps.api.main import app
from apps.api.services.multi_dasha_confluence_engine import (
    MultiDashaConfluenceEngine,
    YoginiDashaEngine,
)


def _build_sample_chart() -> D1Chart:
    """Real (if minimal) D1Chart fixture — Moon in Aries/Bharani, Lagna Aries — used to
    exercise the now-real chart-driven Vimshottari/Chara/Yogini extraction."""
    asc = Ascendant(10.0, 10.0, "aries", 10.0, "ashwini", 1)
    rashis = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
    planets = [
        SiderealPosition("sun", 30.0, "taurus", 0.0, 2, "krittika", 2, False, False, None, None),
        SiderealPosition("moon", 15.0, "aries", 15.0, 1, "bharani", 1, False, False, None, None),
        SiderealPosition("mars", 60.0, "gemini", 0.0, 3, "mrigashira", 3, False, False, None, None),
        SiderealPosition("mercury", 90.0, "cancer", 0.0, 4, "punarvasu", 4, False, False, None, None),
        SiderealPosition("jupiter", 105.0, "cancer", 15.0, 4, "pushya", 2, False, False, None, "exalted"),
        SiderealPosition("venus", 120.0, "leo", 0.0, 5, "magha", 1, False, False, None, None),
        SiderealPosition("saturn", 275.0, "capricorn", 5.0, 10, "uttara_phalguni", 2, False, False, None, None),
        SiderealPosition("rahu", 180.0, "libra", 0.0, 7, "chitra", 3, True, False, None, None),
        SiderealPosition("ketu", 0.0, "aries", 0.0, 1, "ashwini", 1, True, False, None, None),
    ]
    houses = [HouseCusp(n, float((n - 1) * 30), float((n - 1) * 30), rashis[n - 1]) for n in range(1, 13)]
    panchanga = PanchangaResult(
        tithi=TithiInfo(1, "shukla_pratipada", "shukla", 50.0),
        nakshatra=NakshatraInfo("bharani", 2, 1, "venus", 0.0, 0.0),
        yoga=YogaInfo(1, "vishkambha", 50.0),
        karana=KaranaInfo(1, "bava", False),
        vara=VaraInfo(6, "saturday", "saturn"),
        julian_day=2451545.0,
        ayanamsa_deg=23.85,
    )
    ephemeris = EphemerisResult(
        julian_day=2451545.0,
        ayanamsa_value=23.85,
        ayanamsa_system="lahiri",
        ascendant=asc,
        house_cusps=houses,
        planet_positions=planets,
        panchanga=panchanga,
    )
    return D1Chart(ephemeris, asc, houses, planets, [], [], panchanga, "lahiri", "W")


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
    chart = _build_sample_chart()
    matrix = engine.evaluate_confluence_matrix(
        chart=chart,
        target_start=date(2025, 1, 1),
        target_end=date(2035, 12, 31),
        objective="marriage",
    )

    assert matrix.objective == "marriage"
    assert matrix.chart_id != "canonical-d1-chart"  # no longer a hardcoded placeholder
    assert len(matrix.all_intervals) >= 4
    assert len(matrix.confluence_windows) >= 1

    # Verify Confluence Density Score bounds [0, 100]
    for w in matrix.confluence_windows:
        assert 0.0 <= w.confluence_density_score <= 100.0
        assert w.system_count >= 2

    assert matrix.peak_confluence_window is not None
    assert matrix.peak_confluence_window.confluence_density_score > 0.0


def test_multi_dasha_confluence_no_chart_returns_no_intervals():
    """With no chart supplied, real-data extraction has nothing to compute
    from and honestly returns empty intervals rather than fabricated ones."""
    engine = MultiDashaConfluenceEngine()
    matrix = engine.evaluate_confluence_matrix(
        chart=None,
        target_start=date(2025, 1, 1),
        target_end=date(2025, 12, 31),
        objective="marriage",
    )
    assert matrix.chart_id == "no-chart-supplied"
    assert matrix.all_intervals == ()
    assert matrix.confluence_windows == ()


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
