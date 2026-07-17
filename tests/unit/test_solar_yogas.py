"""
AstroOS — Solar Yoga Unit Tests (Module 8, Phase 3)
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


# ── Vosi (2nd from Sun) ────────────────────────────────────────────────────────

def test_vosi_present():
    planets = [_make_planet("sun", house_number=1), _make_planet("mars", house_number=2)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-OMY-002")
    assert result.is_present is True


def test_vosi_absent_only_moon_in_2nd():
    """Moon in the 2nd from Sun doesn't count — specifically excluded."""
    planets = [_make_planet("sun", house_number=1), _make_planet("moon", house_number=2)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-OMY-002")
    assert result.is_present is False


def test_vosi_absent_when_sun_missing():
    chart = _make_chart([])
    result = _result(chart, "BPHS-OMY-002")
    assert result.is_present is False


# ── Vasi (12th from Sun) ───────────────────────────────────────────────────────

def test_vasi_present():
    planets = [_make_planet("sun", house_number=1), _make_planet("venus", house_number=12)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-OMY-003")
    assert result.is_present is True


def test_vasi_absent_only_moon_in_12th():
    planets = [_make_planet("sun", house_number=1), _make_planet("moon", house_number=12)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-OMY-003")
    assert result.is_present is False


def test_vasi_absent_when_sun_missing():
    chart = _make_chart([])
    result = _result(chart, "BPHS-OMY-003")
    assert result.is_present is False


# ── Ubhayachari (both sides) ───────────────────────────────────────────────────

def test_ubhayachari_present_both_sides():
    planets = [
        _make_planet("sun", house_number=1),
        _make_planet("mars", house_number=2),
        _make_planet("venus", house_number=12),
    ]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-OMY-004")
    assert result.is_present is True


def test_ubhayachari_absent_only_one_side():
    planets = [_make_planet("sun", house_number=1), _make_planet("mars", house_number=2)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-OMY-004")
    assert result.is_present is False


def test_ubhayachari_absent_when_sun_missing():
    chart = _make_chart([])
    result = _result(chart, "BPHS-OMY-004")
    assert result.is_present is False


# ── Budhaditya ─────────────────────────────────────────────────────────────────

def test_budhaditya_present():
    planets = [_make_planet("sun", house_number=3), _make_planet("mercury", house_number=3)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-OMY-005")
    assert result.is_present is True


def test_budhaditya_absent_not_conjunct():
    planets = [_make_planet("sun", house_number=3), _make_planet("mercury", house_number=5)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-OMY-005")
    assert result.is_present is False


def test_budhaditya_absent_when_mercury_missing():
    planets = [_make_planet("sun", house_number=3)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-OMY-005")
    assert result.is_present is False


# ── Sun (not lagna) is the reference point ────────────────────────────────────

def test_solar_yogas_use_sun_not_lagna_as_reference():
    """Sun in house 5 (not house 1) — Vosi's '2nd house' must be house 6."""
    planets = [_make_planet("sun", house_number=5), _make_planet("mars", house_number=6)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-OMY-002")
    assert result.is_present is True
    assert 6 in result.involved_houses
