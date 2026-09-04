"""
AstroOS — Navatara / Tarabala Unit Tests
"""

from datetime import datetime, timezone

from packages.shared.tarabala import (
    EXTENDED_27_NAMES,
    LORDSHIP_TARA_POSITION,
    TARA_NAMES_9,
    best_stars,
    current_age_year,
    extended_27_name,
    extended_27_position,
    favorable_nakshatras_from,
    is_favorable_tara_9,
    karma_and_sadhaka_nakshatras,
    solar_return_boundary,
    special_point_nakshatra,
    tara_name_9,
    tara_position_9,
    yearly_tara,
)


def test_janma_nakshatra_is_position_0_and_unfavorable():
    assert tara_position_9("ashwini", "ashwini") == 0
    assert tara_name_9(0) == "janma"
    assert not is_favorable_tara_9(0)


def test_9_positions_repeat_exactly_3_times_across_27_nakshatras():
    from packages.shared.enums import Nakshatra
    counts = {}
    for n in Nakshatra:
        pos = tara_position_9("ashwini", n.value)
        counts[pos] = counts.get(pos, 0) + 1
    assert set(counts.values()) == {3}
    assert set(counts.keys()) == set(range(9))


def test_favorable_and_unfavorable_sets_are_disjoint_and_cover_all_9():
    from packages.shared.tarabala import FAVORABLE_TARA_9, UNFAVORABLE_TARA_9
    assert FAVORABLE_TARA_9.isdisjoint(UNFAVORABLE_TARA_9)
    assert FAVORABLE_TARA_9 | UNFAVORABLE_TARA_9 == set(TARA_NAMES_9)
    assert len(FAVORABLE_TARA_9) == 5
    assert len(UNFAVORABLE_TARA_9) == 4


def test_lordship_tara_covers_all_9_vimshottari_lords():
    assert set(LORDSHIP_TARA_POSITION.keys()) == {
        "ketu", "venus", "sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury",
    }
    assert set(LORDSHIP_TARA_POSITION.values()) == set(TARA_NAMES_9)


def test_best_stars_is_subset_of_each_individual_favorable_set():
    moon_favorable = favorable_nakshatras_from("ashwini")
    lagna_favorable = favorable_nakshatras_from("bharani")
    intersection = best_stars("ashwini", "bharani")
    assert intersection <= moon_favorable
    assert intersection <= lagna_favorable
    assert len(moon_favorable) == 15
    assert len(lagna_favorable) == 15


def test_extended_27_table_matches_skill_source_exactly():
    # Spot-check the irregular positions the source explicitly calls out
    # as real (not a transcription error / not a clean mod-9 repeat).
    assert extended_27_name(1) == "janma"
    assert extended_27_name(10) == "karma"
    assert extended_27_name(16) == "sanghatik"
    assert extended_27_name(18) == "samudayik"
    assert extended_27_name(19) == "aadhaana"
    assert extended_27_name(23) == "vinasika"
    assert extended_27_name(25) == "jaati"
    assert extended_27_name(26) == "desa"
    assert extended_27_name(27) == "abhisheka"
    assert len(EXTENDED_27_NAMES) == 27


def test_karma_and_sadhaka_nakshatras_are_10th_and_6th_inclusive():
    karma, sadhaka = karma_and_sadhaka_nakshatras("ashwini")
    assert extended_27_position("ashwini", karma) == 10
    assert extended_27_position("ashwini", sadhaka) == 6


def test_solar_return_handles_feb_29_birth():
    leap_birth = datetime(2000, 2, 29, 6, 0, tzinfo=timezone.utc)
    boundary = solar_return_boundary(leap_birth, 1)  # 2001 is not a leap year
    assert boundary == datetime(2001, 2, 28, 6, 0, tzinfo=timezone.utc)


def test_current_age_year_before_first_birthday_is_1():
    birth = datetime(1990, 6, 15, 8, 0, tzinfo=timezone.utc)
    assert current_age_year(birth, datetime(1990, 12, 1, tzinfo=timezone.utc)) == 1
    assert current_age_year(birth, datetime(1991, 6, 14, tzinfo=timezone.utc)) == 1
    assert current_age_year(birth, datetime(1991, 6, 16, tzinfo=timezone.utc)) == 2


def test_yearly_tara_cycles_continuously_not_mod_9():
    birth = datetime(1990, 1, 1, tzinfo=timezone.utc)
    # Age 10 -> position 10 -> "karma", not "sampat" (which mod-9 karma%9=1 would wrongly give).
    age_year, position, name = yearly_tara("ashwini", birth, datetime(1999, 6, 1, tzinfo=timezone.utc))
    assert age_year == 10
    assert position == 10
    assert name == "karma"
    # Age 28 wraps back to position 1 -> "janma".
    age_year28, position28, name28 = yearly_tara("ashwini", birth, datetime(2017, 6, 1, tzinfo=timezone.utc))
    assert age_year28 == 28
    assert position28 == 1
    assert name28 == "janma"


def test_special_points_28_scheme_matches_real_source_example():
    """Regression-anchors this session's cross-check against a real SBC
    tool's Main sheet (Janma Nakshatra = Uttara Phalguni), which
    reproduced every one of these 10 named special points exactly."""
    ref = "uttara_phalguni"
    expected = {
        "jaati": "swati",
        "desa": "shravana",
        "sanghatika": "uttara_bhadrapada",
        "samudayika": "ashwini",
        "aadhana": "bharani",
        "vainashika": "mrigashira",
        "manasa": "pushya",
        "abhisheka": "purva_phalguni",
        "karma": "uttara_ashadha",
        "janma": "uttara_phalguni",
    }
    for name, expected_nakshatra in expected.items():
        assert special_point_nakshatra(ref, name) == expected_nakshatra, name
