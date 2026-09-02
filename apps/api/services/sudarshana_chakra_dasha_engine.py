"""
AstroOS — Sudarshana Chakra Dasha (SCD) Engine
==============================================

Canonical Specification from Vinay Ji's 78-Document Knowledge Base:
Source: docs/wikidot_canonical_knowledge/03_chakras_and_special_systems/sudarshana-chakra.md
        docs/wikidot_canonical_knowledge/05_natal_case_studies/amitabh-bachchan.md
        docs/wikidot_canonical_knowledge/05_natal_case_studies/narendra-modi.md

Sudarshana Chakra Dasha (SCD) progresses through the horoscope sequentially:
- Annual Progression (Varsha): 1 house per year from Lagna, Sun, and Moon.
  - Year 1 (Age 0-1): House 1
  - Year 2 (Age 1-2): House 2
  - ... Year 12 (Age 11-12): House 12
  - Year 13 (Age 12-13): House 1 (Cycle 2)
- Monthly Sub-Progression (Masa): 1 house per solar month within the active year.
- Evaluates active houses simultaneously from:
  1. LK (Lagna Kundali)
  2. SK (Surya Kundali)
  3. CK (Chandra Kundali)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from apps.api.domain.horoscope import D1Chart
from apps.api.services.phalita_core.tphalit_core import (
    RASHI_LORDS,
    get_rashi_idx,
    HOUSE_PLACEMENT_WEIGHTS,
)


@dataclass(frozen=True)
class SCDLevelResult:
    """Active house and lord details for a single SCD reference point (LK, SK, or CK)."""
    reference_name: str     # "LK" / "SK" / "CK"
    ref_rashi_idx: int
    active_house_num: int   # [1 to 12]
    active_rashi_idx: int   # [0 to 11]
    active_lord: str
    occupants: tuple[str, ...]
    house_score: float      # [-1.0 to +1.0]


@dataclass(frozen=True)
class SudarshanaChakraDashaReport:
    """Complete Sudarshana Chakra Dasha assessment for a native at a given target date."""
    target_date: date
    native_age_years: float
    scd_cycle_number: int       # 1, 2, 3...
    annual_house_offset: int    # 1 to 12
    monthly_house_offset: int   # 1 to 12
    lk_annual: SCDLevelResult
    sk_annual: SCDLevelResult
    ck_annual: SCDLevelResult
    composite_scd_score: float  # [-1.0 to +1.0]
    active_themes: tuple[str, ...]
    is_amavasya_sc: bool


    @property
    def age_years(self) -> float:
        return self.native_age_years

    @property
    def active_house_from_lagna(self) -> int:
        return self.annual_house_offset

    @property
    def primary_theme(self) -> str:
        return self.active_themes[0] if self.active_themes else ""

    @property
    def house_significations(self) -> list[str]:
        return list(self.active_themes)



class SudarshanaChakraDashaEngine:
    """Deterministic Sudarshana Chakra Dasha calculation engine."""

    def compute_scd(
        self,
        natal_chart: D1Chart,
        birth_datetime: datetime,
        target_date: date,
    ) -> SudarshanaChakraDashaReport:
        """Compute the active SCD progression for a chart on a target date."""
        birth_date = birth_datetime.date()
        days_diff = (target_date - birth_date).days
        age_years = max(0.0, days_diff / 365.2422)

        cycle_num = int(age_years // 12) + 1
        annual_house = int(age_years % 12) + 1  # 1 to 12

        # Month offset within current year (approx 30.4375 days per solar month)
        days_in_cur_year = days_diff % 365.2422
        month_offset = int((days_in_cur_year / 365.2422) * 12) + 1

        lagna_rashi = get_rashi_idx(natal_chart.ascendant.rashi)
        p_map = {p.planet.lower(): p for p in natal_chart.planets}

        moon_p = p_map.get("moon")
        moon_rashi = get_rashi_idx(moon_p.rashi) if moon_p else lagna_rashi

        sun_p = p_map.get("sun")
        sun_rashi = get_rashi_idx(sun_p.rashi) if sun_p else lagna_rashi

        is_amavasya = (moon_rashi == sun_rashi)

        def eval_ref(ref_name: str, base_rashi: int) -> SCDLevelResult:
            act_rashi = (base_rashi + annual_house - 1) % 12
            act_lord = RASHI_LORDS.get(act_rashi, "")
            occ = tuple(p.planet.lower() for p in natal_chart.planets if get_rashi_idx(p.rashi) == act_rashi)
            score = HOUSE_PLACEMENT_WEIGHTS.get(annual_house, 0.0)
            return SCDLevelResult(
                reference_name=ref_name,
                ref_rashi_idx=base_rashi,
                active_house_num=annual_house,
                active_rashi_idx=act_rashi,
                active_lord=act_lord,
                occupants=occ,
                house_score=score,
            )

        lk = eval_ref("LK", lagna_rashi)
        sk = eval_ref("SK", sun_rashi)
        ck = eval_ref("CK", moon_rashi)

        if is_amavasya:
            comp_score = 0.5 * sk.house_score + 0.5 * ck.house_score
        else:
            comp_score = 0.34 * lk.house_score + 0.33 * sk.house_score + 0.33 * ck.house_score

        # Domain themes based on active house
        house_themes = {
            1: "Identity, physical body, new beginnings, vitality",
            2: "Accumulated wealth, family responsibilities, speech",
            3: "Courage, efforts, short travel, siblings, initiatives",
            4: "Mother, home, property, vehicles, emotional peace",
            5: "Intelligence, children, creative output, investments",
            6: "Overcoming obstacles, competition, debts, service",
            7: "Partnerships, public relationships, marriage, contracts",
            8: "Transformation, sudden shifts, unearned gains, longevity",
            9: "Dharma, higher wisdom, father, pilgrimage, fortune",
            10: "Career elevation, public status, authority, leadership",
            11: "Major financial gains, network growth, aspirations",
            12: "Expenses, foreign relocations, spiritual retreat, release",
        }

        themes = (house_themes.get(annual_house, "General development"),)

        return SudarshanaChakraDashaReport(
            target_date=target_date,
            native_age_years=age_years,
            scd_cycle_number=cycle_num,
            annual_house_offset=annual_house,
            monthly_house_offset=month_offset,
            lk_annual=lk,
            sk_annual=sk,
            ck_annual=ck,
            composite_scd_score=comp_score,
            active_themes=themes,
            is_amavasya_sc=is_amavasya,
        )
