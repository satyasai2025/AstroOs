"""
Unit tests for Samskara & Classical Electional Muhurta Engine (E01–E35)
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.muhurta_samskara_engine import MuhurtaSamskaraEngine, SamskaraEvaluationResult


@pytest.fixture
def ephem():
    return EphemerisWrapper(ephemeris_path="data/ephemeris")


def test_list_all_samskaras():
    samskaras = MuhurtaSamskaraEngine.list_samskaras()
    assert len(samskaras) >= 14
    codes = {s["code"] for s in samskaras}
    assert "E17_Vivaah" in codes
    assert "E21_GrihPravesh" in codes
    assert "E19_Upnayan" in codes
    assert "E23_Mundan" in codes
    assert "E16_Yatra" in codes
    assert "E30_BeejVapana" in codes
    assert "E34_Vrishti" in codes


def test_evaluate_vivah_samskara(ephem):
    # Test a target datetime (e.g. 2026-05-15 08:30 UTC)
    dt = datetime(2026, 5, 15, 8, 30, 0, tzinfo=timezone.utc)
    res = MuhurtaSamskaraEngine.evaluate(
        samskara_code="E17_Vivaah",
        dt=dt,
        lat=28.6139,
        lon=77.2090,
        ephem=ephem,
    )
    assert isinstance(res, SamskaraEvaluationResult)
    assert res.samskara_code == "E17_Vivaah"
    assert res.samskara_name == "Vivaah Samskara (Marriage Ceremony)"
    assert 0.0 <= res.suitability_score <= 100.0
    assert res.tithi_name != ""
    assert res.nakshatra_name != ""
    assert res.lagna_rashi != ""


def test_evaluate_grih_pravesh(ephem):
    dt = datetime(2026, 6, 20, 10, 0, 0, tzinfo=timezone.utc)
    res = MuhurtaSamskaraEngine.evaluate(
        samskara_code="E21_GrihPravesh",
        dt=dt,
        lat=19.0760,
        lon=72.8777,
        ephem=ephem,
    )
    assert res.samskara_code == "E21_GrihPravesh"
    assert res.category == "vastu_election"


def test_invalid_samskara_code(ephem):
    dt = datetime(2026, 5, 15, 8, 30, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="Unknown Samskara code"):
        MuhurtaSamskaraEngine.evaluate(
            samskara_code="E99_NonExistent",
            dt=dt,
            lat=28.6139,
            lon=77.2090,
            ephem=ephem,
        )
