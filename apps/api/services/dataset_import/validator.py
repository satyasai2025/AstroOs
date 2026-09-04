"""
AstroOS — Validator

Validates mapped records against a set of validation rules.
Supports L1 (schema) and L2 (quality) validation levels.
Each rule returns a ValidationResult with pass/fail, severity, and details.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ValidationLevel(str, Enum):
    L1 = "L1"  # Schema validation
    L2 = "L2"  # Quality validation


@dataclass
class ValidationRule:
    """A single validation rule."""
    rule_id: str
    name: str
    description: str
    severity: Severity
    level: ValidationLevel
    check: Callable[[Dict[str, Any]], bool]
    error_message: str = ""


@dataclass
class Violation:
    """A single validation violation."""
    rule_id: str
    severity: Severity
    record_index: int
    field: str
    message: str
    value: Any = None


@dataclass
class ValidationResult:
    """Result of validating one or more records."""
    level: ValidationLevel
    passed: int = 0
    failed: int = 0
    violations: List[Violation] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.passed + self.failed

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total > 0 else 0.0


class Validator:
    """Validates mapped records against registered rules.

    Rules are checked in order. First failure per record per rule stops
    processing for that rule (fail-fast per record).
    """

    def __init__(self):
        self._rules: List[ValidationRule] = []

    def add_rule(self, rule: ValidationRule) -> None:
        self._rules.append(rule)

    def validate_batch(self, records: List[Dict[str, Any]], level: ValidationLevel = ValidationLevel.L1) -> ValidationResult:
        """Validate all records at the given level. Returns aggregated result."""
        result = ValidationResult(level=level)

        for idx, record in enumerate(records):
            for rule in self._rules:
                if rule.level != level:
                    continue
                if not rule.check(record):
                    result.failed += 1
                    result.violations.append(Violation(
                        rule_id=rule.rule_id,
                        severity=rule.severity,
                        record_index=idx,
                        field="",
                        message=rule.error_message or rule.name,
                    ))
                else:
                    result.passed += 1

        return result


def required_field_not_none(field_name: str) -> ValidationRule:
    """Factory for a 'required field not null' rule."""
    def check(record: Dict[str, Any]) -> bool:
        return record.get(field_name) is not None
    return ValidationRule(
        rule_id=f"U-REQ-{field_name.upper()}",
        name=f"Required field {field_name} is not null",
        description=f"Field {field_name} must be present and non-null",
        severity=Severity.CRITICAL,
        level=ValidationLevel.L1,
        check=check,
        error_message=f"Field '{field_name}' is null or missing",
    )


def latitude_in_range(min_lat: float = -90.0, max_lat: float = 90.0) -> ValidationRule:
    """Factory for latitude range validation."""
    def check(record: Dict[str, Any]) -> bool:
        val = record.get("birth_latitude")
        if val is None:
            return True  # handled by required-field rule
        try:
            return min_lat <= float(val) <= max_lat
        except (TypeError, ValueError):
            return False
    return ValidationRule(
        rule_id="U-GEO-LAT",
        name="Latitude in valid range",
        description=f"birth_latitude must be between {min_lat} and {max_lat}",
        severity=Severity.CRITICAL,
        level=ValidationLevel.L1,
        check=check,
        error_message=f"birth_latitude out of range [{min_lat}, {max_lat}]",
    )


def longitude_in_range(min_lon: float = -180.0, max_lon: float = 180.0) -> ValidationRule:
    """Factory for longitude range validation."""
    def check(record: Dict[str, Any]) -> bool:
        val = record.get("birth_longitude")
        if val is None:
            return True
        try:
            return min_lon <= float(val) <= max_lon
        except (TypeError, ValueError):
            return False
    return ValidationRule(
        rule_id="U-GEO-LON",
        name="Longitude in valid range",
        description=f"birth_longitude must be between {min_lon} and {max_lon}",
        severity=Severity.CRITICAL,
        level=ValidationLevel.L1,
        check=check,
        error_message=f"birth_longitude out of range [{min_lon}, {max_lon}]",
    )


def date_not_in_future(field_name: str = "birth_datetime_utc") -> ValidationRule:
    """Factory for 'date not in future' validation."""
    def check(record: Dict[str, Any]) -> bool:
        val = record.get(field_name)
        if val is None:
            return True
        try:
            if isinstance(val, str):
                d = datetime.fromisoformat(val.replace("Z", "+00:00"))
            elif isinstance(val, datetime):
                d = val
            elif isinstance(val, date):
                d = datetime(val.year, val.month, val.day, tzinfo=None)
            else:
                return False
            return d <= datetime.now(d.tzinfo) if d.tzinfo else d.date() <= date.today()
        except (TypeError, ValueError):
            return False
    return ValidationRule(
        rule_id="U-DATE-FUTURE",
        name="Date not in future",
        description=f"{field_name} must not be in the future",
        severity=Severity.HIGH,
        level=ValidationLevel.L1,
        check=check,
        error_message=f"{field_name} is in the future",
    )


def field_not_empty(field_name: str) -> ValidationRule:
    """Factory: validates that a string field is not empty."""
    def check(record: Dict[str, Any]) -> bool:
        val = record.get(field_name)
        if val is None:
            return True
        return isinstance(val, str) and len(val.strip()) > 0
    return ValidationRule(
        rule_id=f"U-REQ-{field_name.upper()}-NOT-EMPTY",
        name=f"Field {field_name} is not empty",
        description=f"String field {field_name} must not be empty",
        severity=Severity.HIGH,
        level=ValidationLevel.L1,
        check=check,
        error_message=f"Field '{field_name}' is empty",
    )


def string_max_length(field_name: str, max_len: int) -> ValidationRule:
    """Factory: validates that a string field does not exceed max length."""
    def check(record: Dict[str, Any]) -> bool:
        val = record.get(field_name)
        if val is None:
            return True
        return isinstance(val, str) and len(val) <= max_len
    return ValidationRule(
        rule_id=f"U-STR-{field_name.upper()}-LEN",
        name=f"Field {field_name} max length {max_len}",
        description=f"String field {field_name} must not exceed {max_len} characters",
        severity=Severity.MEDIUM,
        level=ValidationLevel.L2,
        check=check,
        error_message=f"Field '{field_name}' exceeds {max_len} characters",
    )


def enum_value(field_name: str, allowed_values: Set[str], case_sensitive: bool = False) -> ValidationRule:
    """Factory: validates that a field's value is in an allowed set."""
    def check(record: Dict[str, Any]) -> bool:
        val = record.get(field_name)
        if val is None:
            return True
        if not isinstance(val, str):
            return False
        if case_sensitive:
            return val in allowed_values
        return val.lower() in {v.lower() for v in allowed_values}
    return ValidationRule(
        rule_id=f"U-ENUM-{field_name.upper()}",
        name=f"Field {field_name} is valid enum value",
        description=f"Field {field_name} must be one of: {', '.join(sorted(allowed_values))}",
        severity=Severity.CRITICAL,
        level=ValidationLevel.L1,
        check=check,
        error_message=f"Field '{field_name}' has invalid value",
    )


