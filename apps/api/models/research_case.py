"""
AstroOS — Research Case ORM Models (Module 27, Phase 1)

Four tables, one immutable per-snapshot guarantee, two FK relationships:

  ResearchCase — top-level container per person/subject
  LifeEvent    — one recorded life event within a research case
  EventSnapshot — one astrological timestamp within an event window
                   (v1, v2, etc.) — never overwritten
  Attachment  — linked files/documents for events

Inherits from AstroBase (UUID PK, created_at, updated_at, deleted_at).
Enum storage uses SQLAlchemy SAEnum with values_callable for
canonical lowercase backend values.
"""

from __future__ import annotations

import uuid
from datetime import date
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import AstroBase


# ── Backend enums ──────────────────────────────────────────────────────────
# Stored lowercase; frontend Pydantic schemas use TitleCase.
# values_callable ensures SQLAlchemy stores .value not .name.


class _EventType(str, Enum):
    MARRIAGE = "marriage"
    DIVORCE = "divorce"
    PROMOTION = "promotion"
    JOB_CHANGE = "job_change"
    ACCIDENT = "accident"
    SURGERY = "surgery"
    HOSPITALIZATION = "hospitalization"
    CHILD_BIRTH = "child_birth"
    DEATH_PARENT = "death_parent"
    DEATH_SPOUSE = "death_spouse"
    FOREIGN_TRAVEL = "foreign_travel"
    EDUCATION = "education"
    PROPERTY = "property"
    VEHICLE = "vehicle"
    FINANCE = "finance"
    BUSINESS = "business"
    POLITICAL = "political"
    SPIRITUAL = "spiritual"
    AWARDS = "awards"
    LITIGATION = "litigation"
    HEALTH = "health"
    OTHER = "other"


class _Severity(str, Enum):
    MAJOR = "major"
    MODERATE = "moderate"
    MINOR = "minor"


class _VerificationStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    CONFLICTING = "conflicting"


class _SourceConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class _BirthTimeConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class _Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class _AttachmentType(str, Enum):
    CERTIFICATE = "certificate"
    IMAGE = "image"
    PDF = "pdf"
    NOTES = "notes"
    OTHER = "other"


# ── ORM Models ──────────────────────────────────────────────────────────────


class ResearchCaseModel(AstroBase):
    """Top-level container for one research subject's birth data and events."""

    __tablename__ = "research_cases"

    # ── Identity ────────────────────────────────────────────────────────────
    research_case_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="Human-readable ID, e.g. RC-2024-001",
    )

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Owner / researcher; nullable for anonymised cases.",
    )

    # ── Person ──────────────────────────────────────────────────────────────
    person_name: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True
    )
    gender: Mapped[str] = mapped_column(
        SAEnum(
            _Gender,
            name="research_gender",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        server_default="other",
    )
    dob: Mapped[date] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        comment="Date of birth (calendar date).",
    )
    tob: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, comment="Time of birth HH:MM 24h."
    )
    place_of_birth: Mapped[str] = mapped_column(
        String(300), nullable=False
    )
    country: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="Free-text country/region; null for cases imported before this field existed.",
    )
    latitude: Mapped[float] = mapped_column(
        Float, nullable=False, comment="WGS-84 latitude in degrees."
    )
    longitude: Mapped[float] = mapped_column(
        Float, nullable=False, comment="WGS-84 longitude in degrees."
    )
    timezone: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="IANA timezone name."
    )
    data_source: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Source label: interview, certificate, etc."
    )
    birth_time_confidence: Mapped[str] = mapped_column(
        SAEnum(
            _BirthTimeConfidence,
            name="research_birth_time_confidence",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        server_default="medium",
    )

    # ── Birth chart config ───────────────────────────────────────────────────
    ayanamsa: Mapped[str] = mapped_column(
        String(50), default="lahiri", nullable=False
    )
    house_system: Mapped[str] = mapped_column(
        String(50), default="P", nullable=False
    )
    divisional_charts: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="JSON array of selected vargas, e.g. [\\\"D1\\\", \\\"D9\\\"]."
    )
    rectified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    rectification_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    # ── Research metadata ───────────────────────────────────────────────────
    research_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    source_batch: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="Import batch identifier."
    )
    duplicate_of_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_cases.id", ondelete="SET NULL"),
        nullable=True, comment="If this case is a detected duplicate, points to canonical."
    )
    validation_status: Mapped[str] = mapped_column(
        String(20), default="passed", nullable=False
    )
    import_job_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )

    # ── Relationships ──────────────────────────────────────────────────────
    life_events: Mapped[list["LifeEventModel"]] = relationship(
        back_populates="research_case", cascade="all, delete-orphan", lazy="selectin"
    )
    attachments: Mapped[list["AttachmentModel"]] = relationship(
        back_populates="research_case", cascade="all, delete-orphan", lazy="selectin"
    )


