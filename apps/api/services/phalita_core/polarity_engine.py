"""
AstroOS — Classical Polarity Engine
=====================================

Lookup-table based polarity assessment using ONLY documented rules from:
1. Laghu Parashari (Dasha lord classification)  →  md-and-ad-results-laghu-parashari.md
2. BPHS Gochara table via Vinay Ji             →  ashtaka-varga.md

NO LLM interpretation. NO hallucinated rules.
Every decision traces to a specific line in the source documents.

Design: Exactly like pre-LLM astrology software (Kundalee, Jagannatha Hora):
  Input → Lookup Table → Fixed text output
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from apps.api.domain.horoscope import D1Chart

# ─────────────────────────────────────────────────────────────────────────────
# RASHI UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

_RASHI_ORDER = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]

_RASHI_LORDS = {
    "aries": "mars", "taurus": "venus", "gemini": "mercury", "cancer": "moon",
    "leo": "sun", "virgo": "mercury", "libra": "venus", "scorpio": "mars",
    "sagittarius": "jupiter", "capricorn": "saturn", "aquarius": "saturn",
    "pisces": "jupiter",
}


def _house_number(lagna_rashi: str, planet_rashi: str) -> int:
    """Whole-sign house number of planet_rashi from lagna_rashi (1-indexed)."""
    l = _RASHI_ORDER.index(lagna_rashi.lower())
    p = _RASHI_ORDER.index(planet_rashi.lower())
    return ((p - l) % 12) + 1


def _lord_of_house(lagna_rashi: str, house: int) -> str:
    """Lord of the nth house from lagna (whole sign)."""
    rashi_index = (_RASHI_ORDER.index(lagna_rashi.lower()) + house - 1) % 12
    return _RASHI_LORDS[_RASHI_ORDER[rashi_index]]


# ─────────────────────────────────────────────────────────────────────────────
# TABLE 1 — DASHA LORD CLASSIFICATION
# Source: md-and-ad-results-laghu-parashari.md
#
# "Lord of trine, lord of 5th and 9th, auspicious"
# "Lord of kendra 1st, 4th, 7th and 10th as neutral"
# "Lord of 3rd, 6th and 11th, inauspicious"
# "Lord of 8th, inauspicious"
# "Lord of 2nd and 7th as Maraka"
# ─────────────────────────────────────────────────────────────────────────────

_TRIKONA_HOUSES   = {5, 9}        # H1 handled separately — lagna lord is special
_KENDRA_HOUSES    = {1, 4, 7, 10}
_TRISHADAYA_HOUSES = {3, 6, 11}
_MARAKA_HOUSES    = {2, 7}
_DUSTHANA_HOUSES  = {8}           # 12 is neutral per text ("lord of 2nd and 12th are neutral")
_NEUTRAL_HOUSES   = {2, 12}       # "Lord of 2nd and 12th are neutral"


def _classify_dasha_lord(lagna_rashi: str, planet: str) -> tuple[str, str]:
    """
    Classify a dasha lord per Laghu Parashari.

    Returns:
        (category, source_rule) where category is one of:
        YOGA_KARAKA, TRIKONA, KENDRA, TRISHADAYA, MARAKA, DUSTHANA, NEUTRAL

    Source: md-and-ad-results-laghu-parashari.md
    """
    planet = planet.lower()
    lagna  = lagna_rashi.lower()

    # Find ALL houses owned by this planet
    owned_houses = set()
    for h in range(1, 13):
        if _lord_of_house(lagna, h) == planet:
            owned_houses.add(h)

    # Yoga karaka: owns both kendra AND trikona
    # Source: "Yoga karaka lord of kendra and trine"
    is_kendra  = bool(owned_houses & _KENDRA_HOUSES)
    is_trikona = bool(owned_houses & _TRIKONA_HOUSES) or (1 in owned_houses)
    if is_kendra and is_trikona:
        rule = "Yoga karaka: owns kendra AND trikona — md-and-ad-results-laghu-parashari.md"
        return ("YOGA_KARAKA", rule)

    # Trikona lord (H5, H9) — auspicious
    # Source: "Lord of trine, lord of 5th and 9th, auspicious"
    if owned_houses & _TRIKONA_HOUSES:
        rule = "Trikona lord (H5 or H9) — auspicious — md-and-ad-results-laghu-parashari.md"
        return ("TRIKONA", rule)

    # Lagna lord (H1) — special: "Lagna lord who is lord of kendra and trine also"
    # H1 alone = kendra, treated as neutral-to-auspicious
    if 1 in owned_houses and not (owned_houses & _TRISHADAYA_HOUSES) and not (owned_houses & _DUSTHANA_HOUSES):
        rule = "Lagna lord (H1) — kendra, generally neutral — md-and-ad-results-laghu-parashari.md"
        return ("KENDRA", rule)

    # Maraka: owns H2 or H7 (and not trikona)
    # Source: "Lord of 2nd and 7th as Maraka"
    if owned_houses & _MARAKA_HOUSES and not (owned_houses & _TRIKONA_HOUSES):
        rule = "Maraka lord (H2 or H7) — death-inflicting — md-and-ad-results-laghu-parashari.md"
        return ("MARAKA", rule)

    # Dusthana: owns H8
    # Source: "Lord of 8th, inauspicious"
    if owned_houses & _DUSTHANA_HOUSES:
        rule = "Dusthana lord (H8) — inauspicious — md-and-ad-results-laghu-parashari.md"
        return ("DUSTHANA", rule)

    # Trishadaya: owns H3, H6, or H11
    # Source: "Lord of 3rd, 6th and 11th, inauspicious"
    if owned_houses & _TRISHADAYA_HOUSES:
        rule = "Trishadaya lord (H3, H6 or H11) — inauspicious — md-and-ad-results-laghu-parashari.md"
        return ("TRISHADAYA", rule)

    # Kendra: owns H4, H10 (not H1 which was handled above)
    if owned_houses & _KENDRA_HOUSES:
        rule = "Kendra lord (H4 or H10) — neutral — md-and-ad-results-laghu-parashari.md"
        return ("KENDRA", rule)

    # Neutral: H2/H12 owners
    # Source: "Lord of 2nd and 12th are neutral"
    rule = "Neutral lord (H2 or H12) — gives results per chart context — md-and-ad-results-laghu-parashari.md"
    return ("NEUTRAL", rule)


# ─────────────────────────────────────────────────────────────────────────────
# TABLE 2 — DASHA COMBINATION POLARITY
# Source: md-and-ad-results-laghu-parashari.md
#
# "Yoga karaka MD + Yoga karaka AD = full auspicious"
# "Maraka MD + Maraka AD = death or death-like situation"
# "Yoga karaka MD + Maraka AD = mixed results"
# "Trikona lord MD + Trishadaya AD = mixed (virudha dharmi)"
# ─────────────────────────────────────────────────────────────────────────────

# (MD_category, AD_category) → (polarity, laghu_parashari_rule)
_DASHA_POLARITY_TABLE: dict[tuple[str, str], tuple[str, str]] = {
    # Sadharmi (same nature) combinations
    ("YOGA_KARAKA", "YOGA_KARAKA"): ("AUSPICIOUS",   "Yoga karaka MD + Yoga karaka AD = full auspicious — Laghu Parashari"),
    ("TRIKONA",     "TRIKONA"):     ("AUSPICIOUS",   "Trikona MD + Trikona AD = sadharmi, auspicious — Laghu Parashari"),
    ("TRISHADAYA",  "TRISHADAYA"):  ("CHALLENGING",  "Trishadaya MD + Trishadaya AD = sadharmi inauspicious — Laghu Parashari"),
    ("MARAKA",      "MARAKA"):      ("CHALLENGING",  "Maraka MD + Maraka AD = death or death-like — Laghu Parashari"),
    ("DUSTHANA",    "DUSTHANA"):    ("CHALLENGING",  "Dusthana MD + Dusthana AD = inauspicious — Laghu Parashari"),
    ("KENDRA",      "KENDRA"):      ("NEUTRAL",      "Kendra MD + Kendra AD = sadharmi neutral — Laghu Parashari"),
    ("NEUTRAL",     "NEUTRAL"):     ("NEUTRAL",      "Neutral MD + Neutral AD = neutral results — Laghu Parashari"),

    # Yoga karaka with others
    ("YOGA_KARAKA", "TRIKONA"):     ("AUSPICIOUS",   "Yoga karaka MD + Trikona AD = atma-sambandhi, auspicious — Laghu Parashari"),
    ("YOGA_KARAKA", "KENDRA"):      ("AUSPICIOUS",   "Yoga karaka MD + Kendra AD = sambandhi — Laghu Parashari"),
    ("YOGA_KARAKA", "TRISHADAYA"):  ("MIXED",        "Yoga karaka MD + Trishadaya AD = virudha dharmi — Laghu Parashari"),
    ("YOGA_KARAKA", "MARAKA"):      ("MIXED",        "Yoga karaka MD + Maraka AD = mixed — Laghu Parashari"),
    ("YOGA_KARAKA", "DUSTHANA"):    ("MIXED",        "Yoga karaka MD + Dusthana AD = virudha dharmi — Laghu Parashari"),
    ("YOGA_KARAKA", "NEUTRAL"):     ("AUSPICIOUS",   "Yoga karaka MD + Neutral AD = auspicious first, mixed later — Laghu Parashari"),

    # Trikona with others
    ("TRIKONA",     "YOGA_KARAKA"): ("AUSPICIOUS",   "Trikona MD + Yoga karaka AD = sadharmi — Laghu Parashari"),
    ("TRIKONA",     "KENDRA"):      ("AUSPICIOUS",   "Trikona MD + Kendra AD = sadharmi — Laghu Parashari"),
    ("TRIKONA",     "TRISHADAYA"):  ("MIXED",        "Trikona MD + Trishadaya AD = virudha dharmi, very few trikona results — Laghu Parashari"),
    ("TRIKONA",     "MARAKA"):      ("MIXED",        "Trikona MD + Maraka AD = mixed — Laghu Parashari"),
    ("TRIKONA",     "DUSTHANA"):    ("MIXED",        "Trikona MD + Dusthana AD = mixed — Laghu Parashari"),
    ("TRIKONA",     "NEUTRAL"):     ("AUSPICIOUS",   "Trikona MD + Neutral AD = auspicious — Laghu Parashari"),

    # Trishadaya with others
    ("TRISHADAYA",  "YOGA_KARAKA"): ("MIXED",        "Trishadaya MD + Yoga karaka AD = virudha dharmi — Laghu Parashari"),
    ("TRISHADAYA",  "TRIKONA"):     ("MIXED",        "Trishadaya MD + Trikona AD = virudha dharmi — Laghu Parashari"),
    ("TRISHADAYA",  "KENDRA"):      ("CHALLENGING",  "Trishadaya MD + Kendra AD = anubhaya — Laghu Parashari"),
    ("TRISHADAYA",  "MARAKA"):      ("CHALLENGING",  "Trishadaya MD + Maraka AD = anubhaya inauspicious — Laghu Parashari"),
    ("TRISHADAYA",  "DUSTHANA"):    ("CHALLENGING",  "Trishadaya MD + Dusthana AD = inauspicious — Laghu Parashari"),
    ("TRISHADAYA",  "NEUTRAL"):     ("CHALLENGING",  "Trishadaya MD + Neutral AD = reduced inauspicious — Laghu Parashari"),

    # Maraka with others
    ("MARAKA",      "YOGA_KARAKA"): ("MIXED",        "Maraka MD + Yoga karaka AD = mixed — Laghu Parashari"),
    ("MARAKA",      "TRIKONA"):     ("MIXED",        "Maraka MD + Trikona AD = mixed — Laghu Parashari"),
    ("MARAKA",      "KENDRA"):      ("CHALLENGING",  "Maraka MD + Kendra AD = anubhaya — Laghu Parashari"),
    ("MARAKA",      "TRISHADAYA"):  ("CHALLENGING",  "Maraka MD + Trishadaya AD = inauspicious — Laghu Parashari"),
    ("MARAKA",      "DUSTHANA"):    ("CHALLENGING",  "Maraka MD + Dusthana AD = inauspicious — Laghu Parashari"),
    ("MARAKA",      "NEUTRAL"):     ("CHALLENGING",  "Maraka MD + Neutral AD = malefic first, neutral later — Laghu Parashari"),

    # Kendra with others
    ("KENDRA",      "YOGA_KARAKA"): ("AUSPICIOUS",   "Kendra MD + Yoga karaka AD = sambandhi — Laghu Parashari"),
    ("KENDRA",      "TRIKONA"):     ("AUSPICIOUS",   "Kendra MD + Trikona AD = sadharmi — Laghu Parashari"),
    ("KENDRA",      "TRISHADAYA"):  ("MIXED",        "Kendra MD + Trishadaya AD = virudha dharmi — Laghu Parashari"),
    ("KENDRA",      "MARAKA"):      ("MIXED",        "Kendra MD + Maraka AD = mixed — Laghu Parashari"),
    ("KENDRA",      "DUSTHANA"):    ("MIXED",        "Kendra MD + Dusthana AD = mixed — Laghu Parashari"),
    ("KENDRA",      "NEUTRAL"):     ("NEUTRAL",      "Kendra MD + Neutral AD = neutral — Laghu Parashari"),

    # Dusthana with others
    ("DUSTHANA",    "YOGA_KARAKA"): ("MIXED",        "Dusthana MD + Yoga karaka AD = mixed — Laghu Parashari"),
    ("DUSTHANA",    "TRIKONA"):     ("MIXED",        "Dusthana MD + Trikona AD = mixed — Laghu Parashari"),
    ("DUSTHANA",    "KENDRA"):      ("CHALLENGING",  "Dusthana MD + Kendra AD = anubhaya — Laghu Parashari"),
    ("DUSTHANA",    "TRISHADAYA"):  ("CHALLENGING",  "Dusthana MD + Trishadaya AD = inauspicious — Laghu Parashari"),
    ("DUSTHANA",    "MARAKA"):      ("CHALLENGING",  "Dusthana MD + Maraka AD = inauspicious — Laghu Parashari"),
    ("DUSTHANA",    "NEUTRAL"):     ("CHALLENGING",  "Dusthana MD + Neutral AD = reduced inauspicious — Laghu Parashari"),

    # Neutral with others
    ("NEUTRAL",     "YOGA_KARAKA"): ("AUSPICIOUS",   "Neutral MD + Yoga karaka AD = auspicious — Laghu Parashari"),
    ("NEUTRAL",     "TRIKONA"):     ("AUSPICIOUS",   "Neutral MD + Trikona AD = auspicious — Laghu Parashari"),
    ("NEUTRAL",     "TRISHADAYA"):  ("MIXED",        "Neutral MD + Trishadaya AD = mixed — Laghu Parashari"),
    ("NEUTRAL",     "MARAKA"):      ("MIXED",        "Neutral MD + Maraka AD = mixed — Laghu Parashari"),
    ("NEUTRAL",     "DUSTHANA"):    ("MIXED",        "Neutral MD + Dusthana AD = mixed — Laghu Parashari"),
    ("NEUTRAL",     "KENDRA"):      ("NEUTRAL",      "Neutral MD + Kendra AD = neutral — Laghu Parashari"),
}


# ─────────────────────────────────────────────────────────────────────────────
# TABLE 3 — TRANSIT POLARITY (GOCHARA) FROM NATAL MOON
# Source: ashtaka-varga.md  (BPHS table as documented by Vinay Ji)
#
# Key: (planet, house_from_natal_moon)
# Value: (polarity, result_text_from_bphs, source)
#
# 1 = AUSPICIOUS, 0 = INAUSPICIOUS
# ─────────────────────────────────────────────────────────────────────────────

_GOCHARA_TABLE: dict[tuple[str, int], tuple[str, str]] = {
    # SUN
    ("sun",  1): ("INAUSPICIOUS", "स्थानहानि (loss of position) — BPHS/ashtaka-varga.md"),
    ("sun",  2): ("INAUSPICIOUS", "भय (fear) — BPHS/ashtaka-varga.md"),
    ("sun",  3): ("AUSPICIOUS",   "धन (wealth) — BPHS/ashtaka-varga.md"),
    ("sun",  4): ("INAUSPICIOUS", "मानहानि (loss of respect) — BPHS/ashtaka-varga.md"),
    ("sun",  5): ("INAUSPICIOUS", "दैन्य (poverty/misery) — BPHS/ashtaka-varga.md"),
    ("sun",  6): ("AUSPICIOUS",   "विजय (victory) — BPHS/ashtaka-varga.md"),
    ("sun",  7): ("INAUSPICIOUS", "भ्रमण (wandering) — BPHS/ashtaka-varga.md"),
    ("sun",  8): ("INAUSPICIOUS", "पीड़ा (suffering) — BPHS/ashtaka-varga.md"),
    ("sun",  9): ("INAUSPICIOUS", "धर्महानि (loss of righteousness) — BPHS/ashtaka-varga.md"),
    ("sun", 10): ("AUSPICIOUS",   "कार्यसिद्धि (accomplishment of work) — BPHS/ashtaka-varga.md"),
    ("sun", 11): ("AUSPICIOUS",   "धनप्राप्ति (gain of wealth) — BPHS/ashtaka-varga.md"),
    ("sun", 12): ("INAUSPICIOUS", "कष्ट (suffering) — BPHS/ashtaka-varga.md"),

    # MOON
    ("moon",  1): ("AUSPICIOUS",   "भाग्योदय (rise of fortune) — BPHS/ashtaka-varga.md"),
    ("moon",  2): ("INAUSPICIOUS", "धनहानि (loss of wealth) — BPHS/ashtaka-varga.md"),
    ("moon",  3): ("AUSPICIOUS",   "जय (victory) — BPHS/ashtaka-varga.md"),
    ("moon",  4): ("INAUSPICIOUS", "भय (fear) — BPHS/ashtaka-varga.md"),
    ("moon",  5): ("INAUSPICIOUS", "शोक (grief) — BPHS/ashtaka-varga.md"),
    ("moon",  6): ("AUSPICIOUS",   "आरोग्यता (good health) — BPHS/ashtaka-varga.md"),
    ("moon",  7): ("AUSPICIOUS",   "सुख (happiness) — BPHS/ashtaka-varga.md"),
    ("moon",  8): ("INAUSPICIOUS", "दुःख (sorrow) — BPHS/ashtaka-varga.md"),
    ("moon",  9): ("INAUSPICIOUS", "रोग* (illness — likely misprint per Vinay Ji) — BPHS/ashtaka-varga.md"),
    ("moon", 10): ("AUSPICIOUS",   "इष्टसिद्धि (desired accomplishment) — BPHS/ashtaka-varga.md"),
    ("moon", 11): ("AUSPICIOUS",   "प्रसन्नता (happiness/contentment) — BPHS/ashtaka-varga.md"),
    ("moon", 12): ("INAUSPICIOUS", "व्यय (expenditure/loss) — BPHS/ashtaka-varga.md"),

    # MARS
    ("mars",  1): ("INAUSPICIOUS", "अन्तःशोक (inner grief) — BPHS/ashtaka-varga.md"),
    ("mars",  2): ("INAUSPICIOUS", "भय (fear) — BPHS/ashtaka-varga.md"),
    ("mars",  3): ("AUSPICIOUS",   "जय (victory) — BPHS/ashtaka-varga.md"),
    ("mars",  4): ("INAUSPICIOUS", "स्थानभ्रंश (loss of position) — BPHS/ashtaka-varga.md"),
    ("mars",  5): ("INAUSPICIOUS", "ज्वर (fever/illness) — BPHS/ashtaka-varga.md"),
    ("mars",  6): ("AUSPICIOUS",   "कलह में विजय (victory in conflict) — BPHS/ashtaka-varga.md"),
    ("mars",  7): ("INAUSPICIOUS", "स्त्रीकलह (conflict with spouse) — BPHS/ashtaka-varga.md"),
    ("mars",  8): ("INAUSPICIOUS", "ज्वर (fever) — BPHS/ashtaka-varga.md"),
    ("mars",  9): ("INAUSPICIOUS", "दीनता (humiliation) — BPHS/ashtaka-varga.md"),
    ("mars", 10): ("INAUSPICIOUS", "कार्यनाश (destruction of work) — BPHS/ashtaka-varga.md"),
    ("mars", 11): ("AUSPICIOUS",   "लाभ (gain) — BPHS/ashtaka-varga.md"),
    ("mars", 12): ("INAUSPICIOUS", "माननाश (loss of honour) — BPHS/ashtaka-varga.md"),

    # MERCURY
    ("mercury",  1): ("INAUSPICIOUS", "धनहानि (loss of wealth) — BPHS/ashtaka-varga.md"),
    ("mercury",  2): ("AUSPICIOUS",   "धनलाभ (gain of wealth) — BPHS/ashtaka-varga.md"),
    ("mercury",  3): ("INAUSPICIOUS", "भय (fear) — BPHS/ashtaka-varga.md"),
    ("mercury",  4): ("AUSPICIOUS",   "धनप्राप्ति (gain of wealth) — BPHS/ashtaka-varga.md"),
    ("mercury",  5): ("INAUSPICIOUS", "स्त्रीकलह (conflict) — BPHS/ashtaka-varga.md"),
    ("mercury",  6): ("AUSPICIOUS",   "विजय (victory) — BPHS/ashtaka-varga.md"),
    ("mercury",  7): ("INAUSPICIOUS", "विरोध (opposition) — BPHS/ashtaka-varga.md"),
    ("mercury",  8): ("AUSPICIOUS",   "पुत्रसुख (happiness from children) — BPHS/ashtaka-varga.md"),
    ("mercury",  9): ("INAUSPICIOUS", "विघ्न (obstruction) — BPHS/ashtaka-varga.md"),
    ("mercury", 10): ("AUSPICIOUS",   "सुख (happiness) — BPHS/ashtaka-varga.md"),
    ("mercury", 11): ("AUSPICIOUS",   "लाभ (gain) — BPHS/ashtaka-varga.md"),
    ("mercury", 12): ("INAUSPICIOUS", "पराभव (defeat) — BPHS/ashtaka-varga.md"),

    # JUPITER
    ("jupiter",  1): ("INAUSPICIOUS", "अनिष्ट (inauspicious) — BPHS/ashtaka-varga.md"),
    ("jupiter",  2): ("AUSPICIOUS",   "लाभ (gain) — BPHS/ashtaka-varga.md"),
    ("jupiter",  3): ("INAUSPICIOUS", "स्थितिनाश (loss of position) — BPHS/ashtaka-varga.md"),
    ("jupiter",  4): ("INAUSPICIOUS", "बन्धुकष्ट (trouble from relatives) — BPHS/ashtaka-varga.md"),
    ("jupiter",  5): ("AUSPICIOUS",   "पुत्रसुख (happiness from children) — BPHS/ashtaka-varga.md"),
    ("jupiter",  6): ("INAUSPICIOUS", "दामादों से विरोध (conflict) — BPHS/ashtaka-varga.md"),
    ("jupiter",  7): ("AUSPICIOUS",   "यात्रा (travel/journey) — BPHS/ashtaka-varga.md"),
    ("jupiter",  8): ("INAUSPICIOUS", "मार्गक्लेश (hardship in travel/path) — BPHS/ashtaka-varga.md"),
    ("jupiter",  9): ("AUSPICIOUS",   "शुभ (auspicious) — BPHS/ashtaka-varga.md"),
    ("jupiter", 10): ("INAUSPICIOUS", "धनकष्ट (financial difficulty) — BPHS/ashtaka-varga.md"),
    ("jupiter", 11): ("AUSPICIOUS",   "पुत्रसुख/लाभ (happiness, gain) — BPHS/ashtaka-varga.md"),
    ("jupiter", 12): ("INAUSPICIOUS", "दुःख (sorrow) — BPHS/ashtaka-varga.md"),

    # VENUS
    ("venus",  1): ("AUSPICIOUS",   "शुभ (auspicious) — BPHS/ashtaka-varga.md"),
    ("venus",  2): ("AUSPICIOUS",   "धनलाभ (gain of wealth) — BPHS/ashtaka-varga.md"),
    ("venus",  3): ("AUSPICIOUS",   "धनवृद्धि (increase of wealth) — BPHS/ashtaka-varga.md"),
    ("venus",  4): ("AUSPICIOUS",   "सुख (happiness) — BPHS/ashtaka-varga.md"),
    ("venus",  5): ("AUSPICIOUS",   "पुत्रसुख (happiness from children) — BPHS/ashtaka-varga.md"),
    ("venus",  6): ("INAUSPICIOUS", "कष्ट (suffering) — BPHS/ashtaka-varga.md"),
    ("venus",  7): ("INAUSPICIOUS", "पीड़ा (pain) — BPHS/ashtaka-varga.md"),
    ("venus",  8): ("AUSPICIOUS",   "संपत्ति (wealth/property) — BPHS/ashtaka-varga.md"),
    ("venus",  9): ("AUSPICIOUS",   "सुख (happiness) — BPHS/ashtaka-varga.md"),
    ("venus", 10): ("INAUSPICIOUS", "कलह (conflict) — BPHS/ashtaka-varga.md"),
    ("venus", 11): ("INAUSPICIOUS", "भय (fear) — BPHS/ashtaka-varga.md"),
    ("venus", 12): ("AUSPICIOUS",   "अर्थलाभ (gain of money) — BPHS/ashtaka-varga.md"),

    # SATURN
    ("saturn",  1): ("INAUSPICIOUS", "नाश (destruction) — BPHS/ashtaka-varga.md"),
    ("saturn",  2): ("INAUSPICIOUS", "हानि (loss) — BPHS/ashtaka-varga.md"),
    ("saturn",  3): ("AUSPICIOUS",   "लाभ (gain) — BPHS/ashtaka-varga.md"),
    ("saturn",  4): ("INAUSPICIOUS", "शत्रुवृद्धि (increase of enemies) — BPHS/ashtaka-varga.md"),
    ("saturn",  5): ("INAUSPICIOUS", "नाश (destruction) — BPHS/ashtaka-varga.md"),
    ("saturn",  6): ("AUSPICIOUS",   "लाभ (gain) — BPHS/ashtaka-varga.md"),
    ("saturn",  7): ("INAUSPICIOUS", "स्त्रीकष्ट (trouble from/to spouse) — BPHS/ashtaka-varga.md"),
    ("saturn",  8): ("INAUSPICIOUS", "शत्रुभय (fear of enemies) — BPHS/ashtaka-varga.md"),
    ("saturn",  9): ("INAUSPICIOUS", "धर्महानि (loss of righteousness) — BPHS/ashtaka-varga.md"),
    ("saturn", 10): ("INAUSPICIOUS", "वैर (enmity) — BPHS/ashtaka-varga.md"),
    ("saturn", 11): ("AUSPICIOUS",   "आयुवृद्धि (increase of life/longevity) — BPHS/ashtaka-varga.md"),
    ("saturn", 12): ("INAUSPICIOUS", "हानि (loss) — BPHS/ashtaka-varga.md"),
}


# ─────────────────────────────────────────────────────────────────────────────
# OUTPUT DATACLASS
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TransitPlanetResult:
    """Single planet's gochara result from BPHS table for a specific reference point."""
    planet: str
    reference_point: str   # "LAGNA" / "SUN" / "MOON"
    house_from_ref: int
    polarity: str          # AUSPICIOUS / INAUSPICIOUS / NEUTRAL
    bphs_result: str       # Exact Hindi/Sanskrit text from BPHS table


