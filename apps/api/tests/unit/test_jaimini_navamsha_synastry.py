import pytest
from datetime import datetime, timezone
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.jaimini_navamsha_synastry import JaiminiNavamshaSynastry


@pytest.fixture
def horoscope():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    return HoroscopeEngine(wrapper)


def test_upapada_lagna_calculation_and_alignment(horoscope):
    """Calculates Upapada Lagna and verifies cross-chart alignment."""
    dt_a = datetime(1990, 5, 15, 8, 30, tzinfo=timezone.utc)
    dt_b = datetime(1992, 8, 20, 14, 15, tzinfo=timezone.utc)
    chart_a = horoscope.generate_d1(dt_a, 13.0827, 80.2707, "lahiri")
    chart_b = horoscope.generate_d1(dt_b, 18.5204, 73.8567, "lahiri")

    ul_a = JaiminiNavamshaSynastry.calculate_upapada_rashi(chart_a)
    assert ul_a in ("aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces")

    up_compat = JaiminiNavamshaSynastry.evaluate_upapada_compatibility(chart_a, chart_b)
    assert up_compat.jaimini_compatibility_score >= 0.0
    assert len(up_compat.explanation) > 0


def test_navamsha_synastry_harmony_score(horoscope):
    """Evaluates D9 Navamsha cross-chart resonance."""
    dt_a = datetime(1990, 5, 15, 8, 30, tzinfo=timezone.utc)
    dt_b = datetime(1992, 8, 20, 14, 15, tzinfo=timezone.utc)
    chart_a = horoscope.generate_d1(dt_a, 13.0827, 80.2707, "lahiri")
    chart_b = horoscope.generate_d1(dt_b, 18.5204, 73.8567, "lahiri")

    nav_res = JaiminiNavamshaSynastry.evaluate_navamsha_synastry(chart_a, chart_b)
    assert nav_res.navamsha_harmony_score >= 0.0
    assert len(nav_res.lagna_relationship) > 0

