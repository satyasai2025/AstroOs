"""Unit tests for apps/api/services/batch_report_service.py (Phase II.4)."""

import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from apps.api.domain.report import ChartReport, ReportContent, ReportMetadata, ReportSection
from apps.api.schemas.batch import BatchChartReportRequest, BatchSubjectInput
from apps.api.services.batch_report_service import (
    _report_to_template_dict,
    _slug,
    run_batch_chart_reports,
)
from apps.api.services.worker_pool import Job, JobCancelled, JobPriority


def _fake_report(title="Test Chart", subject_name="Alice") -> ChartReport:
    metadata = ReportMetadata(
        report_id=uuid.uuid4(),
        report_type="chart",
        report_version="1.0",
        generated_at=datetime.now(timezone.utc),
    )
    section = ReportSection(
        title="Chart Summary",
        section_type="chart_summary",
        content=ReportContent(section_type="chart_summary", data={"ascendant": "Aries"}),
        order=0,
    )
    return ChartReport(metadata=metadata, title=title, subject_name=subject_name, sections=(section,))


# ── _slug ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "text,expected",
    [
        ("Alice Smith", "Alice-Smith"),
        ("  weird///chars!! ", "weird-chars"),
        ("", "fallback"),
        ("already-ok_123", "already-ok_123"),
    ],
)
def test_slug(text, expected):
    assert _slug(text, "fallback") == expected


# ── _report_to_template_dict (AMP-009 fix, local to Phase II.4) ─────────────

def test_report_to_template_dict_flattens_content_data():
    report = _fake_report()
    d = _report_to_template_dict(report)
    assert d["title"] == "Test Chart"
    assert d["subject_name"] == "Alice"
    assert d["sections"][0]["section_type"] == "chart_summary"
    # The critical flattening: `data` promoted out of `content`, matching
    # what ReportTemplateEngine.render_csv reads (section["data"]).
    assert d["sections"][0]["data"] == {"ascendant": "Aries"}
    assert "content" not in d["sections"][0]


def test_report_to_template_dict_has_no_domain_objects():
    """Every value must be JSON/CSV-friendly (str/dict/list), not dataclasses/UUIDs/datetimes."""
    d = _report_to_template_dict(_fake_report())
    assert isinstance(d["metadata"]["report_id"], str)
    assert isinstance(d["metadata"]["generated_at"], str)


# ── run_batch_chart_reports (integration-ish, fake horoscope engine) ────────

class _FakeHoroscopeEngine:
    def __init__(self, wrapper):
        pass

    def generate_d1(self, **kwargs):
        return object()  # ReportEngine.build_chart_report is monkeypatched below


@pytest.fixture()
def patched_engines(monkeypatch):
    monkeypatch.setattr(
        "apps.api.services.batch_report_service.HoroscopeEngine", _FakeHoroscopeEngine
    )
    monkeypatch.setattr(
        "apps.api.services.batch_report_service.ReportEngine.build_chart_report",
        staticmethod(lambda chart, **kwargs: _fake_report(
            title=kwargs.get("title", "x"), subject_name=kwargs.get("subject_name", "x")
        )),
    )


def _job() -> Job:
    return Job(id="job1", pool="io", priority=JobPriority.BULK, fn=lambda j: None)


def test_run_batch_produces_zip_with_one_file_per_subject(tmp_path, patched_engines):
    request = BatchChartReportRequest(
        subjects=[
            BatchSubjectInput(
                birth_datetime_utc="1990-01-01T12:00:00Z", latitude=10.0, longitude=20.0, label="A"
            ),
            BatchSubjectInput(
                birth_datetime_utc="1991-01-01T12:00:00Z", latitude=11.0, longitude=21.0, label="B"
            ),
        ],
        format="csv",
    )
    job = _job()
    result = run_batch_chart_reports(job, request, wrapper=object(), output_dir=tmp_path)

    assert result["succeeded"] == 2
    assert result["failed_count"] == 0
    assert job.progress_current == 2
    assert job.progress_total == 2

    zip_path = Path(result["zip_path"])
    assert zip_path.exists()
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        assert "MANIFEST.txt" in names
        assert any(n.endswith("_A.csv") for n in names)
        assert any(n.endswith("_B.csv") for n in names)


def test_run_batch_records_per_subject_failure_without_aborting(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "apps.api.services.batch_report_service.HoroscopeEngine", _FakeHoroscopeEngine
    )

    calls = {"n": 0}

    def flaky_build(chart, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ValueError("boom")
        return _fake_report(subject_name=kwargs.get("subject_name", "x"))

    monkeypatch.setattr(
        "apps.api.services.batch_report_service.ReportEngine.build_chart_report",
        staticmethod(flaky_build),
    )

    request = BatchChartReportRequest(
        subjects=[
            BatchSubjectInput(
                birth_datetime_utc="1990-01-01T12:00:00Z", latitude=10.0, longitude=20.0, label="Fails"
            ),
            BatchSubjectInput(
                birth_datetime_utc="1991-01-01T12:00:00Z", latitude=11.0, longitude=21.0, label="Succeeds"
            ),
        ],
        format="csv",
    )
    job = _job()
    result = run_batch_chart_reports(job, request, wrapper=object(), output_dir=tmp_path)

    assert result["succeeded"] == 1
    assert result["failed_count"] == 1
    assert result["failed"][0]["label"] == "Fails"
    assert "boom" in result["failed"][0]["error"]


def test_run_batch_raises_job_cancelled_when_cancel_requested(tmp_path, patched_engines):
    request = BatchChartReportRequest(
        subjects=[
            BatchSubjectInput(
                birth_datetime_utc="1990-01-01T12:00:00Z", latitude=10.0, longitude=20.0, label="A"
            ),
        ],
        format="csv",
    )
    job = _job()
    job.cancel_requested = True
    with pytest.raises(JobCancelled):
        run_batch_chart_reports(job, request, wrapper=object(), output_dir=tmp_path)
