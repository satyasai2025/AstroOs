"""AstroOS — Muhurta and Panchanga API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class HoraResponse(BaseModel):
    index: int = Field(..., description="1–12 within its half (day or night)")
    lord: str = Field(..., description="Ruling Graha")
    start: datetime
    end: datetime
    is_day: bool


class InauspiciousPeriodResponse(BaseModel):
    name: str
    start: datetime
    end: datetime


class AuspiciousWindowResponse(BaseModel):
    name: str
    start: datetime
    end: datetime
    is_auspicious: bool = True
    description: str = ""


class ChoghadiyaResponse(BaseModel):
    index: int = Field(..., description="1–8 within its half (day or night)")
    name: str
    nature: str = Field(..., description="'auspicious' or 'inauspicious'")
    start: datetime
    end: datetime
    is_day: bool
    lord: str = ""


class TithiLimbResponse(BaseModel):
    number: int
    name: str
    paksha: str
    completion_percent: float
    end_time: Optional[datetime] = None
    lord: str
    group: str


class VaraLimbResponse(BaseModel):
    number: int
    name: str
    lord: str
    nature: str


class NakshatraLimbResponse(BaseModel):
    number: int
    name: str
    pada: int
    lord: str
    degree_in_nakshatra: float
    completion_percent: float
    end_time: Optional[datetime] = None
    quality: str


class YogaLimbResponse(BaseModel):
    number: int
    name: str
    completion_percent: float
    end_time: Optional[datetime] = None
    meaning: str


class KaranaLimbResponse(BaseModel):
    number: int
    name: str
    is_fixed: bool
    completion_percent: float
    end_time: Optional[datetime] = None
    nature: str


class SamvatsaraMasaResponse(BaseModel):
    shaka_year: int
    shaka_samvatsara: str
    vikram_year: int
    vikram_samvatsara: str
    amanta_masa: str
    purnimanta_masa: str
    is_adhika: bool = False


class CelestialBodiesResponse(BaseModel):
    sun_sign: str
    sun_sign_degree: float
    sun_longitude: float
    moon_sign: str
    moon_sign_degree: float
    moon_longitude: float
    ascendant_sign: str
    ascendant_degree: float
    moonrise: Optional[datetime] = None
    moonset: Optional[datetime] = None


class TarabalaDetailResponse(BaseModel):
    tara_number: int
    tara_name: str
    is_auspicious: bool
    score: float
    description: str


class ChandrabalaDetailResponse(BaseModel):
    house_from_natal_moon: int
    status: str
    is_auspicious: bool
    score: float
    description: str


class PanchakaDetailResponse(BaseModel):
    remainder: int
    panchaka_name: str
    description: str
    has_dosha: bool
    score: float


class ActivitySuitabilityResponse(BaseModel):
    activity_id: str
    name: str
    score: float
    verdict: str
    points: list[str]


class MuhurtaResponse(BaseModel):
    sunrise: datetime
    sunset: datetime
    next_sunrise: datetime
    horas: list[HoraResponse]
    rahukalam: InauspiciousPeriodResponse
    gulikalam: InauspiciousPeriodResponse
    yamagandam: InauspiciousPeriodResponse
    choghadiya: list[ChoghadiyaResponse]
    
    # Extended Full Panchanga & Auspicious Timings
    tithi: Optional[TithiLimbResponse] = None
    vara: Optional[VaraLimbResponse] = None
    nakshatra: Optional[NakshatraLimbResponse] = None
    yoga: Optional[YogaLimbResponse] = None
    karana: Optional[KaranaLimbResponse] = None
    calendar: Optional[SamvatsaraMasaResponse] = None
    celestial: Optional[CelestialBodiesResponse] = None
    
    abhijit_muhurta: Optional[AuspiciousWindowResponse] = None
    brahma_muhurta: Optional[AuspiciousWindowResponse] = None
    dur_muhurta: list[InauspiciousPeriodResponse] = Field(default_factory=list)
    amrit_kaal: Optional[AuspiciousWindowResponse] = None
    
    tarabala: Optional[TarabalaDetailResponse] = None
    chandrabala: Optional[ChandrabalaDetailResponse] = None
    panchaka: Optional[PanchakaDetailResponse] = None
    activities: list[ActivitySuitabilityResponse] = Field(default_factory=list)

