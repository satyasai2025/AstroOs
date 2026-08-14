"""
AstroOS — Planet Sign-Change Domain Objects

"When will this planet change sign?" — the planetary counterpart to the
lagna scanner (domain/lagna_scan.py), matching what Jagannatha Hora offers
as "When will this planet change sign in this chart?".

Unlike the lagna, a planet's longitude is NOT monotonic: it stations and
turns retrograde, so it can approach a rashi boundary, reverse, and cross
much later — or in the opposite direction entirely. A linear
degrees-remaining ÷ current-speed estimate is therefore unreliable, and
badly so:

    Jupiter, retrograde at 4.06° Scorpio
        naive : 56 days backward into Libra
        actual: 190 days FORWARD into Sagittarius — it stations direct
                before ever reaching Libra
    Saturn at 7.86° Taurus
        naive : 196 days
        actual: 712 days — a retrograde loop intervenes

Hence these values come from an actual scan, never from extrapolation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class PlanetSignPeriod:
    """A planet's current rashi tenancy, with entry/exit moments."""

    planet: str
    sidereal_longitude: float
    rashi: str
    rashi_degree: float
    nakshatra: str
    pada: int

    is_retrograde: bool
    speed_deg_per_day: float

    entered_utc: Optional[datetime] = None
    exits_utc: Optional[datetime] = None
    days_since_entry: Optional[float] = None
    days_until_exit: Optional[float] = None

    previous_rashi: Optional[str] = None
    next_rashi: Optional[str] = None
    """The rashi it will occupy after `exits_utc` — not necessarily the next
    sign in zodiacal order, since a retrograde planet exits backwards."""

    exits_retrograde: Optional[bool] = None
    """Whether the planet is retrograde at the moment it leaves the sign."""

    search_limit_days: float = 0.0
    """How far the scan looked. `exits_utc is None` means no change was found
    within this window, not that the planet never changes sign."""
