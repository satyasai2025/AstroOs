"""
AstroOS — Unit Tests for Jaimini Special Dashas (Shoola & Mandooka)
"""

from datetime import date, datetime, timezone
import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.jaimini_special_dashas import MandookaDashaEngine, ShoolaDashaEngine


@pytest.fixture
def sample_chart():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    horo = HoroscopeEngine(wrapper)
    dt = datetime(1990, 5, 15, 8, 30, tzinfo=timezone.utc)
    return horo.generate_d1(dt, 28.6139, 77.2090, "lahiri")


def test_shoola_dasha_calculation(sample_chart):
    engine = ShoolaDashaEngine()
    res = engine.compute(sample_chart, date(1990, 5, 15), max_depth=2)

    assert res.system == "shoola"
    assert len(res.periods) == 12
    assert res.total_cycle_years == 108

    # Each Mahadasha is exactly 9 years
    p0 = res.periods[0]
    assert (p0.end_date.year - p0.start_date.year) in (9, 10)
    assert len(p0.sub_periods) == 12


def test_mandooka_dasha_calculation(sample_chart):
    engine = MandookaDashaEngine()
    res = engine.compute(sample_chart, date(1990, 5, 15), max_depth=2)

    assert res.system == "mandooka"
    assert len(res.periods) == 12
    assert res.total_cycle_years >= 60

    p0 = res.periods[0]
    assert len(p0.sub_periods) == 12
