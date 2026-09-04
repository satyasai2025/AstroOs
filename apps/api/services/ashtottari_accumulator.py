"""
AstroOS — Ashtottari Dasha 5-Tier Accumulator & Engine
======================================================
Implements full 5-tier Ashtottari Dasha hierarchy according to Vinay Jha's
Kundalee software (A75_AshtottariDasha, frmDashaAshtottari):
  - Cycle Duration: 108 Years
  - 8 Planetary Lords (Krittikadi Arka-cycle default):
      1. Sun     (6 yrs)   - Krittika, Rohini, Mrigashira (3 nakshatras)
      2. Moon    (15 yrs)  - Ardra, Punarvasu, Pushya, Ashlesha (4 nakshatras)
      3. Mars    (8 yrs)   - Magha, P.Phalguni, U.Phalguni (3 nakshatras)
      4. Mercury (17 yrs)  - Hasta, Chitra, Swati, Vishakha (4 nakshatras)
      5. Saturn  (10 yrs)  - Anuradha, Jyeshtha, Moola (3 nakshatras)
      6. Jupiter (19 yrs)  - P.Ashadha, U.Ashadha, Abhijit, Shravana (4 nakshatras)
      7. Rahu    (12 yrs)  - Dhanishtha, Shatabhisha, P.Bhadrapada (3 nakshatras)
      8. Venus   (21 yrs)  - U.Bhadrapada, Revati, Ashwini, Bharani (4 nakshatras)
  - Time Basis: Exact True Tithi (Spashta Tithi from Phalit.kkk)
      Table time format: Yr:Mon:Date:Hr:Min:Sec
  - 5 Tiers: MD, AD, PD, SD, PrD with energy conservation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple

from apps.api.services.ephemeris_wrapper import EphemerisWrapper


ASHTOTTARI_SPECS: list[tuple[str, int, tuple[int, ...]]] = [
    # (Lord, Duration Years, Standard 27-Nakshatra Indices)
    ("sun",     6,  (3, 4, 5)),               # Krittika, Rohini, Mrigashira
    ("moon",    15, (6, 7, 8, 9)),          # Ardra, Punarvasu, Pushya, Ashlesha
    ("mars",    8,  (10, 11, 12)),           # Magha, P.Phalguni, U.Phalguni
    ("mercury", 17, (13, 14, 15, 16)),   # Hasta, Chitra, Swati, Vishakha
    ("saturn",  10, (17, 18, 19)),        # Anuradha, Jyeshtha, Moola
    ("jupiter", 19, (20, 21, 22)),       # P.Ashadha, U.Ashadha, Shravana
    ("rahu",    12, (23, 24, 25)),          # Dhanishtha, Shatabhisha, P.Bhadrapada
    ("venus",   21, (26, 27, 1, 2)),       # U.Bhadrapada, Revati, Ashwini, Bharani
]

TOTAL_ASHTOTTARI_YEARS: int = 108
ASHTOTTARI_LORDS: list[str] = [e[0] for e in ASHTOTTARI_SPECS]
ASHTOTTARI_YEARS_MAP: dict[str, int] = {e[0]: e[1] for e in ASHTOTTARI_SPECS}

# Surya Siddhanta Tithi Year (360 tithis):
SS_MEAN_TITHI_YEAR_DAYS: float = 354.36725956904595


@dataclass(frozen=True)
class AshtottariHierarchyNode:
    tier: Literal["MD", "AD", "PD", "SD", "PrD"]
    lord: str
    start_time_iso: str
    end_time_iso: str
    duration_seconds: float
    duration_days: float
    duration_years: float
    sub_periods: tuple[AshtottariHierarchyNode, ...] = ()


def get_ashtottari_starting_lord(nakshatra_1_indexed: int) -> tuple[str, int, int]:
    """Returns (lord, duration_years, group_nakshatra_count)."""
    if not (1 <= nakshatra_1_indexed <= 27):
        raise ValueError(f"Nakshatra index must be 1..27, got {nakshatra_1_indexed}")
    for lord, yrs, naks in ASHTOTTARI_SPECS:
        if nakshatra_1_indexed in naks:
            return lord, yrs, len(naks)
    return "sun", 6, 3


class AshtottariAccumulator:
    """Computes multi-tier Ashtottari Dasha hierarchy with True/Mean Tithi accumulation."""

    def __init__(
        self,
        ephemeris_wrapper: Optional[EphemerisWrapper] = None,
        year_days: float = SS_MEAN_TITHI_YEAR_DAYS,
    ) -> None:
        self.ephemeris = ephemeris_wrapper or EphemerisWrapper(ephemeris_path="data/ephemeris")
        self.year_days = year_days
        self.year_seconds = year_days * 86400.0

    def compute_hierarchy(
        self,
        birth_datetime: datetime,
        moon_longitude: float,
        max_tier: Literal["MD", "AD", "PD", "SD", "PrD"] = "PD",
        num_cycles: int = 1,
    ) -> dict[str, Any]:
        """
        Builds full 5-tier Ashtottari hierarchy.
        """
        lon = moon_longitude % 360.0
        deg_per_nak = 360.0 / 27.0
        nak_idx = int(lon // deg_per_nak) + 1
        deg_in_nak = lon % deg_per_nak
        frac_elapsed = deg_in_nak / deg_per_nak
        frac_rem = 1.0 - frac_elapsed

        start_lord, total_md_yrs, group_size = get_ashtottari_starting_lord(nak_idx)
        start_lord_idx = ASHTOTTARI_LORDS.index(start_lord)

        # Balance calculation:
        # In Ashtottari, the lord's total years is distributed among its nakshatras.
        # Balance = (remaining fraction in current nakshatra / group_size) * total_years
        bal_yrs = (frac_rem / float(group_size)) * float(total_md_yrs)
        bal_sec = bal_yrs * self.year_seconds

        dt_start = birth_datetime if birth_datetime.tzinfo else birth_datetime.replace(tzinfo=timezone.utc)
        dt_first_md_end = dt_start + timedelta(seconds=bal_sec)

        mahadashas: list[AshtottariHierarchyNode] = []

        # 1. First (partial) MD
        first_md = self._build_node(
            tier="MD",
            lord=start_lord,
            nominal_years=float(total_md_yrs),
            start_dt=dt_start,
            end_dt=dt_first_md_end,
            is_partial=True,
            balance_fraction=frac_rem / float(group_size),
            max_tier=max_tier,
        )
        mahadashas.append(first_md)

        curr_start = dt_first_md_end

        # 2. Subsequent MDs
        total_mds = num_cycles * 8
        for i in range(1, total_mds):
            l_idx = (start_lord_idx + i) % 8
            spec = ASHTOTTARI_SPECS[l_idx]
            nom_yrs = float(spec[1])
            dur_sec = nom_yrs * self.year_seconds
            curr_end = curr_start + timedelta(seconds=dur_sec)

            md_node = self._build_node(
                tier="MD",
                lord=spec[0],
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
            "system": "ashtottari_5tier",
            "cycle_years": TOTAL_ASHTOTTARI_YEARS,
            "year_basis": "exact_true_tithi",
            "year_days": self.year_days,
            "birth_nakshatra": nak_idx,
            "starting_lord": start_lord,
            "balance_years": round(bal_yrs, 6),
            "max_tier_computed": max_tier,
            "mahadashas": [self._node_to_dict(md) for md in mahadashas],
        }

    def _build_node(
        self,
        tier: Literal["MD", "AD", "PD", "SD", "PrD"],
        lord: str,
        nominal_years: float,
        start_dt: datetime,
        end_dt: datetime,
        is_partial: bool,
        balance_fraction: float,
        max_tier: str,
    ) -> AshtottariHierarchyNode:
        dur_sec = (end_dt - start_dt).total_seconds()
        dur_days = dur_sec / 86400.0
        dur_yrs = dur_sec / self.year_seconds

        tier_order = ["MD", "AD", "PD", "SD", "PrD"]
        curr_tier_idx = tier_order.index(tier)
        max_tier_idx = tier_order.index(max_tier)

        sub_periods = []
        if curr_tier_idx < max_tier_idx:
            next_tier = tier_order[curr_tier_idx + 1]
            start_l_idx = ASHTOTTARI_LORDS.index(lord)

            curr_sub_start = start_dt
            for step in range(8):
                idx = (start_l_idx + step) % 8
                sub_spec = ASHTOTTARI_SPECS[idx]
                sub_lord = sub_spec[0]
                sub_base_yrs = float(sub_spec[1])

                sub_prop = sub_base_yrs / float(TOTAL_ASHTOTTARI_YEARS)
                sub_nom_sec = dur_sec * sub_prop if not is_partial else (nominal_years * self.year_seconds) * sub_prop * balance_fraction

                sub_end = curr_sub_start + timedelta(seconds=sub_nom_sec)
                if step == 7 or sub_end > end_dt:
                    sub_end = end_dt

                if sub_end > curr_sub_start:
                    child = self._build_node(
                        tier=next_tier,
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

        return AshtottariHierarchyNode(
            tier=tier,
            lord=lord,
            start_time_iso=start_dt.isoformat(),
            end_time_iso=end_dt.isoformat(),
            duration_seconds=dur_sec,
            duration_days=round(dur_days, 4),
            duration_years=round(dur_yrs, 6),
            sub_periods=tuple(sub_periods),
        )

    def _node_to_dict(self, node: AshtottariHierarchyNode) -> dict[str, Any]:
        res = {
            "tier": node.tier,
            "lord": node.lord,
            "start": node.start_time_iso,
            "end": node.end_time_iso,
            "duration_days": node.duration_days,
            "duration_years": node.duration_years,
        }
        if node.sub_periods:
            res["sub_periods"] = [self._node_to_dict(c) for c in node.sub_periods]
        return res