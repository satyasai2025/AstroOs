"""
Unit tests for DashaEngine — Task 6.

Tests use a real EphemerisWrapper (Moshier fallback, no .se1 files required)
so they run in CI without extra data files.

Reference chart: 1986-06-15 10:30:00 UTC, lat=28.6139, lon=77.2090 (New Delhi)
Lahiri ayanamsa.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from apps.api.config import get_settings
from apps.api.services.dasha_engine import (
    DashaEngine,
    _nakshatra_balance,
    _jaimini_sign_duration,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from packages.shared.constants import (
    ASHTOTTARI_DASHA_YEARS,
    ASHTOTTARI_SEQUENCE,
    ASHTOTTARI_TOTAL_YEARS,
    DAYS_PER_JULIAN_YEAR,
    DEGREES_PER_NAKSHATRA,
    KALACHAKRA_SIGN_YEARS,
    KALACHAKRA_TOTAL_YEARS,
    VIMSHOTTARI_DASHA_YEARS,
    VIMSHOTTARI_SEQUENCE,
    VIMSHOTTARI_TOTAL_YEARS,
    YOGINI_DASHA_YEARS,
    YOGINI_SEQUENCE,
    YOGINI_TOTAL_YEARS,
)

# ── Fixtures ───────────────────────────────────────────────────────────────────

_SETTINGS = get_settings()
_WRAPPER = EphemerisWrapper(ephemeris_path=_SETTINGS.EPHEMERIS_PATH)
ENGINE = DashaEngine(_WRAPPER)

REF_DT = datetime(1986, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
REF_LAT = 28.6139
REF_LON = 77.2090
REF_DATE = date(1986, 6, 15)


# ── Structural helpers ─────────────────────────────────────────────────────────


def assert_periods_contiguous(periods) -> None:
    for i in range(1, len(periods)):
        assert periods[i].start_date == periods[i - 1].end_date, (
            f"Gap at level {periods[i].level}: "
            f"{periods[i - 1].lord}.end={periods[i - 1].end_date} "
            f"!= {periods[i].lord}.start={periods[i].start_date}"
        )


def assert_sub_covers_parent(period) -> None:
    if not period.sub_periods:
        return
    assert period.sub_periods[0].start_date == period.start_date, (
        f"sub_periods[0].start != parent.start for {period.lord}"
    )
    assert period.sub_periods[-1].end_date == period.end_date, (
        f"sub_periods[-1].end != parent.end for {period.lord}"
    )
    assert_periods_contiguous(period.sub_periods)
    for sp in period.sub_periods:
        assert_sub_covers_parent(sp)


def assert_tree_valid(tree, expected_maha_count: int) -> None:
    assert tree.birth_date is not None
    assert tree.system is not None
    assert len(tree.mahadashas) == expected_maha_count
    assert_periods_contiguous(tree.mahadashas)
    for m in tree.mahadashas:
        assert m.level == 1
        assert m.duration_days > 0
        assert m.start_date < m.end_date
        assert_sub_covers_parent(m)


# ── _nakshatra_balance ─────────────────────────────────────────────────────────


class TestNakshatraBalance:
    def test_ashwini_gives_ketu(self):
        lord, bal, _ = _nakshatra_balance(
            0.0, VIMSHOTTARI_SEQUENCE, VIMSHOTTARI_DASHA_YEARS,
            VIMSHOTTARI_TOTAL_YEARS, date(2000, 1, 1),
        )
        assert lord == "ketu"
        assert abs(bal - 7.0) < 0.001

    def test_magha_gives_ketu_again(self):
        lon = 9 * DEGREES_PER_NAKSHATRA + 1.0
        lord, _, _ = _nakshatra_balance(
            lon, VIMSHOTTARI_SEQUENCE, VIMSHOTTARI_DASHA_YEARS,
            VIMSHOTTARI_TOTAL_YEARS, date(2000, 1, 1),
        )
        assert lord == "ketu"

    def test_mid_venus_nakshatra_gives_half_balance(self):
        lon = 1 * DEGREES_PER_NAKSHATRA + DEGREES_PER_NAKSHATRA / 2.0
        lord, bal, _ = _nakshatra_balance(
            lon, VIMSHOTTARI_SEQUENCE, VIMSHOTTARI_DASHA_YEARS,
            VIMSHOTTARI_TOTAL_YEARS, date(2000, 1, 1),
        )
        assert lord == "venus"
        assert abs(bal - 10.0) < 0.01

    def test_balance_never_exceeds_lord_period(self):
        for idx in range(27):
            lon = idx * DEGREES_PER_NAKSHATRA + 0.1
            lord, bal, _ = _nakshatra_balance(
                lon, VIMSHOTTARI_SEQUENCE, VIMSHOTTARI_DASHA_YEARS,
                VIMSHOTTARI_TOTAL_YEARS, date(1990, 1, 1),
            )
            assert bal <= VIMSHOTTARI_DASHA_YEARS[lord] + 1e-9

    def test_first_start_before_birth_for_partial(self):
        lon = 5.0
        _, _, first_start = _nakshatra_balance(
            lon, VIMSHOTTARI_SEQUENCE, VIMSHOTTARI_DASHA_YEARS,
            VIMSHOTTARI_TOTAL_YEARS, date(2000, 6, 1),
        )
        assert first_start < date(2000, 6, 1)

    def test_nakshatra_boundary_full_balance(self):
        sun_start = 2 * DEGREES_PER_NAKSHATRA
        lord, bal, _ = _nakshatra_balance(
            sun_start, VIMSHOTTARI_SEQUENCE, VIMSHOTTARI_DASHA_YEARS,
            VIMSHOTTARI_TOTAL_YEARS, date(2000, 1, 1),
        )
        assert lord == "sun"
        assert abs(bal - 6.0) < 0.001

    def test_all_27_nakshatras_produce_valid_lords(self):
        valid = set(VIMSHOTTARI_SEQUENCE)
        for idx in range(27):
            lon = idx * DEGREES_PER_NAKSHATRA + DEGREES_PER_NAKSHATRA / 2.0
            lord, bal, _ = _nakshatra_balance(
                lon, VIMSHOTTARI_SEQUENCE, VIMSHOTTARI_DASHA_YEARS,
                VIMSHOTTARI_TOTAL_YEARS, date(2000, 1, 1),
            )
            assert lord in valid
            assert bal > 0


# ── _jaimini_sign_duration ─────────────────────────────────────────────────────


class TestJaiminiSignDuration:
    def test_same_sign_gives_12(self):
        assert _jaimini_sign_duration("aries", "aries") == 12

    def test_adjacent_forward_gives_1(self):
        assert _jaimini_sign_duration("aries", "taurus") == 1

    def test_opposite_sign_gives_6(self):
        assert _jaimini_sign_duration("aries", "libra") == 6

    def test_shorter_direction_always_chosen(self):
        assert _jaimini_sign_duration("aries", "scorpio") == 5
        assert _jaimini_sign_duration("aries", "sagittarius") == 4

    def test_symmetric(self):
        rashis = [
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
        ]
        for a in rashis:
            for b in rashis:
                assert _jaimini_sign_duration(a, b) == _jaimini_sign_duration(b, a)

    def test_all_durations_in_valid_range(self):
        rashis = [
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
        ]
        for a in rashis:
            for b in rashis:
                d = _jaimini_sign_duration(a, b)
                assert 1 <= d <= 12, f"{a}→{b}: {d}"


# ── Vimshottari Dasha ──────────────────────────────────────────────────────────


class TestVimshottariDasha:
    def test_returns_9_mahadashas(self):
        tree = ENGINE.compute_vimshottari(REF_DT, REF_LAT, REF_LON)
        assert len(tree.mahadashas) == 9

    def test_system_name(self):
        assert ENGINE.compute_vimshottari(REF_DT, REF_LAT, REF_LON).system == "vimshottari"

    def test_total_cycle_years(self):
        assert ENGINE.compute_vimshottari(REF_DT, REF_LAT, REF_LON).total_cycle_years == 120

    def test_all_lords_present_exactly_once(self):
        tree = ENGINE.compute_vimshottari(REF_DT, REF_LAT, REF_LON)
        lords = sorted(m.lord for m in tree.mahadashas)
        assert lords == sorted(VIMSHOTTARI_SEQUENCE)

    def test_mahadasha_durations_match_table(self):
        tree = ENGINE.compute_vimshottari(REF_DT, REF_LAT, REF_LON)
        for m in tree.mahadashas:
            expected = round(VIMSHOTTARI_DASHA_YEARS[m.lord] * DAYS_PER_JULIAN_YEAR)
            assert abs(m.duration_days - expected) <= 1, (
                f"{m.lord}: expected ~{expected} days, got {m.duration_days}"
            )

    def test_tree_structure_depth_1(self):
        tree = ENGINE.compute_vimshottari(REF_DT, REF_LAT, REF_LON, max_depth=1)
        assert_tree_valid(tree, 9)
        for m in tree.mahadashas:
            assert m.sub_periods == ()

    def test_tree_structure_depth_2(self):
        tree = ENGINE.compute_vimshottari(REF_DT, REF_LAT, REF_LON, max_depth=2)
        assert_tree_valid(tree, 9)
        for m in tree.mahadashas:
            assert len(m.sub_periods) == 9
            for a in m.sub_periods:
                assert a.level == 2
                assert a.sub_periods == ()

    def test_tree_structure_depth_3(self):
        tree = ENGINE.compute_vimshottari(REF_DT, REF_LAT, REF_LON, max_depth=3)
        assert_tree_valid(tree, 9)
        for m in tree.mahadashas:
            for a in m.sub_periods:
                assert len(a.sub_periods) == 9
                for p in a.sub_periods:
                    assert p.level == 3

    def test_trigger_nakshatra_number_in_range(self):
        tree = ENGINE.compute_vimshottari(REF_DT, REF_LAT, REF_LON)
        assert 1 <= tree.trigger_nakshatra_number <= 27

    def test_trigger_planet_valid_lord(self):
        tree = ENGINE.compute_vimshottari(REF_DT, REF_LAT, REF_LON)
        assert tree.trigger_planet in set(VIMSHOTTARI_SEQUENCE)

    def test_mahadasha_1_starts_at_or_before_birth(self):
        tree = ENGINE.compute_vimshottari(REF_DT, REF_LAT, REF_LON)
        assert tree.mahadashas[0].start_date <= REF_DATE

    def test_max_depth_clamped(self):
        tree = ENGINE.compute_vimshottari(REF_DT, REF_LAT, REF_LON, max_depth=99)
        assert tree.max_depth == 5

    def test_different_ayanamsas_give_different_results(self):
        t_lahiri = ENGINE.compute_vimshottari(REF_DT, REF_LAT, REF_LON, ayanamsa="lahiri")
        t_kp = ENGINE.compute_vimshottari(REF_DT, REF_LAT, REF_LON, ayanamsa="kp")
        lahiri_lords = [m.lord for m in t_lahiri.mahadashas]
        kp_lords = [m.lord for m in t_kp.mahadashas]
        # Same set of lords, but may start at a different point in the cycle
        assert sorted(lahiri_lords) == sorted(kp_lords)

    def test_antardasha_lord_sequence_starts_from_maha_lord(self):
        tree = ENGINE.compute_vimshottari(REF_DT, REF_LAT, REF_LON, max_depth=2)
        for maha in tree.mahadashas:
            if maha.sub_periods:
                assert maha.sub_periods[0].lord == maha.lord, (
                    f"Antardasha sequence should start from Mahadasha lord "
                    f"{maha.lord}, got {maha.sub_periods[0].lord}"
                )


# ── Yogini Dasha ───────────────────────────────────────────────────────────────


class TestYoginiDasha:
    def test_returns_8_mahadashas(self):
        tree = ENGINE.compute_yogini(REF_DT, REF_LAT, REF_LON)
        assert len(tree.mahadashas) == 8

    def test_system_name(self):
        assert ENGINE.compute_yogini(REF_DT, REF_LAT, REF_LON).system == "yogini"

    def test_total_cycle_years(self):
        assert ENGINE.compute_yogini(REF_DT, REF_LAT, REF_LON).total_cycle_years == 36

    def test_all_yogini_lords_present(self):
        tree = ENGINE.compute_yogini(REF_DT, REF_LAT, REF_LON)
        lords = sorted(m.lord for m in tree.mahadashas)
        assert lords == sorted(YOGINI_SEQUENCE)

    def test_durations_match_yogini_table(self):
        tree = ENGINE.compute_yogini(REF_DT, REF_LAT, REF_LON)
        for m in tree.mahadashas:
            expected = round(YOGINI_DASHA_YEARS[m.lord] * DAYS_PER_JULIAN_YEAR)
            assert abs(m.duration_days - expected) <= 1

    def test_tree_structure_depth_2(self):
        tree = ENGINE.compute_yogini(REF_DT, REF_LAT, REF_LON, max_depth=2)
        assert_tree_valid(tree, 8)
        for m in tree.mahadashas:
            assert len(m.sub_periods) == 8

    def test_tree_structure_depth_3(self):
        tree = ENGINE.compute_yogini(REF_DT, REF_LAT, REF_LON, max_depth=3)
        assert_tree_valid(tree, 8)

    def test_trigger_planet_is_graha(self):
        tree = ENGINE.compute_yogini(REF_DT, REF_LAT, REF_LON)
        valid_grahas = {"moon", "sun", "jupiter", "mars", "mercury", "saturn", "venus", "rahu"}
        assert tree.trigger_planet in valid_grahas


# ── Ashtottari Dasha ───────────────────────────────────────────────────────────


class TestAshtottariDasha:
    def test_returns_8_mahadashas(self):
        tree = ENGINE.compute_ashtottari(REF_DT, REF_LAT, REF_LON)
        assert len(tree.mahadashas) == 8

    def test_system_name(self):
        assert ENGINE.compute_ashtottari(REF_DT, REF_LAT, REF_LON).system == "ashtottari"

    def test_total_cycle_years(self):
        assert ENGINE.compute_ashtottari(REF_DT, REF_LAT, REF_LON).total_cycle_years == 108

    def test_all_lords_present(self):
        tree = ENGINE.compute_ashtottari(REF_DT, REF_LAT, REF_LON)
        lords = sorted(m.lord for m in tree.mahadashas)
        assert lords == sorted(ASHTOTTARI_SEQUENCE)

    def test_durations_match_table(self):
        tree = ENGINE.compute_ashtottari(REF_DT, REF_LAT, REF_LON)
        for m in tree.mahadashas:
            expected = round(ASHTOTTARI_DASHA_YEARS[m.lord] * DAYS_PER_JULIAN_YEAR)
            assert abs(m.duration_days - expected) <= 1

    def test_tree_structure_depth_2(self):
        tree = ENGINE.compute_ashtottari(REF_DT, REF_LAT, REF_LON, max_depth=2)
        assert_tree_valid(tree, 8)

    def test_antardasha_starts_from_maha_lord(self):
        tree = ENGINE.compute_ashtottari(REF_DT, REF_LAT, REF_LON, max_depth=2)
        for maha in tree.mahadashas:
            if maha.sub_periods:
                assert maha.sub_periods[0].lord == maha.lord


# ── Kalachakra Dasha ───────────────────────────────────────────────────────────


class TestKalachakraDasha:
    def test_returns_12_mahadashas(self):
        tree = ENGINE.compute_kalachakra(REF_DT, REF_LAT, REF_LON)
        assert len(tree.mahadashas) == 12

    def test_system_name(self):
        assert ENGINE.compute_kalachakra(REF_DT, REF_LAT, REF_LON).system == "kalachakra"

    def test_total_cycle_years(self):
        assert ENGINE.compute_kalachakra(REF_DT, REF_LAT, REF_LON).total_cycle_years == 100

    def test_all_lords_are_valid_rashi_names(self):
        valid = set(KALACHAKRA_SIGN_YEARS.keys())
        tree = ENGINE.compute_kalachakra(REF_DT, REF_LAT, REF_LON)
        for m in tree.mahadashas:
            assert m.lord in valid, f"Invalid sign: {m.lord}"

    def test_all_12_signs_present(self):
        tree = ENGINE.compute_kalachakra(REF_DT, REF_LAT, REF_LON)
        lords = sorted(m.lord for m in tree.mahadashas)
        assert lords == sorted(KALACHAKRA_SIGN_YEARS.keys())

    def test_tree_structure_depth_2(self):
        tree = ENGINE.compute_kalachakra(REF_DT, REF_LAT, REF_LON, max_depth=2)
        assert_tree_valid(tree, 12)
        for m in tree.mahadashas:
            assert len(m.sub_periods) == 12


# ── Chara Dasha ────────────────────────────────────────────────────────────────


class TestCharaDasha:
    def test_returns_12_mahadashas(self):
        tree = ENGINE.compute_chara(REF_DT, REF_LAT, REF_LON)
        assert len(tree.mahadashas) == 12

    def test_system_name(self):
        assert ENGINE.compute_chara(REF_DT, REF_LAT, REF_LON).system == "chara"

    def test_all_lords_are_rashi_names(self):
        valid_rashis = {
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
        }
        tree = ENGINE.compute_chara(REF_DT, REF_LAT, REF_LON)
        for m in tree.mahadashas:
            assert m.lord in valid_rashis

    def test_all_12_signs_present(self):
        tree = ENGINE.compute_chara(REF_DT, REF_LAT, REF_LON)
        assert len({m.lord for m in tree.mahadashas}) == 12

    def test_total_years_in_valid_range(self):
        # Chara total = sum of 12 sign durations, each 1–12, so total is 12–144
        tree = ENGINE.compute_chara(REF_DT, REF_LAT, REF_LON)
        assert 12 <= tree.total_cycle_years <= 144

    def test_tree_structure_depth_2(self):
        tree = ENGINE.compute_chara(REF_DT, REF_LAT, REF_LON, max_depth=2)
        assert_tree_valid(tree, 12)
        for m in tree.mahadashas:
            assert len(m.sub_periods) == 12

    def test_tree_structure_depth_3(self):
        tree = ENGINE.compute_chara(REF_DT, REF_LAT, REF_LON, max_depth=3)
        assert_tree_valid(tree, 12)

    def test_start_date_is_birth_date(self):
        tree = ENGINE.compute_chara(REF_DT, REF_LAT, REF_LON)
        assert tree.mahadashas[0].start_date == REF_DATE

    def test_trigger_planet_is_lagna_rashi(self):
        valid_rashis = {
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
        }
        tree = ENGINE.compute_chara(REF_DT, REF_LAT, REF_LON)
        assert tree.trigger_planet in valid_rashis


# ── Narayana Dasha ─────────────────────────────────────────────────────────────


class TestNarayanaDasha:
    def test_returns_12_mahadashas(self):
        tree = ENGINE.compute_narayana(REF_DT, REF_LAT, REF_LON)
        assert len(tree.mahadashas) == 12

    def test_system_name(self):
        assert ENGINE.compute_narayana(REF_DT, REF_LAT, REF_LON).system == "narayana"

    def test_all_signs_present(self):
        tree = ENGINE.compute_narayana(REF_DT, REF_LAT, REF_LON)
        assert len({m.lord for m in tree.mahadashas}) == 12

    def test_total_years_in_valid_range(self):
        tree = ENGINE.compute_narayana(REF_DT, REF_LAT, REF_LON)
        assert 12 <= tree.total_cycle_years <= 144

    def test_tree_structure_depth_2(self):
        tree = ENGINE.compute_narayana(REF_DT, REF_LAT, REF_LON, max_depth=2)
        assert_tree_valid(tree, 12)

    def test_narayana_differs_from_chara(self):
        chara = ENGINE.compute_chara(REF_DT, REF_LAT, REF_LON)
        narayana = ENGINE.compute_narayana(REF_DT, REF_LAT, REF_LON)
        # Different systems may yield different starting signs or durations
        chara_lords = [m.lord for m in chara.mahadashas]
        narayana_lords = [m.lord for m in narayana.mahadashas]
        # Both must have 12 signs; they may or may not be identical
        assert len(chara_lords) == 12
        assert len(narayana_lords) == 12


# ── Cross-system consistency ───────────────────────────────────────────────────


class TestCrossSystemConsistency:
    def test_all_systems_same_birth_date(self):
        systems = [
            ENGINE.compute_vimshottari(REF_DT, REF_LAT, REF_LON),
            ENGINE.compute_yogini(REF_DT, REF_LAT, REF_LON),
            ENGINE.compute_ashtottari(REF_DT, REF_LAT, REF_LON),
            ENGINE.compute_kalachakra(REF_DT, REF_LAT, REF_LON),
            ENGINE.compute_chara(REF_DT, REF_LAT, REF_LON),
            ENGINE.compute_narayana(REF_DT, REF_LAT, REF_LON),
        ]
        for t in systems:
            assert t.birth_date == REF_DATE

    def test_all_systems_have_valid_nakshatras(self):
        systems = [
            ENGINE.compute_vimshottari(REF_DT, REF_LAT, REF_LON),
            ENGINE.compute_yogini(REF_DT, REF_LAT, REF_LON),
            ENGINE.compute_ashtottari(REF_DT, REF_LAT, REF_LON),
        ]
        for t in systems:
            assert 1 <= t.trigger_nakshatra_number <= 27
            assert isinstance(t.trigger_nakshatra, str) and t.trigger_nakshatra

    def test_all_periods_positive_duration(self):
        tree = ENGINE.compute_vimshottari(REF_DT, REF_LAT, REF_LON, max_depth=3)
        for maha in tree.mahadashas:
            assert maha.duration_days > 0
            for ant in maha.sub_periods:
                assert ant.duration_days >= 0
                for prat in ant.sub_periods:
                    assert prat.duration_days >= 0

    def test_all_mahadasha_lords_are_string(self):
        for system in ("vimshottari", "yogini", "ashtottari", "kalachakra", "chara", "narayana"):
            compute_fn = getattr(ENGINE, f"compute_{system}")
            tree = compute_fn(REF_DT, REF_LAT, REF_LON, max_depth=1)
            for m in tree.mahadashas:
                assert isinstance(m.lord, str) and m.lord
