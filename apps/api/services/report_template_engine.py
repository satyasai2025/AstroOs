"""AstroOS — Report Template Engine (Phase F.1)"""

from __future__ import annotations

import csv
import io
import json
import logging
import os
from typing import Any, Optional
from jinja2 import (
    Environment,
    FileSystemLoader,
    TemplateNotFound,
    select_autoescape,
)

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "templates", "reports"
)

_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)

_env.filters["rashi"] = lambda v: v.capitalize() if v else ""
_env.filters["planet"] = lambda v: v.capitalize() if v else ""


class ReportTemplateEngine:
    """Template rendering for reports."""

    @staticmethod
    def render_html(report: dict, template_name: str = "horoscope.html") -> str:
        """
        Render `report` through `template_name`.

        Falls back to base.html ONLY when the requested template does not
        exist. Any other failure — a syntax error in the template, a bad
        variable reference — is raised.

        This previously caught bare `Exception` and silently returned
        base.html, so a broken template produced a plausible-looking but
        WRONG document with no error anywhere: the caller asked for the
        foundation sheet and got the generic fallback instead, and nothing
        in the logs said so.
        """
        try:
            template = _env.get_template(template_name)
        except TemplateNotFound:
            logger.warning(
                "Report template %r not found; falling back to base.html",
                template_name,
            )
            return _env.get_template("base.html").render(report=report)
        return template.render(report=report)

    @staticmethod
    def render_pdf(
        report: dict,
        template_name: str = "horoscope.html",
        *,
        expected_pages: int | None = None,
    ) -> bytes:
        """
        Render `report` to PDF.

        Delegates to `services.pdf_renderer`, which prefers headless Chromium
        — the renderer the fixed-A4 templates were composed and tested
        against. This previously called WeasyPrint directly, which cannot even
        import on Windows without GTK, so every PDF export raised.

        `expected_pages` is the registry page_target. When given, the rendered
        page count is verified and a mismatch raises rather than returning a
        mis-paginated report.
        """
        from apps.api.services.pdf_renderer import render_pdf as _render

        html = ReportTemplateEngine.render_html(report, template_name)
        return _render(html, expected_pages=expected_pages)

    @staticmethod
    def render_json(report: dict) -> str:
        return json.dumps(report, indent=2, default=str)

    @staticmethod
    def render_csv(report: dict, sections: Optional[list[str]] = None) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        for s in report.get("sections", []):
            if sections and s["section_type"] not in sections:
                continue
            data = s.get("data", {})
            if all(isinstance(v, list) for v in data.values() if v):
                keys = list(data.keys())
                writer.writerow(keys)
                for row in zip(*[data[k] for k in keys]):
                    writer.writerow(row)
        return output.getvalue()

    @staticmethod
    def list_templates() -> list[str]:
        try:
            return [
                f
                for f in os.listdir(_TEMPLATES_DIR)
                if f.endswith(".html") and not f.startswith("_")
            ]
        except FileNotFoundError:
            return []