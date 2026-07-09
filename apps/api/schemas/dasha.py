"""
AstroOS — Dasha API Schemas (Task 6)

Pydantic request/response models for all six dasha endpoints.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

AyanamsaCode = Literal["lahiri", "kp", "raman", "yukteshwar", "fagan_bradley", "true_chitra"]
HouseSystemCode = Literal["W", "P", "K", "E"]
DashaSystem = Literal["vimshottari", "yogini", "ashtottari", "kalachakra", "chara", "narayana"]


# ── Request ───────────────────────────────────────────────────────────────────


class DashaRequest(BaseModel):
    """Request body shared by all dasha endpoints."""

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
        Field(default="lahiri", description="Ayanamsa system for sidereal conversion."),
    ] = "lahiri"
    house_system: Annotated[
        HouseSystemCode,
        Field(
            default="W",
            description="House system (used for Lagna in Chara/Narayana; ignored for others).",
        ),
    ] = "W"
    max_depth: Annotated[
        int,
        Field(
            default=3,
            ge=1,
            le=5,
            description=(
                "Nesting depth: 1=Mahadasha, 2=Antardasha, 3=Pratyantar, "
                "4=Sookshma, 5=Prana."
            ),
        ),
    ] = 3

    @field_validator("birth_datetime_utc")
    @classmethod
    def must_be_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("birth_datetime_utc must be timezone-aware.")
        return v


# ── Response ──────────────────────────────────────────────────────────────────


class DashaPeriodResponse(BaseModel):
    """A single period at any level of the dasha tree."""

    lord: str = Field(description="Ruling Graha, Yogini name, or Rashi name.")
    start_date: date
    end_date: date
    duration_days: int
    level: int = Field(ge=1, le=5)
    sub_periods: list[DashaPeriodResponse] = Field(
        default_factory=list,
        description="Nested sub-periods (Antardasha, Pratyantar, etc.).",
    )

    model_config = {"populate_by_name": True}


class DashaTreeResponse(BaseModel):
    """Full dasha tree response for one system."""

    system: str = Field(description="Dasha system name.")
    birth_date: date
    trigger_planet: str = Field(
        description="First lord / starting sign that determines the opening dasha."
    )
    trigger_nakshatra: str = Field(description="Moon's nakshatra at birth.")
    trigger_nakshatra_number: int = Field(description="Moon's nakshatra number (1–27).")
    mahadashas: list[DashaPeriodResponse]
    max_depth: int
    total_cycle_years: int


# Allow self-referential model
DashaPeriodResponse.model_rebuild()
