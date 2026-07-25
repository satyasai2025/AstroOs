"""
AstroOS — Uchcha Bala & Kendradi Bala Unit Tests (Module 9 Phase 2)
"""

import pytest

from apps.api.domain.ephemeris import DignityType, SiderealPosition
from apps.api.services.shadbala.kendradi_bala import KendradiBalaCalculator
from apps.api.services.shadbala.uchcha_bala import UchchaBalaCalculator


def _make_planet(planet, sidereal_longitude=10.0, house_number=1):
    return SiderealPosition(
        planet=planet, sidereal_longitude=sidereal_longitude, rashi="aries", rashi_degree=10.0,
        house_number=house_number, nakshatra="ashwini", pada=1, is_retrograde=False,
        is_combust=False, combustion_orb=None, dignity=DignityType.NEUTRAL,
    )


# ── Uchcha Bala ────────────────────────────────────────────────────────────────

def test_uchcha_bala_at_exact_exaltation_scores_60():
    """Sun exalts at exactly 10 degrees Aries = absolute longitude 10.0."""
    calc = UchchaBalaCalculator()
    p = _make_planet("sun", sidereal_longitude=10.0)
    result = calc.calculate(p)
    assert result.value_shashtiamsas == pytest.approx(60.0, abs=1e-6)


def test_uchcha_bala_at_exact_debilitation_scores_0():
    """Sun's debilitation is always exactly 180 degrees from exaltation → absolute 190.0."""
    calc = UchchaBalaCalculator()
    p = _make_planet("sun", sidereal_longitude=190.0)
    result = calc.calculate(p)
    assert result.value_shashtiamsas == pytest.approx(0.0, abs=1e-6)


def test_uchcha_bala_halfway_scores_30():
    calc = UchchaBalaCalculator()
    p = _make_planet("sun", sidereal_longitude=100.0)  # 90 deg from 10.0
    result = calc.calculate(p)
    assert result.value_shashtiamsas == pytest.approx(30.0, abs=1e-6)


def test_uchcha_bala_rejects_rahu_ketu():
    calc = UchchaBalaCalculator()
    with pytest.raises(ValueError):
        calc.calculate(_make_planet("rahu"))


def test_uchcha_bala_values_always_between_0_and_60():
    calc = UchchaBalaCalculator()
    for planet in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]:
        for lon in [0.0, 45.0, 123.0, 200.0, 359.0]:
            result = calc.calculate(_make_planet(planet, sidereal_longitude=lon))
            assert 0.0 <= result.value_shashtiamsas <= 60.0


def test_uchcha_bala_calculate_all_returns_7():
    calc = UchchaBalaCalculator()
    planets = [_make_planet(p) for p in
               ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]]
    results = calc.calculate_all(planets)
    assert len(results) == 7
    assert "rahu" not in {r.planet for r in results}


# ── Kendradi Bala ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("house", [1, 4, 7, 10])
def test_kendradi_bala_kendra_scores_60(house):
    calc = KendradiBalaCalculator()
    result = calc.calculate(_make_planet("sun", house_number=house))
    assert result.value_shashtiamsas == pytest.approx(60.0)


@pytest.mark.parametrize("house", [2, 5, 8, 11])
def test_kendradi_bala_panapara_scores_30(house):
    calc = KendradiBalaCalculator()
    result = calc.calculate(_make_planet("sun", house_number=house))
    assert result.value_shashtiamsas == pytest.approx(30.0)


@pytest.mark.parametrize("house", [3, 6, 9, 12])
def test_kendradi_bala_apoklima_scores_15(house):
    calc = KendradiBalaCalculator()
    result = calc.calculate(_make_planet("sun", house_number=house))
    assert result.value_shashtiamsas == pytest.approx(15.0)


def test_kendradi_bala_rejects_rahu_ketu():
    calc = KendradiBalaCalculator()
    with pytest.raises(ValueError):
        calc.calculate(_make_planet("rahu", house_number=1))


def test_kendradi_bala_calculate_all_filters_to_7_classical():
    calc = KendradiBalaCalculator()
    planets = [_make_planet(p, house_number=1) for p in
               ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]]
    results = calc.calculate_all(planets)
    assert len(results) == 7
    assert "rahu" not in {r.planet for r in results}
