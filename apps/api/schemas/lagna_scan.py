"""
AstroOS — Lagna Scan API Schemas

DTOs for the birth-time rectification endpoints. Converted from
domain/lagna_scan.py at the router boundary; the engine never sees these.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from apps.api.schemas.common import BirthDataInput


class LagnaScanRequest(BirthDataInput):
    window_hours: float = Field(
        default=2.0, gt=0, le=24,
        description="Half-width of the timeline around the birth moment.",
    )


class ShiftBirthtimeRequest(BirthDataInput):
    direction: Literal["next", "previous"] = Field(
        description="Which adjacent rashi to move the lagna into."
    )


class BoundaryDistanceSchema(BaseModel):
    label: str = Field(description="rashi | nakshatra | pada")
    minutes_since_previous: float
    minutes_until_next: float
    degrees_since_previous: float
    degrees_until_next: float


class LagnaIntervalSchema(BaseModel):
    rashi: str
    start_utc: datetime
    end_utc: datetime
    duration_minutes: float
    contains_birth: bool


class LagnaScanResponse(BaseModel):
    sidereal_longitude: float
    rashi: str
    rashi_degree: float
    nakshatra: str
    pada: int

    arcmin_per_minute: float = Field(
        description="How far the lagna moves per minute of birth-time error, "
                    "at this latitude and rising sign. The rectification "
                    "sensitivity — a small number means the lagna is robust "
                    "to an uncertain birth time, a large one means it is not."
    )
    boundaries: list[BoundaryDistanceSchema]
    intervals: list[LagnaIntervalSchema]
    window_start_utc: datetime
    window_end_utc: datetime


class ShiftBirthtimeResponse(BaseModel):
    original_birth_datetime_utc: datetime
    shifted_birth_datetime_utc: datetime
    shift_minutes: float
    direction: str
    resulting_rashi: str
    resulting_rashi_degree: float
