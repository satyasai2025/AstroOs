"""
AstroOS — Sadhu Padhdhati Marriage Timing Engine

Ports the "Sudarshana Chakra Prism" marriage-timing method found in the
Sadhu_Padhdhati_Marriage.xlsm reference workbook to Python, as a second
timing method alongside MarriageTimingEngine's Jupiter/Saturn transit
scanner (see routers/ai_phase_e.py — both are selectable in the
Compatibility Report's Timeline tab).

Source method, as built in the workbook
----------------------------------------
For each of D1 (Rashi) and D9 (Navamsa):
  1. Compute an "Escalation Factor" (EF) — a count of "Yes" answers to ~26
     classical relationship questions asked at three levels:
       - General  (does Saturn aspect/conjoin the Sun?)
       - Physical (from Lagna: 7th/5th lords, Lagna/11th lords — mutual
         aspect, conjunction, or parivartana; placements in the 11th/1st;
         Sun in the 3rd from Lagna as a bonus-weighted "badhaka" check)
       - Astral   (the same Physical-level question set, re-run with the
         Moon standing in for the Lagna — i.e. a Chandra Lagna reframe)
  2. Compute a "Reducing Factor" (RF) — benefic support around the same
     reference points (7th/11th lords, Lagna/Moon lord).
  3. Delay = Base(birth year, gender) + (Step + (EF-1)*MF)*m - RF
     where Step/MF are gender constants and m=1.5 is a fixed multiplier.
  4. Net Delay = round-up(average(Delay_D1, Delay_D9))
  5. Central year = birth year + Net Delay; ±2 gives a 5-year window.
  6. An "Alphabet Class" (A-H) is read off a 12x12 table keyed by the D1
     and D9 Ascendant signs, then combined with a navamsa-position sum of
     the D1 and D9 Ascendant lords (mod 18) into an 18x8 "Destiny Factor"
     lookup (1-5), which selects the exact year within the 5-year window.

Automation boundary (read before trusting EF/RF as ground truth)
------------------------------------------------------------------
In the source workbook, EVERY "Yes"/"No" answer and every "which planets"
entry behind EF and RF is *typed in by hand* by the astrologer inspecting
the chart — there is no macro that detects aspects or conjunctions. This
engine automates that judgment using the same classical graha-drishti /
conjunction / parivartana primitives the Ashtakoota and Yoga engines use
elsewhere in AstroOS (see yoga_predicates.py), which is a faithful,
deterministic mechanization of what each question literally asks.

RF is a softer case: the workbook's "Benefic HP?" and "Special Benefic"
columns have no formula definition at all (they're free-form judgment
cells), so RF here is a documented, principled *approximation* — count of
natural benefics supporting the key reference points — not a 1:1 port.
Treat EF, the lookup tables, and the final arithmetic as faithful; treat
RF (and therefore the exact year, which depends on it) as an estimate in
the same spirit as the source method, not an exact reproduction of one
astrologer's manual entries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from packages.shared.constants import SIGN_LORDS

# ── Constants ────────────────────────────────────────────────────────────────

RASHIS = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]

NATURAL_BENEFICS = {"jupiter", "venus", "mercury", "moon"}

# Classical graha-drishti (full aspect) house-offsets, whole-sign, no orbs —
# every planet aspects the 7th house from itself; Mars/Jupiter/Saturn have
# additional special aspects. Rahu/Ketu use the universal 7th-only rule (no
# classically-agreed special aspects for them, same simplification used
# elsewhere in this codebase — see yoga_predicates.py's CLASSICAL_SEVEN).
ASPECT_OFFSETS: dict[str, set[int]] = {
    "sun": {7}, "moon": {7}, "mercury": {7}, "venus": {7},
    "rahu": {7}, "ketu": {7},
    "mars": {4, 7, 8},
    "jupiter": {5, 7, 9},
    "saturn": {3, 7, 10},
}

# m — fixed multiplier constant from the workbook (Sheet1!D80), not derived
# from any chart input.
DELAY_MULTIPLIER = 1.5

# Desha Kala Patra base-age table (Tables!M22:P26): [year_from, year_to,
# male_base, female_base]. The workbook only tabulates 1800-2010; birth
# years outside that range fall back to the nearest bracket.
BASE_AGE_TABLE: list[tuple[int, int, int, int]] = [
    (1800, 1900, 18, 13),
    (1900, 1930, 23, 21),
    (1930, 1970, 24, 23),
    (1970, 1990, 25, 24),
    (1990, 2010, 26, 25),
]

# Alphabet Class table (Tables!C4:N15): row = D1 Ascendant rashi (1-12),
# col = D9 Ascendant rashi (1-12) -> letter A-H, or None where the
# workbook has "X" (an undefined combination in the source method).
_AC = None
ALPHABET_CLASS_TABLE: list[list[str | None]] = [
    ["F", "E", "F", "H", "A", "A", "E", "C", "C", _AC, _AC, _AC],
    ["A", "A", "C", "E", "F", "F", _AC, _AC, _AC, "B", "F", "G"],
    ["A", "E", "B", _AC, _AC, _AC, "H", "F", "C", "C", "G", "D"],
    ["X", _AC, _AC, "F", "C", "F", "C", "B", "E", "F", "G", "D"],
    ["E", "G", "G", "D", "D", "E", "E", "E", "H", _AC, _AC, _AC],
    ["F", "F", "A", "F", "C", "C", _AC, _AC, _AC, "F", "A", "A"],
    ["E", "E", "A", _AC, _AC, _AC, "A", "F", "F", "D", "D", "A"],
    ["X", _AC, _AC, "A", "D", "A", "H", "C", "A", "A", "D", "D"],
    ["C", "A", "G", "G", "A", "C", "E", "C", "E", _AC, _AC, _AC],
    ["A", "A", "C", "C", "H", "E", _AC, _AC, _AC, "E", "E", "C"],
    ["B", "F", "B", _AC, _AC, _AC, "F", "H", "H", "F", "F", "G"],
    ["X", _AC, _AC, "F", "C", "F", "F", "C", "D", "E", "E", "C"],
]

# Destiny Factor table (Tables!C21:J38): row = (navamsa-sum mod 18), 1-18
# (0 wraps to 18, matching the workbook's cyclic MOD 18 indexing),
# col = Alphabet Class letter A-H -> value 1-5.
DESTINY_FACTOR_COLUMNS = ["A", "B", "C", "D", "E", "F", "G", "H"]
DESTINY_FACTOR_TABLE: list[list[int]] = [
    [4, 5, 4, 5, 2, 1, 3, 1],
    [5, 4, 3, 5, 3, 1, 4, 2],
    [5, 3, 2, 4, 4, 2, 5, 3],
    [4, 2, 1, 3, 5, 3, 5, 4],
    [3, 1, 1, 2, 5, 4, 4, 5],
    [2, 1, 2, 1, 4, 5, 3, 5],
    [1, 2, 3, 1, 3, 5, 2, 4],
    [1, 3, 4, 2, 2, 4, 1, 3],
    [2, 4, 5, 3, 1, 3, 1, 2],
    [3, 5, 5, 4, 1, 2, 2, 1],
    [3, 5, 5, 4, 1, 2, 2, 1],
    [2, 4, 5, 3, 1, 3, 1, 2],
    [1, 3, 4, 2, 2, 4, 1, 3],
    [1, 2, 3, 1, 3, 5, 2, 4],
    [2, 1, 2, 1, 4, 5, 3, 5],
    [3, 1, 1, 2, 5, 4, 4, 5],
    [4, 2, 1, 3, 5, 3, 5, 4],
    [5, 3, 1, 4, 4, 2, 5, 3],
]


# ── Inputs / outputs ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ChartPositions:
    """
    One chart's worth of sign positions, already whole-sign house-numbered
    relative to its own Ascendant (house 1 = Ascendant, as usual). Built
    once for D1 (from real ephemeris longitudes) and once for D9 (from
    compute_varga_sign), then fed through the same evaluation logic.
    """
    lagna_sign_index: int                    # 0-11 (Aries=0)
    planet_sign_index: dict[str, int]         # planet -> 0-11
    planet_natal_longitude: dict[str, float]  # ALWAYS the D1 longitude — used
    # for the navamsa-position lookup regardless of which chart this is,
    # matching the workbook's C88/C90 formulas (see module docstring).

    def house_of_sign(self, sign_index: int) -> int:
        return ((sign_index - self.lagna_sign_index) % 12) + 1

    def house_of_planet(self, planet: str) -> int:
        return self.house_of_sign(self.planet_sign_index[planet])

    def sign_at_house(self, house_number: int) -> int:
        return (self.lagna_sign_index + house_number - 1) % 12

    def lord_of_house(self, house_number: int) -> str:
        rashi = RASHIS[self.sign_at_house(house_number)]
        return SIGN_LORDS[rashi]


@dataclass(frozen=True)
class LevelBreakdown:
    """One Physical- or Astral-level pass's raw Yes-count, for transparency."""
    label: str
    yes_count: int
    max_count: int
    badhaka: bool  # Sun in 3rd from this level's reference point


