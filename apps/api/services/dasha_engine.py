"""
AstroOS — Dasha Engine (Task 6)

Computes six Dasha systems from a birth moment:

  1. Vimshottari  — 120-year nakshatra-based cycle (Parashara, BPHS Ch.46)
  2. Yogini       — 36-year nakshatra-based cycle  (BPHS Ch.47)
  3. Ashtottari   — 108-year nakshatra-based cycle (BPHS Ch.46)
  4. Kalachakra   — 100-year navamsha-sign cycle   (BPHS Ch.47)
  5. Chara        — Jaimini sign-based cycle        (Jaimini Sutras Ch.2)
  6. Narayana     — Jaimini sign-based D1 cycle, own seed/progression/
                    duration rules (Jaimini Sutras Ch.2) — NOT the same
                    rule as Chara, and computed on D1 (Rasi), not D9;
                    see compute_narayana()'s own docstring for the fix
                    history of a previous, incorrect implementation.

All six systems return a DashaTree with nested DashaPeriods up to
the requested depth (1=Mahadasha … 5=Prana).

Sub-period formula (universal for nakshatra-based systems)
----------------------------------------------------------
  sub_days(L, parent) = parent_days × L_years / total_cycle_years

  Periods are date-anchored using the proportional offset from the
  parent period start to avoid cumulative rounding drift.
"""

from __future__ import annotations

import hashlib
import math
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Sequence


from apps.api.domain.dasha import DashaPeriod, DashaTree
from apps.api.services.divisional_engine import compute_varga_sign
from apps.api.services.ephemeris_wrapper import (
    EphemerisWrapper,
    longitude_to_nakshatra,
    longitude_to_rashi,
)
from packages.shared.constants import (
    ASHTOTTARI_DASHA_YEARS,
    ASHTOTTARI_NAKSHATRA_LORDS,
    ASHTOTTARI_SEQUENCE,
    ASHTOTTARI_TOTAL_YEARS,
    DAYS_PER_JULIAN_YEAR,
    DEGREES_PER_NAKSHATRA,
    JAIMINI_ALT_LORDS,
    KALACHAKRA_APASAVYA_SIGNS,
    KALACHAKRA_SAVYA_SIGNS,
    KALACHAKRA_SIGN_YEARS,
    KALACHAKRA_TOTAL_YEARS,
    SIGN_LORDS,
    VIMSHOTTARI_DASHA_YEARS,
    VIMSHOTTARI_NAKSHATRA_LORDS,
    VIMSHOTTARI_SEQUENCE,
    VIMSHOTTARI_TOTAL_YEARS,
    YOGINI_DASHA_YEARS,
    YOGINI_GRAHA,
    YOGINI_NAKSHATRA_LORDS,
    YOGINI_SEQUENCE,
    YOGINI_TOTAL_YEARS,
)

from packages.shared.degrees import normalize_degrees
from packages.shared.enums import Rashi

_RASHI_LIST = [r.value for r in Rashi]

_LEVEL_NAMES = {1: "Mahadasha", 2: "Antardasha", 3: "Pratyantar", 4: "Sookshma", 5: "Prana"}

MAX_SUPPORTED_DEPTH = 5


# ── Generic period-tree builder ───────────────────────────────────────────────


def _build_nakshatra_periods(
    start_lord: str,
    sequence: list[str],
    period_years: dict[str, int | float],
    total_years: int | float,
    start_date: date | datetime,
    end_date: date | datetime,
    level: int,
    max_depth: int,
) -> tuple[DashaPeriod, ...]:
    """
    Recursively build a dasha sub-period tree for nakshatra-based systems.

    All boundaries are anchored from start_date using proportional offsets to
    prevent cumulative rounding drift, carrying exact microsecond precision for
    levels 4 (Sookshma) and 5 (Prana) when datetime is supplied.
    """
    if level > max_depth:
        return ()

    is_dt = isinstance(start_date, datetime)
    if is_dt:
        parent_seconds = (end_date - start_date).total_seconds()
        if parent_seconds <= 0:
            return ()
    else:
        parent_days = (end_date - start_date).days
        if parent_days <= 0:
            return ()

    n = len(sequence)
    start_idx = sequence.index(start_lord)
    periods: list[DashaPeriod] = []
    elapsed_ratio = 0.0

    for i in range(n):
        lord = sequence[(start_idx + i) % n]
        lord_years = period_years[lord]
        next_ratio = elapsed_ratio + lord_years / total_years

        if is_dt:
            p_start = start_date + timedelta(seconds=elapsed_ratio * parent_seconds)
            p_end = end_date if i == n - 1 else start_date + timedelta(seconds=next_ratio * parent_seconds)
            p_days = max((p_end - p_start).total_seconds() / 86400.0, 0.0)
        else:
            p_start = start_date + timedelta(days=round(elapsed_ratio * parent_days))
            p_end = end_date if i == n - 1 else start_date + timedelta(days=round(next_ratio * parent_days))
            p_days = max((p_end - p_start).days, 0)


        sub = _build_nakshatra_periods(
            lord, sequence, period_years, total_years,
            p_start, p_end, level + 1, max_depth,
        )
        periods.append(DashaPeriod(
            lord=lord,
            start_date=p_start,
            end_date=p_end,
            duration_days=p_days,
            level=level,
            sub_periods=sub,
        ))
        elapsed_ratio = next_ratio

    return tuple(periods)


