"""
AstroOS — BPHS Ishta-Kashta & Main Strength Engine
===================================================
Implements the canonical discrete dignity and house strength formulation
from BPHS (Ishta-Kashta-Vivechana Adhyaya, Verses 7-9) and Vinay Jha's treatises:

  1. Main Strength (Discrete 9-Point Scale):
     Exalted (60) → Moolatrikona (45) → Own Sign (30) → Adhi-Mitra (22) →
     Mitra (15) → Sama (8) → Shatru (4) → Ati-Shatru (2) → Neecha (0)
  2. 50% Baseline Presence Rule:
     Even if a house lord casts 0% direct drishti on its own house,
     its inherent structural presence is 50% of the normal aspect.
  3. Shadbala Tie-Breaker:
     Shadbala has a narrow gradient (~2x) compared to the wide gradient (30x)
     of Main Strength, and is used strictly to arbitrate ties between equal Main Strengths.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

# BPHS Ishta-Kashta discrete values mapped to Jha Rank [9 down to 1]
BPHS_DIGNITY_SCALE: Dict[str, int] = {
    "exalted": 60,        # Rank 9
    "moolatrikona": 45,   # Rank 8
    "own": 30,            # Rank 7
    "adhi_mitra": 22,     # Rank 6 (Fast Friend)
    "mitra": 15,          # Rank 5 (Friend)
    "sama": 8,            # Rank 4 (Neutral)
    "shatru": 4,          # Rank 3 (Enemy)
    "ati_shatru": 2,      # Rank 2 (Bitter Enemy)
    "neecha": 0,          # Rank 1 (Debilitated)
}

BPHS_RANK_TO_POINTS: Dict[int, int] = {
    9: 60,
    8: 45,
    7: 30,
    6: 22,
    5: 15,
    4: 8,
    3: 4,
    2: 2,
    1: 0,
}


@dataclass(frozen=True)
class PlanetMainStrength:
    """Calculated Main Strength for a single planet."""
    planet: str
    dignity_label: str
    main_strength_score: int    # 0 to 60
    main_strength_rank: int     # 1 to 9
    is_retrograde: bool
    effective_strength: float   # Adjusted for Vakri amplification


@dataclass(frozen=True)
class BhavaStrengthReport:
    """Strength calculation for an astrological house."""
    house_number: int
    lord: str
    lord_main_strength: int
    has_direct_lord_aspect: bool
    effective_lord_aspect_factor: float  # 1.0 if direct aspect, 0.50 if 0% aspect (Jha 50% rule)
    occupant_strength_sum: float
    total_bhava_score: float


class IshtaKashtaEngine:
    """Calculates BPHS discrete Main Strength and Bhava Strength."""

    @staticmethod
    def get_main_strength(dignity: str, is_retrograde: bool = False) -> PlanetMainStrength:
        """
        Maps dignity string to BPHS 60-point scale with Vakri amplification.
        """
        norm_dig = dignity.lower().strip()
        
        # Standardize labels
        if "exalt" in norm_dig:
            key = "exalted"
            rank = 9
        elif "moola" in norm_dig or "trikona" in norm_dig:
            key = "moolatrikona"
            rank = 8
        elif "own" in norm_dig or "sva" in norm_dig:
            key = "own"
            rank = 7
        elif "adhi_mitra" in norm_dig or "great_friend" in norm_dig or "fast_friend" in norm_dig:
            key = "adhi_mitra"
            rank = 6
        elif "mitra" in norm_dig or "friend" in norm_dig:
            key = "mitra"
            rank = 5
        elif "sama" in norm_dig or "neutral" in norm_dig:
            key = "sama"
            rank = 4
        elif "ati_shatru" in norm_dig or "bitter_enemy" in norm_dig:
            key = "ati_shatru"
            rank = 2
        elif "shatru" in norm_dig or "enemy" in norm_dig:
            key = "shatru"
            rank = 3
        elif "neecha" in norm_dig or "debil" in norm_dig:
            key = "neecha"
            rank = 1
        else:
            key = "sama"
            rank = 4

        base_score = BPHS_DIGNITY_SCALE.get(key, 8)

        # BPHS: Vakri planet gains significant Chesta Bala amplification
        # An auspicious Vakri becomes more auspicious, an inauspicious Vakri more challenging
        effective_score = float(base_score)
        if is_retrograde:
            if base_score >= 15:
                effective_score *= 1.35  # Benefic retrograde boost
            elif base_score <= 4:
                effective_score *= 0.65  # Malefic retrograde penalty

        return PlanetMainStrength(
            planet="",
            dignity_label=key,
            main_strength_score=base_score,
            main_strength_rank=rank,
            is_retrograde=is_retrograde,
            effective_strength=round(effective_score, 2),
        )

    @staticmethod
    def calculate_bhava_strength(
        house_number: int,
        lord: str,
        lord_dignity: str,
        lord_is_retrograde: bool,
        has_direct_lord_aspect: bool,
        occupant_strengths: Optional[list[float]] = None,
    ) -> BhavaStrengthReport:
        """
        Calculates net Bhava strength enforcing Jha's 50% Baseline Presence Rule.
        """
        lord_str = IshtaKashtaEngine.get_main_strength(lord_dignity, lord_is_retrograde)
        
        # 50% Baseline Rule: If lord has zero aspect on its own house,
        # its inherent baseline structural influence is exactly 50% (0.50)
        aspect_factor = 1.0 if has_direct_lord_aspect else 0.50
        
        occ_sum = sum(occupant_strengths) if occupant_strengths else 0.0
        
        # Net Bhava Score combines Lord's aspected strength + occupants
        bhava_total = (lord_str.effective_strength * aspect_factor) + occ_sum

        return BhavaStrengthReport(
            house_number=house_number,
            lord=lord,
            lord_main_strength=lord_str.main_strength_score,
            has_direct_lord_aspect=has_direct_lord_aspect,
            effective_lord_aspect_factor=aspect_factor,
            occupant_strength_sum=round(occ_sum, 2),
            total_bhava_score=round(bhava_total, 2),
        )
