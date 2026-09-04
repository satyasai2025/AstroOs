"""
AstroOS — JSON / JSONL Adapter

Reads JSON (array of objects) and JSONL (one JSON object per line) files
and yields RawRecord objects. Auto-detects format from file content.
Uses only Python stdlib (json module).
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterator, List

from apps.api.services.dataset_import.adapter_base import ColumnDefinition, RawRecord, SourceAdapter


class JsonAdapter(SourceAdapter):
    """Generic JSON/JSONL adapter for .json and .jsonl files.

    Auto-detects JSON array vs JSONL format by checking the first
    non-whitespace character.
    """

    SUPPORTED_EXTENSIONS = [".json", ".jsonl"]

    def read(self, file_path: str) -> Iterator[RawRecord]:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            content = f.read()

        stripped = content.strip()
        if not stripped:
            return

        # Detect format: JSON array starts with '[', JSONL starts with '{'
        if stripped[0] == "[":
            yield from self._read_json_array(content, file_path)
        elif stripped[0] == "{":
            yield from self._read_jsonl(content, file_path)
        else:
            raise ValueError(
                f"Unrecognized JSON format in {file_path}: "
                f"expected '[' (JSON array) or '{{' (JSONL), got '{stripped[0]}'"
            )

    def _read_json_array(self, content: str, file_path: str) -> Iterator[RawRecord]:
        """Read JSON array of objects."""
        records = json.loads(content)
        if not isinstance(records, list):
            raise ValueError("JSON root must be an array of objects")

        for idx, item in enumerate(records):
            if not isinstance(item, dict):
                raise ValueError(f"JSON array element at index {idx} is not an object")
            yield RawRecord(
                data=item,
                source_index=idx + 1,
                source_file=os.path.basename(file_path),
                source_sheet="",
            )

    def _read_jsonl(self, content: str, file_path: str) -> Iterator[RawRecord]:
        """Read JSONL (one JSON object per line)."""
        lines = content.split("\n")
        idx = 0
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue  # skip blank lines
            item = json.loads(stripped)
            if not isinstance(item, dict):
                raise ValueError(f"JSONL line {idx + 1} is not an object")
            yield RawRecord(
                data=item,
                source_index=idx + 1,
                source_file=os.path.basename(file_path),
                source_sheet="",
            )
            idx += 1

    def get_source_metadata(self, file_path: str) -> Dict[str, Any]:
        """Return source metadata. Reads file to count records and discover keys."""
        with open(file_path, "r", encoding="utf-8-sig") as f:
            content = f.read()

        stripped = content.strip()
        if not stripped:
            return {
                "source_file": os.path.basename(file_path),
                "source_format": "json",
                "record_count": 0,
                "source_columns": [],
                "file_size_bytes": os.path.getsize(file_path),
            }

        # Detect format
        if stripped[0] == "[":
            records = json.loads(stripped)
            record_count = len(records) if isinstance(records, list) else 0
            source_format = "json"
        elif stripped[0] == "{":
            lines = [l for l in stripped.split("\n") if l.strip()]
            record_count = len(lines)
            source_format = "jsonl"
        else:
            record_count = 0
            source_format = "json"

        # Infer columns from first record
        sample = self._get_first_record(stripped)
        columns = list(sample.keys()) if sample else []

        return {
            "source_file": os.path.basename(file_path),
            "source_format": source_format,
            "record_count": record_count,
            "source_columns": columns,
            "file_size_bytes": os.path.getsize(file_path),
        }

    def get_column_definitions(self, file_path: str) -> List[ColumnDefinition]:
        """Infer column types from the first 10 records."""
        with open(file_path, "r", encoding="utf-8-sig") as f:
            content = f.read()

        stripped = content.strip()
        if not stripped:
            return []

        records = self._get_sample_records(stripped, max_samples=10)
        if not records:
            return []

        # Get union of all keys
        all_keys: set = set()
        for r in records:
            all_keys.update(r.keys())

        columns = []
        for key in sorted(all_keys):
            values = [r.get(key) for r in records]
            non_null = [v for v in values if v is not None]
            nullable = any(v is None for v in values)

            if not non_null:
                data_type = "string"
            elif all(isinstance(v, bool) for v in non_null):
                data_type = "boolean"
            elif all(isinstance(v, int) for v in non_null):
                data_type = "integer"
            elif all(isinstance(v, (int, float)) for v in non_null):
                data_type = "float"
            elif all(isinstance(v, dict) for v in non_null):
                data_type = "object"
            elif all(isinstance(v, list) for v in non_null):
                data_type = "array"
            else:
                data_type = "string"

            columns.append(ColumnDefinition(
                name=key,
                data_type=data_type,
                nullable=nullable,
                example=non_null[0] if non_null else None,
            ))

        return columns

    def _get_first_record(self, content: str) -> dict:
        """Get the first record from JSON or JSONL content."""
        stripped = content.strip()
        if not stripped:
            return {}
        if stripped[0] == "[":
            records = json.loads(stripped)
            if isinstance(records, list) and records:
                return records[0]
        elif stripped[0] == "{":
            first_line = stripped.split("\n")[0].strip()
            if first_line:
                return json.loads(first_line)
        return {}

    def _get_sample_records(self, content: str, max_samples: int = 10) -> List[dict]:
        """Get up to max_samples records from JSON or JSONL content."""
        stripped = content.strip()
        if not stripped:
            return []
        if stripped[0] == "[":
            records = json.loads(stripped)
            if isinstance(records, list):
                return records[:max_samples]
        elif stripped[0] == "{":
            lines = [l.strip() for l in stripped.split("\n") if l.strip()]
            samples = []
            for line in lines[:max_samples]:
                try:
                    samples.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
            return samples
        return []

    def get_adapter_name(self) -> str:
        return "JSON"

    def get_supported_formats(self) -> List[str]:
        return self.SUPPORTED_EXTENSIONS
