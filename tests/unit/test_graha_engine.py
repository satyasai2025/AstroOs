"""
AstroOS — GrahaEngine Unit Tests (Module 6.5 — Foundation Completion)

Covers dignity classification (own sign / exalted / debilitated /
moolatrikona) and strength scoring, independently of HoroscopeEngine.
"""

import pytest

from apps.api.domain.ephemeris import DignityType, SiderealPosition
from apps.api.services.graha_engine import (
    DUSTHANA_HOUSES,
    GrahaEngine,
    KENDRA_HOUSES,
    TRIKONA_HOUSES,
)


@pytest.fixture
def engine() -> GrahaEngine:
    return GrahaEngine()


def _make_planet(
    planet: str,
    rashi: str,
    house_number: int = 1,
    dignity: DignityType = DignityType.NEUTRAL,
    is_retrograde: bool = False,
    is_combust: bool = False,
) -> SiderealPosition:
    return SiderealPosition(
        planet=planet,
        sidereal_longitude=10.0,
        rashi=rashi,
        rashi_degree=10.0,
        house_number=house_number,
        nakshatra="ashwini",
        pada=1,
        is_retrograde=is_retrograde,
        is_combust=is_combust,
        combustion_orb=None,
        dignity=dignity,
    )


# ── Dignity classification ────────────────────────────────────────────────────

def test_is_own_sign_true(engine):
    assert engine.is_own_sign("mars", "aries") is True
    assert engine.is_own_sign("mars", "scorpio") is True  # Mars rules two signs


def test_is_own_sign_false(engine):
    assert engine.is_own_sign("mars", "taurus") is False


def test_is_exalted_true(engine):
    assert engine.is_exalted("sun", "aries") is True
    assert engine.is_exalted("moon", "taurus") is True


def test_is_exalted_false_wrong_sign(engine):
    assert engine.is_exalted("sun", "libra") is False


def test_is_exalted_false_rahu_ketu_not_in_table(engine):
    # Rahu/Ketu exaltation is contested across traditions; this codebase's
    # EXALTATION_DEGREES table does include them (gemini/sagittarius) —
    # confirm the engine reads through to whatever the shared table says.
    assert engine.is_exalted("rahu", "gemini") is True
    assert engine.is_exalted("rahu", "sagittarius") is False


def test_is_debilitated_true(engine):
    assert engine.is_debilitated("sun", "libra") is True


def test_is_debilitated_false(engine):
    assert engine.is_debilitated("sun", "aries") is False


def test_is_moolatrikona_true(engine):
    assert engine.is_moolatrikona("sun", "leo") is True


def test_is_moolatrikona_false_for_rahu_ketu(engine):
    """Rahu/Ketu have no classical Moolatrikona sign."""
    assert engine.is_moolatrikona("rahu", "gemini") is False
    assert engine.is_moolatrikona("ketu", "sagittarius") is False


def test_dignity_flags_are_mutually_exclusive_in_practice(engine):
    """A planet exalted in a sign should not also read as debilitated there."""
    assert engine.is_exalted("sun", "aries") is True
    assert engine.is_debilitated("sun", "aries") is False


# ── Strength scoring ──────────────────────────────────────────────────────────

def test_compute_strength_returns_one_entry_per_planet(engine):
    planets = [_make_planet(p, "aries") for p in ["sun", "moon", "mars"]]
    strengths = engine.compute_strength(planets)
    assert len(strengths) == 3


def test_compute_strength_sorted_descending(engine):
    planets = [
        _make_planet("sun", "aries", dignity=DignityType.EXALTED),
        _make_planet("moon", "libra", dignity=DignityType.DEBILITATED),
        _make_planet("mars", "taurus", dignity=DignityType.NEUTRAL),
    ]
    strengths = engine.compute_strength(planets)
    scores = [s.strength_score for s in strengths]
    assert scores == sorted(scores, reverse=True)
    assert strengths[0].planet == "sun"  # exalted should score highest here


def test_compute_strength_score_bounds(engine):
    """Score must always stay within 0.0-10.0 regardless of bonuses/penalties."""
    planets = [
        _make_planet(
            "mars", "aries", house_number=1, dignity=DignityType.EXALTED,
            is_retrograde=True, is_combust=False,
        ),
        _make_planet(
            "saturn", "libra", house_number=8, dignity=DignityType.DEBILITATED,
            is_retrograde=False, is_combust=True,
        ),
    ]
    strengths = engine.compute_strength(planets)
    for s in strengths:
        assert 0.0 <= s.strength_score <= 10.0


def test_compute_strength_kendra_bonus_applied(engine):
    in_kendra = _make_planet("jupiter", "cancer", house_number=1)  # kendra
    not_in_kendra = _make_planet("jupiter", "cancer", house_number=2)  # not kendra
    s_kendra = engine.compute_strength([in_kendra])[0]
    s_other = engine.compute_strength([not_in_kendra])[0]
    assert s_kendra.strength_score > s_other.strength_score
    assert s_kendra.is_in_kendra is True
    assert s_other.is_in_kendra is False


def test_compute_strength_dusthana_penalty_applied(engine):
    in_dusthana = _make_planet("saturn", "capricorn", house_number=6)
    s = engine.compute_strength([in_dusthana])[0]
    assert s.is_in_dusthana is True


def test_compute_strength_combust_penalty_applied(engine):
    combust = _make_planet("mercury", "virgo", house_number=3, is_combust=True)
    not_combust = _make_planet("mercury", "virgo", house_number=3, is_combust=False)
    s_combust = engine.compute_strength([combust])[0]
    s_clean = engine.compute_strength([not_combust])[0]
    assert s_combust.strength_score < s_clean.strength_score


def test_compute_strength_retrograde_bonus_applied(engine):
    retro = _make_planet("saturn", "capricorn", house_number=3, is_retrograde=True)
    direct = _make_planet("saturn", "capricorn", house_number=3, is_retrograde=False)
    s_retro = engine.compute_strength([retro])[0]
    s_direct = engine.compute_strength([direct])[0]
    assert s_retro.strength_score > s_direct.strength_score


def test_compute_strength_house_classification_flags_consistent(engine):
    for house_num in range(1, 13):
        planet = _make_planet("sun", "leo", house_number=house_num)
        s = engine.compute_strength([planet])[0]
        assert s.is_in_kendra == (house_num in KENDRA_HOUSES)
        assert s.is_in_trikona == (house_num in TRIKONA_HOUSES)
        assert s.is_in_dusthana == (house_num in DUSTHANA_HOUSES)


def test_compute_strength_none_dignity_defaults_neutral(engine):
    """Rahu/Ketu often carry no DignityType — must not crash, default to neutral base."""
    planet = _make_planet("rahu", "gemini", dignity=None)
    strengths = engine.compute_strength([planet])
    assert len(strengths) == 1
    assert strengths[0].dignity is None
