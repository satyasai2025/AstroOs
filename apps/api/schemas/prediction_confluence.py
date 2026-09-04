"""
AstroOS — Prediction Confluence & Synthesis Schemas (Module 23, Priority 8)

Pydantic schemas for multi-system prediction synthesis, cross-domain scanning,
and freezing into immutable P7 validation snapshots.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field

from apps.api.domain.prediction_confluence import (
    ProvenanceType,
    SynthesizedVerdict,
    SystemSupportStatus,
)
from apps.api.domain.prediction_validation import (
    PredictionCategory,
    TemporalSplitType,
)


class SystemContributionSchema(BaseModel):
    system_id: str
    system_name: str
    support_status: SystemSupportStatus
    provenance_type: ProvenanceType
    primary_houses: list[int]
    active_significators: list[str]
    rule_or_factor: str
    rationale: str
    veto_reason: Optional[str] = None
    evidence_snapshot: dict[str, Any] = Field(default_factory=dict)


class ConfluenceMatrixSchema(BaseModel):
    supporting_count: int
    veto_count: int
    neutral_count: int
    total_systems: int
    confluence_ratio: float
    active_vetoes: list[str]
    synthesized_verdict: SynthesizedVerdict
    verdict_rationale: str


class SynthesizedTimingWindowSchema(BaseModel):
    window_start: datetime
    window_end: datetime
    peak_fructification_date: datetime
    dasha_sub_period: str
    transit_trigger: str
    sbc_trigger_moment: str


class EmpiricalTrackRecordSchema(BaseModel):
    historical_hit_rate: float
    historical_precision: Optional[float] = None
    sample_size: int
    wilson_95_ci: tuple[float, float]
    sample_size_warning: Optional[str] = None
    matched_cohort_name: str = ""


class UnifiedPredictionSynthesisSchema(BaseModel):
    synthesis_id: str
    chart_id: str
    subject_name: str
    category: PredictionCategory
    synthesized_event_description: str
    confluence_matrix: ConfluenceMatrixSchema
    system_contributions: list[SystemContributionSchema]
    synthesized_timing_window: SynthesizedTimingWindowSchema
    empirical_track_record: EmpiricalTrackRecordSchema
    provenance_breakdown: dict[str, list[str]]
    synthesis_timestamp: datetime
    synthesis_hash: str


class ConfluenceSynthesisRequest(BaseModel):
    chart_id: Optional[str] = None
    chart_data: Optional[dict[str, Any]] = None
    category: PredictionCategory = PredictionCategory.CAREER
    target_datetime: Optional[datetime] = None
    horizon_months: int = Field(default=12, ge=1, le=60)


class ConfluenceSynthesisResponse(BaseModel):
    synthesis: UnifiedPredictionSynthesisSchema


class ConfluenceDomainScanRequest(BaseModel):
    chart_id: Optional[str] = None
    chart_data: Optional[dict[str, Any]] = None
    target_datetime: Optional[datetime] = None
    horizon_months: int = Field(default=12, ge=1, le=60)


class DomainScanItem(BaseModel):
    category: PredictionCategory
    event_description: str
    confluence_verdict: SynthesizedVerdict
    confluence_ratio: float
    supporting_count: int
    veto_count: int
    active_vetoes: list[str]
    peak_timing: datetime


class ConfluenceDomainScanResponse(BaseModel):
    chart_id: str
    subject_name: str
    scanned_domains: list[DomainScanItem]
    scan_timestamp: datetime


class FreezeToP7Request(BaseModel):
    synthesis_id: str
    synthesis_payload: Optional[UnifiedPredictionSynthesisSchema] = None
    target_split_type: TemporalSplitType = TemporalSplitType.VALIDATION


class FreezeToP7Response(BaseModel):
    prediction_id: str
    chart_id: str
    subject_name: str
    technique: str
    category: PredictionCategory
    evidence_hash: str
    frozen_timestamp: datetime
    status: str
    message: str
