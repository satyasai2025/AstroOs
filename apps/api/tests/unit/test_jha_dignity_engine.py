"""
AstroOS — Unit Tests for Vinay Jha Canonical Dignity Engine (Step 3 & 4)
"""

import pytest
from apps.api.services.jha_dignity_engine import (
    JhaDignityEngine,
    JhaDignityResult,
    compute_dignity,
    compute_strength,
)


def test_jha_dignity_exalted_and_debilitated():
    """Verify that Exalted is Tier 9 (256x) and Debilitated is Tier 1 (1x)."""
    # Sun in Aries 10° (Exalted)
    res_exalted = JhaDignityEngine.evaluate_planet_dignity(
        planet="sun",
        sidereal_lon=10.0,
        chart_planet_positions={"sun": 10.0, "mars": 200.0},
    )
    assert res_exalted.dignity_tier == 9
    assert res_exalted.main_strength == 256.0
    assert "Exalted" in res_exalted.dignity_label

    # Sun in Libra 10° (Debilitated)
    res_debilitated = JhaDignityEngine.evaluate_planet_dignity(
        planet="sun",
        sidereal_lon=190.0,
        chart_planet_positions={"sun": 190.0, "venus": 20.0},
    )
    assert res_debilitated.dignity_tier == 1
    assert res_debilitated.main_strength == 1.0
    assert "Debilitated" in res_debilitated.dignity_label


def test_jha_dignity_moolatrikona_vs_own_sign():
    """Verify distinction between Moolatrikona (Tier 8, 128x) and Own Sign (Tier 7, 64x)."""
    # Sun in Leo 10° (within 0-20° Moolatrikona range)
    res_mt = JhaDignityEngine.evaluate_planet_dignity(
        planet="sun",
        sidereal_lon=130.0, # Leo is 120°-150°
        chart_planet_positions={"sun": 130.0},
    )
    assert res_mt.dignity_tier == 8
    assert res_mt.main_strength == 128.0

    # Sun in Leo 25° (outside 0-20° range -> Svakshetra / Own Sign)
    res_own = JhaDignityEngine.evaluate_planet_dignity(
        planet="sun",
        sidereal_lon=145.0,
        chart_planet_positions={"sun": 145.0},
    )
    assert res_own.dignity_tier == 7
    assert res_own.main_strength == 64.0


def test_jha_dignity_panchadha_maitri():
    """Verify Panchadha Maitri synthesis (Natural + Temporal)."""
    # Jupiter in Cancer (Exalted -> 9)
    # Let's test Jupiter in Sagittarius (Own Sign/Moolatrikona)
    # Jupiter in Taurus (sign ruled by Venus, natural enemy)
    # If Venus is in 2nd, 3rd, 4th, 10th, 11th, 12th from Jupiter -> Temporal Friend (+1)
    # Natural Enemy (-1) + Temporal Friend (+1) = Sama / Neutral (Tier 4, 8.0x)
    jup_lon = 45.0 # Taurus 15°
    ven_lon = 80.0 # Gemini 20° (2nd house from Taurus -> Temporal Friend)
    res_sama = JhaDignityEngine.evaluate_planet_dignity(
        planet="jupiter",
        sidereal_lon=jup_lon,
        chart_planet_positions={"jupiter": jup_lon, "venus": ven_lon},
    )
    assert res_sama.dignity_tier == 4
    assert res_sama.main_strength == 8.0
    assert "Neutral" in res_sama.panchadha_relation


def test_jha_dignity_shadbala_tiebreaker():
    """Verify that Shadbala is used strictly as a tiebreaker when Main Strength is tied."""
    res_a = JhaDignityResult(
        planet="jupiter", rashi_index=0, rashi_name="aries", degree_in_rashi=10.0,
        sign_lord="mars", naisargika_relation="Friend", tatkalika_relation="Friend",
        panchadha_relation="Atimitra", dignity_tier=6, dignity_label="Fast Friend",
        main_strength=32.0, vimshopaka_weight=6.0, final_varga_strength=9.6,
        shadbala_score=1.45,
    )
    res_b = JhaDignityResult(
        planet="mars", rashi_index=4, rashi_name="leo", degree_in_rashi=12.0,
        sign_lord="sun", naisargika_relation="Friend", tatkalika_relation="Friend",
        panchadha_relation="Atimitra", dignity_tier=6, dignity_label="Fast Friend",
        main_strength=32.0, vimshopaka_weight=6.0, final_varga_strength=9.6,
        shadbala_score=1.20,
    )

    winner, reason = JhaDignityEngine.resolve_strength_tiebreaker(res_a, res_b)
    assert winner.planet == "jupiter"
    assert "tiebreaker by Shadbala" in reason


