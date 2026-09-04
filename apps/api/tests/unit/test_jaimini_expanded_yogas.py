"""
AstroOS — Unit Tests for Jaimini Expanded Yogas Engine
"""

from datetime import datetime, timezone
import pytest

from apps.api.services.divisional_engine import DivisionalEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.jaimini_expanded_yogas import JaiminiExpandedYogaEngine


@pytest.fixture
def sample_charts():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    horo = HoroscopeEngine(wrapper)
    div = DivisionalEngine(wrapper)
    dt = datetime(1990, 5, 15, 8, 30, tzinfo=timezone.utc)
    d1 = horo.generate_d1(dt, 28.6139, 77.2090, "lahiri")
    d9 = div.compute(dt, 28.6139, 77.2090, "D9", "lahiri")
    return d1, d9


def test_expanded_yogas_evaluation(sample_charts):
    d1, d9 = sample_charts
    engine = JaiminiExpandedYogaEngine()
    yogas = engine.evaluate_all(d1, d9, scheme="sapta_karaka")

    assert len(yogas) == 5
    rule_ids = [y.rule_id for y in yogas]
    assert "JAIMINI-RY-002" in rule_ids  # AK-PK
    assert "JAIMINI-RY-003" in rule_ids  # AmK-DK
    assert "JAIMINI-AY-001" in rule_ids  # Srimantah AL-A11
    assert "JAIMINI-AY-002" in rule_ids  # Vipareeta Arudha
    assert "JAIMINI-KY-002" in rule_ids  # Karakamsha Moksha
