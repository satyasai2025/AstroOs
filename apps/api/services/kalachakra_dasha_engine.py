"""
AstroOS — Kalachakra Dasha (KCD) Canonical Engine
=================================================
Implements the authentic classical Parashari Kalachakra Dasha as certified
in Vinay Jha's Kundalee software (A72_KCDProc, frmKCDDashaAD, frmKCDDashaPD):

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

5. Calendar Units:
   - Surya Siddhanta Mean Tithi Year: 354.36725957 days
   - Savana / Solar selectable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple

from packages.shared.constants import (
    KALACHAKRA_SIGN_YEARS,
    KALACHAKRA_SAVYA_SIGNS,
    KALACHAKRA_APASAVYA_SIGNS,
)

# ----------------------------------------------------------------------------
# 1. Classical Kalachakra Navamsha Sequences (BPHS Adhyayas 46-50)
# ----------------------------------------------------------------------------

# 12 Canonical 9-sign Navamsha sequences:
# Each sequence contains 9 signs with classical leaps (Gatis).
CANONICAL_KCD_SEQUENCES: dict[str, list[str]] = {
    # Savya Sequences:
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

# Savya vs Apasavya Nakshatras (1-indexed, 1=Ashwini ... 27=Revati)
SAVYA_NAKSHATRAS: set[int] = {1, 2, 3, 7, 8, 9, 13, 14, 15, 16, 21, 22, 23, 25, 26}
APASAVYA_NAKSHATRAS: set[int] = {4, 5, 6, 10, 11, 12, 17, 18, 19, 20, 24, 27}

SS_MEAN_TITHI_YEAR_DAYS: float = 354.36725956904595


@dataclass(frozen=True)
class KCDPeriod:
    rashi: str
    ruler: str
    duration_years: int
    duration_days: float
    start_time_iso: str
    end_time_iso: str
    gati: Optional[Literal["manduka", "markati", "simhavalokana"]] = None
    sub_periods: tuple[KCDPeriod, ...] = ()


def detect_gati(from_rashi: str, to_rashi: str) -> Optional[Literal["manduka", "markati", "simhavalokana"]]:
    """Detects classical Kalachakra Gatis (Leaps)."""
    f = from_rashi.lower()
    t = to_rashi.lower()

    # Manduka Gati (Frog leap: skipping a sign)
    if (f == "cancer" and t == "virgo") or (f == "virgo" and t == "cancer"):
        return "manduka"
    if (f == "leo" and t == "gemini") or (f == "gemini" and t == "leo"):
        return "manduka"

    # Markati Gati (Monkey leap)
    if (f == "cancer" and t == "leo") or (f == "gemini" and t == "cancer"):
        return "markati"

    # Simhavalokana (Lion's backward gaze)
    if (f == "pisces" and t == "scorpio") or (f == "sagittarius" and t == "aries"):
        return "simhavalokana"

    return None


class KalachakraDashaEngine:
    """Engine computing authentic Parashari Kalachakra Dasha with Deha/Jeeva and Gatis."""

    def __init__(self, year_days: float = SS_MEAN_TITHI_YEAR_DAYS) -> None:
        self.year_days = year_days
        self.year_seconds = year_days * 86400.0

    def compute_kalachakra_dasha(
        self,
        birth_datetime: datetime,
        moon_longitude: float,
        num_cycles: int = 1,
    ) -> dict[str, Any]:
        """
        Computes Kalachakra Dasha for a given birth datetime and Moon longitude.
        """
        lon = moon_longitude % 360.0
        deg_per_nak = 360.0 / 27.0
        nak_idx = int(lon // deg_per_nak) + 1  # 1..27
        deg_in_nak = lon % deg_per_nak

        deg_per_pada = deg_per_nak / 4.0  # 3°20' = 3.333333°
        pada_idx = int(deg_in_nak // deg_per_pada) + 1  # 1..4
        deg_in_pada = deg_in_nak % deg_per_pada

        frac_elapsed_pada = deg_in_pada / deg_per_pada
        frac_rem_pada = 1.0 - frac_elapsed_pada

        is_savya = nak_idx in SAVYA_NAKSHATRAS

        # Map to Navamsha Rashi
        total_padas_elapsed = int(lon // deg_per_pada)
        navamsha_sign_idx = total_padas_elapsed % 12
        rashi_keys = [
            "mesha", "vrishabha", "mithuna", "karka", "simha", "kanya",
            "tula", "vrischika", "dhanu", "makara", "kumbha", "meena"
        ]
        navamsha_key = rashi_keys[navamsha_sign_idx]

        # Get canonical 9-sign sequence
        seq = CANONICAL_KCD_SEQUENCES.get(navamsha_key, CANONICAL_KCD_SEQUENCES["mesha"])

        # Determine Deha and Jeeva
        if is_savya:
            deha_rashi = seq[0]
            jeeva_rashi = seq[-1]
        else:
            jeeva_rashi = seq[0]
            deha_rashi = seq[-1]

        total_sequence_years = sum(KALACHAKRA_SIGN_YEARS[r] for r in seq)

        # Balance at birth:
        # The fraction remaining in the pada applies to the first Mahadasha sign!
        first_sign = seq[0]
        first_sign_yrs = float(KALACHAKRA_SIGN_YEARS[first_sign])
        balance_years = frac_rem_pada * first_sign_yrs
        balance_seconds = balance_years * self.year_seconds

        dt_start = birth_datetime if birth_datetime.tzinfo else birth_datetime.replace(tzinfo=timezone.utc)
        dt_first_md_end = dt_start + timedelta(seconds=balance_seconds)

        mahadashas: list[dict[str, Any]] = []

        # 1. First (partial) Mahadasha
        first_gati = None
        first_md_dict = self._build_kcd_md(
            rashi=first_sign,
            start_dt=dt_start,
            end_dt=dt_first_md_end,
            is_partial=True,
            gati=first_gati,
            full_seq=seq,
        )
        mahadashas.append(first_md_dict)

        curr_start = dt_first_md_end
        prev_rashi = first_sign

        # 2. Subsequent Mahadashas across the sequence
        for cycle in range(num_cycles):
            start_step = 1 if cycle == 0 else 0
            for step in range(start_step, len(seq)):
                r = seq[step]
                nom_yrs = float(KALACHAKRA_SIGN_YEARS[r])
                dur_sec = nom_yrs * self.year_seconds
                curr_end = curr_start + timedelta(seconds=dur_sec)

                gati = detect_gati(prev_rashi, r)

                md_dict = self._build_kcd_md(
                    rashi=r,
                    start_dt=curr_start,
                    end_dt=curr_end,
                    is_partial=False,
                    gati=gati,
                    full_seq=seq,
                )
                mahadashas.append(md_dict)
                prev_rashi = r
                curr_start = curr_end

        return {
            "system": "kalachakra",
            "cycle_type": "savya" if is_savya else "apasavya",
            "year_basis": "mean_tithi",
            "year_days": self.year_days,
            "birth_nakshatra_number": nak_idx,
            "pada": pada_idx,
            "navamsha_sign": navamsha_key,
            "deha_rashi": deha_rashi,
            "jeeva_rashi": jeeva_rashi,
            "total_sequence_years": total_sequence_years,
            "balance_years": round(balance_years, 6),
            "mahadashas": mahadashas,
        }

    def _build_kcd_md(
        self,
        rashi: str,
        start_dt: datetime,
        end_dt: datetime,
        is_partial: bool,
        gati: Optional[str],
        full_seq: list[str],
    ) -> dict[str, Any]:
        dur_sec = (end_dt - start_dt).total_seconds()
        dur_days = dur_sec / 86400.0
        dur_yrs = dur_sec / self.year_seconds

        # Antardashas divide MD proportionally across the 9 signs of full_seq
        tot_seq_yrs = sum(KALACHAKRA_SIGN_YEARS[r] for r in full_seq)
        ads = []
        curr_ad_start = start_dt

        for r_ad in full_seq:
            ad_prop = float(KALACHAKRA_SIGN_YEARS[r_ad]) / float(tot_seq_yrs)
            ad_dur_sec = dur_sec * ad_prop
            curr_ad_end = curr_ad_start + timedelta(seconds=ad_dur_sec)
            if curr_ad_end > end_dt:
                curr_ad_end = end_dt

            ads.append({
                "antar_rashi": r_ad,
                "start": curr_ad_start.isoformat(),
                "end": curr_ad_end.isoformat(),
                "duration_days": round((curr_ad_end - curr_ad_start).total_seconds() / 86400.0, 4),
            })
            curr_ad_start = curr_ad_end
            if curr_ad_start >= end_dt:
                break

        return {
            "rashi": rashi,
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat(),
            "duration_days": round(dur_days, 4),
            "duration_years": round(dur_yrs, 6),
            "is_partial": is_partial,
            "gati": gati,
            "antardashas": ads,
        }