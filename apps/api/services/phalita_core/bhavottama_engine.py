"""
AstroOS — Bhavottama (Kimshukadi) Detection Engine
==================================================

Canonical Reference: docs/JHA_PREDICTION_FRAMEWORK.md (Step 6)
Source: BPHS Kimshukadi Yoga Adhyaya & Jha's "How To Make Correct Predictions"

Key Siddhantic Principles Enforced:
1. Bhavottama != Rashi Vargottama.
   - Rashi Vargottama = Same Zodiac Sign across divisionals.
   - Bhavottama = Same House (Bhava) offset from Lagna across divisionals.
2. Classical Kimshukadi Yogas are fundamentally Bhavottama placements.
3. Quality Multiplier:
   - If planet is in good dignity (Exalted, Moolatrikona, Own Sign) and Bhavottama -> High positive amplification.
   - If planet is debilitated and Bhavottama -> Compounded malefic friction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from apps.api.services.intelligence.strength_model import DignityScore, StrengthModel



@dataclass(frozen=True)
class BhavottamaStatus:
    """Bhavottama assessment for a single planet across core divisionals."""
    planet: str
    d1_house: int
    d9_house: int
    d10_house: int
    is_d1_d9_bhavottama: bool       # Same house in D1 and D9
    is_d1_d10_bhavottama: bool      # Same house in D1 and D10
    is_tri_bhavottama: bool         # Same house in D1, D9, and D10 (Kimshuka Yoga)
    d1_dignity_score: int          # 1 to 9
    dignity_label: str
    amplification_factor: float    # Multiplier: > 1.0 if benefic, < 1.0 (or negative) if afflicted
    shastric_description: str


class BhavottamaEngine:
    """
    Detects Bhavottama (same house across divisionals) and computes shastric yoga amplification.
    """

    @classmethod
    def evaluate_planet(
        cls,
        planet: str,
        d1_house: int,
        d9_house: int,
        d10_house: int,
        d1_sign_idx: int,
    ) -> BhavottamaStatus:
        """
        Evaluates whether a planet holds Bhavottama placement and its resulting potency.
        """
        p_cap = planet.capitalize()
        dignity = StrengthModel.get_dignity_score(p_cap, d1_sign_idx)
        d_val = int(dignity)


        is_d9_bhav = (d1_house == d9_house)
        is_d10_bhav = (d1_house == d10_house)
        is_tri_bhav = (is_d9_bhav and is_d10_bhav)

        # Compute amplification factor
        if is_tri_bhav:
            if d_val >= 7:  # Exalted / Moolatrikona / Own Sign
                amp = 2.0
                desc = f"Tri-Bhavottama (Kimshuka Yoga) in House {d1_house}: Exalted dignity ({dignity.name}) delivers grand auspicious fruits."
            elif d_val <= 3:  # Inimical / Debilitated
                amp = 0.4
                desc = f"Tri-Bhavottama affliction in House {d1_house}: Debilitated state ({dignity.name}) compounds malefic obstacles."
            else:
                amp = 1.5
                desc = f"Tri-Bhavottama in House {d1_house}: Solid stabilizing foundation across D1, D9, and D10."
        elif is_d9_bhav:
            if d_val >= 7:
                amp = 1.5
                desc = f"Navamsha Bhavottama in House {d1_house}: Strong inner dharmic backing ({dignity.name})."
            elif d_val <= 3:
                amp = 0.7
                desc = f"Navamsha Bhavottama with weak dignity ({dignity.name}) in House {d1_house}."
            else:
                amp = 1.25
                desc = f"Navamsha Bhavottama in House {d1_house} provides steady structural support."
        elif is_d10_bhav:
            if d_val >= 7:
                amp = 1.4
                desc = f"Dashamsha Bhavottama in House {d1_house}: Professional karmic manifestation energized."
            elif d_val <= 3:
                amp = 0.75
                desc = f"Dashamsha Bhavottama in House {d1_house} under dignity strain."
            else:
                amp = 1.2
                desc = f"Dashamsha Bhavottama in House {d1_house}: Active career focus."
        else:
            amp = 1.0
            desc = f"Standard divisional distribution (H{d1_house} in D1, H{d9_house} in D9, H{d10_house} in D10)."

        return BhavottamaStatus(
            planet=planet,
            d1_house=d1_house,
            d9_house=d9_house,
            d10_house=d10_house,
            is_d1_d9_bhavottama=is_d9_bhav,
            is_d1_d10_bhavottama=is_d10_bhav,
            is_tri_bhavottama=is_tri_bhav,
            d1_dignity_score=d_val,
            dignity_label=dignity.name,
            amplification_factor=round(amp, 2),
            shastric_description=desc,
        )

    @classmethod
    def evaluate_chart_bhavottamas(
        cls,
        d1_houses: Dict[str, int],
        d9_houses: Dict[str, int],
        d10_houses: Dict[str, int],
        d1_signs: Dict[str, int],
    ) -> List[BhavottamaStatus]:
        """
        Evaluates Bhavottama placements for all classical 7 planets.
        """
        results = []
        for p in ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"):
            h1 = d1_houses.get(p, 1)
            h9 = d9_houses.get(p, 1)
            h10 = d10_houses.get(p, 1)
            s1 = d1_signs.get(p, 0)
            status = cls.evaluate_planet(
                planet=p.capitalize(),
                d1_house=h1,
                d9_house=h9,
                d10_house=h10,
                d1_sign_idx=s1,
            )
            results.append(status)
        return results
