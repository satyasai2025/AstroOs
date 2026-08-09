"""
AstroOS — Transit Patterns API Schemas

Pydantic request/response models for the transit pattern detection endpoint.
Extends the base transit request with configurable aspect and return orbs.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field, field_validator

AyanamsaCode = Literal["lahiri", "kp", "raman", "yukteshwar", "fagan_bradley", "true_chitra"]
HouseSystemCode = Literal["W", "P", "K", "E"]


# ── Request ───────────────────────────────────────────────────────────────────


class TransitPatternsRequest(BaseModel):
    """
    Request body for POST /transit/patterns.

    Same shape as TransitRequest plus configurable orbs for aspect and
    return-period detection.
    """

    birth_datetime_utc: Annotated[
        datetime,
        Field(description="UTC birth datetime (ISO-8601, must include timezone offset)."),
    ]
    latitude: Annotated[
        float,
        Field(ge=-90.0, le=90.0, description="Geographic birth latitude in decimal degrees."),
    ]
    longitude: Annotated[
        float,
        Field(ge=-180.0, le=180.0, description="Geographic birth longitude in decimal degrees."),
    ]
    ayanamsa: Annotated[
        AyanamsaCode,
        Field(default="lahiri", description="Ayanamsa (sidereal correction) system."),
    ] = "lahiri"
    house_system: Annotated[
        HouseSystemCode,
        Field(default="W", description="House system used for the natal D1 lagna."),
    ] = "W"
    transit_datetime_utc: Annotated[
        Optional[datetime],
        Field(
            default=None,
            description=(
                "UTC moment to check transiting planets against (ISO-8601, "
                "must include timezone offset). Defaults to the current "
                "UTC time if omitted."
            ),
        ),
    ] = None
    aspect_orb: Annotated[
        float,
        Field(
            default=6.0,
            ge=0.0,
            le=15.0,
            description="Maximum orb in degrees for aspect detection (0-15).",
        ),
    ] = 6.0
    return_orb: Annotated[
        float,
        Field(
            default=3.0,
            ge=0.0,
            le=10.0,
            description="Maximum orb in degrees for return-period detection (0-10).",
        ),
    ] = 3.0

    @field_validator("birth_datetime_utc")
    @classmethod
    def birth_must_be_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("birth_datetime_utc must be timezone-aware (include UTC offset).")
        return v

    @field_validator("transit_datetime_utc")
    @classmethod
    def transit_must_be_timezone_aware(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None and v.tzinfo is None:
            raise ValueError("transit_datetime_utc must be timezone-aware (include UTC offset).")
        return v

    def resolved_transit_datetime_utc(self) -> datetime:
        """The transit moment: the given value, or now (UTC) if omitted."""
        return self.transit_datetime_utc or datetime.now(timezone.utc)


# ── Response sub-models ───────────────────────────────────────────────────────


class SadeSatiResponse(BaseModel):
    """Sade Sati (Saturn's ~7.5 year transit over natal Moon) status."""

    is_active: bool = Field(description="Whether Sade Sati is currently active.")
    phase: Optional[str] = Field(
        default=None,
        description=(
            "Phase of Sade Sati: 'first_year' (house 12), "
            "'peak' (house 1), 'third_year' (house 2).  None if not active."
        ),
    )
    house_from_moon: Optional[int] = Field(
        default=None, ge=1, le=12,
        description="Saturn's current house from the natal Moon (1-12).",
    )
    start_date: Optional[date] = Field(
        default=None,
        description="Estimated start date of the current Sade Sati period.",
    )
    end_date: Optional[date] = Field(
        default=None,
        description="Estimated end date of the current Sade Sati period.",
    )


class AshtamaShaniResponse(BaseModel):
    """Ashtama Shani (Saturn in 8th from natal Moon) status."""

    is_active: bool = Field(description="Whether Ashtama Shani is currently active.")
    house_from_moon: Optional[int] = Field(
        default=None, ge=1, le=12,
        description="Saturn's current house from the natal Moon (1-12).",
    )
    start_date: Optional[date] = Field(
        default=None,
        description="Estimated start date of the Ashtama Shani period.",
    )
    end_date: Optional[date] = Field(
        default=None,
        description="Estimated end date of the Ashtama Shani period.",
    )


class ReturnPeriodResponse(BaseModel):
    """A single planet's return status."""

    planet: str = Field(description="Graha name.")
    is_at_return: bool = Field(
        description="True if the transiting planet is within orb of its natal position."
    )
    orb: float = Field(
        ge=0.0, le=180.0,
        description="Current angular separation in degrees from its natal position.",
    )
    estimated_return_date: Optional[date] = Field(
        default=None,
        description="Estimated date of the next exact return (within seasonal variation).",
    )


class TransitAspectResponse(BaseModel):
    """
    A Vedic graha drishti (house-based aspect) cast by a transiting planet
    onto a natal planet — same rule table as the natal chart's own aspects
    (services/aspect_engine.py): every planet aspects the 7th house from
    its position, with Mars/Jupiter/Saturn/Rahu/Ketu's classical special
    aspects. Not a Western/Ptolemaic angle aspect.
    """

    aspect_type: str = Field(
        description="Aspect type: 'opposition', 'trine', 'square', or 'special_graha'."
    )
    transiting_planet: str = Field(description="Transiting graha.")
    natal_planet: str = Field(description="Natal graha.")
    orb: float = Field(
        ge=0.0, le=15.0,
        description="Orb within the aspected sign (degrees) — same convention as aspect_engine.py's natal aspect orb, not a Ptolemaic angle orb.",
    )


# ── Response ──────────────────────────────────────────────────────────────────


class TransitPatternsResponse(BaseModel):
    """Complete transit pattern detection response."""

    transit_datetime_utc: datetime = Field(
        description="The UTC moment transiting positions were computed for."
    )
    natal_moon_rashi: str = Field(
        description="Natal Moon's rashi — transit houses are counted from this."
    )
    sade_sati: SadeSatiResponse
    ashtama_shani: AshtamaShaniResponse
    return_periods: list[ReturnPeriodResponse] = Field(
        description="Planetary return status for all 9 grahas."
    )
    aspects: list[TransitAspectResponse] = Field(
        description="Detected transit-to-natal aspects within the configured orb."
    )
