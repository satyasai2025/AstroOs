"""
AstroOS — Paksha Bala Unit Tests (Module 9 Phase 2)
"""

import pytest

from apps.api.domain.ephemeris import DignityType, SiderealPosition
from apps.api.services.shadbala.paksha_bala import PakshaBalaCalculator


def _make_planet(planet, sidereal_longitude):
    return SiderealPosition(
        planet=planet, sidereal_longitude=sidereal_longitude, rashi="aries", rashi_degree=10.0,
        house_number=1, nakshatra="ashwini", pada=1, is_retrograde=False,
        is_combust=False, combustion_orb=None, dignity=DignityType.NEUTRAL,
    )


def test_full_moon_maximizes_benefic_bala():
    """Moon exactly 180 degrees from Sun (full moon) — benefics at maximum."""
    planets = [_make_planet("sun", 0.0), _make_planet("moon", 180.0), _make_planet("jupiter", 50.0)]
    calc = PakshaBalaCalculator()
    result = calc.calculate("jupiter", planets)
    assert result.value_shashtiamsas == pytest.approx(60.0, abs=1e-4)


def test_new_moon_minimizes_benefic_bala():
    """Moon conjunct Sun (new moon) — benefics at minimum."""
    planets = [_make_planet("sun", 0.0), _make_planet("moon", 0.0), _make_planet("jupiter", 50.0)]
    calc = PakshaBalaCalculator()
    result = calc.calculate("jupiter", planets)
    assert result.value_shashtiamsas == pytest.approx(0.0, abs=1e-4)


def test_new_moon_maximizes_malefic_bala():
    planets = [_make_planet("sun", 0.0), _make_planet("moon", 0.0), _make_planet("saturn", 50.0)]
    calc = PakshaBalaCalculator()
    result = calc.calculate("saturn", planets)
    assert result.value_shashtiamsas == pytest.approx(60.0, abs=1e-4)


def test_full_moon_minimizes_malefic_bala():
    planets = [_make_planet("sun", 0.0), _make_planet("moon", 180.0), _make_planet("saturn", 50.0)]
    calc = PakshaBalaCalculator()
    result = calc.calculate("saturn", planets)
    assert result.value_shashtiamsas == pytest.approx(0.0, abs=1e-4)


def test_benefic_and_malefic_at_same_elongation_sum_to_60():
    planets = [_make_planet("sun", 0.0), _make_planet("moon", 75.0), _make_planet("jupiter", 50.0), _make_planet("saturn", 50.0)]
    calc = PakshaBalaCalculator()
    benefic = calc.calculate("jupiter", planets)
    malefic = calc.calculate("saturn", planets)
    assert benefic.value_shashtiamsas + malefic.value_shashtiamsas == pytest.approx(60.0, abs=1e-3)


def test_quarter_moon_gives_half_bala():
    """90 degrees elongation (quarter moon) is the midpoint — 30 Shashtiamsas."""
    planets = [_make_planet("sun", 0.0), _make_planet("moon", 90.0), _make_planet("jupiter", 50.0)]
    calc = PakshaBalaCalculator()
    result = calc.calculate("jupiter", planets)
    assert result.value_shashtiamsas == pytest.approx(30.0, abs=1e-4)


def test_symmetric_around_full_moon():
    """Waxing 120 deg and waning-equivalent 240 deg (both 60 from full moon) must match."""
    calc = PakshaBalaCalculator()
    waxing = [_make_planet("sun", 0.0), _make_planet("moon", 120.0), _make_planet("jupiter", 50.0)]
    waning = [_make_planet("sun", 0.0), _make_planet("moon", 240.0), _make_planet("jupiter", 50.0)]
    result_waxing = calc.calculate("jupiter", waxing)
    result_waning = calc.calculate("jupiter", waning)
    assert result_waxing.value_shashtiamsas == pytest.approx(result_waning.value_shashtiamsas, abs=1e-4)


def test_missing_sun_or_moon_degrades_gracefully():
    planets = [_make_planet("jupiter", 50.0)]
    calc = PakshaBalaCalculator()
    result = calc.calculate("jupiter", planets)
    assert result.value_shashtiamsas == 0.0
    assert "not found" in result.trace[0]


def test_rejects_rahu_ketu():
    calc = PakshaBalaCalculator()
    with pytest.raises(ValueError):
        calc.calculate("rahu", [])


def test_calculate_all_returns_7_classical_grahas():
    planets = [_make_planet("sun", 0.0), _make_planet("moon", 90.0)]
    calc = PakshaBalaCalculator()
    results = calc.calculate_all(planets)
    assert len(results) == 7
    assert {r.planet for r in results} == {
        "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"
    }
