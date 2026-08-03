"""
Unit tests for apps/api/services/research_validation.py (Module 27).

Pure validation — no DB, no ephemeris. Locks in the seven runtime bugs
fixed 2026-07-31 (see docs/module-27-research-case-import-report.md §2):
undefined _valid_age_range, missing SourceConfidence import,
person_bon_confidence typo, loop-var `e` vs `event`, two wrong schema
field names, and `existing_hashes or set()` silently discarding the
batch's shared hash set.
"""

from __future__ import annotations

from datetime import date

import pytest

from apps.api.schemas.research_case import (
    EventType,
    Gender,
    LifeEventCreateSchema,
    PersonInfoSchema,
    ResearchCaseCreateSchema,
)
from apps.api.services.research_validation import (
    validate_research_case,
    validate_research_case_batch,
)


def make_person(**overrides):
    defaults = dict(
        name="Test", gender=Gender.FEMALE, dob=date(1986, 6, 15), tob="10:30",
        place="Delhi", latitude=28.6139, longitude=77.209,
        timezone="Asia/Kolkata", source="Interview",
    )
    defaults.update(overrides)
    return PersonInfoSchema(**defaults)


def make_event(**overrides):
    defaults = dict(type=EventType.MARRIAGE, event_date=date(2012, 2, 14))
    defaults.update(overrides)
    return LifeEventCreateSchema(**defaults)


def make_case(id: str = "RC-2024-001", person=None, life_events=None, **overrides):
    defaults = dict(
        id=id,
        person=person if person is not None else make_person(),
        life_events=life_events if life_events is not None else [make_event()],
    )
    defaults.update(overrides)
    return ResearchCaseCreateSchema(**defaults)


class TestValidCase:
    def test_valid_case_passes_cleanly(self):
        result = validate_research_case(make_case())
        assert result.valid is True
        assert result.duplicate_case is False
        assert result.duplicate_events == []
        assert result.issues == []


class TestBirthDataValidation:
    def test_future_dob_is_invalid(self):
        result = validate_research_case(make_case(person=make_person(dob=date(2030, 1, 1))))
        assert result.valid is False
        assert any(i.field == "person.dob" for i in result.issues)

    def test_pre_1500_dob_is_invalid(self):
        result = validate_research_case(make_case(person=make_person(dob=date(1400, 1, 1))))
        assert result.valid is False
        assert any(i.field == "person.dob" for i in result.issues)

    def test_zero_coordinates_are_invalid(self):
        result = validate_research_case(
            make_case(person=make_person(latitude=0, longitude=0))
        )
        assert result.valid is False
        assert any("latitude" in i.field for i in result.issues)

    def test_missing_place_is_invalid(self):
        result = validate_research_case(make_case(person=make_person(place="")))
        assert result.valid is False
        assert any(i.field == "person.place" for i in result.issues)

    def test_missing_timezone_is_invalid(self):
        result = validate_research_case(make_case(person=make_person(timezone="")))
        assert result.valid is False
        assert any(i.field == "person.timezone" for i in result.issues)


class TestEventValidation:
    def test_event_before_birth_is_invalid(self):
        result = validate_research_case(
            make_case(life_events=[make_event(event_date=date(1980, 1, 1))])
        )
        assert result.valid is False
        assert any("event_date" in i.field for i in result.issues)

    def test_future_event_is_invalid(self):
        result = validate_research_case(
            make_case(life_events=[make_event(event_date=date(2035, 1, 1))])
        )
        assert result.valid is False
        assert any("event_date" in i.field for i in result.issues)

    def test_event_window_out_of_range_rejected_by_schema(self):
        """event_window_days is constrained at the Pydantic schema layer (le=365),
        so the validator's own range branch is defensive/unreachable via the API."""
        with pytest.raises(Exception):
            make_case(life_events=[make_event(event_window_days=500)])


class TestDuplicateDetection:
    def test_duplicate_case_within_batch_flags_second(self):
        first = make_case(id="RC-2024-001")
        second = make_case(id="RC-2024-002")  # same person data, new id
        batch = validate_research_case_batch([first, second])
        assert batch.validations[0].valid is True
        assert batch.validations[1].duplicate_case is True
        assert batch.validations[1].valid is False
        assert batch.total_valid == 1
        assert batch.total_invalid == 1

    def test_shared_hash_set_is_respected_not_discarded(self):
        """Regression for bug #7: `existing_hashes or set()` is falsy when empty."""
        seen: set[str] = set()
        validate_research_case(make_case(id="RC-A"), existing_hashes=seen)
        result = validate_research_case(make_case(id="RC-B"), existing_hashes=seen)
        assert result.duplicate_case is True

    def test_duplicate_events_within_case_are_warned(self):
        case = make_case(
            life_events=[
                make_event(event_date=date(2012, 2, 14)),
                make_event(event_date=date(2012, 2, 14)),
            ]
        )
        result = validate_research_case(case)
        assert len(result.duplicate_events) == 1
        assert any(i.severity == "warning" for i in result.issues)

    def test_different_event_dates_are_not_duplicates(self):
        case = make_case(
            life_events=[
                make_event(type=EventType.MARRIAGE, event_date=date(2012, 2, 14)),
                make_event(type=EventType.MARRIAGE, event_date=date(2015, 6, 1)),
            ]
        )
        result = validate_research_case(case)
        assert result.duplicate_events == []
        assert result.valid is True


class TestConfidencePropagation:
    def test_high_event_confidence_warns_when_birth_medium(self):
        case = make_case(
            person=make_person(birth_time_confidence="medium"),
            life_events=[make_event(confidence="high")],
        )
        result = validate_research_case(case)
        assert result.valid is True  # warning severity, not an error
        assert any("confidence" in i.field for i in result.issues)

    def test_high_event_confidence_no_warning_when_birth_high(self):
        case = make_case(
            person=make_person(birth_time_confidence="high"),
            life_events=[make_event(confidence="high")],
        )
        result = validate_research_case(case)
        assert result.valid is True
        assert not any("confidence" in i.field for i in result.issues)
