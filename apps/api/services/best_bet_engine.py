"""
AstroOS — Best Bet 58-Point Marriage Matching Engine

Implements the "Best Bet" method by Jai Shaker:
- Group 1: Practical Compatibility (36 points)
  - Spiritual Harmony (12): Rajju, Nadi, Gana
  - Psychological Harmony (12): Moon/Nakshatra, Rashi, Rashi Lord, Tara
  - Physical & Material Harmony (12): Dina, Mahendra, Yoni, Vedha
- Group 2: Karmic Compatibility (12 points)
  - Mars Dosha (6): Mars position from Ascendant, Moon, Venus
  - Karmic Pattern (6): Sun, Moon, Venus, Saturn, Lagna dignity ratio
- Group 3: Future Compatibility (10 points)
  - Dasha Compatibility: Vimshottari Dasha overlap
  - Mutual Planetary Positions: Sun, Moon, Mars, Venus, Jupiter interactions

Final score out of 58. 60-70%+ considered good.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

logger = logging.getLogger(__name__)

# Which of the 3 groups count toward total_score/max_score/percentage per
# relationship type — the same "don't silently run the marriage formula
# under a different label" fix applied to AshtakootaEngine (see that
# module's RELATIONSHIP_KOOTA_APPLICABILITY docstring for the full
# rationale). Practical Compatibility (spiritual/psychological/physical
# harmony) is relevant to every relationship type, so it's always
# included. Karmic (Mars Dosha, karmic pattern) is specifically about
# marital harm and is dropped everywhere else. Future (Dasha overlap,
# mutual planetary interactions) says something about a business
# partnership's or a parent-child relationship's long-run trajectory, so
# it's kept there; dropped for friendship, which this method doesn't
# treat as a long-horizon commitment.
RELATIONSHIP_GROUP_APPLICABILITY: dict[str, set] = {
    "marriage": {"practical", "karmic", "future"},
    "business": {"practical", "future"},
    "friendship": {"practical"},
    "parent_child": {"practical", "future"},
}


class CompatibilityStatus(Enum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    AVERAGE = "Average"
    POOR = "Poor"


@dataclass
class BestBetResponse:
    """Full Best Bet compatibility result."""
    subject_name_a: str
    subject_name_b: str
    total_score: float
    max_score: float
    percentage: float
    verdict: str
    status: str

    # Group scores
    practical_score: float
    practical_max: float
    karmic_score: float
    karmic_max: float
    future_score: float
    future_max: float

    # Detailed breakdown
    spiritual_score: float
    spiritual_max: float
    psychological_score: float
    psychological_max: float
    physical_score: float
    physical_max: float
    mars_dosha_score: float
    mars_dosha_max: float
    karmic_pattern_score: float
    karmic_pattern_max: float
    dasha_score: float
    dasha_max: float
    mutual_planets_score: float
    mutual_planets_max: float

    # Sub-factor details
    sub_factors: List[dict] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    challenges: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class BestBetEngine:
    """
    Calculates Best Bet 58-point compatibility score.

    Note: Full implementation requires:
    - Complete nakshatra/rashi lookup tables
    - Dasha engine integration
    - Planet position data from horoscope engine

    This is a structured placeholder that defines the scoring framework
    and can be incrementally implemented as supporting data becomes available.
    """

    # Maximum scores per group and sub-factor
    MAX_PRACTICAL = 36.0
    MAX_KARMIC = 12.0
    MAX_FUTURE = 10.0
    MAX_TOTAL = 58.0

    MAX_SPIRITUAL = 12.0
    MAX_PSYCHOLOGICAL = 12.0
    MAX_PHYSICAL = 12.0
    MAX_MARS_DOSHA = 6.0
    MAX_KARMIC_PATTERN = 6.0
    MAX_DASHA = 5.0
    MAX_MUTUAL_PLANETS = 5.0

    @staticmethod
    def _get_nakshatra_index(nakshatra_name: str) -> int:
        """Get index in 27-nakshatra cycle. Returns -1 if not found."""
        nakshatras = [
            "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
            "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
            "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
            "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
            "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
        ]
        for i, n in enumerate(nakshatras):
            if nakshatra_name.lower().replace(" ", "").replace("_", "") == n.lower().replace(" ", ""):
                return i
        return -1

    @staticmethod
    def _get_rashi_index(rashi_name: str) -> int:
        """Get index in 12-rashi cycle. Returns -1 if not found."""
        rashis = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
        for i, r in enumerate(rashis):
            if rashi_name.lower().replace(" ", "").replace("_", "") == r.lower().replace(" ", ""):
                return i
        return -1

    @staticmethod
    def _calculate_rajju_score(nakshatra_a: int, nakshatra_b: int) -> tuple[float, str]:
        """
        Rajju (Nuptial Thread): Same group of 3 nakshatras = 2/2.
        Groups: (0-2), (3-5), (6-8), (9-11), (12-14), (15-17), (18-20), (21-23), (24-26)
        """
        if nakshatra_a < 0 or nakshatra_b < 0:
            return 0.0, "Nakshatra data unavailable"

        group_a = nakshatra_a // 3
        group_b = nakshatra_b // 3

        if group_a == group_b:
            return 2.0, "Same Rajju group — strong marital bond"
        else:
            return 0.0, "Different Rajju group"

    @staticmethod
    def _calculate_nadi_score(nakshatra_a: int, nakshatra_b: int) -> tuple[float, str]:
        """
        Nadi (Pulse/Health): Same nadi = 0/8, different = 8/8.
        Nadi groups: (0,8,16,24), (1,9,17,25), (2,10,18,26), (3,11,19), (4,12,20), (5,13,21), (6,14,22), (7,15,23)
        """
        if nakshatra_a < 0 or nakshatra_b < 0:
            return 0.0, "Nakshatra data unavailable"

        # 8 nadi groups based on nakshatra index mod 3 and other rules
        nadi_a = (nakshatra_a % 3) * 2 + (nakshatra_a // 9)
        nadi_b = (nakshatra_b % 3) * 2 + (nakshatra_b // 9)

        if nadi_a != nadi_b:
            return 8.0, "Different Nadi — health compatibility"
        else:
            return 0.0, "Same Nadi — health concerns"

    @staticmethod
    def _calculate_gana_score(nakshatra_a: int, nakshatra_b: int) -> tuple[float, str]:
        """
        Gana (Temperament): Deva=2, Manushya=1, Rakshasa=0.
        Same gana = 6/6. Deva-Rakshasa = 0/6. Others = 3-5/6 depending.
        """
        if nakshatra_a < 0 or nakshatra_b < 0:
            return 0.0, "Nakshatra data unavailable"

        def get_gana(idx: int) -> int:
            # Simplified: based on nakshatra group
            if idx < 6:
                return 1  # Manushya
            elif idx < 18:
                return 2  # Deva
            else:
                return 0  # Rakshasa

        gana_a = get_gana(nakshatra_a)
        gana_b = get_gana(nakshatra_b)

        if gana_a == gana_b:
            return 6.0, "Same Gana — temperament match"
        elif abs(gana_a - gana_b) == 1:
            return 5.0, "Compatible Gana"
        else:
            return 0.0, "Incompatible Gana (Deva-Rakshasa)"

    @staticmethod
    def _calculate_dina_score(nakshatra_a: int, nakshatra_b: int) -> tuple[float, str]:
        """
        Dina (Day): Based on nakshatra difference.
        """
        if nakshatra_a < 0 or nakshatra_b < 0:
            return 0.0, "Nakshatra data unavailable"

        diff = abs(nakshatra_b - nakshatra_a) % 27
        if diff == 0:
            return 3.0, "Same nakshatra — moderate"
        elif diff % 9 == 0:
            return 3.0, "Compatible Dina"
        else:
            return 1.0, "Neutral Dina"

    @staticmethod
    def _calculate_yoni_score(nakshatra_a: int, nakshatra_b: int) -> tuple[float, str]:
        """
        Yoni (Animal): Same yoni = 4/4, friendly = 3, neutral = 2, enemy = 0.
        """
        if nakshatra_a < 0 or nakshatra_b < 0:
            return 0.0, "Nakshatra data unavailable"

        # Simplified yoni mapping (actual has 14 yonis with relationships)
        yoni_map = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        yoni_a = yoni_map[nakshatra_a]
        yoni_b = yoni_map[nakshatra_b]

        if yoni_a == yoni_b:
            return 4.0, "Same Yoni — strong physical compatibility"
        elif (yoni_a - yoni_b) % 14 in [1, 13]:
            return 3.0, "Friendly Yoni"
        elif (yoni_a - yoni_b) % 14 in [2, 12]:
            return 2.0, "Neutral Yoni"
        else:
            return 0.0, "Incompatible Yoni"

    @staticmethod
    def _calculate_vedha_score(nakshatra_a: int, nakshatra_b: int) -> tuple[float, str]:
        """
        Vedha (Obstruction): Nakshatras that obstruct each other = 0/2.
        """
        if nakshatra_a < 0 or nakshatra_b < 0:
            return 0.0, "Nakshatra data unavailable"

        # Simplified: nakshatras 7 apart obstruct
        diff = abs(nakshatra_b - nakshatra_a) % 27
        if diff == 7 or diff == 20:
            return 0.0, "Vedha (obstruction) present"
        else:
            return 2.0, "No Vedha"

    @staticmethod
    def _calculate_mars_dosha_score(mars_house_a: int, moon_house_a: int, venus_house_a: int,
                                     mars_house_b: int, moon_house_b: int, venus_house_b: int) -> tuple[float, str]:
        """
        Mars Dosha: Mars in 1, 2, 4, 7, 8, 12 from Asc/Moon/Venus = dosha.
        Compare severity between partners. Matching dosha levels cancel.
        """
        dosha_houses = {1, 2, 4, 7, 8, 12}

        def count_dosha(mars_h: int, moon_h: int, venus_h: int) -> int:
            count = 0
            for ref in [mars_h, moon_h, venus_h]:
                if ((mars_h - ref) % 12) + 1 in dosha_houses:
                    count += 1
            return count

        dosha_a = count_dosha(mars_house_a, moon_house_a, venus_house_a)
        dosha_b = count_dosha(mars_house_b, moon_house_b, venus_house_b)

        if dosha_a == 0 and dosha_b == 0:
            return 6.0, "No Mars Dosha — excellent"
        elif dosha_a == dosha_b:
            return 6.0, f"Equal Mars Dosha (both level {dosha_a}) — cancels out"
        else:
            return 2.0, f"Mars Dosha mismatch (levels {dosha_a} vs {dosha_b})"

    @staticmethod
    def _calculate_karmic_pattern_score(
        sun_dignity_a: float, moon_dignity_a: float, venus_dignity_a: float,
        saturn_dignity_a: float, lagna_dignity_a: float,
        sun_dignity_b: float, moon_dignity_b: float, venus_dignity_b: float,
        saturn_dignity_b: float, lagna_dignity_b: float
    ) -> tuple[float, str]:
        """
        Karmic Pattern: Ratio of dignities between partners.
        Closer to 1:1 = better score.
        """
        avg_a = (sun_dignity_a + moon_dignity_a + venus_dignity_a + saturn_dignity_a + lagna_dignity_a) / 5
        avg_b = (sun_dignity_b + moon_dignity_b + venus_dignity_b + saturn_dignity_b + lagna_dignity_b) / 5

        if avg_a == 0 or avg_b == 0:
            return 3.0, "Insufficient dignity data"

        ratio = max(avg_a, avg_b) / min(avg_a, avg_b)
        if ratio < 1.3:
            return 6.0, "Karmic patterns well-aligned"
        elif ratio < 1.7:
            return 4.0, "Moderate karmic alignment"
        else:
            return 2.0, "Different karmic patterns"

    @staticmethod
    def _calculate_dasha_compatibility_score(dasha_overlap_pct: float) -> tuple[float, str]:
        """
        Dasha Compatibility: How much the Vimshottari dashas overlap favorably.
        """
        if dasha_overlap_pct > 0.7:
            return 5.0, "Strong dasha overlap — favorable future"
        elif dasha_overlap_pct > 0.4:
            return 3.0, "Moderate dasha overlap"
        else:
            return 1.0, "Limited dasha overlap"

    @staticmethod
    def _calculate_mutual_planets_score(
        sun_interaction: str, moon_interaction: str, mars_interaction: str,
        venus_interaction: str, jupiter_interaction: str
    ) -> tuple[float, str]:
        """
        Mutual planetary positions: aspect/conjunction strength.
        """
        score_map = {"excellent": 1.0, "good": 0.8, "neutral": 0.5, "poor": 0.2}
        total = sum(score_map.get(i, 0.5) for i in [sun_interaction, moon_interaction, mars_interaction, venus_interaction, jupiter_interaction])
        max_score = 5.0
        normalized = (total / max_score) * max_score

        if normalized >= 4.0:
            return normalized, "Excellent mutual planetary positions"
        elif normalized >= 3.0:
            return normalized, "Good mutual planetary positions"
        elif normalized >= 2.0:
            return normalized, "Neutral planetary interactions"
        else:
            return normalized, "Challenging planetary interactions"

    @classmethod
    def calculate(
        cls,
        subject_name_a: str,
        subject_name_b: str,
        # Nakshatra data
        nakshatra_a: str,
        nakshatra_b: str,
        rashi_a: str,
        rashi_b: str,
        # House positions for Mars dosha
        mars_house_a: int,
        moon_house_a: int,
        venus_house_a: int,
        mars_house_b: int,
        moon_house_b: int,
        venus_house_b: int,
        # Dignity data for karmic pattern
        sun_dignity_a: float = 5.0,
        moon_dignity_a: float = 5.0,
        venus_dignity_a: float = 5.0,
        saturn_dignity_a: float = 5.0,
        lagna_dignity_a: float = 5.0,
        sun_dignity_b: float = 5.0,
        moon_dignity_b: float = 5.0,
        venus_dignity_b: float = 5.0,
        saturn_dignity_b: float = 5.0,
        lagna_dignity_b: float = 5.0,
        # Dasha data
        dasha_overlap_pct: float = 0.5,
        # Mutual planet interactions
        sun_interaction: str = "neutral",
        moon_interaction: str = "neutral",
        mars_interaction: str = "neutral",
        venus_interaction: str = "neutral",
        jupiter_interaction: str = "neutral",
        relationship_type: str = "marriage",
    ) -> BestBetResponse:
        """
        Calculate Best Bet 58-point compatibility score.

        All parameters should be provided from actual chart data where available.
        Default values allow partial computation when some data is missing.
        """
        nakshatra_idx_a = cls._get_nakshatra_index(nakshatra_a)
        nakshatra_idx_b = cls._get_nakshatra_index(nakshatra_b)

        # Group 1: Practical Compatibility (36 points)
        # Spiritual Harmony (12)
        rajju_score, rajju_desc = cls._calculate_rajju_score(nakshatra_idx_a, nakshatra_idx_b)
        nadi_score, nadi_desc = cls._calculate_nadi_score(nakshatra_idx_a, nakshatra_idx_b)
        gana_score, gana_desc = cls._calculate_gana_score(nakshatra_idx_a, nakshatra_idx_b)
        spiritual_score = rajju_score + nadi_score + gana_score

        # Psychological Harmony (12)
        # Simplified: based on rashi and nakshatra compatibility
        rashi_idx_a = cls._get_rashi_index(rashi_a)
        rashi_idx_b = cls._get_rashi_index(rashi_b)
        rashi_diff = abs(rashi_idx_a - rashi_idx_b)
        if rashi_diff in [0, 3, 6, 9]:
            rashi_compat = 4.0
        elif rashi_diff in [1, 2, 4, 5, 7, 8]:
            rashi_compat = 3.0
        else:
            rashi_compat = 2.0

        nakshatra_diff = abs(nakshatra_idx_a - nakshatra_idx_b) % 27
        if nakshatra_diff in [0, 9, 18]:
            nakshatra_compat = 4.0
        elif nakshatra_diff in [3, 6, 12, 15, 21, 24]:
            nakshatra_compat = 3.0
        else:
            nakshatra_compat = 2.0

        psychological_score = min(rashi_compat + nakshatra_compat, 12.0)

        # Physical & Material Harmony (12)
        dina_score, _ = cls._calculate_dina_score(nakshatra_idx_a, nakshatra_idx_b)
        # Mahendra: nakshatras 1 apart or same pada = good
        if nakshatra_diff in [0, 1, 26]:
            mahendra_score = 2.0
        else:
            mahendra_score = 1.0
        yoni_score, _ = cls._calculate_yoni_score(nakshatra_idx_a, nakshatra_idx_b)
        vedha_score, _ = cls._calculate_vedha_score(nakshatra_idx_a, nakshatra_idx_b)

        physical_score = min(dina_score + mahendra_score + yoni_score + vedha_score, 12.0)
        practical_score = min(spiritual_score + psychological_score + physical_score, 36.0)

        # Group 2: Karmic Compatibility (12 points)
        mars_dosha_score, _ = cls._calculate_mars_dosha_score(
            mars_house_a, moon_house_a, venus_house_a,
            mars_house_b, moon_house_b, venus_house_b
        )
        karmic_pattern_score, _ = cls._calculate_karmic_pattern_score(
            sun_dignity_a, moon_dignity_a, venus_dignity_a, saturn_dignity_a, lagna_dignity_a,
            sun_dignity_b, moon_dignity_b, venus_dignity_b, saturn_dignity_b, lagna_dignity_b
        )
        karmic_score = min(mars_dosha_score + karmic_pattern_score, 12.0)

        # Group 3: Future Compatibility (10 points)
        dasha_score, _ = cls._calculate_dasha_compatibility_score(dasha_overlap_pct)
        mutual_planets_score, _ = cls._calculate_mutual_planets_score(
            sun_interaction, moon_interaction, mars_interaction,
            venus_interaction, jupiter_interaction
        )
        future_score = min(dasha_score + mutual_planets_score, 10.0)

        # Total — only groups relevant to this relationship type count
        # toward total_score/max_score/percentage; see
        # RELATIONSHIP_GROUP_APPLICABILITY's docstring for why.
        relationship_type = relationship_type if relationship_type in RELATIONSHIP_GROUP_APPLICABILITY else "marriage"
        applicable_groups = RELATIONSHIP_GROUP_APPLICABILITY[relationship_type]
        group_scores = {"practical": practical_score, "karmic": karmic_score, "future": future_score}
        group_maxes = {"practical": cls.MAX_PRACTICAL, "karmic": cls.MAX_KARMIC, "future": cls.MAX_FUTURE}
        total_score = sum(group_scores[g] for g in applicable_groups)
        max_score = sum(group_maxes[g] for g in applicable_groups)
        percentage = (total_score / max_score) * 100 if max_score else 0.0

        # Verdict
        relationship_label = {
            "marriage": "Marriage", "business": "Business Partnership",
            "friendship": "Friendship", "parent_child": "Parent-Child Relationship",
        }[relationship_type]
        if percentage >= 70:
            verdict = f"Excellent Match for {relationship_label}"
            status = CompatibilityStatus.EXCELLENT.value
        elif percentage >= 60:
            verdict = f"Good Match for {relationship_label}"
            status = CompatibilityStatus.GOOD.value
        elif percentage >= 50:
            verdict = f"Average Match for {relationship_label}"
            status = CompatibilityStatus.AVERAGE.value
        else:
            verdict = f"Poor Match for {relationship_label}"
            status = CompatibilityStatus.POOR.value

        # Build sub-factors — Practical's always included; Karmic's/Future's
        # only listed when their group applies to this relationship type.
        sub_factors = [
            {"name": "Rajju", "score": rajju_score, "max": 2.0, "description": rajju_desc},
            {"name": "Nadi", "score": nadi_score, "max": 8.0, "description": nadi_desc},
            {"name": "Gana", "score": gana_score, "max": 6.0, "description": gana_desc},
            {"name": "Rashi Compatibility", "score": rashi_compat, "max": 4.0, "description": "Rashi sign compatibility"},
            {"name": "Nakshatra Compatibility", "score": nakshatra_compat, "max": 4.0, "description": "Nakshatra star compatibility"},
            {"name": "Dina", "score": dina_score, "max": 3.0, "description": "Day compatibility"},
            {"name": "Mahendra", "score": mahendra_score, "max": 2.0, "description": "Mahendra factor"},
            {"name": "Yoni", "score": yoni_score, "max": 4.0, "description": "Physical compatibility"},
            {"name": "Vedha", "score": vedha_score, "max": 2.0, "description": "Obstruction check"},
        ]
        if "karmic" in applicable_groups:
            sub_factors += [
                {"name": "Mars Dosha", "score": mars_dosha_score, "max": 6.0, "description": "Mars affliction analysis"},
                {"name": "Karmic Pattern", "score": karmic_pattern_score, "max": 6.0, "description": "Karmic alignment"},
            ]
        if "future" in applicable_groups:
            sub_factors += [
                {"name": "Dasha Compatibility", "score": dasha_score, "max": 5.0, "description": "Dasha period overlap"},
                {"name": "Mutual Planets", "score": mutual_planets_score, "max": 5.0, "description": "Planetary interactions"},
            ]

        # Strengths and challenges
        strengths = []
        challenges = []

        if spiritual_score >= 10:
            strengths.append("Excellent spiritual harmony")
        if psychological_score >= 10:
            strengths.append("Strong psychological compatibility")
        if physical_score >= 10:
            strengths.append("Good physical and material harmony")
        if "karmic" in applicable_groups and mars_dosha_score >= 5:
            strengths.append("Low or balanced Mars Dosha")
        if "karmic" in applicable_groups and karmic_pattern_score >= 5:
            strengths.append("Aligned karmic patterns")
        if "future" in applicable_groups and dasha_score >= 4:
            strengths.append("Favorable dasha overlap")

        if spiritual_score < 6:
            challenges.append("Spiritual harmony needs attention")
        if psychological_score < 6:
            challenges.append("Psychological compatibility may need work")
        if physical_score < 6:
            challenges.append("Physical/material harmony concerns")
        if "karmic" in applicable_groups and mars_dosha_score < 3:
            challenges.append("Mars Dosha mismatch")
        if "karmic" in applicable_groups and karmic_pattern_score < 3:
            challenges.append("Different karmic patterns")
        if "future" in applicable_groups and dasha_score < 2:
            challenges.append("Limited dasha overlap")

        recommendations = [
            "Focus on areas with lower scores for relationship growth",
            "Consider traditional remedies for challenging factors",
            "Strengthen communication in weaker compatibility dimensions",
            "Regular relationship counseling can help bridge gaps",
        ]

        return BestBetResponse(
            subject_name_a=subject_name_a,
            subject_name_b=subject_name_b,
            total_score=total_score,
            max_score=max_score,
            percentage=round(percentage, 1),
            verdict=verdict,
            status=status,
            practical_score=practical_score,
            practical_max=cls.MAX_PRACTICAL,
            karmic_score=karmic_score,
            karmic_max=cls.MAX_KARMIC,
            future_score=future_score,
            future_max=cls.MAX_FUTURE,
            spiritual_score=spiritual_score,
            spiritual_max=cls.MAX_SPIRITUAL,
            psychological_score=psychological_score,
            psychological_max=cls.MAX_PSYCHOLOGICAL,
            physical_score=physical_score,
            physical_max=cls.MAX_PHYSICAL,
            mars_dosha_score=mars_dosha_score,
            mars_dosha_max=cls.MAX_MARS_DOSHA,
            karmic_pattern_score=karmic_pattern_score,
            karmic_pattern_max=cls.MAX_KARMIC_PATTERN,
            dasha_score=dasha_score,
            dasha_max=cls.MAX_DASHA,
            mutual_planets_score=mutual_planets_score,
            mutual_planets_max=cls.MAX_MUTUAL_PLANETS,
            sub_factors=sub_factors,
            strengths=strengths,
            challenges=challenges,
            recommendations=recommendations,
        )
