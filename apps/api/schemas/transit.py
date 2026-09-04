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
from typing import Annotated, Optional

from pydantic import BaseModel, Field, field_validator

from apps.api.schemas.common import BirthDataInput


# ── Request ───────────────────────────────────────────────────────────────────


class TransitRequest(BirthDataInput):
    """Request body for computing Gochara (transit) against a natal chart."""

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
    house_from_natal_ascendant: int = Field(
        default=1, ge=1, le=12, description="House from natal Ascendant (Lagna) (1–12)."
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
    transit_rashi_degree: float = Field(
        default=0.0, description="Degree within transit_rashi, [0, 30)."
    )
    transit_nakshatra: str = Field(
        default="", description="Standard 27-system nakshatra at the transit moment."
    )
    transit_pada: int = Field(default=1, ge=1, le=4, description="Nakshatra pada (1-4).")
    is_retrograde: bool = False
    speed_deg_per_day: float = Field(
        default=0.0, description="Sidereal longitude speed; negative = retrograde."
    )
    gati: str = Field(
        default="sama",
        description=(
            "Classical Ashta Gati speed state: vakra, vikala, mandatara, manda, "
            "sama, chara, or atichara. See services/gati_classifier.py for the "
            "classification rules and its accuracy caveats — Anuvakra/Kutila are "
            "not distinguishable from a single instantaneous position."
        ),
    )


class TransitResponse(BaseModel):
    """Full Gochara (transit) response: every graha's current read against the natal chart."""

    transit_datetime_utc: datetime = Field(
        description="The UTC moment transiting positions were computed for."
    )
    natal_moon_rashi: str = Field(
        description="Natal Moon's rashi — the reference point every house_from_natal_moon is counted from."
    )
    planets: list[TransitPlanetResponse]


# ── Transit Timeline (Animated Mixed Varga / Transit) ─────────────────────────


class TransitTimelinePlanet(BaseModel):
    """One planet's state at a timeline keyframe."""

    planet: str
    sidereal_longitude: float = Field(description="Sidereal longitude in degrees [0, 360).")
    rashi: str = Field(description="Rashi (sign) name.")
    rashi_degree: float = Field(description="Degree within the rashi [0, 30).")
    rashi_minute: int = Field(ge=0, lt=60, description="Minute within the rashi degree.")
    rashi_second: int = Field(ge=0, lt=60, description="Second within the rashi minute.")
    is_direct: bool = Field(description="True = direct motion, False = retrograde.")
    is_station: bool = Field(default=False, description="True if at station (about to change direction).")
    speed_deg_per_day: float = Field(description="Speed in degrees per day (negative = retrograde).")
    nakshatra: str = Field(description="Nakshatra at this longitude.")
    pada: int = Field(ge=1, le=4, description="Nakshatra pada (1-4).")
    degree_in_nakshatra: float = Field(description="Degree within nakshatra [0, 13°20').")
    navamsha_rashi: str = Field(default="", description="D9 Navamsha rashi.")
    navamsha_lord: str = Field(default="", description="D9 Navamsha lord.")
    is_combust: bool = Field(default=False, description="Combustion state.")
    combustion_orb: Optional[float] = Field(default=None, description="Combustion orb in degrees.")
    dignity: Optional[str] = Field(default=None, description="Dignity state.")
    house_from_natal_moon: int = Field(ge=1, le=12, description="Transit house from natal Moon.")
    house_from_natal_ascendant: int = Field(ge=1, le=12, description="Transit house from natal Ascendant.")
    aspects: list[str] = Field(default_factory=list, description="Graha drishti aspects cast.")


class PanchangaKeyframe(BaseModel):
    """Panchanga data at a specific moment."""

    tithi: dict
    nakshatra: dict
    yoga: dict
    karana: dict
    vara: dict
    sunrise: str
    sunset: str
    rahu_kalam: dict
    gulika: dict
    yamaganda: dict
    hora: list[dict]


class TransitEvent(BaseModel):
    """An event detected between keyframes."""

    datetime_utc: datetime
    planet: str
    event_type: str
    description: str
    from_value: Optional[str] = None
    to_value: Optional[str] = None


class TransitTimelineKeyframe(BaseModel):
    """One computed moment in a transit timeline."""

    datetime_utc: datetime
    planets: list[TransitTimelinePlanet]
    panchanga: Optional[PanchangaKeyframe] = None
    events: Optional[list[TransitEvent]] = None


class TransitTimelineRequest(BaseModel):
    """Request body for computing transit timeline."""

    birth_datetime_utc: datetime
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    ayanamsa: str = "lahiri"
    house_system: str = "W"
    start_datetime_utc: datetime
    end_datetime_utc: datetime
    interval_minutes: int = Field(ge=1, le=1440, description="Preferred interval in minutes.")
    adaptive: bool = True
    include_panchanga: bool = True
    include_navamsha: bool = True
    include_combustion: bool = True
    include_dignity: bool = True
    planets: Optional[list[str]] = None

    @field_validator("birth_datetime_utc", "start_datetime_utc", "end_datetime_utc")
    @classmethod
    def must_be_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("datetime fields must be timezone-aware (include UTC offset).")
        return v


class TransitTimelineResponse(BaseModel):
    """Transit timeline response with keyframes and events."""

    request: dict
    keyframes: list[TransitTimelineKeyframe]
    events: list[TransitEvent]
    computed_range: dict
    actual_intervals: Optional[list[int]] = None
