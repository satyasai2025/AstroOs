"""
AstroOS — Ashtottari Dasha Engine (108-Year Cycle)
==================================================
Provides authentic Parashari Ashtottari Dasha calculation as certified in
Vinay Jha's Kundalee software (A75_AshtottariDasha, frmDashaAshtottari):
  - Cycle Duration: 108 Years
  - 8 Planetary Lords (Krittikadi / Arka-cycle default):
      1. Sun     (6 yrs)   - Krittika, Rohini, Mrigashira (3 nakshatras)
      2. Moon    (15 yrs)  - Ardra, Punarvasu, Pushya, Ashlesha (4 nakshatras)
      3. Mars    (8 yrs)   - Magha, Purva Phalguni, Uttara Phalguni (3 nakshatras)
      4. Mercury (17 yrs)  - Hasta, Chitra, Swati, Vishakha (4 nakshatras)
      5. Saturn  (10 yrs)  - Anuradha, Jyeshtha, Moola (3 nakshatras)
      6. Jupiter (19 yrs)  - Purva Ashadha, Uttara Ashadha, Abhijit, Shravana (4 nakshatras)
      7. Rahu    (12 yrs)  - Dhanishtha, Shatabhisha, Purva Bhadrapada (3 nakshatras)
      8. Venus   (21 yrs)  - Uttara Bhadrapada, Revati, Ashwini, Bharani (4 nakshatras)
      Total: 3 + 4 + 3 + 4 + 3 + 4 + 3 + 4 = 28 Nakshatras (including Abhijit)
      Sum of Years: 6 + 15 + 8 + 17 + 10 + 19 + 12 + 21 = 108 Years!
  - Time Basis: True Tithi (Spashta Tithi from Phalit.kkk)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple


ASHTOTTARI_ORDER: list[tuple[str, int, tuple[int, ...]]] = [
    # (Lord, Duration Years, Standard 27-Nakshatra Indices 1..27)
    ("sun", 6, (3, 4, 5)),               # Krittika, Rohini, Mrigashira
    ("moon", 15, (6, 7, 8, 9)),          # Ardra, Punarvasu, Pushya, Ashlesha
    ("mars", 8, (10, 11, 12)),           # Magha, P.Phalguni, U.Phalguni
    ("mercury", 17, (13, 14, 15, 16)),   # Hasta, Chitra, Swati, Vishakha
    ("saturn", 10, (17, 18, 19)),        # Anuradha, Jyeshtha, Moola
    ("jupiter", 19, (20, 21, 22)),       # P.Ashadha, U.Ashadha, Shravana (Abhijit embedded)
    ("rahu", 12, (23, 24, 25)),          # Dhanishtha, Shatabhisha, P.Bhadrapada
    ("venus", 21, (26, 27, 1, 2)),       # U.Bhadrapada, Revati, Ashwini, Bharani
]

TOTAL_ASHTOTTARI_YEARS: int = 108
ASHTOTTARI_LORDS: list[str] = [entry[0] for entry in ASHTOTTARI_ORDER]
ASHTOTTARI_YEARS: dict[str, int] = {entry[0]: entry[1] for entry in ASHTOTTARI_ORDER}

DEFAULT_ASHTOTTARI_YEAR_DAYS: float = 354.367  # Exact Tithi basis from Phalit.kkk


def get_ashtottari_lord_by_nakshatra(nakshatra_number: int) -> tuple[str, int, int]:
    """
    Returns (lord, total_years, group_size) for 1-indexed Nakshatra (1=Ashwini ... 27=Revati).
    """
    if not (1 <= nakshatra_number <= 27):
        raise ValueError(f"Nakshatra number must be between 1 and 27, got {nakshatra_number}")
    for lord, yrs, naks in ASHTOTTARI_ORDER:
        if nakshatra_number in naks:
            return lord, yrs, len(naks)
    # Default fallback
    return "sun", 6, 3


def compute_ashtottari_dasha_tree(
    birth_datetime: datetime,
    moon_longitude: float,
    num_cycles: int = 1,
    year_length_days: float = DEFAULT_ASHTOTTARI_YEAR_DAYS,
) -> dict[str, any]:
    """
    Computes full Ashtottari Dasha tree (108 years) from Moon's sidereal longitude.
    """
    lon = moon_longitude % 360.0
    deg_per_nak = 360.0 / 27.0
    nak_idx = int(lon // deg_per_nak) + 1  # 1..27
    deg_in_nak = lon % deg_per_nak
    fraction_elapsed_nak = deg_in_nak / deg_per_nak

    start_lord, total_md_years, group_size = get_ashtottari_lord_by_nakshatra(nak_idx)
    start_lord_idx = ASHTOTTARI_LORDS.index(start_lord)

    # In Ashtottari, each nakshatra within the lord's group represents 1/group_size of the total period
    fraction_remaining = 1.0 - fraction_elapsed_nak
    balance_years = (fraction_remaining / float(group_size)) * float(total_md_years)
    balance_days = round(balance_years * year_length_days)

    b_date = birth_datetime.date() if isinstance(birth_datetime, datetime) else birth_datetime
    first_end = b_date + timedelta(days=balance_days)

    mahadashas: list[dict[str, any]] = []

    # 1. First (partial) Mahadasha
    curr_start = b_date
    curr_end = first_end

    first_ads = _build_ashtottari_antardashas(
        md_lord=start_lord,
        md_total_years=total_md_years,
        actual_start_date=curr_start,
        actual_end_date=curr_end,
        is_partial=True,
        balance_fraction=fraction_remaining,
        year_length_days=year_length_days,
    )
    mahadashas.append({
        "lord": start_lord,
        "start_date": str(curr_start),
        "end_date": str(curr_end),
        "duration_days": balance_days,
        "duration_years": round(balance_years, 4),
        "is_partial": True,
        "antardashas": first_ads,
    })

    curr_start = curr_end

    # 2. Subsequent Mahadashas across requested cycles
    total_periods = num_cycles * 8
    for step in range(1, total_periods):
        order_idx = (start_lord_idx + step) % 8
        lord_info = ASHTOTTARI_ORDER[order_idx]
        l_name = lord_info[0]
        l_years = lord_info[1]
        dur_days = round(l_years * year_length_days)
        curr_end = curr_start + timedelta(days=dur_days)

        ads = _build_ashtottari_antardashas(
            md_lord=l_name,
            md_total_years=l_years,
            actual_start_date=curr_start,
            actual_end_date=curr_end,
            is_partial=False,
            balance_fraction=1.0,
            year_length_days=year_length_days,
        )

        mahadashas.append({
            "lord": l_name,
            "start_date": str(curr_start),
            "end_date": str(curr_end),
            "duration_days": dur_days,
            "duration_years": float(l_years),
            "is_partial": False,
            "antardashas": ads,
        })
        curr_start = curr_end

    return {
        "system": "ashtottari",
        "cycle_years": TOTAL_ASHTOTTARI_YEARS,
        "year_length_days": year_length_days,
        "year_basis": "exact_true_tithi",
        "birth_nakshatra": nak_idx,
        "starting_lord": start_lord,
        "balance_at_birth_years": round(balance_years, 4),
        "mahadashas": mahadashas,
    }


def _build_ashtottari_antardashas(
    md_lord: str,
    md_total_years: int,
    actual_start_date: date,
    actual_end_date: date,
    is_partial: bool,
    balance_fraction: float,
    year_length_days: float,
) -> list[dict[str, any]]:
    """
    Builds the 8 Antardashas of an Ashtottari Mahadasha.
    Formula: AD Years = (MD Years * AD Base Years) / 108.0
    """
    start_idx = ASHTOTTARI_LORDS.index(md_lord)
    ads = []
    curr = actual_start_date

    for i in range(8):
        l_idx = (start_idx + i) % 8
        ad_info = ASHTOTTARI_ORDER[l_idx]
        ad_name = ad_info[0]
        ad_base_yrs = ad_info[1]

        ad_prop = float(ad_base_yrs) / float(TOTAL_ASHTOTTARI_YEARS)
        ad_nominal_years = float(md_total_years) * ad_prop
        ad_nominal_days = round(ad_nominal_years * year_length_days)

        if is_partial:
            ad_days = round(ad_nominal_days * balance_fraction)
        else:
            ad_days = ad_nominal_days

        end_d = curr + timedelta(days=ad_days)
        if end_d > actual_end_date or i == 7:
            end_d = actual_end_date

        dur = (end_d - curr).days
        if dur > 0:
            ads.append({
                "antar_lord": ad_name,
                "start_date": str(curr),
                "end_date": str(end_d),
                "duration_days": dur,
            })
            curr = end_d
        if curr >= actual_end_date:
            break

    return ads