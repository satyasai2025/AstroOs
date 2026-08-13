"""
AstroOS — Shared API Schema Primitives

AyanamsaCode, HouseSystemCode, and the 5-field birth-data request block
(birth_datetime_utc/latitude/longitude/ayanamsa/house_system + the
timezone-aware validator) were independently redefined — sometimes
copy-pasted verbatim, sometimes drifting (missing the validator,
different defaults) — across ~15 router schema files. This module is
the single source; every request needing birth data should inherit
BirthDataInput (adding whatever extra fields it needs) rather than
redefine these fields.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

AyanamsaCode = Literal["lahiri", "kp", "raman", "yukteshwar", "fagan_bradley", "true_chitra"]
HouseSystemCode = Literal["W", "P", "K", "E"]


class BirthDataInput(BaseModel):
    """UTC birth datetime + location + ayanamsa/house-system — the
    standard 5-field request block every chart-computing endpoint needs."""

    birth_datetime_utc: Annotated[
        datetime,
        Field(description="UTC birth datetime (ISO-8601, must include timezone offset)."),
    ]
    latitude: Annotated[
        float,
        Field(ge=-90.0, le=90.0, description="Geographic latitude in decimal degrees."),
    ]
    longitude: Annotated[
        float,
        Field(ge=-180.0, le=180.0, description="Geographic longitude in decimal degrees."),
    ]
    ayanamsa: Annotated[
        AyanamsaCode,
        Field(default="lahiri", description="Ayanamsa (sidereal correction) system."),
    ] = "lahiri"
    house_system: Annotated[
        HouseSystemCode,
        Field(default="W", description="House system used for D1 lagna."),
    ] = "W"

    @field_validator("birth_datetime_utc")
    @classmethod
    def must_be_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("birth_datetime_utc must be timezone-aware (include UTC offset).")
        return v