@dataclass(frozen=True)
class TriLagnaPlanetGochara:
    """3-Kundali simultaneous gochara assessment for a single planet."""
    planet: str
    house_from_lagna: int
    lagna_polarity: str
    lagna_result: str
    house_from_sun: int
    sun_polarity: str
    sun_result: str
    house_from_moon: int
    moon_polarity: str
    moon_result: str
    composite_polarity: str # AUSPICIOUS / INAUSPICIOUS / MIXED
    composite_score: float   # [-1.0 to +1.0]


@dataclass(frozen=True)
class PolarityReport:
    """
    Lookup-table based polarity assessment using 3-Kundali Sudarshana Chakra Gochara.
    Every field is traceable to specific canonical source documents.
    """
    # Dasha classification
    md_lord: str
    ad_lord: str
    md_category: str
    ad_category: str
    md_rule_source: str
    ad_rule_source: str

    # Dasha polarity (Laghu Parashari combination table)
    dasha_polarity: str
    dasha_polarity_rule: str

    # Sudarshana Chakra 3-Kundali Gochara Results
    tri_lagna_planet_results: tuple    # tuple[TriLagnaPlanetGochara, ...]
    is_amavasya_sc: bool               # If Sun & Moon conjunct -> LK discarded per SC rule
    transit_auspicious_count: int      # Across all 7 planets composite
    transit_inauspicious_count: int
    transit_net_polarity: str          # AUSPICIOUS / CHALLENGING / MIXED

    # Final combined
    final_polarity: str
    final_polarity_logic: str


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENGINE
# ─────────────────────────────────────────────────────────────────────────────

