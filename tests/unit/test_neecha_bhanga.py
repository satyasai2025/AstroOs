"""
AstroOS — Neecha Bhanga Raja Yoga Unit Tests (Module 8)
"""

import pytest

from apps.api.domain.ephemeris import DignityType, HouseCusp, SiderealPosition
from apps.api.services.yoga_engine import YogaEngine

_ZODIAC = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]


def _make_planet(planet, house_number, rashi):
    return SiderealPosition(
        planet=planet, sidereal_longitude=10.0, rashi=rashi, rashi_degree=10.0,
        house_number=house_number, nakshatra="ashwini", pada=1,
        is_retrograde=False, is_combust=False, combustion_orb=None, dignity=DignityType.NEUTRAL,
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


def _result(chart, yoga_id="BPHS-NBRY-001"):
    return YogaEngine().evaluate_one(chart, yoga_id)


# Sun debilitates in Libra. Libra's dispositor is Venus.
# Sun exalts in Aries — so exalted_in_sign("libra") is None (Sun exalts
# in Aries, not Libra) — need to pick condition-specific setups per test.

def test_not_debilitated_returns_absent_immediately():
    """A planet that isn't debilitated should short-circuit with a clear reason."""
    planets = [
        _make_planet("sun", house_number=1, rashi="aries"),  # exalted, not debilitated
        _make_planet("moon", house_number=1, rashi="aries"),
    ]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _result(chart)
    assert result.is_present is False
    assert "sun is not debilitated" in result.missing


def test_condition_a_dispositor_in_kendra_cancels():
    """
    Sun debilitated in Libra (dispositor venus). Place venus in a kendra
    house from lagna to satisfy condition (a).
    """
    planets = [
        _make_planet("sun", house_number=6, rashi="libra"),   # sun debilitated
        _make_planet("venus", house_number=4, rashi="taurus"),  # dispositor in kendra
        _make_planet("moon", house_number=2, rashi="taurus"),
    ]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _result(chart)
    assert result.is_present is True
    assert result.strength == "cancelled"
    assert any("(a)" in s for s in result.satisfied)


def test_condition_c_dispositor_exalted_cancels():
    """
    Sun debilitated in Libra (dispositor venus). Venus exalted in Pisces
    satisfies condition (c), even with venus NOT in a kendra house.
    """
    planets = [
        _make_planet("sun", house_number=6, rashi="libra"),
        _make_planet("venus", house_number=3, rashi="pisces"),  # venus exalted, house 3 = not kendra
        _make_planet("moon", house_number=8, rashi="scorpio"),
    ]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _result(chart)
    assert result.is_present is True
    assert any("(c)" in s for s in result.satisfied)


def test_no_cancellation_when_no_condition_met():
    """
    Sun debilitated in Libra. Dispositor venus not in kendra, not
    exalted; no planet's exaltation-lord condition met either.
    """
    planets = [
        _make_planet("sun", house_number=6, rashi="libra"),
        _make_planet("venus", house_number=3, rashi="gemini"),  # not kendra, not exalted
        _make_planet("moon", house_number=8, rashi="scorpio"),
    ]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _result(chart)
    assert result.is_present is False
    assert len(result.missing) >= 3  # all three conditions unmet, all reported


def test_dispositor_not_in_chart_all_conditions_unevaluable():
    """
    Sun debilitated in Libra, but venus (the dispositor) isn't in the
    chart at all — conditions (a) and (c) both depend on venus's
    position and must degrade gracefully, not crash.
    """
    planets = [
        _make_planet("sun", house_number=6, rashi="libra"),
        _make_planet("moon", house_number=2, rashi="taurus"),
    ]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _result(chart)
    assert result.is_present is False
    assert any("dispositor venus not found" in t.lower() for t in result.trace)


def test_all_nine_planets_have_independent_evaluators():
    ids = [f"BPHS-NBRY-{i:03d}" for i in range(1, 10)]
    chart = _make_chart([], lagna_rashi="aries")
    for yoga_id in ids:
        result = _result(chart, yoga_id)
        assert result is not None
        assert result.yoga_id == yoga_id


def test_result_reports_which_debilitation_sign_and_dispositor():
    planets = [
        _make_planet("sun", house_number=6, rashi="libra"),
        _make_planet("venus", house_number=4, rashi="taurus"),
        _make_planet("moon", house_number=2, rashi="taurus"),
    ]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _result(chart)
    assert "venus" in result.involved_planets  # the dispositor
    assert "sun" in result.involved_planets


def test_trace_covers_all_three_conditions():
    planets = [
        _make_planet("sun", house_number=6, rashi="libra"),
        _make_planet("venus", house_number=3, rashi="gemini"),
        _make_planet("moon", house_number=8, rashi="scorpio"),
    ]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _result(chart)
    trace_text = " ".join(result.trace)
    assert "(a)" in trace_text
    assert "(b)" in trace_text
    assert "(c)" in trace_text
