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
    # Added in Module 9 Phase 0 (Foundation Extension): this data was
    # already computed by EphemerisWrapper into the tropical PlanetPosition
    # object in the same conversion loop that builds SiderealPosition, but
    # was previously discarded rather than threaded through — see
    # docs/architecture.md, "Ephemeris Calculation Contract". Defaults keep
    # every existing test/call site that constructs SiderealPosition
    # directly (without these fields) working unchanged.
    latitude_deg: float = 0.0            # ecliptic latitude (tropical == sidereal, unaffected by ayanamsa)
    distance_au: float = 0.0             # geocentric distance, Astronomical Units
    speed_deg_per_day: float = 0.0       # longitude speed; negative = retrograde (magnitude needed for Chesta Bala)
    declination_deg: float = 0.0         # equatorial declination (needed for Ayana Bala)
    # Added for KP (Krishnamurti Paddhati) support: the nakshatra's ruling
    # Graha (Star Lord — same lord as NakshatraInfo.lord, duplicated here so
    # API consumers don't need a second lookup) and the finer Sub Lord,
    # the planet whose proportional (Vimshottari-years-based) slice of the
    # nakshatra this exact longitude falls in. See
    # ephemeris_wrapper.longitude_to_sub_lord for the computation.
    nakshatra_lord: str = ""             # Star Lord
    sub_lord: str = ""                   # KP Sub Lord
    sub_sub_lord: str = ""               # KP Sub Sub Lord (one level finer than sub_lord)
    # Added for Bhava Chalit support: `house_number` (above) is the
    # cuspal/Chalit house — which real cusp-to-cusp span (for whichever
    # house_system was requested) this planet's longitude falls in. This
    # is a SEPARATE number: the Rashi (sign-counting) house, i.e. "how
    # many signs is this planet's sign from the lagna's sign" — the
    # method every house_number used to use unconditionally before the
    # Chalit fix. The two can differ for the same planet whenever a
    # planet sits near a sign boundary and the real cusp doesn't land
    # exactly on that boundary (true for any non-Whole-Sign house
    # system). Classical KP analysis needs both simultaneously.
    rashi_house_number: int = 0


@dataclass(frozen=True)
class Ascendant:
    """Lagna — first house cusp."""
    longitude: float                 # tropical
    sidereal_longitude: float        # sidereal
    rashi: str
    rashi_degree: float
    nakshatra: str
    pada: int
    nakshatra_lord: str = ""         # Star Lord (KP)
    sub_lord: str = ""               # Sub Lord (KP)
    sub_sub_lord: str = ""           # Sub Sub Lord (KP)


@dataclass(frozen=True)
class HouseCusp:
    """A single bhava cusp."""
    house_number: int                # 1–12
    longitude: float                 # tropical longitude of cusp
    sidereal_longitude: float
    rashi: str
    # KP practice reads predictions primarily off cuspal Star Lord / Sub
    # Lord (the "significators" method), not just the cusp's rashi — see
    # ephemeris_wrapper.longitude_to_sub_lord.
    nakshatra_lord: str = ""         # Star Lord (KP)
    sub_lord: str = ""               # Sub Lord (KP)
    sub_sub_lord: str = ""           # Sub Sub Lord (KP)


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
    # Added in Module 9 Phase 0 (Foundation Extension) — needed by Kala
    # Bala's Nathonnata/Ayana/Tribhaga sub-components. Defaults keep
    # existing test/call sites unaffected.
    sunrise_jd: Optional[float] = None   # Julian Day of sunrise on the birth date, at the birth location
    sunset_jd: Optional[float] = None    # Julian Day of sunset on the birth date, at the birth location
    is_daytime_birth: Optional[bool] = None  # True if birth falls between sunrise and sunset
