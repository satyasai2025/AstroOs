"""
AstroOS — Vimsopaka Bala Domain Objects

Vimsopaka Bala ("20-point strength scale") measures a planet's strength across
divisional charts (vargas) using 4 classical Parashari varga schemes:
Shadvarga (6 vargas), Saptavarga (7 vargas), Dasavarga (10 vargas), and
Shodasavarga (16 vargas).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


SchemeName = Literal["shadvarga", "saptavarga", "dasavarga", "shodasavarga"]
VimsopakaCategory = Literal["Ati Purna", "Purna", "Madhya", "Alpa"]


@dataclass(frozen=True)
class VargaDignityScore:
    """Placement, dignity, and score for a planet in one divisional chart."""
    varga: str
    varga_rashi: str
    dignity: str
    weight: float
    base_points: float
    weighted_points: float


@dataclass(frozen=True)
class VimsopakaSchemeResult:
    """Vimsopaka Bala result for one planet in one Varga scheme."""
    scheme_name: SchemeName
    total_weight: float
    vimsopaka_score: float
    category: VimsopakaCategory
    varga_breakdown: tuple[VargaDignityScore, ...]


@dataclass(frozen=True)
class VimsopakaPlanetResult:
    """Vimsopaka Bala results across all 4 classical schemes for one planet."""
    planet: str
    shadvarga: VimsopakaSchemeResult
    saptavarga: VimsopakaSchemeResult
    dasavarga: VimsopakaSchemeResult
    shodasavarga: VimsopakaSchemeResult


@dataclass(frozen=True)
class VimsopakaChartResult:
    """Complete Vimsopaka Bala analysis for all classical grahas."""
    planets: tuple[VimsopakaPlanetResult, ...]
