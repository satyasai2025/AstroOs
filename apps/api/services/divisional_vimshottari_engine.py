"""
AstroOS — Divisional Vimshottari Dasha Engine
=============================================

Canonical Reference: docs/CANONICAL_PREDICTION_FRAMEWORK.md (Step 1 & Step 2)
Source: BPHS Dashaphala-adhyaya & Jha's "How To Make Correct Predictions"

Core Principle:
"Find out the five Vimshottari planets of D1 and relevant divisional.
Thereafter, compare the main strengths of Vimshottari planets of D1 and
relevant divisional."

This engine computes independent Vimshottari dasha sequences seeded for
specific Divisional (Varga) charts:
- D9  (Navamsha) — Marriage & Dharma
- D10 (Dashamsha) — Career, Power & Status
- D7  (Saptamsha) — Children & Progeny
- D4  (Chaturthamsha) — Property & Vehicles
- D24 (Chaturvimshamsha) — Higher Learning
- D30 (Trishamsha) — Disease, Crises & Misfortunes
- D12 (Dwadashamsha) — Parents & Ancestry
- D3  (Drekkana) — Siblings, Valour & Longevity
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from apps.api.domain.dasha import DashaPeriod, DashaTree
from apps.api.services.dasha_engine import (
    DashaEngine,
    _build_nakshatra_periods,
)
from apps.api.services.divisional_engine import (
    DivisionalEngine,
    compute_varga_sign,
)
from apps.api.services.ephemeris_wrapper import (
    EphemerisWrapper,
    longitude_to_nakshatra,
)
from packages.shared.constants import (
    DAYS_PER_JULIAN_YEAR,
    DEGREES_PER_NAKSHATRA,
    VIMSHOTTARI_DASHA_YEARS,
    VIMSHOTTARI_NAKSHATRA_LORDS,
    VIMSHOTTARI_SEQUENCE,
    VIMSHOTTARI_TOTAL_YEARS,
)


@dataclass(frozen=True)
class DivisionalDashaActiveLords:
    """Active Vimshottari lords for a divisional chart at a specific evaluation date."""
    varga_number: int
    evaluation_date: date
    mahadasha_lord: str
    antardasha_lord: str
    pratyantardasha_lord: str
    varga_code: str = ""
    target_date: Optional[date] = None
    md_start_date: Optional[date] = None
    md_end_date: Optional[date] = None
    ad_start_date: Optional[date] = None
    ad_end_date: Optional[date] = None
    sookshma_lord: Optional[str] = None
    praana_lord: Optional[str] = None


class DivisionalVimshottariEngine:
    """
    Computes Vimshottari Dasha trees for arbitrary Divisional (Varga) charts.
    """

    def __init__(self, ephemeris_wrapper: Optional[EphemerisWrapper] = None) -> None:
        self._wrapper = ephemeris_wrapper or EphemerisWrapper(ephemeris_path="data/ephemeris")
        self._dasha_engine = DashaEngine(self._wrapper)

    def compute_varga_moon_longitude(
        self,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        varga_number: int,
    ) -> float:
        """
        Calculates the effective longitude of the Moon projected into the target Varga.
        
        Formula:
          varga_span = 30.0 / varga_number
          portion_in_sign = moon_d1_lon % 30.0
          sub_div_index = int(portion_in_sign / varga_span)
          remainder_in_sub = (portion_in_sign % varga_span) * varga_number
          
          varga_sign_idx = compute_varga_sign(moon_d1_lon, varga_number)
          varga_longitude = (varga_sign_idx * 30.0) + remainder_in_sub
        """
        calc_res = self._wrapper.calculate(dt=birth_datetime, latitude=latitude, longitude=longitude)
        moon_pos = next(p for p in calc_res.planet_positions if p.planet.lower() == "moon")
        d1_lon = moon_pos.sidereal_longitude

        if varga_number == 1:
            return d1_lon

        from packages.shared.constants import KALACHAKRA_SAVYA_SIGNS
        varga_code = f"D{varga_number}" if isinstance(varga_number, int) else str(varga_number)
        varga_rashi, varga_rashi_deg = compute_varga_sign(varga_code, d1_lon)


        rashi_name_clean = varga_rashi.lower()
        if rashi_name_clean in KALACHAKRA_SAVYA_SIGNS:
            varga_sign_idx = KALACHAKRA_SAVYA_SIGNS.index(rashi_name_clean)
        else:
            varga_sign_idx = 0

        varga_lon = (float(varga_sign_idx) * 30.0 + varga_rashi_deg) % 360.0
        return varga_lon


    def compute_divisional_vimshottari(
        self,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        varga_number: int,
        max_depth: int = 3,
        num_cycles: int = 1,
    ) -> DashaTree:
        """
        Generates full Vimshottari Dasha tree for the specified Divisional chart.
        """
        varga_moon_lon = self.compute_varga_moon_longitude(
            birth_datetime=birth_datetime,
            latitude=latitude,
            longitude=longitude,
            varga_number=varga_number,
        )

        nak_info = longitude_to_nakshatra(varga_moon_lon)
        start_lord = nak_info.lord.lower()
        fraction_elapsed = nak_info.degree_in_nakshatra / DEGREES_PER_NAKSHATRA
        total_lord_years = VIMSHOTTARI_DASHA_YEARS[start_lord]
        remaining_fraction = 1.0 - fraction_elapsed
        balance_years = remaining_fraction * float(total_lord_years)
        balance_days = round(balance_years * DAYS_PER_JULIAN_YEAR)


        b_date = birth_datetime.date()
        first_end_date = b_date + timedelta(days=balance_days)

        start_seq_idx = VIMSHOTTARI_SEQUENCE.index(start_lord)
        mahadashas: list[DashaPeriod] = []

        # 1. First (partial) Mahadasha
        first_subs = _build_nakshatra_periods(
            start_lord=start_lord,
            sequence=VIMSHOTTARI_SEQUENCE,
            period_years=VIMSHOTTARI_DASHA_YEARS,
            total_years=VIMSHOTTARI_TOTAL_YEARS,
            start_date=b_date,
            end_date=first_end_date,
            level=2,
            max_depth=max_depth,
        )
        mahadashas.append(
            DashaPeriod(
                lord=start_lord,
                start_date=b_date,
                end_date=first_end_date,
                duration_days=balance_days,
                level=1,
                sub_periods=first_subs,
            )
        )

        # 2. Subsequent Mahadashas
        current_start = first_end_date
        total_mds = len(VIMSHOTTARI_SEQUENCE) * num_cycles
        for i in range(1, total_mds):
            lord = VIMSHOTTARI_SEQUENCE[(start_seq_idx + i) % len(VIMSHOTTARI_SEQUENCE)]
            md_years = VIMSHOTTARI_DASHA_YEARS[lord]
            md_days = round(md_years * DAYS_PER_JULIAN_YEAR)
            current_end = current_start + timedelta(days=md_days)

            subs = _build_nakshatra_periods(
                start_lord=lord,
                sequence=VIMSHOTTARI_SEQUENCE,
                period_years=VIMSHOTTARI_DASHA_YEARS,
                total_years=VIMSHOTTARI_TOTAL_YEARS,
                start_date=current_start,
                end_date=current_end,
                level=2,
                max_depth=max_depth,
            )
            mahadashas.append(
                DashaPeriod(
                    lord=lord,
                    start_date=current_start,
                    end_date=current_end,
                    duration_days=md_days,
                    level=1,
                    sub_periods=subs,
                )
            )
            current_start = current_end

        return DashaTree(
            system=f"Vimshottari_D{varga_number}",
            birth_date=b_date,
            trigger_planet=start_lord,
            trigger_nakshatra=nak_info.nakshatra,
            trigger_nakshatra_number=nak_info.nakshatra_number,
            mahadashas=tuple(mahadashas),
            max_depth=max_depth,
            total_cycle_years=VIMSHOTTARI_TOTAL_YEARS,
        )

    def get_active_lords_at_date(
        self,
        tree: DashaTree,
        target_date: date,
        varga_number: int = 1,
    ) -> DivisionalDashaActiveLords:
        """
        Locates the running MD, AD, PD lords in the divisional dasha tree at target_date.
        """
        mahadashas = getattr(tree, "mahadashas", getattr(tree, "periods", ()))
        active_md = None
        for md in mahadashas:
            if md.contains(target_date):
                active_md = md
                break

        if not active_md and mahadashas:
            active_md = mahadashas[-1]


        active_ad = None
        for ad in active_md.sub_periods:
            if ad.contains(target_date):
                active_ad = ad
                break
        if not active_ad and active_md.sub_periods:
            active_ad = active_md.sub_periods[-1]

        active_pd = None
        if active_ad and active_ad.sub_periods:
            for pd in active_ad.sub_periods:
                if pd.contains(target_date):
                    active_pd = pd
                    break
            if not active_pd and active_ad.sub_periods:
                active_pd = active_ad.sub_periods[-1]

        md_start = active_md.start_date if active_md else target_date
        md_end = active_md.end_date if active_md else target_date
        ad_start = active_ad.start_date if active_ad else md_start
        ad_end = active_ad.end_date if active_ad else md_end

        return DivisionalDashaActiveLords(
            varga_number=varga_number,
            varga_code=f"D{varga_number}",
            evaluation_date=target_date,
            target_date=target_date,
            mahadasha_lord=active_md.lord if active_md else "Sun",
            antardasha_lord=active_ad.lord if active_ad else (active_md.lord if active_md else "Sun"),
            pratyantardasha_lord=active_pd.lord if active_pd else (active_ad.lord if active_ad else (active_md.lord if active_md else "Sun")),
            md_start_date=md_start,
            md_end_date=md_end,
            ad_start_date=ad_start,
            ad_end_date=ad_end,
        )
