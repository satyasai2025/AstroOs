"""
AstroOS — Export Engine (Module 21, Phase 1)

Renders structured Reports (Module 20) into downloadable formats:
JSON, Markdown, and HTML. Pure formatting layer — no calculations.

Each renderer is a stateless class reading only ReportSection/ReportContent.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Union

from apps.api.domain.export_domain import ExportFormat, ExportResult
from apps.api.domain.report import (
    ChartReport,
    ComparisonReport,
    ReportContent,
    ResearchReport,
)

_Report = Union[ChartReport, ResearchReport, ComparisonReport]


def _filename(report: _Report, ext: str) -> str:
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rtype = report.metadata.report_type
    return f"{rtype}_report_{date_str}.{ext}"


def _size(content: str) -> int:
    return len(content.encode("utf-8"))


# ── JSON Renderer ────────────────────────────────────────────────────────────


class JsonRenderer:
    """Serializes report sections into a structured JSON document."""

    @staticmethod
    def render(report: _Report) -> ExportResult:
        doc = {
            "report": {
                "type": report.metadata.report_type,
                "title": getattr(report, "title", ""),
                "generated_at": report.metadata.generated_at.isoformat(),
                "engine_versions": report.metadata.engine_versions,
            },
            "sections": [
                {
                    "title": s.title,
                    "type": s.section_type,
                    "data": s.content.data,
                }
                for s in report.sections
            ],
        }
        content = json.dumps(doc, indent=2, default=str)
        return ExportResult(
            format=ExportFormat.JSON,
            content=content,
            filename=_filename(report, "json"),
            mime_type="application/json",
            size_bytes=_size(content),
        )


# ── Markdown Renderer ────────────────────────────────────────────────────────


class MarkdownRenderer:
    """Renders report sections as formatted markdown."""

    @staticmethod
    def render(report: _Report) -> ExportResult:
        lines: list[str] = []
        title = getattr(report, "title", "Report")
        lines.append(f"# {title}")
        lines.append("")
        date_str = report.metadata.generated_at.strftime("%Y-%m-%d %H:%M UTC")
        lines.append(f"*Generated: {date_str}*")
        lines.append("")
        lines.append("---")
        lines.append("")

        for section in report.sections:
            lines.append(f"## {section.title}")
            lines.append("")
            lines.extend(_render_section_markdown(section.content))
            lines.append("")
            lines.append("---")
            lines.append("")

        content = "\n".join(lines)
        return ExportResult(
            format=ExportFormat.MARKDOWN,
            content=content,
            filename=_filename(report, "md"),
            mime_type="text/markdown",
            size_bytes=_size(content),
        )


def _render_section_markdown(content: ReportContent) -> list[str]:
    """Route section content to the appropriate markdown template."""
    t = content.section_type
    d = content.data

    if t == "chart_summary":
        return [
            f"- **Ayanamsa:** {d.get('ayanamsa', '')}",
            f"- **House System:** {d.get('house_system', '')}",
            f"- **Lagna Rashi:** {d.get('lagna_rashi', '')}",
            f"- **Lagna Degree:** {d.get('lagna_degree', '')}",
            f"- **Moon Nakshatra:** {d.get('moon_nakshatra', '')}",
        ]

    if t == "planets":
        planets = d.get("planets", [])
        if not planets:
            return ["*No planet data.*"]
        rows = ["| Planet | Rashi | House | Dignity | Retrograde |"]
        rows.append("|--------|-------|-------|---------|------------|")
        for p in planets:
            rows.append(
                f"| {p.get('name', '')} | {p.get('rashi', '')} "
                f"| {p.get('house', '')} | {p.get('dignity', '') or ''} "
                f"| {p.get('retrograde', False)} |"
            )
        return rows

    if t == "timeline_summary":
        cats = d.get("events_per_category", {})
        lines = [
            f"- **Total Events:** {d.get('total_events', 0)}",
            f"- **Date Range:** {d.get('date_range', [])}",
        ]
        if cats:
            lines.append("- **Categories:**")
            for cat, count in cats.items():
                lines.append(f"  - {cat}: {count}")
        return lines

    if t == "verification_summary":
        strengths = d.get("strengths", {})
        lines = [
            f"- **Total Pairs:** {d.get('total_pairs', 0)}",
            f"- **Total Rules:** {d.get('total_rules', 0)}",
        ]
        if strengths:
            lines.append("- **Strengths:**")
            for k, v in strengths.items():
                lines.append(f"  - {k}: {v}")
        return lines

    if t == "statistics_summary":
        dists = d.get("distributions", [])
        lines = [f"- **Sample Size:** {d.get('sample_size', 0)}"]
        if dists:
            lines.append("- **Distributions:**")
            for dist in dists:
                lines.append(f"  - {dist.get('label', '')}: {dist.get('total', 0)} total")
        return lines

    if t == "snapshot_overview":
        labels = d.get("labels", [])
        lines = [f"- **Snapshot Count:** {d.get('snapshot_count', 0)}"]
        if labels:
            lines.append("- **Labels:**")
            for lbl in labels:
                lines.append(f"  - {lbl}")
        return lines

    if t == "planet_comparison":
        planets = d.get("planets", [])
        if not planets:
            return ["*No comparison data.*"]
        rows = ["| Chart | Planet | Rashi | House | Dignity |"]
        rows.append("|-------|--------|-------|-------|---------|")
        for p in planets:
            rows.append(
                f"| {p.get('chart_label', '')} | {p.get('planet', '')} "
                f"| {p.get('rashi', '')} | {p.get('house', '')} "
                f"| {p.get('dignity', '') or ''} |"
            )
        return rows

    # Fallback for unknown section types.
    return [f"*{t} data not rendered in markdown.*"]


# ── HTML Renderer ────────────────────────────────────────────────────────────


class HtmlRenderer:
    """Renders report sections as semantic HTML5 with inline CSS."""

    _CSS = """
    <style>
      body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
             max-width: 960px; margin: auto; padding: 2em; color: #333; }
      h1 { color: #1a1a1a; border-bottom: 2px solid #eee; padding-bottom: 0.3em; }
      h2 { color: #333; margin-top: 1.5em; }
      .meta { color: #666; font-size: 0.9em; }
      table { border-collapse: collapse; width: 100%; margin: 1em 0; }
      th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
      th { background: #f5f5f5; font-weight: 600; }
      .section { margin: 2em 0; }
      ul { padding-left: 1.5em; }
      hr { border: none; border-top: 1px solid #eee; margin: 2em 0; }
    </style>"""

    @staticmethod
    def render(report: _Report) -> ExportResult:
        title = getattr(report, "title", "Report")
        date_str = report.metadata.generated_at.strftime("%Y-%m-%d %H:%M UTC")

        parts = [
            "<!DOCTYPE html>",
            "<html><head>",
            f"<title>{title}</title>",
            HtmlRenderer._CSS,
            "</head><body>",
            f"<h1>{title}</h1>",
            f'<p class="meta">Generated: {date_str}</p>',
            "<hr>",
        ]

        for section in report.sections:
            parts.append(f'<div class="section">')
            parts.append(f"<h2>{section.title}</h2>")
            parts.extend(_render_section_html(section.content))
            parts.append("</div>")
            parts.append("<hr>")

        parts.append("</body></html>")
        content = "\n".join(parts)

        return ExportResult(
            format=ExportFormat.HTML,
            content=content,
            filename=_filename(report, "html"),
            mime_type="text/html",
            size_bytes=_size(content),
        )


def _render_section_html(content: ReportContent) -> list[str]:
    """Route section content to the appropriate HTML template."""
    t = content.section_type
    d = content.data

    if t == "chart_summary":
        items = [
            ("Ayanamsa", d.get("ayanamsa")),
            ("House System", d.get("house_system")),
            ("Lagna Rashi", d.get("lagna_rashi")),
            ("Lagna Degree", d.get("lagna_degree")),
            ("Moon Nakshatra", d.get("moon_nakshatra")),
        ]
        return ["<table>"] + [
            f"<tr><td>{label}</td><td>{val or ''}</td></tr>"
            for label, val in items
        ] + ["</table>"]

    if t == "planets":
        planets = d.get("planets", [])
        if not planets:
            return ["<p><em>No planet data.</em></p>"]
        rows = [
            "<table>",
            "<tr><th>Planet</th><th>Rashi</th><th>House</th><th>Dignity</th><th>Retrograde</th></tr>",
        ]
        for p in planets:
            rows.append(
                f"<tr><td>{p.get('name', '')}</td><td>{p.get('rashi', '')}</td>"
                f"<td>{p.get('house', '')}</td><td>{p.get('dignity', '') or ''}</td>"
                f"<td>{p.get('retrograde', False)}</td></tr>"
            )
        rows.append("</table>")
        return rows

    if t == "timeline_summary":
        lines = [
            "<ul>",
            f"<li><strong>Total Events:</strong> {d.get('total_events', 0)}</li>",
            f"<li><strong>Date Range:</strong> {d.get('date_range', [])}</li>",
        ]
        cats = d.get("events_per_category", {})
        if cats:
            lines.append("<li><strong>Categories:</strong><ul>")
            for cat, count in cats.items():
                lines.append(f"<li>{cat}: {count}</li>")
            lines.append("</ul></li>")
        lines.append("</ul>")
        return lines

    if t == "verification_summary":
        lines = [
            "<ul>",
            f"<li><strong>Total Pairs:</strong> {d.get('total_pairs', 0)}</li>",
            f"<li><strong>Total Rules:</strong> {d.get('total_rules', 0)}</li>",
        ]
        strengths = d.get("strengths", {})
        if strengths:
            lines.append("<li><strong>Strengths:</strong><ul>")
            for k, v in strengths.items():
                lines.append(f"<li>{k}: {v}</li>")
            lines.append("</ul></li>")
        lines.append("</ul>")
        return lines

    if t == "statistics_summary":
        dists = d.get("distributions", [])
        lines = [
            "<ul>",
            f"<li><strong>Sample Size:</strong> {d.get('sample_size', 0)}</li>",
        ]
        if dists:
            lines.append("<li><strong>Distributions:</strong><ul>")
            for dist in dists:
                lines.append(f"<li>{dist.get('label', '')}: {dist.get('total', 0)} total</li>")
            lines.append("</ul></li>")
        lines.append("</ul>")
        return lines

    if t == "snapshot_overview":
        labels = d.get("labels", [])
        lines = [
            "<ul>",
            f"<li><strong>Snapshot Count:</strong> {d.get('snapshot_count', 0)}</li>",
        ]
        if labels:
            lines.append("<li><strong>Labels:</strong><ul>")
            for lbl in labels:
                lines.append(f"<li>{lbl}</li>")
            lines.append("</ul></li>")
        lines.append("</ul>")
        return lines

    if t == "planet_comparison":
        planets = d.get("planets", [])
        if not planets:
            return ["<p><em>No comparison data.</em></p>"]
        rows = [
            "<table>",
            "<tr><th>Chart</th><th>Planet</th><th>Rashi</th><th>House</th><th>Dignity</th></tr>",
        ]
        for p in planets:
            rows.append(
                f"<tr><td>{p.get('chart_label', '')}</td><td>{p.get('planet', '')}</td>"
                f"<td>{p.get('rashi', '')}</td><td>{p.get('house', '')}</td>"
                f"<td>{p.get('dignity', '') or ''}</td></tr>"
            )
        rows.append("</table>")
        return rows

    return [f"<p><em>{t} data not rendered.</em></p>"]


# ── Export Engine ─────────────────────────────────────────────────────────────


class ExportEngine:
    """Dispatches reports to the appropriate format renderer."""

    @staticmethod
    def export(
        report: _Report,
        format: ExportFormat,
    ) -> ExportResult:
        if format == ExportFormat.JSON:
            return JsonRenderer.render(report)
        elif format == ExportFormat.MARKDOWN:
            return MarkdownRenderer.render(report)
        elif format == ExportFormat.HTML:
            return HtmlRenderer.render(report)
        elif format == ExportFormat.CSV:
            raise NotImplementedError("Use CsvResearchExporter for CSV export with citations.")
        else:
            raise ValueError(f"Unsupported format: {format.value}")

    @staticmethod
    def export_json(report: _Report) -> ExportResult:
        return ExportEngine.export(report, ExportFormat.JSON)

    @staticmethod
    def export_markdown(report: _Report) -> ExportResult:
        return ExportEngine.export(report, ExportFormat.MARKDOWN)

    @staticmethod
    def export_html(report: _Report) -> ExportResult:
        return ExportEngine.export(report, ExportFormat.HTML)
