"""
AstroOS — Nathonnata Bala Integration Tests (Module 9)

Exercises NathonnataBalaCalculator against real chart data computed by
EphemerisWrapper (Moshier fallback, same pattern as every other
integration test in this codebase — no live .se1 files required).
"""

from datetime import datetime, timezone

import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.shadbala.nathonnata_bala import NathonnataBalaCalculator

_EPHE_PATH = "data/ephemeris"
_LAT = 28.6139
_LON = 77.2090


@pytest.fixture(scope="module")
def wrapper() -> EphemerisWrapper:
    return EphemerisWrapper(ephemeris_path=_EPHE_PATH)


def test_mercury_always_scores_60(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    chart = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=_LAT, longitude=_LON,
    )
    calc = NathonnataBalaCalculator(wrapper)
    results = calc.calculate_all(chart.planets, chart.ephemeris, latitude=_LAT, longitude=_LON)
    mercury_result = next(r for r in results if r.planet == "mercury")
    assert mercury_result.value_shashtiamsas == pytest.approx(60.0)


def test_diurnal_and_nocturnal_planets_complementary(wrapper):
    """Any diurnal-favoring and nocturnal-favoring planet must sum to 60 at the same birth time."""
    horoscope_engine = HoroscopeEngine(wrapper)
    chart = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=_LAT, longitude=_LON,
    )
    calc = NathonnataBalaCalculator(wrapper)
    results = {r.planet: r.value_shashtiamsas for r in
               calc.calculate_all(chart.planets, chart.ephemeris, latitude=_LAT, longitude=_LON)}
    assert results["sun"] + results["moon"] == pytest.approx(60.0, abs=1e-4)
    assert results["jupiter"] + results["mars"] == pytest.approx(60.0, abs=1e-4)
    assert results["venus"] + results["saturn"] == pytest.approx(60.0, abs=1e-4)


def test_deterministic_across_repeated_calls(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    chart = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=_LAT, longitude=_LON,
    )
    calc = NathonnataBalaCalculator(wrapper)
    first = calc.calculate_all(chart.planets, chart.ephemeris, latitude=_LAT, longitude=_LON)
    second = calc.calculate_all(chart.planets, chart.ephemeris, latitude=_LAT, longitude=_LON)
    assert first == second


def test_all_7_classical_grahas_computed(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    chart = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=_LAT, longitude=_LON,
    )
    calc = NathonnataBalaCalculator(wrapper)
    results = calc.calculate_all(chart.planets, chart.ephemeris, latitude=_LAT, longitude=_LON)
    assert len(results) == 7


def test_values_within_bounds_across_multiple_birth_times(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    calc = NathonnataBalaCalculator(wrapper)
    for hour in [2, 8, 10, 14, 18, 22]:
        chart = horoscope_engine.generate_d1(
            birth_datetime_utc=datetime(1990, 6, 15, hour, 0, 0, tzinfo=timezone.utc),
            latitude=_LAT, longitude=_LON,
        )
        results = calc.calculate_all(chart.planets, chart.ephemeris, latitude=_LAT, longitude=_LON)
        for r in results:
            assert 0.0 <= r.value_shashtiamsas <= 60.0
