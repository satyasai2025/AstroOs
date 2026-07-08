"""
AstroOS — Divisional Chart API Schemas (Task 5)

Pydantic request/response models for all varga chart endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

from apps.api.services.divisional_engine import SUPPORTED_VARGAS

# ── Literals ──────────────────────────────────────────────────────────────────

VargaCode = Literal[
    "D2", "D3", "D4", "D7", "D9",
    "D10", "D12", "D16", "D20", "D24",
    "D27", "D30", "D40", "D45", "D60",
]

AyanamsaCode = Literal["lahiri", "kp", "raman", "yukteshwar", "fagan_bradley", "true_chitra"]
HouseSystemCode = Literal["W", "P", "K", "E"]


# ── Request ───────────────────────────────────────────────────────────────────


class VargaChartRequest(BaseModel):
    """Request body for computing a single or all divisional chart(s)."""

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
        Field(
            default="W",
            description=(
                "House system used for D1 lagna: "
                "W=Whole Sign, P=Placidus, K=Koch, E=Equal."
            ),
        ),
    ] = "W"

    @field_validator("birth_datetime_utc")
    @classmethod
    def must_be_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("birth_datetime_utc must be timezone-aware (include UTC offset).")
        return v


# ── Response pieces ───────────────────────────────────────────────────────────


class VargaAscendantResponse(BaseModel):
    """Lagna position in the varga chart."""

    d1_sidereal_longitude: float = Field(description="D1 sidereal longitude (0–360°).")
    d1_rashi: str = Field(description="D1 natal sign.")
    d1_rashi_degree: float = Field(description="Degree within D1 sign (0–30°).")
    varga_rashi: str = Field(description="Sign occupied in this varga chart.")
    varga_rashi_degree: float = Field(description="Degree within varga sign (0–30°).")


class VargaPlanetResponse(BaseModel):
    """Single planet's position inside a varga chart."""

    planet: str
    d1_sidereal_longitude: float = Field(description="D1 sidereal longitude (0–360°).")
    d1_rashi: str
    d1_rashi_degree: float
    varga_rashi: str = Field(description="Sign in this varga chart.")
    varga_rashi_degree: float = Field(description="Degree within varga sign (0–30°).")
    varga_house_number: int = Field(ge=1, le=12, description="House from varga lagna (1–12).")
    nakshatra: str
    pada: int = Field(ge=1, le=4)
    is_retrograde: bool
    is_combust: bool


class VargaChartResponse(BaseModel):
    """Full response for a single computed varga chart."""

    varga: str = Field(description="Divisional chart code: D2, D9, D60, etc.")
    divisor: int = Field(description="Numeric divisor.")
    ascendant: VargaAscendantResponse
    planet_positions: list[VargaPlanetResponse]
    ayanamsa_system: str
    julian_day: float


class AllVargaChartsResponse(BaseModel):
    """Response containing all 15 varga charts computed in a single pass."""

    charts: dict[str, VargaChartResponse] = Field(
        description="Mapping of varga code → computed chart (D2 … D60)."
    )
    julian_day: float
    ayanamsa_system: str
