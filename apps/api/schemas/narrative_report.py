"""
AstroOS — Structured Narrative & Comparative Reporting Schemas (Module 20, Phase 5)

Pydantic models for:
  POST /api/v1/report/narrative
  POST /api/v1/report/comparative-narrative
  POST /api/v1/report/export-document
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class TechnicalEvidenceItemSchema(BaseModel):
    evidence_id: str
    category: str
    parameter_name: str
    computed_value: str
    classical_reference: Optional[str] = None
    confidence_or_strength: str = "Deterministic (100%)"


class MultiVargaGrahaRowSchema(BaseModel):
    planet: str
    d1_rashi: str
    d1_house: int
    d1_dignity: str
    d9_rashi: str
    d9_dignity: str
    d10_rashi: str
    d10_dignity: str
    d7_rashi: str
    d7_dignity: str
    is_vargottama: bool


class NarrativeParagraphSchema(BaseModel):
    paragraph_index: int
    heading: str
    content_text: str
    referenced_evidence_ids: list[str]


class StructuredNarrativeSectionSchema(BaseModel):
    section_type: str
    title: str
    subtitle: str
    paragraphs: list[NarrativeParagraphSchema]
    evidence_table: list[TechnicalEvidenceItemSchema]
    raw_section_data: dict[str, Any] = Field(default_factory=dict)


class ComparativeChartMetricsSchema(BaseModel):
    chart_a_name: str
    chart_b_name: str
    lagna_relationship: str
    moon_relationship: str
    ashtakoota_guna_score: Optional[float] = None
    varga_dignity_overlap_score: float
    synastry_aspects: list[str]
    comparative_summary: str
    evidence_items: list[TechnicalEvidenceItemSchema]


class FullStructuredAstrologicalReportResponse(BaseModel):
    report_id: str
    report_title: str
    subject_name: str
    birth_datetime_iso: str
    latitude: float
    longitude: float
    ayanamsa: str
    house_system: str
    generated_at_iso: str
    sections: list[StructuredNarrativeSectionSchema]
    multi_varga_matrix: list[MultiVargaGrahaRowSchema]
    all_evidence_index: dict[str, TechnicalEvidenceItemSchema]
    comparative_analysis: Optional[ComparativeChartMetricsSchema] = None
    overall_confluence_summary: str


class NarrativeReportRequest(BaseModel):
    chart: dict[str, Any]
    subject_name: Optional[str] = "Primary Subject"
    report_title: Optional[str] = "Complete Technical Astrological Report"
    transit_datetime_iso: Optional[str] = None
    ayanamsa: Optional[str] = "lahiri"
    house_system: Optional[str] = "W"


class ComparativeNarrativeReportRequest(BaseModel):
    chart_a: dict[str, Any]
    chart_b: dict[str, Any]
    chart_a_name: Optional[str] = "Person A (Natal)"
    chart_b_name: Optional[str] = "Person B / Event Snapshot"
    report_title: Optional[str] = "Comparative Astrological Synastry & Varga Report"


class DocumentExportRequest(BaseModel):
    report: dict[str, Any]
    export_format: str = Field(description="'pdf', 'html', 'csv', or 'json'")
    include_tables: bool = True


class DocumentExportResponse(BaseModel):
    export_format: str
    filename: str
    mime_type: str
    content_base64_or_text: str
    size_bytes: int
