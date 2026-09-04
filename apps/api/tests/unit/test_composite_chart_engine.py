import pytest
from datetime import datetime, timezone
from apps.api.services.composite_chart_engine import CompositeChartEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine


@pytest.fixture
def horoscope():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    return HoroscopeEngine(wrapper)


def test_shortest_arc_midpoint():
    """Shortest arc midpoint between 10° and 30° is 20°; between 350° and 10° is 0°."""
    assert CompositeChartEngine.shortest_arc_midpoint(10.0, 30.0) == pytest.approx(20.0, abs=1e-4)
    assert CompositeChartEngine.shortest_arc_midpoint(350.0, 10.0) == pytest.approx(0.0, abs=1e-4)


def test_composite_chart_generation(horoscope):
    """Generates complete composite chart with Ascendant and 9 planets."""
    dt_a = datetime(1990, 5, 15, 8, 30, tzinfo=timezone.utc)
    dt_b = datetime(1992, 8, 20, 14, 15, tzinfo=timezone.utc)
    chart_a = horoscope.generate_d1(dt_a, 13.0827, 80.2707, "lahiri")
    chart_b = horoscope.generate_d1(dt_b, 18.5204, 73.8567, "lahiri")

    comp = CompositeChartEngine.calculate_composite_chart(chart_a, chart_b, "Partner A", "Partner B")
    assert comp.composite_ascendant.sidereal_longitude >= 0.0
    assert len(comp.composite_planets) >= 7
    assert len(comp.relationship_purpose_summary) > 0

