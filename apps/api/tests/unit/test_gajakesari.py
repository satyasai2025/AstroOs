"""
AstroOS — Gajakesari Yoga Unit Tests (Module 8)
"""

import pytest

from apps.api.domain.ephemeris import DignityType, HouseCusp, SiderealPosition
from apps.api.services.yoga_engine import YogaEngine

_ZODIAC = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]


def _make_planet(planet, house_number, rashi="aries", is_combust=False, dignity=DignityType.NEUTRAL):
    return SiderealPosition(
        planet=planet, sidereal_longitude=10.0, rashi=rashi, rashi_degree=10.0,
        house_number=house_number, nakshatra="ashwini", pada=1,
        is_retrograde=False, is_combust=is_combust, combustion_orb=None, dignity=dignity,
    )


def _make_chart(planets, lagna_rashi="aries"):
    lagna_index = _ZODIAC.index(lagna_rashi)
    houses = [
        HouseCusp(
            house_number=i + 1, longitude=float(((lagna_index + i) % 12) * 30),
            sidereal_longitude=float(((lagna_index + i) % 12) * 30),
            rashi=_ZODIAC[(lagna_index + i) % 12],
        )
        for i in range(12)
    ]

    class _FakeChart:
        pass

    chart = _FakeChart()
    chart.houses = houses
    chart.planets = planets
    chart.aspects = []
    return chart


def _result(chart):
    return YogaEngine().evaluate_one(chart, "BPHS-OMY-001")


def test_gajakesari_present_jupiter_kendra_from_moon():
    """Moon in house 1, Jupiter in house 4 (kendra from Moon), in own sign (not debilitated/combust)."""
    planets = [
        _make_planet("moon", house_number=1, rashi="cancer"),
        _make_planet("jupiter", house_number=4, rashi="sagittarius"),
    ]
    chart = _make_chart(planets)
    result = _result(chart)
    assert result.is_present is True
    assert result.strength == "full"


def test_gajakesari_absent_jupiter_not_in_kendra_from_moon():
    planets = [
        _make_planet("moon", house_number=1, rashi="cancer"),
        _make_planet("jupiter", house_number=2, rashi="leo"),
    ]
    chart = _make_chart(planets)
    result = _result(chart)
    assert result.is_present is False


def test_gajakesari_partial_strength_when_jupiter_debilitated():
    """Kendra condition met, but Jupiter debilitated (Capricorn) weakens it."""
    planets = [
        _make_planet("moon", house_number=1, rashi="cancer"),
        _make_planet("jupiter", house_number=4, rashi="capricorn"),
    ]
    chart = _make_chart(planets)
    result = _result(chart)
    # Jupiter IS debilitated in capricorn per classical tables
    assert result.is_present is True
    assert result.strength == "partial"
    assert any("debilitated" in m for m in result.missing)


def test_gajakesari_partial_strength_when_jupiter_combust():
    planets = [
        _make_planet("moon", house_number=1, rashi="cancer"),
        _make_planet("jupiter", house_number=4, rashi="capricorn", is_combust=True),
    ]
    chart = _make_chart(planets)
    result = _result(chart)
    assert result.strength == "partial"
    assert any("combust" in m for m in result.missing)


def test_gajakesari_absent_when_moon_missing():
    planets = [_make_planet("jupiter", house_number=4, rashi="capricorn")]
    chart = _make_chart(planets)
    result = _result(chart)
    assert result.is_present is False


def test_gajakesari_kendra_from_moon_not_from_lagna():
    """
    Jupiter in kendra from lagna but NOT from Moon must not fire — this
    is specifically a Moon-relative yoga, not a lagna-relative one.
    """
    planets = [
        _make_planet("moon", house_number=2, rashi="leo"),   # Moon not in house 1
        _make_planet("jupiter", house_number=4, rashi="scorpio"),  # kendra from lagna (house 1) but not from moon (house 2)
    ]
    chart = _make_chart(planets)
    result = _result(chart)
    # house 4 from reference house 2: offsets landing on 4 = (4-2+1)=3, not in {1,4,7,10}
    assert result.is_present is False
