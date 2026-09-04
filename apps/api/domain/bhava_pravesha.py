"""
AstroOS — Bhava Pravesha (Bhaavanta) Domain Models
==================================================
Provenance: Kundalee Binary gochar.kkk / Bhaavaanta.VBP (Vinay Jha)
Title: 24-Hour Bhaava Praveshas Of Planets

Siddhantic Invariant:
  "भावप्रवेश कुण्डली का प्रभाव अगली भावप्रवेश कुण्डली तक रहता है।"
  (The transit chart cast at the exact second of a planet's Bhava-entry
   remains the governing seed chart until its subsequent Bhava-entry.)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class BhavaEntryEvent:
    """Represents a single planetary Bhava entry (ingress) event."""
    planet: str
    entered_house: int                       # 1 to 12
    ingress_datetime_utc: datetime           # Exact UTC datetime of ingress
    ingress_time_local_str: str              # HH:MM:SS formatted in target timezone
    planet_sidereal_lon: float               # Sidereal longitude at moment of entry
    cusp_boundary_lon: float                 # Bhava Sandhi (boundary) longitude
    active_until_utc: Optional[datetime]     # Governs until this moment (next ingress)
    duration_minutes: float                  # Active duration in minutes
    is_vidisha_kendrika: bool = False        # True for intermediate angular points


@dataclass(frozen=True)
class DailyBhavaPraveshaSchedule:
    """Complete 24-hour Bhava Pravesha timeline for a given date and location."""
    target_date: date
    latitude: float
    longitude: float
    timezone_offset_hours: float             # e.g. +5.5 for IST, -5.0 for EST, 0.0 for UTC
    timezone_name: str                       # e.g. "IST", "UTC", "EST"
    total_events_count: int                  # Total ingress events (e.g. 96 to 104)
    events_by_planet: Dict[str, Tuple[BhavaEntryEvent, ...]]
    chronological_events: Tuple[BhavaEntryEvent, ...]
    provenance: str = "kundalee-binary gochar.kkk (BhaavantKundalis)"
    rule_version: str = "1.0"
