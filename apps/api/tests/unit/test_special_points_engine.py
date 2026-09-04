from __future__ import annotations

from datetime import datetime, timezone
import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.special_points_engine import SpecialPointsEngine


@pytest.fixture
def sample_chart():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris", ayanamsa="lahiri")
    engine = HoroscopeEngine(wrapper)
    dt = datetime(1990, 5, 15, 8, 30, tzinfo=timezone.utc)
    return engine.generate_d1(dt, 13.0827, 80.2707, ayanamsa="lahiri")


def test_bhrigu_bindu_calculation(sample_chart):
    engine = SpecialPointsEngine()
    bb = engine.compute_bhrigu_bindu(sample_chart)

    assert 0.0 <= bb.sidereal_longitude < 360.0
    assert len(bb.rashi) > 0
    assert 0.0 <= bb.rashi_degree < 30.0
    assert len(bb.nakshatra) > 0
    assert 1 <= bb.pada <= 4
    assert len(bb.nakshatra_lord) > 0
    assert len(bb.sign_lord) > 0
    assert 1 <= bb.house_number <= 12


def test_yogi_and_avayogi_calculation(sample_chart):
    engine = SpecialPointsEngine()
    yogi_res = engine.compute_yogi_points(sample_chart)

    assert 0.0 <= yogi_res.yogi_point_longitude < 360.0
    assert 0.0 <= yogi_res.avayogi_point_longitude < 360.0
    assert len(yogi_res.yogi_planet) > 0
    assert len(yogi_res.sahayogi_planet) > 0
    assert len(yogi_res.avayogi_planet) > 0

    # Invariant: Avayogi is 186° 40' from Yogi
    diff = (yogi_res.avayogi_point_longitude - yogi_res.yogi_point_longitude) % 360.0
    expected_diff = 186.0 + 40.0 / 60.0
    assert diff == pytest.approx(expected_diff, abs=1e-4)


def test_special_points_snapshot(sample_chart):
    engine = SpecialPointsEngine()
    snapshot = engine.compute_all(sample_chart)

    assert snapshot.bhrigu_bindu is not None
    assert snapshot.yogi_points is not None
    assert snapshot.rule_version == "1.0"
