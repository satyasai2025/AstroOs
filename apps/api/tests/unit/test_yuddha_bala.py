"""
AstroOS — Yuddha Bala Unit Tests (Module 9)
"""

import pytest

from apps.api.domain.ephemeris import DignityType, SiderealPosition
from apps.api.services.shadbala.yuddha_bala import YuddhaBalaCalculator


def _make_planet(planet, sidereal_longitude, rashi="leo", latitude_deg=0.0):
    return SiderealPosition(
        planet=planet, sidereal_longitude=sidereal_longitude, rashi=rashi, rashi_degree=10.0,
        house_number=1, nakshatra="ashwini", pada=1, is_retrograde=False,
        is_combust=False, combustion_orb=None, dignity=DignityType.NEUTRAL,
        latitude_deg=latitude_deg,
    )


def test_no_war_when_planets_far_apart():
    calc = YuddhaBalaCalculator()
    planets = [
        _make_planet("mars", 100.0, rashi="leo"),
        _make_planet("venus", 110.0, rashi="leo"),
    ]
    r = calc.calculate("mars", planets)
    assert r.value_shashtiamsas == 0.0
    assert "not at war" in r.trace[0]


def test_no_war_when_different_signs_even_if_close_in_longitude():
    """Same absolute closeness but different signs must not count as war."""
    calc = YuddhaBalaCalculator()
    planets = [
        _make_planet("mars", 29.9, rashi="aries"),
        _make_planet("venus", 30.1, rashi="taurus"),
    ]
    r = calc.calculate("mars", planets)
    assert r.value_shashtiamsas == 0.0


def test_war_detected_within_orb_same_sign():
    calc = YuddhaBalaCalculator()
    planets = [
        _make_planet("mars", 100.0, rashi="leo", latitude_deg=-1.0),
        _make_planet("venus", 100.5, rashi="leo", latitude_deg=1.0),
    ]
    r = calc.calculate("mars", planets)
    assert r.value_shashtiamsas == 30.0


def test_war_only_between_eligible_planets():
    """Sun/Moon are not eligible for Yuddha even if conjunct with an eligible planet."""
    calc = YuddhaBalaCalculator()
    planets = [
        _make_planet("mars", 100.0, rashi="leo"),
        _make_planet("sun", 100.2, rashi="leo"),
    ]
    r = calc.calculate("mars", planets)
    assert r.value_shashtiamsas == 0.0
    assert "not at war" in r.trace[0]


def test_more_southern_latitude_wins():
    calc = YuddhaBalaCalculator()
    planets = [
        _make_planet("mars", 100.0, rashi="leo", latitude_deg=-2.0),
        _make_planet("saturn", 100.3, rashi="leo", latitude_deg=1.5),
    ]
    mars_result = calc.calculate("mars", planets)
    saturn_result = calc.calculate("saturn", planets)
    assert mars_result.value_shashtiamsas == 30.0
    assert saturn_result.value_shashtiamsas == 0.0


def test_loser_gets_zero_not_negative():
    calc = YuddhaBalaCalculator()
    planets = [
        _make_planet("jupiter", 200.0, rashi="libra", latitude_deg=3.0),
        _make_planet("mercury", 200.2, rashi="libra", latitude_deg=-3.0),
    ]
    r = calc.calculate("jupiter", planets)
    assert r.value_shashtiamsas == 0.0


def test_exact_latitude_tie_no_winner():
    calc = YuddhaBalaCalculator()
    planets = [
        _make_planet("mars", 100.0, rashi="leo", latitude_deg=0.5),
        _make_planet("venus", 100.3, rashi="leo", latitude_deg=0.5),
    ]
    mars_result = calc.calculate("mars", planets)
    venus_result = calc.calculate("venus", planets)
    assert mars_result.value_shashtiamsas == 0.0
    assert venus_result.value_shashtiamsas == 0.0


def test_exactly_at_orb_boundary_counts_as_war():
    calc = YuddhaBalaCalculator()
    planets = [
        _make_planet("mars", 100.0, rashi="leo", latitude_deg=-1.0),
        _make_planet("venus", 101.0, rashi="leo", latitude_deg=1.0),
    ]
    r = calc.calculate("mars", planets)
    assert r.value_shashtiamsas == 30.0


def test_just_beyond_orb_boundary_is_not_war():
    calc = YuddhaBalaCalculator()
    planets = [
        _make_planet("mars", 100.0, rashi="leo"),
        _make_planet("venus", 101.001, rashi="leo"),
    ]
    r = calc.calculate("mars", planets)
    assert r.value_shashtiamsas == 0.0


def test_rejects_sun_moon_rahu_ketu():
    calc = YuddhaBalaCalculator()
    for planet in ["sun", "moon", "rahu", "ketu"]:
        with pytest.raises(ValueError):
            calc.calculate(planet, [])


def test_planet_not_in_chart_returns_zero_gracefully():
    calc = YuddhaBalaCalculator()
    r = calc.calculate("mars", [])
    assert r.value_shashtiamsas == 0.0
    assert "not found" in r.trace[0]


def test_calculate_all_returns_5_eligible_planets():
    calc = YuddhaBalaCalculator()
    planets = [_make_planet(p, float(i) * 40, rashi="leo") for i, p in
               enumerate(["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"])]
    results = calc.calculate_all(planets)
    assert len(results) == 5
    assert {r.planet for r in results} == {"mars", "mercury", "jupiter", "venus", "saturn"}


def test_values_always_0_or_30():
    calc = YuddhaBalaCalculator()
    planets = [
        _make_planet("mars", 100.0, rashi="leo", latitude_deg=-1.0),
        _make_planet("venus", 100.5, rashi="leo", latitude_deg=1.0),
        _make_planet("mercury", 200.0, rashi="libra"),
        _make_planet("jupiter", 300.0, rashi="capricorn"),
        _make_planet("saturn", 50.0, rashi="taurus"),
    ]
    for r in calc.calculate_all(planets):
        assert r.value_shashtiamsas in (0.0, 30.0)
