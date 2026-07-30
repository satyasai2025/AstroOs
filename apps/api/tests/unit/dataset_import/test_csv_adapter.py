"""Tests for CsvAdapter."""

import os
import tempfile
import pytest
from apps.api.services.dataset_import.adapters.csv_adapter import CsvAdapter


def _write_csv(path: str, rows: list, delimiter: str = ","):
    """Write a CSV file with header + data rows."""
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=delimiter)
        for row in rows:
            writer.writerow(row)


@pytest.fixture
def csv_file():
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        path = f.name
    _write_csv(path, [
        ["fname", "lname", "gender", "lat", "lng", "year"],
        ["Alice", "Smith", "F", 40.7128, -74.0060, 1990],
        ["Bob", "Jones", "M", 34.0522, -118.2437, 1985],
        ["Carol", "Lee", "F", 51.5072, -0.1275, 2000],
    ])
    yield path
    os.unlink(path)


@pytest.fixture
def csv_file_tab():
    """Create a tab-delimited CSV file."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        path = f.name
    _write_csv(path, [
        ["fname", "lname", "year"],
        ["Dave", "Brown", 1995],
        ["Eve", "Davis", 2001],
    ], delimiter="\t")
    yield path
    os.unlink(path)


@pytest.fixture
def csv_file_empty():
    """Create an empty CSV file (header only)."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        path = f.name
    _write_csv(path, [["col1", "col2"]])
    yield path
    os.unlink(path)


class TestCsvAdapter:
    def test_read_yields_records(self, csv_file):
        adapter = CsvAdapter()
        records = list(adapter.read(csv_file))
        assert len(records) == 3
        assert records[0].data["fname"] == "Alice"
        assert records[0].source_index == 1
        assert records[2].data["fname"] == "Carol"

    def test_read_record_fields(self, csv_file):
        adapter = CsvAdapter()
        first = next(adapter.read(csv_file))
        assert "data" in dir(first)
        assert "source_index" in dir(first)
        assert first.data.get("lat") is not None
        assert first.data.get("lng") is not None

    def test_source_metadata(self, csv_file):
        adapter = CsvAdapter()
        meta = adapter.get_source_metadata(csv_file)
        assert meta["source_format"] == "csv"
        assert meta["record_count"] == 3
        assert "fname" in meta["source_columns"]
        assert "year" in meta["source_columns"]

    def test_column_definitions(self, csv_file):
        adapter = CsvAdapter()
        cols = adapter.get_column_definitions(csv_file)
        names = [c.name for c in cols]
        assert "fname" in names
        assert "lat" in names
        # lat/lng should be detected as float
        for c in cols:
            if c.name in ("lat", "lng"):
                assert c.data_type == "float"

    def test_get_adapter_name(self):
        adapter = CsvAdapter()
        assert adapter.get_adapter_name() == "CSV"

    def test_supported_formats(self):
        adapter = CsvAdapter()
        assert ".csv" in adapter.get_supported_formats()

    def test_tab_delimited(self, csv_file_tab):
        adapter = CsvAdapter()
        records = list(adapter.read(csv_file_tab))
        assert len(records) == 2
        assert records[0].data["fname"] == "Dave"
        assert records[1].data["fname"] == "Eve"

    def test_empty_file(self, csv_file_empty):
        adapter = CsvAdapter()
        records = list(adapter.read(csv_file_empty))
        assert len(records) == 0

    def test_no_header_mode(self):
        """Test reading a file without headers."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            path = f.name
        _write_csv(path, [
            ["Alice", "Smith", "F"],
            ["Bob", "Jones", "M"],
        ])
        try:
            adapter = CsvAdapter(has_header=False)
            records = list(adapter.read(path))
            assert len(records) == 2
            # Columns should be named col_0, col_1, col_2
            for record in records:
                assert "col_0" in record.data
                assert "col_1" in record.data
                assert "col_2" in record.data
        finally:
            os.unlink(path)
