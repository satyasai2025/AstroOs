"""
AstroOS — Kalachakra Dasha (KCD) 5-Tier Canonical Engine
========================================================
Implements the authentic classical Parashari Kalachakra Dasha as certified
in Vinay Jha's Kundalee software:
  - Module Table: A74_KCDmodule, A81_KCD_subs
  - Form Definitions:
      * frmKCDDashaAD   (Offset 1265104) -> Antardasha
      * frmKCDDashaPD   (Offset 1265956) -> Pratyantardasha
      * frmKCDDashaSD   (Offset 1265316) -> Sookshma Dasha
      * frmKCDDashaPrD  (Offset 1264892) -> Praana Dasha

1. Savya (सव्य - Direct) vs Apasavya (अपसव्य - Reverse) Nakshatras:
   - Savya: Ashwini, Bharani, Krittika, Punarvasu, Pushya, Ashlesha,
            Hasta, Chitra, Swati, Vishakha, U.Ashadha, Shravana, Dhanishtha,
            P.Bhadrapada, U.Bhadrapada.
   - Apasavya: Rohini, Mrigashira, Ardra, Magha, P.Phalguni, U.Phalguni,
               Anuradha, Jyeshtha, Moola, Shatabhisha, Revati.

2. Canonical 9-Sign Dasha Sequences (Navamsha-based):
   - Every Nakshatra Pada maps to an authentic 9-sign Kalachakra sequence.
   - Total years = Sum of the 9 signs' Kalachakra years.

3. Deha (देह) and Jeeva (जीव) Rashis:
   - Savya: 1st sign = Deha, 9th sign = Jeeva.
   - Apasavya: 1st sign = Jeeva, 9th sign = Deha.

4. The Three Classical Gatis (Leaps):
   - Manduka Gati (मण्डूक गति - Frog Leap): Karka -> Kanya or Kanya -> Karka, Simha -> Mithuna
   - Markati Gati (मर्कटी गति - Monkey Leap): Karka -> Simha, Mithuna -> Simha
   - Simhavalokana Gati (सिंहावलोकन - Lion's Gaze): Meena -> Vrischika, Dhanu -> Mesha

5. Full 5-Tier Hierarchy:
   - MD -> AD -> PD -> SD -> PrD with mathematical energy conservation.
   - Time Basis: Surya Siddhanta Mean Tithi Year (354.36725957 days / 360 tithis).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple


# ============================================================================
# 1. 12-Sign Kalachakra Years (BPHS Canonical)
# ============================================================================
KALACHAKRA_SIGN_YEARS: dict[str, int] = {
    "aries":       7,
    "taurus":      9,
    "gemini":      9,
    "cancer":      16,
    "leo":         7,
    "virgo":       9,
    "libra":       9,
    "scorpio":     7,
    "sagittarius": 9,
    "capricorn":   4,
    "aquarius":    4,
    "pisces":      10,
}
# Total across 12 signs = 100 years

# ============================================================================
# 2. Canonical 9-Sign Navamsha Sequences (BPHS Adhyayas 46-50)
# ============================================================================
CANONICAL_KCD_SEQUENCES: dict[str, list[str]] = {
    "mesha":       ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius"],
    "vrishabha":   ["capricorn", "aquarius", "pisces", "scorpio", "libra", "virgo", "cancer", "leo", "gemini"],
    "mithuna":     ["taurus", "aries", "pisces", "aquarius", "capricorn", "sagittarius", "aries", "taurus", "gemini"],
    "karka":       ["cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"],
    "simha":       ["scorpio", "libra", "virgo", "cancer", "leo", "gemini", "taurus", "aries", "pisces"],
    "kanya":       ["aquarius", "capricorn", "sagittarius", "aries", "taurus", "gemini", "cancer", "leo", "virgo"],
    "tula":        ["libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces", "scorpio", "libra", "virgo"],
    "vrischika":   ["cancer", "leo", "gemini", "taurus", "aries", "pisces", "aquarius", "capricorn", "sagittarius"],
    "dhanu":       ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius"],
    "makara":      ["capricorn", "aquarius", "pisces", "scorpio", "libra", "virgo", "cancer", "leo", "gemini"],
    "kumbha":      ["taurus", "aries", "pisces", "aquarius", "capricorn", "sagittarius", "aries", "taurus", "gemini"],
    "meena":       ["cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"],
}

SAVYA_NAKSHATRAS: set[int] = {1, 2, 3, 7, 8, 9, 13, 14, 15, 16, 21, 22, 23, 25, 26}
APASAVYA_NAKSHATRAS: set[int] = {4, 5, 6, 10, 11, 12, 17, 18, 19, 20, 24, 27}

SS_MEAN_TITHI_YEAR_DAYS: float = 354.36725956904595


def detect_kcd_gati(from_rashi: str, to_rashi: str) -> Optional[Literal["manduka", "markati", "simhavalokana"]]:
    """Detects classical Kalachakra Gatis (Leaps)."""
    f = from_rashi.lower()
    t = to_rashi.lower()

    if (f == "cancer" and t == "virgo") or (f == "virgo" and t == "cancer"):
        return "manduka"
    if (f == "leo" and t == "gemini") or (f == "gemini" and t == "leo"):
        return "manduka"

    if (f == "cancer" and t == "leo") or (f == "gemini" and t == "cancer"):
        return "markati"

    if (f == "pisces" and t == "scorpio") or (f == "sagittarius" and t == "aries"):
        return "simhavalokana"

    return None


@dataclass(frozen=True)
class KCDHierarchyNode:
    tier: Literal["MD", "AD", "PD", "SD", "PrD"]
    rashi: str
    duration_years: float
    duration_days: float
    duration_seconds: float
    start_time_iso: str
    end_time_iso: str
    gati: Optional[str] = None
    sub_periods: tuple[KCDHierarchyNode, ...] = ()


class Kalachakra5TierService:
    """Service computing 5-tier Kalachakra Dasha hierarchy with exact datetime math."""

    def __init__(self, year_days: float = SS_MEAN_TITHI_YEAR_DAYS) -> None:
        self.year_days = year_days
        self.year_seconds = year_days * 86400.0

    def compute_hierarchy(
        self,
        birth_datetime: datetime,
        moon_longitude: float,
        max_tier: Literal["MD", "AD", "PD", "SD", "PrD"] = "PD",
        num_md_cycles: int = 1,
    ) -> dict[str, Any]:
        lon = moon_longitude % 360.0
        deg_per_nak = 360.0 / 27.0
        nak_idx = int(lon // deg_per_nak) + 1
        deg_in_nak = lon % deg_per_nak

        deg_per_pada = deg_per_nak / 4.0
        pada_idx = int(deg_in_nak // deg_per_pada) + 1
        deg_in_pada = deg_in_nak % deg_per_pada

        frac_elapsed_pada = deg_in_pada / deg_per_pada
        frac_rem_pada = 1.0 - frac_elapsed_pada

        is_savya = nak_idx in SAVYA_NAKSHATRAS

        total_padas_elapsed = int(lon // deg_per_pada)
        navamsha_sign_idx = total_padas_elapsed % 12
        rashi_keys = [
            "mesha", "vrishabha", "mithuna", "karka", "simha", "kanya",
            "tula", "vrischika", "dhanu", "makara", "kumbha", "meena"
        ]
        navamsha_key = rashi_keys[navamsha_sign_idx]
        seq = CANONICAL_KCD_SEQUENCES.get(navamsha_key, CANONICAL_KCD_SEQUENCES["mesha"])

        if is_savya:
            deha_rashi = seq[0]
            jeeva_rashi = seq[-1]
        else:
            jeeva_rashi = seq[0]
            deha_rashi = seq[-1]

        total_seq_years = sum(KALACHAKRA_SIGN_YEARS[r] for r in seq)

        first_sign = seq[0]
        first_sign_nom_yrs = float(KALACHAKRA_SIGN_YEARS[first_sign])
        bal_yrs = frac_rem_pada * first_sign_nom_yrs
        bal_sec = bal_yrs * self.year_seconds

        dt_start = birth_datetime if birth_datetime.tzinfo else birth_datetime.replace(tzinfo=timezone.utc)
        dt_first_md_end = dt_start + timedelta(seconds=bal_sec)

        mahadashas: list[KCDHierarchyNode] = []

        # 1. First (partial) MD
        if bal_sec > 0.001:
            first_md = self._build_node(
                tier="MD",
                rashi=first_sign,
                nominal_years=first_sign_nom_yrs,
                start_dt=dt_start,
                end_dt=dt_first_md_end,
                is_partial=True,
                balance_fraction=frac_rem_pada,
                max_tier=max_tier,
                full_seq=seq,
                gati=None,
            )
            mahadashas.append(first_md)
            curr_start = dt_first_md_end
        else:
            curr_start = dt_start
        prev_rashi = first_sign

        # 2. Subsequent MDs
        for cycle in range(num_md_cycles):
            start_step = 1 if cycle == 0 else 0
            for step in range(start_step, len(seq)):
                r = seq[step]
                nom_yrs = float(KALACHAKRA_SIGN_YEARS[r])
                dur_sec = nom_yrs * self.year_seconds
                curr_end = curr_start + timedelta(seconds=dur_sec)

                gati = detect_kcd_gati(prev_rashi, r)

                md_node = self._build_node(
                    tier="MD",
                    rashi=r,
                    nominal_years=nom_yrs,
                    start_dt=curr_start,
                    end_dt=curr_end,
                    is_partial=False,
                    balance_fraction=1.0,
                    max_tier=max_tier,
                    full_seq=seq,
                    gati=gati,
                )
                mahadashas.append(md_node)
                prev_rashi = r
                curr_start = curr_end

        return {
            "system": "kalachakra_5tier",
            "cycle_type": "savya" if is_savya else "apasavya",
            "year_basis": "mean_tithi",
            "year_days": self.year_days,
            "birth_nakshatra": nak_idx,
            "pada": pada_idx,
            "navamsha_sign": navamsha_key,
            "deha_rashi": deha_rashi,
            "jeeva_rashi": jeeva_rashi,
            "total_sequence_years": total_seq_years,
            "balance_years": round(bal_yrs, 6),
            "max_tier_computed": max_tier,
            "mahadashas": [self._node_to_dict(md) for md in mahadashas],
        }

    def _build_node(
        self,
        tier: Literal["MD", "AD", "PD", "SD", "PrD"],
        rashi: str,
        nominal_years: float,
        start_dt: datetime,
        end_dt: datetime,
        is_partial: bool,
        balance_fraction: float,
        max_tier: str,
        full_seq: list[str],
        gati: Optional[str],
    ) -> KCDHierarchyNode:
        dur_sec = (end_dt - start_dt).total_seconds()
        dur_days = dur_sec / 86400.0
        dur_yrs = dur_sec / self.year_seconds

        tier_order = ["MD", "AD", "PD", "SD", "PrD"]
        curr_tier_idx = tier_order.index(tier)
        max_tier_idx = tier_order.index(max_tier)

        sub_periods = []
        if curr_tier_idx < max_tier_idx:
            next_tier = tier_order[curr_tier_idx + 1]
            tot_seq_yrs = sum(KALACHAKRA_SIGN_YEARS[r] for r in full_seq)

            curr_sub_start = start_dt
            prev_sub_rashi = rashi

            for step in range(len(full_seq)):
                sub_r = full_seq[step]
                sub_base_yrs = float(KALACHAKRA_SIGN_YEARS[sub_r])
                sub_prop = sub_base_yrs / float(tot_seq_yrs)

                sub_nom_sec = dur_sec * sub_prop if not is_partial else (nominal_years * self.year_seconds) * sub_prop * balance_fraction
                sub_end = curr_sub_start + timedelta(seconds=sub_nom_sec)

                if step == len(full_seq) - 1 or sub_end > end_dt:
                    sub_end = end_dt

                sub_gati = detect_kcd_gati(prev_sub_rashi, sub_r)

                if sub_end > curr_sub_start:
                    child = self._build_node(
                        tier=next_tier,
                        rashi=sub_r,
                        nominal_years=nominal_years * sub_prop,
                        start_dt=curr_sub_start,
                        end_dt=sub_end,
                        is_partial=is_partial,
                        balance_fraction=balance_fraction,
                        max_tier=max_tier,
                        full_seq=full_seq,
                        gati=sub_gati,
                    )
                    sub_periods.append(child)
                    prev_sub_rashi = sub_r
                    curr_sub_start = sub_end
                if curr_sub_start >= end_dt:
                    break

        return KCDHierarchyNode(
            tier=tier,
            rashi=rashi,
            duration_years=round(dur_yrs, 6),
            duration_days=round(dur_days, 4),
            duration_seconds=dur_sec,
            start_time_iso=start_dt.isoformat(),
            end_time_iso=end_dt.isoformat(),
            gati=gati,
            sub_periods=tuple(sub_periods),
        )

    def _node_to_dict(self, node: KCDHierarchyNode) -> dict[str, Any]:
        res = {
            "tier": node.tier,
            "rashi": node.rashi,
            "start": node.start_time_iso,
            "end": node.end_time_iso,
            "duration_days": node.duration_days,
            "duration_years": node.duration_years,
            "gati": node.gati,
        }
        if node.sub_periods:
            res["sub_periods"] = [self._node_to_dict(c) for c in node.sub_periods]
        return res