"""
AstroOS — Ayana Bala Unit Tests (Module 9)

Formula was replaced (see ayana_bala.py's module docstring) after being
cross-checked against PyJHora's declination_of_planets()/_ayana_bala()
and found incorrect — it used real astronomical declination directly,
where the classical method uses tropical-longitude-derived "bhuja" and
an inverse-Lagrange Kranti table instead. These tests use the same
tropical-longitude input the real formula needs (sidereal longitude +
ayanamsa), not raw declination.
"""

import pytest

from apps.api.domain.ephemeris import DignityType, SiderealPosition
from apps.api.services.shadbala.ayana_bala import AyanaBalaCalculator

_AYANAMSA = 24.0  # approx Lahiri ayanamsa around 1995 — used to build tropical longitudes


def _make_planet(planet, sidereal_longitude):
    return SiderealPosition(
        planet=planet, sidereal_longitude=sidereal_longitude, rashi="aries", rashi_degree=10.0,
        house_number=1, nakshatra="ashwini", pada=1, is_retrograde=False,
        is_combust=False, combustion_orb=None, dignity=DignityType.NEUTRAL,
    )


def test_reference_chart_matches_pyjhora_exactly():
    """
    1995-01-01 12:00 UTC, New Delhi (Lahiri) — cross-verified against
    PyJHora's jhora.horoscope.chart.strength._ayana_bala() for this
    exact chart. Sidereal longitudes and ayanamsa are this project's
    own verified EphemerisWrapper output for the same birth data.
    """
    ayanamsa_deg = 23.78725828436319  # this chart's real Lahiri ayanamsa value (EphemerisWrapper output)
    longitudes = {
        "sun": 256.8125, "moon": 257.4318, "mars": 128.8693, "mercury": 267.4526,
        "jupiter": 221.0448, "venus": 210.5277, "saturn": 314.2452,
    }
    expected = {
        "sun": 1.12, "moon": 59.38, "mars": 43.44, "mercury": 57.86,
        "jupiter": 2.98, "venus": 5.89, "saturn": 40.93,
    }
    calc = AyanaBalaCalculator()
    for planet, lon in longitudes.items():
        result = calc.calculate(_make_planet(planet, lon), ayanamsa_deg)
        assert result.value_shashtiamsas == pytest.approx(expected[planet], abs=0.05), planet


def test_sun_can_exceed_60_due_to_classical_doubling():
    """Sun's Ayana Bala is doubled by classical dispensation — can exceed the usual 60-Shashtiamsa cap."""
    calc = AyanaBalaCalculator()
    result = calc.calculate(_make_planet("sun", 0.0), _AYANAMSA)  # near max-north tropical position
    assert result.value_shashtiamsas > 60.0


def test_mercury_is_always_north_favoring_regardless_of_position():
    calc = AyanaBalaCalculator()
    north_result = calc.calculate(_make_planet("mercury", 10.0), _AYANAMSA)   # tropical ~34° (north half)
    south_result = calc.calculate(_make_planet("mercury", 190.0), _AYANAMSA)  # tropical ~214° (south half)
    assert "north-favoring" in north_result.trace[1]
    assert "north-favoring" in south_result.trace[1]


def test_rejects_rahu_ketu():
    calc = AyanaBalaCalculator()
    with pytest.raises(ValueError):
        calc.calculate(_make_planet("rahu", 10.0), _AYANAMSA)


def test_calculate_all_returns_7_classical_grahas():
    planets = [_make_planet(p, 10.0) for p in
               ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]]
    calc = AyanaBalaCalculator()
    results = calc.calculate_all(planets, _AYANAMSA)
    assert len(results) == 7
    assert "rahu" not in {r.planet for r in results}