def test_moon_and_mercury_exaltation_vs_moolatrikona_degrees():
    """Verify exact degree transitions: Moon in Taurus and Mercury in Virgo."""
    # Moon in Taurus 2° -> Exalted (Tier 9)
    res_moon_ex = JhaDignityEngine.evaluate_planet_dignity(
        planet="moon", sidereal_lon=32.0, chart_planet_positions={"moon": 32.0}
    )
    assert res_moon_ex.dignity_tier == 9
    assert res_moon_ex.main_strength == 256.0

    # Moon in Taurus 10° -> Moolatrikona (Tier 8)
    res_moon_mt = JhaDignityEngine.evaluate_planet_dignity(
        planet="moon", sidereal_lon=40.0, chart_planet_positions={"moon": 40.0}
    )
    assert res_moon_mt.dignity_tier == 8
    assert res_moon_mt.main_strength == 128.0

    # Mercury in Virgo 10° -> Exalted (Tier 9)
    res_merc_ex = JhaDignityEngine.evaluate_planet_dignity(
        planet="mercury", sidereal_lon=160.0, chart_planet_positions={"mercury": 160.0}
    )
    assert res_merc_ex.dignity_tier == 9
    assert res_merc_ex.main_strength == 256.0

    # Mercury in Virgo 18° -> Moolatrikona (Tier 8)
    res_merc_mt = JhaDignityEngine.evaluate_planet_dignity(
        planet="mercury", sidereal_lon=168.0, chart_planet_positions={"mercury": 168.0}
    )
    assert res_merc_mt.dignity_tier == 8
    assert res_merc_mt.main_strength == 128.0

    # Mercury in Virgo 25° -> Own Sign (Tier 7)
    res_merc_own = JhaDignityEngine.evaluate_planet_dignity(
        planet="mercury", sidereal_lon=175.0, chart_planet_positions={"mercury": 175.0}
    )
    assert res_merc_own.dignity_tier == 7
    assert res_merc_own.main_strength == 64.0


def test_directionality_asymmetry():
    """Verify that lookup is strictly NATURAL_REL[P][D] and asymmetric."""
    # Moon in Gemini (Dispositor Mercury): Moon considers Mercury Friend (+1)
    # If Mercury is in Cancer (2nd house -> Temporal Friend +1) -> Atimitra (Tier 6, 32.0)
    res_moon = JhaDignityEngine.evaluate_planet_dignity(
        planet="moon", sidereal_lon=70.0, chart_planet_positions={"moon": 70.0, "mercury": 100.0}
    )
    assert res_moon.dignity_tier == 6
    assert res_moon.main_strength == 32.0

    # Mercury in Cancer (Dispositor Moon): Mercury considers Moon Enemy (-1)
    # Moon is in Gemini (12th house from Cancer -> Temporal Friend +1)
    # Natural Enemy (-1) + Temporal Friend (+1) -> Sama (Tier 4, 8.0)
    res_merc = JhaDignityEngine.evaluate_planet_dignity(
        planet="mercury", sidereal_lon=100.0, chart_planet_positions={"mercury": 100.0, "moon": 70.0}
    )
    assert res_merc.dignity_tier == 4
    assert res_merc.main_strength == 8.0


def test_venus_exaltation_pisces_neecha_virgo():
    """Sanity test requested by user: Venus in Pisces gives Tier 9 and Venus in Virgo gives Tier 1."""
    assert compute_dignity("शुक्र", sign=11, degree=27.0) == 9  # मीन 27° deep उच्च
    assert compute_dignity("शुक्र", sign=11, degree=10.0) == 9  # मीन पूरी राशि उच्च
    assert compute_dignity("शुक्र", sign=5, degree=15.0) == 1   # कन्या = नीच
    assert compute_dignity("venus", sign=11, degree=27.0) == 9
    assert compute_dignity("venus", sign=5, degree=15.0) == 1
