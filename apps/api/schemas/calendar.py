"""AstroOS — Calendar (Masa + Samvatsara) API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MasaResponse(BaseModel):
    amanta: str = Field(..., description="New-moon-to-new-moon month name")
    purnimanta: str = Field(..., description="Full-moon-to-full-moon month name")


class SamvatsaraResponse(BaseModel):
    shaka_year: int
    shaka_samvatsara: str
    vikram_year: int
    vikram_samvatsara: str


class CalendarResponse(BaseModel):
    masa: MasaResponse
    samvatsara: SamvatsaraResponse
