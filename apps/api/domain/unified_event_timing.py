"""
AstroOS — Unified Multi-System Event Timing Engine Domain Models

Synchronizes four classical timing pillars into a single unified timing matrix:
  1. Vimshottari Dasha (DashaEngine + find_active_dasha_chain)
  2. Gochara Transits (TransitEngine + VedhaCalculator + AshtakavargaEngine)
  3. Sarvatobhadra Chakra (SBCVedhaEngine + SBCReportService)
  4. KP Cuspal/Sub-Lord Triggers (KPEngine + CSL + Star/Sub triggers)

Every score is derived transparently from observable astrological conditions
without black-box or fabricated probabilities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional


class EventCategory(str, Enum):
    MARRIAGE = "marriage"
    CAREER = "career"
    WEALTH = "wealth"
    PROPERTY = "property"
    FOREIGN_TRAVEL = "foreign_travel"
    HEALTH = "health"
    CHILDBIRTH = "childbirth"
    EDUCATION = "education"


class ConfluenceTier(str, Enum):
    VERY_HIGH = "VERY_HIGH"       # >= 75%
    HIGH = "HIGH"                 # 60 - 74%
    MODERATE = "MODERATE"         # 45 - 59%
    LOW = "LOW"                   # 30 - 44%
    UNFAVORABLE = "UNFAVORABLE"   # < 30%


class WindowConfluenceStatus(str, Enum):
    HIGH_CONFLUENCE = "HIGH_CONFLUENCE"
    MODERATE_CONFLUENCE = "MODERATE_CONFLUENCE"
    PARTIAL_WINDOW = "PARTIAL_WINDOW"
    INHIBITED = "INHIBITED"


# ── Per-System Evidence Containers ──────────────────────────────────────────


@dataclass(frozen=True)
class DashaTimingEvidence:
    """Vimshottari Dasha period activation evidence."""
    active_chain: list[dict[str, Any]]
    significator_lords: list[str]
    is_dasha_active: bool
    active_level: Optional[str]
    active_lord: Optional[str]
    score: float  # 0.0 - 100.0
    detail: str


@dataclass(frozen=True)
class GocharaTransitEvidence:
    """Gochara transits, houses from natal Moon/Lagna, aspects & Vedha."""
    key_transits: list[dict[str, Any]]
    gochara_vedha_clear: bool
    ashtakavarga_support: float  # Average bindus in active transit houses
    sade_sati_status: Optional[str]
    score: float  # 0.0 - 100.0
    detail: str


@dataclass(frozen=True)
class SBCVedhaEvidence:
    """Sarvatobhadra Chakra 28-nakshatra ray paths and Sangya hits."""
    janma_hits: list[dict[str, Any]]
    relevant_sangya_hits: list[dict[str, Any]]
    benefic_count: int
    malefic_count: int
    net_protection: float
    score: float  # 0.0 - 100.0
    detail: str


@dataclass(frozen=True)
class KPTimingEvidence:
    """KP CSL, Star Lord significations, transit sub triggers & veto check."""
    primary_cusp: int
    csl: str
    csl_star_lord: str
    csl_signifies: list[int]
    required_houses: list[int]
    active_transit_triggers: list[dict[str, Any]]
    rp_triggers: list[str]
    dusthana_veto: bool
    fructification: str  # OPEN | PARTIAL | CLOSED
    score: float  # 0.0 - 100.0
    detail: str


# ── Unified Moment Snapshot ──────────────────────────────────────────────────


@dataclass(frozen=True)
class UnifiedTimingSnapshot:
    """
    Synchronized 4-system matrix evaluated at an exact datetime moment.
    """
    evaluated_datetime_utc: datetime
    event_type: str
    dasha: DashaTimingEvidence
    gochara: GocharaTransitEvidence
    sbc: SBCVedhaEvidence
    kp: KPTimingEvidence
    confluence_score: float  # 0.0 - 100.0
    confidence_tier: ConfluenceTier
    system_weights: dict[str, float]
    primary_positive_triggers: list[str]
    primary_inhibiting_factors: list[str]
    summary_narrative: str


# ── Continuous Timeline & Candidate Windows ──────────────────────────────────


@dataclass(frozen=True)
class TimelineSamplePoint:
    """Discrete sample point on the continuous timeline for graph visualization."""
    date: str
    confluence_score: float
    dasha_score: float
    gochara_score: float
    sbc_score: float
    kp_score: float
    peak_flag: bool = False


@dataclass(frozen=True)
class UnifiedEventTimingWindow:
    """Identified high-confluence window for an event over time."""
    window_id: str
    event_type: str
    start_date: date
    end_date: date
    peak_date: date
    peak_score: float
    confluence_status: WindowConfluenceStatus
    system_scores: dict[str, float]
    primary_drivers: list[str]
    inhibiting_factors: list[str]
    narrative: str


@dataclass(frozen=True)
class UnifiedEventTimingScanResult:
    """Full scan result over a requested date range."""
    chart_id: Optional[str]
    event_type: str
    start_date: date
    end_date: date
    evaluated_moment_snapshot: UnifiedTimingSnapshot
    candidate_windows: list[UnifiedEventTimingWindow]
    time_series: list[TimelineSamplePoint]
    confluence_summary: str
