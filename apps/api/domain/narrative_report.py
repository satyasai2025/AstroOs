"""
AstroOS — Structured Narrative & Comparative Reporting Domain Models (Module 20, Phase 5)

Pure dataclasses for:
1. Standardized 9-Section Astrological Narrative Report
2. Multi-Varga Dignity & Comparative Analysis (D1, D9, D10, D7)
3. Technical Evidence Tables & Cross-Referenced Evidence IDs
4. Chart-vs-Chart / Chart-vs-Transit Comparative Findings
5. Multi-Format Export Models (PDF, HTML, CSV, JSON)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class ReportSectionType(str, Enum):
    SUMMARY = "summary"
    CHART_AND_VARGAS = "chart_and_vargas"
    YOGAS_AND_RULES = "yogas_and_rules"
    DASHA_HIERARCHY = "dasha_hierarchy"
    TRANSITS_AND_ASHTAKAVARGA = "transits_and_ashtakavarga"
    KP_ANALYSIS = "kp_analysis"
    SBC_VEDHAS = "sbc_vedhas"
    COMPARATIVE_FINDINGS = "comparative_findings"
    LIMITATIONS = "limitations"


class VargaDignity(str, Enum):
    EXALTED = "Exalted"
    MOOLATRIKONA = "Moolatrikona"
    OWN_SIGN = "Own Sign"
    FRIENDLY = "Friendly"
    NEUTRAL = "Neutral"
    ENEMY = "Enemy"
    DEBILITATED = "Debilitated"


@dataclass(frozen=True)
class TechnicalEvidenceItem:
    """Individual atomic piece of computed evidence with a unique tracking ID."""
    evidence_id: str  # e.g. "EVID-D1-MOON-01", "EVID-KP-CSL-10"
    category: str
    parameter_name: str
    computed_value: str
    classical_reference: Optional[str] = None
    confidence_or_strength: str = "Deterministic (100%)"


@dataclass(frozen=True)
class MultiVargaGrahaRow:
    """Comparative dignity across D1, D9, D10, D7 for a single graha."""
    planet: str
    d1_rashi: str
    d1_house: int
    d1_dignity: VargaDignity
    d9_rashi: str
    d9_dignity: VargaDignity
    d10_rashi: str
    d10_dignity: VargaDignity
    d7_rashi: str
    d7_dignity: VargaDignity
    is_vargottama: bool  # D1 rashi == D9 rashi


@dataclass(frozen=True)
class NarrativeParagraph:
    """A paragraph of deterministic text cross-referenced to computed evidence."""
    paragraph_index: int
    heading: str
    content_text: str
    referenced_evidence_ids: list[str]


@dataclass(frozen=True)
class StructuredNarrativeSection:
    """A complete section in the 9-section report hierarchy."""
    section_type: ReportSectionType
    title: str
    subtitle: str
    paragraphs: list[NarrativeParagraph]
    evidence_table: list[TechnicalEvidenceItem]
    raw_section_data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ComparativeChartMetrics:
    """Side-by-side comparative analysis of two charts."""
    chart_a_name: str
    chart_b_name: str
    lagna_relationship: str  # e.g. "1-7 (Complementary Opposition)", "6-8 (Shadashtaka Tension)"
    moon_relationship: str   # e.g. "5-9 (Harmonic Trine)"
    ashtakoota_guna_score: Optional[float] = None  # Out of 36
    varga_dignity_overlap_score: float = 0.0
    synastry_aspects: list[str] = field(default_factory=list)
    comparative_summary: str = ""
    evidence_items: list[TechnicalEvidenceItem] = field(default_factory=list)


@dataclass(frozen=True)
class FullStructuredAstrologicalReport:
    """The master 9-section narrative report model."""
    report_id: uuid.UUID
    report_title: str
    subject_name: str
    birth_datetime_iso: str
    latitude: float
    longitude: float
    ayanamsa: str
    house_system: str
    generated_at_iso: str
    
    sections: list[StructuredNarrativeSection]
    multi_varga_matrix: list[MultiVargaGrahaRow]
    all_evidence_index: dict[str, TechnicalEvidenceItem]
    comparative_analysis: Optional[ComparativeChartMetrics] = None
    overall_confluence_summary: str = ""
