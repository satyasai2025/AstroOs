"""
AstroOS — Vimsopaka Bala Engine

Computes Vimsopaka Bala ("20-Point Strength Scale") across all 4 Parashari
Varga schemes: Shadvarga (6 vargas), Saptavarga (7 vargas), Dasavarga (10 vargas),
and Shodasavarga (16 vargas).

BPHS Rules & Weights:
--------------------
1. Shadvarga:
   D1(6.0), D2(2.0), D3(4.0), D9(5.0), D12(2.0), D30(1.0) -> Total Weight = 20.0

2. Saptavarga:
   D1(5.0), D2(2.0), D3(3.0), D7(2.5), D9(4.5), D12(2.0), D30(1.0) -> Total Weight = 20.0

3. Dasavarga:
   D1(3.0), D2(1.5), D3(1.5), D7(1.5), D9(3.0), D10(1.5), D12(1.5), D16(1.5), D30(1.5), D60(3.5) -> Total Weight = 20.0

4. Shodasavarga:
   D1(3.5), D2(1.0), D3(1.0), D4(0.5), D7(0.5), D9(3.0), D10(0.5), D12(0.5),
   D16(2.0), D20(0.5), D24(0.5), D27(0.5), D30(1.0), D40(0.5), D45(0.5), D60(4.0) -> Total Weight = 20.0

Dignity Base Points (out of 20):
-------------------------------
- Exalted: 20.0
- Moolatrikona: 18.0
- Own Sign: 15.0
- Friendly Sign: 10.0
- Neutral Sign: 7.0
- Enemy Sign: 5.0
- Debilitated: 0.0

Vimsopaka Strength Classification:
---------------------------------
- >= 15.0: Ati Purna (Full / Exceptionally Strong)
- 10.0 - <15.0: Purna (Good / Strong)
- 5.0 - <10.0: Madhya (Moderate / Average)
- < 5.0: Alpa (Weak / Low Strength)
"""

from __future__ import annotations

from datetime import datetime
from typing import Mapping

from apps.api.domain.horoscope import D1Chart
from apps.api.domain.vimsopaka import (
    SchemeName,
    VargaDignityScore,
    VimsopakaCategory,
    VimsopakaChartResult,
    VimsopakaPlanetResult,
    VimsopakaSchemeResult,
)
from apps.api.services.divisional_engine import DivisionalEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from packages.shared.dignity import compute_dignity_value

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]

# Base points out of 20 for dignity in a varga
DIGNITY_BASE_POINTS: dict[str, float] = {
    "exalted": 20.0,
    "moolatrikona": 18.0,
    "own": 15.0,
    "friendly": 10.0,
    "neutral": 7.0,
    "enemy": 5.0,
    "debilitated": 0.0,
}

# Scheme varga weights (Sum = 20.0 for each scheme)
SCHEME_WEIGHTS: dict[SchemeName, dict[str, float]] = {
    "shadvarga": {
        "D1": 6.0,
        "D2": 2.0,
        "D3": 4.0,
        "D9": 5.0,
        "D12": 2.0,
        "D30": 1.0,
    },
    "saptavarga": {
        "D1": 5.0,
        "D2": 2.0,
        "D3": 3.0,
        "D7": 2.5,
        "D9": 4.5,
        "D12": 2.0,
        "D30": 1.0,
    },
    "dasavarga": {
        "D1": 3.0,
        "D2": 1.5,
        "D3": 1.5,
        "D7": 1.5,
        "D9": 3.0,
        "D10": 1.5,
        "D12": 1.5,
        "D16": 1.5,
        "D30": 1.5,
        "D60": 3.5,
    },
    "shodasavarga": {
        "D1": 3.5,
        "D2": 1.0,
        "D3": 1.0,
        "D4": 0.5,
        "D7": 0.5,
        "D9": 3.0,
        "D10": 0.5,
        "D12": 0.5,
        "D16": 2.0,
        "D20": 0.5,
        "D24": 0.5,
        "D27": 0.5,
        "D30": 1.0,
        "D40": 0.5,
        "D45": 0.5,
        "D60": 4.0,
    },
}


def classify_vimsopaka(score: float) -> VimsopakaCategory:
    """Classify Vimsopaka Bala score into BPHS strength category."""
    if score >= 15.0:
        return "Ati Purna"
    if score >= 10.0:
        return "Purna"
    if score >= 5.0:
        return "Madhya"
    return "Alpa"


