"""
AstroOS — Geocoding API Schemas (v2 Phase A Stabilization)
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class PlaceSearchRequest(BaseModel):
    """Request payload for place search operations."""
    query: str = Field(min_length=2, description="Free-text place name, e.g. 'Pune, India'.")
    limit: int = Field(default=8, ge=1, le=20)


class PlaceResultResponse(BaseModel):
    """Response payload describing place result data."""
    display_name: str
    latitude: float
    longitude: float
    country: Optional[str] = None
    state: Optional[str] = None


class PlaceSearchResponse(BaseModel):
    """Response payload describing place search data."""
    results: list[PlaceResultResponse]


class TimezoneResolveRequest(BaseModel):
    """Request payload for timezone resolve operations."""
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    local_date: date = Field(description="The birth date, in local time — determines DST/zone-rule state.")


class TimezoneResolutionResponse(BaseModel):
    """Response payload describing timezone resolution data."""
    iana_name: str
    utc_offset_minutes: int
    is_dst: bool
