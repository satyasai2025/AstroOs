"""
AstroOS — Upagraha & Special Lagna Domain Objects

Two families of derived points that classical texts treat as first-class
chart factors, but which are NOT planets — they are computed from the
day/night division and from elapsed time since sunrise:

  Upagrahas (shadowy sub-planets)
    Gulika / Maandi — derived from the eighth-part (Kaala) division of the
    day (sunrise→sunset) or night (sunset→next sunrise), counted from a
    weekday-dependent starting lord.

  Special Lagnas
    Bhava Lagna, Hora Lagna, Ghati Lagna — progressions of the Sun's
    position at sunrise, advancing at 1, 2 and 30 times the rate of a
    standard lagna respectively.

Pure Python dataclasses, no ORM/Pydantic dependency — same convention as
domain/ephemeris.py and domain/jaimini.py.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UpagrahaPosition:
    """One computed upagraha (Gulika, Maandi, ...)."""

    name: str                    # "gulika" | "maandi"
    sidereal_longitude: float    # 0–360
    rashi: str
    rashi_degree: float
    nakshatra: str
    pada: int
    nakshatra_lord: str = ""
    house_number: int = 0        # bhava it falls in, relative to the lagna


@dataclass(frozen=True)
class SpecialLagna:
    """One special lagna (Bhava / Hora / Ghati)."""

    name: str                    # "bhava_lagna" | "hora_lagna" | "ghati_lagna"
    sidereal_longitude: float
    rashi: str
    rashi_degree: float
    nakshatra: str
    pada: int
    nakshatra_lord: str = ""
    house_number: int = 0


@dataclass(frozen=True)
class UpagrahaResult:
    """All derived points for one chart, plus the day/night frame they came from."""

    upagrahas: tuple[UpagrahaPosition, ...] = ()
    special_lagnas: tuple[SpecialLagna, ...] = ()

    # The frame the eighth-part division was built on — surfaced so a caller
    # can show its work rather than presenting bare longitudes.
    is_daytime_birth: bool = False
    period_start_jd: float = 0.0   # sunrise (day birth) or sunset (night birth)
    period_end_jd: float = 0.0     # sunset (day birth) or next sunrise (night birth)
    part_duration_hours: float = 0.0
    weekday: str = ""              # Vedic weekday (from sunrise, not midnight)
    starting_lord: str = ""        # lord of the first eighth-part
