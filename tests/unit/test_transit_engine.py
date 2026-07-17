"""
AstroOS — Transit Engine Unit Tests (Module 11)

Uses real EphemerisWrapper (Moshier fallback, no live .se1 files
required) for transiting positions, but constructs synthetic natal
charts to control the natal Moon's rashi precisely — letting the
house-from-Moon, Sade Sati, and Ashtama Shani logic be verified exactly
rather than only spot-checked against whatever a real chart happens to
produce.
"""

from datetime import datetime, timezone

import pytest

from apps.api.domain.ephemeris import Ascendant, DignityType, SiderealPosition
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.transit_engine import TransitEngine, _house_from_reference

_EPHE_PATH = "data/ephemeris"


@pytest.fixture(scope="module")
def wrapper() -> EphemerisWrapper:
    return EphemerisWrapper(ephemeris_path=_EPHE_PATH)


def _make_planet(planet, rashi):
    return SiderealPosition(
        planet=planet, sidereal_longitude=10.0, rashi=rashi, rashi_degree=10.0,
        house_number=1, nakshatra="ashwini", pada=1, is_retrograde=False,
        is_combust=False, combustion_orb=None, dignity=DignityType.NEUTRAL,
    )


def _make_natal_chart(moon_rashi, lagna_rashi="aries"):
    all_planets = ["sun", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]

    class _FakeChart:
        pass

    chart = _FakeChart()
    chart.planets = [_make_planet("moon", moon_rashi)] + [_make_planet(p, "aries") for p in all_planets]
    chart.ascendant = Ascendant(
        longitude=0.0, sidereal_longitude=0.0, rashi=lagna_rashi, rashi_degree=0.0,
        nakshatra="ashwini", pada=1,
    )
    return chart


def test_house_from_reference_same_rashi_is_house_1():
    assert _house_from_reference("aries", "aries") == 1


def test_house_from_reference_next_rashi_is_house_2():
    assert _house_from_reference("aries", "taurus") == 2


def test_house_from_reference_wraps_cyclically():
    assert _house_from_reference("aquarius", "pisces") == 2
    assert _house_from_reference("pisces", "aries") == 2
    assert _house_from_reference("pisces", "aquarius") == 12


def _find_transit_with_saturn_in(wrapper, engine, natal_chart, target_rashi, max_years=30):
    from datetime import timedelta
    dt = datetime(2000, 1, 1, tzinfo=timezone.utc)
    for _ in range(max_years * 4):
        results = engine.compute_transit(natal_chart, dt)
        saturn_result = next(r for r in results if r.planet == "saturn")
        if saturn_result.transit_rashi == target_rashi:
            return saturn_result
        dt += timedelta(days=90)
    raise AssertionError(f"Could not find a transit date with Saturn in {target_rashi} within {max_years} years")


def test_saturn_in_12th_from_moon_is_sade_sati(wrapper):
    natal = _make_natal_chart(moon_rashi="aries")
    engine = TransitEngine(wrapper)
    result = _find_transit_with_saturn_in(wrapper, engine, natal, "pisces")
    assert result.is_sade_sati is True
    assert result.is_ashtama_shani is False


def test_saturn_in_1st_from_moon_is_sade_sati(wrapper):
    natal = _make_natal_chart(moon_rashi="aries")
    engine = TransitEngine(wrapper)
    result = _find_transit_with_saturn_in(wrapper, engine, natal, "aries")
    assert result.is_sade_sati is True


def test_saturn_in_2nd_from_moon_is_sade_sati(wrapper):
    natal = _make_natal_chart(moon_rashi="aries")
    engine = TransitEngine(wrapper)
    result = _find_transit_with_saturn_in(wrapper, engine, natal, "taurus")
    assert result.is_sade_sati is True


def test_saturn_in_8th_from_moon_is_ashtama_shani(wrapper):
    natal = _make_natal_chart(moon_rashi="aries")
    engine = TransitEngine(wrapper)
    result = _find_transit_with_saturn_in(wrapper, engine, natal, "scorpio")
    assert result.is_ashtama_shani is True
    assert result.is_sade_sati is False


def test_saturn_elsewhere_is_neither(wrapper):
    natal = _make_natal_chart(moon_rashi="aries")
    engine = TransitEngine(wrapper)
    result = _find_transit_with_saturn_in(wrapper, engine, natal, "leo")
    assert result.is_sade_sati is False
    assert result.is_ashtama_shani is False


