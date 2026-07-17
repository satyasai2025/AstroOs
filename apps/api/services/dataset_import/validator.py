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
from typing import Any, Callable, Dict, List, Optional


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
