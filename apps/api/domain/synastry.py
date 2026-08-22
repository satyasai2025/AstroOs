"""
AstroOS — Inter-Chart Synastry, Ashta-Kuta & Cross-Chart Confluence Domain Models (Priority 13)

Defines dataclasses for:
  - 8-Fold Ashta-Kuta Compatibility (36 Gunas) with granular rule breakdowns & classical textual provenance
  - Classical Dosha Mitigations (Nadi Dosha Parihara, Bhakoot Dosha Parihara)
  - Inter-Chart Planetary Aspects & Angular Harmonics
  - Cross-House Overlays
  - Joint Temporal Confluence Windows (consuming P12/P8 timing engines)
  - Composite Synastry Matrix
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional


class KutaName(str, Enum):
    VARNA = "varna"
    VASHYA = "vashya"
    TARA = "tara"
    YONI = "yoni"
    GRAHA_MAITRI = "graha_maitri"
    GANA = "gana"
    BHAKOOT = "bhakoot"
    NADI = "nadi"


@dataclass(frozen=True)
class KutaEvaluation:
    """Individual evaluation for one of the 8 Ashta-Kutas."""
    kuta: KutaName
    label: str
    obtained_points: float
    max_points: float
    partner_a_attribute: str
    partner_b_attribute: str
    raw_relationship: str
    is_mitigated: bool
    cancellation_reason: Optional[str]
    description: str
    classical_source: str  # e.g., 'Brihat Parashara Hora Shastra, Ch. 73' or 'Muhurta Chintamani, Ch. 2'


@dataclass(frozen=True)
class DoshaParihara:
    """Explicit audit record for classical dosha detection and cancellation."""
    dosha_name: str  # e.g. 'Nadi Dosha', 'Bhakoot Dosha', 'Gana Dosha'
    is_present: bool
    is_cancelled: bool
    parihara_rule: Optional[str]
    classical_reference: str
    explanation: str


@dataclass(frozen=True)
class InterChartAspect:
    """Mutual planetary angular aspect between Chart A and Chart B."""
    planet_a: str
    planet_b: str
    longitude_a: float
    longitude_b: float
    angle_degrees: float
    aspect_type: str  # 'conjunction', 'opposition', 'trine', 'square', 'sextile', 'mutual_vedic_aspect'
    orb_degrees: float
    is_harmonious: bool
    interpretation: str


@dataclass(frozen=True)
class CrossHouseOverlay:
    """Placement of Chart A's planet inside Chart B's house grid."""
    planet_a: str
    chart_a_house: int
    chart_b_house_occupied: int
    rashi_in_chart_b: str
    functional_impact: str


@dataclass(frozen=True)
class JointConfluenceWindow:
    """Synthesized joint timing window where both partners' timing drivers cross activation thresholds."""
    start_date: date
    end_date: date
    chart_a_density_score: float
    chart_b_density_score: float
    joint_confluence_density: float
    chart_a_active_systems: tuple[str, ...]
    chart_b_active_systems: tuple[str, ...]
    objective: str
    synthesis_notes: str


@dataclass(frozen=True)
class SynastryMatrix:
    """Aggregate composite synastry matrix combining structural compatibility, aspect overlays, and joint timing."""
    chart_a_name: str
    chart_b_name: str
    evaluated_at: datetime
    ashta_kuta_evaluations: tuple[KutaEvaluation, ...]
    total_guna_obtained: float
    max_guna_possible: float
    guna_percentage: float
    dosha_pariharas: tuple[DoshaParihara, ...]
    inter_chart_aspects: tuple[InterChartAspect, ...]
    cross_house_overlays: tuple[CrossHouseOverlay, ...]
    joint_confluence_windows: tuple[JointConfluenceWindow, ...]
    structural_summary: str
    timing_summary: str
    provenance_notes: str
