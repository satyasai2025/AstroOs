from __future__ import annotations

from datetime import datetime, timezone
import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.vaiseshikamsa_engine import VaiseshikamsaEngine


@pytest.fixture
def sample_chart():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris", ayanamsa="lahiri")
    engine = HoroscopeEngine(wrapper)
    dt = datetime(1990, 5, 15, 8, 30, tzinfo=timezone.utc)
    return engine.generate_d1(dt, 13.0827, 80.2707, ayanamsa="lahiri")


def test_vaiseshikamsa_engine_calculation(sample_chart):
    engine = VaiseshikamsaEngine()
    result = engine.calculate_all(sample_chart, scheme="dasavarga")

    assert len(result.planets) == 7
    planets = {p.planet: p for p in result.planets}

    for name in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]:
        assert name in planets
        p_res = planets[name]
        assert p_res.scheme == "dasavarga"
        assert p_res.total_vargas_evaluated == 10
        assert 0 <= p_res.auspicious_varga_count <= 10
        assert 0 <= p_res.swavarga_count <= p_res.auspicious_varga_count
        assert len(p_res.placements) == 10
        assert isinstance(p_res.title, str)


def test_vaiseshikamsa_shodasavarga_scheme(sample_chart):
    engine = VaiseshikamsaEngine()
    result = engine.calculate_all(sample_chart, scheme="shodasavarga")

    assert len(result.planets) == 7
    for p in result.planets:
        assert p.scheme == "shodasavarga"
        assert p.total_vargas_evaluated == 16
        assert len(p.placements) == 16
