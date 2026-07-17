"""
AstroOS — Schema Mapper

Maps source column names to AstroOS canonical field names using a
ColumnMapping configuration. Handles type coercion hints, default
values, and optional field exclusion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from apps.api.services.dataset_import.adapter_base import ColumnMapping


class SchemaMapper:
    """Transforms RawRecord.data dicts from source field names to AstroOS
    canonical field names using a list of ColumnMapping rules.

    Transformation is always deterministic and pure: no I/O, no side effects.
    """

    def __init__(self, mappings: List[ColumnMapping], record_transformers: Optional[Dict[str, Callable]] = None):
        self._mappings = {m.source_column: m for m in mappings if not m.exclude}
        self._excluded = {m.source_column for m in mappings if m.exclude}
        self._transformers = record_transformers or {}

    def map_record(self, raw: Any) -> Dict[str, Any]:
        """Map one record's source fields to AstroOS fields.

        Returns a dict keyed by AstroOS canonical field names.
        Missing required fields raise ValueError.
        Excluded fields are dropped.
        Unknown source fields are ignored (passed through if not excluded).
        """
        result: Dict[str, Any] = {}
        for mapping in self._mappings.values():
            raw_value = raw.get(mapping.source_column)
            if mapping.exclude:
                continue
            if raw_value is None and mapping.default_value is not None:
                result[mapping.target_field] = mapping.default_value
            elif raw_value is None and mapping.required:
                raise ValueError(
                    f"Required field '{mapping.target_field}' is missing "
                    f"(source column: '{mapping.source_column}')"
                )
            elif raw_value is not None and mapping.transformer:
                transform = self._transformers.get(mapping.transformer)
                if transform:
                    result[mapping.target_field] = transform(raw_value, raw)
                else:
                    result[mapping.target_field] = raw_value
            elif raw_value is not None:
                result[mapping.target_field] = raw_value
            else:
                result[mapping.target_field] = None

        return result

    def map_batch(self, records: list) -> list:
        """Map a batch of records. Returns list of mapped dicts."""
        return [self.map_record(r) for r in records]

    def get_required_fields(self) -> List[str]:
        """Return list of target fields marked as required."""
        return [m.target_field for m in self._mappings.values() if m.required]

    def get_optional_fields(self) -> List[str]:
        """Return list of target fields marked as optional."""
        return [m.target_field for m in self._mappings.values() if not m.required]
