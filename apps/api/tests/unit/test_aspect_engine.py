"""
AstroOS — AspectEngine Unit Tests (Module 6.5 — Foundation Completion)

Pure unit coverage using synthetic planet positions — no Swiss Ephemeris
dependency. See tests/integration/test_aspect_engine_integration.py for
coverage against real computed charts.
"""

import pytest

from apps.api.domain.ephemeris import DignityType, SiderealPosition
from apps.api.services.aspect_engine import ASPECT_ORB, AspectEngine, SPECIAL_ASPECTS, UNIVERSAL_ASPECT


@pytest.fixture
def engine() -> AspectEngine:
    return AspectEngine()


def _make_planet(planet: str, house_number: int, rashi_degree: float = 15.0) -> SiderealPosition:
    return SiderealPosition(
        planet=planet, sidereal_longitude=float(house_number - 1) * 30 + rashi_degree,
        rashi="aries", rashi_degree=rashi_degree, house_number=house_number,
        nakshatra="ashwini", pada=1, is_retrograde=False, is_combust=False,
        combustion_orb=None, dignity=DignityType.NEUTRAL,
    )


# ── Classification ────────────────────────────────────────────────────────────

def test_classify_conjunction(engine):
    assert engine.classify(1) == "conjunction"


def test_classify_opposition(engine):
    assert engine.classify(7) == "opposition"


def test_classify_trine(engine):
    assert engine.classify(5) == "trine"
    assert engine.classify(9) == "trine"


def test_classify_square(engine):
    assert engine.classify(4) == "square"
    assert engine.classify(10) == "square"


def test_classify_special_graha(engine):
    """Any offset not in the standard set (e.g. Mars's 8th) is special_graha."""
    assert engine.classify(8) == "special_graha"
    assert engine.classify(3) == "special_graha"


# ── Universal 7th-house aspect ────────────────────────────────────────────────

def test_all_planets_aspect_7th_house(engine):
    """Every planet aspects the house 7 positions from its own (opposition)."""
    from_planet = _make_planet("sun", house_number=1)
    to_planet = _make_planet("venus", house_number=7)
    aspects = engine.compute([from_planet, to_planet])

    found = [a for a in aspects if a.from_planet == "sun" and a.to_planet == "venus"]
    assert len(found) == 1
    assert found[0].aspect_type == "opposition"


def test_no_aspect_when_not_in_aspected_house(engine):
    from_planet = _make_planet("sun", house_number=1)
    to_planet = _make_planet("venus", house_number=3)  # not aspected by sun
    aspects = engine.compute([from_planet, to_planet])
    assert aspects == []


def test_planet_does_not_aspect_itself(engine):
    """A single planet has no partner to aspect even at its own house offset."""
    planet = _make_planet("sun", house_number=1)
    aspects = engine.compute([planet])
    assert aspects == []


# ── Special graha aspects ─────────────────────────────────────────────────────

def test_mars_special_aspects_4th_and_8th(engine):
    mars = _make_planet("mars", house_number=1)
    target_4th = _make_planet("moon", house_number=4)
    target_8th = _make_planet("venus", house_number=8)
    aspects = engine.compute([mars, target_4th, target_8th])

    types = {(a.to_planet): a.aspect_type for a in aspects if a.from_planet == "mars"}
    assert types["moon"] == "square"          # 4th offset classifies as square
    assert types["venus"] == "special_graha"  # 8th offset has no standard classification


def test_jupiter_special_aspects_5th_and_9th(engine):
    jupiter = _make_planet("jupiter", house_number=1)
    target_5th = _make_planet("moon", house_number=5)
    target_9th = _make_planet("venus", house_number=9)
    aspects = engine.compute([jupiter, target_5th, target_9th])

    from_jupiter = [a for a in aspects if a.from_planet == "jupiter"]
    assert len(from_jupiter) == 2
    assert all(a.aspect_type == "trine" for a in from_jupiter)


