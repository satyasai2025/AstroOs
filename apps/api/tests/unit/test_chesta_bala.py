"""
AstroOS — Chesta Bala Unit Tests (Module 9)

Formula was replaced (see chesta_bala.py's module docstring): the
earlier raw-speed-vs-mean-speed model was confirmed backwards (faster
direct motion should score HIGHER, not clamp to 0) and is replaced by
the classical Chesta Kendra method. Tests use real sidereal longitudes
plus the birth JD/ayanamsa (needed to reconstruct mean longitudes),
not just speed_deg_per_day.
"""

from datetime import datetime, timezone

import pytest

from apps.api.domain.ephemeris import DignityType, SiderealPosition
from apps.api.services.ephemeris_wrapper import datetime_to_jd
from apps.api.services.shadbala.chesta_bala import ChestaBalaCalculator

_JD = datetime_to_jd(datetime(1995, 1, 1, 12, 0, 0, tzinfo=timezone.utc))
_AYANAMSA = 23.78725828436319  # this project's own verified Lahiri ayanamsa for the reference chart


def _make_planet(planet, sidereal_longitude, speed=1.0, retrograde=False):
    return SiderealPosition(
        planet=planet, sidereal_longitude=sidereal_longitude, rashi="aries", rashi_degree=10.0,
        house_number=1, nakshatra="ashwini", pada=1, is_retrograde=retrograde,
        is_combust=False, combustion_orb=None, dignity=DignityType.NEUTRAL,
        speed_deg_per_day=speed,
    )


def test_reference_chart_no_longer_produces_false_zeros():
    """
    1995-01-01 12:00 UTC, New Delhi — the bug this replacement fixes:
    Mercury/Jupiter/Saturn previously scored exactly 0.0 (clamped) with
    the old speed-vs-constant formula despite moving at ordinary direct
    speed. None should be exactly 0 now.
    """
    longitudes = {
        "mars": 128.8693, "mercury": 267.4526, "jupiter": 221.0448,
        "venus": 210.5277, "saturn": 314.2452,
    }
    planets = [_make_planet(p, lon) for p, lon in longitudes.items()]
    calc = ChestaBalaCalculator()
    results = calc.calculate_all(planets, _JD, _AYANAMSA)
    assert len(results) == 5
    for r in results:
        assert r.value_shashtiamsas > 0.0, f"{r.planet} incorrectly scored 0"
        assert 0.0 <= r.value_shashtiamsas <= 60.0, f"{r.planet} out of 0-60 range"


def test_rejects_sun_and_moon():
    calc = ChestaBalaCalculator()
    with pytest.raises(ValueError):
        calc.calculate(_make_planet("sun", 100.0), _JD, _AYANAMSA)
    with pytest.raises(ValueError):
        calc.calculate(_make_planet("moon", 100.0), _JD, _AYANAMSA)


def test_rejects_rahu_ketu():
    calc = ChestaBalaCalculator()
    with pytest.raises(ValueError):
        calc.calculate(_make_planet("rahu", 100.0), _JD, _AYANAMSA)


def test_calculate_all_returns_only_the_5_scoped_planets():
    planets = [_make_planet(p, 10.0 * i) for i, p in enumerate(
        ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]
    )]
    calc = ChestaBalaCalculator()
    results = calc.calculate_all(planets, _JD, _AYANAMSA)
    result_planets = {r.planet for r in results}
    assert result_planets == {"mars", "mercury", "jupiter", "venus", "saturn"}


def test_superior_planet_uses_suns_mean_longitude_as_seeghrocha():
    result = ChestaBalaCalculator().calculate(_make_planet("mars", 128.8693), _JD, _AYANAMSA)
    assert "Sun's mean longitude" in result.trace[0]


def test_inferior_planet_uses_own_mean_longitude_as_seeghrocha():
    result = ChestaBalaCalculator().calculate(_make_planet("mercury", 267.4526), _JD, _AYANAMSA)
    assert "own mean longitude" in result.trace[0]