class LifeEventModel(AstroBase):
    """One recorded life event within a research case window."""

    __tablename__ = "life_events"

    research_case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    external_event_id: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Client-provided event ID."
    )

    # ── Classification ─────────────────────────────────────────────────────
    event_type: Mapped[str] = mapped_column(
        SAEnum(
            _EventType,
            name="life_event_type",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        index=True,
    )
    severity: Mapped[str] = mapped_column(
        SAEnum(
            _Severity,
            name="life_event_severity",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        server_default="moderate",
    )
    category: Mapped[str] = mapped_column(
        String(100), default="Other", nullable=False
    )
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("event_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment=(
            "Optional FK to the leaf node in event_categories (the "
            "hierarchical category tree). Nullable so existing rows and "
            "any import that only supplies the plain-text `category` "
            "field keep working unchanged. When set, `category` is kept "
            "in sync with the node's resolved path for backward-compat "
            "string reads."
        ),
    )
    event_type_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("event_types.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment=(
            "Optional FK to the leaf node in event_types (the open, "
            "hierarchical event-type tree that replaces the closed "
            "`event_type` enum for the manual-entry/import path). When "
            "set, `event_type_label` mirrors the node's resolved path "
            "and the legacy `event_type` enum column is set to 'other'."
        ),
    )
    event_type_label: Mapped[str] = mapped_column(
        String(100), default="Other", nullable=False
    )
    verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    confidence: Mapped[str] = mapped_column(
        SAEnum(
            _SourceConfidence,
            name="life_event_confidence",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        server_default="medium",
    )
    source: Mapped[str] = mapped_column(
        String(100), default="self-report", nullable=False,
        comment="Where the event data came from.",
    )

    # ── Date / time / place ─────────────────────────────────────────────────
    event_date: Mapped[date] = mapped_column(
        DateTime(timezone=False),  # FastAPI accepts date from ISO-8601
        nullable=False,
        index=True,
    )
    event_time: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, comment="HH:MM 24h or null."
    )
    event_place: Mapped[Optional[str]] = mapped_column(
        String(300), nullable=True
    )

    # ── Window ──────────────────────────────────────────────────────────────
    event_window_days: Mapped[int] = mapped_column(
        nullable=False, default=30,
        comment="±N days defining the event window for snapshot computation."
    )

    # ── Descriptive ─────────────────────────────────────────────────────────
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    tags: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="JSON array of tags."
    )

    # ── Relationships ──────────────────────────────────────────────────────
    research_case: Mapped["ResearchCaseModel"] = relationship(
        back_populates="life_events"
    )
    snapshots: Mapped[list["EventSnapshotModel"]] = relationship(
        back_populates="life_event", cascade="all, delete-orphan", lazy="selectin"
    )


class EventSnapshotModel(AstroBase):
    """One immutable astrological snapshot at a date within an event window.

    Versioned — never overwritten. If calculation logic improves,
    new versions are appended; old versions are retained for audit.
    """

    __tablename__ = "event_snapshots"

    life_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("life_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    snapshot_date: Mapped[date] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        comment="The calendar date for this snapshot.",
    )
    snapshot_version: Mapped[str] = mapped_column(
        String(20), default="1.0", nullable=False,
        comment="Algorithm version producing this snapshot, e.g. 1.0, 2.0."
    )

    # ── Dasha ──────────────────────────────────────────────────────────────
    mahadasha: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )
    antardasha: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )
    pratyantar: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )

    # ── Transit features (JSON blob — flexible schema) ─────────────────────
    transit_features: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="JSON dict: {\\\"Ju_7th_aspect\\\": true, \\\"Ve_retrograde\\\": false}"
    )

    # ── Shadbala (JSON blob — per-graha ≤ 60 rupa values) ──────────────────
    shadbala_values: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="JSON dict: {\\\"Ve\\\": 85.3, \\\"Ju\\\": 72.1, \\\"Sa\\\": 91.5}"
    )

    # ── Yoga / varga / nakshatra (JSON lists) ──────────────────────────────
    active_yogas: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="JSON list of yoga names."
    )
    varga_activations: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="JSON dict: {\\\"D9_Venus\\\": \\\"strong\\\", \\\"D10_Saturn\\\": \\\"strong\\\"}"
    )
    nakshatra_activations: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="JSON list of nakshatra names."
    )
    house_lord_statuses: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="JSON dict: {\\\"7L\\\": \\\"strong\\\", \\\"10L\\\": \\\"activated\\\"}"
    )
    facts_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="JSON list of Fact dicts: [{\\\"key\\\": \\\"...\\\", \\\"value\\\": ..., \\\"source\\\": \\\"...\\\"}]"
    )

    # ── Relationships ──────────────────────────────────────────────────────
    life_event: Mapped["LifeEventModel"] = relationship(
        back_populates="snapshots"
    )


class AttachmentModel(AstroBase):
    """A file/documents associated with a research case or event.

    For simplicity in v1, attachments can belong to either a ResearchCase
    (research documents, consent forms) or a LifeEvent (certificates,
    medical reports).
    """

    __tablename__ = "attachments"

    # ── Ownership ──────────────────────────────────────────────────────────
    research_case_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_cases.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    life_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("life_events.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    attachment_type: Mapped[str] = mapped_column(
        SAEnum(
            _AttachmentType,
            name="attachment_type",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        server_default="notes",
    )
    filename: Mapped[str] = mapped_column(
        String(300), nullable=False, comment="Original filename."
    )
    url: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True,
        comment="Resolved URL or local storage path."
    )
    content_type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    file_size_bytes: Mapped[Optional[int]] = mapped_column(
        nullable=True, comment="Size in bytes."
    )

    # ── Relationships ──────────────────────────────────────────────────────
    research_case: Mapped[Optional["ResearchCaseModel"]] = relationship(
        back_populates="attachments"
    )
