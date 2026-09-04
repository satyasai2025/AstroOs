"""
AstroOS — Astrological Case Similarity & Comparative Research Engine
Inspired by classical KundaleeCompare & Astro-Databank.
Computes multi-dimensional astrological similarity (Lagna, Moon Rashi, Sun Rashi, 10th House Karaka, Dasha Lord) between a native and historical benchmark records.
"""

from __future__ import annotations
from typing import Any, Dict, List

class CaseSimilarityEngine:
    """
    Finds historical horoscopes sharing core astrological signatures with the native.
    """

    @staticmethod
    def calculate_similarity(
        native: dict[str, Any], # {asc_rashi, moon_rashi, sun_rashi, dasha_lord, profession}
        benchmark: dict[str, Any]
    ) -> dict[str, Any]:
        score = 0.0
        matching_factors = []
        
        # 1. Ascendant (Lagna) match - 30 points
        if native.get("asc_rashi") and native.get("asc_rashi") == benchmark.get("asc_rashi"):
            score += 30.0
            matching_factors.append(f"Identical Ascendant in {native['asc_rashi'].title()}")
            
        # 2. Moon Sign (Janma Rashi) match - 25 points
        if native.get("moon_rashi") and native.get("moon_rashi") == benchmark.get("moon_rashi"):
            score += 25.0
            matching_factors.append(f"Same Moon Sign in {native['moon_rashi'].title()}")
            
        # 3. Sun Sign match - 20 points
        if native.get("sun_rashi") and native.get("sun_rashi") == benchmark.get("sun_rashi"):
            score += 20.0
            matching_factors.append(f"Same Sun Sign in {native['sun_rashi'].title()}")
            
        # 4. Same Mahadasha Lord - 15 points
        if native.get("dasha_lord") and native.get("dasha_lord") == benchmark.get("dasha_lord"):
            score += 15.0
            matching_factors.append(f"Synchronous Dasha Lord ({native['dasha_lord'].title()})")
            
        # 5. Career / Archetype resonance - 10 points
        if native.get("category") and native.get("category") == benchmark.get("category"):
            score += 10.0
            matching_factors.append("Archetypal Life Domain Match")
            
        return {
            "name": benchmark.get("name"),
            "dob": benchmark.get("dob"),
            "category": benchmark.get("category"),
            "notes": benchmark.get("notes"),
            "similarity_score": round(score, 1),
            "matching_factors": matching_factors,
        }
