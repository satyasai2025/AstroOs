"""
AstroOS — Export Domain Objects (Module 21, Phase 1)

ExportFormat enum and ExportResult for rendered report output.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ExportFormat(str, Enum):
    """Target format for report export."""

    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"      # Phase 2
    DOCX = "docx"    # Phase 2


@dataclass(frozen=True)
class ExportResult:
    """Output of an export operation."""

    format: ExportFormat
    content: str
    filename: str
    mime_type: str
    size_bytes: int
