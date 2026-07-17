"""
AstroOS — Statistics Domain Model Unit Tests (Module 18, Phase 1)
"""

import dataclasses
import uuid
from datetime import datetime

import pytest

from apps.api.domain.statistics import (
    AggregateReport,
    Crosstab,
    DatasetMetadata,
    Distribution,
    NumericSummary,
    StatValue,
)


class TestStatValue:
    def test_is_frozen(self):
        s = StatValue(label="Mean", value=5.0, unit="mean")
        with pytest.raises(dataclasses.FrozenInstanceError):
            s.value = 10.0


class TestDistribution:
    def test_is_frozen(self):
        d = Distribution(label="Test", variable="x", bins=("a",), counts=(5,), total=5)
        with pytest.raises(dataclasses.FrozenInstanceError):
            d.total = 10

    def test_bins_and_counts_aligned(self):
        d = Distribution(
            label="Houses", variable="planet.x.house",
            bins=("1", "2", "3"), counts=(10, 20, 30), total=60,
        )
        assert len(d.bins) == len(d.counts) == 3


class TestCrosstab:
    def test_is_frozen(self):
        c = Crosstab(
            label="T", row_variable="r", column_variable="c",
            row_labels=("a",), column_labels=("x",),
            cells=((5,),), row_totals=(5,),
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            c.row_labels = ("b",)


class TestNumericSummary:
    def test_is_frozen(self):
        n = NumericSummary(
            label="T", variable="x", count=5, mean=3.0, std_dev=1.0,
            min=1.0, max=5.0, median=3.0, q1=2.0, q3=4.0, sum=15.0,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            n.mean = 4.0

    def test_expected_fields(self):
        n = NumericSummary(
            label="Jupiter House", variable="planet.jupiter.house",
            count=100, mean=5.5, std_dev=2.0,
            min=1.0, max=12.0, median=5.5, q1=3.0, q3=8.0, sum=550.0,
        )
        assert n.count == 100
        assert n.mean == 5.5
        assert n.median == 5.5


class TestDatasetMetadata:
    def test_is_frozen(self):
        m = DatasetMetadata(sample_size=10, snapshot_count=10)
        with pytest.raises(dataclasses.FrozenInstanceError):
            m.sample_size = 20

    def test_defaults(self):
        m = DatasetMetadata(sample_size=5, snapshot_count=10)
        assert m.filtered_sample_size is None
        assert m.experiment_id is None
        assert m.engine_version == "1.0"
        assert m.generated_at is None

    def test_all_fields(self):
        eid = uuid.uuid4()
        now = datetime.now()
        m = DatasetMetadata(
            sample_size=50, snapshot_count=100, filtered_sample_size=200,
            experiment_id=eid, engine_version="1.1", generated_at=now,
        )
        assert m.sample_size == 50
        assert m.filtered_sample_size == 200
        assert m.experiment_id == eid
        assert m.generated_at == now


class TestAggregateReport:
    def test_is_frozen(self):
        meta = DatasetMetadata(sample_size=0, snapshot_count=0)
        r = AggregateReport(title="Test", metadata=meta)
        with pytest.raises(dataclasses.FrozenInstanceError):
            r.title = "Changed"

    def test_default_collections(self):
        meta = DatasetMetadata(sample_size=0, snapshot_count=0)
        r = AggregateReport(title="T", metadata=meta)
        assert r.distributions == ()
        assert r.crosstabs == ()
        assert r.numeric_summaries == ()
        assert r.stat_values == ()

    def test_reports_version_default(self):
        meta = DatasetMetadata(sample_size=0, snapshot_count=0)
        r = AggregateReport(title="T", metadata=meta)
        assert r.report_version == "1.0"
