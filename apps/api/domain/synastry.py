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


# ── 1. Comprehensive Kuja Dosha (Manglik) Domain Models ─────────────────────────


@dataclass(frozen=True)
class KujaDoshaProfile:
    """Detailed Tri-Bhava Kuja Dosha analysis for a single chart."""
    chart_name: str
    has_dosha: bool
    severity: str  # 'None', 'Mild', 'Moderate', 'Severe'
    house_from_lagna: Optional[int]
    house_from_moon: Optional[int]
    house_from_venus: Optional[int]
    raw_dosha_points: float  # Lagna(100) + Moon(50) + Venus(25) = max 175
    effective_dosha_score: float  # After classical pariharas (0-100 scale)
    pariharas_applied: tuple[str, ...]
    is_cancelled: bool
    explanation: str


@dataclass(frozen=True)
class KujaDoshaComparison:
    """Cross-chart Kuja Dosha balance evaluation between Partner A and Partner B."""
    partner_a: KujaDoshaProfile
    partner_b: KujaDoshaProfile
    is_balanced: bool
    dosha_difference: float
    compatibility_verdict: str
    classical_mitigation_notes: str


# ── 2. Dasa Kuta (10 Poruthams) Domain Models ──────────────────────────────────


@dataclass(frozen=True)
class DasaKutaItem:
    """Evaluation of a single Porutham in the South Indian 10-Kuta system."""
    name: str  # e.g. 'Dina', 'Gana', 'Mahendra', 'Stree Deergha', 'Yoni', 'Rashi', 'Rashi Adhipati', 'Vashya', 'Rajju', 'Vedha'
    label: str
    is_compatible: bool
    obtained_score: float
    max_score: float
    partner_a_value: str
    partner_b_value: str
    description: str
    classical_source: str


@dataclass(frozen=True)
class DasaKutaResult:
    """Aggregate result for the 10-Porutham compatibility framework."""
    items: tuple[DasaKutaItem, ...]
    total_score: float
    max_total_score: float
    compatibility_percentage: float
    is_rajju_compatible: bool
    is_vedha_compatible: bool
    is_mahendra_present: bool
    is_stree_deergha_present: bool
    verdict: str
    summary: str


# ── 3. Upapada & D9 Navamsha Synastry Domain Models ────────────────────────────


@dataclass(frozen=True)
class UpapadaCompatibility:
    """Jaimini Upapada Lagna (A12) alignment and 2nd house marital sustenance."""
    ul_rashi_a: str
    ul_rashi_b: str
    lagna_rashi_a: str
    lagna_rashi_b: str
    moon_rashi_a: str
    moon_rashi_b: str
    alignment_type: str  # '1/7 Axis', 'Trinal (1/5/9)', 'Mutual Kendra (1/4/7/10)', 'Neutral/Dusthana'
    is_harmonious: bool
    second_from_ul_status_a: str
    second_from_ul_status_b: str
    jaimini_compatibility_score: float  # 0.0 to 100.0
    explanation: str


@dataclass(frozen=True)
class NavamshaSynastryResult:
    """D9 Navamsha divisional cross-chart harmonic resonance."""
    d9_lagna_a: str
    d9_lagna_b: str
    lagna_relationship: str  # 'Conjoined', 'Trinal 5/9', 'Kendra 1/4/7/10', 'Opposite 1/7', 'Shadashtaka 6/8'
    d9_moon_a: str
    d9_moon_b: str
    d9_venus_a: str
    d9_venus_b: str
    mutual_d9_trines: tuple[str, ...]
    navamsha_harmony_score: float  # 0.0 to 100.0
    verdict: str
    explanation: str


# ── 4. Composite & Midpoint Chart Domain Models ────────────────────────────────


@dataclass(frozen=True)
class CompositePlanet:
    """Midpoint planetary position for composite relationship chart."""
    planet: str
    sidereal_longitude: float
    rashi: str
    rashi_degree: float
    house_number: int


@dataclass(frozen=True)
class CompositeChartResult:
    """Midpoint composite horoscope representing the relationship entity."""
    chart_a_name: str
    chart_b_name: str
    composite_ascendant: CompositePlanet
    composite_planets: tuple[CompositePlanet, ...]
    relationship_purpose_summary: str