class VimsopakaEngine:
    """Computes Vimsopaka Bala for planets across all 4 Parashari Varga schemes."""

    def __init__(
        self,
        divisional_engine: DivisionalEngine | None = None,
        ephemeris_wrapper: EphemerisWrapper | None = None,
    ) -> None:
        if divisional_engine is not None:
            self._divisional_engine = divisional_engine
        else:
            wrapper = ephemeris_wrapper or EphemerisWrapper(ephemeris_path="data/ephemeris")
            self._divisional_engine = DivisionalEngine(wrapper)

    def compute_all(
        self,
        d1_chart: D1Chart,
        *,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
        house_system: str = "W",
    ) -> VimsopakaChartResult:
        """Compute Vimsopaka Bala for all classical grahas."""
        # Pre-compute all required divisional charts once
        all_required_vargas = {
            varga
            for scheme in SCHEME_WEIGHTS.values()
            for varga in scheme.keys()
            if varga != "D1"
        }

        varga_charts = {}
        for varga in sorted(all_required_vargas):
            varga_charts[varga] = self._divisional_engine.compute(
                birth_datetime_utc=birth_datetime_utc,
                latitude=latitude,
                longitude=longitude,
                varga=varga,
                ayanamsa=ayanamsa,
                house_system=house_system,
            )

        planet_results = []
        for planet_name in _CLASSICAL_SEVEN:
            planet_res = self._compute_planet(
                planet_name, d1_chart, varga_charts
            )
            planet_results.append(planet_res)

        return VimsopakaChartResult(planets=tuple(planet_results))

    def _compute_planet(
        self,
        planet: str,
        d1_chart: D1Chart,
        varga_charts: Mapping[str, any],
    ) -> VimsopakaPlanetResult:
        # 1. Map placements across all vargas for this planet
        placements: dict[str, tuple[str, float]] = {}

        # D1 placement
        d1_pos = next((p for p in d1_chart.planets if p.planet == planet), None)
        if d1_pos:
            placements["D1"] = (d1_pos.rashi, d1_pos.rashi_degree)

        # Divisional placements
        for varga, chart in varga_charts.items():
            pos = next((p for p in chart.planet_positions if p.planet == planet), None)
            if pos:
                placements[varga] = (pos.varga_rashi, pos.varga_rashi_degree)

        # 2. Compute scheme results
        shadvarga = self._compute_scheme("shadvarga", planet, placements)
        saptavarga = self._compute_scheme("saptavarga", planet, placements)
        dasavarga = self._compute_scheme("dasavarga", planet, placements)
        shodasavarga = self._compute_scheme("shodasavarga", planet, placements)

        return VimsopakaPlanetResult(
            planet=planet,
            shadvarga=shadvarga,
            saptavarga=saptavarga,
            dasavarga=dasavarga,
            shodasavarga=shodasavarga,
        )

    def _compute_scheme(
        self,
        scheme_name: SchemeName,
        planet: str,
        placements: dict[str, tuple[str, float]],
    ) -> VimsopakaSchemeResult:
        weights = SCHEME_WEIGHTS[scheme_name]
        total_weight = sum(weights.values())

        varga_breakdown = []
        total_weighted_points = 0.0

        for varga, weight in weights.items():
            if varga in placements:
                rashi, degree = placements[varga]
                dignity_str = compute_dignity_value(planet, rashi, degree) or "neutral"
            else:
                rashi = "unknown"
                dignity_str = "neutral"

            base_points = DIGNITY_BASE_POINTS.get(dignity_str, 7.0)
            weighted_points = (base_points / 20.0) * weight
            total_weighted_points += weighted_points

            varga_breakdown.append(
                VargaDignityScore(
                    varga=varga,
                    varga_rashi=rashi,
                    dignity=dignity_str,
                    weight=weight,
                    base_points=base_points,
                    weighted_points=round(weighted_points, 4),
                )
            )

        final_score = round(total_weighted_points, 4)
        category = classify_vimsopaka(final_score)

        return VimsopakaSchemeResult(
            scheme_name=scheme_name,
            total_weight=total_weight,
            vimsopaka_score=final_score,
            category=category,
            varga_breakdown=tuple(varga_breakdown),
        )
