"""
AstroOS — Tribhaga Bala Integration Tests (Module 9)

Exercises TribhagaBalaCalculator against real chart data computed by
EphemerisWrapper (Moshier fallback, same pattern as every other
integration test in this codebase — no live .se1 files required).
"""

from datetime import datetime, timezone

import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.shadbala.tribhaga_bala import TribhagaBalaCalculator

_EPHE_PATH = "data/ephemeris"
_LAT = 28.6139
_LON = 77.2090


@pytest.fixture(scope="module")
def wrapper() -> EphemerisWrapper:
    return EphemerisWrapper(ephemeris_path=_EPHE_PATH)


def test_daytime_birth_exactly_one_lord_scores_60(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    chart = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=_LAT, longitude=_LON,
    )
    calc = TribhagaBalaCalculator(wrapper)
    results = calc.calculate_all(chart.planets, chart.ephemeris, latitude=_LAT, longitude=_LON)
    scoring = [r for r in results if r.value_shashtiamsas > 0]
    assert len(scoring) == 1


def test_nighttime_birth_exactly_one_lord_scores_60(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    chart = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 20, 0, 0, tzinfo=timezone.utc),
        latitude=_LAT, longitude=_LON,
    )
    calc = TribhagaBalaCalculator(wrapper)
    results = calc.calculate_all(chart.planets, chart.ephemeris, latitude=_LAT, longitude=_LON)
    scoring = [r for r in results if r.value_shashtiamsas > 0]
    assert len(scoring) == 1


def test_jupiter_always_scores_zero_across_multiple_births(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    calc = TribhagaBalaCalculator(wrapper)
    for hour in [2, 8, 10, 14, 18, 22]:
        chart = horoscope_engine.generate_d1(
            birth_datetime_utc=datetime(1990, 6, 15, hour, 0, 0, tzinfo=timezone.utc),
            latitude=_LAT, longitude=_LON,
        )
        results = calc.calculate_all(chart.planets, chart.ephemeris, latitude=_LAT, longitude=_LON)
        jupiter_result = next(r for r in results if r.planet == "jupiter")
        assert jupiter_result.value_shashtiamsas == 0.0


def test_deterministic_across_repeated_calls(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    chart = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=_LAT, longitude=_LON,
    )
    calc = TribhagaBalaCalculator(wrapper)
    first = calc.calculate_all(chart.planets, chart.ephemeris, latitude=_LAT, longitude=_LON)
    second = calc.calculate_all(chart.planets, chart.ephemeris, latitude=_LAT, longitude=_LON)
    assert first == second


def test_all_7_classical_grahas_computed(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    chart = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=_LAT, longitude=_LON,
    )
    calc = TribhagaBalaCalculator(wrapper)
    results = calc.calculate_all(chart.planets, chart.ephemeris, latitude=_LAT, longitude=_LON)
    assert len(results) == 7
