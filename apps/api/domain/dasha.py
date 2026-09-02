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
from datetime import date, datetime, timezone
from typing import Optional, Sequence


@dataclass(frozen=True)
class DashaPeriod:
    """
    A single period in the dasha tree at any level (immutable).

    'lord' is the ruling entity for this period:
      - Vimshottari / Ashtottari: Graha name (e.g. "jupiter")
      - Yogini: Yogini name (e.g. "siddha")
      - Kalachakra: Rashi name (e.g. "cancer")
      - Chara / Narayana: Rashi name (e.g. "aries")
    """

    lord: str
    start_date: date | datetime
    end_date: date | datetime
    duration_days: float | int
    level: int
    sub_periods: tuple[DashaPeriod, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not (1 <= self.level <= 5):
            raise ValueError(f"Dasha level must be between 1 and 5, got {self.level}")
        if isinstance(self.sub_periods, list):
            object.__setattr__(self, "sub_periods", tuple(self.sub_periods))

    @property
    def start_datetime_utc(self) -> datetime:
        """Timezone-aware UTC datetime for start boundary."""
        if isinstance(self.start_date, datetime):
            return self.start_date if self.start_date.tzinfo else self.start_date.replace(tzinfo=timezone.utc)
        return datetime(self.start_date.year, self.start_date.month, self.start_date.day, tzinfo=timezone.utc)

    @property
    def end_datetime_utc(self) -> datetime:
        """Timezone-aware UTC datetime for end boundary."""
        if isinstance(self.end_date, datetime):
            return self.end_date if self.end_date.tzinfo else self.end_date.replace(tzinfo=timezone.utc)
        return datetime(self.end_date.year, self.end_date.month, self.end_date.day, tzinfo=timezone.utc)

    @property
    def start_date_only(self) -> date:
        """Normalized date object for start boundary (stripping time component if datetime)."""
        if isinstance(self.start_date, datetime):
            return self.start_date.date()
        return self.start_date

    @property
    def end_date_only(self) -> date:
        """Normalized date object for end boundary (stripping time component if datetime)."""
        if isinstance(self.end_date, datetime):
            return self.end_date.date()
        return self.end_date

    def contains(self, target: date | datetime) -> bool:
        """Check if target date or datetime falls within [start, end]."""
        if isinstance(target, datetime):
            tgt = target if target.tzinfo else target.replace(tzinfo=timezone.utc)
            return self.start_datetime_utc <= tgt <= self.end_datetime_utc
        return self.start_date_only <= target <= self.end_date_only


@dataclass(frozen=True)
class DashaTree:
    """
    Complete dasha calculation result for one birth moment and one dasha system.
    """

    system: str
    """Dasha system name: 'vimshottari', 'yogini', 'ashtottari', 'kalachakra', 'chara', 'narayana'."""

    birth_date: date | datetime
    """Birth date or datetime (UTC)."""

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
    """Total years in one complete dasha cycle (120, 36, 108, 100, 144)."""

    # Self-auditing & reproducibility provenance
    year_convention: str = "365.25_julian"
    """Year length convention: '365.25_julian' (canonical BPHS) or '360_savana'."""
    balance_at_birth: float = 0.0
    """Remaining balance (years) of the starting Mahadasha at birth."""
    moon_longitude_at_trigger: float = 0.0
    """Sidereal longitude of Moon at birth (0-360) used to calculate balance."""
    ayanamsa_used: float = 0.0
    """Numeric ayanamsa value (degrees) applied."""
    birth_datetime_utc: Optional[datetime] = None
    """High-precision birth timestamp."""
    content_hash: str = ""
    """SHA-256 canonical hash of this dasha result."""

    def __post_init__(self) -> None:
        if not (0 <= self.trigger_nakshatra_number <= 27):
            raise ValueError(
                f"trigger_nakshatra_number must be 0-27, got {self.trigger_nakshatra_number}"
            )
        if isinstance(self.mahadashas, list):
            object.__setattr__(self, "mahadashas", tuple(self.mahadashas))

    def validate_tiling(self) -> bool:
        """
        Verify the partitioning invariant: sub-periods must exactly tile
        their parent periods with zero gaps and zero overlaps across the full tree.
        """
        if not self.mahadashas:
            return True
        for i in range(len(self.mahadashas) - 1):
            if self.mahadashas[i].end_date != self.mahadashas[i + 1].start_date:
                raise ValueError(
                    f"Mahadasha tiling gap/overlap between {self.mahadashas[i].lord} and {self.mahadashas[i+1].lord}"
                )
        for md in self.mahadashas:
            _validate_period_tiling(md)
        return True


def _validate_period_tiling(period: DashaPeriod) -> None:
    if not period.sub_periods:
        return
    if period.sub_periods[0].start_date != period.start_date:
        raise ValueError(
            f"First sub-period {period.sub_periods[0].lord} start does not match parent {period.lord} start"
        )
    if period.sub_periods[-1].end_date != period.end_date:
        raise ValueError(
            f"Last sub-period {period.sub_periods[-1].lord} end does not match parent {period.lord} end"
        )
    for i in range(len(period.sub_periods) - 1):
        if period.sub_periods[i].end_date != period.sub_periods[i + 1].start_date:
            raise ValueError(
                f"Sub-period tiling gap/overlap between {period.sub_periods[i].lord} and {period.sub_periods[i+1].lord}"
            )
        _validate_period_tiling(period.sub_periods[i])
    _validate_period_tiling(period.sub_periods[-1])


