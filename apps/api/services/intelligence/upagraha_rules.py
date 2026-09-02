"""
AstroOS — Vinay Jha Upagraha Rules & Cognitive Interferences (Gulika & Mandi)

Implements classical rulebooks for Gulika & Mandi based on Vinay Jha's Shastric
treatise (BPHS, Jataka Parijata & Jataka Alankara):

Core Principles:
1. Upachaya Rule: Gulika in houses 3, 6, 10, 11 gives auspicious/benefic results (+1.5).
   In all other 8 houses (1, 2, 4, 5, 7, 8, 9, 12), Gulika is harmful (-1.0 to -2.5).
2. Mrityu / Longevity: Gulika in the 8th house directly indicates severe health crisis
   or fatal turning points (Mrityu Yoga).
3. Marriage / Relationship: Mandi in the 7th house, or conjunct with the 7th lord or Venus,
   causes delay, marital impediments, or estrangement (-1.5 to -2.0).
4. Lagna Conjunction: Gulika/Mandi conjunct Lagna causes Gyāna-nāsha (impaired inner discernment)
   or vulnerability to sudden danger.
5. Luminary Conjunctions:
   - Conjunct Sun: Lineage/paternal affliction (Vamsha-nāsha / Sun blemish).
   - Conjunct Moon: Longevity/mental distress (Ayu-nāsha / Moon blemish).
6. Benefic Suppression: If Gulika/Mandi dispositor or aspecting planets are exalted,
   moolatrikona, or benefics (Jupiter/Venus), adverse effects are mitigated.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class UpagrahaInterference:
    rule_name: str
    target_domain: str  # "marriage", "career", "health", "longevity", "general"
    weight_delta: float
    description: str
    is_auspicious: bool


class UpagrahaRulesEngine:
    """
    Evaluates Gulika & Mandi placement, conjunctions, and aspects to generate
    cognitive weight modifiers for event prediction.
    """

    UPACHAYA_HOUSES = {3, 6, 10, 11}

    @classmethod
    def evaluate_upagrahas(
        cls,
        gulika_house: int,               # 1..12
        mandi_house: int,                # 1..12
        graha_houses: Dict[str, int],     # graha -> house (1..12)
        seventh_lord: Optional[str] = None,
        eighth_lord: Optional[str] = None,
    ) -> List[UpagrahaInterference]:
        """
        Evaluates full spectrum of Gulika/Mandi rules against the birth chart.
        """
        interferences: List[UpagrahaInterference] = []

        # 1. Upachaya vs Non-Upachaya evaluation for Gulika
        if gulika_house in cls.UPACHAYA_HOUSES:
            interferences.append(
                UpagrahaInterference(
                    rule_name="GULIKA_UPACHAYA_BENEFIC",
                    target_domain="career",
                    weight_delta=+1.5,
                    description=f"Gulika in {gulika_house}th house (Upachaya) produces courage, material victory and auspiciousness.",
                    is_auspicious=True,
                )
            )
        else:
            interferences.append(
                UpagrahaInterference(
                    rule_name="GULIKA_NON_UPACHAYA_AFFLICTION",
                    target_domain="temperament",
                    weight_delta=-0.5,
                    description=f"Gulika in {gulika_house}th house (Non-Upachaya) introduces subtle friction and hidden impediments.",
                    is_auspicious=False,
                )
            )


        # 2. 8th House Gulika (Mrityu / Crisis Yoga)
        if gulika_house == 8 or mandi_house == 8:
            interferences.append(
                UpagrahaInterference(
                    rule_name="GULIKA_8TH_MRITYU_INDICATOR",
                    target_domain="health",
                    weight_delta=+2.5,  # positive risk weight for health crisis
                    description="Gulika/Mandi in 8th house forms a potent catalyst for sudden physical crisis or transformative events.",
                    is_auspicious=False,
                )
            )

        # 3. 7th House Mandi / Gulika (Marriage Delay / Impediment)
        if mandi_house == 7 or gulika_house == 7:
            interferences.append(
                UpagrahaInterference(
                    rule_name="MANDI_7TH_MARRIAGE_OBSTACLE",
                    target_domain="marriage",
                    weight_delta=-1.75,
                    description="Mandi/Gulika positioned in 7th house causes delays, friction, or unexpected obstacles in matrimonial timing.",
                    is_auspicious=False,
                )
            )

        # 4. Mandi conjunct 7th Lord or Venus (Yuvatiya Graha)
        if seventh_lord and graha_houses.get(seventh_lord) == mandi_house:
            interferences.append(
                UpagrahaInterference(
                    rule_name="MANDI_CONJUNCT_7TH_LORD",
                    target_domain="marriage",
                    weight_delta=-1.5,
                    description=f"Mandi conjunct 7th lord ({seventh_lord}) imposes karmic delays and tests on relationship manifestation.",
                    is_auspicious=False,
                )
            )

        if graha_houses.get("Venus") in (mandi_house, gulika_house):
            interferences.append(
                UpagrahaInterference(
                    rule_name="UPAGRAHA_CONJUNCT_VENUS",
                    target_domain="marriage",
                    weight_delta=-1.25,
                    description="Gulika/Mandi conjunct Karaka Venus dampens smooth romantic culmination.",
                    is_auspicious=False,
                )
            )

        # 5. Lagna Conjunction (1st House)
        if gulika_house == 1 or mandi_house == 1:
            interferences.append(
                UpagrahaInterference(
                    rule_name="GULIKA_LAGNA_CONJUNCTION",
                    target_domain="health",
                    weight_delta=+1.5,
                    description="Gulika/Mandi on Lagna clouds inner discernment (Gyāna-nāsha) and creates physical vulnerability.",
                    is_auspicious=False,
                )
            )

        # 6. Conjunction with Sun (Vamsha-nāsha) or Moon (Ayu-nāsha)
        if graha_houses.get("Sun") == gulika_house:
            interferences.append(
                UpagrahaInterference(
                    rule_name="GULIKA_CONJUNCT_SUN",
                    target_domain="career",
                    weight_delta=-1.0,
                    description="Gulika conjunct Sun afflicts solar vitality and paternal/authority harmony.",
                    is_auspicious=False,
                )
            )

        if graha_houses.get("Moon") == gulika_house:
            interferences.append(
                UpagrahaInterference(
                    rule_name="GULIKA_CONJUNCT_MOON",
                    target_domain="health",
                    weight_delta=+2.0,
                    description="Gulika conjunct Moon constitutes Ayu-nāsha / intense psychosomatic distress.",
                    is_auspicious=False,
                )
            )

        return interferences

    @classmethod
    def get_domain_modifier(
        cls,
        domain: str,
        interferences: List[UpagrahaInterference],
    ) -> float:
        """
        Sums up weight modifiers for a specific domain (e.g. 'marriage', 'health', 'career').
        """
        total = 0.0
        for inf in interferences:
            if inf.target_domain == domain or inf.target_domain == "general":
                total += inf.weight_delta
        return total
