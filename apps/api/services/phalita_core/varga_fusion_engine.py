"""
AstroOS — Varga Fusion Engine
=============================

Canonical Specification from Vinay Ji's 78-Document Knowledge Base:
Source: docs/wikidot_canonical_knowledge/04_ai_and_computational_systems/phalita-moe-ai-model.md (Lines 503-520)
        docs/wikidot_canonical_knowledge/03_chakras_and_special_systems/divisional-charts.md
        docs/wikidot_canonical_knowledge/01_astronomical_foundations/start.md (Point 7)

Mathematical Invariants:
1. Signed Varga Addition:
   F_total = (W_D1 * F_D1 + W_D2 * F_D2 + W_D9 * F_D9 + W_D10 * F_D10 + W_D60 * F_D60) / Total_W
   (Conflicting divisional indications naturally suppress each other).
2. Domain-Specific Vimshopaka Weights:
   - Career: D1 (5.0), D9 (4.0), D10 (6.0), D60 (5.0)
   - Marriage: D1 (5.0), D9 (7.0), D60 (4.0)
   - Wealth: D1 (5.0), D2 (5.0), D9 (3.0), D11 (4.0), D60 (3.0)
   - Progeny: D1 (5.0), D7 (6.0), D9 (4.0), D60 (3.0)
3. Bhāvottama Multiplier:
   A planet occupying the same house across divisionals (D1, D9, D10, D60) acquires super-exalted amplification.
4. Vargottama:
   A planet occupying the same sign in D1 and D9.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from apps.api.domain.horoscope import D1Chart
from apps.api.services.divisional_engine import compute_varga_sign
from apps.api.services.phalita_core.tphalit_core import (
    TPhalitCore,
    get_rashi_idx,
    HOUSE_PLACEMENT_WEIGHTS,
    RASHI_LORDS,
)


@dataclass(frozen=True)
class PlanetVargaStatus:
    """A planet's dignities and placements across key divisional charts."""
    planet: str
    d1_rashi_idx: int
    d1_house: int
    d9_rashi_idx: int
    d9_house: int
    d10_rashi_idx: int
    d10_house: int
    d60_rashi_idx: int
    d60_house: int
    is_vargottama: bool       # Same sign in D1 and D9
    is_bhavottama: bool       # Same house in D1 and D9/D10/D60
    bhavottama_divisions: tuple[str, ...]
    amplification_factor: float # [1.0 to 2.0]


@dataclass(frozen=True)
class VargaFusionReport:
    """Composite signed score across all divisionals by life domain."""
    planet_statuses: Dict[str, PlanetVargaStatus]
    fused_domain_scores: Dict[str, float]  # "career", "marriage", "wealth", "spirituality" [-1.0 to +1.0]
    bhavottama_planets: tuple[str, ...]
    vargottama_planets: tuple[str, ...]
    overall_varga_harmony: float           # [-1.0 to +1.0]


# Domain Weightings per Shodashavarga Vimshopaka rules
DOMAIN_VARGA_WEIGHTS = {
    "career": {"D1": 5.0, "D9": 4.0, "D10": 6.0, "D60": 5.0},
    "marriage": {"D1": 5.0, "D9": 7.0, "D60": 4.0},
    "wealth": {"D1": 5.0, "D2": 5.0, "D9": 3.0, "D10": 3.0, "D60": 4.0},
    "general": {"D1": 6.0, "D9": 5.0, "D10": 4.0, "D60": 5.0},
}


