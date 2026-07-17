"""
AstroOS — Normalizer

Normalizes mapped records to AstroOS canonical formats:
- Date/time assembly from component fields
- Coordinate precision normalization
- String trimming and case normalization
- Enum value standardization
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class NormalizationAction:
    """Record of a normalization transformation applied."""
    record_index: int
    field: str
    original_value: Any
    normalized_value: Any
    action: str  # e.g. "date_assembly", "coordinate_precision", "string_trim"


class Normalizer:
    """Applies normalization rules to mapped records."""

    def __init__(self, rules: List[Callable] = None):
        self._rules = rules or []

    def normalize_record(self, record: Dict[str, Any], index: int = 0) -> Tuple[Dict[str, Any], List[NormalizationAction]]:
        """Normalize one record. Returns (normalized_record, actions_taken)."""
        actions = []
        result = dict(record)

        for rule in self._rules:
            result, new_actions = rule(result, index)
            actions.extend(new_actions)

        return result, actions

    def normalize_batch(self, records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[NormalizationAction]]:
        """Normalize a batch of records."""
        all_actions = []
        normalized = []
        for idx, record in enumerate(records):
            norm, actions = self.normalize_record(record, index=idx)
            normalized.append(norm)
            all_actions.extend(actions)
        return normalized, all_actions


def assemble_datetime(
    date_fields: Tuple[str, ...],
    time_fields: Tuple[str, ...],
    target_field: str = "birth_datetime_utc",
) -> Callable:
    """Create a normalization rule that assembles datetime from components.

    Args:
        date_fields: Tuple of (day, month, year) field names.
        time_fields: Tuple of (hour, minute) field names.
        target_field: Output field name.
    """
    day_f, month_f, year_f = date_fields
    hour_f, minute_f = time_fields

    def rule(record: Dict[str, Any], index: int) -> Tuple[Dict[str, Any], list]:
        result = dict(record)
        actions = []

        day_val = result.get(day_f)
        month_val = result.get(month_f)
        year_val = result.get(year_f)
        hour_val = result.get(hour_f) or 0
        minute_val = result.get(minute_f) or 0

        if all(v is not None for v in [day_val, month_val, year_val]):
            try:
                dt = datetime(
                    int(year_val), int(month_val), int(day_val),
                    int(hour_val), int(minute_val),
                    tzinfo=timezone.utc,
                )
                result[target_field] = dt.isoformat()
                actions.append(NormalizationAction(
                    record_index=index,
                    field=target_field,
                    original_value=f"{year_val}-{month_val}-{day_val} {hour_val}:{minute_val}",
                    normalized_value=dt.isoformat(),
                    action="date_assembly",
                ))
            except (ValueError, TypeError):
                result[target_field] = None
                actions.append(NormalizationAction(
                    record_index=index,
                    field=target_field,
                    original_value=f"{year_val}-{month_val}-{day_val}",
                    normalized_value=None,
                    action="date_assembly_failed",
                ))
        return result, actions

    return rule


def normalize_coordinates(precision: int = 6) -> Callable:
    """Create a normalization rule that rounds coordinates to N decimal places."""

    def rule(record: Dict[str, Any], index: int) -> Tuple[Dict[str, Any], list]:
        result = dict(record)
        actions = []
        for field in ("birth_latitude", "birth_longitude"):
            val = result.get(field)
            if val is not None:
                try:
                    rounded = float(Decimal(str(val)).quantize(Decimal(10) ** -precision, rounding=ROUND_HALF_UP))
                    if rounded != float(val):
                        actions.append(NormalizationAction(
                            record_index=index,
                            field=field,
                            original_value=val,
                            normalized_value=rounded,
                            action="coordinate_precision",
                        ))
                    result[field] = rounded
                except (TypeError, ValueError):
                    result[field] = None
        return result, actions

    return rule


def trim_strings(fields: Optional[List[str]] = None) -> Callable:
    """Create a normalization rule that trims whitespace from string fields."""

    def rule(record: Dict[str, Any], index: int) -> Tuple[Dict[str, Any], list]:
        result = dict(record)
        actions = []
        target_fields = fields or list(result.keys())
        for field in target_fields:
            val = result.get(field)
            if isinstance(val, str) and val != val.strip():
                original = val
                trimmed = val.strip()
                result[field] = trimmed
                actions.append(NormalizationAction(
                    record_index=index,
                    field=field,
                    original_value=original,
                    normalized_value=trimmed,
                    action="string_trim",
                ))
        return result, actions

    return rule
