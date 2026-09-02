"""
AstroOS — Main Strength x Vimshopaka Final Varga Fusion Engine
==============================================================

Canonical Reference: docs/JHA_PREDICTION_FRAMEWORK.md (Step 3 & Step 4)
Source: BPHS Ishta-Kashta-Vivechana Chapter & Jha's "How To Make Correct Predictions"

Key Siddhantic Rules Enforced:
1. "Main strength is scaled on a logarithmic scale of base two (cf BPHS, which uses
    log-base two), while Shadbala has a maximum scale of approximately double."
2. "When D1 current Vimshottari planet's strength is to be compared with the Vimshottari
    planet of the required divisional, then MULTIPLY Main Strength with Vimshopaka Strength
    of the divisional to get final strength."
3. "Use Shadbala ONLY when the main strength of two competing planets are same."
4. "Due to high Vimshopaka of D1, divisional charts should NOT be used unless their
    current Vimshottari planets have very high strengths with respect to the current
    Vimshottari planets of D1."
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from apps.api.services.intelligence.strength_model import DignityScore, StrengthModel

from packages.shared.constants import SIGN_LORDS


# Standard Parashari Vimshopaka Weights (Dashavarga Scheme out of 20 total points)
VIMSHOPAKA_WEIGHTS_DASHAVARGA: Dict[int, float] = {
    1: 3.0,   # D1 Rasi (Dominant)
    2: 1.5,   # D2 Hora
    3: 1.5,   # D3 Drekkana
    4: 1.5,   # D4 Chaturthamsha
    7: 1.5,   # D7 Saptamsha
    9: 3.0,   # D9 Navamsha (High)
    10: 2.0,  # D10 Dashamsha
    12: 1.0,  # D12 Dwadashamsha
    16: 1.0,  # D16 Shodashamsha
    24: 1.0,  # D24 Chaturvimshamsha
    30: 1.0,  # D30 Trishamsha
    60: 4.0,  # D60 Shashtiamsha (gated behind birth accuracy)
}


@dataclass(frozen=True)
class PlanetVargaStrengthDetail:
    """Detailed strength assessment for a single planet in a specific varga."""
    planet: str
    varga_number: int
    rashi_index: int
    dignity_score: int         # 1 to 9 Log-Base-2 scale
    dignity_label: str         # Exalted, Own Sign, Neutral, Debilitated, etc.
    vimshopaka_weight: float   # Weight out of 20
    final_varga_strength: float # dignity_score * vimshopaka_weight
    shadbala_rupas: Optional[float] = None
    is_debilitation_cancelled: bool = False


@dataclass(frozen=True)
class DualDashaVargaComparison:
    """Comparison of D1 active dasha lords vs Divisional active dasha lords."""
    domain: str
    target_varga: int
    d1_md_lord: str
    d1_ad_lord: str
    div_md_lord: str
    div_ad_lord: str
    d1_combined_strength: float
    div_combined_strength: float
    is_divisional_supportive: bool
    siddhantic_verdict: str


class VargaStrengthFusionEngine:
    """
    Computes Main Strength x Vimshopaka Final Strengths and resolves D1 vs Divisional confluence.
    """

    @classmethod
    def compute_main_strength(
        cls,
        planet: str,
        sign_index: int,
        sign_occupants: Optional[Tuple[str, ...]] = None,
    ) -> Tuple[int, str, bool]:
        """
        Computes 1-9 Log-Base-2 Main Strength with Parashari Debilitation Cancellation (Neecha Bhanga).
        """
        p_cap = planet.capitalize()
        dignity = StrengthModel.get_dignity_score(p_cap, sign_index)
        d_val = int(dignity)
        is_cancelled = False


        # Neecha Bhanga Check (Jha Rule: debilitated planet conjunct own sign lord becomes neutral 4)
        if d_val == 1 and sign_occupants:
            from packages.shared.constants import KALACHAKRA_SAVYA_SIGNS
            r_name = KALACHAKRA_SAVYA_SIGNS[sign_index] if sign_index < len(KALACHAKRA_SAVYA_SIGNS) else ""
            sign_lord = SIGN_LORDS.get(r_name, "").lower()
            if sign_lord in [occ.lower() for occ in sign_occupants]:
                d_val = 4  # Neutralized to Sama (Neutral)
                is_cancelled = True


        return d_val, dignity.name, is_cancelled

    @classmethod
    def evaluate_planet_varga_strength(
        cls,
        planet: str,
        varga_number: int,
        sign_index: int,
        shadbala_rupas: Optional[float] = None,
        sign_occupants: Optional[Tuple[str, ...]] = None,
    ) -> PlanetVargaStrengthDetail:
        """
        Evaluates Final Varga Strength = Main Strength * Vimshopaka Weight.
        """
        d_val, d_label, is_canc = cls.compute_main_strength(planet, sign_index, sign_occupants)
        w = VIMSHOPAKA_WEIGHTS_DASHAVARGA.get(varga_number, 1.5)
        final_str = float(d_val) * w

        return PlanetVargaStrengthDetail(
            planet=planet,
            varga_number=varga_number,
            rashi_index=sign_index,
            dignity_score=d_val,
            dignity_label=d_label,
            vimshopaka_weight=w,
            final_varga_strength=round(final_str, 2),
            shadbala_rupas=shadbala_rupas,
            is_debilitation_cancelled=is_canc,
        )

    @classmethod
    def compare_d1_vs_divisional_dashas(
        cls,
        domain: str,
        target_varga: int,
        d1_md_detail: PlanetVargaStrengthDetail,
        d1_ad_detail: PlanetVargaStrengthDetail,
        div_md_detail: PlanetVargaStrengthDetail,
        div_ad_detail: PlanetVargaStrengthDetail,
    ) -> DualDashaVargaComparison:
        """
        Compares D1 running dasha strength with Divisional running dasha strength.
        Applies Shadbala tiebreaker if Main Strengths match.
        """
        d1_comb = (d1_md_detail.final_varga_strength * 0.6) + (d1_ad_detail.final_varga_strength * 0.4)
        div_comb = (div_md_detail.final_varga_strength * 0.6) + (div_ad_detail.final_varga_strength * 0.4)

        # Shadbala tiebreaker check
        if round(d1_comb, 1) == round(div_comb, 1):
            s_d1 = (d1_md_detail.shadbala_rupas or 1.0) + (d1_ad_detail.shadbala_rupas or 1.0)
            s_div = (div_md_detail.shadbala_rupas or 1.0) + (div_ad_detail.shadbala_rupas or 1.0)
            is_supportive = s_div >= s_d1
            verdict = f"Tie in Main Strength broken by Shadbala ({s_div:.2f} vs {s_d1:.2f} Rupas)."
        else:
            is_supportive = div_comb >= (d1_comb * 0.75) # Divisional confirms promise if adequate
            if div_comb > d1_comb:
                verdict = f"Divisional D{target_varga} significantly amplifies D1 natal promise (+{div_comb - d1_comb:.1f})."
            elif is_supportive:
                verdict = f"Divisional D{target_varga} harmoniously confirms D1 natal promise."
            else:
                verdict = f"Divisional D{target_varga} exhibits friction against D1 activation."

        return DualDashaVargaComparison(
            domain=domain,
            target_varga=target_varga,
            d1_md_lord=d1_md_detail.planet,
            d1_ad_lord=d1_ad_detail.planet,
            div_md_lord=div_md_detail.planet,
            div_ad_lord=div_ad_detail.planet,
            d1_combined_strength=round(d1_comb, 2),
            div_combined_strength=round(div_comb, 2),
            is_divisional_supportive=is_supportive,
            siddhantic_verdict=verdict,
        )

    @classmethod
    def compare_dual_dashas(

        cls,
        domain: str,
        target_varga: int,
        d1_md_lord: str,
        d1_ad_lord: str,
        div_md_lord: str,
        div_ad_lord: str,
        d1_planet_signs: Dict[str, int],
        div_planet_signs: Dict[str, int],
    ) -> DualDashaVargaComparison:
        """
        Convenience wrapper that evaluates planet strengths and compares dual dashas.
        """
        d1_md_s = cls.evaluate_planet_varga_strength(d1_md_lord, 1, d1_planet_signs.get(d1_md_lord.lower(), 0))
        d1_ad_s = cls.evaluate_planet_varga_strength(d1_ad_lord, 1, d1_planet_signs.get(d1_ad_lord.lower(), 0))
        div_md_s = cls.evaluate_planet_varga_strength(div_md_lord, target_varga, div_planet_signs.get(div_md_lord.lower(), 0))
        div_ad_s = cls.evaluate_planet_varga_strength(div_ad_lord, target_varga, div_planet_signs.get(div_ad_lord.lower(), 0))
        return cls.compare_d1_vs_divisional_dashas(domain, target_varga, d1_md_s, d1_ad_s, div_md_s, div_ad_s)

