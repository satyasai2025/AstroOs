from __future__ import annotations

from datetime import datetime, timezone
import pytest

from apps.api.services.avastha_engine import AvasthaEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine


@pytest.fixture
def sample_chart():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris", ayanamsa="lahiri")
    engine = HoroscopeEngine(wrapper)
    dt = datetime(1990, 5, 15, 8, 30, tzinfo=timezone.utc)
    return engine.generate_d1(dt, 13.0827, 80.2707, ayanamsa="lahiri")


def test_avastha_engine_all_four_systems(sample_chart):
    engine = AvasthaEngine()
    results = engine.compute_all(sample_chart.planets, lagna_rashi_num=3, ghati_from_sunrise=5.2)

    assert len(results) >= 7
    for res in results:
        # 1. Baladi
        assert res.baladi_avastha in ["Bala", "Kumara", "Yuva", "Vriddha", "Mrita"]
        assert len(res.baladi_trace) > 0

        # 2. Deeptadi
        assert res.deeptadi_avastha in [
            "Deepta", "Swastha", "Pramudita", "Shanta", "Sama", "Dukhita", "Vikala", "Kopa"
        ]
        assert len(res.deeptadi_trace) > 0

        # 3. Jagradadi
        assert res.jagradadi_avastha in ["Jagrata", "Swapna", "Sushupti"]
        assert len(res.jagradadi_trace) > 0

        # 4. Sayanadi
        assert res.sayanadi_avastha in [
            "Shayana", "Upaveshana", "Netrapani", "Prakasana", "Gamana",
            "Agamana", "Sabha", "Bhojana", "Nrityalipsa", "Kautuka", "Nidra", "Sushupti"
        ]
        assert len(res.sayanadi_trace) > 0


def test_jagradadi_dignity_mapping(sample_chart):
    engine = AvasthaEngine()
    results = engine.compute_all(sample_chart.planets)
    by_planet = {r.planet: r for r in results}

    sun_res = by_planet.get("sun")
    assert sun_res is not None
    assert sun_res.jagradadi_avastha in ["Jagrata", "Swapna", "Sushupti"]
