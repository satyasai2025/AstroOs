"""
AstroOS — Dasha Engine (Task 6)

Computes six Dasha systems from a birth moment:

  1. Vimshottari  — 120-year nakshatra-based cycle (Parashara, BPHS Ch.46)
  2. Yogini       — 36-year nakshatra-based cycle  (BPHS Ch.47)
  3. Ashtottari   — 108-year nakshatra-based cycle (BPHS Ch.46)
  4. Kalachakra   — 100-year navamsha-sign cycle   (BPHS Ch.47)
  5. Chara        — Jaimini sign-based cycle        (Jaimini Sutras Ch.2)
  6. Narayana     — Jaimini sign-based D9 cycle     (Jaimini Sutras Ch.2)

All six systems return a DashaTree with nested DashaPeriods up to
the requested depth (1=Mahadasha … 5=Prana).

Sub-period formula (universal for nakshatra-based systems)
----------------------------------------------------------
  sub_days(L, parent) = parent_days × L_years / total_cycle_years

  Periods are date-anchored using the proportional offset from the
  parent period start to avoid cumulative rounding drift.
"""

from __future__ import annotations

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
    start_date: date,
    end_date: date,
    level: int,
    max_depth: int,
) -> tuple[DashaPeriod, ...]:
    """
    Recursively build a dasha sub-period tree for nakshatra-based systems.

    All dates are anchored from start_date using proportional offsets to
    prevent cumulative rounding drift.

    Args:
        start_lord:   Lord whose sub-period sequence begins first.
        sequence:     Full ordered sequence of lords (cycled from start_lord).
        period_years: Map of lord → years in the cycle.
        total_years:  Total years in one complete cycle.
        start_date:   Inclusive start of the parent period.
        end_date:     Exclusive end of the parent period.
        level:        Current tree depth (1 = Mahadasha).
        max_depth:    Stop recursing at this depth.
    """
    if level > max_depth:
        return ()

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

        p_start = start_date + timedelta(days=round(elapsed_ratio * parent_days))
        # Clamp the very last sub-period to the exact parent end
        if i == n - 1:
            p_end = end_date
        else:
            p_end = start_date + timedelta(days=round(next_ratio * parent_days))

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
    start_date: date,
    end_date: date,
    level: int,
    max_depth: int,
) -> tuple[DashaPeriod, ...]:
    """
    Recursively build a dasha sub-period tree for sign-based systems
    (Kalachakra, Chara, Narayana).

    Sub-periods follow the same sign sequence cyclically from start_sign.
    """
    if level > max_depth:
        return ()

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

        p_start = start_date + timedelta(days=round(elapsed_ratio * parent_days))
        if i == n - 1:
            p_end = end_date
        else:
            p_end = start_date + timedelta(days=round(next_ratio * parent_days))

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
    birth_date: date,
) -> tuple[str, float, date]:
    """
    Compute the starting lord, remaining balance (years), and the date on
    which the first Mahadasha began (before birth for partial periods).

    Returns:
        (first_lord, balance_years, first_maha_start_date)
    """
    lon = normalize_degrees(moon_sidereal_lon)
    nakshatra_idx = int(lon / DEGREES_PER_NAKSHATRA)
    nakshatra_idx = min(nakshatra_idx, 26)  # clamp edge case
    deg_in_nak = lon % DEGREES_PER_NAKSHATRA
    fraction_elapsed = deg_in_nak / DEGREES_PER_NAKSHATRA

    first_lord = lord_sequence[nakshatra_idx % len(lord_sequence)]
    first_lord_years = period_years[first_lord]

    # Balance (remaining) years at birth
    balance_years = (1.0 - fraction_elapsed) * first_lord_years

    # Days already elapsed in the first Mahadasha before birth
    elapsed_days = fraction_elapsed * first_lord_years * DAYS_PER_JULIAN_YEAR
    first_start = birth_date - timedelta(days=round(elapsed_days))

    return first_lord, balance_years, first_start


# ── Jaimini helpers ───────────────────────────────────────────────────────────


