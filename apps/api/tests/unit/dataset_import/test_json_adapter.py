"""Tests for JsonAdapter."""

import json
import os
import tempfile
import pytest
from apps.api.services.dataset_import.adapters.json_adapter import JsonAdapter


def _write_file(path: str, content: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


@pytest.fixture
def json_array_file():
    """Create a JSON array file."""
    data = [
        {"fname": "Alice", "lname": "Smith", "year": 1990},
        {"fname": "Bob", "lname": "Jones", "year": 1985},
        {"fname": "Carol", "lname": "Lee", "year": 2000},
    ]
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        path = f.name
        json.dump(data, f)
    yield path
    os.unlink(path)


@pytest.fixture
def jsonl_file():
    """Create a JSONL file."""
    lines = [
        json.dumps({"fname": "Dave", "lname": "Brown", "year": 1995}),
        json.dumps({"fname": "Eve", "lname": "Davis", "year": 2001}),
        json.dumps({"fname": "Frank", "lname": "Green", "year": 1988}),
    ]
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as f:
        path = f.name
        f.write("\n".join(lines))
    yield path
    os.unlink(path)


@pytest.fixture
def json_array_empty():
    """Create an empty JSON array file."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        path = f.name
        json.dump([], f)
    yield path
    os.unlink(path)


class TestJsonAdapter:
    def test_read_json_array(self, json_array_file):
        adapter = JsonAdapter()
        records = list(adapter.read(json_array_file))
        assert len(records) == 3
        assert records[0].data["fname"] == "Alice"
        assert records[0].source_index == 1

    def test_read_jsonl(self, jsonl_file):
        adapter = JsonAdapter()
        records = list(adapter.read(jsonl_file))
        assert len(records) == 3
        assert records[0].data["fname"] == "Dave"
        assert records[2].data["fname"] == "Frank"

    def test_source_metadata_json(self, json_array_file):
        adapter = JsonAdapter()
        meta = adapter.get_source_metadata(json_array_file)
        assert meta["source_format"] == "json"
        assert meta["record_count"] == 3
        assert "fname" in meta["source_columns"]

    def test_source_metadata_jsonl(self, jsonl_file):
        adapter = JsonAdapter()
        meta = adapter.get_source_metadata(jsonl_file)
        assert meta["source_format"] == "jsonl"
        assert meta["record_count"] == 3

    def test_empty_array(self, json_array_empty):
        adapter = JsonAdapter()
        records = list(adapter.read(json_array_empty))
        assert len(records) == 0

    def test_get_adapter_name(self):
        adapter = JsonAdapter()
        assert adapter.get_adapter_name() == "JSON"

    def test_supported_formats(self):
        adapter = JsonAdapter()
        fmts = adapter.get_supported_formats()
        assert ".json" in fmts
        assert ".jsonl" in fmts

    def test_column_definitions_json(self, json_array_file):
        adapter = JsonAdapter()
        cols = adapter.get_column_definitions(json_array_file)
        names = [c.name for c in cols]
        assert "fname" in names
        assert "year" in names
        for c in cols:
            if c.name == "year":
                assert c.data_type == "integer"
            if c.name in ("fname", "lname"):
                assert c.data_type == "string"

    def test_column_definitions_jsonl(self, jsonl_file):
        adapter = JsonAdapter()
        cols = adapter.get_column_definitions(jsonl_file)
        names = [c.name for c in cols]
        assert "fname" in names
        assert "lname" in names

    def test_detect_mixed_types(self):
        """Test with mixed-type values."""
        data = [
            {"name": "Alice", "active": True, "score": 95},
            {"name": "Bob", "active": False, "score": 87},
        ]
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            path = f.name
            json.dump(data, f)
        try:
            adapter = JsonAdapter()
            cols = adapter.get_column_definitions(path)
            col_map = {c.name: c for c in cols}
            assert col_map["active"].data_type == "boolean"
            assert col_map["score"].data_type == "integer"
        finally:
            os.unlink(path)
