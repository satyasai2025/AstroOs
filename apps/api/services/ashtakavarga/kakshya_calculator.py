"""
AstroOS — Prastarashtakavarga & Kakshya Calculator (Module 10 Phase 4)
======================================================================
Implements classical Parashari Prastarashtakavarga and Kakshya Subdivisions:
  Source: BPHS Chapter 69 & C.S. Patel & Aiyar (1957)

1. Kakshya Order (Orbital Speed Hierarchy):
   Each rashi (30°) is divided into 8 equal Kakshyas of 3°45' (3.75°) each.
   Order of lords (slowest to fastest):
     Kakshya 1: 0°00' - 3°45'   -> Saturn
     Kakshya 2: 3°45' - 7°30'   -> Jupiter
     Kakshya 3: 7°30' - 11°15'  -> Mars
     Kakshya 4: 11°15' - 15°00' -> Sun
     Kakshya 5: 15°00' - 18°45' -> Venus
     Kakshya 6: 18°45' - 22°30' -> Mercury
     Kakshya 7: 22°30' - 26°15' -> Moon
     Kakshya 8: 26°15' - 30°00' -> Lagna

2. Prastarashtakavarga Matrix:
   8x12 binary grid for each target planet showing bindu contribution
   by each of the 8 kakshya lords across all 12 rashis.
   Sum of column R across all 8 kakshyas = Bhinnashtakavarga bindu count in R!

3. Transit (Gochara) Kakshya Trigger:
   Evaluates whether a transiting planet at sidereal longitude λ has a bindu
   in the active kakshya it is traversing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from packages.shared.ashtakavarga_bindu_table import BINDU_TABLE
from packages.shared.enums import Rashi

_RASHI_LIST = [r.value for r in Rashi]

KAKSHYA_LORDS: tuple[str, ...] = (
    "saturn",
    "jupiter",
    "mars",
    "sun",
    "venus",
    "mercury",
    "moon",
    "lagna",
)

KAKSHYA_SPAN_DEG: float = 3.75  # 3°45'


@dataclass(frozen=True)
class KakshyaTransitEvaluation:
    transiting_planet: str
    transit_longitude: float
    rashi: str
    rashi_index: int
    degree_in_rashi: float
    kakshya_index: int  # 0..7
    kakshya_lord: str
    kakshya_start_deg: float
    kakshya_end_deg: float
    has_bindu: bool
    bav_bindus_in_rashi: int


class KakshyaCalculator:
    """Calculates Prastarashtakavarga matrices and Gochara Kakshya activations."""

    def compute_prastara_matrix(
        self,
        target_planet: str,
        contributor_rashis: dict[str, str],
    ) -> dict[str, list[int]]:
        """
        Returns 8x12 matrix for target_planet:
        dict mapping each kakshya_lord to a list of 12 ints (0 or 1).
        """
        if target_planet not in BINDU_TABLE:
            raise ValueError(f"Target planet {target_planet} not in BINDU_TABLE")

        target_table = BINDU_TABLE[target_planet]
        matrix: dict[str, list[int]] = {lord: [0] * 12 for lord in KAKSHYA_LORDS}

        for contributor, offsets in target_table.items():
            if contributor not in contributor_rashis:
                continue
            c_rashi = contributor_rashis[contributor].lower()
            if c_rashi not in _RASHI_LIST:
                continue
            c_idx = _RASHI_LIST.index(c_rashi)

            for offset in offsets:
                # 1-indexed offset from contributor's sign
                marked_idx = (c_idx + offset - 1) % 12
                matrix[contributor][marked_idx] = 1

        return matrix

    def compute_all_prastara(
        self,
        contributor_rashis: dict[str, str],
    ) -> dict[str, dict[str, list[int]]]:
        return {
            p: self.compute_prastara_matrix(p, contributor_rashis)
            for p in BINDU_TABLE.keys()
        }

    def evaluate_transit_kakshya(
        self,
        transiting_planet: str,
        transit_longitude: float,
        prastara_matrix: dict[str, list[int]],
    ) -> KakshyaTransitEvaluation:
        lon = transit_longitude % 360.0
        r_idx = int(lon // 30.0)
        r_name = _RASHI_LIST[r_idx]
        deg_in_rashi = lon % 30.0

        k_idx = min(int(deg_in_rashi // KAKSHYA_SPAN_DEG), 7)
        k_lord = KAKSHYA_LORDS[k_idx]

        k_start = k_idx * KAKSHYA_SPAN_DEG
        k_end = (k_idx + 1) * KAKSHYA_SPAN_DEG

        has_bindu = bool(prastara_matrix.get(k_lord, [0] * 12)[r_idx] == 1)
        bav_bindus = sum(prastara_matrix[lord][r_idx] for lord in KAKSHYA_LORDS)

        return KakshyaTransitEvaluation(
            transiting_planet=transiting_planet,
            transit_longitude=round(transit_longitude, 4),
            rashi=r_name,
            rashi_index=r_idx,
            degree_in_rashi=round(deg_in_rashi, 4),
            kakshya_index=k_idx,
            kakshya_lord=k_lord,
            kakshya_start_deg=k_start,
            kakshya_end_deg=k_end,
            has_bindu=has_bindu,
            bav_bindus_in_rashi=bav_bindus,
        )