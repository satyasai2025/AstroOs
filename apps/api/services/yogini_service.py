"""
AstroOS — Yogini Dasha 5-Tier Engine (MD, AD, PD, SD, PrD)
==========================================================
Implements full 5-tier Yogini Dasha hierarchy according to Vinay Jha's
Kundalee software (A66_YoginiModule, frmDashaaYogini):
  - Cycle Duration: 36 Years
  - Time Unit: Mean Tithi (Surya Siddhanta Mean Tithi Year = 354.36725957 days)
  - 1 Mean Tithi = 0.9843534988 days = 23h 37m 28.14s
  - 5 Tiers:
      1. Mahadasha (MD)
      2. Antardasha (AD)
      3. Pratyantardasha (PD)
      4. Sookshma Dasha (SD)
      5. Praana Dasha (PrD)
  - Strict Mathematical Conservation:
      Sum of child periods exactly equals parent period at all 5 tiers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple


# ============================================================================
# 1. Classical Yogini Definitions & Constants
# ============================================================================

YOGINI_SPECS: list[tuple[int, str, str, int]] = [
    # (Index 1..8, Name, Lord, Duration Years)
    (1, "Mangala",  "moon",    1),
    (2, "Pingala",  "sun",     2),
    (3, "Dhanya",   "jupiter", 3),
    (4, "Bhramari", "mars",    4),
    (5, "Bhadrika", "mercury", 5),
    (6, "Ulka",     "saturn",  6),
    (7, "Siddha",   "venus",   7),
    (8, "Sankata",  "rahu",    8),
]

TOTAL_YOGINI_YEARS: int = 36

# Surya Siddhanta exact Mean Tithi Year in civil days:
# 360 tithis * (1577917828 civil days in Mahayuga / 1603000080 tithis in Mahayuga)
MEAN_TITHI_DAY: float = 1577917828.0 / 1603000080.0  # 0.9843534988029054 days
MEAN_TITHI_YEAR_DAYS: float = 360.0 * MEAN_TITHI_DAY  # 354.36725956904595 days

YOGINI_NAMES: list[str] = [y[1] for y in YOGINI_SPECS]
YOGINI_YEARS_MAP: dict[str, int] = {y[1].lower(): y[3] for y in YOGINI_SPECS}
YOGINI_LORDS_MAP: dict[str, str] = {y[1].lower(): y[2] for y in YOGINI_SPECS}


@dataclass(frozen=True)
class YoginiHierarchyNode:
    tier: Literal["MD", "AD", "PD", "SD", "PrD"]
    yogini_name: str
    ruling_graha: str
    start_time_iso: str
    end_time_iso: str
    duration_seconds: float
    duration_days: float
    duration_years: float
    sub_periods: tuple[YoginiHierarchyNode, ...] = ()


def get_starting_yogini(nakshatra_number_1_indexed: int) -> tuple[int, str, str, int]:
    """
    Computes starting Yogini from 1-indexed Nakshatra (1=Ashwini ... 27=Revati).
    Formula: Yogini Index = ((Nakshatra_Index + 3) % 8) + 1
    """
    if not (1 <= nakshatra_number_1_indexed <= 27):
        raise ValueError(f"Nakshatra index must be 1..27, got {nakshatra_number_1_indexed}")
    idx = ((nakshatra_number_1_indexed + 3) % 8) + 1
    return YOGINI_SPECS[idx - 1]


class Yogini5TierService:
    """Service computing 5-tier Yogini dasha hierarchy with exact datetime math."""

    def __init__(self, year_days: float = MEAN_TITHI_YEAR_DAYS) -> None:
        self.year_days = year_days
        self.year_seconds = year_days * 86400.0

    def compute_hierarchy(
        self,
        birth_datetime: datetime,
        moon_longitude: float,
        max_tier: Literal["MD", "AD", "PD", "SD", "PrD"] = "PD",
        num_md_cycles: int = 1,
    ) -> dict[str, Any]:
        """
        Generates full multi-tier hierarchy down to max_tier.
        """
        lon = moon_longitude % 360.0
        deg_per_nak = 360.0 / 27.0  # 13°20'
        nak_idx = int(lon // deg_per_nak) + 1
        deg_in_nak = lon % deg_per_nak
        frac_elapsed = deg_in_nak / deg_per_nak
        frac_rem = 1.0 - frac_elapsed

        start_y = get_starting_yogini(nak_idx)
        start_idx = start_y[0] - 1
        total_start_yrs = float(start_y[3])
        bal_yrs = frac_rem * total_start_yrs
        bal_sec = bal_yrs * self.year_seconds

        dt_start = birth_datetime if birth_datetime.tzinfo else birth_datetime.replace(tzinfo=timezone.utc)
        dt_first_md_end = dt_start + timedelta(seconds=bal_sec)

        mahadashas: list[YoginiHierarchyNode] = []

        # 1. First (partial) MD
        first_md = self._build_node(
            tier="MD",
            name=start_y[1],
            lord=start_y[2],
            nominal_years=total_start_yrs,
            start_dt=dt_start,
            end_dt=dt_first_md_end,
            is_partial=True,
            balance_fraction=frac_rem,
            max_tier=max_tier,
        )
        mahadashas.append(first_md)

        curr_start = dt_first_md_end

        # 2. Subsequent MDs
        total_mds = num_md_cycles * 8
        for i in range(1, total_mds):
            y_idx = (start_idx + i) % 8
            spec = YOGINI_SPECS[y_idx]
            nom_yrs = float(spec[3])
            dur_sec = nom_yrs * self.year_seconds
            curr_end = curr_start + timedelta(seconds=dur_sec)

            md_node = self._build_node(
                tier="MD",
                name=spec[1],
                lord=spec[2],
                nominal_years=nom_yrs,
                start_dt=curr_start,
                end_dt=curr_end,
                is_partial=False,
                balance_fraction=1.0,
                max_tier=max_tier,
            )
            mahadashas.append(md_node)
            curr_start = curr_end

        return {
            "system": "yogini_5tier",
            "cycle_years": TOTAL_YOGINI_YEARS,
            "year_basis": "mean_tithi",
            "year_days": self.year_days,
            "birth_nakshatra": nak_idx,
            "starting_yogini": start_y[1],
            "balance_years": round(bal_yrs, 6),
            "max_tier_computed": max_tier,
            "mahadashas": [self._node_to_dict(md) for md in mahadashas],
        }

    def _build_node(
        self,
        tier: Literal["MD", "AD", "PD", "SD", "PrD"],
        name: str,
        lord: str,
        nominal_years: float,
        start_dt: datetime,
        end_dt: datetime,
        is_partial: bool,
        balance_fraction: float,
        max_tier: str,
    ) -> YoginiHierarchyNode:
        dur_sec = (end_dt - start_dt).total_seconds()
        dur_days = dur_sec / 86400.0
        dur_yrs = dur_sec / self.year_seconds

        tier_order = ["MD", "AD", "PD", "SD", "PrD"]
        curr_tier_idx = tier_order.index(tier)
        max_tier_idx = tier_order.index(max_tier)

        sub_periods = []
        if curr_tier_idx < max_tier_idx:
            next_tier = tier_order[curr_tier_idx + 1]
            start_y_idx = [y[1].lower() for y in YOGINI_SPECS].index(name.lower())

            curr_sub_start = start_dt
            for step in range(8):
                idx = (start_y_idx + step) % 8
                sub_spec = YOGINI_SPECS[idx]
                sub_name = sub_spec[1]
                sub_lord = sub_spec[2]
                sub_base_yrs = float(sub_spec[3])

                sub_prop = sub_base_yrs / float(TOTAL_YOGINI_YEARS)
                sub_nom_sec = dur_sec * sub_prop if not is_partial else (nominal_years * self.year_seconds) * sub_prop * balance_fraction

                sub_end = curr_sub_start + timedelta(seconds=sub_nom_sec)
                if step == 7 or sub_end > end_dt:
                    sub_end = end_dt

                if sub_end > curr_sub_start:
                    child = self._build_node(
                        tier=next_tier,
                        name=sub_name,
                        lord=sub_lord,
                        nominal_years=nominal_years * sub_prop,
                        start_dt=curr_sub_start,
                        end_dt=sub_end,
                        is_partial=is_partial,
                        balance_fraction=balance_fraction,
                        max_tier=max_tier,
                    )
                    sub_periods.append(child)
                    curr_sub_start = sub_end
                if curr_sub_start >= end_dt:
                    break

        return YoginiHierarchyNode(
            tier=tier,
            yogini_name=name,
            ruling_graha=lord,
            start_time_iso=start_dt.isoformat(),
            end_time_iso=end_dt.isoformat(),
            duration_seconds=dur_sec,
            duration_days=round(dur_days, 4),
            duration_years=round(dur_yrs, 6),
            sub_periods=tuple(sub_periods),
        )

    def _node_to_dict(self, node: YoginiHierarchyNode) -> dict[str, Any]:
        res = {
            "tier": node.tier,
            "yogini": node.yogini_name,
            "lord": node.ruling_graha,
            "start": node.start_time_iso,
            "end": node.end_time_iso,
            "duration_days": node.duration_days,
            "duration_years": node.duration_years,
        }
        if node.sub_periods:
            res["sub_periods"] = [self._node_to_dict(c) for c in node.sub_periods]
        return res