def _build_sign_periods(
    start_sign: str,
    sign_sequence: list[str],
    sign_years: dict[str, int | float],
    total_years: int | float,
    start_date: date | datetime,
    end_date: date | datetime,
    level: int,
    max_depth: int,
) -> tuple[DashaPeriod, ...]:
    """
    Recursively build a dasha sub-period tree for sign-based systems
    (Kalachakra, Chara, Narayana).
    """
    if level > max_depth:
        return ()

    is_dt = isinstance(start_date, datetime)
    if is_dt:
        parent_seconds = (end_date - start_date).total_seconds()
        if parent_seconds <= 0:
            return ()
    else:
        parent_days = (end_date - start_date).days
        if parent_days <= 0:
            return ()

    n = len(sign_sequence)
    start_idx = sign_sequence.index(start_sign)
    periods: list[DashaPeriod] = []
    elapsed_ratio = 0.0

    for i in range(n):
        sign = sign_sequence[(start_idx + i) % n]
        sign_yr = sign_years[sign]
        next_ratio = elapsed_ratio + sign_yr / total_years

        if is_dt:
            p_start = start_date + timedelta(seconds=elapsed_ratio * parent_seconds)
            p_end = end_date if i == n - 1 else start_date + timedelta(seconds=next_ratio * parent_seconds)
            p_days = max((p_end - p_start).total_seconds() / 86400.0, 0.0)
        else:
            p_start = start_date + timedelta(days=round(elapsed_ratio * parent_days))
            p_end = end_date if i == n - 1 else start_date + timedelta(days=round(next_ratio * parent_days))
            p_days = max((p_end - p_start).days, 0)


        sub = _build_sign_periods(
            sign, sign_sequence, sign_years, total_years,
            p_start, p_end, level + 1, max_depth,
        )
        periods.append(DashaPeriod(
            lord=sign,
            start_date=p_start,
            end_date=p_end,
            duration_days=p_days,
            level=level,
            sub_periods=sub,
        ))
        elapsed_ratio = next_ratio

    return tuple(periods)



# ── Nakshatra-based balance calculation ───────────────────────────────────────


def _nakshatra_balance(
    moon_sidereal_lon: float,
    lord_sequence: list[str],
    period_years: dict[str, int | float],
    total_years: int | float,
    birth_dt: date | datetime,
) -> tuple[str, float, date | datetime]:
    """
    Compute the starting lord, remaining balance (years), and the date/datetime on
    which the first Mahadasha began (before birth for partial periods).

    Returns:
        (first_lord, balance_years, first_maha_start)
    """
    lon = normalize_degrees(moon_sidereal_lon)
    nak_index_float = lon / DEGREES_PER_NAKSHATRA
    if math.isclose(nak_index_float, round(nak_index_float), abs_tol=1e-9, rel_tol=0.0):
        nakshatra_idx = int(round(nak_index_float)) % 27
        deg_in_nak = 0.0
    else:
        nakshatra_idx = int(nak_index_float)
        deg_in_nak = lon - nakshatra_idx * DEGREES_PER_NAKSHATRA

    nakshatra_idx = min(nakshatra_idx, 26)  # clamp edge case
    fraction_elapsed = deg_in_nak / DEGREES_PER_NAKSHATRA

    first_lord = lord_sequence[nakshatra_idx % len(lord_sequence)]
    first_lord_years = period_years[first_lord]

    # Balance (remaining) years at birth
    balance_years = (1.0 - fraction_elapsed) * first_lord_years

    # Time already elapsed in the first Mahadasha before birth
    if isinstance(birth_dt, datetime):
        elapsed_seconds = fraction_elapsed * first_lord_years * DAYS_PER_JULIAN_YEAR * 86400.0
        first_start = birth_dt - timedelta(seconds=elapsed_seconds)
    else:
        elapsed_days = fraction_elapsed * first_lord_years * DAYS_PER_JULIAN_YEAR
        first_start = birth_dt - timedelta(days=round(elapsed_days))

    return first_lord, balance_years, first_start



# ── Narayana Dasha tables and helpers ──────────────────────────────────────────
#
# Narayana Dasha is NOT "Chara Dasha applied to D9" — that was this
# module's previous, incorrect assumption (confirmed wrong via a
# PyJHora jhora.horoscope.dhasa.raasi.narayana cross-check). It is a
# genuinely different classical system, computed on the D1 (Rasi)
# chart by default (not D9), with its own seed-sign rule, its own
# fixed 12-sign progression table (with Ketu/Saturn exceptions when
# either occupies the seed sign), its own duration formula, and a
# two-cycle structure (each of the 12 progression signs runs once for
# its computed duration, then again for the 12-minus-that complement),
# totaling a fixed 144 years (12 signs x 12 years max, matching
# Chara's classical companion system). Tables and formulas below are
# ported directly from PyJHora's const.py / horoscope/dhasa/raasi/
# narayana.py (jhora.horoscope.dhasa.raasi.narayana), not re-derived.

# 12 progression tables (rows = seed sign 0=Aries..11=Pisces), each row
# giving the 12-sign dasha order starting from that seed.
NARAYANA_PROGRESSION_NORMAL: tuple[tuple[int, ...], ...] = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11),
    (1, 8, 3, 10, 5, 0, 7, 2, 9, 4, 11, 6),
    (2, 10, 6, 5, 1, 9, 8, 4, 0, 11, 7, 3),
    (3, 2, 1, 0, 11, 10, 9, 8, 7, 6, 5, 4),
    (4, 9, 2, 7, 0, 5, 10, 3, 8, 1, 6, 11),
    (5, 9, 1, 2, 6, 10, 11, 3, 7, 8, 0, 4),
    (6, 7, 8, 9, 10, 11, 0, 1, 2, 3, 4, 5),
    (7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5, 0),
    (8, 4, 0, 11, 7, 3, 2, 10, 6, 5, 1, 9),
    (9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 11, 10),
    (10, 3, 8, 1, 6, 11, 4, 9, 2, 7, 0, 5),
    (11, 3, 7, 8, 0, 4, 5, 9, 1, 2, 6, 10),
)
NARAYANA_PROGRESSION_SATURN_EXCEPTION: tuple[tuple[int, ...], ...] = tuple(
    tuple((seed + i) % 12 for i in range(12)) for seed in range(12)
)
NARAYANA_PROGRESSION_KETU_EXCEPTION: tuple[tuple[int, ...], ...] = (
    (0, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1),
    (1, 6, 11, 4, 9, 2, 7, 0, 5, 10, 3, 8),
    (2, 6, 10, 11, 3, 7, 8, 0, 4, 5, 9, 1),
    (3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1, 2),
    (4, 11, 6, 1, 8, 3, 10, 5, 0, 7, 2, 9),
    (5, 1, 9, 8, 4, 0, 11, 7, 3, 2, 10, 6),
    (6, 5, 4, 3, 2, 1, 0, 11, 10, 9, 8, 7),
    (7, 0, 5, 10, 3, 8, 1, 6, 11, 4, 9, 2),
    (8, 0, 4, 5, 9, 1, 2, 6, 10, 11, 3, 7),
    (9, 10, 11, 0, 1, 2, 3, 4, 5, 6, 7, 8),
    (10, 5, 0, 7, 2, 9, 4, 11, 6, 1, 8, 3),
    (11, 7, 3, 2, 10, 6, 5, 1, 9, 8, 4, 0),
)

