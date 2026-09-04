"""
AstroOS — Navatara / Tarabala

Sourcing per the sensitive-timing skill's "Extended Navatara framework"
and "27-Tara year cycle" sections. Two DISTINCT naming conventions are
used deliberately, not merged:

1. **9-name cycle** (repeats 3x across 27 nakshatras) — used for the
   three Tarabala dimensions (natal placement, transit, lordship) and
   for the dual-viewpoint (Moon+Lagna) filtering. Position formula:
   `(target_index - janma_index) mod 9`, 0-indexed, Janma Nakshatra
   itself counts as position 0 (the skill's own "inclusive counting"
   description, position 1 in 1-indexed terms).
2. **Full 27-name extended table** (distinct name at every position,
   NOT a repeating cycle) — used only for (a) the yearly Tara cycle
   (each year of life, counted by exact solar-return anniversaries of
   the birth moment) and (b) career-specific questions (10th = Karma,
   6th = Sadhaka checked against the running dasha lord).

Confusing the two would misname the star that matters most for a given
question type — this module keeps them as separate functions rather
than one parameterised one, so a caller can't accidentally apply the
wrong table.

**Lordship Tarabala — explicitly flagged as unconfirmed application
methodology, not unset data.** The FIXED planet -> Tara-position mapping
below (each of the 9 Tara positions corresponds, in Vimshottari dasha-
lord order, to one planet) is stated directly in the source skill. What
is NOT confirmed against a specific reference is *how* this fixed
mapping gets applied to a specific reading (e.g. whether it's about the
dasha lord's own ruled-Tara being "active" during its own dasha, or
something else). This module exposes the mapping itself
(`LORDSHIP_TARA_POSITION`) but does not compute an "active lordship
Tarabala" verdict — callers should state the general shape rather than
present a specific computed reading as validated, per the skill's own
caution.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from packages.shared.enums import Nakshatra

_STANDARD_27: list[str] = [n.value for n in Nakshatra]

# ── 9-name cycle (Tarabala dimensions) ──────────────────────────────────────

TARA_NAMES_9 = [
    "janma", "sampat", "vipat", "kshema", "pratyari",
    "sadhaka", "naidhana", "mitra", "paramamitra",
]

FAVORABLE_TARA_9 = {"sampat", "kshema", "sadhaka", "mitra", "paramamitra"}
UNFAVORABLE_TARA_9 = {"janma", "vipat", "pratyari", "naidhana"}


def tara_position_9(janma_nakshatra: str, target_nakshatra: str) -> int:
    """0-8 Tara position of `target_nakshatra` counted from
    `janma_nakshatra` (0 = Janma itself). Both must be standard
    27-system tokens (packages.shared.enums.Nakshatra values)."""
    janma_idx = _STANDARD_27.index(janma_nakshatra)
    target_idx = _STANDARD_27.index(target_nakshatra)
    return (target_idx - janma_idx) % 9


def tara_name_9(position: int) -> str:
    return TARA_NAMES_9[position % 9]


def is_favorable_tara_9(position: int) -> bool:
    return TARA_NAMES_9[position % 9] in FAVORABLE_TARA_9


def natal_tarabala(janma_nakshatra: str, planet_natal_nakshatra: str) -> tuple[int, str, bool]:
    """(position, name, is_favorable) for a planet's own natal
    nakshatra, relative to the Janma Nakshatra."""
    pos = tara_position_9(janma_nakshatra, planet_natal_nakshatra)
    return pos, tara_name_9(pos), is_favorable_tara_9(pos)


def transit_tarabala(janma_nakshatra: str, planet_transit_nakshatra: str) -> tuple[int, str, bool]:
    """Same computation as natal_tarabala, applied to a planet's
    current transiting nakshatra instead of its natal one."""
    pos = tara_position_9(janma_nakshatra, planet_transit_nakshatra)
    return pos, tara_name_9(pos), is_favorable_tara_9(pos)


# Fixed Vimshottari dasha-lord order -> Tara position (source-stated mapping).
LORDSHIP_TARA_POSITION: dict[str, str] = {
    "ketu": "janma",
    "venus": "sampat",
    "sun": "vipat",
    "moon": "kshema",
    "mars": "pratyari",
    "rahu": "sadhaka",
    "jupiter": "naidhana",
    "saturn": "mitra",
    "mercury": "paramamitra",
}


# ── Dual-viewpoint (Moon + Lagna) filtering ─────────────────────────────────


def favorable_nakshatras_from(janma_nakshatra: str) -> set[str]:
    """The 15 (of 27) nakshatras that are a favorable Tara from the
    given reference nakshatra (Moon's Janma Nakshatra, or the Lagna
    Nakshatra, per the dual-viewpoint technique)."""
    return {
        n for n in _STANDARD_27
        if is_favorable_tara_9(tara_position_9(janma_nakshatra, n))
    }


def best_stars(moon_janma_nakshatra: str, lagna_nakshatra: str) -> set[str]:
    """Intersection of both viewpoints' favorable-star sets — the
    native's personally strongest stars, per "The Nadi Practitioner's
    Modified Tarabalam" technique."""
    return favorable_nakshatras_from(moon_janma_nakshatra) & favorable_nakshatras_from(lagna_nakshatra)


