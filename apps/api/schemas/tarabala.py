"""
AstroOS — Navatara / Tarabala API Schemas
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, Field, field_validator


class TarabalaReportRequest(BaseModel):
    janma_nakshatra: Annotated[str, Field(description="Standard 27-system natal Moon nakshatra token.")]
    birth_datetime_utc: Annotated[datetime, Field(description="UTC birth datetime (ISO-8601, must include timezone offset).")]
    moment_utc: Annotated[
        Optional[datetime],
        Field(default=None, description="UTC moment to compute Tarabala at. Defaults to the current UTC time."),
    ] = None
    lagna_nakshatra: Annotated[
        Optional[str],
        Field(default=None, description="Standard 27-system Lagna nakshatra token, for the dual-viewpoint best-stars intersection."),
    ] = None
    dasha_chain: Annotated[
        Optional[list[str]],
        Field(default=None, description="Active dasha lords, Mahadasha first (e.g. ['venus','sun','moon']), for lordship Tara convergence."),
    ] = None

    @field_validator("birth_datetime_utc", "moment_utc")
    @classmethod
    def _require_tz(cls, v):
        if v is not None and v.tzinfo is None:
            raise ValueError("datetimes must include a timezone offset")
        return v


class PlanetTaraResponse(BaseModel):
    planet: str
    nakshatra: str
    position: int
    name: str
    is_favorable: bool


class LordshipTaraEntryResponse(BaseModel):
    dasha_level: int
    lord: str
    position_name: str
    is_favorable: bool


class SpecialPointEntryResponse(BaseModel):
    name: str
    from_moon: str
    from_lagna: Optional[str] = None


class TarabalaReportResponse(BaseModel):
    janma_nakshatra: str
    lagna_nakshatra: Optional[str] = None
    moment_utc: datetime
    natal_tarabala: list[PlanetTaraResponse]
    transit_tarabala: list[PlanetTaraResponse]
    lordship_tarabala: list[LordshipTaraEntryResponse]
    favorable_level_count: int
    total_active_levels: int
    all_levels_favorable: bool
    yearly_age: Optional[int] = None
    yearly_position: Optional[int] = None
    yearly_name: Optional[str] = None
    best_stars: Optional[list[str]] = None
    special_points: list[SpecialPointEntryResponse]
