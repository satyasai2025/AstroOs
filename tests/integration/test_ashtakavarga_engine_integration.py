"""
AstroOS — Ashtakavarga Engine Integration Tests (Module 10)

Exercises AshtakavargaEngine against real chart data computed by
EphemerisWrapper (Moshier fallback, same pattern as every other
integration test in this codebase — no live .se1 files required).
"""

from datetime import datetime, timezone

import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine

_EPHE_PATH = "data/ephemeris"


@pytest.fixture(scope="module")
def wrapper() -> EphemerisWrapper:
    return EphemerisWrapper(ephemeris_path=_EPHE_PATH)


def test_checksum_holds_on_real_chart(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    chart = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=28.6139, longitude=77.2090,
    )
    engine = AshtakavargaEngine()
    assert engine.verify_checksum(chart) is True


def test_checksum_holds_across_multiple_real_charts(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    engine = AshtakavargaEngine()
    birth_dates = [
        datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        datetime(1975, 12, 25, 3, 0, 0, tzinfo=timezone.utc),
        datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        datetime(2020, 8, 20, 18, 45, 0, tzinfo=timezone.utc),
    ]
    for dt in birth_dates:
        chart = horoscope_engine.generate_d1(
            birth_datetime_utc=dt, latitude=28.6139, longitude=77.2090,
        )
        assert engine.verify_checksum(chart) is True


def test_each_planet_total_matches_classical_constant_on_real_chart(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    chart = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=28.6139, longitude=77.2090,
    )
    engine = AshtakavargaEngine()
    results = engine.compute_bhinnashtakavarga(chart)
    totals = {r.target_planet: r.total_bindus for r in results}
    assert totals == {
        "sun": 48, "moon": 49, "mars": 39, "mercury": 54,
        "jupiter": 56, "venus": 52, "saturn": 39,
    }


def test_deterministic_across_repeated_calls(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    chart = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=28.6139, longitude=77.2090,
    )
    engine = AshtakavargaEngine()
    first_bhinna = engine.compute_bhinnashtakavarga(chart)
    second_bhinna = engine.compute_bhinnashtakavarga(chart)
    assert first_bhinna == second_bhinna

    first_sav = engine.compute_sarvashtakavarga(chart)
    second_sav = engine.compute_sarvashtakavarga(chart)
    assert first_sav == second_sav


def test_different_charts_produce_different_distributions(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    engine = AshtakavargaEngine()

    chart_a = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=28.6139, longitude=77.2090,
    )
    chart_b = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1975, 12, 25, 3, 0, 0, tzinfo=timezone.utc),
        latitude=40.7128, longitude=-74.0060,
    )
    sav_a = engine.compute_sarvashtakavarga(chart_a)
    sav_b = engine.compute_sarvashtakavarga(chart_b)
    assert sav_a.bindus_by_rashi != sav_b.bindus_by_rashi
    assert sav_a.total_bindus == sav_b.total_bindus == 337


def test_sav_values_within_theoretical_bounds(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    chart = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=28.6139, longitude=77.2090,
    )
    engine = AshtakavargaEngine()
    sav = engine.compute_sarvashtakavarga(chart)
    for count in sav.bindus_by_rashi:
        assert 0 <= count <= 56  # theoretical max per rashi (8 bindus x 7 planets)


def test_sarvashtakavarga_bindus_from_lagna(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    chart = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=28.6139, longitude=77.2090,
    )
    engine = AshtakavargaEngine()
    sav = engine.compute_sarvashtakavarga(chart)
    lagna_rashi = chart.ascendant.rashi
    # House 1 from lagna must equal the bindus in the lagna's own rashi
    assert sav.bindus_from_lagna(lagna_rashi, 1) == sav.bindus_in_rashi(lagna_rashi)


def test_reduced_bhinnashtakavarga_on_real_chart(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    chart = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=28.6139, longitude=77.2090,
    )
    engine = AshtakavargaEngine()
    unreduced = {r.target_planet: r.total_bindus for r in engine.compute_bhinnashtakavarga(chart)}
    reduced = {r.target_planet: r.total_bindus for r in engine.compute_reduced_bhinnashtakavarga(chart)}
    assert set(reduced.keys()) == set(unreduced.keys())
    for planet in unreduced:
        assert 0 <= reduced[planet] <= unreduced[planet]


def test_reduced_bhinnashtakavarga_deterministic(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    chart = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=28.6139, longitude=77.2090,
    )
    engine = AshtakavargaEngine()
    first = engine.compute_reduced_bhinnashtakavarga(chart)
    second = engine.compute_reduced_bhinnashtakavarga(chart)
    assert first == second