# ── Full 27-name extended table (yearly cycle + career) ─────────────────────

# Position -> name, 1-indexed (index 0 of this list == position 1 == Janma).
EXTENDED_27_NAMES: list[str] = [
    "janma", "sampat", "vipat", "kshema", "pratyak", "sadhaka", "naidhana", "mitra", "paramamitra",
    "karma", "sampat", "vipat", "kshema", "pratyak", "sadhaka", "sanghatik", "mitra", "samudayik",
    "aadhaana", "sampat", "vipat", "kshema", "vinasika", "sadhaka", "jaati", "desa", "abhisheka",
]

KARMA_POSITION = 10  # 1-indexed
SADHAKA_CAREER_POSITION = 6  # 1-indexed (distinct from the 9-cycle "sadhaka" at the same number, same underlying formula)


def extended_27_position(janma_nakshatra: str, target_nakshatra: str) -> int:
    """1-27 position of `target_nakshatra` from `janma_nakshatra`,
    inclusive counting (Janma Nakshatra itself = position 1)."""
    janma_idx = _STANDARD_27.index(janma_nakshatra)
    target_idx = _STANDARD_27.index(target_nakshatra)
    return ((target_idx - janma_idx) % 27) + 1


def extended_27_name(position_1_indexed: int) -> str:
    return EXTENDED_27_NAMES[(position_1_indexed - 1) % 27]


# ── 28-nakshatra ("28 Star Scheme") extended table ──────────────────────────
#
# A SEPARATE named-position table from EXTENDED_27_NAMES above, found in a
# real SBC tool's `Main` sheet (cell A2: "Choose NakScheme: 28"), citing
# "Sanjay Rath's Brhat Nakshatras" as its source — this is what that
# tool's own "Nakshatra | From Moon | From Lagna" special-points panel
# (visible in the SBC screen's right-hand reference table) is actually
# built from, NOT EXTENDED_27_NAMES; the two must not be conflated even
# though several names overlap.
#
# **Sourcing split, stated explicitly:** the 8 (name, count) overrides
# below are read directly from the xlsm (Main sheet, "28 Star Scheme"
# column, cols named/count/NakName) — Jaati=4, Desa=12, Sanghatika=16,
# Samudayika=18, Aadhana=19, Vainashika=22, Manasa=25, Abhisheka=28.
# Each was cross-checked against that same sheet's own computed example
# (Janma Nakshatra = Uttara Phalguni): e.g. position 4 (Jaati) landed on
# Swati, position 28 (Abhisheka) on Purva Phalguni, position 18
# (Samudayika) on Ashwini — all reproduced exactly by
# extended_28_position()/_STANDARD_28 below, confirming both the
# override counts AND the Abhijit-insertion point are correct together,
# not just individually plausible. The workbook does NOT list the other
# 20 positions explicitly; the baseline filling those (plain 9-cycle,
# continuing past 27 into position 28) is INFERRED by structural
# analogy to EXTENDED_27_NAMES (a 9-cycle baseline with specific
# override positions) — not independently confirmed for this 28-scheme.
# Treat position numbers not in _EXTENDED_28_OVERRIDES with the same
# "not yet independently verified" caution used elsewhere in this
# project for inferred-but-unconfirmed data. "Karma" (from
# EXTENDED_27_NAMES) is NOT part of this 28-scheme column at all — it
# only ever appeared in the 27-scheme block — so it's handled as a
# special case in special_point_nakshatra() below, not folded in here.
_EXTENDED_28_OVERRIDES: dict[int, str] = {
    4: "jaati", 12: "desa", 16: "sanghatika", 18: "samudayika", 19: "aadhana",
    22: "vainashika", 25: "manasa", 28: "abhisheka",
}

# 28-nakshatra token list — Abhijit inserted between Uttara Ashadha and
# Shravana, same insertion point as sarvatobhadra_grid.py's SBC_BORDER
# (that placement IS independently Saravali/Classical Vedic-verified, even though
# this specific 28-scheme Tara table's position-name assignments are not).
_STANDARD_28: list[str] = (
    _STANDARD_27[: _STANDARD_27.index("shravana")]
    + ["abhijit"]
    + _STANDARD_27[_STANDARD_27.index("shravana"):]
)


def extended_28_position(janma_nakshatra: str, target_nakshatra: str) -> int:
    """1-28 position of `target_nakshatra` from `janma_nakshatra` under
    the 28-nakshatra (Abhijit-inclusive) scheme, inclusive counting."""
    janma_idx = _STANDARD_28.index(janma_nakshatra)
    target_idx = _STANDARD_28.index(target_nakshatra)
    return ((target_idx - janma_idx) % 28) + 1


