"""
AstroOS — Export Domain Model Unit Tests (Module 21, Phase 1)
"""

import dataclasses

import pytest

from apps.api.domain.export_domain import ExportFormat, ExportResult


class TestExportFormat:
    def test_enum_values(self):
        assert ExportFormat.JSON.value == "json"
        assert ExportFormat.MARKDOWN.value == "markdown"
        assert ExportFormat.HTML.value == "html"
        assert ExportFormat.PDF.value == "pdf"
        assert ExportFormat.DOCX.value == "docx"

    def test_all_members(self):
        assert len(ExportFormat) == 6  # JSON, MARKDOWN, HTML, PDF, DOCX, CSV


class TestExportResult:
    def test_is_frozen(self):
        r = ExportResult(
            format=ExportFormat.JSON, content="{}",
            filename="test.json", mime_type="application/json",
            size_bytes=2,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            r.content = "[]"

    def test_stores_output(self):
        r = ExportResult(
            format=ExportFormat.HTML, content="<html/>",
            filename="r.html", mime_type="text/html", size_bytes=7,
        )
        assert r.format == ExportFormat.HTML
        assert r.content == "<html/>"
        assert r.size_bytes == 7
