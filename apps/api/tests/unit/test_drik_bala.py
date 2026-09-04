"""
AstroOS — Drik Bala Unit Tests (Module 9)

Formula was replaced (see drik_bala.py's module docstring) with the
classical Parashari piecewise "Sputa Drishti" table after the earlier
simple orb-based linear falloff was found to not match a verified
reference. calculate_all() now takes planet longitudes directly (no
AspectEngine dependency) since the piecewise formula needs the raw
angular separation, not a pre-computed orb.
"""

import pytest

from apps.api.domain.ephemeris import DignityType, SiderealPosition
from apps.api.services.shadbala.drik_bala import DrikBalaCalculator, _piecewise_drishti_virupas


def _make_planet(planet, sidereal_longitude):
    return SiderealPosition(
        planet=planet, sidereal_longitude=sidereal_longitude, rashi="aries", rashi_degree=10.0,
        house_number=1, nakshatra="ashwini", pada=1, is_retrograde=False,
        is_combust=False, combustion_orb=None, dignity=DignityType.NEUTRAL,
    )


def test_reference_chart_matches_pyjhora_exactly():
    """
    1995-01-01 12:00 UTC, New Delhi (Lahiri) — cross-verified against
    PyJHora's jhora.horoscope.chart.strength._drik_bala() for this exact
    chart (this project's own verified EphemerisWrapper sidereal
    longitudes for the same birth data).
    """
    longitudes = {
        "sun": 256.8125, "moon": 257.4318, "mars": 128.8693, "mercury": 267.4526,
        "jupiter": 221.0448, "venus": 210.5277, "saturn": 314.2452,
    }
    expected = {
        "sun": -2.75, "moon": -2.45, "mars": 11.82, "mercury": 2.56,
        "jupiter": -18.88, "venus": -14.63, "saturn": 8.08,
    }
    planets = [_make_planet(p, lon) for p, lon in longitudes.items()]
    calc = DrikBalaCalculator()
    results = {r.planet: r.value_shashtiamsas for r in calc.calculate_all(planets)}
    for planet, exp in expected.items():
        assert results[planet] == pytest.approx(exp, abs=0.05), planet


@pytest.mark.parametrize("angle,expected", [
    (0.0, 0.0),
    (15.0, 0.0),
    (45.0, 7.5),      # 0.5 * (45-30)
    (135.0, 15.0),    # 150-135, no jupiter bonus for a non-jupiter aspecter
    (165.0, 30.0),    # 2 * (165-150)
    (250.0, 25.0),    # 0.5 * (300-250)
])
def test_piecewise_bands_match_formula_for_non_special_aspecter(angle, expected):
    assert _piecewise_drishti_virupas(angle, "venus") == pytest.approx(expected)


def test_mars_gets_special_aspect_bonus_at_90_to_120():
    """Mars' special 4th-house-count aspect (90-120°) adds +15 virupas beyond the base formula."""
    base = _piecewise_drishti_virupas(100.0, "venus")
    mars_value = _piecewise_drishti_virupas(100.0, "mars")
    assert mars_value == pytest.approx(base + 15.0)


def test_jupiter_gets_special_aspect_bonus_at_120_to_150():
    """Jupiter's special 5th-house-count aspect (120-150°) adds +30 virupas beyond the base formula."""
    base = _piecewise_drishti_virupas(130.0, "venus")
    jupiter_value = _piecewise_drishti_virupas(130.0, "jupiter")
    assert jupiter_value == pytest.approx(base + 30.0)


def test_saturn_gets_special_aspect_bonus_at_60_to_90():
    """Saturn's special 3rd-house-count aspect (60-90°) adds +45 virupas beyond the base formula."""
    base = _piecewise_drishti_virupas(70.0, "venus")
    saturn_value = _piecewise_drishti_virupas(70.0, "saturn")
    assert saturn_value == pytest.approx(base + 45.0)


def test_calculate_all_returns_7_classical_grahas():
    planets = [_make_planet(p, 10.0 * i) for i, p in enumerate(
        ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]
    )]
    calc = DrikBalaCalculator()
    results = calc.calculate_all(planets)
    assert len(results) == 7
    assert "rahu" not in {r.planet for r in results}
