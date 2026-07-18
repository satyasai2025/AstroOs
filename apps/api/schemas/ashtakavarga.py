"""
AstroOS — Ashtakavarga API Schemas

Pydantic request/response models for the Ashtakavarga endpoints
(Bhinnashtakavarga per graha, Sarvashtakavarga, and the combined "all"
view). Mirrors the request body shape used by divisional/dasha
endpoints (birth_datetime_utc, latitude, longitude, ayanamsa,
house_system) since AshtakavargaEngine operates on the same D1Chart
those engines build from that data.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

AyanamsaCode = Literal["lahiri", "kp", "raman", "yukteshwar", "fagan_bradley", "true_chitra"]
HouseSystemCode = Literal["W", "P", "K", "E"]


# ── Request ───────────────────────────────────────────────────────────────────


class AshtakavargaRequest(BaseModel):
    """Request body for computing Ashtakavarga from birth data."""

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


class BhinnashtakavargaResponse(BaseModel):
    """One target graha's individual Ashtakavarga bindu table (12 rashis)."""

    target_planet: str = Field(description="The graha this bindu table belongs to.")
    bindus_by_rashi: list[int] = Field(
        description="12 values, index 0 = Aries ... index 11 = Pisces."
    )
    total_bindus: int
    rule_version: str


class SarvashtakavargaResponse(BaseModel):
    """Combined Ashtakavarga — sum of all 7 planetary Bhinnashtakavargas."""

    bindus_by_rashi: list[int] = Field(
        description="12 values, index 0 = Aries ... index 11 = Pisces."
    )
    total_bindus: int
    rule_version: str
    checksum_valid: bool = Field(
        description="True if total_bindus equals the classical expected total of 337."
    )


class AllAshtakavargaResponse(BaseModel):
    """Full Ashtakavarga view: raw + reduced Bhinnashtakavarga, plus Sarvashtakavarga."""

    bhinnashtakavarga: list[BhinnashtakavargaResponse] = Field(
        description="Unreduced Bhinnashtakavarga for all 7 classical grahas."
    )
    bhinnashtakavarga_reduced: list[BhinnashtakavargaResponse] = Field(
        description=(
            "Bhinnashtakavarga after both classical Shodhana (reduction) "
            "passes — Trikona Shodhana then Ekadhipatya Shodhana."
        )
    )
    sarvashtakavarga: SarvashtakavargaResponse
