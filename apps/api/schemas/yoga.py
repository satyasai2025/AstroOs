"""
AstroOS — Yoga API Schemas

Pydantic request/response models for the Yoga (planetary combination
detection) endpoints. Mirrors the request-shape convention established
in schemas/divisional.py and schemas/dasha.py (birth data + ayanamsa +
house system), since YogaEngine evaluates against an already-built D1
chart built the same way those engines build theirs.

Phase 2 additions (v2.1.0 "Vistara"):
  - YogaResultResponse gains strength_score and counter_examples.
  - YogaActivationResponse / YogaTimelineResponse for dasha correlation.
  - YogaEvaluationRequest gains include_strength, include_timeline, category.
  - YogaEvaluationResponse gains strength_scored / with_timeline flags.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field, field_validator

AyanamsaCode = Literal["lahiri", "kp", "raman", "yukteshwar", "fagan_bradley", "true_chitra"]
HouseSystemCode = Literal["W", "P", "K", "E"]
YogaStrengthCode = Literal["full", "partial", "cancelled"]
DashaSystemCode = Literal["vimshottari", "yogini", "ashtottari", "kalachakra", "chara", "narayana"]


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
    include_strength: Annotated[
        bool,
        Field(
            default=False,
            description=(
                "If true, each yoga result includes a 0-100 numerical "
                "strength score based on planetary dignity, house placement, "
                "aspects, conjunctions, combustion, and retrograde status."
            ),
        ),
    ] = False
    include_timeline: Annotated[
        bool,
        Field(
            default=False,
            description=(
                "If true, the response includes yoga activation timelines "
                "correlated with Dasha periods."
            ),
        ),
    ] = False
    category: Annotated[
        Optional[str],
        Field(
            default=None,
            description=(
                "Filter results to yogas in this category only "
                "(e.g. 'Chandra Yoga', 'Nabhasa Yoga'). "
                "If null, all categories are included."
            ),
        ),
    ] = None
    dasha_system: Annotated[
        DashaSystemCode,
        Field(
            default="vimshottari",
            description=(
                "Dasha system used for timeline activation analysis "
                "(only relevant when include_timeline=True)."
            ),
        ),
    ] = "vimshottari"
    max_depth: Annotated[
        int,
        Field(
            default=3,
            ge=1,
            le=5,
            description=(
                "Dasha nesting depth for timeline analysis "
                "(1=Mahadasha, 2=Antardasha, 3=Pratyantar)."
            ),
        ),
    ] = 3

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
    # Phase 2: numerical strength and counter-examples
    strength_score: Optional[int] = Field(
        default=None,
        description="0-100 numerical strength score (populated when include_strength=True).",
    )
    counter_examples: list[str] = Field(
        default_factory=list,
        description="Classical conditions that weaken or cancel this yoga.",
    )


class YogaEvaluationResponse(BaseModel):
    """Full response for evaluating all (or a filtered subset of) yogas against a chart."""

    results: list[YogaResultResponse]
    total_evaluated: int = Field(description="Number of yoga results returned.")
    total_present: int = Field(description="Number of returned results with is_present=True.")
    strength_scored: bool = Field(
        default=False,
        description="True when results include 0-100 strength scores.",
    )
    with_timeline: bool = Field(
        default=False,
        description="True when the response includes activation timeline data.",
    )


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


# ── Phase 2: Activation / Timeline Responses ──────────────────────────────────


class YogaActivationResponse(BaseModel):
    """One activation entry: a dasha period during which a yoga is active.

    Wraps the YogaActivation dataclass from services/yoga_timeline.py.
    """

    yoga_id: str = Field(description="Yoga being activated.")
    planet: str = Field(description="Involved planet whose dasha is activating the yoga.")
    period_name: str = Field(
        description="Human-readable dasha period name, e.g. 'Jupiter Mahadasha / Saturn Antardasha'.",
    )
    period_level: int = Field(
        ge=1, le=5,
        description="Dasha depth: 1=Mahadasha, 2=Antardasha, 3=Pratyantar, 4=Sookshma, 5=Prana.",
    )
    start_date: date
    end_date: date
    is_current: bool = Field(
        default=False,
        description="True if this activation period contains today's date.",
    )


class YogaTimelineResponse(BaseModel):
    """Activation timeline for a single yoga across all Dasha periods.

    Wraps the YogaTimeline dataclass from services/yoga_timeline.py.
    """

    yoga_id: str
    yoga_name: str
    activations: list[YogaActivationResponse] = Field(default_factory=list)
    current_activation: Optional[YogaActivationResponse] = None


class YogaTimelineEvaluationResponse(BaseModel):
    """Response wrapping all yoga activation timelines for a chart."""

    timelines: list[YogaTimelineResponse]
    total_present: int = Field(description="Number of present yogas with timelines.")
    total_activated: int = Field(description="Number of yogas with at least one activation period.")
    dasha_system: str = Field(description="Dasha system used for timeline computation.")
