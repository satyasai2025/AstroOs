"""
AstroOS — Report Domain Model Unit Tests (Module 20, Phase 1)
"""

import dataclasses
import uuid
from datetime import datetime

import pytest

from apps.api.domain.report import (
    ChartReport,
    ComparisonReport,
    ReportContent,
    ReportMetadata,
    ReportSection,
    ResearchReport,
)


class TestReportContent:
    def test_fields_accessible(self):
        rc = ReportContent(section_type="test", data={"key": "val"})
        assert rc.section_type == "test"
        assert rc.data["key"] == "val"

    def test_default_data(self):
        rc = ReportContent(section_type="test")
        assert rc.data == {}


class TestReportSection:
    def test_is_frozen(self):
        rc = ReportContent(section_type="t")
        s = ReportSection(title="T", section_type="t", content=rc)
        with pytest.raises(dataclasses.FrozenInstanceError):
            s.title = "Changed"

    def test_default_order(self):
        rc = ReportContent(section_type="t")
        s = ReportSection(title="T", section_type="t", content=rc)
        assert s.order == 0


class TestReportMetadata:
    def test_is_frozen(self):
        m = ReportMetadata(
            report_id=uuid.uuid4(), report_type="chart",
            report_version="1.0", generated_at=datetime.now(),
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            m.report_type = "research"

    def test_defaults(self):
        m = ReportMetadata(
            report_id=uuid.uuid4(), report_type="chart",
            report_version="1.0", generated_at=datetime.now(),
        )
        assert m.engine_versions == {}
        assert m.chart_id is None
        assert m.generated_by is None


class TestChartReport:
    def test_is_frozen(self):
        m = ReportMetadata(
            report_id=uuid.uuid4(), report_type="chart",
            report_version="1.0", generated_at=datetime.now(),
        )
        r = ChartReport(metadata=m, title="T", subject_name="S")
        with pytest.raises(dataclasses.FrozenInstanceError):
            r.title = "Changed"

    def test_default_sections(self):
        m = ReportMetadata(
            report_id=uuid.uuid4(), report_type="chart",
            report_version="1.0", generated_at=datetime.now(),
        )
        r = ChartReport(metadata=m, title="T", subject_name="S")
        assert r.sections == ()


class TestResearchReport:
    def test_is_frozen(self):
        m = ReportMetadata(
            report_id=uuid.uuid4(), report_type="research",
            report_version="1.0", generated_at=datetime.now(),
        )
        r = ResearchReport(metadata=m, title="T", snapshot_count=5)
        with pytest.raises(dataclasses.FrozenInstanceError):
            r.snapshot_count = 10


class TestComparisonReport:
    def test_is_frozen(self):
        m = ReportMetadata(
            report_id=uuid.uuid4(), report_type="comparison",
            report_version="1.0", generated_at=datetime.now(),
        )
        cids = (uuid.uuid4(), uuid.uuid4())
        r = ComparisonReport(
            metadata=m, title="T", chart_ids=cids, chart_labels=("A", "B"),
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            r.chart_ids = ()
