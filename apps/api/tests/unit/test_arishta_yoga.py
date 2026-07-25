"""
AstroOS — Arishta Yoga Unit Tests (Module 8, Phase 2)
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


# ── Papakartari Yoga (Lagna) ───────────────────────────────────────────────────

def test_papakartari_present_malefics_both_sides():
    planets = [_make_planet("saturn", house_number=12), _make_planet("mars", house_number=2)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-ARY-001")
    assert result.is_present is True


def test_papakartari_absent_only_one_side():
    planets = [_make_planet("saturn", house_number=12)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-ARY-001")
    assert result.is_present is False


def test_papakartari_absent_benefics_not_malefics():
    planets = [_make_planet("jupiter", house_number=12), _make_planet("venus", house_number=2)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-ARY-001")
    assert result.is_present is False


# ── Malefics in Dusthana from Moon ─────────────────────────────────────────────

def test_malefics_from_moon_present():
    planets = [_make_planet("moon", house_number=1), _make_planet("saturn", house_number=6)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-ARY-002")
    assert result.is_present is True


def test_malefics_from_moon_absent_only_benefics():
    planets = [_make_planet("moon", house_number=1), _make_planet("jupiter", house_number=6)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-ARY-002")
    assert result.is_present is False


def test_malefics_from_moon_checks_all_three_houses():
    planets = [_make_planet("moon", house_number=1), _make_planet("rahu", house_number=8)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-ARY-002")
    assert result.is_present is True
    assert any("8th" in s for s in result.satisfied)


def test_malefics_from_moon_absent_when_moon_missing():
    chart = _make_chart([])
    result = _result(chart, "BPHS-ARY-002")
    assert result.is_present is False


# ── Shakata Yoga ───────────────────────────────────────────────────────────────

def test_shakata_present_moon_6th_from_jupiter():
    """Jupiter in a NON-kendra house (2nd) so cancellation doesn't apply."""
    planets = [_make_planet("jupiter", house_number=2), _make_planet("moon", house_number=7)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-ARY-003")
    assert result.is_present is True


def test_shakata_present_moon_8th_from_jupiter():
    planets = [_make_planet("jupiter", house_number=2), _make_planet("moon", house_number=9)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-ARY-003")
    assert result.is_present is True


def test_shakata_present_moon_12th_from_jupiter():
    planets = [_make_planet("jupiter", house_number=2), _make_planet("moon", house_number=1)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-ARY-003")
    assert result.is_present is True


def test_shakata_cancelled_when_jupiter_in_kendra_from_lagna():
    """rule_version 1.1: base condition met but Jupiter itself is in a kendra — cancelled."""
    planets = [_make_planet("jupiter", house_number=1), _make_planet("moon", house_number=6)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-ARY-003")
    assert result.is_present is False
    assert any("Cancelled" in s for s in result.satisfied)
    assert result.rule_version == "1.1"


def test_shakata_cancelled_when_jupiter_exalted():
    planets = [
        _make_planet("jupiter", house_number=2, rashi="cancer"),  # exalted, non-kendra house
        _make_planet("moon", house_number=7),
    ]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-ARY-003")
    assert result.is_present is False
    assert any("exalted" in s.lower() for s in result.satisfied)


def test_shakata_absent_moon_elsewhere():
    planets = [_make_planet("jupiter", house_number=1), _make_planet("moon", house_number=5)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-ARY-003")
    assert result.is_present is False


def test_shakata_notes_remaining_cancellation_exceptions_not_evaluated():
    """
    v1.1 implements the Jupiter-in-kendra and Jupiter-exalted exceptions,
    but other classical exceptions (e.g. aspected by benefics) remain
    unimplemented — the docstring should still make that explicit.
    """
    import apps.api.services.yogas.arishta_yoga as arishta_yoga_module
    doc = " ".join(arishta_yoga_module.evaluate_shakata_yoga.__doc__.lower().split())
    assert "not implemented" in doc


def test_shakata_absent_when_jupiter_missing():
    planets = [_make_planet("moon", house_number=6)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-ARY-003")
    assert result.is_present is False


# ── Descriptive, not predictive, framing (Design Audit product note) ─────────

def test_arishta_results_do_not_contain_predictive_language():
    """
    Per the Design Audit's product note: results should describe the
    classical condition present, not predict an outcome. Crude check for
    predictive words that should never appear in satisfied/missing text.
    """
    planets = [_make_planet("saturn", house_number=12), _make_planet("mars", house_number=2)]
    chart = _make_chart(planets)
    result = _result(chart, "BPHS-ARY-001")
    forbidden_words = ["death", "poverty", "will cause", "will suffer"]
    all_text = " ".join(result.satisfied) + " ".join(result.missing)
    for word in forbidden_words:
        assert word not in all_text.lower()
