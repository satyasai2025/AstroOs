"""
AstroOS — CSV Adapter

Reads any CSV file and yields RawRecord objects.
Handles various delimiters, encodings, and line endings.
Uses only Python stdlib (csv module).
"""

from __future__ import annotations

import csv
import os
import codecs
from typing import Any, Dict, Iterator, List, Optional

from apps.api.services.dataset_import.adapter_base import ColumnDefinition, RawRecord, SourceAdapter


class CsvAdapter(SourceAdapter):
    """Generic CSV adapter for .csv files.

    Auto-detects delimiter, handles BOM, and infers column types.
    """

    SUPPORTED_EXTENSIONS = [".csv"]
    COMMON_DELIMITERS = [",", "\t", ";", "|"]

    def __init__(
        self,
        delimiter: Optional[str] = None,
        encoding: str = "utf-8-sig",
        has_header: bool = True,
    ):
        """
        Args:
            delimiter: Delimiter character. None = auto-detect.
            encoding: File encoding. Default utf-8-sig handles BOM.
            has_header: First row is a header row.
        """
        self._delimiter = delimiter
        self._encoding = encoding
        self._has_header = has_header

    def _detect_delimiter(self, sample: str) -> str:
        """Detect delimiter by counting occurrences in the first line."""
        first_line = sample.split("\n")[0] if sample else ""
        counts = {d: first_line.count(d) for d in self.COMMON_DELIMITERS}
        # Return the delimiter with the most occurrences (excluding zero)
        best = max(counts, key=counts.get)
        return best if counts[best] > 0 else ","

    def _open_file(self, file_path: str):
        """Open file with encoding detection, return file object."""
        raw = open(file_path, "rb")
        # Read BOM
        prefix = raw.read(3)
        raw.seek(0)
        if prefix.startswith(codecs.BOM_UTF8):
            return codecs.getreader("utf-8-sig")(raw)
        elif prefix.startswith(codecs.BOM_UTF16_LE):
            return codecs.getreader("utf-16-le")(raw)
        elif prefix.startswith(codecs.BOM_UTF16_BE):
            return codecs.getreader("utf-16-be")(raw)
        else:
            raw.seek(0)
            return codecs.getreader(self._encoding)(raw)

    def _detect_encoding(self, file_path: str) -> str:
        """Detect encoding from BOM. Returns encoding name."""
        with open(file_path, "rb") as f:
            prefix = f.read(3)
        if prefix.startswith(codecs.BOM_UTF8):
            return "utf-8-sig"
        elif prefix.startswith(codecs.BOM_UTF16_LE):
            return "utf-16-le"
        elif prefix.startswith(codecs.BOM_UTF16_BE):
            return "utf-16-be"
        return self._encoding

    def read(self, file_path: str) -> Iterator[RawRecord]:
        delimiter = self._delimiter
        encoding = self._detect_encoding(file_path)

        # Sample for delimiter detection
        if delimiter is None:
            with self._open_file(file_path) as f:
                sample = f.read(4096)
                f.seek(0) if hasattr(f, 'seek') else None
                delimiter = self._detect_delimiter(sample)

        # For auto-detection, re-open after sampling
        file_obj = self._open_file(file_path)
        try:
            reader = csv.DictReader(file_obj, delimiter=delimiter)

            # If no header, create generic column names
            if not self._has_header:
                # Peek at first row to count columns
                first_row = next(reader, None)
                if first_row is None:
                    return
                field_count = len(first_row)
                fieldnames = [f"col_{i}" for i in range(field_count)]
                # Re-create reader with explicit fieldnames
                file_obj.seek(0)
                reader = csv.DictReader(
                    file_obj, delimiter=delimiter, fieldnames=fieldnames
                )
                start_idx = 0
            else:
                if reader.fieldnames is None:
                    return
                start_idx = 0

            for idx, row in enumerate(reader, start=start_idx):
                # Strip whitespace from keys and values
                cleaned = {}
                for k, v in row.items():
                    key = k.strip() if k else f"col_{idx}"
                    cleaned[key] = v.strip() if isinstance(v, str) else v

                yield RawRecord(
                    data=cleaned,
                    source_index=idx + 1,
                    source_file=os.path.basename(file_path),
                    source_sheet="",
                )
        finally:
            file_obj.close()

    def get_source_metadata(self, file_path: str) -> Dict[str, Any]:
        delimiter = self._detect_delimiter(
            open(file_path, "r", encoding=self._detect_encoding(file_path)).read(4096)
        )
        encoding = self._detect_encoding(file_path)

        with self._open_file(file_path) as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            fieldnames = reader.fieldnames or []
            record_count = sum(1 for _ in reader)

        file_size = os.path.getsize(file_path)

        return {
            "source_file": os.path.basename(file_path),
            "source_format": "csv",
            "record_count": record_count,
            "source_columns": fieldnames,
            "delimiter": delimiter,
            "encoding": encoding.replace("-sig", ""),
            "file_size_bytes": file_size,
        }

    def get_column_definitions(self, file_path: str) -> List[ColumnDefinition]:
        delimiter = self._detect_delimiter(
            open(file_path, "r", encoding=self._detect_encoding(file_path)).read(4096)
        )

        with self._open_file(file_path) as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            fieldnames = reader.fieldnames or []

            # Read first 10 data rows for type inference
            sample_rows = []
            for i, row in enumerate(reader):
                if i >= 10:
                    break
                sample_rows.append(row)

        columns = []
        for field in fieldnames:
            values = [row.get(field) for row in sample_rows]
            non_null = [v for v in values if v is not None and v != ""]

            # Infer type
            if not non_null:
                data_type = "string"
                nullable = True
            elif all(_is_numeric(v) for v in non_null):
                if all(v.isdigit() if isinstance(v, str) else True for v in non_null):
                    data_type = "integer"
                else:
                    data_type = "float"
                nullable = any(v is None or v == "" for v in values)
            else:
                data_type = "string"
                nullable = any(v is None or v == "" for v in values)

            columns.append(ColumnDefinition(
                name=field,
                data_type=data_type,
                nullable=nullable,
                example=non_null[0] if non_null else None,
            ))

        return columns

    def get_adapter_name(self) -> str:
        return "CSV"

    def get_supported_formats(self) -> List[str]:
        return self.SUPPORTED_EXTENSIONS


def _is_numeric(value: Any) -> bool:
    """Check if a value is numeric (int or float)."""
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    return False
