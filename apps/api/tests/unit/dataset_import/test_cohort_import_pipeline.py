"""Integration test for the cohort Excel import pipeline."""

import os
import tempfile
import openpyxl
import pytest
from apps.api.services.dataset_import.framework import ImportConfig, ImportPipeline
from apps.api.services.dataset_import.adapters.cohort_excel_adapter import CohortExcelAdapter
from apps.api.services.dataset_import.adapter_base import ColumnMapping
from apps.api.services.dataset_import.validator import (
    Severity, ValidationLevel, ValidationRule,
    latitude_in_range, longitude_in_range, required_field_not_none,
)


def _create_test_excel(path: str, row_count: int = 10):
    """Create a synthetic Excel file with cohort data for testing."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Cohort Data"
    # Header row
    headers = ["fname", "lname", "gender", "place", "country", "lat", "lng",
               "day", "month", "year", "hour", "min", "calType", "jdUt", "rr"]
    ws.append(headers)
    # Data rows
    for i in range(row_count):
        ws.append([
            f"First{i}", f"Last{i}",
            "M" if i % 2 == 0 else "F",
            f"City{i}", "Country",
            40.0 + i * 0.1, -70.0 - i * 0.1,
            15 + i, "Jan", 2000 + i,
            12, 0, "g", 2451545.0 + i * 365, "AA",
        ])
    wb.save(path)


@pytest.fixture
def source_file():
    """Generate a synthetic Excel file as a test fixture."""
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        path = f.name
    _create_test_excel(path, row_count=10)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def output_dir():
    """Temporary directory for pipeline output."""
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def adapter():
    return CohortExcelAdapter()


@pytest.fixture
def config(adapter, source_file, output_dir):
    return ImportConfig(
        dataset_id="ASTRO-RS-COHORT-v0.1.0",
        source_file=source_file,
        output_dir=output_dir,
        column_mappings=adapter.get_column_mappings(),
        validation_rules=[
            required_field_not_none("birth_latitude"),
            required_field_not_none("birth_longitude"),
            latitude_in_range(),
            longitude_in_range(),
        ],
        normalization_rules=adapter.get_normalization_rules(),
        dedup_key_fields=adapter.get_dedup_key_fields(),
        export_format="CSV",
        source_metadata=adapter.get_source_metadata(source_file),
    )


class TestCohortExcelAdapter:
    def test_read_yields_records(self, adapter, source_file):
        records = list(adapter.read(source_file))
        assert len(records) == 10  # Synthetic test data

    def test_read_record_fields(self, adapter, source_file):
        first = next(adapter.read(source_file))
        assert hasattr(first, "data")
        assert hasattr(first, "source_index")
        assert first.source_index == 1
        assert first.data.get("lat") is not None
        assert first.data.get("lng") is not None

    def test_source_metadata(self, adapter, source_file):
        meta = adapter.get_source_metadata(source_file)
        assert meta["source_format"] == "xlsx"
        assert "lat" in meta["source_columns"]
        assert "lng" in meta["source_columns"]

    def test_column_definitions(self, adapter, source_file):
        cols = adapter.get_column_definitions(source_file)
        assert len(cols) == 15
        names = [c.name for c in cols]
        assert "fname" in names
        assert "lat" in names

    def test_adapter_name(self, adapter):
        assert adapter.get_adapter_name() == "CohortExcel"

    def test_dataset_identity(self, adapter):
        assert adapter.DATASET_ID == "ASTRO-RS-COHORT-v0.1.0"
        assert adapter.DATASET_NAME == "RS-COHORT Birth Chart Cohort"

    def test_source_metadata_no_branding(self, adapter, source_file):
        meta = adapter.get_source_metadata(source_file)
        assert meta.get("name", "") == "RS-COHORT Birth Chart Cohort"
        assert "dataset" in meta.get("source_description", "").lower()


class TestFullPipeline:
    def test_pipeline_runs(self, config):
        pipeline = ImportPipeline(CohortExcelAdapter(), config)
        report = pipeline.run()
        assert report.errors == []
        assert report.total_records == 10
        assert report.records_imported > 0
        assert report.quality_assessment is not None
        assert report.quality_assessment["quality_score"] > 0

    def test_pipeline_produces_csv(self, config):
        pipeline = ImportPipeline(CohortExcelAdapter(), config)
        report = pipeline.run()
        assert len(report.export_results) == 1
        assert report.export_results[0].format == "CSV"
        assert report.export_results[0].record_count > 0
        assert os.path.exists(report.export_results[0].output_path)

    def test_pipeline_produces_metadata(self, config):
        pipeline = ImportPipeline(CohortExcelAdapter(), config)
        report = pipeline.run()
        assert report.export_results[0].metadata_path
        assert os.path.exists(report.export_results[0].metadata_path)

    def test_pipeline_deduplication(self, config):
        pipeline = ImportPipeline(CohortExcelAdapter(), config)
        report = pipeline.run()
        assert report.duplicate_detection is not None
        assert report.duplicate_detection.total_records == 10

    def test_pipeline_quality_tier(self, config):
        pipeline = ImportPipeline(CohortExcelAdapter(), config)
        report = pipeline.run()
        tier = report.quality_assessment["quality_tier"]
        assert tier in ["A", "B", "C", "D", "F"]
        score = report.quality_assessment["quality_score"]
        assert 0.0 <= score <= 1.0
