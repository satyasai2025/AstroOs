"""
AstroOS — Dasha Domain Models (Task 6)

Frozen dataclasses representing computed dasha trees.
No framework dependencies — pure Python.

A DashaPeriod is a node in the dasha tree:
  Level 1 = Mahadasha   (main period)
  Level 2 = Antardasha  (sub-period)
  Level 3 = Pratyantar  (sub-sub-period)
  Level 4 = Sookshma    (micro-period)
  Level 5 = Prana       (ultra-micro-period)

Each node may contain sub_periods to the requested depth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class DashaPeriod:
    """
    A single period in the dasha tree at any level.

    'lord' is the ruling entity for this period:
      - Vimshottari / Ashtottari: Graha name (e.g. "jupiter")
      - Yogini: Yogini name (e.g. "siddha")
      - Kalachakra: Rashi name (e.g. "cancer")
      - Chara / Narayana: Rashi name (e.g. "aries")
    """

    lord: str
    start_date: date
    end_date: date
    duration_days: int
    level: int
    sub_periods: tuple[DashaPeriod, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DashaTree:
    """
    Complete dasha calculation result for one birth moment and one dasha system.
    """

    system: str
    """Dasha system name: 'vimshottari', 'yogini', 'ashtottari', 'kalachakra', 'chara', 'narayana'."""

    birth_date: date
    """Birth date (UTC)."""

    # Trigger information (what determined the starting dasha)
    trigger_planet: str
    """For nakshatra-based systems: Moon's nakshatra lord or yogini. For sign-based: Lagna sign."""
    trigger_nakshatra: str
    """Moon's nakshatra at birth (or '' for sign-based systems)."""
    trigger_nakshatra_number: int
    """Moon's nakshatra number 1–27 (or 0 for sign-based)."""

    mahadashas: tuple[DashaPeriod, ...]
    """All Mahadasha periods (level 1) for the full cycle, with nested sub-periods."""

    max_depth: int
    """Depth of sub-period computation (1=Mahadasha only, 5=Prana)."""

    total_cycle_years: int
    """Total years in one complete dasha cycle (120, 36, 108, 100)."""
