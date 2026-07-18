"""
AstroOS — Export API Schemas (Module 21 — HTTP surface)

Request bodies mirror schemas/report.py's Chart/Research/Comparison
report requests exactly (same report is built first, then rendered) —
extended with `format` to select the target renderer.
"""

from __future__ import annotations

from typing import Literal

from apps.api.schemas.report import (
    ChartReportRequest,
    ComparisonReportRequest,
    ResearchReportRequest,
)

ExportFormatCode = Literal["json", "markdown", "html"]


class ChartExportRequest(ChartReportRequest):
    format: ExportFormatCode = "json"


class ResearchExportRequest(ResearchReportRequest):
    format: ExportFormatCode = "json"


class ComparisonExportRequest(ComparisonReportRequest):
    format: ExportFormatCode = "json"
