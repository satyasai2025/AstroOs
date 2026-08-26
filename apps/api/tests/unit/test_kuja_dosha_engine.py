import pytest
from datetime import datetime, timezone
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.kuja_dosha_engine import KujaDoshaEngine


@pytest.fixture
def horoscope():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    return HoroscopeEngine(wrapper)


def test_kuja_dosha_evaluation(horoscope):
    """Evaluates Kuja Dosha profile on standard charts."""
    dt = datetime(1990, 5, 15, 8, 30, tzinfo=timezone.utc)
    chart = horoscope.generate_d1(dt, 13.0827, 80.2707, "lahiri")

    profile = KujaDoshaEngine.evaluate_chart(chart, "Rohan")
    assert profile.chart_name == "Rohan"
    assert profile.house_from_lagna is not None
    assert profile.raw_dosha_points >= 0.0
    assert len(profile.explanation) > 0


def test_kuja_dosha_cross_chart_comparison(horoscope):
    """Compares Kuja Dosha balance between two charts."""
    dt_a = datetime(1990, 5, 15, 8, 30, tzinfo=timezone.utc)
    dt_b = datetime(1992, 8, 20, 14, 15, tzinfo=timezone.utc)
    chart_a = horoscope.generate_d1(dt_a, 13.0827, 80.2707, "lahiri")
    chart_b = horoscope.generate_d1(dt_b, 18.5204, 73.8567, "lahiri")

    comp = KujaDoshaEngine.compare_charts(chart_a, chart_b, "Rohan", "Priya")
    assert comp.partner_a.chart_name == "Rohan"
    assert comp.partner_b.chart_name == "Priya"
    assert isinstance(comp.is_balanced, bool)
    assert len(comp.compatibility_verdict) > 0

