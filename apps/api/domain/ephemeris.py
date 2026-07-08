"""
AstroOS — Ephemeris Domain Objects

Typed, immutable value objects returned by the Swiss Ephemeris wrapper.
No ORM or Pydantic dependencies — pure Python dataclasses.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class DignityType(str, Enum):
    EXALTED = "exalted"
    OWN = "own"
    MOOLATRIKONA = "moolatrikona"
    FRIENDLY = "friendly"
    NEUTRAL = "neutral"
    ENEMY = "enemy"
    DEBILITATED = "debilitated"


@dataclass(frozen=True)
class PlanetPosition:
    """Ecliptic position of a single Graha (tropical coordinates)."""
    planet: str                      # Graha enum value
    longitude: float                 # tropical ecliptic longitude 0–360°
    latitude: float                  # ecliptic latitude
    distance_au: float               # distance in Astronomical Units
    speed_deg_per_day: float         # longitude speed; negative = retrograde
    is_retrograde: bool


@dataclass(frozen=True)
class SiderealPosition:
    """Sidereal position derived from PlanetPosition + ayanamsa."""
    planet: str
    sidereal_longitude: float        # 0–360°
    rashi: str                       # Rashi enum value
    rashi_degree: float              # 0–30° within the sign
    house_number: int                # 1–12 (from lagna)
    nakshatra: str                   # Nakshatra enum value
    pada: int                        # 1–4
    is_retrograde: bool
    is_combust: bool
    combustion_orb: Optional[float]  # degrees from Sun; None for Sun itself
    dignity: Optional[DignityType]


@dataclass(frozen=True)
class Ascendant:
    """Lagna — first house cusp."""
    longitude: float                 # tropical
    sidereal_longitude: float        # sidereal
    rashi: str
    rashi_degree: float
    nakshatra: str
    pada: int


@dataclass(frozen=True)
class HouseCusp:
    """A single bhava cusp."""
    house_number: int                # 1–12
    longitude: float                 # tropical longitude of cusp
    sidereal_longitude: float
    rashi: str


@dataclass(frozen=True)
class NakshatraInfo:
    """Nakshatra details for any ecliptic longitude."""
    nakshatra: str                   # name
    nakshatra_number: int            # 1–27
    pada: int                        # 1–4
    lord: str                        # ruling Graha
    degree_in_nakshatra: float       # 0–13.333°
    degree_in_pada: float            # 0–3.333°


@dataclass(frozen=True)
class TithiInfo:
    """Lunar tithi (lunar day)."""
    number: int                      # 1–30
    name: str
    paksha: str                      # "shukla" or "krishna"
    completion_percent: float        # 0–100


@dataclass(frozen=True)
class YogaInfo:
    """Nithya Yoga (Sun + Moon longitude sum)."""
    number: int                      # 1–27
    name: str
    completion_percent: float


@dataclass(frozen=True)
class KaranaInfo:
    """Half-tithi (Karana)."""
    number: int                      # 1–60
    name: str
    is_fixed: bool


@dataclass(frozen=True)
class VaraInfo:
    """Day of the week (Vara)."""
    number: int                      # 0=Sunday … 6=Saturday
    name: str                        # English
    lord: str                        # Graha lord


@dataclass(frozen=True)
class PanchangaResult:
    """Five limbs of Vedic time calculation."""
    tithi: TithiInfo
    nakshatra: NakshatraInfo
    yoga: YogaInfo
    karana: KaranaInfo
    vara: VaraInfo
    julian_day: float
    ayanamsa_deg: float


@dataclass(frozen=True)
class EphemerisResult:
    """Full ephemeris result for a given moment and location."""
    julian_day: float
    ayanamsa_value: float
    ayanamsa_system: str
    ascendant: Ascendant
    house_cusps: list[HouseCusp]
    planet_positions: list[SiderealPosition]
    panchanga: PanchangaResult
