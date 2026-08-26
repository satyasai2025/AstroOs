from __future__ import annotations

from datetime import datetime, timezone
import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.sensitive_degrees_engine import SensitiveDegreesEngine


@pytest.fixture
def sample_chart():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris", ayanamsa="lahiri")
    engine = HoroscopeEngine(wrapper)
    dt = datetime(1990, 5, 15, 8, 30, tzinfo=timezone.utc)
    return engine.generate_d1(dt, 13.0827, 80.2707, ayanamsa="lahiri")


def test_khara_lords_calculation(sample_chart):
    engine = SensitiveDegreesEngine()
    khara = engine.compute_khara_lords(sample_chart)

    assert len(khara.moon_64th_navamsha_rashi) > 0
    assert len(khara.moon_64th_navamsha_lord) > 0
    assert 0.0 <= khara.moon_64th_navamsha_longitude < 360.0

    assert len(khara.lagna_64th_navamsha_rashi) > 0
    assert len(khara.lagna_64th_navamsha_lord) > 0
    assert 0.0 <= khara.lagna_64th_navamsha_longitude < 360.0

    assert len(khara.lagna_22nd_drekkana_rashi) > 0
    assert len(khara.lagna_22nd_drekkana_lord) > 0
    assert 0.0 <= khara.lagna_22nd_drekkana_longitude < 360.0


def test_mrityu_bhaga_evaluation(sample_chart):
    engine = SensitiveDegreesEngine()
    eval_res = engine.evaluate_mrityu_bhaga("sun", "aries", 20.2, orb=1.0)

    assert eval_res.point == "sun"
    assert eval_res.rashi == "aries"
    assert eval_res.mrityu_degree == 20.0
    assert eval_res.orb_distance == pytest.approx(0.2, abs=1e-4)
    assert eval_res.is_in_mrityu_bhaga is True

    eval_inactive = engine.evaluate_mrityu_bhaga("sun", "aries", 25.0, orb=1.0)
    assert eval_inactive.is_in_mrityu_bhaga is False


def test_pushkara_evaluation(sample_chart):
    engine = SensitiveDegreesEngine()
    # Aries 21° is Pushkara Bhaga
    pushk = engine.evaluate_pushkara("sun", 21.0, "aries", 21.0, orb=1.0)
    assert pushk.is_in_pushkara_bhaga is True

    # Aries 21° is 7th Navamsha (part 6, 20° to 23°20'), which is Pushkara Navamsha
    assert pushk.is_pushkara_navamsha is True
    assert pushk.navamsha_rashi == "libra"
    assert pushk.navamsha_lord == "venus"


def test_sensitive_degrees_snapshot(sample_chart):
    engine = SensitiveDegreesEngine()
    snapshot = engine.compute_all(sample_chart)

    assert snapshot.khara_lords is not None
    assert len(snapshot.mrityu_bhagas) >= 8  # 7 planets + rahu/ketu + lagna
    assert len(snapshot.pushkara_evaluations) >= 8
    assert snapshot.rule_version == "1.0"
