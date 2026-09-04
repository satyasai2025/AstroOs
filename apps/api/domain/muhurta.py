"""
AstroOS — Muhurta and Panchanga domain models.

Contains domain representations for:
- 5 Limbs of Panchanga (Tithi, Vara, Nakshatra, Yoga, Karana) with exact end times and attributes
- Samvatsara and Masa
- Solar and Lunar rise/set timings
- Planetary Horas and Choghadiya periods
- Auspicious and Inauspicious segments (Abhijit, Brahma, Rahu, Gulika, Yamaganda, Durmuhurta, Amrit Kaal)
- Tarabala, Chandrabala, and Panchaka Dosha evaluation
- Activity Suitability Playbook
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class HoraPeriod:
    """One of the 24 unequal-length planetary hours spanning a solar day+night."""
    index: int            # 1–12 within its half (day or night)
    lord: str              # ruling Graha
    start_jd: float
    end_jd: float
    is_day: bool            # True = between sunrise and sunset


@dataclass(frozen=True)
class InauspiciousPeriod:
    """A single inauspicious segment (Rahukalam / Gulikalam / Yamagandam / Durmuhurta)."""
    name: str
    start_jd: float
    end_jd: float


@dataclass(frozen=True)
class AuspiciousWindowPeriod:
    """An auspicious timing window (Abhijit / Brahma / Amrit Kaal / Vijaya)."""
    name: str
    start_jd: float
    end_jd: float
    is_auspicious: bool = True
    description: str = ""


@dataclass(frozen=True)
class ChoghadiyaPeriod:
    """One of the 8 day or 8 night Choghadiya segments (1/8 of daylight or night)."""
    index: int              # 1–8 within its half (day or night)
    name: str               # Udveg | Chal | Labh | Amrit | Kaal | Shubh | Rog
    nature: str              # "auspicious" | "inauspicious"
    start_jd: float
    end_jd: float
    is_day: bool
    lord: str = ""


@dataclass(frozen=True)
class TithiLimbInfo:
    number: int             # 1-30
    name: str               # Pratipada ... Purnima/Amavasya
    paksha: str             # "shukla" | "krishna"
    completion_percent: float
    end_jd: Optional[float]
    lord: str
    group: str              # Nanda, Bhadra, Jaya, Rikta, Poorna


@dataclass(frozen=True)
class VaraLimbInfo:
    number: int             # 0=Sunday ... 6=Saturday
    name: str               # Sunday / Ravivara ...
    lord: str               # Sun / Surya ...
    nature: str             # "Dhruva / Auspicious", etc.


@dataclass(frozen=True)
class NakshatraLimbInfo:
    number: int             # 1-27
    name: str               # Ashwini ...
    pada: int               # 1-4
    lord: str               # Ketu ...
    degree_in_nakshatra: float
    completion_percent: float
    end_jd: Optional[float]
    quality: str            # Dhruva (Fixed), Chara (Movable), etc.


@dataclass(frozen=True)
class YogaLimbInfo:
    number: int             # 1-27
    name: str               # Vishkambha ...
    completion_percent: float
    end_jd: Optional[float]
    meaning: str


@dataclass(frozen=True)
class KaranaLimbInfo:
    number: int             # 1-60
    name: str               # Bava, Balava ...
    is_fixed: bool
    completion_percent: float
    end_jd: Optional[float]
    nature: str


@dataclass(frozen=True)
class SamvatsaraMasaLimbInfo:
    shaka_year: int
    shaka_samvatsara: str
    vikram_year: int
    vikram_samvatsara: str
    amanta_masa: str
    purnimanta_masa: str
    is_adhika: bool = False


@dataclass(frozen=True)
class CelestialBodiesInfo:
    sun_sign: str
    sun_sign_degree: float
    sun_longitude: float
    moon_sign: str
    moon_sign_degree: float
    moon_longitude: float
    ascendant_sign: str
    ascendant_degree: float
    moonrise_jd: Optional[float] = None
    moonset_jd: Optional[float] = None


@dataclass(frozen=True)
class TarabalaDetailInfo:
    tara_number: int        # 1-9
    tara_name: str
    is_auspicious: bool
    score: float
    description: str


@dataclass(frozen=True)
class ChandrabalaDetailInfo:
    house_from_natal_moon: int # 1-12
    status: str
    is_auspicious: bool
    score: float
    description: str


@dataclass(frozen=True)
class PanchakaDetailInfo:
    remainder: int
    panchaka_name: str
    description: str
    has_dosha: bool
    score: float


@dataclass(frozen=True)
class ActivitySuitabilityDetail:
    activity_id: str
    name: str
    score: float
    verdict: str
    points: list[str]


@dataclass(frozen=True)
class MuhurtaResult:
    """Muhurta and Panchanga timings for one calendar day/moment at a given location."""
    sunrise_jd: float
    sunset_jd: float
    next_sunrise_jd: float
    horas: list[HoraPeriod]
    rahukalam: InauspiciousPeriod
    gulikalam: InauspiciousPeriod
    yamagandam: InauspiciousPeriod
    choghadiya: list[ChoghadiyaPeriod]
    
    # Extended Full Panchanga & Auspicious Timings
    tithi: Optional[TithiLimbInfo] = None
    vara: Optional[VaraLimbInfo] = None
    nakshatra: Optional[NakshatraLimbInfo] = None
    yoga: Optional[YogaLimbInfo] = None
    karana: Optional[KaranaLimbInfo] = None
    calendar: Optional[SamvatsaraMasaLimbInfo] = None
    celestial: Optional[CelestialBodiesInfo] = None
    
    abhijit_muhurta: Optional[AuspiciousWindowPeriod] = None
    brahma_muhurta: Optional[AuspiciousWindowPeriod] = None
    dur_muhurta: list[InauspiciousPeriod] = field(default_factory=list)
    amrit_kaal: Optional[AuspiciousWindowPeriod] = None
    
    tarabala: Optional[TarabalaDetailInfo] = None
    chandrabala: Optional[ChandrabalaDetailInfo] = None
    panchaka: Optional[PanchakaDetailInfo] = None
    activities: list[ActivitySuitabilityDetail] = field(default_factory=list)
