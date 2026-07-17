"""Integration test for the full AstroDatabank import pipeline."""

import os
import tempfile
import pytest
from apps.api.services.dataset_import.framework import ImportConfig, ImportPipeline
from apps.api.services.dataset_import.adapters.astrodatabank_adapter import AstroDatabankAdapter
from apps.api.services.dataset_import.adapter_base import ColumnMapping
from apps.api.services.dataset_import.validator import (
    Severity, ValidationLevel, ValidationRule,
    latitude_in_range, longitude_in_range, required_field_not_none,
)


@pytest.fixture
def astrodatabank_file():
    """Path to the AstroDatabank.xlsx test fixture."""
    path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "Downloads", "AstroDatabank.xlsx")
    if not os.path.exists(path):
        pytest.skip("AstroDatabank.xlsx not found in Downloads folder")
    return path


@pytest.fixture
def output_dir():
    """Temporary directory for pipeline output."""
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def adapter():
    return AstroDatabankAdapter()


@pytest.fixture
def config(adapter, astrodatabank_file, output_dir):
    return ImportConfig(
        dataset_id="ASTRO-RS-COHORT-v0.1.0",
        source_file=astrodatabank_file,
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
        source_metadata=adapter.get_source_metadata(astrodatabank_file),
    )


class TestAstroDatabankAdapter:
    def test_read_yields_records(self, adapter, astrodatabank_file):
        records = list(adapter.read(astrodatabank_file))
        assert len(records) > 0
        assert len(records) == 57466  # AstroDatabank has exactly 57466 records

    def test_read_record_fields(self, adapter, astrodatabank_file):
        first = next(adapter.read(astrodatabank_file))
        assert "data" in first
        assert "source_index" in first
        assert first.source_index == 1
        assert first.data.get("lat") is not None
        assert first.data.get("lng") is not None

    def test_source_metadata(self, adapter, astrodatabank_file):
        meta = adapter.get_source_metadata(astrodatabank_file)
        assert meta["record_count"] == 57466
        assert meta["source_format"] == "xlsx"
        assert "lat" in meta["source_columns"]
        assert "lng" in meta["source_columns"]

    def test_column_definitions(self, adapter, astrodatabank_file):
        cols = adapter.get_column_definitions(astrodatabank_file)
        assert len(cols) == 15
        names = [c.name for c in cols]
        assert "fname" in names
        assert "lat" in names


class TestFullPipeline:
    def test_pipeline_runs(self, config):
        pipeline = ImportPipeline(AstroDatabankAdapter(), config)
        report = pipeline.run()
        assert report.errors == []
        assert report.total_records == 57466
        assert report.records_imported > 0
        assert report.quality_assessment is not None
        assert report.quality_assessment["quality_score"] > 0

    def test_pipeline_produces_csv(self, config):
        pipeline = ImportPipeline(AstroDatabankAdapter(), config)
        report = pipeline.run()
        assert len(report.export_results) == 1
        assert report.export_results[0].format == "CSV"
        assert report.export_results[0].record_count > 0
        assert os.path.exists(report.export_results[0].output_path)

    def test_pipeline_produces_metadata(self, config):
        pipeline = ImportPipeline(AstroDatabankAdapter(), config)
        report = pipeline.run()
        assert report.export_results[0].metadata_path
        assert os.path.exists(report.export_results[0].metadata_path)

    def test_pipeline_deduplication(self, config):
        pipeline = ImportPipeline(AstroDatabankAdapter(), config)
        report = pipeline.run()
        assert report.duplicate_detection is not None
        assert report.duplicate_detection.total_records == 57466

    def test_pipeline_quality_tier(self, config):
        pipeline = ImportPipeline(AstroDatabankAdapter(), config)
        report = pipeline.run()
        tier = report.quality_assessment["quality_tier"]
        assert tier in ["A", "B", "C", "D", "F"]
        score = report.quality_assessment["quality_score"]
        assert 0.0 <= score <= 1.0
