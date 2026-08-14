"""
AstroOS — Horoscope API Schemas (Task 4)

Pydantic response models for the D1 chart endpoint.
The router converts D1Chart domain objects to these schemas.
No service-layer code here — pure serialisation contracts.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from apps.api.schemas.common import BirthDataInput


class AscendantSchema(BaseModel):
    """Schema representing ascendant data."""
    longitude: float = Field(description="Tropical ecliptic longitude (°)")
    sidereal_longitude: float = Field(description="Sidereal longitude (°)")
    rashi: str = Field(description="Zodiac sign (English slug)")
    rashi_degree: float = Field(description="Degrees within sign (0–30)")
    nakshatra: str = Field(description="Nakshatra name")
    pada: int = Field(description="Pada (1–4)")
    nakshatra_lord: str = Field(default="", description="Star Lord (KP)")
    sub_lord: str = Field(default="", description="Sub Lord (KP)")
    sub_sub_lord: str = Field(default="", description="Sub Sub Lord (KP)")
    navamsa_rashi: str = Field(default="", description="Navamsa (D9) sign of the ascendant")
    navamsa_rashi_degree: float = Field(default=0.0, description="Degrees within navamsa sign (0–30)")


class HouseCuspSchema(BaseModel):
    """Schema representing house cusp data."""
    house_number: int = Field(ge=1, le=12)
    longitude: float
    sidereal_longitude: float
    rashi: str
    nakshatra_lord: str = Field(default="", description="Star Lord (KP)")
    sub_lord: str = Field(default="", description="Cuspal Sub Lord (KP) — the primary KP significator tool")
    sub_sub_lord: str = Field(default="", description="Cuspal Sub Sub Lord (KP)")


class PlanetPositionSchema(BaseModel):
    """Schema representing planet position data."""
    planet: str
    sidereal_longitude: float
    rashi: str
    rashi_degree: float
    house_number: int = Field(
        ge=1, le=12,
        description="Bhava Chalit (cuspal) house — real cusp-to-cusp span for the requested house_system",
    )
    nakshatra: str
    pada: int = Field(ge=1, le=4)
    is_retrograde: bool
    is_combust: bool
    combustion_orb: Optional[float] = None
    dignity: Optional[str] = None
    nakshatra_lord: str = Field(default="", description="Star Lord (KP)")
    sub_lord: str = Field(default="", description="Sub Lord (KP)")
    sub_sub_lord: str = Field(default="", description="Sub Sub Lord (KP)")
    rashi_house_number: int = Field(
        default=0, ge=0, le=12,
        description="Rashi (sign-counting) house — signs from the lagna's sign; can differ from house_number",
    )
    navamsa_rashi: str = Field(default="", description="Navamsa (D9) sign of the planet")
    navamsa_rashi_degree: float = Field(default=0.0, description="Degrees within navamsa sign (0–30)")


class AspectSchema(BaseModel):
    """Schema representing aspect data."""
    from_planet: str
    to_planet: str
    aspect_type: str
    orb_degrees: float
    is_applying: bool


class PlanetStrengthSchema(BaseModel):
    """Schema representing planet strength data."""
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
    """Schema representing tithi data."""
    number: int = Field(ge=1, le=30)
    name: str
    paksha: str
    completion_percent: float


class YogaSchema(BaseModel):
    """Schema representing yoga data."""
    number: int = Field(ge=1, le=27)
    name: str
    completion_percent: float


class KaranaSchema(BaseModel):
    """Schema representing karana data."""
    number: int
    name: str
    is_fixed: bool


class VaraSchema(BaseModel):
    """Schema representing vara data."""
    number: int = Field(ge=0, le=6)
    name: str
    lord: str


class NakshatraInfoSchema(BaseModel):
    """Schema representing nakshatra info data."""
    nakshatra: str
    nakshatra_number: int = Field(ge=1, le=27)
    pada: int = Field(ge=1, le=4)
    lord: str
    degree_in_nakshatra: float
    degree_in_pada: float


class PanchangaSchema(BaseModel):
    """Schema representing panchanga data."""
    tithi: TithiSchema
    nakshatra: NakshatraInfoSchema
    yoga: YogaSchema
    karana: KaranaSchema
    vara: VaraSchema
    julian_day: float
    ayanamsa_deg: float


class D1ChartRequest(BirthDataInput):
    """Request payload for d1 chart operations."""


class D1ChartResponse(BaseModel):
    """Response payload describing d1 chart data."""
    id: Optional[uuid.UUID] = None
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


class BirthChartSummarySchema(BaseModel):
    """One row in a user's saved-charts list."""
    id: uuid.UUID
    subject_name: str
    birth_datetime_utc: datetime
    birth_latitude: float
    birth_longitude: float
    place_name: Optional[str] = None
    ayanamsa: str
    house_system: str
    lagna_rashi: Optional[str] = None
    moon_nakshatra: Optional[str] = None
    created_at: datetime
    is_default: bool = False

    model_config = {"from_attributes": True}


class BirthChartListResponse(BaseModel):
    """Paginated list of a user's saved charts."""
    charts: list[BirthChartSummarySchema]
    total: int
    limit: int
    offset: int
