"""
Unit tests for Vimshottari True-Tithi vs Solar Dasha Comparative Engine.
"""

from datetime import datetime, timezone
import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.vimshottari_tithi_engine import (
    VimshottariTithiEngine,
    datetime_to_jd,
    jd_to_datetime,
)


@pytest.fixture(scope="module")
def engine():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    return VimshottariTithiEngine(ephemeris_wrapper=wrapper)


def test_datetime_jd_roundtrip():
    dt = datetime(1985, 4, 15, 14, 30, 25, 500000, tzinfo=timezone.utc)
    jd = datetime_to_jd(dt)
    dt_recovered = jd_to_datetime(jd)
    # Precision should match to within 1 millisecond
    diff_seconds = abs((dt - dt_recovered).total_seconds())
    assert diff_seconds < 0.002, f"Roundtrip error: {diff_seconds}s"


def test_true_tithi_root_finding(engine):
    birth_dt = datetime(1990, 8, 15, 6, 0, 0, tzinfo=timezone.utc)
    birth_jd = datetime_to_jd(birth_dt)
    
    # 30 tithis (1 synodic month) from birth
    target_tithis = 30.0
    jd_after_1m = engine.find_jd_for_cumulative_tithis(birth_jd, target_tithis)
    days_elapsed = jd_after_1m - birth_jd
    
    # Synodic month is between 29.2 and 29.8 days
    assert 29.2 < days_elapsed < 29.8, f"Synodic month length abnormal: {days_elapsed} days"
    
    # Verify elongation at target JD is exactly the same phase angle
    e_birth = engine.get_instantaneous_elongation(birth_jd)
    e_target = engine.get_instantaneous_elongation(jd_after_1m)
    diff = abs(e_target - e_birth)
    if diff > 180:
        diff = 360 - diff
    assert diff < 0.01, f"Elongation mismatch: {diff}°"


def test_vimshottari_timeline_modes(engine):
    birth_dt = datetime(1980, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    
    solar = engine.compute_timeline(birth_dt, mode="solar_365", max_depth=2)
    savana = engine.compute_timeline(birth_dt, mode="savana_360", max_depth=2)
    chaandra = engine.compute_timeline(birth_dt, mode="chaandra_mean_354", max_depth=2)
    true_tithi = engine.compute_timeline(birth_dt, mode="true_tithi", max_depth=2)
    
    assert len(solar.mahadashas) == 9
    assert len(savana.mahadashas) == 9
    assert len(chaandra.mahadashas) == 9
    assert len(true_tithi.mahadashas) == 9
    
    # Check that all start on birth_dt
    for timeline in (solar, savana, chaandra, true_tithi):
        assert timeline.mahadashas[0].start_dt.date() == birth_dt.date()
        
    # Check that cumulative true_tithi dasha runs faster (shorter solar calendar time) than solar 365.25
    solar_end_jd = solar.mahadashas[-1].end_jd
    true_tithi_end_jd = true_tithi.mahadashas[-1].end_jd
    
    # 120 Chandra years is ~116.4 Solar years, so difference should be ~3.6 solar years (~1300 days)
    drift_days = solar_end_jd - true_tithi_end_jd
    assert 1200 < drift_days < 1400, f"Expected ~1300 days drift over full cycle, got {drift_days}"


def test_comparison_report(engine):
    birth_dt = datetime(1995, 6, 21, 18, 30, 0, tzinfo=timezone.utc)
    report = engine.compare_all_models(birth_dt)
    
    assert len(report.comparisons) == 9
    for comp in report.comparisons:
        assert "mahadasha" in comp
        assert "drift_true_tithi_vs_solar_days" in comp
        assert "astronomical_jitter_vs_mean_hours" in comp
        # Drift should be negative (True Tithi finishes earlier in Gregorian calendar than 365.25 solar year)
        assert comp["drift_true_tithi_vs_solar_days"] <= 0.0
