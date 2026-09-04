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
    field_not_empty,
    string_max_length,
    enum_value,
    date_in_range,
    cross_field_consistency,
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


class TestNewValidationRules:
    def test_field_not_empty_pass(self):
        rule = field_not_empty("name")
        assert rule.check({"name": "Alice"})

    def test_field_not_empty_fail(self):
        rule = field_not_empty("name")
        assert not rule.check({"name": ""})

    def test_field_not_empty_none(self):
        rule = field_not_empty("name")
        assert rule.check({"name": None})

    def test_string_max_length_pass(self):
        rule = string_max_length("name", 5)
        assert rule.check({"name": "Alice"})

    def test_string_max_length_fail(self):
        rule = string_max_length("name", 5)
        assert not rule.check({"name": "Alexander"})

    def test_enum_value_pass(self):
        rule = enum_value("gender", {"M", "F"})
        assert rule.check({"gender": "M"})
        assert rule.check({"gender": "F"})

    def test_enum_value_fail(self):
        rule = enum_value("gender", {"M", "F"})
        assert not rule.check({"gender": "X"})

    def test_enum_value_case_insensitive(self):
        rule = enum_value("gender", {"M", "F"})
        assert rule.check({"gender": "m"})
        assert rule.check({"gender": "f"})

    def test_enum_value_case_sensitive(self):
        rule = enum_value("code", {"AA", "BB"}, case_sensitive=True)
        assert rule.check({"code": "AA"})
        assert not rule.check({"code": "aa"})

    def test_date_in_range_pass(self):
        rule = date_in_range("dt", min_date="1900-01-01", max_date="2100-01-01")
        assert rule.check({"dt": "2000-06-15T12:00:00+00:00"})

    def test_date_in_range_before_min(self):
        rule = date_in_range("dt", min_date="1900-01-01")
        assert not rule.check({"dt": "1800-01-01T00:00:00+00:00"})

    def test_date_in_range_after_max(self):
        rule = date_in_range("dt", max_date="2100-01-01")
        assert not rule.check({"dt": "2200-01-01T00:00:00+00:00"})

    def test_date_in_range_none(self):
        rule = date_in_range("dt", min_date="1900-01-01")
        assert rule.check({"dt": None})

    def test_cross_field_consistency_pass(self):
        def end_after_start(end, start):
            return end >= start
        rule = cross_field_consistency("end_date", "start_date", end_after_start)
        assert rule.check({"start_date": "2000-01-01", "end_date": "2000-06-01"})

    def test_cross_field_consistency_fail(self):
        def end_after_start(end, start):
            return end >= start
        rule = cross_field_consistency("end_date", "start_date", end_after_start)
        assert not rule.check({"start_date": "2000-06-01", "end_date": "2000-01-01"})

    def test_cross_field_consistency_null_safe(self):
        def end_after_start(end, start):
            return end >= start
        rule = cross_field_consistency("end_date", "start_date", end_after_start)
        assert rule.check({"start_date": None, "end_date": "2000-06-01"})
        assert rule.check({"start_date": "2000-01-01", "end_date": None})
