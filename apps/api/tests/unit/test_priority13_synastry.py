"""
Unit & Integration Tests for Priority 13 — Inter-Chart Synastry, Ashta-Kuta Compatibility & Joint Confluence
"""

import pytest
from datetime import datetime, timezone, date
from fastapi.testclient import TestClient

from apps.api.domain.synastry import KutaName
from apps.api.main import app
from apps.api.services.synastry_engine import AshtaKutaEngine, SynastryEngine
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper


def test_ashtakuta_calculation_and_cancellations():
    """Verify classical 36-Guna calculation and Nadi/Bhakoot Parihara rules."""
    # Test Case 1: Aries/Ashwini (Pada 1) vs Leo/Magha (Pada 1)
    # Varna: Kshatriya vs Kshatriya (1/1)
    # Vashya: Chatushpada vs Vanachara (1/2)
    # Gana: Deva vs Rakshasa (Cancelled by Graha Maitri Mars/Sun friends -> 6/6)
    # Bhakoot: 1/5 axis (Cancelled by Sun/Mars friends -> 7/7)
    # Nadi: Aadi vs Antya (8/8)
    evals, pariharas = AshtaKutaEngine.evaluate(
        moon_a_rashi="aries",
        moon_a_nakshatra="ashwini",
        moon_a_pada=1,
        moon_b_rashi="leo",
        moon_b_nakshatra="magha",
        moon_b_pada=1,
    )
    assert len(evals) == 8
    total_pts = sum(k.obtained_points for k in evals)
    assert total_pts >= 25.0  # High compatibility score

    # Check Nadi Dosha cancellation with same Nakshatra different Pada
    nadi_evals, nadi_pariharas = AshtaKutaEngine.evaluate(
        moon_a_rashi="aries",
        moon_a_nakshatra="ashwini",
        moon_a_pada=1,
        moon_b_rashi="aries",
        moon_b_nakshatra="ashwini",
        moon_b_pada=2,
    )
    nadi_kuta = next(k for k in nadi_evals if k.kuta == KutaName.NADI)
    assert nadi_kuta.obtained_points == 8.0
    assert nadi_kuta.is_mitigated is True

    # Check Bhakoot cancellation for Aries/Scorpio (same lord Mars)
    bhakoot_evals, _ = AshtaKutaEngine.evaluate(
        moon_a_rashi="aries",
        moon_a_nakshatra="ashwini",
        moon_a_pada=1,
        moon_b_rashi="scorpio",
        moon_b_nakshatra="anuradha",
        moon_b_pada=1,
    )
    bhakoot_kuta = next(k for k in bhakoot_evals if k.kuta == KutaName.BHAKOOT)
    assert bhakoot_kuta.obtained_points == 7.0
    assert bhakoot_kuta.is_mitigated is True


def test_synastry_matrix_engine():
    """Verify composite SynastryEngine generates aspects, overlays, and joint timing."""
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    horoscope = HoroscopeEngine(wrapper)
    engine = SynastryEngine()

    dt_a = datetime(1990, 5, 15, 8, 30, tzinfo=timezone.utc)
    dt_b = datetime(1992, 8, 20, 14, 15, tzinfo=timezone.utc)

    chart_a = horoscope.generate_d1(dt_a, 13.0827, 80.2707, "lahiri")
    chart_b = horoscope.generate_d1(dt_b, 18.5204, 73.8567, "lahiri")

    matrix = engine.evaluate_synastry(
        chart_a=chart_a,
        chart_b=chart_b,
        chart_a_name="Rohan",
        chart_b_name="Priya",
        target_start=date(2026, 1, 1),
        target_end=date(2027, 12, 31),
        objective="marriage",
    )

    assert matrix.chart_a_name == "Rohan"
    assert matrix.chart_b_name == "Priya"
    assert len(matrix.ashta_kuta_evaluations) == 8
    assert matrix.total_guna_obtained > 0.0
    assert len(matrix.inter_chart_aspects) >= 0
    assert len(matrix.cross_house_overlays) > 0
    assert len(matrix.joint_confluence_windows) > 0
    assert matrix.joint_confluence_windows[0].joint_confluence_density > 0.0


def test_synastry_fastapi_endpoints():
    """Verify FastAPI router endpoints for Ashta-Kuta and Synastry Matrix."""
    client = TestClient(app)

    # 1. Test /api/v1/research/synastry/kutas
    kutas_res = client.get("/api/v1/research/synastry/kutas")
    assert kutas_res.status_code == 200
    k_data = kutas_res.json()
    assert len(k_data["ashta_kutas"]) == 8
    assert k_data["total_max_points"] == 36.0

    # 2. Test /api/v1/research/synastry/ashtakuta
    ak_req = {
        "partner_a_rashi": "aries",
        "partner_a_nakshatra": "ashwini",
        "partner_a_pada": 1,
        "partner_b_rashi": "leo",
        "partner_b_nakshatra": "magha",
        "partner_b_pada": 1,
    }
    ak_res = client.post("/api/v1/research/synastry/ashtakuta", json=ak_req)
    assert ak_res.status_code == 200
    ak_data = ak_res.json()
    assert ak_data["total_guna_obtained"] >= 20.0
    assert len(ak_data["evaluations"]) == 8
    assert len(ak_data["dosha_pariharas"]) > 0

    # 3. Test /api/v1/research/synastry/matrix
    matrix_req = {
        "chart_a_birth": {
            "name": "Partner A",
            "datetime_utc": "1990-05-15T08:30:00Z",
            "latitude": 13.0827,
            "longitude": 80.2707,
            "ayanamsa": "lahiri",
        },
        "chart_b_birth": {
            "name": "Partner B",
            "datetime_utc": "1992-08-20T14:15:00Z",
            "latitude": 18.5204,
            "longitude": 73.8567,
            "ayanamsa": "lahiri",
        },
        "target_start_date": "2026-01-01",
        "target_end_date": "2027-12-31",
        "objective": "marriage",
    }
    m_res = client.post("/api/v1/research/synastry/matrix", json=matrix_req)
    assert m_res.status_code == 200
    m_data = m_res.json()
    assert m_data["chart_a_name"] == "Partner A"
    assert m_data["chart_b_name"] == "Partner B"
    assert len(m_data["ashta_kuta_evaluations"]) == 8
    assert len(m_data["joint_confluence_windows"]) > 0
