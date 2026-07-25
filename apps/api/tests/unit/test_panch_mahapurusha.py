"""
AstroOS — Panch Mahapurusha Yoga Unit Tests (Module 8)
"""

import pytest

from apps.api.domain.ephemeris import DignityType, HouseCusp, SiderealPosition
from apps.api.services.house_engine import HouseEngine
from apps.api.services.yoga_engine import YogaEngine
from apps.api.services.yoga_predicates import YogaContext

_ZODIAC = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]


def _make_planet(planet: str, house_number: int, rashi: str, dignity=DignityType.NEUTRAL) -> SiderealPosition:
    return SiderealPosition(
        planet=planet, sidereal_longitude=10.0, rashi=rashi, rashi_degree=10.0,
        house_number=house_number, nakshatra="ashwini", pada=1,
        is_retrograde=False, is_combust=False, combustion_orb=None, dignity=dignity,
    )


def _make_chart(planets, lagna_rashi="aries"):
    from apps.api.domain.horoscope import D1Chart

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


def _get_result(chart, yoga_id):
    engine = YogaEngine()
    return engine.evaluate_one(chart, yoga_id)


# ── Ruchaka Yoga (Mars) ────────────────────────────────────────────────────────

def test_ruchaka_present_own_sign_in_kendra():
    """Mars in Aries (own sign) in house 1 (kendra from itself as lagna)."""
    planets = [_make_planet("mars", house_number=1, rashi="aries")]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _get_result(chart, "BPHS-PM-001")
    assert result.is_present is True
    assert result.strength == "full"


def test_ruchaka_absent_own_sign_not_kendra():
    """Mars in own sign (Scorpio) but not in a kendra house."""
    planets = [_make_planet("mars", house_number=2, rashi="scorpio")]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _get_result(chart, "BPHS-PM-001")
    assert result.is_present is False
    assert any("not in kendra" in m for m in result.missing)


def test_ruchaka_absent_kendra_not_own_or_exalted():
    """Mars in kendra house but in a sign that's neither own nor exalted."""
    planets = [_make_planet("mars", house_number=1, rashi="gemini")]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _get_result(chart, "BPHS-PM-001")
    assert result.is_present is False


def test_ruchaka_absent_when_mars_missing():
    chart = _make_chart([], lagna_rashi="aries")
    result = _get_result(chart, "BPHS-PM-001")
    assert result.is_present is False
    assert "mars not found in chart" in result.missing


def test_ruchaka_present_via_exaltation():
    """Mars exalted in Capricorn, placed in a kendra house."""
    planets = [_make_planet("mars", house_number=4, rashi="capricorn")]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _get_result(chart, "BPHS-PM-001")
    assert result.is_present is True
    assert any("exalted" in s for s in result.satisfied)


# ── Each of the 5 sub-yogas fires independently ───────────────────────────────

@pytest.mark.parametrize("yoga_id,planet,own_rashi", [
    ("BPHS-PM-001", "mars", "aries"),
    ("BPHS-PM-002", "mercury", "gemini"),
    ("BPHS-PM-003", "jupiter", "sagittarius"),
    ("BPHS-PM-004", "venus", "taurus"),
    ("BPHS-PM-005", "saturn", "capricorn"),
])
def test_each_mahapurusha_yoga_fires_in_own_sign_kendra(yoga_id, planet, own_rashi):
    planets = [_make_planet(planet, house_number=1, rashi=own_rashi)]
    chart = _make_chart(planets, lagna_rashi=own_rashi)
    result = _get_result(chart, yoga_id)
    assert result.is_present is True


def test_mahapurusha_yogas_are_independent():
    """A chart with only Mars present should not accidentally fire Sasa Yoga."""
    planets = [_make_planet("mars", house_number=1, rashi="aries")]
    chart = _make_chart(planets, lagna_rashi="aries")
    ruchaka = _get_result(chart, "BPHS-PM-001")
    sasa = _get_result(chart, "BPHS-PM-005")
    assert ruchaka.is_present is True
    assert sasa.is_present is False


# ── Trace / satisfied / missing presence (auditability requirements) ─────────

def test_result_has_yoga_id_and_rule_version():
    planets = [_make_planet("mars", house_number=1, rashi="aries")]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _get_result(chart, "BPHS-PM-001")
    assert result.yoga_id == "BPHS-PM-001"
    assert result.rule_version == "1.0"
    assert result.source_text == "BPHS"


def test_result_has_nonempty_trace():
    planets = [_make_planet("mars", house_number=1, rashi="aries")]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _get_result(chart, "BPHS-PM-001")
    assert len(result.trace) > 0
    assert any("Step" in t for t in result.trace)


def test_result_reports_missing_when_not_present():
    planets = [_make_planet("mars", house_number=2, rashi="taurus")]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _get_result(chart, "BPHS-PM-001")
    assert result.is_present is False
    assert len(result.missing) > 0
