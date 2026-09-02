"""
AstroOS — Drishti (Aspect) Model for Cognitive Intelligence

Implements full and special Parashari aspects (Drishti) and their numeric
influence scores across houses and planetary targets.

Classical Drishti Rules:
- All planets cast full (100% / score 1.0) aspect on the 7th house from their placement.
- Special Aspects (Vishesh Drishti):
    * Mars: Full aspect on 4th and 8th houses.
    * Jupiter (and Rahu/Ketu in many Nadi traditions): Full aspect on 5th and 9th houses.
    * Saturn: Full aspect on 3rd and 10th houses.
- Partial aspects (charan drishti): 3/10, 5/9, 4/8 with graduated weights (0.25 to 0.75).
"""

from __future__ import annotations
from typing import Dict, List, Tuple


class DrishtiModel:
    """
    Computes aspect score (0.0 to 1.0) cast by a source graha from one house to a target house.
    Houses are 1-indexed (1 to 12).
    """

    @staticmethod
    def get_house_distance(source_house: int, target_house: int) -> int:
        """
        Returns 1-indexed house count from source to target (inclusive count: 1 to 12).
        E.g., source=1, target=7 -> distance=7.
        """
        dist = ((target_house - source_house) % 12) + 1
        return dist

    @classmethod
    def get_aspect_strength(cls, graha: str, source_house: int, target_house: int) -> float:
        """
        Calculates drishti strength cast by graha on target house.
        Returns a float between 0.0 and 1.0 (or higher if benefic boost applies).
        """
        dist = cls.get_house_distance(source_house, target_house)

        # Same house -> Conjunction (Yuti), maximum direct influence
        if dist == 1:
            return 1.0

        # Universal 7th house full drishti
        if dist == 7:
            return 1.0

        # Special aspects by Graha
        if graha == "Mars":
            if dist in (4, 8):
                return 1.0
            if dist in (5, 9):
                return 0.50
            if dist in (3, 10):
                return 0.25

        elif graha == "Jupiter":
            if dist in (5, 9):
                return 1.0
            if dist in (4, 8):
                return 0.75
            if dist in (3, 10):
                return 0.50

        elif graha == "Saturn":
            if dist in (3, 10):
                return 1.0
            if dist in (4, 8):
                return 0.75
            if dist in (5, 9):
                return 0.50

        elif graha in ("Rahu", "Ketu"):
            # Nadi tradition: Rahu and Ketu aspect 5th and 9th trines
            if dist in (5, 9):
                return 0.75

        # Standard partial Parashari aspect for all other planets
        if dist in (5, 9):
            return 0.50
        elif dist in (4, 8):
            return 0.75
        elif dist in (3, 10):
            return 0.25

        return 0.0

    @classmethod
    def get_aspecting_planets_on_house(
        cls,
        target_house: int,
        planetary_positions: Dict[str, int],  # graha -> house (1..12)
    ) -> List[Tuple[str, float]]:
        """
        Finds all planets casting drishti on target_house with their respective strengths.
        """
        aspects = []
        for graha, house in planetary_positions.items():
            strength = cls.get_aspect_strength(graha, house, target_house)
            if strength > 0.0:
                aspects.append((graha, strength))
        return sorted(aspects, key=lambda x: x[1], reverse=True)
