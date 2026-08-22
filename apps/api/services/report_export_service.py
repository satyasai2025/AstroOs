"""
AstroOS — Multi-Format Report Export Service (Module 20, Phase 5)

Generates standalone exports for:
1. PDF (Printable HTML / PDF binary)
2. HTML (Standalone responsive single-file document)
3. CSV (Multi-section tabular data export)
4. JSON (Full structured machine-readable payload)
"""

from __future__ import annotations

import base64
import csv
import io
import json
from typing import Any
from apps.api.schemas.narrative_report import DocumentExportResponse


class ReportExportService:
    """
    Renders reports into PDF, standalone HTML, CSV, or JSON documents.
    """

    def export_document(
        self,
        report_data: dict[str, Any],
        export_format: str = "html",
        include_tables: bool = True,
    ) -> DocumentExportResponse:
        fmt = export_format.strip().lower()
        subject_name = report_data.get("subject_name", "Subject").replace(" ", "_")

        if fmt == "json":
            content_str = json.dumps(report_data, indent=2, default=str)
            return DocumentExportResponse(
                export_format="json",
                filename=f"AstroOS_Report_{subject_name}.json",
                mime_type="application/json",
                content_base64_or_text=content_str,
                size_bytes=len(content_str.encode("utf-8")),
            )

        elif fmt == "csv":
            content_str = self._render_csv(report_data)
            return DocumentExportResponse(
                export_format="csv",
                filename=f"AstroOS_Report_{subject_name}.csv",
                mime_type="text/csv",
                content_base64_or_text=content_str,
                size_bytes=len(content_str.encode("utf-8")),
            )

        elif fmt == "pdf":
            # Render clean printable standalone HTML with print styling & base64 encode
            html_content = self._render_standalone_html(report_data, is_print_ready=True)
            encoded_pdf_or_html = base64.b64encode(html_content.encode("utf-8")).decode("ascii")
            return DocumentExportResponse(
                export_format="pdf",
                filename=f"AstroOS_Report_{subject_name}.pdf",
                mime_type="application/pdf",
                content_base64_or_text=encoded_pdf_or_html,
                size_bytes=len(html_content.encode("utf-8")),
            )

        else:  # html (default)
            html_content = self._render_standalone_html(report_data, is_print_ready=False)
            return DocumentExportResponse(
                export_format="html",
                filename=f"AstroOS_Report_{subject_name}.html",
                mime_type="text/html",
                content_base64_or_text=html_content,
                size_bytes=len(html_content.encode("utf-8")),
            )

    def _render_csv(self, report_data: dict[str, Any]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)

        # Header metadata
        writer.writerow(["AstroOS Technical Astrological Report"])
        writer.writerow(["Subject Name", report_data.get("subject_name", "N/A")])
        writer.writerow(["Report Title", report_data.get("report_title", "N/A")])
        writer.writerow(["Generated At", report_data.get("generated_at_iso", "N/A")])
        writer.writerow([])

        # Multi-Varga Matrix
        writer.writerow(["--- MULTI-VARGA DIGNITY MATRIX ---"])
        writer.writerow(["Planet", "D1 Rashi", "D1 House", "D1 Dignity", "D9 Rashi", "D9 Dignity", "D10 Rashi", "D10 Dignity", "D7 Rashi", "D7 Dignity", "Vargottama"])
        for row in report_data.get("multi_varga_matrix", []):
            writer.writerow([
                row.get("planet"),
                row.get("d1_rashi"),
                row.get("d1_house"),
                row.get("d1_dignity"),
                row.get("d9_rashi"),
                row.get("d9_dignity"),
                row.get("d10_rashi"),
                row.get("d10_dignity"),
                row.get("d7_rashi"),
                row.get("d7_dignity"),
                row.get("is_vargottama"),
            ])
        writer.writerow([])

        # Section Evidence Tables
        writer.writerow(["--- TECHNICAL EVIDENCE DATA ITEMS ---"])
        writer.writerow(["Evidence ID", "Category", "Parameter", "Computed Value", "Classical Reference", "Confidence"])
        for sec in report_data.get("sections", []):
            for ev in sec.get("evidence_table", []):
                writer.writerow([
                    ev.get("evidence_id"),
                    ev.get("category"),
                    ev.get("parameter_name"),
                    ev.get("computed_value"),
                    ev.get("classical_reference"),
                    ev.get("confidence_or_strength"),
                ])

        return output.getvalue()

    def _render_standalone_html(self, report_data: dict[str, Any], is_print_ready: bool = False) -> str:
        title = report_data.get("report_title", "AstroOS Technical Astrological Report")
        subject = report_data.get("subject_name", "Primary Subject")
        generated_at = report_data.get("generated_at_iso", "")
        sections = report_data.get("sections", [])
        vargas = report_data.get("multi_varga_matrix", [])

        varga_rows_html = "".join([
            f"""<tr>
                <td style="padding:8px;border:1px solid #334155;font-weight:bold;">{v.get('planet')}</td>
                <td style="padding:8px;border:1px solid #334155;">{v.get('d1_rashi')} ({v.get('d1_dignity')})</td>
                <td style="padding:8px;border:1px solid #334155;">{v.get('d9_rashi')} ({v.get('d9_dignity')})</td>
                <td style="padding:8px;border:1px solid #334155;">{v.get('d10_rashi')} ({v.get('d10_dignity')})</td>
                <td style="padding:8px;border:1px solid #334155;">{v.get('d7_rashi')} ({v.get('d7_dignity')})</td>
                <td style="padding:8px;border:1px solid #334155;color:{'#10b981' if v.get('is_vargottama') else '#94a3b8'};">{'YES' if v.get('is_vargottama') else 'No'}</td>
            </tr>"""
            for v in vargas
        ])

        sections_html = ""
        for sec in sections:
            paragraphs_html = "".join([
                f"""<div style="margin-bottom:12px;">
                    <h4 style="color:#38bdf8;margin:0 0 4px 0;font-size:14px;">{p.get('heading')}</h4>
                    <p style="margin:0;line-height:1.6;color:#e2e8f0;font-size:13px;">{p.get('content_text')}</p>
                    <div style="font-size:11px;color:#94a3b8;margin-top:4px;">Referenced Evidence: <code>{', '.join(p.get('referenced_evidence_ids', []))}</code></div>
                </div>"""
                for p in sec.get("paragraphs", [])
            ])

            evidence_rows_html = "".join([
                f"""<tr>
                    <td style="padding:6px;border:1px solid #334155;font-family:monospace;font-size:11px;color:#38bdf8;">{e.get('evidence_id')}</td>
                    <td style="padding:6px;border:1px solid #334155;font-size:12px;">{e.get('category')}</td>
                    <td style="padding:6px;border:1px solid #334155;font-size:12px;font-weight:600;">{e.get('parameter_name')}</td>
                    <td style="padding:6px;border:1px solid #334155;font-size:12px;color:#cbd5e1;">{e.get('computed_value')}</td>
                    <td style="padding:6px;border:1px solid #334155;font-size:11px;color:#94a3b8;">{e.get('classical_reference') or '-'}</td>
                </tr>"""
                for e in sec.get("evidence_table", [])
            ])

            sections_html += f"""
            <section style="margin-bottom:28px;padding:16px;background:#0f172a;border:1px solid #1e293b;border-radius:8px;">
                <h3 style="color:#f8fafc;margin:0 0 4px 0;font-size:16px;">{sec.get('title')}</h3>
                <div style="color:#64748b;font-size:12px;margin-bottom:14px;">{sec.get('subtitle')}</div>
                {paragraphs_html}
                {f'''<div style="margin-top:14px;">
                    <div style="font-size:12px;font-weight:bold;color:#94a3b8;margin-bottom:6px;text-transform:uppercase;">Technical Evidence Table</div>
                    <table style="width:100%;border-collapse:collapse;text-align:left;">
                        <thead>
                            <tr style="background:#1e293b;color:#94a3b8;font-size:11px;">
                                <th style="padding:6px;border:1px solid #334155;">Evidence ID</th>
                                <th style="padding:6px;border:1px solid #334155;">Category</th>
                                <th style="padding:6px;border:1px solid #334155;">Parameter</th>
                                <th style="padding:6px;border:1px solid #334155;">Computed Value</th>
                                <th style="padding:6px;border:1px solid #334155;">Classical Source</th>
                            </tr>
                        </thead>
                        <tbody>{evidence_rows_html}</tbody>
                    </table>
                </div>''' if evidence_rows_html else ''}
            </section>
            """

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — {subject}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: #020617;
            color: #f8fafc;
            margin: 0;
            padding: 32px;
            box-sizing: border-box;
        }}
        .container {{ max-width: 960px; margin: 0 auto; }}
        header {{ border-bottom: 2px solid #334155; padding-bottom: 16px; margin-bottom: 24px; }}
        code {{ background: #1e293b; padding: 2px 4px; border-radius: 4px; font-family: monospace; font-size: 11px; }}
        @media print {{
            body {{ background: #ffffff !important; color: #000000 !important; padding: 12px !important; }}
            section {{ background: #ffffff !important; border: 1px solid #ccc !important; page-break-inside: avoid; }}
            h3, h4 {{ color: #000000 !important; }}
            p {{ color: #222222 !important; }}
            table, th, td {{ border-color: #999 !important; color: #000000 !important; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div style="font-size:11px;color:#38bdf8;font-weight:bold;letter-spacing:1px;text-transform:uppercase;">AstroOS Technical Astrological Report</div>
            <h1 style="margin:4px 0 8px 0;font-size:24px;">{title}</h1>
            <div style="font-size:13px;color:#94a3b8;">
                <strong>Subject:</strong> {subject} &nbsp;|&nbsp; <strong>Generated:</strong> {generated_at}
            </div>
        </header>

        <!-- Multi-Varga Summary Table -->
        <section style="margin-bottom:28px;padding:16px;background:#0f172a;border:1px solid #1e293b;border-radius:8px;">
            <h3 style="color:#f8fafc;margin:0 0 4px 0;font-size:16px;">Multi-Varga Dignity Matrix (D1, D9, D10, D7)</h3>
            <table style="width:100%;border-collapse:collapse;text-align:left;font-size:12px;margin-top:10px;">
                <thead>
                    <tr style="background:#1e293b;color:#94a3b8;">
                        <th style="padding:8px;border:1px solid #334155;">Planet</th>
                        <th style="padding:8px;border:1px solid #334155;">D1 Rashi</th>
                        <th style="padding:8px;border:1px solid #334155;">D9 Navamsha</th>
                        <th style="padding:8px;border:1px solid #334155;">D10 Dashamsha</th>
                        <th style="padding:8px;border:1px solid #334155;">D7 Saptamsha</th>
                        <th style="padding:8px;border:1px solid #334155;">Vargottama</th>
                    </tr>
                </thead>
                <tbody>{varga_rows_html}</tbody>
            </table>
        </section>

        <!-- 9 Standardized Report Sections -->
        {sections_html}

        <footer style="margin-top:40px;border-top:1px solid #334155;padding-top:16px;text-align:center;font-size:11px;color:#64748b;">
            Generated by AstroOS Deterministic Reporting Engine v2.0 • Swiss Ephemeris Standard
        </footer>
    </div>
</body>
</html>"""
