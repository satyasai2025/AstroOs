"""
AstroOS — Sanyasa Yoga Unit Tests (Module 8, Phase 3)
"""

from apps.api.domain.ephemeris import DignityType, HouseCusp, SiderealPosition
from apps.api.services.yoga_engine import YogaEngine

_ZODIAC = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]


def _make_planet(planet, house_number, rashi="aries"):
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


def _result(chart, yoga_id):
    return YogaEngine().evaluate_one(chart, yoga_id)


def test_sy001_present_four_conjunct():
    planets = [
        _make_planet("sun", house_number=5), _make_planet("mars", house_number=5),
        _make_planet("mercury", house_number=5), _make_planet("jupiter", house_number=5),
    ]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-SY-001")
    assert result.is_present is True


def test_sy001_absent_only_three_conjunct():
    planets = [
        _make_planet("sun", house_number=5), _make_planet("mars", house_number=5),
        _make_planet("mercury", house_number=5),
    ]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-SY-001")
    assert result.is_present is False


def test_sy001_absent_when_no_planets():
    chart = _make_chart([])
    result = _result(chart, "BPHS-SY-001")
    assert result.is_present is False


def test_sy002_present_debilitated_lagna_lord_in_12th():
    """Lagna Aries: lord=mars. Mars in house 12, debilitated (cancer)."""
    planets = [_make_planet("mars", house_number=12, rashi="cancer")]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _result(chart, "BPHS-SY-002")
    assert result.is_present is True


def test_sy002_present_lagna_lord_conjunct_malefic_in_12th():
    planets = [
        _make_planet("mars", house_number=12, rashi="aries"),
        _make_planet("saturn", house_number=12, rashi="aries"),
    ]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _result(chart, "BPHS-SY-002")
    assert result.is_present is True


def test_sy002_absent_lagna_lord_in_12th_but_not_afflicted():
    """Mars in 12th, own sign (scorpio), no malefic conjunction."""
    planets = [_make_planet("mars", house_number=12, rashi="scorpio")]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _result(chart, "BPHS-SY-002")
    assert result.is_present is False


def test_sy002_absent_lagna_lord_not_in_12th():
    planets = [_make_planet("mars", house_number=3, rashi="cancer")]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _result(chart, "BPHS-SY-002")
    assert result.is_present is False


def test_sy002_absent_when_lagna_lord_missing():
    chart = _make_chart([], lagna_rashi="aries")
    result = _result(chart, "BPHS-SY-002")
    assert result.is_present is False