@dataclass(frozen=True)
class ChartDelayResult:
    chart_label: str  # "D1" or "D9"
    base: int
    step: int
    escalation_factor: int
    male_female_factor: int
    reducing_factor: int
    delay: float
    levels: list[LevelBreakdown]


@dataclass(frozen=True)
class SadhuPadhdhatiResult:
    subject_name: str
    birth_year: int
    gender: str
    d1: ChartDelayResult
    d9: ChartDelayResult
    net_delay: int
    predicted_year: int
    window_start: int
    window_end: int
    alphabet_class: str | None
    destiny_factor: int | None


# ── Aspect / relationship primitives (self-contained, house-number based —
#    see module docstring on why D1 and D9 share this instead of using the
#    orb-based AspectInfo the rest of the app computes for D1 only) ────────

def _aspects(from_planet: str, from_house: int, to_house: int) -> bool:
    distance = ((to_house - from_house) % 12) + 1
    return distance in ASPECT_OFFSETS.get(from_planet, {7})


def _mutual_aspect(pos: ChartPositions, a: str, b: str) -> bool:
    ha, hb = pos.house_of_planet(a), pos.house_of_planet(b)
    return _aspects(a, ha, hb) and _aspects(b, hb, ha)


def _conjunct(pos: ChartPositions, a: str, b: str) -> bool:
    return pos.house_of_planet(a) == pos.house_of_planet(b)


