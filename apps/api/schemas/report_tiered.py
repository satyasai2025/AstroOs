"""AstroOS — Tiered Report Schemas (Phase 10)"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

ReportTierLiteral = Literal["free_2page", "pro_5page", "research_dossier"]
ExportFormatLiteral = Literal["pdf", "html", "json"]


class GenerateTieredReportRequest(BaseModel):
    """Request to generate a tiered PDF/HTML report."""
    chart_id: Optional[uuid.UUID] = Field(default=None, description="ID of an existing birth chart")
    subject_name: Optional[str] = Field(default="Subject", max_length=100)
    birth_datetime_utc: Optional[datetime] = None
    birth_latitude: Optional[float] = None
    birth_longitude: Optional[float] = None
    report_tier: ReportTierLiteral = Field(default="free_2page", description="Report detail tier")
    export_format: ExportFormatLiteral = Field(default="pdf", description="Output document format")


class TieredReportItemResponse(BaseModel):
    """Metadata for a generated report."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    chart_id: Optional[uuid.UUID] = None
    subject_name: str
    report_tier: ReportTierLiteral
    export_format: ExportFormatLiteral
    page_count: int
    file_size_bytes: int
    download_url: str
    created_at: datetime


class TieredReportHistoryResponse(BaseModel):
    """List of generated reports."""
    items: list[TieredReportItemResponse]
    total: int
