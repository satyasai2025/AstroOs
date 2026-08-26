"""
AstroOS — Vaiseshikamsa Domain Models

Vaiseshikamsa represents the classical Parashari system (BPHS Ch. 44) of grading
a planet's strength based on how many divisional charts (vargas) it occupies in
auspicious dignities (Exalted, Moolatrikona, Own Sign, Great Friend / Friend).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

VaiseshikamsaScheme = Literal["shadvarga", "saptavarga", "dasavarga", "shodasavarga"]


@dataclass(frozen=True)
class VargaDignityPlacement:
    """Individual dignity placement of a planet in a specific divisional chart."""
    varga: str
    rashi: str
    dignity: str  # exalted, moolatrikona, own, friendly, neutral, enemy, debilitated
    is_auspicious: bool  # True if exalted, moolatrikona, own, or friendly


@dataclass(frozen=True)
class PlanetVaiseshikamsaResult:
    """Vaiseshikamsa evaluation for a single graha within a varga scheme."""
    planet: str
    scheme: VaiseshikamsaScheme
    total_vargas_evaluated: int
    auspicious_varga_count: int
    swavarga_count: int  # own sign + moolatrikona + exalted
    title: str  # e.g., "Parijata", "Uttama", "Gopura", "None"
    description: str
    placements: tuple[VargaDignityPlacement, ...]


@dataclass(frozen=True)
class VaiseshikamsaChartResult:
    """Vaiseshikamsa results for all classical planets across evaluated schemes."""
    planets: tuple[PlanetVaiseshikamsaResult, ...]
    rule_version: str = "1.0"
