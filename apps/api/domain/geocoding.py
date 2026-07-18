"""
AstroOS — Geocoding Domain Objects (v2 Phase A Stabilization)

Birth-place search results and timezone/DST resolution. Pure Python
dataclasses — no ORM/Pydantic dependency, same convention as every
other domain module in this codebase.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PlaceResult:
    """One candidate location from a place-name search."""

    display_name: str
    latitude: float
    longitude: float
    country: Optional[str] = None
    state: Optional[str] = None


@dataclass(frozen=True)
class TimezoneResolution:
    """
    The IANA timezone and actual UTC offset for a specific coordinate
    AND date — not just the coordinate alone, since a location's UTC
    offset can differ by date (DST, or historical zone-rule changes,
    both of which Python's zoneinfo/tzdata resolve correctly from the
    IANA database rather than a naive fixed offset).
    """

    iana_name: str
    utc_offset_minutes: int
    is_dst: bool