def _exchange(pos: ChartPositions, house_a: int, house_b: int) -> bool:
    lord_a, lord_b = pos.lord_of_house(house_a), pos.lord_of_house(house_b)
    return pos.house_of_planet(lord_a) == house_b and pos.house_of_planet(lord_b) == house_a


# ── EF: the ~13-question relational block, run once for Physical (ref =
#    Lagna) and once for Astral (ref = Moon, via rebasing) ──────────────────

def _rebase_to_moon(pos: ChartPositions) -> ChartPositions:
    moon_sign = pos.planet_sign_index["moon"]
    return ChartPositions(
        lagna_sign_index=moon_sign,
        planet_sign_index=pos.planet_sign_index,
        planet_natal_longitude=pos.planet_natal_longitude,
    )


def _evaluate_level(pos: ChartPositions, label: str) -> LevelBreakdown:
    """The 12-question Physical/Astral block (rows 46-57 / 59-70 in the
    workbook) plus its badhaka bonus row (58 / 71), evaluated against
    `pos` — the caller passes either the chart as-is (Physical, ref=Lagna)
    or rebased-to-Moon (Astral, ref=Moon's sign standing in for house 1)."""
    lord1 = pos.lord_of_house(1)   # Lagna-lord (Physical) / Moon-lord (Astral)
    lord5 = pos.lord_of_house(5)
    lord7 = pos.lord_of_house(7)   # HPL
    lord11 = pos.lord_of_house(11)

    yes = 0
    # 1-2: Saturn's relation to HP (7th) / HPL (7th lord)
    yes += int(_aspects("saturn", pos.house_of_planet("saturn"), 7) or _aspects("saturn", pos.house_of_planet("saturn"), pos.house_of_planet(lord7)))
    yes += int(pos.house_of_planet("saturn") == 7 or _conjunct(pos, "saturn", lord7))
    # 3-5: 7th lord & 5th lord relationship
    yes += int(_mutual_aspect(pos, lord7, lord5))
    yes += int(_conjunct(pos, lord7, lord5))
    yes += int(_exchange(pos, 7, 5))
    # 6-8: reference-lord (Lagna/Moon lord) & 11th lord relationship
    yes += int(_mutual_aspect(pos, lord1, lord11))
    yes += int(_conjunct(pos, lord1, lord11))
    yes += int(_exchange(pos, 1, 11))
    # 9: reference-lord placed in 11th, without exchange already counted above
    exch_1_11 = _exchange(pos, 1, 11)
    yes += int(pos.house_of_planet(lord1) == 11 and not exch_1_11)
    # 10: Saturn in the 11th
    yes += int(pos.house_of_planet("saturn") == 11)
    # 11: 11th lord in its own house
    yes += int(pos.house_of_planet(lord11) == 11)
    # 12: 11th lord in the reference house (1st), without exchange
    yes += int(pos.house_of_planet(lord11) == 1 and not exch_1_11)

    badhaka = pos.house_of_planet("sun") == 3
    return LevelBreakdown(label=label, yes_count=yes, max_count=12, badhaka=badhaka)


