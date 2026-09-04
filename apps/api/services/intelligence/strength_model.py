"""
AstroOS — Strength Model (Base-2 Exponential Strength Mapping)

Implements the 1 to 9 discrete planetary dignity scoring and its exact base-2
exponential strength mapping as detailed by Vinay Jha based on BPHS
(Ishta-Kashta-Vivechana Adhyaya, verses 7-9):

  Score 9 = Exalted (Uchcha)
  Score 8 = Moolatrikona
  Score 7 = Svagrihi (Own sign)
  Score 6 = Fast Friend's sign (Adhi-Mitra)
  Score 5 = Friend's sign (Mitra)
  Score 4 = Neutral sign (Sama)
  Score 3 = Enemy's sign (Shatru)
  Score 2 = Bitter Enemy's sign (Adhi-Shatru)
  Score 1 = Debilitated (Neecha)

Key Shastric Principle:
Base-2 Exponential Strength Mapping (2^(score-1)),
meaning each higher grade is twice as strong as the preceding one.
Exalted planet (score 9 -> 256) is roughly 30x to 256x stronger than
inimical/debilitated placements.
"""


from __future__ import annotations
from enum import IntEnum
from typing import Dict, Optional


class DignityScore(IntEnum):
    NEECHA = 1
    ADHI_SHATRU = 2
    SHATRU = 3
    SAMA = 4
    MITRA = 5
    ADHI_MITRA = 6
    SVAGRIHA = 7
    MOOLATRIKONA = 8
    UCHCHA = 9


class StrengthModel:
    """
    Computes Main Strength (1-9) and Logarithmic Base-2 Multiplier.
    """

    # Exaltation signs (0-indexed: 0=Aries, 1=Taurus, ..., 11=Pisces)
    EXALTATION_SIGNS: Dict[str, int] = {
        "Sun": 0,       # Mesha (Aries)
        "Moon": 1,      # Vrishabha (Taurus)
        "Mars": 9,      # Makara (Capricorn)
        "Mercury": 5,   # Kanya (Virgo)
        "Jupiter": 3,   # Karka (Cancer)
        "Venus": 11,    # Meena (Pisces)
        "Saturn": 6,    # Tula (Libra)
        "Rahu": 1,      # Taurus (or Gemini in some traditions)
        "Ketu": 7,      # Scorpio (or Sagittarius in some traditions)
    }

    # Debilitation signs (exact opposite: +6 signs)
    DEBILITATION_SIGNS: Dict[str, int] = {
        "Sun": 6,       # Tula
        "Moon": 7,      # Vrishchika
        "Mars": 3,      # Karka
        "Mercury": 11,  # Meena
        "Jupiter": 9,   # Makara
        "Venus": 5,     # Kanya
        "Saturn": 0,    # Mesha
        "Rahu": 7,      # Vrishchika
        "Ketu": 1,      # Vrishabha
    }

    # Own signs
    OWN_SIGNS: Dict[str, list[int]] = {
        "Sun": [4],          # Simha
        "Moon": [3],         # Karka
        "Mars": [0, 7],      # Mesha, Vrishchika
        "Mercury": [2, 5],   # Mithuna, Kanya
        "Jupiter": [8, 11],  # Dhanu, Meena
        "Venus": [1, 6],     # Vrishabha, Tula
        "Saturn": [9, 10],   # Makara, Kumbha
        "Rahu": [10],        # Kumbha (co-lord)
        "Ketu": [7],         # Vrishchika (co-lord)
    }

    # Natural friendship table (BPHS)
    NATURAL_FRIENDS: Dict[str, list[str]] = {
        "Sun": ["Moon", "Mars", "Jupiter"],
        "Moon": ["Sun", "Mercury"],
        "Mars": ["Sun", "Moon", "Jupiter"],
        "Mercury": ["Sun", "Venus"],
        "Jupiter": ["Sun", "Moon", "Mars"],
        "Venus": ["Mercury", "Saturn"],
        "Saturn": ["Mercury", "Venus"],
        "Rahu": ["Mercury", "Venus", "Saturn"],
        "Ketu": ["Mars", "Jupiter"],
    }

    NATURAL_ENEMIES: Dict[str, list[str]] = {
        "Sun": ["Venus", "Saturn"],
        "Moon": [],
        "Mars": ["Mercury"],
        "Mercury": ["Moon"],
        "Jupiter": ["Mercury", "Venus"],
        "Venus": ["Sun", "Moon"],
        "Saturn": ["Sun", "Moon", "Mars"],
        "Rahu": ["Sun", "Moon", "Mars"],
        "Ketu": ["Sun", "Moon"],
    }

    SIGN_LORDS: Dict[int, str] = {
        0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon",
        4: "Sun", 5: "Mercury", 6: "Venus", 7: "Mars",
        8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter"
    }

    @classmethod
    def get_dignity_score(
        cls,
        graha: str,
        sign_idx: int,
        is_moolatrikona: bool = False,
        is_temporal_friend: Optional[bool] = None,
    ) -> DignityScore:
        """
        Determines the 1-9 discrete dignity score of a graha in a given rashi.
        """
        if graha in cls.EXALTATION_SIGNS and cls.EXALTATION_SIGNS[graha] == sign_idx:
            return DignityScore.UCHCHA

        if graha in cls.DEBILITATION_SIGNS and cls.DEBILITATION_SIGNS[graha] == sign_idx:
            return DignityScore.NEECHA

        if is_moolatrikona:
            return DignityScore.MOOLATRIKONA

        if graha in cls.OWN_SIGNS and sign_idx in cls.OWN_SIGNS[graha]:
            return DignityScore.SVAGRIHA

        lord = cls.SIGN_LORDS.get(sign_idx)
        if not lord or lord == graha:
            return DignityScore.SAMA

        is_nat_friend = lord in cls.NATURAL_FRIENDS.get(graha, [])
        is_nat_enemy = lord in cls.NATURAL_ENEMIES.get(graha, [])

        # Compound Panchadha Maitri if temporal friendship given
        if is_temporal_friend is True:
            if is_nat_friend:
                return DignityScore.ADHI_MITRA
            elif is_nat_enemy:
                return DignityScore.SAMA
            else:
                return DignityScore.MITRA
        elif is_temporal_friend is False:
            if is_nat_friend:
                return DignityScore.SAMA
            elif is_nat_enemy:
                return DignityScore.ADHI_SHATRU
            else:
                return DignityScore.SHATRU

        # Default to natural relationship if temporal not provided
        if is_nat_friend:
            return DignityScore.MITRA
        elif is_nat_enemy:
            return DignityScore.SHATRU
        return DignityScore.SAMA

    @classmethod
    def calculate_log_strength(cls, score: DignityScore | int) -> float:
        """
        Vinay Jha Logarithmic Base-2 formulation:
        Strength = 2^(score - 1)
        Score 1 = 1.0 (Neecha)
        Score 2 = 2.0
        Score 3 = 4.0
        ...
        Score 9 = 256.0 (Uchcha)
        """
        val = int(score)
        val = max(1, min(9, val))
        return float(1 << (val - 1))
