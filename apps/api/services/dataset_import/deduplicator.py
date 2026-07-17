"""
AstroOS — Deduplicator

Identifies duplicate records using configurable key fields and
deduplication strategies. Returns deduplicated records plus a report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


@dataclass
class DeduplicationReport:
    """Report of deduplication results."""
    total_records: int = 0
    unique_records: int = 0
    duplicates_removed: int = 0
    duplicate_groups: int = 0
    duplicate_indices: List[int] = field(default_factory=list)

    @property
    def duplicate_pct(self) -> float:
        return (self.duplicates_removed / self.total_records * 100) if self.total_records > 0 else 0.0


class Deduplicator:
    """Identifies and removes duplicate records based on key fields.

    Supports exact-match and custom comparison strategies.
    """

    def __init__(self, key_fields: List[str], comparator: Optional[Callable] = None):
        """
        Args:
            key_fields: List of field names to use as the deduplication key.
            comparator: Optional custom comparator(record_a, record_b) -> bool.
                       Defaults to exact match on key_fields.
        """
        self._key_fields = key_fields
        self._comparator = comparator

    def deduplicate(self, records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], DeduplicationReport]:
        """Remove duplicates, keeping the first occurrence.

        Returns:
            (unique_records, report)
        """
        report = DeduplicationReport(total_records=len(records))
        seen_keys: Set[tuple] = set()
        unique = []

        for idx, record in enumerate(records):
            key = self._make_key(record)
            if key not in seen_keys:
                seen_keys.add(key)
                unique.append(record)
            else:
                report.duplicate_indices.append(idx)
                report.duplicates_removed += 1

        report.unique_records = len(unique)
        report.duplicate_groups = len(seen_keys)
        return unique, report

    def _make_key(self, record: Dict[str, Any]) -> tuple:
        """Create a hashable key from the deduplication fields."""
        key_parts = []
        for field in self._key_fields:
            val = record.get(field)
            key_parts.append(str(val).lower().strip() if val is not None else None)
        return tuple(key_parts)