class VargaFusionEngine:
    """Deterministic signed Varga fusion engine."""

    def __init__(self):
        self.tphalit_core = TPhalitCore()

    def evaluate_vargas(
        self,
        d1_chart: D1Chart,
    ) -> VargaFusionReport:
        """Compute signed composite score across D1, D2, D9, D10, D60."""
        lagna_rashi = get_rashi_idx(d1_chart.ascendant.rashi)
        lagna_deg = float(d1_chart.ascendant.rashi_degree)

        p_statuses: Dict[str, PlanetVargaStatus] = {}
        bhavottama_list: List[str] = []
        vargottama_list: List[str] = []

        # Compute divisional ascendants
        lagna_lon = float(getattr(d1_chart.ascendant, "sidereal_longitude", lagna_rashi * 30.0 + lagna_deg))
        d9_lagna = get_rashi_idx(compute_varga_sign("D9", lagna_lon)[0])
        d10_lagna = get_rashi_idx(compute_varga_sign("D10", lagna_lon)[0])
        d60_lagna = get_rashi_idx(compute_varga_sign("D60", lagna_lon)[0])

        for pos in d1_chart.planets:
            p_name = pos.planet.lower()
            r_idx = get_rashi_idx(pos.rashi)
            deg = float(pos.rashi_degree)
            p_lon = float(getattr(pos, "sidereal_longitude", r_idx * 30.0 + deg))

            # D1
            h_d1 = ((r_idx - lagna_rashi) % 12) + 1

            # D9 (Navamsha)
            r_d9 = get_rashi_idx(compute_varga_sign("D9", p_lon)[0])
            h_d9 = ((r_d9 - d9_lagna) % 12) + 1

            # D10 (Dashamsha)
            r_d10 = get_rashi_idx(compute_varga_sign("D10", p_lon)[0])
            h_d10 = ((r_d10 - d10_lagna) % 12) + 1

            # D60 (Shashtyamsha)
            r_d60 = get_rashi_idx(compute_varga_sign("D60", p_lon)[0])
            h_d60 = ((r_d60 - d60_lagna) % 12) + 1

            is_varg = (r_idx == r_d9)
            if is_varg:
                vargottama_list.append(p_name)

            bh_divs: List[str] = ["D1"]
            if h_d9 == h_d1:
                bh_divs.append("D9")
            if h_d10 == h_d1:
                bh_divs.append("D10")
            if h_d60 == h_d1:
                bh_divs.append("D60")

            is_bhav = len(bh_divs) >= 2
            if is_bhav:
                bhavottama_list.append(p_name)

            amp = 1.0 + 0.25 * (len(bh_divs) - 1)

            p_statuses[p_name] = PlanetVargaStatus(
                planet=p_name,
                d1_rashi_idx=r_idx,
                d1_house=h_d1,
                d9_rashi_idx=r_d9,
                d9_house=h_d9,
                d10_rashi_idx=r_d10,
                d10_house=h_d10,
                d60_rashi_idx=r_d60,
                d60_house=h_d60,
                is_vargottama=is_varg,
                is_bhavottama=is_bhav,
                bhavottama_divisions=tuple(bh_divs),
                amplification_factor=amp,
            )

        # Compute Fused Domain Scores via Signed Addition
        fused_scores: Dict[str, float] = {}

        for domain, weights in DOMAIN_VARGA_WEIGHTS.items():
            tot_weight = sum(weights.values())
            weighted_sum = 0.0

            # Evaluate D1 component (from TPhalitCore vector)
            tphalit_vec = self.tphalit_core.extract_full_vector(d1_chart)
            d1_val = tphalit_vec.domain_scores.get(domain if domain in tphalit_vec.domain_scores else "career", 0.0)
            weighted_sum += weights.get("D1", 0.0) * d1_val

            # Evaluate D9 component (focusing on D9 10th/7th/1st lords)
            if "D9" in weights:
                d9_score = sum(
                    HOUSE_PLACEMENT_WEIGHTS.get(st.d9_house, 0.0) * st.amplification_factor
                    for st in p_statuses.values()
                ) / len(p_statuses)
                weighted_sum += weights["D9"] * d9_score

            # Evaluate D10 component (focusing on D10 10th house and occupants)
            if "D10" in weights:
                d10_score = sum(
                    HOUSE_PLACEMENT_WEIGHTS.get(st.d10_house, 0.0) * st.amplification_factor
                    for st in p_statuses.values()
                ) / len(p_statuses)
                weighted_sum += weights["D10"] * d10_score

            # Evaluate D60 component (micro karmic baseline)
            if "D60" in weights:
                d60_score = sum(
                    HOUSE_PLACEMENT_WEIGHTS.get(st.d60_house, 0.0) * st.amplification_factor
                    for st in p_statuses.values()
                ) / len(p_statuses)
                weighted_sum += weights["D60"] * d60_score

            fused_val = weighted_sum / tot_weight
            fused_scores[domain] = max(-1.0, min(1.0, fused_val))

        overall_harmony = sum(fused_scores.values()) / len(fused_scores)

        return VargaFusionReport(
            planet_statuses=p_statuses,
            fused_domain_scores=fused_scores,
            bhavottama_planets=tuple(bhavottama_list),
            vargottama_planets=tuple(vargottama_list),
            overall_varga_harmony=overall_harmony,
        )
