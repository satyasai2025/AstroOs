"""
Unit tests for Ghati, Dinamana & Kula-Muhurta Engine.
"""

from datetime import datetime, timezone
import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.ghati_dinamana_engine import GhatiDinamanaEngine


@pytest.fixture(scope="module")
def engine():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    return GhatiDinamanaEngine(ephemeris_wrapper=wrapper)


def test_dinamana_calculation(engine):
    # Summer Solstice in Delhi: Days are longer than 12 hours
    delhi_lat, delhi_lon = 28.6139, 77.2090
    summer_dt = datetime(2026, 6, 21, 0, 0, 0, tzinfo=timezone.utc)
    res_summer = engine.compute_dinamana(summer_dt, delhi_lat, delhi_lon)
    
    assert res_summer.dinamana_hours > 13.5, f"Expected long summer day, got {res_summer.dinamana_hours}h"
    assert res_summer.ratrimana_hours < 10.5
    assert len(res_summer.day_muhurtas) == 15
    assert len(res_summer.night_muhurtas) == 15
    
    # Check Abhijit is 8th daytime muhurta
    assert res_summer.abhijit_window.index == 8
    assert res_summer.abhijit_window.name == "Abhijit"
    assert res_summer.abhijit_window.benefic is True
    
    # Check Brahma Muhurta is 29th muhurta (14th night muhurta)
    assert res_summer.brahma_muhurta_window.index == 29
    assert res_summer.brahma_muhurta_window.name == "Brahma Muhurta"
    
    # Rahu kalam duration should equal 1/8th of Dinamana
    rahu_start, rahu_end = res_summer.rahu_kalam_window
    rahu_duration_hrs = (rahu_end - rahu_start).total_seconds() / 3600.0
    assert abs(rahu_duration_hrs - (res_summer.dinamana_hours / 8.0)) < 0.01


def test_ishta_roundtrip(engine):
    delhi_lat, delhi_lon = 28.6139, 77.2090
    test_dt = datetime(2026, 3, 21, 6, 30, 0, tzinfo=timezone.utc)
    
    # Convert datetime to Ishta
    ishta = engine.datetime_to_ishta(test_dt, delhi_lat, delhi_lon)
    assert ishta.total_ghatis > 0.0
    
    # Convert Ishta back to datetime
    dt_recovered = engine.ishta_to_datetime(
        test_dt,
        delhi_lat,
        delhi_lon,
        ishta.ghatis,
        ishta.palas,
        ishta.vipalas,
    )
    diff_sec = abs((test_dt - dt_recovered).total_seconds())
    assert diff_sec < 1.0, f"Ishtakala roundtrip error: {diff_sec}s"


def test_kula_compatibility(engine):
    # Sagotra marriage dosha
    res_bad = engine.evaluate_kula_compatibility("Vivaha", gotra_user="Kashyapa", gotra_partner="Kashyapa")
    assert res_bad["is_favorable"] is False
    assert len(res_bad["issues"]) == 1
    assert "Sagotra Dosha" in res_bad["issues"][0]
    
    # Different gotras
    res_good = engine.evaluate_kula_compatibility("Vivaha", gotra_user="Kashyapa", gotra_partner="Bharadwaja")
    assert res_good["is_favorable"] is True
    assert len(res_good["issues"]) == 0
