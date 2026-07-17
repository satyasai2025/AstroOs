"""
AstroOS — Dina-Hora Bala Integration Tests (Module 9)

Exercises DinaHoraBalaCalculator against real chart data computed by
EphemerisWrapper (Moshier fallback, same pattern as every other
integration test in this codebase — no live .se1 files required).
"""

from datetime import datetime, timezone

import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.shadbala.dina_hora_bala import DinaHoraBalaCalculator

_EPHE_PATH = "data/ephemeris"
_LAT = 28.6139
_LON = 77.2090


@pytest.fixture(scope="module")
def wrapper() -> EphemerisWrapper:
    return EphemerisWrapper(ephemeris_path=_EPHE_PATH)


def test_exactly_one_planet_scores_dina_points(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    chart = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=_LAT, longitude=_LON,
    )
    calc = DinaHoraBalaCalculator(wrapper)
    results = calc.calculate_all(chart.planets, chart.ephemeris, latitude=_LAT, longitude=_LON)
    dina_matches = [
        r for r in results
        if any(t.startswith("Dina:") and "-> match" in t for t in r.trace)
    ]
    assert len(dina_matches) == 1


def test_values_always_0_15_or_30(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    calc = DinaHoraBalaCalculator(wrapper)
    for hour in [2, 8, 10, 14, 18, 22]:
        chart = horoscope_engine.generate_d1(
            birth_datetime_utc=datetime(1990, 6, 15, hour, 0, 0, tzinfo=timezone.utc),
            latitude=_LAT, longitude=_LON,
        )
        results = calc.calculate_all(chart.planets, chart.ephemeris, latitude=_LAT, longitude=_LON)
        for r in results:
            assert r.value_shashtiamsas in (0.0, 15.0, 30.0)


def test_deterministic_across_repeated_calls(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    chart = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=_LAT, longitude=_LON,
    )
    calc = DinaHoraBalaCalculator(wrapper)
    first = calc.calculate_all(chart.planets, chart.ephemeris, latitude=_LAT, longitude=_LON)
    second = calc.calculate_all(chart.planets, chart.ephemeris, latitude=_LAT, longitude=_LON)
    assert first == second


def test_all_7_classical_grahas_computed(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    chart = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=_LAT, longitude=_LON,
    )
    calc = DinaHoraBalaCalculator(wrapper)
    results = calc.calculate_all(chart.planets, chart.ephemeris, latitude=_LAT, longitude=_LON)
    assert len(results) == 7


def test_nighttime_birth_computes_correctly(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    chart = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 20, 0, 0, tzinfo=timezone.utc),
        latitude=_LAT, longitude=_LON,
    )
    calc = DinaHoraBalaCalculator(wrapper)
    results = calc.calculate_all(chart.planets, chart.ephemeris, latitude=_LAT, longitude=_LON)
    hora_matches = [
        r for r in results
        if any("Hora" in t and "no match" not in t and "match" in t for t in r.trace)
    ]
    assert len(hora_matches) == 1
