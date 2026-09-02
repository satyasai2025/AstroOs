"""
AstroOS — Divisional Synthesis & Vimshopaka Bala Engine
========================================================
Implements canonical Divisional Chart (Varga) evaluation and Vimshopaka Bala
weighting schemes strictly following BPHS (Chapters 6 & 7) and Vinay Jha's treatises:

  1. The 4 Canonical BPHS Vimshopaka Schemes (Each totaling 20.0 points):
     - SHADVARGA   (6 Vargas): D1=6.0, D2=2.0, D3=4.0, D9=5.0, D12=2.0, D30=1.0
     - SAPTAVARGA  (7 Vargas): D1=5.0, D2=2.0, D3=3.0, D7=2.5, D9=4.5, D12=2.0, D30=1.0
     - DASHAVARGA  (10 Vargas): D1=3.0, D2=1.5, D3=1.5, D7=1.5, D9=1.5, D10=1.5, D12=1.5, D16=1.5, D30=1.5, D60=5.0
     - SHODASHAVARGA (16 Vargas): D1=3.5, D60=4.0, D9=3.0, D16=2.0, D2=1.0, D3=1.0, D30=1.0,
                                  D4=0.5, D7=0.5, D10=0.5, D12=0.5, D20=0.5, D24=0.5, D27=0.5, D40=0.5, D45=0.5

  2. Main Strength Rank (9 down to 1):
     Exalted (9) → Moolatrikona (8) → Own (7) → Adhi-Mitra (6) → Mitra (5) →
     Sama (4) → Shatru (3) → Ati-Shatru (2) → Neecha (1)

  3. Jha's Effective Vimshopaka Strength & Override Evaluation:
     S_eff(P, V) = Main Strength Rank(P, V) * W_v
     A divisional chart modifies D1 outcome only if the active divisional lord
     exhibits exceptional relative strength compared to D1.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

from apps.api.services.divisional_engine import compute_varga_sign
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.ishta_kashta_engine import IshtaKashtaEngine


class VimshopakaScheme(str, Enum):
    SHADVARGA = "shadvarga"          # 6 charts
    SAPTAVARGA = "saptavarga"        # 7 charts
    DASHAVARGA = "dashavarga"        # 10 charts
    SHODASHAVARGA = "shodashavarga"  # 16 charts


# Canonical BPHS Vimshopaka weights (sum = 20.0 for each scheme)
VIMSHOPAKA_WEIGHTS: Dict[VimshopakaScheme, Dict[int, float]] = {
    VimshopakaScheme.SHADVARGA: {
        1: 6.0,
        2: 2.0,
        3: 4.0,
        9: 5.0,
        12: 2.0,
        30: 1.0,
    },
    VimshopakaScheme.SAPTAVARGA: {
        1: 5.0,
        2: 2.0,
        3: 3.0,
        7: 2.5,   # D7 is 2.5 in Saptavarga
        9: 4.5,   # D9 is 4.5 in Saptavarga
        12: 2.0,
        30: 1.0,
    },
    VimshopakaScheme.DASHAVARGA: {
        1: 3.0,
        2: 1.5,
        3: 1.5,
        7: 1.5,
        9: 1.5,
        10: 1.5,  # D10 is 1.5 in Dashavarga
        12: 1.5,
        16: 1.5,
        30: 1.5,
        60: 5.0,  # D60 is 5.0 in Dashavarga
    },
    VimshopakaScheme.SHODASHAVARGA: {
        1: 3.5,
        60: 4.0,
        9: 3.0,
        16: 2.0,
        2: 1.0,
        3: 1.0,
        30: 1.0,
        4: 0.5,
        7: 0.5,
        10: 0.5,
        12: 0.5,
        20: 0.5,
        24: 0.5,
        27: 0.5,
        40: 0.5,
        45: 0.5,
    },
}


class DivisionalVerdict(str, Enum):
    REINFORCING = "REINFORCING"                # Both D1 and Divisional are strong
    D1_PREVAILS = "D1_PREVAILS"                # D1 is strong, Divisional cannot override
    DIVISIONAL_OVERRIDE = "DIVISIONAL_OVERRIDE"# Divisional is exceptionally strong, modifying D1
    MUTUALLY_AFFLICTED = "MUTUALLY_AFFLICTED"  # Both D1 and Divisional are weak/debilitated


@dataclass(frozen=True)
class PlanetVargaStrength:
    """Strength profile of a planet in a specific divisional chart."""
    planet: str
    varga_number: int             # e.g. 10 for D10, 24 for D24
    varga_sign: str               # e.g. "aries"
    dignity_label: str            # e.g. "exalted", "own", "sama"
    main_strength_rank: int       # 1 to 9
    vimshopaka_weight: float      # Weight in the active scheme
    effective_strength: float     # Rank * Weight


@dataclass(frozen=True)
class DivisionalSynthesisReport:
    """Synthesis of D1 baseline with a specific divisional chart (e.g. D10 Karma, D24 Vidya)."""
    planet: str
    target_varga: int             # e.g. 10 (Career) or 24 (Vidya)
    scheme_used: VimshopakaScheme
    d1_strength: PlanetVargaStrength
    divisional_strength: PlanetVargaStrength
    verdict: DivisionalVerdict
    relative_strength_ratio: float
    synthesis_notes: str


class DivisionalSynthesisEngine:
    """Engine for synthesizing D1 baseline with specialized Divisional Vargas."""

    def __init__(self, ephemeris_wrapper: Optional[EphemerisWrapper] = None, ephemeris_path: str = "data/ephemeris"):
        self.wrapper = ephemeris_wrapper or EphemerisWrapper(ephemeris_path=ephemeris_path)

    @staticmethod
    def get_varga_weight(varga: int, scheme: VimshopakaScheme = VimshopakaScheme.SHODASHAVARGA) -> float:
        """Returns the canonical BPHS Vimshopaka weight for a given varga and scheme."""
        weights = VIMSHOPAKA_WEIGHTS.get(scheme, VIMSHOPAKA_WEIGHTS[VimshopakaScheme.SHODASHAVARGA])
        return weights.get(varga, 0.5)

    def evaluate_planet_in_varga(
        self,
        planet: str,
        sidereal_lon: float,
        varga_number: int,
        scheme: VimshopakaScheme = VimshopakaScheme.SHODASHAVARGA,
    ) -> PlanetVargaStrength:
        """
        Calculates a planet's sign, dignity, and effective Vimshopaka strength in a target varga.
        """
        v_sign_res = compute_varga_sign(varga=f"D{varga_number}", sidereal_longitude=sidereal_lon)
        v_sign = v_sign_res[0].lower() if isinstance(v_sign_res, tuple) else str(v_sign_res).lower()


        
        # Calculate dignity in that varga sign
        dignity_str = "sama"
        from packages.shared.constants import DEBILITATION_RASHIS, EXALTATION_DEGREES, OWN_SIGNS
        p_lower = planet.lower()
        if p_lower in EXALTATION_DEGREES and EXALTATION_DEGREES[p_lower][0] == v_sign:
            dignity_str = "exalted"
        elif p_lower in DEBILITATION_RASHIS and DEBILITATION_RASHIS[p_lower] == v_sign:
            dignity_str = "debilitated"
        elif p_lower in OWN_SIGNS and v_sign in OWN_SIGNS[p_lower]:
            dignity_str = "own"
        else:
            dignity_str = "sama"

        main_str = IshtaKashtaEngine.get_main_strength(dignity_str)
        weight = self.get_varga_weight(varga_number, scheme)
        eff_str = main_str.main_strength_rank * weight

        return PlanetVargaStrength(
            planet=planet.capitalize(),
            varga_number=varga_number,
            varga_sign=v_sign,
            dignity_label=dignity_str,
            main_strength_rank=main_str.main_strength_rank,
            vimshopaka_weight=weight,
            effective_strength=round(eff_str, 2),
        )

    def synthesize_d1_vs_divisional(
        self,
        planet: str,
        sidereal_lon: float,
        target_varga: int,
        scheme: VimshopakaScheme = VimshopakaScheme.SHODASHAVARGA,
    ) -> DivisionalSynthesisReport:
        """
        Synthesizes D1 baseline vs target Divisional chart strictly enforcing Jha's override rule.
        """
        d1_prof = self.evaluate_planet_in_varga(planet, sidereal_lon, varga_number=1, scheme=scheme)
        div_prof = self.evaluate_planet_in_varga(planet, sidereal_lon, varga_number=target_varga, scheme=scheme)

        # Jha Override Logic:
        # D1 has high weight (3.5 in Shodash, 3.0 in Dasha, 5.0 in Sapta, 6.0 in Shad)
        # Divisional has lower weight (0.5 to 1.5)
        # Ratio of raw ranks
        rank_d1 = d1_prof.main_strength_rank
        rank_div = div_prof.main_strength_rank

        ratio = round(div_prof.effective_strength / d1_prof.effective_strength, 2) if d1_prof.effective_strength > 0 else 9.99

        if rank_d1 >= 7 and rank_div >= 7:
            verdict = DivisionalVerdict.REINFORCING
            notes = f"{planet} is dignified in both D1 ({d1_prof.dignity_label}) and D{target_varga} ({div_prof.dignity_label}). Flawless auspicious manifestation."
        elif rank_d1 <= 3 and rank_div <= 3:
            verdict = DivisionalVerdict.MUTUALLY_AFFLICTED
            notes = f"{planet} is afflicted in both D1 ({d1_prof.dignity_label}) and D{target_varga} ({div_prof.dignity_label}). Severe struggle in this domain."
        elif rank_d1 >= 6 and rank_div < 6:
            verdict = DivisionalVerdict.D1_PREVAILS
            notes = f"D1 baseline is powerful ({d1_prof.dignity_label}, W={d1_prof.vimshopaka_weight}). Weakness in D{target_varga} causes minor friction but D1 prevails per Jha's rule."
        elif rank_d1 < 4 and rank_div >= 8:
            verdict = DivisionalVerdict.DIVISIONAL_OVERRIDE
            notes = f"D{target_varga} is exceptionally exalted/moolatrikona ({div_prof.dignity_label}). Overrides D1 weakness to produce breakthrough in specialized domain."
        else:
            verdict = DivisionalVerdict.D1_PREVAILS
            notes = f"D1 baseline governs overall trajectory. D{target_varga} provides secondary color."

        return DivisionalSynthesisReport(
            planet=planet.capitalize(),
            target_varga=target_varga,
            scheme_used=scheme,
            d1_strength=d1_prof,
            divisional_strength=div_prof,
            verdict=verdict,
            relative_strength_ratio=ratio,
            synthesis_notes=notes,
        )
