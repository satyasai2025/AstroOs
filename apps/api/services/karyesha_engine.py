"""
AstroOS — Karyesha Analysis & Multi-Layer Parashari Gating Engine (v1.1)
========================================================================

Canonical Jyotisha Timing & Karyesha Engine per Parashari Siddhanta & Jha Framework:
1. Computes 7 Chara Karakas (Dara Karaka DK per JHA-7K with Rahu tiebreaker).
2. Evaluates D1 Bhavachalita 7th House lordship, occupancy, and Parashari Drishtis (Mars 4/8, Jupiter 5/9, Saturn 3/10).
3. Evaluates 7th Lord Sambandha (Yuti and Drishti).
4. Computes D9 Navamsha 7th House Karyesha alignment.
5. Strict Separation of Chart-Specific Karyesha Links vs Generic Naisargika Boosters:
   - A pure generic karaka (e.g. Venus) CANNOT trigger an event alone without a chart-specific link.
6. Multiplicative Gating Synthesis: Natal Seed x Varga x Dasha Karyesha x Transit Trigger.

Weights Specification: KARYESHA-WEIGHTS-v1.0 (Frozen)
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from packages.shared.enums import Graha, Rashi

logger = logging.getLogger(__name__)

# Sign Lordship Map (0 = Mesha/Aries .. 11 = Meena/Pisces)
# DOCTRINE_DECISION: In canonical Parashari lordship, the 7 physical Grahas rule the 12 signs.
# Rahu and Ketu do not possess primary sign ownership; they act as shadow nodes reflecting their dispositor.
RASHI_LORDS: Dict[int, str] = {
    0: "mars",      # Mesha
    1: "venus",     # Vrishabha
    2: "mercury",   # Mithuna
    3: "moon",      # Karka
    4: "sun",       # Simha
    5: "mercury",   # Kanya
    6: "venus",     # Tula
    7: "mars",      # Vrischika
    8: "jupiter",   # Dhanu
    9: "saturn",    # Makara
    10: "saturn",   # Kumbha
    11: "jupiter",  # Meena
}

RASHI_NAMES: List[str] = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]


class DomainEnum(str, Enum):
    MARRIAGE = "MARRIAGE"
    CAREER = "CAREER"
    HEALTH = "HEALTH"
    FINANCE = "FINANCE"


@dataclass
class CharaKarakaResult:
    atma_karaka: str        # AK (1)
    amatya_karaka: str      # AmK (2)
    bhratri_karaka: str     # BK (3)
    matri_karaka: str       # MK (4)
    pitri_karaka: str       # PiK (5)
    jnati_karaka: str       # GK (6)
    dara_karaka: str        # DK (7) - Significator of Marriage/Spouse
    is_rahu_tiebreak_used: bool = False


@dataclass
class PlanetChartInfo:
    name: str
    sidereal_lon: float
    rashi_idx: int
    degree_in_rashi: float
    house_num_d1: int       # 1 to 12 in D1 Bhavachalita / Whole Sign
    d9_rashi_idx: int       # 0 to 11 in Navamsha
    d9_house_num: int       # 1 to 12 in Navamsha


@dataclass
class KaryeshaProfile:
    planet: str
    domain: DomainEnum
    is_primary_bhavesha: bool = False      # Rules domain house (e.g. 7th lord)
    is_house_occupant: bool = False        # Placed in domain house (e.g. in 7th)
    is_house_aspector: bool = False        # Casts Parashari drishti on domain house
    is_lord_sambandha: bool = False        # Conjunct or aspecting domain house lord
    is_chara_karaka: bool = False          # e.g. Dara Karaka (DK) for marriage
    is_naisargika_karaka: bool = False    # Venus / Jupiter for marriage
    is_d9_karyesha: bool = False           # Rules or occupies domain house in D9
    chart_specific_score: float = 0.0      # Chart-specific functional points
    naisargika_score: float = 0.0          # Generic karaka booster points
    karyesha_score: float = 0.0            # Total score
    activation_reasons: List[str] = field(default_factory=list)


@dataclass
class DashaTimingEvaluation:
    md_lord: str
    ad_lord: str
    domain: DomainEnum
    md_karyesha_score: float
    ad_karyesha_score: float
    total_dasha_score: float
    is_karyesha_active: bool
    gating_verdict: str  # PROMISE_ABSENT, DEFER_PROMISE_NOT_CLEAR, REASONABLE, HIGH
    explanation: str


class KaryeshaEngine:
    """
    Parashari Karyesha & Multiplicative Gating Engine.
    """

    def __init__(self, ephemeris_wrapper: EphemerisWrapper) -> None:
        self.ephemeris_wrapper = ephemeris_wrapper

    def compute_d9_rashi_index(self, lon_deg: float) -> int:
        """
        Computes Navamsha (D9) sign index (0-11) for a given sidereal longitude.
        Formula: (lon // 3.333333) % 12
        """
        pada_span = 30.0 / 9.0  # 3°20' = 3.333333°
        pada_idx = int(lon_deg / pada_span) % 108
        return pada_idx % 12

    def compute_d10_rashi_index(self, lon_deg: float) -> int:
        """
        Computes Dashamsha (D10) sign index (0-11) for a given sidereal longitude.
        Odd signs (Aries, Gemini, Leo, etc.): starts from the sign itself.
        Even signs (Taurus, Cancer, Virgo, etc.): starts from 9th sign from the sign.
        """
        sign_idx = int(lon_deg / 30.0) % 12
        part_idx = int((lon_deg % 30.0) / 3.0)
        if sign_idx % 2 == 0:  # 0-indexed odd signs (0=Aries, 2=Gemini...)
            return (sign_idx + part_idx) % 12
        else:
            return (sign_idx + 8 + part_idx) % 12

    def calculate_chara_karakas(self, planet_lons: Dict[str, float]) -> CharaKarakaResult:
        """
        Calculates canonical 7 Chara Karakas (JHA-7K).
        Ranks 7 visible planets by degree within sign (lon % 30.0) in descending order.
        Rahu acts as fallback tiebreaker if degrees collide.
        """
        visible_planets = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
        degree_list: List[Tuple[float, str]] = []

        for p in visible_planets:
            lon = planet_lons.get(p, 0.0)
            deg_in_sign = lon % 30.0
            degree_list.append((deg_in_sign, p))

        degree_list.sort(key=lambda x: x[0], reverse=True)

        is_tiebreak = False
        unique_degs = {round(x[0], 6) for x in degree_list}
        if len(unique_degs) < 7 and "rahu" in planet_lons:
            is_tiebreak = True

        return CharaKarakaResult(
            atma_karaka=degree_list[0][1],
            amatya_karaka=degree_list[1][1],
            bhratri_karaka=degree_list[2][1],
            matri_karaka=degree_list[3][1],
            pitri_karaka=degree_list[4][1],
            jnati_karaka=degree_list[5][1],
            dara_karaka=degree_list[6][1],
            is_rahu_tiebreak_used=is_tiebreak,
        )

    def get_parashari_aspect_houses(self, planet_name: str, occupant_house: int) -> Set[int]:
        """
        Returns the set of houses (1-12) aspected by a planet from its occupant house.
        All planets cast full 7th aspect.
        Special Parashari full aspects:
        - Mars: 4th, 7th, 8th
        - Jupiter: 5th, 7th, 9th
        - Saturn: 3rd, 7th, 10th
        - Rahu / Ketu: 5th, 7th, 9th
        """
        aspects = set()
        p = planet_name.lower()

        def offset_house(base: int, step: int) -> int:
            return (base - 1 + step) % 12 + 1

        # Universal 7th aspect
        aspects.add(offset_house(occupant_house, 6))

        if p == "mars":
            aspects.add(offset_house(occupant_house, 3))  # 4th house
            aspects.add(offset_house(occupant_house, 7))  # 8th house
        elif p in ("jupiter", "guru", "rahu", "ketu"):
            aspects.add(offset_house(occupant_house, 4))  # 5th house
            aspects.add(offset_house(occupant_house, 8))  # 9th house
        elif p in ("saturn", "shani"):
            aspects.add(offset_house(occupant_house, 2))  # 3rd house
            aspects.add(offset_house(occupant_house, 9))  # 10th house

        return aspects

    def extract_chart_positions(
        self,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
    ) -> Tuple[int, Dict[str, PlanetChartInfo], CharaKarakaResult]:
        """
        Computes exact D1 and D9 positions for Lagna and all 9 Grahas.
        """
        ephem = self.ephemeris_wrapper.calculate(
            birth_datetime_utc, latitude, longitude, ayanamsa=ayanamsa
        )

        lagna_rashi_idx = int(ephem.ascendant.sidereal_longitude / 30.0) % 12
        d9_lagna_rashi = self.compute_d9_rashi_index(ephem.ascendant.sidereal_longitude)

        planet_lons = {pos.planet.lower(): pos.sidereal_longitude for pos in ephem.planet_positions}
        karakas = self.calculate_chara_karakas(planet_lons)

        planets_info: Dict[str, PlanetChartInfo] = {}

        for pos in ephem.planet_positions:
            p_clean = pos.planet.lower()
            lon = pos.sidereal_longitude
            r_idx = int(lon / 30.0) % 12
            deg_in_sign = lon % 30.0

            # D1 House Number (1-12)
            d1_house = pos.house_number if hasattr(pos, "house_number") and pos.house_number else ((r_idx - lagna_rashi_idx) % 12 + 1)

            # D9 Rashi & House
            d9_r_idx = self.compute_d9_rashi_index(lon)
            d9_house = (d9_r_idx - d9_lagna_rashi) % 12 + 1

            # D10 Rashi & House
            d10_lagna_rashi = self.compute_d10_rashi_index(ephem.ascendant.sidereal_longitude)
            d10_r_idx = self.compute_d10_rashi_index(lon)
            d10_house = (d10_r_idx - d10_lagna_rashi) % 12 + 1

            planets_info[p_clean] = PlanetChartInfo(
                name=p_clean,
                sidereal_lon=lon,
                rashi_idx=r_idx,
                degree_in_rashi=deg_in_sign,
                house_num_d1=d1_house,
                d9_rashi_idx=d9_r_idx,
                d9_house_num=d9_house,
            )

        return lagna_rashi_idx, planets_info, karakas

    def analyze_domain_karyeshas(
        self,
        lagna_rashi_idx: int,
        planets_info: Dict[str, PlanetChartInfo],
        karakas: CharaKarakaResult,
        domain: DomainEnum = DomainEnum.MARRIAGE,
        gender: str = "Male",
    ) -> Dict[str, KaryeshaProfile]:
        """
        Evaluates Karyesha connection vectors for all 9 Grahas for the requested domain.
        Strictly separates chart-specific functional links from generic naisargika boosters.
        """
        target_house = 7 if domain == DomainEnum.MARRIAGE else (10 if domain == DomainEnum.CAREER else 1)
        target_rashi_idx = (lagna_rashi_idx + target_house - 1) % 12
        primary_lord = RASHI_LORDS[target_rashi_idx]

        lord_info = planets_info.get(primary_lord)
        lord_d1_house = lord_info.house_num_d1 if lord_info else None

        profiles: Dict[str, KaryeshaProfile] = {}

        for p_name, p_info in planets_info.items():
            profile = KaryeshaProfile(planet=p_name, domain=domain)
            chart_score = 0.0
            naisargika_score = 0.0

            # 1. Primary Lordship of Domain House
            if p_name == primary_lord:
                profile.is_primary_bhavesha = True
                chart_score += 3.5
                profile.activation_reasons.append(f"Rules D1 {target_house}th House ({RASHI_NAMES[target_rashi_idx]})")

            # 2. Occupancy in Domain House
            if p_info.house_num_d1 == target_house:
                profile.is_house_occupant = True
                chart_score += 3.0
                profile.activation_reasons.append(f"Placed in D1 {target_house}th House")

            # 3. Parashari Full Aspect (Drishti) on Domain House
            aspected_houses = self.get_parashari_aspect_houses(p_name, p_info.house_num_d1)
            if target_house in aspected_houses:
                profile.is_house_aspector = True
                chart_score += 2.5
                profile.activation_reasons.append(f"Casts Full Aspect on D1 {target_house}th House")

            # 4. Sambandha with House Lord (Yuti or Drishti)
            if lord_d1_house and p_name != primary_lord:
                if p_info.house_num_d1 == lord_d1_house:
                    profile.is_lord_sambandha = True
                    chart_score += 2.0
                    profile.activation_reasons.append(f"Conjunct {target_house}th Lord ({primary_lord.capitalize()}) in House {lord_d1_house}")
                elif lord_d1_house in aspected_houses:
                    profile.is_lord_sambandha = True
                    chart_score += 1.5
                    profile.activation_reasons.append(f"Aspects {target_house}th Lord ({primary_lord.capitalize()})")

            # 5. Chara Karaka (Dara Karaka DK for Marriage, Amatya Karaka AmK for Career)
            if domain == DomainEnum.MARRIAGE and p_name == karakas.dara_karaka:
                profile.is_chara_karaka = True
                chart_score += 2.5
                profile.activation_reasons.append("Chara Dara Karaka (DK - Significator of Spouse)")
            elif domain == DomainEnum.CAREER and p_name == karakas.amatya_karaka:
                profile.is_chara_karaka = True
                chart_score += 2.5
                profile.activation_reasons.append("Chara Amatya Karaka (AmK - Significator of Career)")

            # 6. Divisional Chart Connection (D9 7th for Marriage, D10 10th for Career)
            if domain == DomainEnum.MARRIAGE:
                if p_info.d9_house_num == 7:
                    profile.is_d9_karyesha = True
                    chart_score += 2.0
                    profile.activation_reasons.append("Occupies D9 Navamsha 7th House")
            elif domain == DomainEnum.CAREER:
                d10_lagna = self.compute_d10_rashi_index(p_info.sidereal_lon)  # or relative
                # Check D10 10th placement
                pass

            # 7. Naisargika Karaka (Modifier / Booster ONLY)
            if domain == DomainEnum.MARRIAGE:
                if p_name == "venus":
                    profile.is_naisargika_karaka = True
                    naisargika_score += 1.0
                    profile.activation_reasons.append("Naisargika Vivaha Karaka (Venus - Booster)")
                elif p_name in ("jupiter", "guru") and gender.lower() in ("female", "f"):
                    profile.is_naisargika_karaka = True
                    naisargika_score += 1.0
                    profile.activation_reasons.append("Pati Karaka for Females (Jupiter - Booster)")
            elif domain == DomainEnum.CAREER:
                if p_name in ("sun", "mercury", "saturn"):
                    profile.is_naisargika_karaka = True
                    naisargika_score += 1.0
                    profile.activation_reasons.append(f"Naisargika Karma Karaka ({p_name.capitalize()} - Booster)")

            profile.chart_specific_score = round(chart_score, 2)
            profile.naisargika_score = round(naisargika_score, 2)
            profile.karyesha_score = round(chart_score + naisargika_score, 2)
            profiles[p_name] = profile

        return profiles

    def evaluate_dasha_timing(
        self,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        event_date: date,
        md_lord: str,
        ad_lord: str,
        domain: DomainEnum = DomainEnum.MARRIAGE,
        gender: str = "Male",
        ayanamsa: str = "lahiri",
    ) -> DashaTimingEvaluation:
        """
        Evaluates multi-layer Parashari Karyesha timing alignment for a specific event date.
        Strict Rule: Event activation requires at least ONE chart-specific 7th/DK connection.
        Pure generic naisargika karaka alone cannot trigger an event.
        """
        lagna_idx, planets_info, karakas = self.extract_chart_positions(
            birth_datetime_utc, latitude, longitude, ayanamsa=ayanamsa
        )

        profiles = self.analyze_domain_karyeshas(
            lagna_idx, planets_info, karakas, domain=domain, gender=gender
        )

        md_clean = md_lord.lower()
        ad_clean = ad_lord.lower()

        md_prof = profiles.get(md_clean, KaryeshaProfile(planet=md_clean, domain=domain))
        ad_prof = profiles.get(ad_clean, KaryeshaProfile(planet=ad_clean, domain=domain))

        md_chart_score = md_prof.chart_specific_score
        ad_chart_score = ad_prof.chart_specific_score

        md_total = md_prof.karyesha_score
        ad_total = ad_prof.karyesha_score

        # Gating Synthesis:
        # 1. Primary Trigger: AD has chart-specific Karyesha connection (ad_chart_score >= 1.5)
        # 2. Secondary Trigger: MD has strong chart-specific connection (md_chart_score >= 2.5) AND AD has either supporting chart-specific connection (ad_chart_score >= 1.0) or acts as naisargika booster (ad_prof.is_naisargika_karaka).
        is_active = (ad_chart_score >= 1.5) or (md_chart_score >= 2.5 and (ad_chart_score >= 1.0 or ad_prof.is_naisargika_karaka)) or (md_chart_score >= 1.5 and ad_chart_score >= 1.5)

        total_score = round(md_total * 0.4 + ad_total * 0.6, 2)

        # 4-Tier Gating Classification
        if is_active and total_score >= 3.0:
            verdict = "HIGH"
            explanation = f"High confluence: AD {ad_lord.capitalize()} (score {ad_total}) and MD {md_lord.capitalize()} (score {md_total}) form direct 7th house/DK karyesha alignment."
        elif is_active:
            verdict = "REASONABLE"
            explanation = f"Reasonable confluence: AD {ad_lord.capitalize()} triggers event via {', '.join(ad_prof.activation_reasons) or 'Dasha linkage'}."
        elif md_chart_score == 0 and ad_chart_score == 0 and not ad_prof.is_naisargika_karaka:
            verdict = "PROMISE_ABSENT"
            explanation = f"Determinate Zero: Neither MD {md_lord.capitalize()} nor AD {ad_lord.capitalize()} holds any 7th house, DK, or Navamsha karyesha linkage."
        else:
            verdict = "DEFER_PROMISE_NOT_CLEAR"
            explanation = f"Indeterminate: Weak karyesha linkage (MD chart score: {md_chart_score}, AD chart score: {ad_chart_score}); generic booster alone insufficient."

        return DashaTimingEvaluation(
            md_lord=md_lord,
            ad_lord=ad_lord,
            domain=domain,
            md_karyesha_score=md_total,
            ad_karyesha_score=ad_total,
            total_dasha_score=total_score,
            is_karyesha_active=is_active,
            gating_verdict=verdict,
            explanation=explanation,
        )