def _jaimini_sign_duration(sign: str, lord_sign: str, use_alternate: bool = False) -> int:
    """
    Chara / Narayana sign duration by Neelakantha's rule:

    Count from `sign` to `lord_sign` in the shorter direction.
    If the lord is in the same sign: 12 years.
    Special: for Scorpio (co-lord Ketu) and Aquarius (co-lord Rahu),
    the shorter count from the two lords is used.

    Returns an integer duration in years (1–12).
    """
    from_idx = _RASHI_LIST.index(sign)
    to_idx = _RASHI_LIST.index(lord_sign)

    forward = (to_idx - from_idx) % 12
    backward = (from_idx - to_idx) % 12

    count = min(forward, backward)
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
        max_depth = min(max(max_depth, 1), MAX_SUPPORTED_DEPTH)
        result = self._wrapper.calculate(
            dt=birth_datetime_utc, latitude=latitude, longitude=longitude, ayanamsa=ayanamsa
        )
        moon_sid = self._moon_sidereal(result)
        nak_info = longitude_to_nakshatra(moon_sid)
        birth_dt_date = birth_datetime_utc.date() if hasattr(birth_datetime_utc, 'date') else birth_datetime_utc

        first_lord, _balance, first_start = _nakshatra_balance(
            moon_sid, VIMSHOTTARI_SEQUENCE, VIMSHOTTARI_DASHA_YEARS,
            VIMSHOTTARI_TOTAL_YEARS, birth_dt_date,
        )

        mahadashas = self._build_full_cycle(
            first_lord, first_start,
            VIMSHOTTARI_SEQUENCE, VIMSHOTTARI_DASHA_YEARS,
            VIMSHOTTARI_TOTAL_YEARS, max_depth,
        )

        return DashaTree(
            system="vimshottari",
            birth_date=birth_dt_date,
            trigger_planet=first_lord,
            trigger_nakshatra=nak_info.nakshatra,
            trigger_nakshatra_number=nak_info.nakshatra_number,
            mahadashas=mahadashas,
            max_depth=max_depth,
            total_cycle_years=VIMSHOTTARI_TOTAL_YEARS,
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
        lord's D1 placement (Neelakantha's rule; shorter of forward/backward).
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
        Narayana Dasha (Jaimini) — sign-based cycle using D9 (Navamsha) positions.

        Duration of each sign = count of signs from the sign to its lord's
        D9 sign placement (same Neelakantha rule as Chara, but applied to D9).
        """
        max_depth = min(max(max_depth, 1), MAX_SUPPORTED_DEPTH)
        result = self._wrapper.calculate(
            dt=birth_datetime_utc, latitude=latitude, longitude=longitude,
            ayanamsa=ayanamsa, house_system=house_system,
        )
        birth_dt_date = birth_datetime_utc.date() if hasattr(birth_datetime_utc, 'date') else birth_datetime_utc

        # Planet D9 sign placements
        planet_d9_signs: dict[str, str] = {}
        for p in result.planet_positions:
            d9_rashi, _ = compute_varga_sign("D9", p.sidereal_longitude)
            planet_d9_signs[p.planet] = d9_rashi

        # Lagna D9 sign
        asc_sid = result.ascendant.sidereal_longitude
        lagna_d9_rashi, _ = compute_varga_sign("D9", asc_sid)

        sign_years = {s: _jaimini_sign_years(s, planet_d9_signs) for s in _RASHI_LIST}
        total_years = sum(sign_years.values())

        sign_sequence = _jaimini_sign_sequence(lagna_d9_rashi)
        first_sign = sign_sequence[0]

        mahadashas = self._build_sign_full_cycle(
            first_sign, birth_dt_date,
            sign_sequence, sign_years,
            total_years, max_depth,
        )

        nak_info = longitude_to_nakshatra(self._moon_sidereal(result))
        return DashaTree(
            system="narayana",
            birth_date=birth_dt_date,
            trigger_planet=lagna_d9_rashi,
            trigger_nakshatra=nak_info.nakshatra,
            trigger_nakshatra_number=nak_info.nakshatra_number,
            mahadashas=mahadashas,
            max_depth=max_depth,
            total_cycle_years=total_years,
        )

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
        first_start: date,
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

        for i in range(n):
            lord = sequence[(start_idx + i) % n]
            lord_days = round(period_years[lord] * DAYS_PER_JULIAN_YEAR)
            current_end = current_start + timedelta(days=lord_days)

            sub = _build_nakshatra_periods(
                lord, sequence, period_years, total_years,
                current_start, current_end, 2, max_depth,
            )
            mahadashas.append(DashaPeriod(
                lord=lord,
                start_date=current_start,
                end_date=current_end,
                duration_days=lord_days,
                level=1,
                sub_periods=sub,
            ))
            current_start = current_end

        return tuple(mahadashas)

    def _build_sign_full_cycle(
        self,
        first_sign: str,
        first_start: date,
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

        for sign in sign_sequence:
            sign_days = round(sign_years[sign] * DAYS_PER_JULIAN_YEAR)
            current_end = current_start + timedelta(days=sign_days)

            sub = _build_sign_periods(
                sign, sign_sequence, sign_years, total_years,
                current_start, current_end, 2, max_depth,
            )
            mahadashas.append(DashaPeriod(
                lord=sign,
                start_date=current_start,
                end_date=current_end,
                duration_days=sign_days,
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
