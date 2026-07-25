"""
AstroOS — Amala Yoga & Kalasarpa Yoga Unit Tests (Module 8, Phase 3)
"""

from apps.api.domain.ephemeris import DignityType, HouseCusp, SiderealPosition
from apps.api.services.yoga_engine import YogaEngine

_ZODIAC = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]


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


def test_amala_present_benefic_10th_from_lagna():
    """Lagna Aries: 10th house = house 10. Jupiter there."""
    planets = [_make_planet("jupiter", house_number=10)]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _result(chart, "BPHS-OMY-006")
    assert result.is_present is True


def test_amala_present_benefic_10th_from_moon():
    planets = [_make_planet("moon", house_number=1), _make_planet("venus", house_number=10)]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _result(chart, "BPHS-OMY-006")
    assert result.is_present is True


def test_amala_absent_only_malefic_in_10th():
    planets = [_make_planet("saturn", house_number=10)]
    chart = _make_chart(planets, lagna_rashi="aries")
    result = _result(chart, "BPHS-OMY-006")
    assert result.is_present is False


def test_amala_absent_no_benefic_either_reference():
    chart = _make_chart([], lagna_rashi="aries")
    result = _result(chart, "BPHS-OMY-006")
    assert result.is_present is False


def test_kalasarpa_present_all_confined_to_rahu_side():
    """Rahu house 1, Ketu house 7. All 7 classical grahas in houses 1-6."""
    planets = [_make_planet("rahu", house_number=1), _make_planet("ketu", house_number=7)]
    for i, planet in enumerate(_CLASSICAL_SEVEN):
        planets.append(_make_planet(planet, house_number=(i % 6) + 1))
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-OMY-007")
    assert result.is_present is True


def test_kalasarpa_absent_when_straddling():
    """One planet on the Ketu side breaks confinement to a single hemisphere."""
    planets = [_make_planet("rahu", house_number=1), _make_planet("ketu", house_number=7)]
    for i, planet in enumerate(_CLASSICAL_SEVEN[:-1]):
        planets.append(_make_planet(planet, house_number=(i % 6) + 1))
    planets.append(_make_planet(_CLASSICAL_SEVEN[-1], house_number=8))  # Ketu side — breaks it
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-OMY-007")
    assert result.is_present is False


def test_kalasarpa_absent_when_rahu_or_ketu_missing():
    chart = _make_chart([_make_planet("rahu", house_number=1)])
    result = _result(chart, "BPHS-OMY-007")
    assert result.is_present is False


def test_kalasarpa_present_all_confined_to_ketu_side():
    planets = [_make_planet("rahu", house_number=1), _make_planet("ketu", house_number=7)]
    for i, planet in enumerate(_CLASSICAL_SEVEN):
        planets.append(_make_planet(planet, house_number=(i % 6) + 7))
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-OMY-007")
    assert result.is_present is True