# "Even-footed" signs (a classical classification distinct from plain
# odd/even sign parity) — Cancer, Leo, Virgo, Capricorn, Aquarius, Pisces.
_EVEN_FOOTED_SIGNS = frozenset({3, 4, 5, 9, 10, 11})
_ODD_SIGNS_0IDX = frozenset({0, 2, 4, 6, 8, 10})
_DUAL_SIGNS_0IDX = frozenset({2, 5, 8, 11})
_FIXED_SIGNS_0IDX = frozenset({1, 4, 7, 10})


def _count_rasis_inclusive(from_idx: int, to_idx: int) -> int:
    """Inclusive sign count from from_idx to to_idx, wrapping forward through the zodiac."""
    return (to_idx - from_idx) % 12 + 1


def _narayana_dhasa_duration(planets_by_sign: dict[int, list[str]], sign_idx: int) -> float:
    """
    Narayana's own duration rule — NOT the same formula as Chara Dasha.
    Ported from PyJHora's narayana._dhasa_duration(): the count runs
    from the sign to its lord's placement (or the reverse) depending on
    whether the sign is "even-footed", minus one, defaulting to 12 if
    that's <= 0; exalted lord adds a year, debilitated lord subtracts one.
    """
    lord = SIGN_LORDS[_RASHI_LIST[sign_idx]]
    lord_sign_idx = _lord_sign_index(planets_by_sign, lord)

    if sign_idx in _EVEN_FOOTED_SIGNS:
        count = _count_rasis_inclusive(lord_sign_idx, sign_idx)
    else:
        count = _count_rasis_inclusive(sign_idx, lord_sign_idx)
    duration = count - 1
    if duration <= 0:
        duration = 12

    dignity = _lord_dignity_at(planets_by_sign, lord, lord_sign_idx)
    if dignity == "exalted":
        duration += 1
    elif dignity == "debilitated":
        duration -= 1
    return float(duration)


def _lord_sign_index(planets_by_sign: dict[int, list[tuple[str, str, float]]], lord: str) -> int:
    for idx, occupants in planets_by_sign.items():
        for planet, _dignity, _deg in occupants:
            if planet == lord:
                return idx
    return _RASHI_LIST.index(SIGN_LORDS_INVERSE_DEFAULT.get(lord, "aries"))


def _lord_dignity_at(planets_by_sign: dict[int, list[tuple[str, str, float]]], lord: str, sign_idx: int) -> str | None:
    for planet, dignity, _deg in planets_by_sign.get(sign_idx, []):
        if planet == lord:
            return dignity
    return None


# Fallback only reached if a lord planet is entirely absent from the
# chart data (should not happen for the 7 classical grahas) — maps a
# lord back to a sign it classically rules, so duration math still
# produces a sane (if not chart-specific) result rather than crashing.
SIGN_LORDS_INVERSE_DEFAULT: dict[str, str] = {v: k for k, v in SIGN_LORDS.items()}


def _stronger_rasi(
    planets_by_sign: dict[int, list[tuple[str, str, float]]], sign_idx1: int, sign_idx2: int,
) -> int:
    """
    Classical "stronger rasi" comparison — Rules 1, 3, 4, 5 of PyJHora's
    house.stronger_rasi() cascade, plus its Rule-6 fallback (higher
    longitude-within-sign of the two candidate lords). Rule 2 (benefic
    conjunction/aspect count onto the rasi) is NOT implemented — it
    needs a "graha drishti onto an arbitrary rashi" primitive this
    codebase's AspectEngine doesn't currently expose (only planet-to-
    planet aspects). Disclosed simplification, not a silent gap: on a
    Rule-1/3/4/5 tie, this falls through one rule earlier than PyJHora
    would (skipping straight from Rule 4 to Rule 5, i.e. never applying
    Rule 2's tie-break) before reaching the same Rule-6 fallback.
    """
    count1 = len(planets_by_sign.get(sign_idx1, []))
    count2 = len(planets_by_sign.get(sign_idx2, []))
    if count1 != count2:
        return sign_idx1 if count1 > count2 else sign_idx2

    exalted1 = sum(1 for _, d, _deg in planets_by_sign.get(sign_idx1, []) if d == "exalted")
    exalted2 = sum(1 for _, d, _deg in planets_by_sign.get(sign_idx2, []) if d == "exalted")
    if (exalted1 > 0) != (exalted2 > 0):
        return sign_idx1 if exalted1 > 0 else sign_idx2

    lord1, lord2 = SIGN_LORDS[_RASHI_LIST[sign_idx1]], SIGN_LORDS[_RASHI_LIST[sign_idx2]]
    lord1_sign = _lord_sign_index(planets_by_sign, lord1)
    lord2_sign = _lord_sign_index(planets_by_sign, lord2)
    oddity1 = (sign_idx1 in _ODD_SIGNS_0IDX) != (lord1_sign in _ODD_SIGNS_0IDX)
    oddity2 = (sign_idx2 in _ODD_SIGNS_0IDX) != (lord2_sign in _ODD_SIGNS_0IDX)
    if oddity1 != oddity2:
        return sign_idx1 if oddity1 else sign_idx2

    def _modality_rank(idx: int) -> int:
        if idx in _DUAL_SIGNS_0IDX:
            return 3
        if idx in _FIXED_SIGNS_0IDX:
            return 2
        return 1

    m1, m2 = _modality_rank(sign_idx1), _modality_rank(sign_idx2)
    if m1 != m2:
        return sign_idx1 if m1 > m2 else sign_idx2

    # Rule-6 fallback: higher degree-within-sign of the two lords.
    lord1_deg = _lord_degree_in_sign(planets_by_sign, lord1)
    lord2_deg = _lord_degree_in_sign(planets_by_sign, lord2)
    return sign_idx1 if lord1_deg >= lord2_deg else sign_idx2


