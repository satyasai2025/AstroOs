"""
AstroOS — Unit Tests for Jaimini Event Timing Engine
"""

from datetime import date, datetime, timezone
import pytest

from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.jaimini_dasha_adapter import JaiminiDashaAdapter
from apps.api.services.jaimini_event_timing_engine import JaiminiEventTimingEngine


@pytest.fixture
def chart_and_dasha():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    horo = HoroscopeEngine(wrapper)
    dasha_adapter = JaiminiDashaAdapter(DashaEngine(wrapper))
    dt = datetime(1990, 5, 15, 8, 30, tzinfo=timezone.utc)
    d1 = horo.generate_d1(dt, 28.6139, 77.2090, "lahiri")
    chara = dasha_adapter.compute_chara(dt, 28.6139, 77.2090, "lahiri")
    return d1, chara


def test_event_timing_generation(chart_and_dasha):
    d1, chara = chart_and_dasha
    engine = JaiminiEventTimingEngine()
    windows = engine.generate_timing_windows(d1, date(1990, 5, 15), chara, scheme="sapta_karaka")

    assert len(windows) > 0
    categories = [w.event_category for w in windows]
    assert any("Career" in c or "Marriage" in c or "Wealth" in c or "Health" in c for c in categories)

    for w in windows:
        assert 0.0 <= w.probability_score <= 100.0
        assert len(w.trigger_reasons) > 0
        assert len(w.classical_sutra) > 0
