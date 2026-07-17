"""
AstroOS — Chesta Bala Unit Tests (Module 9 Phase 2)
"""

import pytest

from apps.api.domain.ephemeris import DignityType, SiderealPosition
from apps.api.services.shadbala.chesta_bala import ChestaBalaCalculator


def _make_planet(planet, speed_deg_per_day, is_retrograde=False):
    return SiderealPosition(
        planet=planet, sidereal_longitude=10.0, rashi="aries", rashi_degree=10.0,
        house_number=1, nakshatra="ashwini", pada=1, is_retrograde=is_retrograde,
        is_combust=False, combustion_orb=None, dignity=DignityType.NEUTRAL,
        speed_deg_per_day=speed_deg_per_day,
    )


def test_retrograde_gives_maximum_bala():
    calc = ChestaBalaCalculator()
    p = _make_planet("mars", speed_deg_per_day=-0.3, is_retrograde=True)
    result = calc.calculate(p)
    assert result.value_shashtiamsas == pytest.approx(60.0)


def test_near_stationary_gives_maximum_bala():
    calc = ChestaBalaCalculator()
    p = _make_planet("saturn", speed_deg_per_day=0.001, is_retrograde=False)
    result = calc.calculate(p)
    assert result.value_shashtiamsas == pytest.approx(60.0)


def test_speed_at_or_above_mean_gives_zero():
    calc = ChestaBalaCalculator()
    p = _make_planet("mars", speed_deg_per_day=0.524, is_retrograde=False)  # exactly mean
    result = calc.calculate(p)
    assert result.value_shashtiamsas == pytest.approx(0.0, abs=1e-6)


def test_speed_above_mean_clamps_at_zero_not_negative():
    calc = ChestaBalaCalculator()
    p = _make_planet("mars", speed_deg_per_day=2.0, is_retrograde=False)  # well above mean
    result = calc.calculate(p)
    assert result.value_shashtiamsas == pytest.approx(0.0, abs=1e-6)


def test_speed_at_half_mean_gives_half_bala():
    calc = ChestaBalaCalculator()
    p = _make_planet("mars", speed_deg_per_day=0.262, is_retrograde=False)  # half of 0.524
    result = calc.calculate(p)
    assert result.value_shashtiamsas == pytest.approx(30.0, abs=0.5)


def test_rejects_sun_and_moon():
    """Sun/Moon use different classical treatment, not scored by this calculator."""
    calc = ChestaBalaCalculator()
    with pytest.raises(ValueError):
        calc.calculate(_make_planet("sun", speed_deg_per_day=0.9))
    with pytest.raises(ValueError):
        calc.calculate(_make_planet("moon", speed_deg_per_day=13.0))


def test_rejects_rahu_ketu():
    calc = ChestaBalaCalculator()
    with pytest.raises(ValueError):
        calc.calculate(_make_planet("rahu", speed_deg_per_day=0.05))


def test_calculate_all_returns_5_planets():
    calc = ChestaBalaCalculator()
    planets = [
        _make_planet(p, 0.1) for p in ["mars", "mercury", "jupiter", "venus", "saturn", "sun", "moon"]
    ]
    results = calc.calculate_all(planets)
    assert len(results) == 5
    assert {r.planet for r in results} == {"mars", "mercury", "jupiter", "venus", "saturn"}


def test_value_always_between_0_and_60():
    calc = ChestaBalaCalculator()
    for speed in [-5.0, -0.5, 0.0, 0.001, 0.5, 1.0, 5.0]:
        for planet in ["mars", "mercury", "jupiter", "venus", "saturn"]:
            p = _make_planet(planet, speed, is_retrograde=(speed < 0))
            result = calc.calculate(p)
            assert 0.0 <= result.value_shashtiamsas <= 60.0
