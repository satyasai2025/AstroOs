"""
AstroOS — Vedha Table & Calculator Unit Tests (Module 11 Phase 2)
"""

import pytest

from apps.api.services.vedha_calculator import VedhaCalculator
from packages.shared.transit_vedha_table import NO_VEDHA_EXCEPTION, VEDHA, VIPREET_VEDHA


def test_all_9_planets_have_vedha_entries():
    assert set(VEDHA.keys()) == {
        "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"
    }


def test_all_9_planets_have_vipreet_vedha_entries():
    assert set(VIPREET_VEDHA.keys()) == {
        "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"
    }


def test_all_house_numbers_within_1_to_12():
    for table in (VEDHA, VIPREET_VEDHA):
        for planet, entries in table.items():
            for house, target in entries.items():
                assert 1 <= house <= 12, f"{planet}: bad house {house}"
                assert 1 <= target <= 12, f"{planet}: bad target {target}"


def test_rahu_ketu_vipreet_vedha_matches_saturn():
    assert VIPREET_VEDHA["rahu"] == VIPREET_VEDHA["saturn"]
    assert VIPREET_VEDHA["ketu"] == VIPREET_VEDHA["saturn"]


def test_mars_saturn_rahu_ketu_share_same_vedha_shape():
    assert VEDHA["mars"] == VEDHA["saturn"] == VEDHA["rahu"] == VEDHA["ketu"]


def test_sun_saturn_mutual_exception():
    assert NO_VEDHA_EXCEPTION["sun"] == "saturn"
    assert NO_VEDHA_EXCEPTION["saturn"] == "sun"


def test_moon_mercury_mutual_exception():
    assert NO_VEDHA_EXCEPTION["moon"] == "mercury"
    assert NO_VEDHA_EXCEPTION["mercury"] == "moon"


def test_mercury_and_venus_are_the_only_asymmetric_tables():
    symmetric_planets = []
    for planet in VEDHA:
        vedha_pairs = set(VEDHA[planet].items())
        vipreet_reversed = set((v, k) for k, v in VIPREET_VEDHA[planet].items())
        if vedha_pairs == vipreet_reversed:
            symmetric_planets.append(planet)
    assert set(symmetric_planets) == {"sun", "moon", "mars", "jupiter", "saturn", "rahu", "ketu"}


def test_classify_house_good():
    calc = VedhaCalculator()
    assert calc.classify_house("sun", 3) is True


def test_classify_house_bad():
    calc = VedhaCalculator()
    assert calc.classify_house("sun", 9) is False


def test_classify_house_uncovered():
    calc = VedhaCalculator()
    assert calc.classify_house("sun", 1) is None


def test_vedha_triggered_when_obstructing_planet_present():
    calc = VedhaCalculator()
    has_vedha, has_vipreet, obstructor = calc.check("sun", 3, {"mars": 9})
    assert has_vedha is True
    assert has_vipreet is False
    assert obstructor == "mars"


def test_vedha_not_triggered_when_no_planet_in_obstruction_house():
    calc = VedhaCalculator()
    has_vedha, has_vipreet, obstructor = calc.check("sun", 3, {"mars": 5})
    assert has_vedha is False
    assert obstructor is None


def test_sun_saturn_exception_blocks_vedha():
    calc = VedhaCalculator()
    has_vedha, _, obstructor = calc.check("sun", 3, {"saturn": 9})
    assert has_vedha is False
    assert obstructor is None


def test_sun_saturn_exception_is_specific_to_that_pair():
    calc = VedhaCalculator()
    has_vedha, _, obstructor = calc.check("sun", 3, {"saturn": 9, "mars": 9})
    assert has_vedha is True
    assert obstructor == "mars"


def test_moon_mercury_exception_blocks_vedha():
    calc = VedhaCalculator()
    has_vedha, _, obstructor = calc.check("moon", 1, {"mercury": 5})
    assert has_vedha is False


def test_vipreet_vedha_triggered_when_relieving_planet_present():
    calc = VedhaCalculator()
    has_vedha, has_vipreet, reliever = calc.check("sun", 4, {"venus": 10})
    assert has_vedha is False
    assert has_vipreet is True
    assert reliever == "venus"


def test_vipreet_vedha_not_triggered_without_relieving_planet():
    calc = VedhaCalculator()
    has_vedha, has_vipreet, reliever = calc.check("sun", 4, {"venus": 2})
    assert has_vipreet is False
    assert reliever is None


def test_saturn_sun_exception_blocks_vipreet_vedha_too():
    calc = VedhaCalculator()
    has_vedha, has_vipreet, reliever = calc.check("saturn", 12, {"sun": 3})
    assert has_vipreet is False
    assert reliever is None


def test_uncovered_house_never_triggers_either():
    calc = VedhaCalculator()
    has_vedha, has_vipreet, obstructor = calc.check("sun", 1, {"mars": 5, "venus": 8})
    assert has_vedha is False
    assert has_vipreet is False
    assert obstructor is None


def test_self_never_counts_as_obstructor():
    calc = VedhaCalculator()
    has_vedha, _, obstructor = calc.check("sun", 3, {"sun": 9})
    assert obstructor is None
