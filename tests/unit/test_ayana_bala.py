"""
AstroOS — Ayana Bala Unit Tests (Module 9)
"""

import pytest

from apps.api.domain.ephemeris import DignityType, SiderealPosition
from apps.api.services.shadbala.ayana_bala import AyanaBalaCalculator

_OBLIQUITY = 23.4408


def _make_planet(planet, declination_deg):
    return SiderealPosition(
        planet=planet, sidereal_longitude=10.0, rashi="aries", rashi_degree=10.0,
        house_number=1, nakshatra="ashwini", pada=1, is_retrograde=False,
        is_combust=False, combustion_orb=None, dignity=DignityType.NEUTRAL,
        declination_deg=declination_deg,
    )


# ── North-favoring planets (Sun, Mars, Jupiter, Venus) ────────────────────────

@pytest.mark.parametrize("planet", ["sun", "mars", "jupiter", "venus"])
def test_north_favoring_max_at_max_north_declination(planet):
    calc = AyanaBalaCalculator()
    result = calc.calculate(_make_planet(planet, _OBLIQUITY))
    assert result.value_shashtiamsas == pytest.approx(60.0, abs=0.01)


@pytest.mark.parametrize("planet", ["sun", "mars", "jupiter", "venus"])
def test_north_favoring_min_at_max_south_declination(planet):
    calc = AyanaBalaCalculator()
    result = calc.calculate(_make_planet(planet, -_OBLIQUITY))
    assert result.value_shashtiamsas == pytest.approx(0.0, abs=0.01)


@pytest.mark.parametrize("planet", ["sun", "mars", "jupiter", "venus"])
def test_north_favoring_midpoint_at_zero_declination(planet):
    calc = AyanaBalaCalculator()
    result = calc.calculate(_make_planet(planet, 0.0))
    assert result.value_shashtiamsas == pytest.approx(30.0, abs=0.01)


# ── South-favoring planets (Moon, Saturn) ─────────────────────────────────────

@pytest.mark.parametrize("planet", ["moon", "saturn"])
def test_south_favoring_max_at_max_south_declination(planet):
    calc = AyanaBalaCalculator()
    result = calc.calculate(_make_planet(planet, -_OBLIQUITY))
    assert result.value_shashtiamsas == pytest.approx(60.0, abs=0.01)


@pytest.mark.parametrize("planet", ["moon", "saturn"])
def test_south_favoring_min_at_max_north_declination(planet):
    calc = AyanaBalaCalculator()
    result = calc.calculate(_make_planet(planet, _OBLIQUITY))
    assert result.value_shashtiamsas == pytest.approx(0.0, abs=0.01)


@pytest.mark.parametrize("planet", ["moon", "saturn"])
def test_south_favoring_midpoint_at_zero_declination(planet):
    calc = AyanaBalaCalculator()
    result = calc.calculate(_make_planet(planet, 0.0))
    assert result.value_shashtiamsas == pytest.approx(30.0, abs=0.01)


# ── Mercury (magnitude-favoring) ───────────────────────────────────────────────

def test_mercury_max_at_max_north_declination():
    calc = AyanaBalaCalculator()
    result = calc.calculate(_make_planet("mercury", _OBLIQUITY))
    assert result.value_shashtiamsas == pytest.approx(60.0, abs=0.01)


def test_mercury_max_at_max_south_declination_too():
    """Mercury favors magnitude — south extreme should ALSO score near-max, unlike other planets."""
    calc = AyanaBalaCalculator()
    result = calc.calculate(_make_planet("mercury", -_OBLIQUITY))
    assert result.value_shashtiamsas == pytest.approx(60.0, abs=0.01)


def test_mercury_min_at_zero_declination():
    calc = AyanaBalaCalculator()
    result = calc.calculate(_make_planet("mercury", 0.0))
    assert result.value_shashtiamsas == pytest.approx(30.0, abs=0.01)


# ── Clamping / general ─────────────────────────────────────────────────────────

def test_declination_beyond_obliquity_clamps_not_overflows():
    """Nodes/edge cases could theoretically report declination beyond the Sun's obliquity bound."""
    calc = AyanaBalaCalculator()
    result = calc.calculate(_make_planet("sun", 40.0))  # unrealistic but must not crash or exceed 60
    assert result.value_shashtiamsas <= 60.0


def test_rejects_rahu_ketu():
    calc = AyanaBalaCalculator()
    with pytest.raises(ValueError):
        calc.calculate(_make_planet("rahu", 10.0))


def test_values_always_between_0_and_60():
    calc = AyanaBalaCalculator()
    for planet in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]:
        for decl in [-30.0, -23.4408, -10.0, 0.0, 10.0, 23.4408, 30.0]:
            result = calc.calculate(_make_planet(planet, decl))
            assert 0.0 <= result.value_shashtiamsas <= 60.0


def test_calculate_all_returns_7_classical_grahas():
    planets = [_make_planet(p, 5.0) for p in
               ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]]
    calc = AyanaBalaCalculator()
    results = calc.calculate_all(planets)
    assert len(results) == 7
    assert "rahu" not in {r.planet for r in results}
