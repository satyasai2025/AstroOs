"""
AstroOS — SBC 10-Sangya Vedha Ray Matrix Domain Objects (Module 19, Phase 4)

Pure dataclasses for:
1. 10 Classical Sangyas (Janma, Karma, Sanghatika, Samudayika, Adhana, Vainashika, Manasa, Jati, Desha, Abhisheka)
2. 9x9 Coordinate Grid Cells (28 Nakshatras with Abhijit, 12 Rashis, Swaras, Vyanjanas, Tithis, Varas)
3. Motion-Based Vedha Rays (Front/Direct, Left/Fast, Right/Retrograde, All 3/Moon)
4. Benefic vs Malefic Obstruction Breakdown & Net Confluence Score
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class VedhaRayDirection(str, Enum):
    FRONT = "Front"  # Direct/Normal motion (Samukha)
    LEFT = "Left"    # Atichara / Fast motion (Vama)
    RIGHT = "Right"  # Vakra / Retrograde motion (Dakshina)
    ALL_THREE = "All Three"  # Chandra / Moon tri-cone ray


class SBCNature(str, Enum):
    NATURAL_BENEFIC = "Natural Benefic"
    NATURAL_MALEFIC = "Natural Malefic"


@dataclass(frozen=True)
class SBCGridCoordinate:
    """Cell position in the 9x9 classical Sarvatobhadra Chakra matrix."""
    row: int  # 0 to 8
    col: int  # 0 to 8
    cell_id: int  # 1 to 81
    element_type: str  # "nakshatra", "rashi", "swara", "vyanjana", "tithi", "vara"
    element_name: str
    element_value: str


@dataclass(frozen=True)
class SBCRayCollision:
    """A single transit ray hitting a natal point or Sangya."""
    transit_planet: str
    is_retrograde: bool
    speed_deg_day: float
    ray_direction: VedhaRayDirection
    source_cell: SBCGridCoordinate
    target_cell: SBCGridCoordinate
    target_sangya: Optional[str]  # e.g., "Janma", "Karma", "Manasa"
    nature: SBCNature
    raw_impact_score: float  # +1.0 for benefic, -1.0 for malefic
    ray_path_coordinates: list[tuple[int, int]]  # Ordered list of (row, col) traversed


@dataclass(frozen=True)
class SangyaVedhaStatus:
    """Net Vedha ray status for one of the 10 classical Sangyas."""
    sangya_key: str
    sangya_name: str  # e.g., "Janma (1st)", "Karma (10th)", "Manasa (25th)"
    domain: str
    natal_nakshatra: str
    natal_nakshatra_number: int
    grid_coord: SBCGridCoordinate
    
    benefic_hits: list[SBCRayCollision]
    malefic_hits: list[SBCRayCollision]
    
    net_score: float  # Benefic sum - Malefic sum
    is_obstructed: bool
    verdict: str
    audit_trace: list[str]


@dataclass(frozen=True)
class SBCCompleteSangyaMatrixReport:
    """Full 10-Sangya transit-to-natal Vedha matrix report."""
    natal_moon_nakshatra: str
    transit_datetime_iso: str
    sangya_statuses: list[SangyaVedhaStatus]
    all_ray_collisions: list[SBCRayCollision]
    overall_sbc_confluence_score: float  # Range: -10.0 to +10.0
    kp_cross_link_summary: str
    audit_trail: list[str]
