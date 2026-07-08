"""
AstroOS — Horoscope Domain Objects (Task 4)

Typed domain objects for D1 birth chart generation.
These are pure Python dataclasses — no ORM or Pydantic dependencies.
"""

from dataclasses import dataclass, field
from typing import Optional

from apps.api.domain.ephemeris import (
    Ascendant,
    DignityType,
    EphemerisResult,
    HouseCusp,
    NakshatraInfo,
    PanchangaResult,
    SiderealPosition,
)


@dataclass(frozen=True)
class AspectInfo:
    """Graha aspect relationship."""
    from_planet: str
    to_planet: str
    aspect_type: str      # "conjunction", "opposition", "trine", "square", "special"
    orb_degrees: float
    is_applying: bool     # True if orb is closing (applying aspect)


@dataclass(frozen=True)
class PlanetStrength:
    """
    Simplified strength assessment for a Graha.

    In a full implementation, this would be full Shadbala. Here we provide
    the key dignity-based and positional assessments.
    """
    planet: str
    dignity: Optional[DignityType]
    is_retrograde: bool
    is_combust: bool
    house_number: int
    is_in_own_sign: bool
    is_exalted: bool
    is_debilitated: bool
    is_in_kendra: bool       # Houses 1, 4, 7, 10
    is_in_trikona: bool      # Houses 1, 5, 9
    is_in_dusthana: bool     # Houses 6, 8, 12
    strength_score: float    # 0.0 – 10.0 composite score


@dataclass(frozen=True)
class D1Chart:
    """
    Rashi Chart (D1 — Janma Kundali).

    The fundamental birth chart in Vedic astrology, generated from the
    Swiss Ephemeris result and annotated with aspects and strength.
    """
    # Raw ephemeris data
    ephemeris: EphemerisResult

    # Derived chart elements
    ascendant: Ascendant
    houses: list[HouseCusp]
    planets: list[SiderealPosition]

    # Analysis
    aspects: list[AspectInfo]
    planet_strengths: list[PlanetStrength]

    # Panchanga
    panchanga: PanchangaResult

    # Chart metadata
    ayanamsa_system: str
    house_system: str
