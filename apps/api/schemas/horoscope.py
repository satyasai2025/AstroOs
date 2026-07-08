"""
AstroOS — Horoscope API Schemas (Task 4)

Pydantic response models for the D1 chart endpoint.
The router converts D1Chart domain objects to these schemas.
No service-layer code here — pure serialisation contracts.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AscendantSchema(BaseModel):
    longitude: float = Field(description="Tropical ecliptic longitude (°)")
    sidereal_longitude: float = Field(description="Sidereal longitude (°)")
    rashi: str = Field(description="Zodiac sign (English slug)")
    rashi_degree: float = Field(description="Degrees within sign (0–30)")
    nakshatra: str = Field(description="Nakshatra name")
    pada: int = Field(description="Pada (1–4)")


class HouseCuspSchema(BaseModel):
    house_number: int = Field(ge=1, le=12)
    longitude: float
    sidereal_longitude: float
    rashi: str


class PlanetPositionSchema(BaseModel):
    planet: str
    sidereal_longitude: float
    rashi: str
    rashi_degree: float
    house_number: int = Field(ge=1, le=12)
    nakshatra: str
    pada: int = Field(ge=1, le=4)
    is_retrograde: bool
    is_combust: bool
    combustion_orb: Optional[float] = None
    dignity: Optional[str] = None


class AspectSchema(BaseModel):
    from_planet: str
    to_planet: str
    aspect_type: str
    orb_degrees: float
    is_applying: bool


class PlanetStrengthSchema(BaseModel):
    planet: str
    dignity: Optional[str] = None
    is_retrograde: bool
    is_combust: bool
    house_number: int
    is_in_own_sign: bool
    is_exalted: bool
    is_debilitated: bool
    is_in_kendra: bool
    is_in_trikona: bool
    is_in_dusthana: bool
    strength_score: float = Field(ge=0.0, le=10.0)


class TithiSchema(BaseModel):
    number: int = Field(ge=1, le=30)
    name: str
    paksha: str
    completion_percent: float


class YogaSchema(BaseModel):
    number: int = Field(ge=1, le=27)
    name: str
    completion_percent: float


class KaranaSchema(BaseModel):
    number: int
    name: str
    is_fixed: bool


class VaraSchema(BaseModel):
    number: int = Field(ge=0, le=6)
    name: str
    lord: str


class NakshatraInfoSchema(BaseModel):
    nakshatra: str
    nakshatra_number: int = Field(ge=1, le=27)
    pada: int = Field(ge=1, le=4)
    lord: str
    degree_in_nakshatra: float
    degree_in_pada: float


class PanchangaSchema(BaseModel):
    tithi: TithiSchema
    nakshatra: NakshatraInfoSchema
    yoga: YogaSchema
    karana: KaranaSchema
    vara: VaraSchema
    julian_day: float
    ayanamsa_deg: float


class D1ChartRequest(BaseModel):
    birth_datetime_utc: datetime = Field(
        description="Birth date and time in UTC (ISO 8601 with timezone)"
    )
    latitude: float = Field(ge=-90.0, le=90.0, description="Geographic latitude (+N, -S)")
    longitude: float = Field(ge=-180.0, le=180.0, description="Geographic longitude (+E, -W)")
    ayanamsa: str = Field(
        default="lahiri",
        description="Ayanamsa system: lahiri | kp | raman | yukteshwar | fagan_bradley | true_chitra",
    )
    house_system: str = Field(
        default="W",
        description="House system: W=Whole Sign, P=Placidus, K=Koch, E=Equal",
    )


class D1ChartResponse(BaseModel):
    ascendant: AscendantSchema
    houses: list[HouseCuspSchema]
    planets: list[PlanetPositionSchema]
    aspects: list[AspectSchema]
    planet_strengths: list[PlanetStrengthSchema]
    panchanga: PanchangaSchema
    ayanamsa_system: str
    house_system: str
    julian_day: float
    ayanamsa_value: float

    model_config = {"from_attributes": True}
