"""
AstroOS — Lagna Scan Domain Objects

Answers "when does the lagna change?" — the question birth-time
rectification turns on. The ascendant moves roughly 1° every 4 minutes,
so a chart born near a rashi boundary can flip sign on a birth-time
uncertainty of well under a minute, silently changing the lagna lord,
every bhava, and every house-based yoga.

Also reports nakshatra and pada boundaries, which matter separately: the
lagna's nakshatra feeds KP sub-lord work, and pada boundaries shift the
Navamsa placement.

Pure dataclasses, no ORM/Pydantic — same convention as domain/upagraha.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class LagnaInterval:
    """One contiguous stretch during which the lagna sits in a single rashi."""

    rashi: str
    start_utc: datetime
    end_utc: datetime
    duration_minutes: float
    contains_birth: bool = False


@dataclass(frozen=True)
class BoundaryDistance:
    """How far the birth moment sits from a boundary, in time and arc."""

    label: str                  # "rashi" | "nakshatra" | "pada"
    minutes_since_previous: float
    minutes_until_next: float
    degrees_since_previous: float
    degrees_until_next: float


@dataclass(frozen=True)
class LagnaScanResult:
    """Where the birth lagna sits, and how fragile that placement is."""

    # Birth moment
    sidereal_longitude: float
    rashi: str
    rashi_degree: float
    nakshatra: str
    pada: int

    # Sensitivity — the headline number for rectification.
    arcmin_per_minute: float
    """How far the lagna moves per minute of birth-time error, at this
    moment and latitude. Varies with latitude and the rising sign."""

    boundaries: tuple[BoundaryDistance, ...] = ()
    intervals: tuple[LagnaInterval, ...] = ()

    window_start_utc: datetime | None = None
    window_end_utc: datetime | None = None
