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

from pydantic import BaseModel, Field

from apps.api.schemas.common import BirthDataInput


# ── Request ───────────────────────────────────────────────────────────────────


class AshtakavargaRequest(BirthDataInput):
    """Request body for computing Ashtakavarga from birth data."""


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
