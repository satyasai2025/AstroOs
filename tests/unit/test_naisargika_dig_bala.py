"""
AstroOS — Naisargika Bala & Dig Bala Unit Tests (Module 9 Phase 1)
"""

import pytest

from apps.api.domain.ephemeris import DignityType, HouseCusp, SiderealPosition
from apps.api.services.shadbala.dig_bala import DigBalaCalculator
from apps.api.services.shadbala.naisargika_bala import NaisargikaBalaCalculator

_ZODIAC = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]


def _make_houses(lagna_rashi="aries"):
    lagna_index = _ZODIAC.index(lagna_rashi)
    return [
        HouseCusp(
            house_number=i + 1, longitude=float(((lagna_index + i) % 12) * 30),
            sidereal_longitude=float(((lagna_index + i) % 12) * 30),
            rashi=_ZODIAC[(lagna_index + i) % 12],
        )
        for i in range(12)
    ]


def _make_planet(planet, sidereal_longitude, house_number=1):
    return SiderealPosition(
        planet=planet, sidereal_longitude=sidereal_longitude, rashi="aries", rashi_degree=10.0,
        house_number=house_number, nakshatra="ashwini", pada=1,
        is_retrograde=False, is_combust=False, combustion_orb=None, dignity=DignityType.NEUTRAL,
    )


# ── Naisargika Bala ────────────────────────────────────────────────────────────

def test_naisargika_sun_strongest():
    calc = NaisargikaBalaCalculator()
    assert calc.calculate("sun").value_shashtiamsas == pytest.approx(60.0)


def test_naisargika_saturn_weakest():
    calc = NaisargikaBalaCalculator()
    assert calc.calculate("saturn").value_shashtiamsas == pytest.approx(60.0 / 7.0, abs=1e-3)


def test_naisargika_descending_order():
    calc = NaisargikaBalaCalculator()
    order = ["sun", "moon", "venus", "jupiter", "mercury", "mars", "saturn"]
    values = [calc.calculate(p).value_shashtiamsas for p in order]
    assert values == sorted(values, reverse=True)


def test_naisargika_rejects_rahu_ketu():
    calc = NaisargikaBalaCalculator()
    with pytest.raises(ValueError):
        calc.calculate("rahu")


def test_naisargika_calculate_all_returns_7():
    calc = NaisargikaBalaCalculator()
    results = calc.calculate_all()
    assert len(results) == 7
    assert {r.planet for r in results} == {
        "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"
    }


def test_naisargika_has_stable_component_id_and_version():
    calc = NaisargikaBalaCalculator()
    r = calc.calculate("sun")
    assert r.component_id == "SHADBALA-NAISARGIKA"
    assert r.rule_version == "1.0"
    assert len(r.trace) > 0


# ── Dig Bala ───────────────────────────────────────────────────────────────────

def test_dig_bala_exactly_at_digbala_point_scores_60():
    """Sun exactly on the 10th cusp (its digbala point) must score exactly 60."""
    houses = _make_houses(lagna_rashi="aries")  # house 10 = capricorn = 270 deg
    sun = _make_planet("sun", sidereal_longitude=270.0)
    calc = DigBalaCalculator()
    result = calc.calculate("sun", sun, houses)
    assert result.value_shashtiamsas == pytest.approx(60.0, abs=1e-6)


def test_dig_bala_exactly_opposite_digbala_point_scores_0():
    """Sun exactly opposite its digbala point (the 4th cusp) must score exactly 0."""
    houses = _make_houses(lagna_rashi="aries")  # house 4 = cancer = 90 deg
    sun = _make_planet("sun", sidereal_longitude=90.0)
    calc = DigBalaCalculator()
    result = calc.calculate("sun", sun, houses)
    assert result.value_shashtiamsas == pytest.approx(0.0, abs=1e-6)


def test_dig_bala_halfway_scores_30():
    """Exactly 90 degrees from the digbala point should score 30 (midpoint)."""
    houses = _make_houses(lagna_rashi="aries")  # house 10 = capricorn = 270 deg
    sun = _make_planet("sun", sidereal_longitude=0.0)  # 90 deg from 270
    calc = DigBalaCalculator()
    result = calc.calculate("sun", sun, houses)
    assert result.value_shashtiamsas == pytest.approx(30.0, abs=1e-6)


@pytest.mark.parametrize("planet,digbala_house", [
    ("sun", 10), ("mars", 10), ("moon", 4), ("venus", 4),
    ("jupiter", 1), ("mercury", 1), ("saturn", 7),
])
def test_dig_bala_correct_digbala_house_per_planet(planet, digbala_house):
    houses = _make_houses(lagna_rashi="aries")
    cusp_longitude = next(h.sidereal_longitude for h in houses if h.house_number == digbala_house)
    p = _make_planet(planet, sidereal_longitude=cusp_longitude)
    calc = DigBalaCalculator()
    result = calc.calculate(planet, p, houses)
    assert result.value_shashtiamsas == pytest.approx(60.0, abs=1e-6)


def test_dig_bala_rejects_rahu_ketu():
    houses = _make_houses()
    p = _make_planet("rahu", 0.0)
    calc = DigBalaCalculator()
    with pytest.raises(ValueError):
        calc.calculate("rahu", p, houses)


def test_dig_bala_values_always_between_0_and_60():
    houses = _make_houses(lagna_rashi="leo")
    calc = DigBalaCalculator()
    for planet in ["sun", "mars", "moon", "venus", "jupiter", "mercury", "saturn"]:
        for lon in [0.0, 45.0, 123.0, 200.0, 359.0]:
            p = _make_planet(planet, lon)
            result = calc.calculate(planet, p, houses)
            assert 0.0 <= result.value_shashtiamsas <= 60.0


def test_dig_bala_calculate_all_skips_missing_planets():
    houses = _make_houses()
    planets = [_make_planet("sun", 270.0)]
    calc = DigBalaCalculator()
    results = calc.calculate_all(planets, houses)
    assert len(results) == 1
    assert results[0].planet == "sun"


def test_dig_bala_trace_documents_digbala_point():
    houses = _make_houses(lagna_rashi="aries")
    sun = _make_planet("sun", sidereal_longitude=270.0)
    calc = DigBalaCalculator()
    result = calc.calculate("sun", sun, houses)
    assert any("digbala point" in t.lower() for t in result.trace)