def date_in_range(field_name: str, min_date: Optional[str] = None, max_date: Optional[str] = None) -> ValidationRule:
    """Factory: validates a date field is within a range (ISO 8601 strings).

    Supports both date-only (YYYY-MM-DD) and datetime (ISO 8601) values.
    Comparisons are done as strings for date-only, or as datetimes for full
    timestamps, to avoid naive-vs-aware comparison errors.
    """
    def check(record: Dict[str, Any]) -> bool:
        val = record.get(field_name)
        if val is None:
            return True
        try:
            val_str = str(val).replace("Z", "+00:00")
            # Try datetime parse first, fall back to string comparison
            try:
                dt = datetime.fromisoformat(val_str)
                if min_date and dt < datetime.fromisoformat(min_date):
                    return False
                if max_date and dt > datetime.fromisoformat(max_date):
                    return False
            except (ValueError, TypeError):
                # Date-only string comparison
                if min_date and val_str < min_date:
                    return False
                if max_date and val_str > max_date:
                    return False
            return True
        except (TypeError, ValueError):
            return False
    desc_parts = []
    if min_date:
        desc_parts.append(f">= {min_date}")
    if max_date:
        desc_parts.append(f"<= {max_date}")
    range_desc = " and ".join(desc_parts) if desc_parts else "any date"
    return ValidationRule(
        rule_id=f"U-DATE-{field_name.upper()}-RNG",
        name=f"Date field {field_name} in range",
        description=f"Field {field_name} must satisfy {range_desc}",
        severity=Severity.HIGH,
        level=ValidationLevel.L2,
        check=check,
        error_message=f"Field '{field_name}' is outside allowed date range",
    )


def cross_field_consistency(
    field_a: str,
    field_b: str,
    predicate: Callable[[Any, Any], bool],
    rule_id: Optional[str] = None,
) -> ValidationRule:
    """Factory: validates a predicate across two fields.

    The predicate receives (value_a, value_b) and returns True if consistent.
    If either field is None, the check passes (null-safe).
    """
    rid = rule_id or f"U-CROSS-{field_a.upper()}-{field_b.upper()}"

    def check(record: Dict[str, Any]) -> bool:
        val_a = record.get(field_a)
        val_b = record.get(field_b)
        if val_a is None or val_b is None:
            return True
        return predicate(val_a, val_b)

    return ValidationRule(
        rule_id=rid,
        name=f"Cross-field consistency: {field_a} vs {field_b}",
        description=f"Fields {field_a} and {field_b} must satisfy a consistency predicate",
        severity=Severity.MEDIUM,
        level=ValidationLevel.L2,
        check=check,
        error_message=f"Cross-field check failed between '{field_a}' and '{field_b}'",
    )
