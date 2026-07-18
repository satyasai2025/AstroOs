"""AstroOS — Report Template Engine (Phase F.1)"""

from __future__ import annotations

import csv
import io
import json
import os
from typing import Any, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "templates", "reports"
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
        try:
            template = _env.get_template(template_name)
            return template.render(report=report)
        except Exception:
            return _env.get_template("base.html").render(report=report)

    @staticmethod
    def render_pdf(report: dict, template_name: str = "horoscope.html") -> bytes:
        try:
            import weasyprint
        except ImportError:
            raise RuntimeError("weasyprint required: pip install weasyprint")
        html = ReportTemplateEngine.render_html(report, template_name)
        return weasyprint.HTML(string=html).write_pdf()

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
            return [f for f in os.listdir(_TEMPLATES_DIR) if f.endswith(".html")]
        except FileNotFoundError:
            return []