def _general_level_yes(pos: ChartPositions) -> int:
    """Rows 42+45: does Saturn aspect the Sun / is Saturn with the Sun."""
    yes = 0
    yes += int(_aspects("saturn", pos.house_of_planet("saturn"), pos.house_of_planet("sun")))
    yes += int(_conjunct(pos, "saturn", "sun"))
    return yes


def _escalation_factor(pos: ChartPositions) -> tuple[int, list[LevelBreakdown]]:
    physical = _evaluate_level(pos, "Physical (from Lagna)")
    astral = _evaluate_level(_rebase_to_moon(pos), "Astral (from Moon)")
    general = _general_level_yes(pos)

    ef = (
        general + physical.yes_count + (3 if physical.badhaka else 0)
        + astral.yes_count + (3 if astral.badhaka else 0)
    )
    return ef, [physical, astral]


# ── RF: documented approximation of the workbook's manually-judged
#    "Benefic HP" / "Special Benefic" columns (see module docstring) ────────

def _reducing_factor_for_level(pos: ChartPositions) -> int:
    lord1 = pos.lord_of_house(1)
    lord7 = pos.lord_of_house(7)
    lord11 = pos.lord_of_house(11)
    key_planets = {lord1, lord7, lord11, "saturn"}

    benefic_support = 0
    for b in NATURAL_BENEFICS:
        if b in key_planets:
            continue
        supports = any(
            _conjunct(pos, b, k) or _aspects(b, pos.house_of_planet(b), pos.house_of_planet(k))
            for k in key_planets
        )
        if supports:
            benefic_support += 1

    benefic_hp = 1 if SIGN_LORDS[RASHIS[pos.sign_at_house(7)]] in NATURAL_BENEFICS else 0

    special_benefic = sum(
        1 for b in NATURAL_BENEFICS
        if pos.house_of_planet(b) in {1, 5, 7, 9, 11}
    )

    return benefic_support + benefic_hp + special_benefic


def _reducing_factor(pos: ChartPositions) -> int:
    physical_rf = _reducing_factor_for_level(pos)
    astral_rf = _reducing_factor_for_level(_rebase_to_moon(pos))
    return physical_rf + astral_rf


# ── Base age table / navamsa lookups ────────────────────────────────────────

def get_base_age(birth_year: int, gender: str) -> int:
    for year_from, year_to, male_base, female_base in BASE_AGE_TABLE:
        if year_from <= birth_year <= year_to:
            return male_base if gender == "male" else female_base
    # Outside the tabulated range — fall back to the nearest bracket rather
    # than raising, since AstroOS accepts a much wider date range than the
    # source workbook's 1800-2010 table.
    bracket = BASE_AGE_TABLE[0] if birth_year < BASE_AGE_TABLE[0][0] else BASE_AGE_TABLE[-1]
    return bracket[2] if gender == "male" else bracket[3]