def _lord_degree_in_sign(planets_by_sign: dict[int, list[tuple[str, str, float]]], lord: str) -> float:
    for occupants in planets_by_sign.values():
        for entry in occupants:
            if entry[0] == lord:
                return entry[2] if len(entry) > 2 else 0.0
    return 0.0


def _narayana_seed_sign(planets_by_sign: dict[int, list[tuple[str, str, float]]], asc_sign_idx: int) -> int:
    seventh_idx = (asc_sign_idx + 6) % 12
    return _stronger_rasi(planets_by_sign, asc_sign_idx, seventh_idx)


def _narayana_progression(planets_by_sign: dict[int, list[tuple[str, str, float]]], seed_idx: int) -> tuple[int, ...]:
    # Rahu/Ketu are always present in a real chart (mathematical points,
    # never "absent"), so no presence-check is needed before locating them.
    ketu_sign = _lord_sign_index(planets_by_sign, "ketu")
    saturn_sign = _lord_sign_index(planets_by_sign, "saturn")
    if ketu_sign == seed_idx:
        return NARAYANA_PROGRESSION_KETU_EXCEPTION[seed_idx]
    if saturn_sign == seed_idx:
        return NARAYANA_PROGRESSION_SATURN_EXCEPTION[seed_idx]
    return NARAYANA_PROGRESSION_NORMAL[seed_idx]


def _narayana_antardhasa_order(planets_by_sign: dict[int, list[tuple[str, str, float]]], dhasa_rasi_idx: int) -> tuple[int, ...]:
    """
    Antardasha order within one Narayana Mahadasha sign — its own seed
    (stronger of the dasha-lord's sign and the 7th-lord's sign) and its
    own direction rule (odd seed -> forward; Saturn in the seed forces
    forward; Ketu in the MAHADASHA sign flips the direction). Ported
    from PyJHora's narayana._narayana_antardhasa().
    """
    dasha_lord = SIGN_LORDS[_RASHI_LIST[dhasa_rasi_idx]]
    lord_sign = _lord_sign_index(planets_by_sign, dasha_lord)
    seventh_lord = SIGN_LORDS[_RASHI_LIST[(dhasa_rasi_idx + 6) % 12]]
    seventh_lord_sign = _lord_sign_index(planets_by_sign, seventh_lord)
    seed = _stronger_rasi(planets_by_sign, lord_sign, seventh_lord_sign)

    direction = 1 if seed in _ODD_SIGNS_0IDX else -1
    saturn_sign = _lord_sign_index(planets_by_sign, "saturn")
    if saturn_sign == seed:
        direction = 1
    ketu_sign = _lord_sign_index(planets_by_sign, "ketu")
    if ketu_sign == dhasa_rasi_idx:
        direction *= -1

    return tuple((seed + direction * i) % 12 for i in range(12))


# ── Jaimini helpers ───────────────────────────────────────────────────────────


def _jaimini_sign_duration(sign: str, lord_sign: str, use_alternate: bool = False) -> int:
    """
    Chara / Narayana sign duration by Neelakantha's rule:

    Count from `sign` to `lord_sign` — direction fixed by `sign`'s own
    parity (odd/male sign -> count forward; even/female sign -> count
    backward), the SAME parity rule already used by
    _jaimini_sign_sequence() for the dasha's own sign-progression
    direction. If the lord is in the same sign: 12 years.

    REPLACES an earlier "whichever direction is numerically shorter"
    implementation — confirmed wrong via cross-check against PyJHora's
    jhora.horoscope.dhasa.raasi.chara/narayana modules (_dhasa_duration_
    knrao_method / _pvnrao_method / _mindsutra, all of which fix
    direction by sign parity, never by minimality). Example divergence:
    Aries (odd) with lord in Scorpio — correct (forward) count is 7
    years; the old "shorter of the two" logic picked backward (5 years)
    instead, since 5 < 7.
    """
    from_idx = _RASHI_LIST.index(sign)
    to_idx = _RASHI_LIST.index(lord_sign)

    is_odd = (from_idx % 2 == 0)  # 0-indexed Aries=0 -> odd in astro numbering
    count = (to_idx - from_idx) % 12 if is_odd else (from_idx - to_idx) % 12

    return 12 if count == 0 else count


def _jaimini_sign_years(sign: str, planet_signs: dict[str, str]) -> int:
    """
    Return the Chara Dasha duration for `sign` given planet D1 sign placements.
    Uses the shorter count between the primary lord and Jaimini alternate lord
    (where applicable: Scorpio → min(Mars, Ketu), Aquarius → min(Saturn, Rahu)).
    """
    primary_lord = SIGN_LORDS[sign]
    primary_lord_sign = planet_signs.get(primary_lord, "aries")
    primary_count = _jaimini_sign_duration(sign, primary_lord_sign)

    if sign in JAIMINI_ALT_LORDS:
        alt_lord = JAIMINI_ALT_LORDS[sign]
        alt_lord_sign = planet_signs.get(alt_lord, "aries")
        alt_count = _jaimini_sign_duration(sign, alt_lord_sign)
        return min(primary_count, alt_count)

    return primary_count


