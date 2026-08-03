"""
AstroOS — Research Case Validation Service (Module 27, Phase 2)

Validates research cases before import. Per spec:
  - Birth data validation (required fields, date range, lat/lng ranges)
  - Duplicate case detection (hash on DOB + name + location)
  - Duplicate event detection (same case, same event type, same date)
  - Date/time consistency (events chronologically ordered, post-birth)
  - Source confidence propagation (person-level → event-level)

Runs synchronously per case; batch validation iterates cases.
No side effects — pure validation, no DB writes.
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime
from typing import Optional

from apps.api.schemas.research_case import (
    EventType,
    LifeEventCreateSchema,
    ResearchCaseCreateSchema,
    ResearchCaseValidationSchema,
    ResearchCaseBatchValidationSchema,
    SourceConfidence,
    ValidationIssueSchema,
)


def _hash_case(person_name: str, dob: date, latitude: float, longitude: float) -> str:
    """Deterministic hash for duplicate detection."""
    payload = f"{person_name}|{dob.isoformat()}|{latitude:.4f}|{longitude:.4f}"
    return hashlib.sha256(payload.encode()).hexdigest()[:20]


def _valid_dob(dob: date) -> bool:
    """Birth date must be in the past and after 1500 CE (modern records)."""
    today = date.today()
    return dob < today and dob.year >= 1500


def _valid_geo(lat: float, lon: float) -> bool:
    """Latitude and longitude must be non-zero and within valid ranges."""
    return -90 <= lat <= 90 and -180 <= lon <= 180 and not (lat == 0 and lon == 0)


def validate_research_case(
    case: ResearchCaseCreateSchema,
    existing_hashes: Optional[set[str]] = None,
) -> ResearchCaseValidationSchema:
    """Validate one research case. Returns a detailed validation result."""

    issues: list[ValidationIssueSchema] = []
    seen_hashes = existing_hashes if existing_hashes is not None else set()

    # ── Person validation ──────────────────────────────────────────────────
    person = case.person

    if not person.dob:
        issues.append(_issue("person.dob", "Date of birth is required", "error"))
    elif not _valid_dob(person.dob):
        issues.append(
            _issue(
                "person.dob",
                f"Date of birth {person.dob} is out of valid range (1500–today).",
                "error",
            )
        )

    if not _valid_geo(person.latitude, person.longitude):
        issues.append(
            _issue(
                "person.latitude/longitude",
                f"Coordinates ({person.latitude}, {person.longitude}) are invalid.",
                "error",
            )
        )

    if not person.place:
        issues.append(_issue("person.place", "Place of birth is required.", "error"))

    if not person.timezone:
        issues.append(_issue("person.timezone", "Timezone is required.", "error"))

    # ── Duplicate case hash ────────────────────────────────────────────────
    case_hash = _hash_case(
        person.name or "anonymous", person.dob, person.latitude, person.longitude
    )
    duplicate_case = case_hash in seen_hashes
    if duplicate_case:
        issues.append(
            _issue(
                "case",
                f"Duplicate case detected ({case_hash}); possible re-import.",
                "error",
            )
        )
    seen_hashes.add(case_hash)

    # ── Source confidence propagation ──────────────────────────────────────
    person_birth_confidence = person.birth_time_confidence.value

    # ── Event validation ───────────────────────────────────────────────────
    duplicate_events: list[str] = []
    seen_event_keys: set[str] = set()
    sorted_events = sorted(case.life_events, key=lambda e: e.event_date)

    if len(sorted_events) == 0:
        issues.append(_issue("life_events", "At least one life event is required.", "error"))

    for i, event in enumerate(case.life_events, start=1):
        prefix = f"life_events[{i - 1}]"

        # Date/Time consistency
        if event.event_date < person.dob:
            issues.append(
                _issue(
                    f"{prefix}.event_date",
                    f"Event date {event.event_date} precedes birth date {person.dob}.",
                    "error",
                )
            )

        if event.event_date > date.today():
            issues.append(
                _issue(
                    f"{prefix}.event_date",
                    f"Event date {event.event_date} is in the future.",
                    "error",
                )
            )

        if event.event_window_days < 0 or event.event_window_days > 365:
            issues.append(
                _issue(
                    f"{prefix}.event_window",
                    f"Event window {event.event_window_days} must be 0–365 days.",
                    "error",
                )
            )

        # Duplicate event detection within same case
        ek = _make_event_key(event.type, event.event_date)
        if ek in seen_event_keys:
            duplicate_events.append(ek)
            issues.append(
                _issue(
                    f"{prefix}",
                    f"Duplicate event: type={event.type.value}, date={event.event_date} already seen in this case.",
                    "warning",
                )
            )
        seen_event_keys.add(ek)

        # Confidence derived from person source
        if event.confidence == SourceConfidence.HIGH:
            if person_birth_confidence != "high":
                issues.append(
                    _issue(
                        f"{prefix}.confidence",
                        f"Event confidence is high but person birth time confidence is {person_birth_confidence}.",
                        "warning",
                    )
                )

    # ── Overall validity ───────────────────────────────────────────────────
    valid = not any(iss.severity == "error" for iss in issues)
    return ResearchCaseValidationSchema(
        valid=valid,
        research_case_id=case.id,
        person_dob=person.dob,
        issues=issues,
        duplicate_case=duplicate_case,
        duplicate_events=duplicate_events,
    )


def validate_research_case_batch(
    cases: list[ResearchCaseCreateSchema],
) -> ResearchCaseBatchValidationSchema:
    """Validate a batch of cases; duplicate detection cross-cases."""
    seen_hashes: set[str] = set()
    validations = []
    for case in cases:
        val = validate_research_case(case, existing_hashes=seen_hashes)
        validations.append(val)
    total_valid = sum(1 for v in validations if v.valid)
    return ResearchCaseBatchValidationSchema(
        validations=validations,
        total_valid=total_valid,
        total_invalid=len(validations) - total_valid,
    )


def _make_event_key(event_type: EventType, event_date: date) -> str:
    return f"{event_type.value}:{event_date.isoformat()}"


def _issue(field: str, message: str, severity: str) -> ValidationIssueSchema:
    return ValidationIssueSchema(field=field, message=message, severity=severity)