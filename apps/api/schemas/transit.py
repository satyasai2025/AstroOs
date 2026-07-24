"""
AstroOS — Transit (Gochara) API Schemas

Pydantic request/response models for the standalone "current transits
against a natal chart" endpoint. Structurally different from
Dasha/Divisional's request shape: TransitEngine needs the natal birth
moment (to build the D1 chart it reads Gochara from) PLUS a second,
independent moment in time — the transit moment being checked against
it — so this request carries both.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field, field_validator

AyanamsaCode = Literal["lahiri", "kp", "raman", "yukteshwar", "fagan_bradley", "true_chitra"]
HouseSystemCode = Literal["W", "P", "K", "E"]


# ── Request ───────────────────────────────────────────────────────────────────


class TransitRequest(BaseModel):
    """Request body for computing Gochara (transit) against a natal chart."""

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
        """The transit moment to use: the given value, or now (UTC) if omitted."""
        return self.transit_datetime_utc or datetime.now(timezone.utc)


# ── Response ──────────────────────────────────────────────────────────────────


class TransitPlanetResponse(BaseModel):
    """One transiting planet's position and classical Gochara (transit) read."""

    planet: str
    transit_rashi: str
    house_from_natal_moon: int = Field(
        ge=1, le=12, description="House from natal Moon (1–12) — Gochara's standard reference."
    )
    ashtakavarga_bindus: Optional[int] = Field(
        default=None,
        description="Bindus in the transiting rashi, from natal Bhinnashtakavarga. "
        "None for Rahu/Ketu — not covered by classical Ashtakavarga.",
    )
    is_sade_sati: bool = Field(default=False, description="Only meaningful for Saturn.")
    is_ashtama_shani: bool = Field(default=False, description="Only meaningful for Saturn.")
    is_favorable_house: Optional[bool] = Field(
        default=None,
        description=(
            "True if the current house is a classical good house for this "
            "planet (subject to Vedha), False if a classical bad house "
            "(subject to Vipreet Vedha relief), None if this source states "
            "no rule for this house."
        ),
    )
    has_vedha: bool = Field(
        default=False, description="Good-house effect is currently obstructed by vedha_planet."
    )
    has_vipreet_vedha: bool = Field(
        default=False, description="Bad-house effect is currently relieved by vedha_planet."
    )
    vedha_planet: Optional[str] = None
    transit_nakshatra_sbc: str = Field(
        default="",
        description=(
            "28-system (Abhijit-aware) nakshatra on the Sarvatobhadra Chakra grid — "
            "scoped only to Nakshatra Vedha; every other nakshatra field in this API "
            "uses the standard 27-system."
        ),
    )
    has_nakshatra_vedha: bool = Field(
        default=False,
        description="A different planet currently occupies this planet's SBC Vedha target nakshatra.",
    )
    nakshatra_vedha_planet: Optional[str] = None
    nakshatra_vedha_type: Optional[str] = Field(
        default=None, description="'forward' (direct motion) or 'backward' (retrograde)."
    )
    nakshatra_vedha_target: Optional[str] = Field(
        default=None, description="The SBC nakshatra this planet's Vedha ray points at."
    )
    rule_version: str = "1.0"


class TransitResponse(BaseModel):
    """Full Gochara (transit) response: every graha's current read against the natal chart."""

    transit_datetime_utc: datetime = Field(
        description="The UTC moment transiting positions were computed for."
    )
    natal_moon_rashi: str = Field(
        description="Natal Moon's rashi — the reference point every house_from_natal_moon is counted from."
    )
    planets: list[TransitPlanetResponse]
