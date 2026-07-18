"""
AstroOS — Yoga API Schemas

Pydantic request/response models for the Yoga (planetary combination
detection) endpoints. Mirrors the request-shape convention established
in schemas/divisional.py and schemas/dasha.py (birth data + ayanamsa +
house system), since YogaEngine evaluates against an already-built D1
chart built the same way those engines build theirs.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field, field_validator

AyanamsaCode = Literal["lahiri", "kp", "raman", "yukteshwar", "fagan_bradley", "true_chitra"]
HouseSystemCode = Literal["W", "P", "K", "E"]
YogaStrengthCode = Literal["full", "partial", "cancelled"]


# ── Request ───────────────────────────────────────────────────────────────────


class YogaEvaluationRequest(BaseModel):
    """Request body for evaluating yoga(s) against a birth chart."""

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
    only_present: Annotated[
        bool,
        Field(
            default=False,
            description=(
                "If true, only yogas that fired (is_present=True) are "
                "returned. Defaults to false, returning every registered "
                "yoga — including ones that did not fire — which is useful "
                "for research comparisons across charts."
            ),
        ),
    ] = False

    @field_validator("birth_datetime_utc")
    @classmethod
    def must_be_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("birth_datetime_utc must be timezone-aware (include UTC offset).")
        return v


# ── Response ──────────────────────────────────────────────────────────────────


class YogaResultResponse(BaseModel):
    """Result of evaluating a single yoga against a chart."""

    yoga_id: str = Field(description="Stable yoga ID, e.g. 'BPHS-PM-001'.")
    name: str
    category: str
    source_text: str
    rule_version: str
    is_present: bool
    strength: Optional[YogaStrengthCode] = None
    involved_planets: list[str] = Field(default_factory=list)
    involved_houses: list[int] = Field(default_factory=list)
    satisfied: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    trace: list[str] = Field(default_factory=list)


class YogaEvaluationResponse(BaseModel):
    """Full response for evaluating all (or a filtered subset of) yogas against a chart."""

    results: list[YogaResultResponse]
    total_evaluated: int = Field(description="Number of yoga results returned.")
    total_present: int = Field(description="Number of returned results with is_present=True.")


class YogaDefinitionResponse(BaseModel):
    """Static, registered metadata for one yoga rule — no chart involved."""

    yoga_id: str
    name: str
    category: str
    source_text: str
    rule_version: str
    requires: list[str] = Field(
        default_factory=list, description="Declared dependencies, e.g. ['D1', 'HouseEngine']."
    )


class YogaCatalogResponse(BaseModel):
    """Full catalog of every registered yoga definition."""

    yogas: list[YogaDefinitionResponse]
    total: int
