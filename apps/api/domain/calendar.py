"""
AstroOS — Hindu luni-solar calendar domain models.

Masa (lunar month, Amanta and Purnimanta reckonings) and Samvatsara
(the 60-year Jupiter cycle, reckoned separately from both the Shaka and
Vikram epochs — the two give different names in the same Gregorian year
since 60 does not evenly divide the 135-year gap between epochs).

Does not yet special-case Adhika Masa (intercalary leap month) naming —
the rashi-at-Amavasya rule below assigns the correct month name for the
month itself, but a leap month should additionally carry an "Adhika"
prefix, which this does not add.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MasaInfo:
    """Lunar month, in both regional reckonings."""
    amanta: str        # New-moon-to-new-moon naming (South India, Maharashtra)
    purnimanta: str      # Full-moon-to-full-moon naming (North India)


@dataclass(frozen=True)
class SamvatsaraInfo:
    """Era year + 60-year Jupiter-cycle (Samvatsara) name."""
    shaka_year: int
    shaka_samvatsara: str
    vikram_year: int
    vikram_samvatsara: str


@dataclass(frozen=True)
class CalendarResult:
    masa: MasaInfo
    samvatsara: SamvatsaraInfo