def _jaimini_sign_sequence(lagna_rashi: str) -> list[str]:
    """
    Chara / Narayana dasha sign sequence starting from the Lagna sign.
    Odd signs (Aries, Gemini, Leo, Libra, Sagittarius, Aquarius): forward.
    Even signs (Taurus, Cancer, Virgo, Scorpio, Capricorn, Pisces): backward.
    """
    lagna_idx = _RASHI_LIST.index(lagna_rashi)
    is_odd = (lagna_idx % 2 == 0)  # 0-indexed Aries=0 → odd in astro
    if is_odd:
        ordered = _RASHI_LIST[lagna_idx:] + _RASHI_LIST[:lagna_idx]
    else:
        all_reversed = list(reversed(_RASHI_LIST))
        rev_idx = all_reversed.index(lagna_rashi)
        ordered = all_reversed[rev_idx:] + all_reversed[:rev_idx]
    return ordered


# ── Dasha Engine ──────────────────────────────────────────────────────────────


class DashaEngine:
    """
    Computes all six Vedic dasha systems from a birth moment.

    All methods accept the same positional parameters and return a DashaTree.
    """

    def __init__(
        self,
        ephemeris_wrapper: EphemerisWrapper,
        birth_chart_repo=None,
        dasha_repo=None,
    ) -> None:
        self._wrapper = ephemeris_wrapper
        # Optional — only required for persist_tree(). Default None keeps
        # the existing single-arg construction working for callers/tests
        # that don't need persistence.
        self._birth_chart_repo = birth_chart_repo
        self._dasha_repo = dasha_repo

    # ── Public compute methods ─────────────────────────────────────────────────

    def compute_vimshottari(
        self,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
        house_system: str = "W",
        max_depth: int = 3,
    ) -> DashaTree:
        """
        Vimshottari Dasha — 120-year cycle based on Moon's nakshatra.

        Sub-period ordering within any period: starts from that period's lord
        and cycles through all 9 lords in the canonical sequence.
        """
        if birth_datetime_utc.tzinfo is None:
            raise ValueError("birth_datetime_utc must be timezone-aware (UTC)")

        max_depth = min(max(max_depth, 1), MAX_SUPPORTED_DEPTH)
        result = self._wrapper.calculate(
            dt=birth_datetime_utc, latitude=latitude, longitude=longitude, ayanamsa=ayanamsa, house_system=house_system
        )
        moon_sid = self._moon_sidereal(result)
        nak_info = longitude_to_nakshatra(moon_sid)
        birth_dt_date = birth_datetime_utc.date()

        first_lord, balance, first_start = _nakshatra_balance(
            moon_sid, VIMSHOTTARI_SEQUENCE, VIMSHOTTARI_DASHA_YEARS,
            VIMSHOTTARI_TOTAL_YEARS, birth_datetime_utc,
        )

        mahadashas = self._build_full_cycle(
            first_lord, first_start,
            VIMSHOTTARI_SEQUENCE, VIMSHOTTARI_DASHA_YEARS,
            VIMSHOTTARI_TOTAL_YEARS, max_depth,
        )

        # Strengthened content_hash committing to the exact computed tree boundaries
        tree_sig = ";".join(
            f"{m.lord}:{m.start_datetime_utc.isoformat()}:{m.end_datetime_utc.isoformat()}"
            for m in mahadashas
        )
        canon_str = f"vimshottari|{birth_datetime_utc.isoformat()}|{first_lord}|{balance:.6f}|{tree_sig}"
        c_hash = hashlib.sha256(canon_str.encode("utf-8")).hexdigest()

        return DashaTree(
            system="vimshottari",
            birth_date=birth_dt_date,
            trigger_planet=first_lord,
            trigger_nakshatra=nak_info.nakshatra,
            trigger_nakshatra_number=nak_info.nakshatra_number,
            mahadashas=mahadashas,
            max_depth=max_depth,
            total_cycle_years=VIMSHOTTARI_TOTAL_YEARS,
            balance_at_birth=balance,
            moon_longitude_at_trigger=moon_sid,
            ayanamsa_used=result.ayanamsa_value,
            birth_datetime_utc=birth_datetime_utc,
            year_convention="365.25_julian",
            content_hash=c_hash,
        )




    def compute_yogini(
        self,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
        house_system: str = "W",
        max_depth: int = 3,
    ) -> DashaTree:
        """
        Yogini Dasha — 36-year cycle based on Moon's nakshatra.
        Sub-period lord = the Graha ruling the Yogini (e.g. Siddha → Venus).
        """
        max_depth = min(max(max_depth, 1), MAX_SUPPORTED_DEPTH)
        result = self._wrapper.calculate(
            dt=birth_datetime_utc, latitude=latitude, longitude=longitude, ayanamsa=ayanamsa
        )
        moon_sid = self._moon_sidereal(result)
        nak_info = longitude_to_nakshatra(moon_sid)
        birth_dt_date = birth_datetime_utc.date() if hasattr(birth_datetime_utc, 'date') else birth_datetime_utc

        first_yogini, _balance, first_start = _nakshatra_balance(
            moon_sid, YOGINI_SEQUENCE, YOGINI_DASHA_YEARS,
            YOGINI_TOTAL_YEARS, birth_dt_date,
        )

        mahadashas = self._build_full_cycle(
            first_yogini, first_start,
            YOGINI_SEQUENCE, YOGINI_DASHA_YEARS,
            YOGINI_TOTAL_YEARS, max_depth,
        )

        return DashaTree(
            system="yogini",
            birth_date=birth_dt_date,
            trigger_planet=YOGINI_GRAHA[first_yogini],
            trigger_nakshatra=nak_info.nakshatra,
            trigger_nakshatra_number=nak_info.nakshatra_number,
            mahadashas=mahadashas,
            max_depth=max_depth,
            total_cycle_years=YOGINI_TOTAL_YEARS,
        )

    def compute_ashtottari(
        self,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
        house_system: str = "W",
        max_depth: int = 3,
    ) -> DashaTree:
        """
        Ashtottari Dasha — 108-year cycle based on Moon's nakshatra.
        Traditionally applied when Rahu occupies a Kendra/Trikona from Lagna.
        """
        max_depth = min(max(max_depth, 1), MAX_SUPPORTED_DEPTH)
        result = self._wrapper.calculate(
            dt=birth_datetime_utc, latitude=latitude, longitude=longitude, ayanamsa=ayanamsa
        )
        moon_sid = self._moon_sidereal(result)
        nak_info = longitude_to_nakshatra(moon_sid)
        birth_dt_date = birth_datetime_utc.date() if hasattr(birth_datetime_utc, 'date') else birth_datetime_utc

        # Determine first lord from the nakshatra lookup table
        nakshatra_idx = min(int(normalize_degrees(moon_sid) / DEGREES_PER_NAKSHATRA), 26)
        first_lord_raw = ASHTOTTARI_NAKSHATRA_LORDS[nakshatra_idx]

        # Reorder ASHTOTTARI_SEQUENCE to start from first_lord_raw
        start_idx = ASHTOTTARI_SEQUENCE.index(first_lord_raw)
        reordered = ASHTOTTARI_SEQUENCE[start_idx:] + ASHTOTTARI_SEQUENCE[:start_idx]

        _first_lord, _balance, first_start = _nakshatra_balance(
            moon_sid, reordered, ASHTOTTARI_DASHA_YEARS,
            ASHTOTTARI_TOTAL_YEARS, birth_dt_date,
        )

        mahadashas = self._build_full_cycle(
            first_lord_raw, first_start,
            ASHTOTTARI_SEQUENCE, ASHTOTTARI_DASHA_YEARS,
            ASHTOTTARI_TOTAL_YEARS, max_depth,
        )

        return DashaTree(
            system="ashtottari",
            birth_date=birth_dt_date,
            trigger_planet=first_lord_raw,
            trigger_nakshatra=nak_info.nakshatra,
            trigger_nakshatra_number=nak_info.nakshatra_number,
            mahadashas=mahadashas,
            max_depth=max_depth,
            total_cycle_years=ASHTOTTARI_TOTAL_YEARS,
        )

    def compute_kalachakra(
        self,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
        house_system: str = "W",
        max_depth: int = 3,
    ) -> DashaTree:
        """
        Kalachakra Dasha — 100-year cycle based on Moon's D9 (Navamsha) sign.

        Direction:
          Savya  (Moon's D1 sign is odd: Aries, Gemini, …) → forward through zodiac.
          Apasavya (Moon's D1 sign is even: Taurus, Cancer, …) → backward.
        """
        max_depth = min(max(max_depth, 1), MAX_SUPPORTED_DEPTH)
        result = self._wrapper.calculate(
            dt=birth_datetime_utc, latitude=latitude, longitude=longitude, ayanamsa=ayanamsa
        )
        moon_sid = self._moon_sidereal(result)
        nak_info = longitude_to_nakshatra(moon_sid)
        birth_dt_date = birth_datetime_utc.date() if hasattr(birth_datetime_utc, 'date') else birth_datetime_utc

        # Moon's D1 sign determines direction
        d1_rashi, _ = longitude_to_rashi(moon_sid)
        d1_idx = _RASHI_LIST.index(d1_rashi)
        is_savya = (d1_idx % 2 == 0)  # odd sign (0-indexed) = Savya

        # Moon's D9 sign = starting dasha sign
        d9_rashi, _ = compute_varga_sign("D9", moon_sid)

        sign_sequence = KALACHAKRA_SAVYA_SIGNS if is_savya else KALACHAKRA_APASAVYA_SIGNS

        # Balance based on position within the D9 sign arc
        deg_in_d9 = moon_sid % (360.0 / 108)  # 108 navamshas in 360°
        fraction_elapsed = deg_in_d9 / (360.0 / 108)

        first_sign_years = KALACHAKRA_SIGN_YEARS[d9_rashi]
        balance_years = (1.0 - fraction_elapsed) * first_sign_years
        elapsed_days = fraction_elapsed * first_sign_years * DAYS_PER_JULIAN_YEAR
        first_start = birth_dt_date - timedelta(days=round(elapsed_days))

        mahadashas = self._build_sign_full_cycle(
            d9_rashi, first_start,
            sign_sequence, KALACHAKRA_SIGN_YEARS,
            KALACHAKRA_TOTAL_YEARS, max_depth,
        )

        return DashaTree(
            system="kalachakra",
            birth_date=birth_dt_date,
            trigger_planet=d9_rashi,
            trigger_nakshatra=nak_info.nakshatra,
            trigger_nakshatra_number=nak_info.nakshatra_number,
            mahadashas=mahadashas,
            max_depth=max_depth,
            total_cycle_years=KALACHAKRA_TOTAL_YEARS,
        )

    def compute_chara(
        self,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
        house_system: str = "W",
        max_depth: int = 3,
    ) -> DashaTree:
        """
        Chara Dasha (Jaimini) — sign-based cycle using D1 planet positions.

        Duration of each sign's dasha = count of signs from the sign to its
        lord's D1 placement (Neelakantha's rule: direction fixed by the
        starting sign's own odd/even parity — odd counts forward, even
        counts backward — not "whichever direction is shorter").
        Total cycle: sum of all 12 sign durations (varies by chart).
        """
        max_depth = min(max(max_depth, 1), MAX_SUPPORTED_DEPTH)
        result = self._wrapper.calculate(
            dt=birth_datetime_utc, latitude=latitude, longitude=longitude,
            ayanamsa=ayanamsa, house_system=house_system,
        )
        birth_dt_date = birth_datetime_utc.date() if hasattr(birth_datetime_utc, 'date') else birth_datetime_utc

        # Planet D1 sign placements
        planet_signs = {
            p.planet: longitude_to_rashi(p.sidereal_longitude)[0]
            for p in result.planet_positions
        }

        # Lagna sign
        asc_sid = result.ascendant.sidereal_longitude
        lagna_rashi, _ = longitude_to_rashi(asc_sid)

        sign_years = {s: _jaimini_sign_years(s, planet_signs) for s in _RASHI_LIST}
        total_years = sum(sign_years.values())

        sign_sequence = _jaimini_sign_sequence(lagna_rashi)

        # Chara starts from Lagna with full period (no fractional balance)
        first_start = birth_dt_date
        first_sign = sign_sequence[0]

        mahadashas = self._build_sign_full_cycle(
            first_sign, first_start,
            sign_sequence, sign_years,
            total_years, max_depth,
        )

        nak_info = longitude_to_nakshatra(self._moon_sidereal(result))
        return DashaTree(
            system="chara",
            birth_date=birth_dt_date,
            trigger_planet=lagna_rashi,
            trigger_nakshatra=nak_info.nakshatra,
            trigger_nakshatra_number=nak_info.nakshatra_number,
            mahadashas=mahadashas,
            max_depth=max_depth,
            total_cycle_years=total_years,
        )

    def compute_narayana(
        self,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
        house_system: str = "W",
        max_depth: int = 3,
    ) -> DashaTree:
        """
        Narayana Dasha (Jaimini) — computed on the D1 (Rasi) chart.

        REPLACES an earlier implementation that was mislabeled: it ran
        Chara Dasha's own math against D9 positions and called that
        "Narayana Dasha," which is not the classical system of that
        name. Confirmed via a PyJHora jhora.horoscope.dhasa.raasi.
        narayana cross-check. Real Narayana Dasha (this implementation):
          - Seed sign = the CLASSICALLY STRONGER of the Lagna sign and
            the 7th-from-Lagna sign (see _narayana_seed_sign /
            _stronger_rasi — Rule-2, aspect-based tie-break, is a
            disclosed simplification; see _stronger_rasi's docstring).
          - Sign order = a fixed 12-sign progression table keyed by seed
            sign (NARAYANA_PROGRESSION_NORMAL), with alternate tables if
            Ketu or Saturn occupies the seed sign — not a simple
            forward/backward walk from the seed.
          - Duration = Narayana's OWN formula (_narayana_dhasa_duration),
            not Chara's — even-footed-sign-dependent count direction,
            plus +1 year if the sign's lord is exalted / -1 if debilitated.
          - Two-cycle structure: each of the 12 progression signs runs
            once for its computed duration, then again for the
            12-minus-that complement, in the same order — NOT a single
            walk around the zodiac like Chara/Kalachakra.
          - Antardasha (and deeper levels): each Mahadasha's own 12-sign
            order (_narayana_antardhasa_order, its own seed/direction
            rule) split into 12 EQUAL parts — not duration-weighted
            like Chara/Kalachakra's sub-periods.
        """
        max_depth = min(max(max_depth, 1), MAX_SUPPORTED_DEPTH)
        result = self._wrapper.calculate(
            dt=birth_datetime_utc, latitude=latitude, longitude=longitude,
            ayanamsa=ayanamsa, house_system=house_system,
        )
        birth_dt_date = birth_datetime_utc.date() if hasattr(birth_datetime_utc, 'date') else birth_datetime_utc

        planets_by_sign: dict[int, list[tuple[str, str, float]]] = {i: [] for i in range(12)}
        for p in result.planet_positions:
            idx = _RASHI_LIST.index(p.rashi)
            dignity = p.dignity.value if p.dignity else None
            planets_by_sign[idx].append((p.planet, dignity, p.rashi_degree))

        asc_sign_idx = _RASHI_LIST.index(longitude_to_rashi(result.ascendant.sidereal_longitude)[0])
        seed_idx = _narayana_seed_sign(planets_by_sign, asc_sign_idx)
        progression = _narayana_progression(planets_by_sign, seed_idx)

        cycle1_years = [_narayana_dhasa_duration(planets_by_sign, idx) for idx in progression]
        cycle2_years = [max(0.0, 12.0 - y) for y in cycle1_years]
        total_years = sum(cycle1_years) + sum(cycle2_years)

        mahadashas: list[DashaPeriod] = []
        current_start = birth_dt_date
        for cycle_years in (cycle1_years, cycle2_years):
            for sign_idx, years in zip(progression, cycle_years):
                sign_days = round(years * DAYS_PER_JULIAN_YEAR)
                current_end = current_start + timedelta(days=sign_days)
                sub = self._narayana_sub_periods(
                    planets_by_sign, sign_idx, current_start, current_end, 2, max_depth,
                )
                mahadashas.append(DashaPeriod(
                    lord=_RASHI_LIST[sign_idx],
                    start_date=current_start,
                    end_date=current_end,
                    duration_days=sign_days,
                    level=1,
                    sub_periods=sub,
                ))
                current_start = current_end

        nak_info = longitude_to_nakshatra(self._moon_sidereal(result))
        return DashaTree(
            system="narayana",
            birth_date=birth_dt_date,
            trigger_planet=_RASHI_LIST[seed_idx],
            trigger_nakshatra=nak_info.nakshatra,
            trigger_nakshatra_number=nak_info.nakshatra_number,
            mahadashas=tuple(mahadashas),
            max_depth=max_depth,
            total_cycle_years=total_years,
        )

    def _narayana_sub_periods(
        self,
        planets_by_sign: dict[int, list[tuple[str, str, float]]],
        parent_sign_idx: int,
        start_date: date,
        end_date: date,
        level: int,
        max_depth: int,
    ) -> tuple[DashaPeriod, ...]:
        """Equal 12-way split per level, each level's own antardasha order — see compute_narayana()'s docstring."""
        if level > max_depth:
            return ()
        parent_days = (end_date - start_date).days
        if parent_days <= 0:
            return ()

        order = _narayana_antardhasa_order(planets_by_sign, parent_sign_idx)
        child_days = parent_days / 12.0
        periods: list[DashaPeriod] = []
        cursor = start_date
        for i, child_idx in enumerate(order):
            c_end = end_date if i == 11 else start_date + timedelta(days=round(child_days * (i + 1)))
            sub = self._narayana_sub_periods(planets_by_sign, child_idx, cursor, c_end, level + 1, max_depth)
            periods.append(DashaPeriod(
                lord=_RASHI_LIST[child_idx],
                start_date=cursor,
                end_date=c_end,
                duration_days=max((c_end - cursor).days, 0),
                level=level,
                sub_periods=sub,
            ))
            cursor = c_end

        return tuple(periods)

    # ── Internal helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _moon_sidereal(result) -> float:
        for p in result.planet_positions:
            if p.planet == "moon":
                return p.sidereal_longitude
        raise RuntimeError("Moon position not found in ephemeris result.")

    def _build_full_cycle(
        self,
        first_lord: str,
        first_start: date | datetime,
        sequence: list[str],
        period_years: dict[str, int | float],
        total_years: int | float,
        max_depth: int,
    ) -> tuple[DashaPeriod, ...]:
        """
        Build all Mahadashas from first_start through the full dasha cycle.
        The first Mahadasha may be partial (birth falls mid-cycle).
        """
        n = len(sequence)
        start_idx = sequence.index(first_lord)
        mahadashas: list[DashaPeriod] = []
        current_start = first_start
        is_dt = isinstance(first_start, datetime)

        for i in range(n):
            lord = sequence[(start_idx + i) % n]
            if is_dt:
                lord_seconds = period_years[lord] * DAYS_PER_JULIAN_YEAR * 86400.0
                current_end = current_start + timedelta(seconds=lord_seconds)
                lord_duration = lord_seconds / 86400.0
            else:
                lord_days = round(period_years[lord] * DAYS_PER_JULIAN_YEAR)
                current_end = current_start + timedelta(days=lord_days)
                lord_duration = lord_days

            sub = _build_nakshatra_periods(
                lord, sequence, period_years, total_years,
                current_start, current_end, 2, max_depth,
            )
            mahadashas.append(DashaPeriod(
                lord=lord,
                start_date=current_start,
                end_date=current_end,
                duration_days=lord_duration,
                level=1,
                sub_periods=sub,
            ))
            current_start = current_end

        return tuple(mahadashas)

    def _build_sign_full_cycle(
        self,
        first_sign: str,
        first_start: date | datetime,
        sign_sequence: list[str],
        sign_years: dict[str, int | float],
        total_years: int | float,
        max_depth: int,
    ) -> tuple[DashaPeriod, ...]:
        """
        Build all Mahadasha sign-periods from first_start through the full cycle.
        """
        mahadashas: list[DashaPeriod] = []
        current_start = first_start
        is_dt = isinstance(first_start, datetime)

        for sign in sign_sequence:
            if is_dt:
                sign_seconds = sign_years[sign] * DAYS_PER_JULIAN_YEAR * 86400.0
                current_end = current_start + timedelta(seconds=sign_seconds)
                sign_duration = sign_seconds / 86400.0
            else:
                sign_days = round(sign_years[sign] * DAYS_PER_JULIAN_YEAR)
                current_end = current_start + timedelta(days=sign_days)
                sign_duration = sign_days

            sub = _build_sign_periods(
                sign, sign_sequence, sign_years, total_years,
                current_start, current_end, 2, max_depth,
            )
            mahadashas.append(DashaPeriod(
                lord=sign,
                start_date=current_start,
                end_date=current_end,
                duration_days=sign_duration,
                level=1,
                sub_periods=sub,
            ))
            current_start = current_end

        return tuple(mahadashas)


    # ── Persistence ──────────────────────────────────────────────────────────
    #
    # Separate from the six compute_*() methods rather than combined
    # "compute_and_persist" methods, for the same reason as HoroscopeEngine
    # and DivisionalEngine: the compute_*() methods are blocking pyswisseph
    # calls that routers offload via asyncio.to_thread; persistence is
    # async DB I/O with no CPU-bound work.

    _SYSTEM_TO_METHOD = {
        "vimshottari": "compute_vimshottari",
        "yogini": "compute_yogini",
        "ashtottari": "compute_ashtottari",
        "kalachakra": "compute_kalachakra",
        "chara": "compute_chara",
        "narayana": "compute_narayana",
    }

    async def persist_tree(
        self,
        tree: DashaTree,
        *,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
        house_system: str = "W",
        user_id=None,
        subject_name: str = "Unnamed",
    ) -> uuid.UUID:
        """
        Persist an already-computed DashaTree (from any of the six
        compute_*() methods): the birth_charts anchor row (created if this
        subject has no existing one) and the full dasha tree for
        tree.system, replacing any prior tree already stored for the same
        (chart, system) pair.

        Requires this engine to have been constructed with
        birth_chart_repo and dasha_repo — raises RuntimeError otherwise.

        Requires migration 0003 (dasha_type enum extended with
        'chara'/'narayana'; `lord` widened to a plain string) — see that
        migration's docstring for why.

        Returns the birth_chart_id.
        """
        if not (self._birth_chart_repo and self._dasha_repo):
            raise RuntimeError(
                "DashaEngine.persist_tree() requires birth_chart_repo and "
                "dasha_repo to be provided at construction time."
            )
        if tree.system not in self._SYSTEM_TO_METHOD:
            raise ValueError(f"Unknown dasha system: {tree.system!r}")

        chart_id = await self._birth_chart_repo.get_or_create(
            birth_datetime_utc=birth_datetime_utc,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            house_system=house_system,
            user_id=user_id,
            subject_name=subject_name,
        )

        await self._dasha_repo.save_tree(chart_id, tree)

        return chart_id
