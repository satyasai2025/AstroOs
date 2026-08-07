"""
AstroOS — Karakamsa Engine Unit Tests
"""

import pytest

from apps.api.services.karakamsa_engine import KarakamsaEngine
from apps.api.tests.unit.jaimini_fixtures import make_d1_chart, make_d9_chart, make_planet

_D1_PLANETS = [
    make_planet("sun", "aries", 25.0),  # highest degree -> Atmakaraka
    make_planet("moon", "cancer", 10.0),
    make_planet("mars", "leo", 5.0),
    make_planet("mercury", "virgo", 20.0),
    make_planet("jupiter", "sagittarius", 15.0),
    make_planet("venus", "libra", 8.0),
    make_planet("saturn", "capricorn", 3.0),
]

_D9_SIGNS = {
    "sun": "sagittarius",
    "moon": "pisces",
    "mars": "gemini",
    "mercury": "scorpio",
    "jupiter": "leo",
    "venus": "aries",
    "saturn": "cancer",
}


def test_karakamsa_is_atmakaraka_d9_sign():
    d1 = make_d1_chart("leo", _D1_PLANETS)
    d9 = make_d9_chart(_D9_SIGNS, "sagittarius")
    result = KarakamsaEngine().compute(d1, d9, scheme="sapta_karaka")
    assert result.atmakaraka == "sun"
    assert result.karakamsa_rashi == "sagittarius"  # sun's D9 sign


def test_swamsa_is_d9_ascendant_sign():
    d1 = make_d1_chart("leo", _D1_PLANETS)
    d9 = make_d9_chart(_D9_SIGNS, "sagittarius")
    result = KarakamsaEngine().compute(d1, d9)
    assert result.swamsa_rashi == "sagittarius"  # the D9 lagna passed to make_d9_chart


def test_traceability_fields_carry_d1_context():
    d1 = make_d1_chart("leo", _D1_PLANETS)
    d9 = make_d9_chart(_D9_SIGNS, "sagittarius")
    result = KarakamsaEngine().compute(d1, d9)
    assert result.d1_atmakaraka_rashi == "aries"
    assert result.d1_lagna_rashi == "leo"


def test_relative_house_1_is_karakamsa_itself():
    d1 = make_d1_chart("leo", _D1_PLANETS)
    d9 = make_d9_chart(_D9_SIGNS, "sagittarius")
    result = KarakamsaEngine().compute(d1, d9)
    house1 = {h.house_number: h for h in result.relative_houses}[1]
    assert house1.rashi == result.karakamsa_rashi
    assert "sun" in house1.planets  # Sun's own D9 sign, so Sun occupies house 1 from Karakamsa by definition


def test_relative_houses_cover_all_12():
    d1 = make_d1_chart("leo", _D1_PLANETS)
    d9 = make_d9_chart(_D9_SIGNS, "sagittarius")
    result = KarakamsaEngine().compute(d1, d9)
    assert [h.house_number for h in result.relative_houses] == list(range(1, 13))


def test_rejects_non_d9_varga_chart():
    d1 = make_d1_chart("leo", _D1_PLANETS)
    not_d9 = make_d9_chart(_D9_SIGNS, "sagittarius")
    object.__setattr__(not_d9, "varga", "D10")  # frozen dataclass -> bypass via object.__setattr__
    with pytest.raises(ValueError):
        KarakamsaEngine().compute(d1, not_d9)


def test_missing_atmakaraka_in_d9_raises():
    d1 = make_d1_chart("leo", _D1_PLANETS)
    incomplete_signs = {k: v for k, v in _D9_SIGNS.items() if k != "sun"}
    d9 = make_d9_chart(incomplete_signs, "sagittarius")
    with pytest.raises(ValueError):
        KarakamsaEngine().compute(d1, d9)
