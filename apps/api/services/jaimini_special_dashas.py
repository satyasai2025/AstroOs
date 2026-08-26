"""
AstroOS — Jaimini Special Dashas (Shoola Dasha & Mandooka Dasha)
Classical Reference: Jaimini Upadesha Sutras (Adhyaya 2, Pada 1), BPHS (Ch. 50-52).
Implements:
  1. Shoola Dasha: 9-year fixed signs dasha for longevity, health, and maraka timing.
  2. Mandooka Dasha: Frog-leap sign dasha for high-impact transformation, career, and D11 timing.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional, Tuple

from apps.api.domain.horoscope import D1Chart
from apps.api.domain.jaimini import JaiminiDashaPeriod, JaiminiDashaResult
from apps.api.services.jaimini_shared import (
    house_count,
    is_movable,
    is_fixed,
    is_dual,
    rashi_at,
    rashi_index,
    signs_from,
    whole_sign_house_rashi,
)
from packages.shared.constants import SIGN_LORDS

_RASHI_ORDER = (
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
)

_MANDOOKA_MOVABLE_SEQUENCE = (0, 3, 6, 9, 1, 4, 7, 10, 2, 5, 8, 11)
_MANDOOKA_FIXED_SEQUENCE = (0, 2, 4, 6, 8, 10, 1, 3, 5, 7, 9, 11)


class ShoolaDashaEngine:
    """
    Computes Shoola Dasha (9-year fixed sign periods for longevity and maraka analysis).
    """

    def compute(self, chart: D1Chart, start_date: date, max_depth: int = 2) -> JaiminiDashaResult:
        lagna_rashi = chart.ascendant.rashi.lower() if chart.ascendant else "aries"
        lagna_idx = rashi_index(lagna_rashi)

        # 7th house rashi
        h7_idx = (lagna_idx + 6) % 12
        h7_rashi = rashi_at(h7_idx)

        # Determine stronger of 1st and 7th: More planets in sign -> stronger
        p_count_1 = sum(1 for p in chart.planets if p.rashi.lower() == lagna_rashi)
        p_count_7 = sum(1 for p in chart.planets if p.rashi.lower() == h7_rashi)

        seed_rashi = lagna_rashi if p_count_1 >= p_count_7 else h7_rashi
        seed_idx = rashi_index(seed_rashi)

        # Odd signs: direct progression; Even signs: reverse progression
        is_odd = (seed_idx % 2 == 0)  # 0=Aries (odd), 1=Taurus (even)...
        step = 1 if is_odd else -1

        mahadashas: list[JaiminiDashaPeriod] = []
        cur_date = start_date
        year_days = 365.25
        mahadasha_days = int(9 * year_days)  # Exactly 9 years per sign in Shoola Dasha

        for i in range(12):
            sign_idx = (seed_idx + (i * step)) % 12
            r_name = rashi_at(sign_idx)
            m_end_date = cur_date + timedelta(days=mahadasha_days)

            sub_periods: list[JaiminiDashaPeriod] = []
            if max_depth >= 2:
                # 12 antardashas within 9 years = 9 months each (273.9 days)
                ad_days = mahadasha_days // 12
                ad_cur_date = cur_date
                ad_step = 1 if (sign_idx % 2 == 0) else -1
                for j in range(12):
                    ad_sign_idx = (sign_idx + (j * ad_step)) % 12
                    ad_r_name = rashi_at(ad_sign_idx)
                    ad_end_date = ad_cur_date + timedelta(days=ad_days) if j < 11 else m_end_date
                    sub_periods.append(JaiminiDashaPeriod(
                        rashi=ad_r_name,
                        start_date=ad_cur_date,
                        end_date=ad_end_date,
                        duration_days=(ad_end_date - ad_cur_date).days,
                        level=2,
                        sub_periods=(),
                    ))
                    ad_cur_date = ad_end_date

            mahadashas.append(JaiminiDashaPeriod(
                rashi=r_name,
                start_date=cur_date,
                end_date=m_end_date,
                duration_days=mahadasha_days,
                level=1,
                sub_periods=tuple(sub_periods),
            ))
            cur_date = m_end_date

        return JaiminiDashaResult(
            system="shoola",
            lagna_rashi=lagna_rashi,
            periods=tuple(mahadashas),
            max_depth=max_depth,
            total_cycle_years=108,
        )


class MandookaDashaEngine:
    """
    Computes Mandooka Dasha (Frog-jump sign periods for high-impact transformation & D11 Rudramsha).
    """

    def compute(self, chart: D1Chart, start_date: date, max_depth: int = 2) -> JaiminiDashaResult:
        lagna_rashi = chart.ascendant.rashi.lower() if chart.ascendant else "aries"
        lagna_idx = rashi_index(lagna_rashi)

        # Sequence sequence based on sign type
        if is_movable(lagna_rashi):
            sequence_offsets = _MANDOOKA_MOVABLE_SEQUENCE
        elif is_fixed(lagna_rashi):
            sequence_offsets = _MANDOOKA_FIXED_SEQUENCE
        else:
            # Dual signs: 1st, 4th, 7th, 10th then next trines
            sequence_offsets = (0, 3, 6, 9, 1, 4, 7, 10, 2, 5, 8, 11)

        mahadashas: list[JaiminiDashaPeriod] = []
        cur_date = start_date
        year_days = 365.25

        for offset in sequence_offsets:
            sign_idx = (lagna_idx + offset) % 12
            r_name = rashi_at(sign_idx)

            # Duration in Mandooka: Variable based on lord distance (7 to 12 years, standard 8 years)
            lord = SIGN_LORDS[r_name]
            lord_positions = [p for p in chart.planets if p.planet == lord]
            if lord_positions:
                dist = house_count(r_name, lord_positions[0].rashi)
                dur_years = dist if dist > 0 else 12
            else:
                dur_years = 8

            dur_days = int(dur_years * year_days)
            m_end_date = cur_date + timedelta(days=dur_days)

            sub_periods: list[JaiminiDashaPeriod] = []
            if max_depth >= 2:
                ad_days = dur_days // 12
                ad_cur_date = cur_date
                for j_offset in sequence_offsets:
                    ad_sign_idx = (sign_idx + j_offset) % 12
                    ad_r_name = rashi_at(ad_sign_idx)
                    ad_end_date = ad_cur_date + timedelta(days=ad_days) if j_offset != sequence_offsets[-1] else m_end_date
                    sub_periods.append(JaiminiDashaPeriod(
                        rashi=ad_r_name,
                        start_date=ad_cur_date,
                        end_date=ad_end_date,
                        duration_days=(ad_end_date - ad_cur_date).days,
                        level=2,
                        sub_periods=(),
                    ))
                    ad_cur_date = ad_end_date

            mahadashas.append(JaiminiDashaPeriod(
                rashi=r_name,
                start_date=cur_date,
                end_date=m_end_date,
                duration_days=dur_days,
                level=1,
                sub_periods=tuple(sub_periods),
            ))
            cur_date = m_end_date

        total_years = sum(p.duration_days for p in mahadashas) // int(year_days)

        return JaiminiDashaResult(
            system="mandooka",
            lagna_rashi=lagna_rashi,
            periods=tuple(mahadashas),
            max_depth=max_depth,
            total_cycle_years=total_years,
        )
