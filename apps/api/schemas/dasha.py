"""
AstroOS — Dasha API Schemas (Task 6)

Pydantic request/response models for all six dasha endpoints.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from apps.api.schemas.common import BirthDataInput

DashaSystem = Literal["vimshottari", "yogini", "ashtottari", "kalachakra", "chara", "narayana"]


# ── Request ───────────────────────────────────────────────────────────────────


class DashaRequest(BirthDataInput):
    """Request body shared by all dasha endpoints."""

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
    persist: Annotated[
        bool,
        Field(
            default=True,
            description=(
                "Whether to save this tree to the dashas table. Set false for "
                "a transient/comparison compute (e.g. browsing a different "
                "dasha system for an already-saved chart) to avoid creating "
                "duplicate birth_charts rows for the same birth input."
            ),
        ),
    ] = True


# ── Response ──────────────────────────────────────────────────────────────────


class DashaPeriodResponse(BaseModel):
    """A single period at any level of the dasha tree."""

    lord: str = Field(description="Ruling Graha, Yogini name, or Rashi name.")
    start_date: datetime | date
    end_date: datetime | date
    duration_days: float | int
    level: int = Field(ge=1, le=5)
    sub_periods: list[DashaPeriodResponse] = Field(
        default_factory=list,
        description="Nested sub-periods (Antardasha, Pratyantar, etc.).",
    )

    model_config = {"populate_by_name": True}


class DashaTreeResponse(BaseModel):
    """Full dasha tree response for one system."""

    system: str = Field(description="Dasha system name.")
    birth_date: datetime | date
    trigger_planet: str = Field(
        description="First lord / starting sign that determines the opening dasha."
    )
    trigger_nakshatra: str = Field(description="Moon's nakshatra at birth.")
    trigger_nakshatra_number: int = Field(description="Moon's nakshatra number (1–27).")
    mahadashas: list[DashaPeriodResponse]
    max_depth: int
    total_cycle_years: float | int


# Allow self-referential model
DashaPeriodResponse.model_rebuild()


class DashaSystemInfo(BaseModel):
    """Metadata describing one registered dasha system, for UI switchers."""

    system: DashaSystem
    label: str
    category: Literal["nakshatra", "sign"]
