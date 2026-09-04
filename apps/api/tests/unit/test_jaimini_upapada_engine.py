"""
AstroOS — Unit Tests for Jaimini Upapada Deep Analysis Engine
"""

from datetime import datetime, timezone
import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.jaimini_upapada_engine import JaiminiUpapadaAnalysisEngine


@pytest.fixture
def sample_chart():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    horo = HoroscopeEngine(wrapper)
    dt = datetime(1990, 5, 15, 8, 30, tzinfo=timezone.utc)
    return horo.generate_d1(dt, 28.6139, 77.2090, "lahiri")


def test_upapada_deep_analysis(sample_chart):
    engine = JaiminiUpapadaAnalysisEngine()
    analysis = engine.analyze(sample_chart)

    assert len(analysis.upapada_rashi) > 0
    assert len(analysis.upapada_lord) > 0
    assert len(analysis.second_house_rashi) > 0
    assert len(analysis.eighth_house_rashi) > 0
    assert 0.0 <= analysis.relationship_longevity_score <= 100.0
    assert "Jaimini Sutra" in analysis.classical_notes
