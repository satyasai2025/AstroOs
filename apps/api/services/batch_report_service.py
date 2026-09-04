"""
AstroOS Batch Report Service (Phase II.4 — Local-First)

Runs as the ``fn`` of a WorkerPool job: computes a D1 chart + report for
each subject in a batch, renders PDF or CSV per subject, and zips the
results to disk under ``Settings.BATCH_OUTPUT_DIR``. Pure orchestration —
reuses HoroscopeEngine / ReportEngine / ReportTemplateEngine unchanged, no
duplicated business logic (per project rules).
"""

from __future__ import annotations

import logging
import re
import zipfile
from pathlib import Path
from typing import Any

from apps.api.domain.report import ChartReport
from apps.api.schemas.batch import BatchChartReportRequest
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.report_engine import ReportEngine
from apps.api.services.worker_pool import Job, JobCancelled

logger = logging.getLogger(__name__)

_SLUG_RE = re.compile(r"[^A-Za-z0-9_-]+")


def _slug(text: str, fallback: str) -> str:
    cleaned = _SLUG_RE.sub("-", text.strip()).strip("-")
    return cleaned or fallback


def _report_to_template_dict(report: ChartReport) -> dict:
    """
    Flatten a domain ``ChartReport`` (a plain dataclass — see
    ``apps/api/domain/report.py``) into the dict shape
    ``ReportTemplateEngine.render_pdf``/``render_csv`` expect.

    Mirrors the flattening ``apps/api/routers/report.py``'s
    ``_sections_response()`` performs for the JSON endpoint (each section's
    ``content.data`` promoted to a top-level ``data`` key) — deliberately
    *not* a raw ``dataclasses.asdict()``/``.model_dump()``, both of which
    would nest ``data`` under ``content`` and leave ``render_csv`` unable to
    find it. See AMP-009 (architecture/decisions/) for why the router's own
    PDF/CSV endpoints currently get this wrong; this function is the
    correct version, kept local to Phase II.4's own code.
    """
    return {
        "title": report.title,
        "subject_name": report.subject_name,
        "metadata": {
            "report_id": str(report.metadata.report_id),
            "report_type": report.metadata.report_type,
            "report_version": report.metadata.report_version,
            "generated_at": report.metadata.generated_at.isoformat(),
        },
        "sections": [
            {
                "title": s.title,
                "section_type": s.section_type,
                "data": dict(s.content.data),
                "order": s.order,
            }
            for s in report.sections
        ],
    }


def run_batch_chart_reports(
    job: Job,
    request: BatchChartReportRequest,
    wrapper: EphemerisWrapper,
    output_dir: Path,
) -> dict[str, Any]:
    """
    Job body executed on the ``io`` worker pool. Returns a small summary
    dict (job.result); the zip itself is written to disk and referenced by
    path so large batches never sit fully in memory.
    """
    from apps.api.services.report_template_engine import ReportTemplateEngine

    horoscope_engine = HoroscopeEngine(wrapper)
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"{job.id}.zip"

    total = len(request.subjects)
    job.set_progress(0, total)
    succeeded = 0
    failed: list[dict[str, str]] = []

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for idx, subject in enumerate(request.subjects, start=1):
            if job.cancel_requested:
                raise JobCancelled()
            label = subject.label or f"subject-{idx}"
            try:
                chart = horoscope_engine.generate_d1(
                    birth_datetime_utc=subject.birth_datetime_utc,
                    latitude=subject.latitude,
                    longitude=subject.longitude,
                    ayanamsa=subject.ayanamsa,
                    house_system=subject.house_system,
                )
                report = ReportEngine.build_chart_report(
                    chart,
                    title=f"{request.title_prefix} — {label}",
                    subject_name=label,
                )
                report_dict = _report_to_template_dict(report)
                if request.format == "pdf":
                    content = ReportTemplateEngine.render_pdf(report_dict)
                else:
                    content = ReportTemplateEngine.render_csv(report_dict).encode("utf-8")
                filename = f"{idx:04d}_{_slug(label, f'subject{idx}')}.{request.format}"
                zf.writestr(filename, content)
                succeeded += 1
            except Exception as exc:  # noqa: BLE001 — per-subject failures don't abort the batch
                logger.warning(
                    "batch subject failed",
                    extra={"job_id": job.id, "subject_index": idx, "label": label, "error": str(exc)},
                )
                failed.append({"index": str(idx), "label": label, "error": str(exc)})
            job.set_progress(idx, total)

        manifest_lines = [f"AstroOS batch report — {succeeded}/{total} succeeded", ""]
        if failed:
            manifest_lines.append("Failed subjects:")
            manifest_lines += [f"  #{f['index']} {f['label']}: {f['error']}" for f in failed]
        zf.writestr("MANIFEST.txt", "\n".join(manifest_lines))

    return {
        "zip_path": str(zip_path),
        "total": total,
        "succeeded": succeeded,
        "failed_count": len(failed),
        "failed": failed,
    }
