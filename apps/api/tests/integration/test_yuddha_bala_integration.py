"""
AstroOS — Yuddha Bala Integration Tests (Module 9)

Exercises YuddhaBalaCalculator against real chart data computed by
EphemerisWrapper (Moshier fallback, same pattern as every other
integration test in this codebase — no live .se1 files required).

Real charts rarely have an actual planetary war (a ~1° orb conjunction
between two of the 5 eligible grahas is uncommon), so these tests focus
on structural correctness across real data rather than asserting a war
exists in any specific chart.
"""

from datetime import datetime, timezone

import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.shadbala.yuddha_bala import YuddhaBalaCalculator

_EPHE_PATH = "data/ephemeris"
_LAT = 28.6139
_LON = 77.2090


@pytest.fixture(scope="module")
def wrapper() -> EphemerisWrapper:
    return EphemerisWrapper(ephemeris_path=_EPHE_PATH)


def test_all_5_eligible_planets_computed(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    chart = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=_LAT, longitude=_LON,
    )
    calc = YuddhaBalaCalculator()
    results = calc.calculate_all(chart.planets)
    assert len(results) == 5
    assert {r.planet for r in results} == {"mars", "mercury", "jupiter", "venus", "saturn"}


def test_values_always_0_or_30_across_multiple_charts(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    calc = YuddhaBalaCalculator()
    for year in [1975, 1985, 1990, 2000, 2010]:
        chart = horoscope_engine.generate_d1(
            birth_datetime_utc=datetime(year, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
            latitude=_LAT, longitude=_LON,
        )
        results = calc.calculate_all(chart.planets)
        for r in results:
            assert r.value_shashtiamsas in (0.0, 30.0)


def test_deterministic_across_repeated_calls(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    chart = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=_LAT, longitude=_LON,
    )
    calc = YuddhaBalaCalculator()
    first = calc.calculate_all(chart.planets)
    second = calc.calculate_all(chart.planets)
    assert first == second


def test_winners_stay_within_reasonable_bound_across_charts(wrapper):
    """Sanity bound on real data: not every planet should be declared a war winner."""
    horoscope_engine = HoroscopeEngine(wrapper)
    calc = YuddhaBalaCalculator()
    for year in [1975, 1985, 1990, 2000, 2010, 2020]:
        chart = horoscope_engine.generate_d1(
            birth_datetime_utc=datetime(year, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
            latitude=_LAT, longitude=_LON,
        )
        results = calc.calculate_all(chart.planets)
        winners = [r for r in results if r.value_shashtiamsas == 30.0]
        assert len(winners) <= 2
