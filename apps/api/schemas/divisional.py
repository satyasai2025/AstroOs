"""
AstroOS — Divisional Chart API Schemas (Task 5)

Pydantic request/response models for all varga chart endpoints.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from apps.api.schemas.common import BirthDataInput
from apps.api.services.divisional_engine import SUPPORTED_VARGAS

# ── Literals ──────────────────────────────────────────────────────────────────

VargaCode = Literal[
    "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9",
    "D10", "D11", "D12", "D16", "D20", "D24",
    "D27", "D30", "D40", "D45", "D60",
    "D81", "D108", "D144",
]


# ── Request ───────────────────────────────────────────────────────────────────


class VargaChartRequest(BirthDataInput):
    """Request body for computing a single or all divisional chart(s)."""


class CustomVargaChartRequest(BirthDataInput):
    """Request body for an arbitrary D-n chart with no classical rule."""

    scheme: Literal["cyclic", "from_sign"] = Field(
        default="cyclic",
        description=(
            "Which generic division scheme to use. 'cyclic' (Parivritti) cuts "
            "the whole zodiac into equal 30/n° parts numbered continuously from "
            "0° Aries. 'from_sign' restarts the count in every sign, "
            "generalising D12's rule. Ignored when n happens to name a chart "
            "with its own classical rule — that rule is used instead."
        ),
    )


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
    """Response containing all 22 varga charts computed in a single pass."""

    charts: dict[str, VargaChartResponse] = Field(
        description="Mapping of varga code → computed chart (D2 … D60)."
    )
    julian_day: float
    ayanamsa_system: str
