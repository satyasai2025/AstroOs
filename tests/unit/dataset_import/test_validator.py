"""Tests for Validator."""

import pytest
from datetime import date, datetime

from apps.api.services.dataset_import.validator import (
    Severity,
    ValidationLevel,
    ValidationRule,
    Validator,
    latitude_in_range,
    longitude_in_range,
    required_field_not_none,
    date_not_in_future,
)


class TestValidator:
    def test_passing_record(self):
        v = Validator()
        v.add_rule(latitude_in_range())
        result = v.validate_batch([{"birth_latitude": 28.0}])
        assert result.passed == 1
        assert result.failed == 0

    def test_failing_record(self):
        v = Validator()
        v.add_rule(latitude_in_range())
        result = v.validate_batch([{"birth_latitude": 95.0}])
        assert result.passed == 0
        assert result.failed == 1
        assert result.violations[0].rule_id == "U-GEO-LAT"

    def test_required_field_missing(self):
        v = Validator()
        v.add_rule(required_field_not_none("first_name"))
        result = v.validate_batch([{"first_name": None}])
        assert result.failed == 1

    def test_required_field_present(self):
        v = Validator()
        v.add_rule(required_field_not_none("first_name"))
        result = v.validate_batch([{"first_name": "John"}])
        assert result.passed == 1

    def test_multiple_rules(self):
        v = Validator()
        v.add_rule(latitude_in_range())
        v.add_rule(longitude_in_range())
        records = [
            {"birth_latitude": 28.0, "birth_longitude": 77.0},
            {"birth_latitude": 95.0, "birth_longitude": 200.0},
        ]
        result = v.validate_batch(records)
        assert result.passed == 2
        assert result.failed == 2

    def test_level_filtering(self):
        v = Validator()
        v.add_rule(ValidationRule(
            rule_id="L1-RULE", name="test", description="",
            severity=Severity.CRITICAL, level=ValidationLevel.L1,
            check=lambda r: True,
        ))
        v.add_rule(ValidationRule(
            rule_id="L2-RULE", name="test", description="",
            severity=Severity.HIGH, level=ValidationLevel.L2,
            check=lambda r: False,
        ))
        result = v.validate_batch([{}], ValidationLevel.L1)
        assert result.passed == 1
        assert result.failed == 0

    def test_date_not_in_future_pass(self):
        rule = date_not_in_future()
        assert rule.check({"birth_datetime_utc": "2000-01-01T12:00:00+00:00"})

    def test_date_not_in_future_fail(self):
        rule = date_not_in_future()
        assert not rule.check({"birth_datetime_utc": "2099-12-31T12:00:00+00:00"})


class TestValidationResult:
    def test_pass_rate(self):
        from apps.api.services.dataset_import.validator import ValidationResult, ValidationLevel
        r = ValidationResult(level=ValidationLevel.L1, passed=3, failed=1)
        assert r.pass_rate == 0.75
        assert r.total == 4
