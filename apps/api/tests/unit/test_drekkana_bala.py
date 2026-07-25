"""
AstroOS — Drekkana Bala Unit Tests (Module 9)
"""

import pytest

from apps.api.domain.ephemeris import DignityType, SiderealPosition
from apps.api.services.shadbala.drekkana_bala import DrekkanaBalaCalculator


def _make_planet(planet, rashi_degree):
    return SiderealPosition(
        planet=planet, sidereal_longitude=10.0, rashi="aries", rashi_degree=rashi_degree,
        house_number=1, nakshatra="ashwini", pada=1, is_retrograde=False,
        is_combust=False, combustion_orb=None, dignity=DignityType.NEUTRAL,
    )


# ── Male planets (Sun, Mars, Jupiter) — full bala in 1st decanate (0-10°) ────

@pytest.mark.parametrize("planet", ["sun", "mars", "jupiter"])
def test_male_planet_full_bala_in_first_decanate(planet):
    calc = DrekkanaBalaCalculator()
    result = calc.calculate(_make_planet(planet, rashi_degree=5.0))
    assert result.value_shashtiamsas == pytest.approx(15.0)


@pytest.mark.parametrize("planet", ["sun", "mars", "jupiter"])
def test_male_planet_zero_bala_elsewhere(planet):
    calc = DrekkanaBalaCalculator()
    result_2nd = calc.calculate(_make_planet(planet, rashi_degree=15.0))
    result_3rd = calc.calculate(_make_planet(planet, rashi_degree=25.0))
    assert result_2nd.value_shashtiamsas == pytest.approx(0.0)
    assert result_3rd.value_shashtiamsas == pytest.approx(0.0)


# ── Female planets (Moon, Venus) — full bala in 2nd decanate (10-20°) ────────

@pytest.mark.parametrize("planet", ["moon", "venus"])
def test_female_planet_full_bala_in_second_decanate(planet):
    calc = DrekkanaBalaCalculator()
    result = calc.calculate(_make_planet(planet, rashi_degree=15.0))
    assert result.value_shashtiamsas == pytest.approx(15.0)


@pytest.mark.parametrize("planet", ["moon", "venus"])
def test_female_planet_zero_bala_elsewhere(planet):
    calc = DrekkanaBalaCalculator()
    result_1st = calc.calculate(_make_planet(planet, rashi_degree=5.0))
    result_3rd = calc.calculate(_make_planet(planet, rashi_degree=25.0))
    assert result_1st.value_shashtiamsas == pytest.approx(0.0)
    assert result_3rd.value_shashtiamsas == pytest.approx(0.0)


# ── Neuter planets (Mercury, Saturn) — full bala in 3rd decanate (20-30°) ────

@pytest.mark.parametrize("planet", ["mercury", "saturn"])
def test_neuter_planet_full_bala_in_third_decanate(planet):
    calc = DrekkanaBalaCalculator()
    result = calc.calculate(_make_planet(planet, rashi_degree=25.0))
    assert result.value_shashtiamsas == pytest.approx(15.0)


@pytest.mark.parametrize("planet", ["mercury", "saturn"])
def test_neuter_planet_zero_bala_elsewhere(planet):
    calc = DrekkanaBalaCalculator()
    result_1st = calc.calculate(_make_planet(planet, rashi_degree=5.0))
    result_2nd = calc.calculate(_make_planet(planet, rashi_degree=15.0))
    assert result_1st.value_shashtiamsas == pytest.approx(0.0)
    assert result_2nd.value_shashtiamsas == pytest.approx(0.0)


# ── Boundary conditions ────────────────────────────────────────────────────────

def test_boundary_at_exactly_10_degrees_is_second_decanate():
    """10.0 is the start of the 2nd decanate, not the end of the 1st."""
    calc = DrekkanaBalaCalculator()
    result = calc.calculate(_make_planet("moon", rashi_degree=10.0))  # female, expects 2nd
    assert result.value_shashtiamsas == pytest.approx(15.0)


def test_boundary_at_exactly_20_degrees_is_third_decanate():
    calc = DrekkanaBalaCalculator()
    result = calc.calculate(_make_planet("saturn", rashi_degree=20.0))  # neuter, expects 3rd
    assert result.value_shashtiamsas == pytest.approx(15.0)


def test_boundary_at_exactly_30_degrees_does_not_overflow():
    """Exactly 30.0 (edge of the sign) must not produce a 4th decanate index."""
    calc = DrekkanaBalaCalculator()
    result = calc.calculate(_make_planet("saturn", rashi_degree=30.0))  # neuter, still 3rd
    assert result.value_shashtiamsas == pytest.approx(15.0)


def test_boundary_just_under_10_degrees_is_first_decanate():
    calc = DrekkanaBalaCalculator()
    result = calc.calculate(_make_planet("sun", rashi_degree=9.999))  # male, expects 1st
    assert result.value_shashtiamsas == pytest.approx(15.0)


# ── General ──────────────────────────────────────────────────────────────────

def test_rejects_rahu_ketu():
    calc = DrekkanaBalaCalculator()
    with pytest.raises(ValueError):
        calc.calculate(_make_planet("rahu", rashi_degree=5.0))


def test_calculate_all_filters_to_7_classical():
    planets = [_make_planet(p, 5.0) for p in
               ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]]
    calc = DrekkanaBalaCalculator()
    results = calc.calculate_all(planets)
    assert len(results) == 7
    assert "rahu" not in {r.planet for r in results}


def test_value_always_0_or_15():
    calc = DrekkanaBalaCalculator()
    for planet in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]:
        for deg in [0.0, 5.0, 9.99, 10.0, 15.0, 19.99, 20.0, 25.0, 29.99, 30.0]:
            result = calc.calculate(_make_planet(planet, deg))
            assert result.value_shashtiamsas in (0.0, 15.0)
