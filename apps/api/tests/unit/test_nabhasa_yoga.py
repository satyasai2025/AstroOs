"""
AstroOS — Nabhasa Yoga Unit Tests (Module 8, Phase 2)
"""

from apps.api.domain.ephemeris import DignityType, HouseCusp, SiderealPosition
from apps.api.services.yoga_engine import YogaEngine

_ZODIAC = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]


def _make_planet(planet, rashi, house_number=1):
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


def _all_seven_in(rashi_options):
    """Place all 7 classical grahas across the given rashi options, cycling."""
    return [
        _make_planet(planet, rashi_options[i % len(rashi_options)])
        for i, planet in enumerate(_CLASSICAL_SEVEN)
    ]


# ── Rajju Yoga (all movable) ───────────────────────────────────────────────────

def test_rajju_present_all_movable():
    planets = _all_seven_in(["aries", "cancer", "libra", "capricorn"])
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-NY-001")
    assert result.is_present is True


def test_rajju_absent_one_planet_outside_movable():
    planets = _all_seven_in(["aries", "cancer", "libra", "capricorn"])
    planets[0] = _make_planet("sun", "taurus")  # fixed sign, breaks it
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-NY-001")
    assert result.is_present is False
    assert any("sun" in m for m in result.missing)


def test_rajju_absent_when_planet_missing():
    chart = _make_chart([])
    result = _result(chart, "BPHS-NY-001")
    assert result.is_present is False


# ── Musala Yoga (all fixed) ────────────────────────────────────────────────────

def test_musala_present_all_fixed():
    planets = _all_seven_in(["taurus", "leo", "scorpio", "aquarius"])
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-NY-002")
    assert result.is_present is True


def test_musala_absent_mixed_modality():
    planets = _all_seven_in(["taurus", "leo", "scorpio", "aquarius"])
    planets[3] = _make_planet("mercury", "aries")  # movable, breaks it
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-NY-002")
    assert result.is_present is False


# ── Nala Yoga (all dual) ───────────────────────────────────────────────────────

def test_nala_present_all_dual():
    planets = _all_seven_in(["gemini", "virgo", "sagittarius", "pisces"])
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-NY-003")
    assert result.is_present is True


def test_nala_absent_mixed_modality():
    planets = _all_seven_in(["gemini", "virgo", "sagittarius", "pisces"])
    planets[6] = _make_planet("saturn", "scorpio")  # fixed, breaks it
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-NY-003")
    assert result.is_present is False


# ── Mutual exclusivity ─────────────────────────────────────────────────────────

def test_rajju_musala_nala_are_mutually_exclusive_in_practice():
    """A chart satisfying Rajju cannot simultaneously satisfy Musala or Nala."""
    planets = _all_seven_in(["aries", "cancer", "libra", "capricorn"])
    chart = _make_chart(planets)
    rajju = _result(chart, "BPHS-NY-001")
    musala = _result(chart, "BPHS-NY-002")
    nala = _result(chart, "BPHS-NY-003")
    assert rajju.is_present is True
    assert musala.is_present is False
    assert nala.is_present is False


def test_ashraya_yogas_use_only_classical_seven_not_nodes():
    """Rahu/Ketu placement must not affect Ashraya Yoga evaluation."""
    planets = _all_seven_in(["aries", "cancer", "libra", "capricorn"])
    planets.append(_make_planet("rahu", "taurus"))  # fixed sign — irrelevant to the 7-planet check
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-NY-001")
    assert result.is_present is True
