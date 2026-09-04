"""
AstroOS — Yogini Dasha Engine (36-Year Cycle)
==============================================
Provides authentic Parashari Yogini Dasha calculation as certified in
Vinay Jha's Kundalee software (A66_YoginiModule, frmDashaaYogini):
  - Cycle Duration: 36 Years
  - 8 Yoginis:
      1. Mangala   (1 yr,  Ruler: Moon)
      2. Pingala   (2 yrs, Ruler: Sun)
      3. Dhanya    (3 yrs, Ruler: Jupiter)
      4. Bhramari  (4 yrs, Ruler: Mars)
      5. Bhadrika  (5 yrs, Ruler: Mercury)
      6. Ulka      (6 yrs, Ruler: Saturn)
      7. Siddha    (7 yrs, Ruler: Venus)
      8. Sankata   (8 yrs, Ruler: Rahu)
  - Formula:
      Yogini Index = ((Nakshatra_Index + 3) % 8) + 1
      (Where Nakshatra_Index: 1=Ashwini ... 27=Revati)
  - Time Basis: Mean Tithi (354.367 days/yr canonical default)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple


YOGINI_ORDER: list[tuple[int, str, str, int]] = [
    # (Index 1..8, Name, Ruling Graha, Duration Years)
    (1, "Mangala", "moon", 1),
    (2, "Pingala", "sun", 2),
    (3, "Dhanya", "jupiter", 3),
    (4, "Bhramari", "mars", 4),
    (5, "Bhadrika", "mercury", 5),
    (6, "Ulka", "saturn", 6),
    (7, "Siddha", "venus", 7),
    (8, "Sankata", "rahu", 8),
]

TOTAL_YOGINI_YEARS: int = 36
YOGINI_NAMES: list[str] = [y[1] for y in YOGINI_ORDER]
YOGINI_YEARS: dict[str, int] = {y[1].lower(): y[3] for y in YOGINI_ORDER}
YOGINI_LORDS: dict[str, str] = {y[1].lower(): y[2] for y in YOGINI_ORDER}

DEFAULT_YOGINI_YEAR_DAYS: float = 354.367  # Mean Tithi basis from Phalit.kkk


@dataclass(frozen=True)
class YoginiPeriod:
    yogini_name: str
    ruling_graha: str
    duration_years: float
    duration_days: int
    start_date: date
    end_date: date
    sub_periods: tuple[YoginiPeriod, ...] = ()


def get_yogini_by_nakshatra(nakshatra_number: int) -> tuple[int, str, str, int]:
    """
    Computes starting Yogini from 1-indexed Nakshatra (1=Ashwini ... 27=Revati).
    Formula: Yogini Index = ((Nakshatra_Index + 3) % 8) + 1
    """
    if not (1 <= nakshatra_number <= 27):
        raise ValueError(f"Nakshatra number must be between 1 and 27, got {nakshatra_number}")
    idx = ((nakshatra_number + 3) % 8) + 1
    return YOGINI_ORDER[idx - 1]


def compute_yogini_dasha_tree(
    birth_datetime: datetime,
    moon_longitude: float,
    num_cycles: int = 2,
    year_length_days: float = DEFAULT_YOGINI_YEAR_DAYS,
) -> dict[str, any]:
    """
    Computes full Yogini Dasha tree (Mahadasha and Antardasha) from Moon's sidereal longitude.
    """
    lon = moon_longitude % 360.0
    deg_per_nak = 360.0 / 27.0  # 13°20' = 13.333333°
    nak_idx = int(lon // deg_per_nak) + 1  # 1..27
    deg_in_nak = lon % deg_per_nak
    fraction_elapsed = deg_in_nak / deg_per_nak
    fraction_remaining = 1.0 - fraction_elapsed

    start_yogini = get_yogini_by_nakshatra(nak_idx)
    start_idx = start_yogini[0] - 1  # 0..7

    start_name = start_yogini[1]
    start_lord = start_yogini[2]
    total_md_years = start_yogini[3]

    balance_years = fraction_remaining * float(total_md_years)
    balance_days = round(balance_years * year_length_days)

    b_date = birth_datetime.date() if isinstance(birth_datetime, datetime) else birth_datetime
    first_end = b_date + timedelta(days=balance_days)

    mahadashas: list[dict[str, any]] = []

    # 1. First (partial) Mahadasha
    curr_start = b_date
    curr_end = first_end

    # Build first MD antardashas
    first_ads = _build_yogini_antardashas(
        md_name=start_name,
        md_total_years=total_md_years,
        actual_start_date=curr_start,
        actual_end_date=curr_end,
        is_partial=True,
        balance_fraction=fraction_remaining,
        year_length_days=year_length_days,
    )
    mahadashas.append({
        "yogini": start_name,
        "ruling_graha": start_lord,
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
        order_idx = (start_idx + step) % 8
        y_info = YOGINI_ORDER[order_idx]
        y_name = y_info[1]
        y_lord = y_info[2]
        y_years = y_info[3]
        dur_days = round(y_years * year_length_days)
        curr_end = curr_start + timedelta(days=dur_days)

        ads = _build_yogini_antardashas(
            md_name=y_name,
            md_total_years=y_years,
            actual_start_date=curr_start,
            actual_end_date=curr_end,
            is_partial=False,
            balance_fraction=1.0,
            year_length_days=year_length_days,
        )

        mahadashas.append({
            "yogini": y_name,
            "ruling_graha": y_lord,
            "start_date": str(curr_start),
            "end_date": str(curr_end),
            "duration_days": dur_days,
            "duration_years": float(y_years),
            "is_partial": False,
            "antardashas": ads,
        })
        curr_start = curr_end

    return {
        "system": "yogini",
        "cycle_years": TOTAL_YOGINI_YEARS,
        "year_length_days": year_length_days,
        "year_basis": "mean_tithi",
        "birth_nakshatra": nak_idx,
        "starting_yogini": start_name,
        "balance_at_birth_years": round(balance_years, 4),
        "mahadashas": mahadashas,
    }


def _build_yogini_antardashas(
    md_name: str,
    md_total_years: int,
    actual_start_date: date,
    actual_end_date: date,
    is_partial: bool,
    balance_fraction: float,
    year_length_days: float,
) -> list[dict[str, any]]:
    """
    Builds the 8 Antardashas of a Yogini Mahadasha.
    Formula: AD Years = (MD Years * AD Base Years) / 36.0
    """
    start_idx = [y[1].lower() for y in YOGINI_ORDER].index(md_name.lower())
    ads = []
    curr = actual_start_date

    total_actual_days = (actual_end_date - actual_start_date).days

    for i in range(8):
        y_idx = (start_idx + i) % 8
        ad_info = YOGINI_ORDER[y_idx]
        ad_name = ad_info[1]
        ad_lord = ad_info[2]
        ad_base_yrs = ad_info[3]

        # Proportion of MD
        ad_prop = float(ad_base_yrs) / float(TOTAL_YOGINI_YEARS)
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
                "antar_yogini": ad_name,
                "ruling_graha": ad_lord,
                "start_date": str(curr),
                "end_date": str(end_d),
                "duration_days": dur,
            })
            curr = end_d
        if curr >= actual_end_date:
            break

    return ads