def _navamsa_number(longitude: float) -> int:
    """Which of the 108 navamsa segments (3°20' each) a longitude falls
    in, 1-indexed, round-up — port of Sheet1!C88/C90's
    ROUNDUP(degree/(30/9))."""
    import math
    return max(1, math.ceil((longitude % 360.0) / (30.0 / 9.0)))


# ── Per-chart delay computation ─────────────────────────────────────────────

def _compute_chart_delay(pos: ChartPositions, chart_label: str, gender: str, base: int) -> ChartDelayResult:
    ef, levels = _escalation_factor(pos)
    rf = _reducing_factor(pos)
    step = 5 if gender == "male" else 4
    mf = 4 if gender == "male" else 3
    delay = base + (step + (ef - 1) * mf) * DELAY_MULTIPLIER - rf
    return ChartDelayResult(
        chart_label=chart_label, base=base, step=step,
        escalation_factor=ef, male_female_factor=mf, reducing_factor=rf,
        delay=delay, levels=levels,
    )


# ── Public entry point ──────────────────────────────────────────────────────

class SadhuPadhdhatiEngine:
    """
    Computes a predicted marriage year for one person, given D1 and D9
    Ascendant + planet sign positions. Callers (the API router) build the
    D9 ChartPositions using divisional_engine.compute_varga_sign("D9", ...)
    fed with each planet's D1 sidereal longitude — see
    routers/ai_phase_e.py's sadhu_padhdhati_timing endpoint for the wiring.
    """

    @staticmethod
    def analyze(
        subject_name: str,
        birth_date: date,
        gender: str,
        d1: ChartPositions,
        d9: ChartPositions,
    ) -> SadhuPadhdhatiResult:
        gender = gender.lower()
        if gender not in ("male", "female"):
            raise ValueError("gender must be 'male' or 'female'")

        base = get_base_age(birth_date.year, gender)
        d1_result = _compute_chart_delay(d1, "D1", gender, base)
        d9_result = _compute_chart_delay(d9, "D9", gender, base)

        import math
        net_delay = math.ceil(round((d1_result.delay + d9_result.delay) / 2, 6))
        central_year = birth_date.year + net_delay
        window_start = central_year - 2
        window_end = central_year + 2

        # Alphabet Class: D1 Ascendant rashi x D9 Ascendant rashi -> letter
        alphabet = ALPHABET_CLASS_TABLE[d1.lagna_sign_index][d9.lagna_sign_index]

        # Navamsa-position sum of the D1 Asc lord and the D9 Asc lord (both
        # read from their D1/natal longitude, per the workbook formula).
        d1_asc_lord = SIGN_LORDS[RASHIS[d1.lagna_sign_index]]
        d9_asc_lord = SIGN_LORDS[RASHIS[d9.lagna_sign_index]]
        nav_sum = (
            _navamsa_number(d1.planet_natal_longitude[d1_asc_lord])
            + _navamsa_number(d1.planet_natal_longitude[d9_asc_lord])
        )
        mod18 = nav_sum % 18
        row_index = 17 if mod18 == 0 else mod18 - 1  # 0-indexed into the 18-row table

        destiny_factor: int | None = None
        predicted_year = central_year
        if alphabet is not None and alphabet in DESTINY_FACTOR_COLUMNS:
            col_index = DESTINY_FACTOR_COLUMNS.index(alphabet)
            destiny_factor = DESTINY_FACTOR_TABLE[row_index][col_index]
            predicted_year = window_start + destiny_factor - 1

        return SadhuPadhdhatiResult(
            subject_name=subject_name,
            birth_year=birth_date.year,
            gender=gender,
            d1=d1_result,
            d9=d9_result,
            net_delay=net_delay,
            predicted_year=predicted_year,
            window_start=window_start,
            window_end=window_end,
            alphabet_class=alphabet,
            destiny_factor=destiny_factor,
        )
