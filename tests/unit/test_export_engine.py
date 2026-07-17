"""
AstroOS — ExportEngine Unit Tests (Module 21, Phase 1)
"""

import uuid
from datetime import datetime

import pytest

from apps.api.domain.export_domain import ExportFormat
from apps.api.domain.report import (
    ChartReport,
    ReportContent,
    ReportMetadata,
    ReportSection,
    ResearchReport,
)
from apps.api.services.export_engine import (
    ExportEngine,
    HtmlRenderer,
    JsonRenderer,
    MarkdownRenderer,
)


def _metadata(report_type: str = "chart") -> ReportMetadata:
    return ReportMetadata(
        report_id=uuid.uuid4(),
        report_type=report_type,
        report_version="1.0",
        generated_at=datetime(2026, 7, 14, 12, 0, 0),
    )


def _chart_report() -> ChartReport:
    meta = _metadata("chart")
    sections = (
        ReportSection(
            title="Chart Summary", section_type="chart_summary",
            content=ReportContent(section_type="chart_summary", data={
                "ayanamsa": "lahiri", "house_system": "W",
                "lagna_rashi": "aries", "lagna_degree": 10.5,
                "moon_nakshatra": "rohini",
            }), order=0,
        ),
        ReportSection(
            title="Planetary Positions", section_type="planets",
            content=ReportContent(section_type="planets", data={
                "planets": [
                    {"name": "sun", "rashi": "aries", "house": 1,
                     "dignity": "own", "retrograde": False},
                    {"name": "moon", "rashi": "taurus", "house": 2,
                     "dignity": "friendly", "retrograde": False},
                ],
                "count": 2,
            }), order=1,
        ),
    )
    return ChartReport(
        metadata=meta, title="Chart Analysis",
        subject_name="Test", sections=sections,
    )


class TestJsonRenderer:
    def test_returns_json_content(self):
        report = _chart_report()
        result = JsonRenderer.render(report)
        assert result.format == ExportFormat.JSON
        assert result.mime_type == "application/json"
        assert result.content.startswith("{")
        assert '"type": "chart_summary"' in result.content
        assert '"lagna_rashi": "aries"' in result.content
        assert result.filename.endswith(".json")

    def test_filename_format(self):
        report = _chart_report()
        result = JsonRenderer.render(report)
        assert "chart_report_" in result.filename


class TestMarkdownRenderer:
    def test_renders_headings(self):
        report = _chart_report()
        result = MarkdownRenderer.render(report)
        assert result.format == ExportFormat.MARKDOWN
        assert result.content.startswith("# Chart Analysis")
        assert "## Chart Summary" in result.content
        assert "## Planetary Positions" in result.content

    def test_renders_tables(self):
        report = _chart_report()
        result = MarkdownRenderer.render(report)
        assert "| Planet | Rashi | House |" in result.content
        assert "| sun | aries | 1 |" in result.content

    def test_filename(self):
        report = _chart_report()
        result = MarkdownRenderer.render(report)
        assert result.filename.endswith(".md")


class TestHtmlRenderer:
    def test_renders_doctype(self):
        report = _chart_report()
        result = HtmlRenderer.render(report)
        assert result.content.startswith("<!DOCTYPE html>")
        assert "<h1>Chart Analysis</h1>" in result.content
        assert "<table>" in result.content

    def test_includes_css(self):
        report = _chart_report()
        result = HtmlRenderer.render(report)
        assert "<style>" in result.content
        assert "font-family" in result.content

    def test_filename(self):
        report = _chart_report()
        result = HtmlRenderer.render(report)
        assert result.filename.endswith(".html")


class TestExportEngine:
    def test_export_json(self):
        report = _chart_report()
        result = ExportEngine.export(report, ExportFormat.JSON)
        assert result.format == ExportFormat.JSON

    def test_export_markdown(self):
        report = _chart_report()
        result = ExportEngine.export(report, ExportFormat.MARKDOWN)
        assert result.format == ExportFormat.MARKDOWN

    def test_export_html(self):
        report = _chart_report()
        result = ExportEngine.export(report, ExportFormat.HTML)
        assert result.format == ExportFormat.HTML

    def test_convenience_methods(self):
        report = _chart_report()
        assert ExportEngine.export_json(report).format == ExportFormat.JSON
        assert ExportEngine.export_markdown(report).format == ExportFormat.MARKDOWN
        assert ExportEngine.export_html(report).format == ExportFormat.HTML

    def test_unsupported_format_raises(self):
        report = _chart_report()
        with pytest.raises(ValueError, match="Unsupported format"):
            ExportEngine.export(report, ExportFormat.PDF)

    def test_research_report(self):
        meta = _metadata("research")
        report = ResearchReport(
            metadata=meta, title="Research", snapshot_count=3,
            sections=(
                ReportSection(
                    title="Overview", section_type="snapshot_overview",
                    content=ReportContent(section_type="snapshot_overview", data={
                        "snapshot_count": 3, "labels": ["A", "B"],
                    }), order=0,
                ),
            ),
        )
        result = ExportEngine.export_json(report)
        assert result.format == ExportFormat.JSON
        assert "Research" in result.content
