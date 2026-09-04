"""
AstroOS — Priority 12: Multi-Dasha Confluence & Yogini Dasha Domain Contract
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Optional


YOGINI_DETAILS = [
    ("mangala", "moon", 1),
    ("pingala", "sun", 2),
    ("dhanya", "jupiter", 3),
    ("bhramari", "mars", 4),
    ("bhadrika", "mercury", 5),
    ("ulka", "saturn", 6),
    ("siddha", "venus", 7),
    ("sankata", "rahu", 8),
]


@dataclass(frozen=True)
class YoginiDashaPeriod:
    """Yogini Dasha period representation (36-year cycle)."""

    yogini_name: str
    lord: str
    duration_years: int
    start_date: date
    end_date: date
    house_activated: int


@dataclass(frozen=True)
class DashaInterval:
    """Standardized dasha interval across Vimshottari, Chara, Yogini, or Kakshya."""

    system_name: str  # vimshottari, chara, yogini, ashtakavarga_kakshya
    lord_or_rashi: str
    level: str  # mahadasha, antardasha, pratyantardasha, rashi_dasha, transit_kakshya
    start_date: date
    end_date: date
    houses_activated: tuple[int, ...]
    promise_score: float  # 0.0 to 100.0


@dataclass(frozen=True)
class ConfluenceWindow:
    """Intersection window where multiple timing systems overlap."""

    window_id: str
    start_date: date
    end_date: date
    duration_days: int
    overlapping_systems: tuple[str, ...]
    system_count: int
    confluence_density_score: float  # 0.0 to 100.0
    activated_houses: tuple[int, ...]
    primary_objective: str
    contributing_dashas: tuple[DashaInterval, ...]


@dataclass(frozen=True)
class MultiDashaConfluenceMatrix:
    """Synthesized polymodal multi-dasha confluence matrix result."""

    chart_id: str
    target_start_date: date
    target_end_date: date
    objective: str
    all_intervals: tuple[DashaInterval, ...]
    confluence_windows: tuple[ConfluenceWindow, ...]
    peak_confluence_window: Optional[ConfluenceWindow]
    consensus_profile_used: str