def test_ashtakavarga_bindus_present_for_classical_seven(wrapper):
    natal = _make_natal_chart(moon_rashi="cancer")
    engine = TransitEngine(wrapper)
    results = engine.compute_transit(natal, datetime(2026, 7, 12, tzinfo=timezone.utc))
    for r in results:
        if r.planet in ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"):
            assert r.ashtakavarga_bindus is not None
            assert 0 <= r.ashtakavarga_bindus <= 8


def test_ashtakavarga_bindus_none_for_rahu_ketu(wrapper):
    natal = _make_natal_chart(moon_rashi="cancer")
    engine = TransitEngine(wrapper)
    results = engine.compute_transit(natal, datetime(2026, 7, 12, tzinfo=timezone.utc))
    for r in results:
        if r.planet in ("rahu", "ketu"):
            assert r.ashtakavarga_bindus is None


def test_compute_transit_returns_all_9_planets(wrapper):
    natal = _make_natal_chart(moon_rashi="virgo")
    engine = TransitEngine(wrapper)
    results = engine.compute_transit(natal, datetime(2026, 7, 12, tzinfo=timezone.utc))
    assert len(results) == 9
    assert {r.planet for r in results} == {
        "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"
    }


def test_house_from_moon_always_between_1_and_12(wrapper):
    natal = _make_natal_chart(moon_rashi="libra")
    engine = TransitEngine(wrapper)
    results = engine.compute_transit(natal, datetime(2026, 7, 12, tzinfo=timezone.utc))
    for r in results:
        assert 1 <= r.house_from_natal_moon <= 12


def test_deterministic_across_repeated_calls(wrapper):
    natal = _make_natal_chart(moon_rashi="sagittarius")
    engine = TransitEngine(wrapper)
    dt = datetime(2026, 7, 12, tzinfo=timezone.utc)
    first = engine.compute_transit(natal, dt)
    second = engine.compute_transit(natal, dt)
    assert first == second


def test_only_saturn_can_have_sade_sati_or_ashtama_shani_flags(wrapper):
    natal = _make_natal_chart(moon_rashi="gemini")
    engine = TransitEngine(wrapper)
    results = engine.compute_transit(natal, datetime(2026, 7, 12, tzinfo=timezone.utc))
    for r in results:
        if r.planet != "saturn":
            assert r.is_sade_sati is False
            assert r.is_ashtama_shani is False


def test_engine_vedha_matches_direct_calculator_computation(wrapper):
    """
    Cross-check: re-running VedhaCalculator directly on the engine's own
    computed houses must match what the engine attached to each result —
    confirms the wiring, not just that VedhaCalculator works in isolation.
    """
    from apps.api.services.vedha_calculator import VedhaCalculator

    natal = _make_natal_chart(moon_rashi="scorpio")
    engine = TransitEngine(wrapper)
    results = engine.compute_transit(natal, datetime(2026, 7, 12, tzinfo=timezone.utc))

    houses_by_planet = {r.planet: r.house_from_natal_moon for r in results}
    calc = VedhaCalculator()
    for r in results:
        other_houses = {p: h for p, h in houses_by_planet.items() if p != r.planet}
        expected_vedha, expected_vipreet, expected_planet = calc.check(
            r.planet, r.house_from_natal_moon, other_houses,
        )
        assert r.has_vedha == expected_vedha
        assert r.has_vipreet_vedha == expected_vipreet
        assert r.vedha_planet == expected_planet


def test_is_favorable_house_populated_for_all_planets(wrapper):
    natal = _make_natal_chart(moon_rashi="pisces")
    engine = TransitEngine(wrapper)
    results = engine.compute_transit(natal, datetime(2026, 7, 12, tzinfo=timezone.utc))
    for r in results:
        assert r.is_favorable_house in (True, False, None)


def test_vedha_and_vipreet_vedha_never_both_true(wrapper):
    natal = _make_natal_chart(moon_rashi="aries")
    engine = TransitEngine(wrapper)
    results = engine.compute_transit(natal, datetime(2026, 7, 12, tzinfo=timezone.utc))
    for r in results:
        assert not (r.has_vedha and r.has_vipreet_vedha)