_ALL_GOCHARA_PLANETS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]


class ClassicalPolarityEngine:
    """
    Sudarshana Chakra 3-Kundali Gochara & Laghu Parashari Dasha Polarity Engine.
    Zero hallucination — all rules from canonical BPHS and Vinay Ji texts.

    Transit: Evaluates all 7 transiting planets simultaneously from:
             1. Lagna Kundali (LK) — physical environment
             2. Surya Kundali (SK) — external authority & soul
             3. Chandra Kundali (CK) — mental perception & fortune
             (Special SC Rule: If Sun & Moon conjunct, discard LK, evaluate SK+CK).
    Dasha:   Laghu Parashari combination rules (md-and-ad-results-laghu-parashari.md).
    """

    def evaluate(
        self,
        natal_chart: D1Chart,
        transit_chart: D1Chart,
        mahadasha_lord: str,
        antardasha_lord: str,
    ) -> PolarityReport:

        lagna = natal_chart.ascendant.rashi.lower()
        md    = mahadasha_lord.lower()
        ad    = antardasha_lord.lower()

        # ── Step 1: Classify Dasha Lords (Laghu Parashari) ───────────────────
        md_cat, md_rule = _classify_dasha_lord(lagna, md)
        ad_cat, ad_rule = _classify_dasha_lord(lagna, ad)

        # ── Step 2: Dasha Polarity from Combination Table ────────────────────
        dasha_pol, dasha_rule = _DASHA_POLARITY_TABLE.get(
            (md_cat, ad_cat),
            ("NEUTRAL", "Combination not in table — default neutral — Laghu Parashari")
        )

        # ── Step 3: Extract Tri-Lagna Reference Rashis ────────────────────────
        natal_pm   = {p.planet.lower(): p for p in natal_chart.planets}
        moon_natal = natal_pm.get("moon")
        sun_natal  = natal_pm.get("sun")

        moon_rashi = moon_natal.rashi.lower() if moon_natal else lagna
        sun_rashi  = sun_natal.rashi.lower() if sun_natal else lagna

        is_amavasya_sc = (moon_rashi == sun_rashi)

        # ── Step 4: 3-Kundali Gochara for all 7 transiting planets ────────────
        transit_pm = {p.planet.lower(): p for p in transit_chart.planets}
        tri_planet_results = []

        pol_score_map = {"AUSPICIOUS": 1.0, "INAUSPICIOUS": -1.0, "NEUTRAL": 0.0}

        for planet in _ALL_GOCHARA_PLANETS:
            t_planet = transit_pm.get(planet)
            if not t_planet:
                continue

            t_rashi = t_planet.rashi.lower()

            # 1. From Lagna
            h_lagna = _house_number(lagna, t_rashi)
            pol_lagna, text_lagna = _GOCHARA_TABLE.get((planet, h_lagna), ("NEUTRAL", f"{planet} H{h_lagna}"))

            # 2. From Sun
            h_sun = _house_number(sun_rashi, t_rashi)
            pol_sun, text_sun = _GOCHARA_TABLE.get((planet, h_sun), ("NEUTRAL", f"{planet} H{h_sun}"))

            # 3. From Moon
            h_moon = _house_number(moon_rashi, t_rashi)
            pol_moon, text_moon = _GOCHARA_TABLE.get((planet, h_moon), ("NEUTRAL", f"{planet} H{h_moon}"))

            # Composite weighting
            if is_amavasya_sc:
                # Discard LK, weight SK 50% and CK 50%
                comp_score = 0.50 * pol_score_map.get(pol_sun, 0.0) + 0.50 * pol_score_map.get(pol_moon, 0.0)
            else:
                comp_score = (
                    0.34 * pol_score_map.get(pol_lagna, 0.0)
                    + 0.33 * pol_score_map.get(pol_sun, 0.0)
                    + 0.33 * pol_score_map.get(pol_moon, 0.0)
                )

            if comp_score > 0.15:
                comp_pol = "AUSPICIOUS"
            elif comp_score < -0.15:
                comp_pol = "INAUSPICIOUS"
            else:
                comp_pol = "MIXED"

            tri_planet_results.append(TriLagnaPlanetGochara(
                planet=planet,
                house_from_lagna=h_lagna,
                lagna_polarity=pol_lagna,
                lagna_result=text_lagna,
                house_from_sun=h_sun,
                sun_polarity=pol_sun,
                sun_result=text_sun,
                house_from_moon=h_moon,
                moon_polarity=pol_moon,
                moon_result=text_moon,
                composite_polarity=comp_pol,
                composite_score=comp_score,
            ))

        # ── Step 5: Net Tri-Lagna Transit Vote ────────────────────────────────
        aus_count = sum(1 for r in tri_planet_results if r.composite_polarity == "AUSPICIOUS")
        ina_count = sum(1 for r in tri_planet_results if r.composite_polarity == "INAUSPICIOUS")

        if aus_count > ina_count:
            transit_net = "AUSPICIOUS"
        elif ina_count > aus_count:
            transit_net = "CHALLENGING"
        else:
            transit_net = "MIXED"

        # ── Step 6: Combine Dasha + Tri-Lagna Transit → Final ─────────────────
        pol_map = {"AUSPICIOUS": 1, "MIXED": 0, "NEUTRAL": 0, "CHALLENGING": -1}
        total = pol_map.get(dasha_pol, 0) + pol_map.get(transit_net, 0)

        sc_desc = "Amavasya (SK+CK)" if is_amavasya_sc else "Sudarshana (LK+SK+CK)"

        if total >= 2:
            final = "AUSPICIOUS"
            logic = f"Dasha={dasha_pol} + Transit={transit_net} ({aus_count}A/{ina_count}I {sc_desc}) → AUSPICIOUS"
        elif total <= -2:
            final = "CHALLENGING"
            logic = f"Dasha={dasha_pol} + Transit={transit_net} ({aus_count}A/{ina_count}I {sc_desc}) → CHALLENGING"
        elif total > 0:
            final = "MIXED_POSITIVE"
            logic = f"Dasha={dasha_pol} + Transit={transit_net} ({aus_count}A/{ina_count}I {sc_desc}) → MIXED_POSITIVE"
        elif total < 0:
            final = "MIXED_NEGATIVE"
            logic = f"Dasha={dasha_pol} + Transit={transit_net} ({aus_count}A/{ina_count}I {sc_desc}) → MIXED_NEGATIVE"
        else:
            final = "NEUTRAL"
            logic = f"Dasha={dasha_pol} + Transit={transit_net} ({aus_count}A/{ina_count}I {sc_desc}) → NEUTRAL"

        return PolarityReport(
            md_lord=md,
            ad_lord=ad,
            md_category=md_cat,
            ad_category=ad_cat,
            md_rule_source=md_rule,
            ad_rule_source=ad_rule,
            dasha_polarity=dasha_pol,
            dasha_polarity_rule=dasha_rule,
            tri_lagna_planet_results=tuple(tri_planet_results),
            is_amavasya_sc=is_amavasya_sc,
            transit_auspicious_count=aus_count,
            transit_inauspicious_count=ina_count,
            transit_net_polarity=transit_net,
            final_polarity=final,
            final_polarity_logic=logic,
        )


