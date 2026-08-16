"""AstroOS — Prashna (Horary) API schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PrashnaArudhaRequest(BaseModel):
    seed_number: int = Field(..., ge=1, le=249, description="Horary number chosen by the querent (1-249).")


class PrashnaArudhaResponse(BaseModel):
    seed_number: int
    sidereal_longitude: float
    rashi: str
    rashi_degree: float
    nakshatra: str
    sign_lord: str
    star_lord: str
    sub_lord: str
    arc_start_degree: float
    arc_end_degree: float


class PrashnaSphutaRequest(BaseModel):
    moment_utc: datetime = Field(..., description="Query/birth moment, UTC.")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    ayanamsa: str = Field("lahiri", description="Ayanamsa system to use.")


class SphutaPositionResponse(BaseModel):
    name: str
    sidereal_longitude: float
    rashi: str
    rashi_degree: float
    nakshatra: str
    pada: int
    nakshatra_lord: str
    house_number: int


class PrashnaSphutaResponse(BaseModel):
    sphutas: list[SphutaPositionResponse]
    ascendant_longitude: float
    gulika_longitude: float
