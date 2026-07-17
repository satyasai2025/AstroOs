"""
AstroOS — Transit Engine Integration Tests (Module 11)

Exercises TransitEngine against a real natal chart computed by
EphemerisWrapper + HoroscopeEngine (Moshier fallback, same pattern as
every other integration test in this codebase).
"""

from datetime import datetime, timezone

import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.transit_engine import TransitEngine

_EPHE_PATH = "data/ephemeris"
_LAT = 28.6139
_LON = 77.2090


@pytest.fixture(scope="module")
def wrapper() -> EphemerisWrapper:
    return EphemerisWrapper(ephemeris_path=_EPHE_PATH)


@pytest.fixture(scope="module")
def natal_chart(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    return horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=_LAT, longitude=_LON,
    )


def test_transit_today_against_real_natal_chart(wrapper, natal_chart):
    engine = TransitEngine(wrapper)
    results = engine.compute_transit(natal_chart, datetime(2026, 7, 12, tzinfo=timezone.utc))
    assert len(results) == 9


def test_different_transit_dates_produce_different_positions(wrapper, natal_chart):
    engine = TransitEngine(wrapper)
    results_a = engine.compute_transit(natal_chart, datetime(2020, 1, 1, tzinfo=timezone.utc))
    results_b = engine.compute_transit(natal_chart, datetime(2026, 7, 12, tzinfo=timezone.utc))
    rashis_a = {r.planet: r.transit_rashi for r in results_a}
    rashis_b = {r.planet: r.transit_rashi for r in results_b}
    assert rashis_a != rashis_b


def test_different_natal_charts_same_transit_date_produce_different_houses(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    chart_a = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=28.6139, longitude=77.2090,
    )
    chart_b = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1975, 12, 25, 3, 0, 0, tzinfo=timezone.utc),
        latitude=40.7128, longitude=-74.0060,
    )
    engine = TransitEngine(wrapper)
    transit_dt = datetime(2026, 7, 12, tzinfo=timezone.utc)
    results_a = engine.compute_transit(chart_a, transit_dt)
    results_b = engine.compute_transit(chart_b, transit_dt)

    houses_a = {r.planet: r.house_from_natal_moon for r in results_a}
    houses_b = {r.planet: r.house_from_natal_moon for r in results_b}
    rashis_a = {r.planet: r.transit_rashi for r in results_a}
    rashis_b = {r.planet: r.transit_rashi for r in results_b}
    assert rashis_a == rashis_b
    assert houses_a != houses_b


def test_ashtakavarga_bindus_match_natal_chart_bhinnashtakavarga(wrapper, natal_chart):
    from apps.api.services.ashtakavarga_engine import AshtakavargaEngine

    engine = TransitEngine(wrapper)
    ashtakavarga_engine = AshtakavargaEngine()

    transit_dt = datetime(2026, 7, 12, tzinfo=timezone.utc)
    results = engine.compute_transit(natal_chart, transit_dt)
    natal_bhinna = {r.target_planet: r for r in ashtakavarga_engine.compute_bhinnashtakavarga(natal_chart)}

    for r in results:
        if r.planet in natal_bhinna:
            expected = natal_bhinna[r.planet].bindus_in_rashi(r.transit_rashi)
            assert r.ashtakavarga_bindus == expected


def test_deterministic_on_real_chart(wrapper, natal_chart):
    engine = TransitEngine(wrapper)
    dt = datetime(2026, 7, 12, tzinfo=timezone.utc)
    first = engine.compute_transit(natal_chart, dt)
    second = engine.compute_transit(natal_chart, dt)
    assert first == second


def test_vedha_fields_present_on_real_chart(wrapper, natal_chart):
    engine = TransitEngine(wrapper)
    results = engine.compute_transit(natal_chart, datetime(2026, 7, 12, tzinfo=timezone.utc))
    for r in results:
        assert r.is_favorable_house in (True, False, None)
        assert isinstance(r.has_vedha, bool)
        assert isinstance(r.has_vipreet_vedha, bool)
        assert not (r.has_vedha and r.has_vipreet_vedha)
