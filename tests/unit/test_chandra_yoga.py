"""
AstroOS — Chandra Yoga Unit Tests (Module 8, Phase 2)
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


# ── Sunapha / Anapha / Durudhara ──────────────────────────────────────────────

def test_sunapha_present():
    planets = [_make_planet("moon", house_number=1), _make_planet("mars", house_number=2)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-CY-001")
    assert result.is_present is True


def test_sunapha_absent_only_sun_in_2nd():
    """Sun in the 2nd from Moon doesn't count — it's specifically excluded."""
    planets = [_make_planet("moon", house_number=1), _make_planet("sun", house_number=2)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-CY-001")
    assert result.is_present is False


def test_sunapha_absent_when_moon_missing():
    chart = _make_chart([])
    result = _result(chart, "BPHS-CY-001")
    assert result.is_present is False
    assert "moon not found in chart" in result.missing


def test_anapha_absent_when_moon_missing():
    chart = _make_chart([])
    result = _result(chart, "BPHS-CY-002")
    assert result.is_present is False


def test_durudhara_absent_when_moon_missing():
    chart = _make_chart([])
    result = _result(chart, "BPHS-CY-003")
    assert result.is_present is False


def test_adhi_yoga_absent_when_moon_missing():
    chart = _make_chart([])
    result = _result(chart, "BPHS-CY-005")
    assert result.is_present is False


def test_anapha_present():
    planets = [_make_planet("moon", house_number=1), _make_planet("venus", house_number=12)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-CY-002")
    assert result.is_present is True


def test_durudhara_requires_both_sides():
    planets = [
        _make_planet("moon", house_number=1),
        _make_planet("mars", house_number=2),
        _make_planet("venus", house_number=12),
    ]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-CY-003")
    assert result.is_present is True


def test_durudhara_absent_only_one_side():
    planets = [_make_planet("moon", house_number=1), _make_planet("mars", house_number=2)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-CY-003")
    assert result.is_present is False


# ── Kemadruma ──────────────────────────────────────────────────────────────────

def test_kemadruma_present_when_moon_isolated():
    """Moon isolated in a NON-kendra house (2nd) — not cancelled by kendra placement."""
    planets = [_make_planet("moon", house_number=2)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-CY-004")
    assert result.is_present is True


def test_kemadruma_cancelled_when_moon_in_kendra_from_lagna():
    """
    rule_version 1.1: base condition met (Moon isolated) but Moon itself
    is in a kendra from lagna — cancellation applies, yoga does not
    manifest.
    """
    planets = [_make_planet("moon", house_number=1)]  # house 1 is a kendra
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-CY-004")
    assert result.is_present is False
    assert any("Cancelled" in s for s in result.satisfied)
    assert result.rule_version == "1.1"


def test_kemadruma_absent_when_planet_conjunct_moon():
    planets = [_make_planet("moon", house_number=1), _make_planet("mars", house_number=1)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-CY-004")
    assert result.is_present is False


def test_kemadruma_absent_when_planet_in_2nd_from_moon():
    planets = [_make_planet("moon", house_number=1), _make_planet("mars", house_number=2)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-CY-004")
    assert result.is_present is False


def test_kemadruma_notes_remaining_cancellation_exceptions_not_evaluated():
    """
    v1.1 implements the Moon-in-kendra-from-lagna exception, but other
    classical exceptions (aspect-based, etc.) remain unimplemented — the
    docstring should still make that explicit.
    """
    import apps.api.services.yogas.chandra_yoga as chandra_yoga_module
    doc = " ".join(chandra_yoga_module.evaluate_kemadruma.__doc__.lower().split())
    assert "not implemented" in doc


# ── Adhi Yoga ──────────────────────────────────────────────────────────────────

def test_adhi_yoga_full_strength_all_three_houses():
    planets = [
        _make_planet("moon", house_number=1),
        _make_planet("jupiter", house_number=6),   # benefic
        _make_planet("venus", house_number=7),     # benefic
        _make_planet("mercury", house_number=8),   # benefic
    ]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-CY-005")
    assert result.is_present is True
    assert result.strength == "full"


def test_adhi_yoga_partial_strength_one_house():
    planets = [_make_planet("moon", house_number=1), _make_planet("jupiter", house_number=6)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-CY-005")
    assert result.is_present is True
    assert result.strength == "partial"


def test_adhi_yoga_absent_no_benefics():
    planets = [
        _make_planet("moon", house_number=1),
        _make_planet("saturn", house_number=6),  # malefic, doesn't count
    ]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-CY-005")
    assert result.is_present is False


# ── Chandra-Mangala Yoga ───────────────────────────────────────────────────────

def test_chandra_mangala_present_conjunct():
    planets = [_make_planet("moon", house_number=3), _make_planet("mars", house_number=3)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-CY-006")
    assert result.is_present is True


def test_chandra_mangala_absent_unrelated():
    planets = [_make_planet("moon", house_number=3), _make_planet("mars", house_number=8)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-CY-006")
    assert result.is_present is False


def test_chandra_mangala_absent_when_mars_missing():
    planets = [_make_planet("moon", house_number=3)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-CY-006")
    assert result.is_present is False


# ── General: houses-from-Moon primitive reused correctly ──────────────────────

def test_all_chandra_yogas_use_moon_not_lagna_as_reference():
    """
    Moon in house 5 (not house 1) — Sunapha's '2nd house' must be house 6
    (from Moon), not house 2 (from lagna).
    """
    planets = [_make_planet("moon", house_number=5), _make_planet("mars", house_number=6)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-CY-001")
    assert result.is_present is True
    assert 6 in result.involved_houses
