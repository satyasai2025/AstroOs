"""
AstroOS — Upagraha & Special Lagna API Schemas

Pydantic DTOs for /api/v1/horoscope/upagrahas. Converts to/from the
domain objects in domain/upagraha.py at the router boundary; the engine
never sees these, matching schemas/technique.py's discipline.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from apps.api.schemas.common import BirthDataInput


class UpagrahaRequest(BirthDataInput):
    """Birth data — house_system is accepted but unused: these points are
    always derived from the whole-sign lagna and the sunrise/sunset frame."""


class DerivedPointSchema(BaseModel):
    name: str
    sidereal_longitude: float
    rashi: str
    rashi_degree: float
    nakshatra: str
    pada: int
    nakshatra_lord: str
    house_number: int = Field(description="Bhava counted from the lagna (1-12).")


class UpagrahaResponse(BaseModel):
    upagrahas: list[DerivedPointSchema] = Field(
        description="Shadowy sub-planets: gulika, maandi."
    )
    special_lagnas: list[DerivedPointSchema] = Field(
        description="bhava_lagna, hora_lagna, ghati_lagna."
    )

    # The frame the eighth-part division was built on, so callers can show
    # the working rather than presenting bare longitudes.
    is_daytime_birth: bool
    weekday: str = Field(
        description="Vedic weekday, reckoned sunrise-to-sunrise — a pre-dawn "
                    "birth therefore carries the previous calendar day."
    )
    starting_lord: str = Field(
        description="Graha ruling the first of the eight parts."
    )
    part_duration_minutes: float
