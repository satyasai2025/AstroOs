"""
AstroOS — Shodhya Pinda Calculator (Ashtakavarga Module 10 Phase 3)
==================================================================
Implements classical Parashari Shodhya Pinda (शोध्य पिण्ड) calculation:
  Source: BPHS Chapter 68 & C.S. Patel & Aiyar (1957), p. 50-55

Formulas:
  1. Rashi Pinda (राशि पिण्ड):
     Multiply the Shodhita (reduced) bindus of each sign by its Rashi Gunakara (multiplier):
       Aries: 7, Taurus: 10, Gemini: 8, Cancer: 4, Leo: 10, Virgo: 5,
       Libra: 7, Scorpio: 8, Sagittarius: 9, Capricorn: 5, Aquarius: 11, Pisces: 12
     Sum of all 12 products = Rashi Pinda.

  2. Graha Pinda (ग्रह पिण्ड):
     Multiply the Shodhita bindus of the sign occupied by each planet by its Graha Gunakara:
       Sun: 5, Moon: 5, Mars: 8, Mercury: 5, Jupiter: 10, Venus: 7, Saturn: 5
     Sum across all occupied planets = Graha Pinda.

  3. Shodhya Pinda (शोध्य पिण्ड):
     Shodhya Pinda = Rashi Pinda + Graha Pinda.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from packages.shared.enums import Rashi

_RASHI_LIST = [r.value for r in Rashi]

# 1. Classical Rashi Multipliers (राशि गुणक)
RASHI_GUNAKARA: dict[str, int] = {
    "aries":       7,
    "taurus":      10,
    "gemini":      8,
    "cancer":      4,
    "leo":         10,
    "virgo":       5,
    "libra":       7,
    "scorpio":     8,
    "sagittarius": 9,
    "capricorn":   5,
    "aquarius":    11,
    "pisces":      12,
}

# 2. Classical Graha Multipliers (ग्रह गुणक)
GRAHA_GUNAKARA: dict[str, int] = {
    "sun":     5,
    "moon":    5,
    "mars":    8,
    "mercury": 5,
    "jupiter": 10,
    "venus":   7,
    "saturn":  5,
}

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]


_RULE_VERSION = "0.9-provisional"


@dataclass(frozen=True)
class ShodhyaPindaResult:
    planet: str
    rashi_pinda: int
    graha_pinda: int
    shodhya_pinda: int
    reduced_bindus: tuple[int, ...]
    rule_version: str = _RULE_VERSION


class ShodhyaPindaCalculator:
    """Calculates Rashi Pinda, Graha Pinda, and Shodhya Pinda for each planet."""

    def calculate_for_planet(
        self,
        planet: str,
        reduced_bindus: tuple[int, ...] | list[int],
        planet_positions_rashi: dict[str, str],
    ) -> ShodhyaPindaResult:
        if len(reduced_bindus) != 12:
            raise ValueError(f"Reduced bindus must have 12 entries, got {len(reduced_bindus)}")

        # 1. Rashi Pinda
        rashi_pinda = 0
        for i, r_name in enumerate(_RASHI_LIST):
            rashi_pinda += int(reduced_bindus[i]) * RASHI_GUNAKARA[r_name]

        # 2. Graha Pinda
        graha_pinda = 0
        for p_name in _CLASSICAL_SEVEN:
            occ_rashi = planet_positions_rashi.get(p_name)
            if occ_rashi and occ_rashi.lower() in _RASHI_LIST:
                r_idx = _RASHI_LIST.index(occ_rashi.lower())
                bindus_in_sign = int(reduced_bindus[r_idx])
                graha_pinda += bindus_in_sign * GRAHA_GUNAKARA[p_name]

        # 3. Total Shodhya Pinda
        total_pinda = rashi_pinda + graha_pinda

        return ShodhyaPindaResult(
            planet=planet,
            rashi_pinda=rashi_pinda,
            graha_pinda=graha_pinda,
            shodhya_pinda=total_pinda,
            reduced_bindus=tuple(reduced_bindus),
        )

    def calculate_all(
        self,
        reduced_bav_map: dict[str, tuple[int, ...] | list[int]],
        planet_positions_rashi: dict[str, str],
    ) -> dict[str, ShodhyaPindaResult]:
        results = {}
        for p in _CLASSICAL_SEVEN:
            if p in reduced_bav_map:
                results[p] = self.calculate_for_planet(
                    planet=p,
                    reduced_bindus=reduced_bav_map[p],
                    planet_positions_rashi=planet_positions_rashi,
                )
        return results