def test_saturn_special_aspects_3rd_and_10th(engine):
    saturn = _make_planet("saturn", house_number=1)
    target_3rd = _make_planet("moon", house_number=3)
    target_10th = _make_planet("venus", house_number=10)
    aspects = engine.compute([saturn, target_3rd, target_10th])

    from_saturn = {a.to_planet: a.aspect_type for a in aspects if a.from_planet == "saturn"}
    assert from_saturn["moon"] == "special_graha"  # 3rd has no standard classification
    assert from_saturn["venus"] == "square"        # 10th offset classifies as square


def test_rahu_ketu_special_aspects_match_jupiter(engine):
    """Rahu/Ketu aspect 5th/7th/9th, same offsets as Jupiter, per SPECIAL_ASPECTS."""
    assert SPECIAL_ASPECTS["rahu"] == SPECIAL_ASPECTS["jupiter"]
    assert SPECIAL_ASPECTS["ketu"] == SPECIAL_ASPECTS["jupiter"]


def test_venus_has_no_special_aspects_only_universal(engine):
    """Venus (not in SPECIAL_ASPECTS) only gets the universal 7th aspect."""
    venus = _make_planet("venus", house_number=1)
    target_4th = _make_planet("moon", house_number=4)  # would be special for Mars, not Venus
    target_7th = _make_planet("mercury", house_number=7)
    aspects = engine.compute([venus, target_4th, target_7th])

    from_venus = [a for a in aspects if a.from_planet == "venus"]
    assert len(from_venus) == 1
    assert from_venus[0].to_planet == "mercury"


# ── Orb calculation ────────────────────────────────────────────────────────────

def test_orb_is_absolute_degree_difference_within_15(engine):
    from_planet = _make_planet("sun", house_number=1, rashi_degree=10.0)
    to_planet = _make_planet("venus", house_number=7, rashi_degree=13.0)
    aspects = engine.compute([from_planet, to_planet])
    assert aspects[0].orb_degrees == pytest.approx(3.0)


def test_orb_wraps_when_difference_exceeds_15(engine):
    """Orb should reflect the shorter angular distance within a 30-degree sign."""
    from_planet = _make_planet("sun", house_number=1, rashi_degree=2.0)
    to_planet = _make_planet("venus", house_number=7, rashi_degree=28.0)
    aspects = engine.compute([from_planet, to_planet])
    # abs(2 - 28) = 26 > 15, so wrapped: 30 - 26 = 4
    assert aspects[0].orb_degrees == pytest.approx(4.0)


def test_orb_is_never_negative(engine):
    for deg_a, deg_b in [(0.0, 29.0), (29.0, 0.0), (15.0, 15.0)]:
        from_planet = _make_planet("sun", house_number=1, rashi_degree=deg_a)
        to_planet = _make_planet("venus", house_number=7, rashi_degree=deg_b)
        aspects = engine.compute([from_planet, to_planet])
        assert aspects[0].orb_degrees >= 0.0


# ── Full chart consistency ────────────────────────────────────────────────────

def test_compute_with_no_planets_returns_empty(engine):
    assert engine.compute([]) == []


def test_compute_returns_only_valid_aspect_types(engine):
    planets = [
        _make_planet("sun", 1), _make_planet("moon", 4), _make_planet("mars", 7),
        _make_planet("mercury", 8), _make_planet("jupiter", 3),
    ]
    aspects = engine.compute(planets)
    valid_types = {"conjunction", "opposition", "trine", "square", "special_graha"}
    assert all(a.aspect_type in valid_types for a in aspects)


def test_compute_never_aspects_planet_to_itself(engine):
    planets = [_make_planet(p, 1) for p in ["sun", "moon", "mars", "mercury", "jupiter"]]
    aspects = engine.compute(planets)
    assert all(a.from_planet != a.to_planet for a in aspects)


def test_is_applying_always_false_no_speed_data(engine):
    """SiderealPosition never carries speed, so is_applying must always be False."""
    from_planet = _make_planet("sun", house_number=1)
    to_planet = _make_planet("venus", house_number=7)
    aspects = engine.compute([from_planet, to_planet])
    assert all(a.is_applying is False for a in aspects)
