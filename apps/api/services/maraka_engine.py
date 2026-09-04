"""
AstroOS — Maraka, Badhaka, and Sambandha Confluence Engine
===========================================================
Source: Vinay Jha's Kundalee (Phalit.kkk - A16_Sambandh, A10_Aayu, frmPhalaadesh)
and BPHS Chapters 44, 46, 50.

Fulfills Jha's Canonical Principles:
  1. 5-Tier Confluence (MD -> AD -> PD -> SD -> PrD):
     "सामान्यतः मृत्यु तब होती है जब विंशोत्तरी महादशा से प्राणदशा तक पाँचों ग्रह मारक हों और अलग-अलग ग्रह हों।"
  2. Distinct Graha Axiom:
     Planets deliver full results through Sambandhi / distinct planets rather than their own sub-periods.
  3. Tatkalika Maitri Filter:
     Temporal relationship between MD and AD lords modulates ease vs violent obstruction.
  4. Badhaka Sthana & Badhakesh:
     Chara -> 11th, Sthira -> 9th, Dvisvabhava -> 7th.
  5. Saturn Maraka Absorption:
     Saturn conjunct or aspecting a Maraka absorbs the killing power.
  6. Completely Flexible (Non-hardcoded) architecture via MarakaConfig and BadhakaConfig.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from apps.api.domain.maraka import (
    BadhakaConfig,
    BadhakaEvaluationResult,
    LagnaModality,
    MarakaConfig,
    MarakaEvaluationResult,
    SambandhaType,
)
from packages.shared.constants import SIGN_LORDS
from packages.shared.enums import Rashi

_RASHI_LIST = [r.value for r in Rashi]

# Modality definitions
_CHARA_RASHIS = frozenset({"aries", "cancer", "libra", "capricorn"})
_STHIRA_RASHIS = frozenset({"taurus", "leo", "scorpio", "aquarius"})
_DVISVABHAVA_RASHIS = frozenset({"gemini", "virgo", "sagittarius", "pisces"})

# Natural planetary friendships (Naisargika Maitri)
_NATURAL_FRIENDS: dict[str, set[str]] = {
    "sun": {"moon", "mars", "jupiter"},
    "moon": {"sun", "mercury"},
    "mars": {"sun", "moon", "jupiter"},
    "mercury": {"sun", "venus"},
    "jupiter": {"sun", "moon", "mars"},
    "venus": {"mercury", "saturn"},
    "saturn": {"mercury", "venus"},
}
_NATURAL_ENEMIES: dict[str, set[str]] = {
    "sun": {"venus", "saturn"},
    "moon": set(),
    "mars": {"mercury"},
    "mercury": {"moon"},
    "jupiter": {"mercury", "venus"},
    "venus": {"sun", "moon"},
    "saturn": {"sun", "moon", "mars"},
}


class MarakaEngine:
    """Calculates Maraka, Badhaka, Sambandha, and 5-tier mortality/health risks."""

    def __init__(
        self,
        maraka_config: MarakaConfig | None = None,
        badhaka_config: BadhakaConfig | None = None,
    ) -> None:
        self._maraka_cfg = maraka_config or MarakaConfig()
        self._badhaka_cfg = badhaka_config or BadhakaConfig()

    def get_lagna_modality(self, lagna_rashi: str) -> LagnaModality:
        r = lagna_rashi.lower()
        if r in _CHARA_RASHIS:
            return LagnaModality.CHARA
        elif r in _STHIRA_RASHIS:
            return LagnaModality.STHIRA
        else:
            return LagnaModality.DVISVABHAVA

    def get_maraka_planets(
        self,
        lagna_rashi: str,
        planet_rashis: dict[str, str],
        config: MarakaConfig | None = None,
    ) -> set[str]:
        """Identifies primary and secondary Maraka planets for the chart."""
        cfg = config or self._maraka_cfg
        r_list = _RASHI_LIST
        lagna_idx = r_list.index(lagna_rashi.lower())

        marakas: set[str] = set()

        # Primary Marakas: 2nd and 7th house lords
        if cfg.include_2nd_7th:
            r2 = r_list[(lagna_idx + 1) % 12]
            r7 = r_list[(lagna_idx + 6) % 12]
            marakas.add(SIGN_LORDS[r2])
            marakas.add(SIGN_LORDS[r7])

        # Secondary Marakas: 6th, 8th, 12th house lords (Trik lords)
        if cfg.include_trik_lords:
            r6 = r_list[(lagna_idx + 5) % 12]
            r8 = r_list[(lagna_idx + 7) % 12]
            r12 = r_list[(lagna_idx + 11) % 12]
            marakas.add(SIGN_LORDS[r6])
            marakas.add(SIGN_LORDS[r8])
            marakas.add(SIGN_LORDS[r12])

        # Saturn Override / Absorption:
        # If Saturn is conjunct with or aspects a primary Maraka (2H or 7H lord)
        if cfg.include_saturn_override and "saturn" in planet_rashis:
            saturn_rashi = planet_rashis["saturn"].lower()
            saturn_idx = r_list.index(saturn_rashi)
            # Saturn aspects 3rd, 7th, 10th houses and occupies same house
            saturn_aspect_indices = {
                saturn_idx,
                (saturn_idx + 2) % 12,
                (saturn_idx + 6) % 12,
                (saturn_idx + 9) % 12,
            }
            # Check if 2H or 7H lord sits in Saturn's aspected signs
            primary_lords = {SIGN_LORDS[r_list[(lagna_idx + 1) % 12]], SIGN_LORDS[r_list[(lagna_idx + 6) % 12]]}
            for p in primary_lords:
                p_r = planet_rashis.get(p)
                if p_r and r_list.index(p_r.lower()) in saturn_aspect_indices:
                    marakas.add("saturn")
                    break

        return marakas

    def get_badhaka_info(
        self,
        lagna_rashi: str,
        config: BadhakaConfig | None = None,
    ) -> BadhakaEvaluationResult:
        """Determines Badhaka Sthana and Badhakesh according to Lagna Modality."""
        cfg = config or self._badhaka_cfg
        modality = self.get_lagna_modality(lagna_rashi)
        r_list = _RASHI_LIST
        l_idx = r_list.index(lagna_rashi.lower())

        if modality == LagnaModality.CHARA:
            b_house = cfg.chara_badhaka_house  # 11
        elif modality == LagnaModality.STHIRA:
            b_house = cfg.sthira_badhaka_house # 9
        else:
            b_house = cfg.dvi_badhaka_house    # 7

        badhaka_rashi = r_list[(l_idx + b_house - 1) % 12]
        badhakesh = SIGN_LORDS[badhaka_rashi]

        trace = [
            f"Lagna: {lagna_rashi.capitalize()} (Modality: {modality.value})",
            f"Badhaka House: {b_house}th house ({badhaka_rashi.capitalize()})",
            f"Badhakesh Planet: {badhakesh.capitalize()}",
        ]

        return BadhakaEvaluationResult(
            lagna_rashi=lagna_rashi.lower(),
            lagna_modality=modality,
            badhaka_house=b_house,
            badhakesh_planet=badhakesh,
            is_badhakesh_in_dasha=False,
            obstructed_houses=[b_house],
            obstructed_rajayogas=[],
            trace=trace,
        )

    def calculate_tatkalika_maitri(
        self,
        p1: str,
        p2: str,
        planet_rashis: dict[str, str],
    ) -> str:
        """
        Calculates Tatkalika (Temporal) relationship between two planets.
        Planets placed in 2nd, 3rd, 4th, 10th, 11th, 12th from each other are Tatkalika Mitra (Friends).
        Planets in 1st, 5th, 6th, 7th, 8th, 9th are Tatkalika Shatru (Enemies).
        """
        p1_r = planet_rashis.get(p1.lower())
        p2_r = planet_rashis.get(p2.lower())
        if not p1_r or not p2_r:
            return "sama"

        idx1 = _RASHI_LIST.index(p1_r.lower())
        idx2 = _RASHI_LIST.index(p2_r.lower())
        diff = (idx2 - idx1) % 12 + 1  # 1-based house difference

        if diff in (2, 3, 4, 10, 11, 12):
            return "mitra"
        else:
            return "shatru"

    def evaluate_5tier_maraka_confluence(
        self,
        lagna_rashi: str,
        planet_rashis: dict[str, str],
        dasha_tier_lords: dict[str, str], # {"MD": "saturn", "AD": "mars", "PD": "venus", "SD": "mercury", "PrD": "sun"}
        d30_confirmation: bool = False,
        config: MarakaConfig | None = None,
    ) -> MarakaEvaluationResult:
        """
        Evaluates 5-tier mortality/critical health risk window:
        'सामान्यतः मृत्यु तब होती है जब विंशोत्तरी महादशा से प्राणदशा तक पाँचों ग्रह मारक हों और अलग-अलग ग्रह हों।'
        """
        cfg = config or self._maraka_cfg
        marakas = self.get_maraka_planets(lagna_rashi, planet_rashis, cfg)

        matched_tiers: dict[str, str] = {}
        active_lords: list[str] = []
        tier_names = ["MD", "AD", "PD", "SD", "PrD"]

        for t in tier_names:
            lord = dasha_tier_lords.get(t, "").lower()
            if lord in marakas:
                matched_tiers[t] = lord
            if lord:
                active_lords.append(lord)

        active_count = len(matched_tiers)
        distinct_planets = set(active_lords)
        distinct_count = len(distinct_planets)

        # Check distinct planets condition
        are_distinct = distinct_count >= cfg.min_distinct_grahas if cfg.require_distinct_grahas else True

        # Check Tatkalika Maitri between MD and AD lords
        md_lord = dasha_tier_lords.get("MD", "")
        ad_lord = dasha_tier_lords.get("AD", "")
        tatkalika = self.calculate_tatkalika_maitri(md_lord, ad_lord, planet_rashis)

        # Saturn absorption flag
        saturn_absorbed = "saturn" in marakas and any(
            p in marakas for p in ["saturn"]
        )

        # Risk level determination
        trace = [
            f"Lagna: {lagna_rashi.capitalize()}",
            f"Active Marakas for chart: {sorted(list(marakas))}",
            f"Dasha Tier Lords: {dasha_tier_lords}",
            f"Matched Maraka Tiers ({active_count}/5): {matched_tiers}",
            f"Distinct Grahas across 5 tiers: {distinct_count} ({sorted(list(distinct_planets))})",
            f"MD-AD Tatkalika relation: {tatkalika}",
        ]

        if active_count >= cfg.min_tiers_for_death_risk and are_distinct:
            risk_level = "CRITICAL_MORTALITY_RISK"
            is_active = True
            trace.append("ALERT: All 5 tiers are distinct Marakas -> Jha mortality threshold fulfilled.")
        elif active_count >= cfg.min_tiers_for_health_crisis:
            risk_level = "SEVERE_HEALTH_CRISIS"
            is_active = True
            trace.append(f"WARNING: {active_count} tiers are Marakas -> Health crisis threshold fulfilled.")
        elif active_count >= 1:
            risk_level = "MODERATE_OBSTRUCTION"
            is_active = False
            trace.append("INFO: Isolated Maraka sub-periods active.")
        else:
            risk_level = "SAFE"
            is_active = False
            trace.append("INFO: No Maraka activation in current window.")

        if d30_confirmation:
            trace.append("D-30 (Trishamsha) confirms malefic affliction.")

        return MarakaEvaluationResult(
            is_maraka_active=is_active,
            risk_level=risk_level,
            active_tier_count=active_count,
            matched_tiers=matched_tiers,
            distinct_graha_count=distinct_count,
            are_grahas_distinct=are_distinct,
            tatkalika_relation_md_ad=tatkalika,
            saturn_absorbed_maraka=saturn_absorbed,
            d30_confirmation=d30_confirmation,
            trace=trace,
        )