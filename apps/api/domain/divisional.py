"""
AstroOS — Divisional Chart Domain Models (Task 5)

Frozen dataclasses representing a computed Varga (divisional) chart.
No framework dependencies — pure Python.

Supported vargas: D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27, D30, D40, D45, D60
"""

from __future__ import annotations

from dataclasses import dataclass


# ── Per-planet position inside a divisional chart ─────────────────────────────


@dataclass(frozen=True)
class VargaPosition:
    """A single planet's placement inside a divisional chart."""

    planet: str
    """Graha name: sun, moon, mars, mercury, jupiter, venus, saturn, rahu, ketu."""

    # D1 (sidereal) coordinates — kept for traceability
    d1_sidereal_longitude: float
    """Planet's sidereal longitude in the D1 Rashi chart (0–360°)."""
    d1_rashi: str
    """Rashi (sign) in D1."""
    d1_rashi_degree: float
    """Degree within the D1 Rashi (0–30°)."""

    # Varga coordinates
    varga_rashi: str
    """Sign the planet occupies in this divisional chart."""
    varga_rashi_degree: float
    """Degree within that varga sign (0–30°, normalized)."""
    varga_house_number: int
    """House number from the varga lagna (1–12)."""

    # Flags carried from D1
    is_retrograde: bool
    is_combust: bool
    nakshatra: str
    """Nakshatra based on D1 sidereal longitude."""
    pada: int
    """Pada (1–4) of that nakshatra."""


# ── Ascendant in the divisional chart ────────────────────────────────────────


@dataclass(frozen=True)
class VargaAscendant:
    """Lagna (ascendant) position inside a divisional chart."""

    d1_sidereal_longitude: float
    d1_rashi: str
    d1_rashi_degree: float
    varga_rashi: str
    varga_rashi_degree: float


# ── Full divisional chart ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class VargaChart:
    """
    A complete computed divisional (Varga) chart for one birth moment.

    Contains the varga lagna, all 9 Graha positions, and request metadata.
    """

    varga: str
    """Divisional chart code: 'D2', 'D9', 'D60', etc."""
    divisor: int
    """Numeric divisor: 2, 9, 60, etc."""

    ascendant: VargaAscendant
    """Lagna in the varga chart."""

    planet_positions: tuple[VargaPosition, ...]
    """All 9 Grahas in varga placement order (sorted by varga_house_number then planet)."""

    ayanamsa_system: str
    """Ayanamsa used for sidereal conversion."""
    julian_day: float
    """Julian Day of the birth moment."""
