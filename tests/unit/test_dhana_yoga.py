"""
AstroOS — Dhana Yoga Unit Tests (Module 8)
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


# ── BPHS-DY-001: 2nd-11th lord association ────────────────────────────────────

def test_dy001_present_lords_conjunct():
    """Lagna Aries: 2nd house=Taurus (lord venus), 11th house=Aquarius (lord saturn)."""
    planets = [
        _make_planet("venus", house_number=5),
        _make_planet("saturn", house_number=5),  # conjunct with venus
    ]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _result(chart, "BPHS-DY-001")
    assert result.is_present is True
    assert result.strength == "full"


def test_dy001_absent_lords_unrelated():
    planets = [
        _make_planet("venus", house_number=3),
        _make_planet("saturn", house_number=8),
    ]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _result(chart, "BPHS-DY-001")
    assert result.is_present is False


def test_dy001_not_evaluable_when_same_lord():
    """
    Construct a lagna where the 2nd and 11th house share the same lord —
    this rule should report is_present=False via the "same planet" path,
    not a false positive.
    """
    # Lagna Pisces: 2nd house=Aries (lord mars), 11th house=Capricorn (lord saturn) -- not same.
    # Need a lagna where houses 2 and 11 land on signs sharing a lord.
    # Aquarius and Capricorn are both ruled by saturn (classically) --
    # if lagna is chosen so 2nd=Capricorn and 11th=Aquarius, same lord.
    # Lagna=Sagittarius: house2=Capricorn(saturn), house11=Libra... not matching.
    # Simplify: lagna=Capricorn: house2=Aquarius(saturn), house11=Scorpio(mars) -- no match.
    # Use lagna=Aquarius: house2=Pisces(jupiter), house11=Sagittarius(jupiter) -- match!
    chart = _make_chart([], lagna_rashi="aquarius")
    result = _result(chart, "BPHS-DY-001")
    assert result.is_present is False
    assert "does not apply" in result.missing[0] or any("same planet" in m for m in result.missing)


# ── BPHS-DY-002: 11th lord in kendra/trikona ──────────────────────────────────

def test_dy002_present_lord_in_kendra():
    """Lagna Aries: 11th house=Aquarius, lord=saturn. Place saturn in house 4 (kendra)."""
    planets = [_make_planet("saturn", house_number=4)]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _result(chart, "BPHS-DY-002")
    assert result.is_present is True


def test_dy002_present_lord_in_trikona():
    planets = [_make_planet("saturn", house_number=9)]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _result(chart, "BPHS-DY-002")
    assert result.is_present is True


def test_dy002_absent_lord_elsewhere():
    planets = [_make_planet("saturn", house_number=3)]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _result(chart, "BPHS-DY-002")
    assert result.is_present is False


def test_dy002_absent_when_lord_missing():
    chart = _make_chart([], lagna_rashi="aries")
    result = _result(chart, "BPHS-DY-002")
    assert result.is_present is False
    assert any("not found" in m for m in result.missing)


def test_dy002_trace_includes_lordship_lookup():
    planets = [_make_planet("saturn", house_number=4)]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _result(chart, "BPHS-DY-002")
    assert any("get_house_lord" in t for t in result.trace)