_BASE_9_CYCLE = ["janma", "sampat", "vipat", "kshema", "pratyak", "sadhaka", "naidhana", "mitra", "paramamitra"]


def extended_28_name(position_1_indexed: int) -> str:
    pos = ((position_1_indexed - 1) % 28) + 1
    if pos in _EXTENDED_28_OVERRIDES:
        return _EXTENDED_28_OVERRIDES[pos]
    return _BASE_9_CYCLE[(pos - 1) % 9]


# The 11 named points a real SBC tool's own special-points reference
# panel shows (curated subset — not every 1-28 position, just these
# named ones), in the same order as that panel.
SPECIAL_POINTS_28 = [
    "janma", "karma", "samudayika", "sanghatika", "jaati", "naidhana",
    "desa", "abhisheka", "aadhana", "vainashika", "manasa",
]

_NAME_TO_28_POSITION: dict[str, int] = {name: pos for pos, name in _EXTENDED_28_OVERRIDES.items()}
_NAME_TO_28_POSITION["janma"] = 1  # position 1 is the baseline 9-cycle's "janma", never overridden
_NAME_TO_28_POSITION["naidhana"] = 7  # baseline 9-cycle value, never overridden in the sourced table
# "karma" is NOT part of the 28-scheme column at all (see module note
# above) — it only ever appeared in the 27-scheme block at position 10.
_KARMA_27_POSITION = 10


def special_point_nakshatra(reference_nakshatra: str, point_name: str) -> str:
    """The real nakshatra at a named special point (one of
    SPECIAL_POINTS_28), counted from `reference_nakshatra` (Moon's
    Janma Nakshatra, or Lagna Nakshatra, per the source tool's own
    "From Moon" / "From Lagna" columns). "karma" is the sole exception —
    sourced only under the 27-scheme block, counted on the 27-nakshatra
    list instead; every other name uses the 28-nakshatra (Abhijit-
    inclusive) list, matching how its position count was actually
    sourced."""
    if point_name == "karma":
        ref_idx = _STANDARD_27.index(reference_nakshatra)
        return _STANDARD_27[(ref_idx + _KARMA_27_POSITION - 1) % 27]
    position = _NAME_TO_28_POSITION[point_name]
    ref_idx = _STANDARD_28.index(reference_nakshatra)
    return _STANDARD_28[(ref_idx + position - 1) % 28]


def karma_and_sadhaka_nakshatras(janma_nakshatra: str) -> tuple[str, str]:
    """(Karma nakshatra, Sadhaka nakshatra) — the two career-specific
    reference points, counted inclusively from Janma Nakshatra."""
    janma_idx = _STANDARD_27.index(janma_nakshatra)
    karma_idx = (janma_idx + KARMA_POSITION - 1) % 27
    sadhaka_idx = (janma_idx + SADHAKA_CAREER_POSITION - 1) % 27
    return _STANDARD_27[karma_idx], _STANDARD_27[sadhaka_idx]


# ── Yearly Tara cycle (exact solar-return age boundaries) ───────────────────


def solar_return_boundary(birth_datetime_utc: datetime, age_years: int) -> datetime:
    """The exact UTC moment age `age_years` begins — the anniversary of
    the birth moment, `age_years` years later. Handles the Feb-29 edge
    case by falling back to Feb 28 in a non-leap target year (the same
    convention Python's own date arithmetic has no built-in handling
    for)."""
    try:
        return birth_datetime_utc.replace(year=birth_datetime_utc.year + age_years)
    except ValueError:
        # Birth on Feb 29, target year not a leap year.
        return birth_datetime_utc.replace(year=birth_datetime_utc.year + age_years, month=2, day=28)


def current_age_year(birth_datetime_utc: datetime, moment_utc: datetime) -> int:
    """1-indexed age-year currently running at `moment_utc` (Age 1 =
    birth to first solar return, etc.), per exact solar-return
    boundaries, not calendar-year or Jan-1-based counting."""
    if moment_utc < birth_datetime_utc:
        raise ValueError("moment_utc is before birth_datetime_utc")
    age = 0
    while solar_return_boundary(birth_datetime_utc, age + 1) <= moment_utc:
        age += 1
    return age + 1


def yearly_tara(birth_nakshatra: str, birth_datetime_utc: datetime, moment_utc: datetime) -> tuple[int, int, str]:
    """(age_year, extended_27_position, extended_27_name) currently
    running at `moment_utc`, using the full 27-position extended table
    cycling continuously (Age 1 = Janma, Age 10 = Karma, Age 28 = Janma
    again) — NOT the 9-cycle used for the Tarabala dimensions above."""
    age_year = current_age_year(birth_datetime_utc, moment_utc)
    position = ((age_year - 1) % 27) + 1
    return age_year, position, extended_27_name(position)
