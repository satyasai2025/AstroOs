"""
AstroOS — Research Case Schemas (Phase II.5)

Pydantic request/response models for the Research Case Import, Feature
Extraction, and Pattern Discovery systems — the event-centric data
pipeline described in apps/api/domain/research_case.py.

Converts to/from the domain objects in the router layer only; schemas
never leak into ImportService or PatternDiscoveryService, same DTO-boundary
discipline as apps/api/schemas/events.py.

Event types follow the KP Master classification (20+ categories).
Event windows enable ±N day analysis instead of single-date snapshots.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from apps.api.domain.research_case import (
    Attachment as AttachmentDomain,
    DashaSnapshot,
    EventSnapshot as EventSnapshotDomain,
    LifeEvent as LifeEventDomain,
    PersonInfo,
    ResearchCase as ResearchCaseDomain,
)


# ── Enums ──────────────────────────────────────────────────────────────────


class EventType(str, Enum):
    MARRIAGE = "Marriage"
    DIVORCE = "Divorce"
    PROMOTION = "Promotion"
    JOB_CHANGE = "Job Change"
    ACCIDENT = "Accident"
    SURGERY = "Surgery"
    HOSPITALIZATION = "Hospitalization"
    CHILD_BIRTH = "Child Birth"
    DEATH_PARENT = "Death of Parent"
    DEATH_SPOUSE = "Death of Spouse"
    FOREIGN_TRAVEL = "Foreign Travel"
    EDUCATION = "Education"
    PROPERTY = "Property"
    VEHICLE = "Vehicle"
    FINANCE = "Finance"
    BUSINESS = "Business"
    POLITICAL = "Political"
    SPIRITUAL = "Spiritual"
    AWARDS = "Awards"
    LITIGATION = "Litigation"
    HEALTH = "Health"
    OTHER = "Other"


class Severity(str, Enum):
    MAJOR = "Major"
    MODERATE = "Moderate"
    MINOR = "Minor"


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    CONFLICTING = "conflicting"


class SourceConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BirthTimeConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


# Maps schema EventType values (TitleCase, e.g. "Job Change") to the canonical
# lowercase backend enum values stored in the ORM (e.g. "job_change").
EVENT_TYPE_TO_BACKEND = {
    EventType.MARRIAGE.value: "marriage",
    EventType.DIVORCE.value: "divorce",
    EventType.PROMOTION.value: "promotion",
    EventType.JOB_CHANGE.value: "job_change",
    EventType.ACCIDENT.value: "accident",
    EventType.SURGERY.value: "surgery",
    EventType.HOSPITALIZATION.value: "hospitalization",
    EventType.CHILD_BIRTH.value: "child_birth",
    EventType.DEATH_PARENT.value: "death_parent",
    EventType.DEATH_SPOUSE.value: "death_spouse",
    EventType.FOREIGN_TRAVEL.value: "foreign_travel",
    EventType.EDUCATION.value: "education",
    EventType.PROPERTY.value: "property",
    EventType.VEHICLE.value: "vehicle",
    EventType.FINANCE.value: "finance",
    EventType.BUSINESS.value: "business",
    EventType.POLITICAL.value: "political",
    EventType.SPIRITUAL.value: "spiritual",
    EventType.AWARDS.value: "awards",
    EventType.LITIGATION.value: "litigation",
    EventType.HEALTH.value: "health",
    EventType.OTHER.value: "other",
}


# ── Person Information ─────────────────────────────────────────────────────


class PersonInfoSchema(BaseModel):
    """Birth and identity data for the research subject."""
    name: Optional[str] = Field(default=None, max_length=200)
    gender: Gender
    dob: date = Field(description="Date of birth")
    tob: Optional[str] = Field(default=None, description="Time of birth (HH:MM)")
    place: str = Field(max_length=300, description="Place of birth")
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timezone: str = Field(max_length=100, description="IANA timezone, e.g. Asia/Kolkata")
    source: str = Field(max_length=100, description="Interview, Certificate, Self-report, etc.")
    birth_time_confidence: BirthTimeConfidence = BirthTimeConfidence.MEDIUM
    country: Optional[str] = Field(
        default=None, max_length=100,
        description="Free-text country/region — optional, enables the dashboard's Country filter.",
    )

    def to_domain(self) -> PersonInfo:
        return PersonInfo(
            name=self.name,
            gender=self.gender.value.lower(),
            dob=self.dob,
            tob=self.tob,
            place=self.place,
            latitude=self.latitude,
            longitude=self.longitude,
            timezone=self.timezone,
            source=self.source,
            birth_time_confidence=self.birth_time_confidence.value,
            country=self.country,
        )


# ── Snapshot ────────────────────────────────────────────────────────────────


class DashaSnapshotSchema(BaseModel):
    """Dasha state at a point in time."""
    mahadasha: str = Field(max_length=10)
    antardasha: str = Field(max_length=10)
    pratyantar: Optional[str] = Field(default=None, max_length=10)

    def to_domain(self) -> DashaSnapshot:
        return DashaSnapshot(
            mahadasha=self.mahadasha,
            antardasha=self.antardasha,
            pratyantar=self.pratyantar,
        )


class TransitSnapshotSchema(BaseModel):
    """Normalised transit features — one per snapshot."""
    features: dict[str, bool] = Field(
        default_factory=dict,
        description="Key-value transit features, e.g. {\\\"Ju_7th_aspect\\\": true}",
    )


class ShadbalaSnapshotSchema(BaseModel):
    """Shadbala values at the snapshot moment."""
    values: dict[str, float] = Field(
        default_factory=dict,
        description="Graha -> rupa value, e.g. {\\\"Ve\\\": 85.0, \\\"Ju\\\": 72.0}",
    )


class EventSnapshotSchema(BaseModel):
    """One astrological snapshot at a specific moment within an event window."""
    snapshot_date: date
    snapshot_version: str = Field(default="1.0", max_length=20)
    current_dasha: Optional[DashaSnapshotSchema] = None
    transits: Optional[dict[str, bool]] = None
    shadbala: Optional[dict[str, float]] = None
    active_yogas: list[str] = Field(default_factory=list)
    varga_activations: dict[str, str] = Field(default_factory=dict)
    nakshatra_activations: list[str] = Field(default_factory=list)
    house_lord_statuses: dict[str, str] = Field(default_factory=dict)

    def to_domain(self) -> EventSnapshotDomain:
        return EventSnapshotDomain(
            snapshot_date=self.snapshot_date,
            snapshot_version=self.snapshot_version,
            current_dasha=self.current_dasha.to_domain() if self.current_dasha else None,
            transits=dict(self.transits or {}),
            shadbala=dict(self.shabdala or {}),
            active_yogas=list(self.active_yogas),
            varga_activations=dict(self.varga_activations),
            nakshatra_activations=list(self.nakshatra_activations),
            house_lord_statuses=dict(self.house_lord_statuses),
        )


# ── Attachment ──────────────────────────────────────────────────────────────


class AttachmentSchema(BaseModel):
    """A file attached to a life event."""
    type: str = Field(default="notes", max_length=50)
    filename: str = Field(max_length=300)
    url: Optional[str] = Field(default=None, max_length=1000)
    content_type: Optional[str] = Field(default=None, max_length=100)

    def to_domain(self) -> AttachmentDomain:
        return AttachmentDomain(
            type=self.type,
            filename=self.filename,
            url=self.url,
            content_type=self.content_type,
        )


# ── Life Event ──────────────────────────────────────────────────────────────


class LifeEventCreateSchema(BaseModel):
    """One recorded life event for a research case."""
    id: Optional[str] = Field(default=None, max_length=50)
    type: Optional[EventType] = Field(
        default=None,
        description=(
            "Legacy closed 22-value event type. Optional now that "
            "event_type_path (the open Event Tree) exists — kept for "
            "backward-compat JSON-upload payloads and the "
            "pattern-discovery/assistant endpoints that still key off it. "
            "Falls back to 'Other' when neither this nor event_type_path "
            "is supplied."
        ),
    )
    event_date: date
    event_time: Optional[str] = Field(default=None, description="HH:MM")
    event_place: Optional[str] = Field(default=None, max_length=300)
    severity: Severity = Severity.MODERATE
    category: str = Field(default="Other", max_length=100)
    category_path: Optional[list[str]] = Field(
        default=None,
        max_length=6,
        description=(
            "Optional hierarchical category path, e.g. [\"Notable\", \"Famous\", "
            "\"Royal family\"], up to 6 levels deep. When supplied, resolves "
            "to a node in the event_categories tree (auto-creating any "
            "missing segment) and the resolved path overwrites `category` "
            "for backward-compat string reads. Open vocabulary — unlike "
            "`type`, unrecognized paths are created, not rejected."
        ),
    )
    event_type_path: Optional[list[str]] = Field(
        default=None,
        max_length=6,
        description=(
            "Optional hierarchical event-type path, e.g. [\"Relationship\", "
            "\"Marriage\", \"Love marriage\"], up to 6 levels deep. Mirrors "
            "category_path but resolves against the open event_types tree "
            "instead of the closed `type` enum — replaces `type` for the "
            "manual-entry/import path. When supplied, the legacy `type` "
            "enum column is stored as 'other'."
        ),
    )
    verified: bool = False
    confidence: SourceConfidence = SourceConfidence.MEDIUM
    source: str = Field(default="self-report", max_length=100)
    description: Optional[str] = Field(default=None, max_length=2000)
    tags: list[str] = Field(default_factory=list)
    event_window_days: int = Field(default=30, ge=0, le=365)
    notes: Optional[str] = Field(default=None, max_length=5000)
    snapshots: list[EventSnapshotSchema] = Field(default_factory=list)
    attachments: list[AttachmentSchema] = Field(default_factory=list)

    def to_domain(self) -> LifeEventDomain:
        return LifeEventDomain(
            id=self.id,
            type=EVENT_TYPE_TO_BACKEND[self.type.value] if self.type else "other",
            event_date=self.event_date,
            event_time=self.event_time,
            event_place=self.event_place,
            severity=self.severity.value.lower(),
            category=self.category,
            category_path=list(self.category_path) if self.category_path else None,
            event_type_path=list(self.event_type_path) if self.event_type_path else None,
            verified=self.verified,
            confidence=self.confidence.value,
            source=self.source,
            description=self.description,
            tags=list(self.tags),
            event_window_days=self.event_window_days,
            notes=self.notes,
            snapshots=[s.to_domain() for s in self.snapshots],
            attachments=[a.to_domain() for a in self.attachments],
        )


# ── Research Case ───────────────────────────────────────────────────────────


class ResearchCaseCreateSchema(BaseModel):
    """Top-level import payload — one research case = one person + events."""
    id: Optional[str] = Field(default=None, max_length=50)
    person: PersonInfoSchema
    ayanamsa: str = Field(default="lahiri", max_length=50)
    house_system: str = Field(default="P", max_length=50)
    divisional_charts: list[str] = Field(default_factory=lambda: ["D1", "D9", "D10", "D60"])
    rectified: bool = False
    rectification_notes: Optional[str] = Field(default=None, max_length=2000)
    life_events: list[LifeEventCreateSchema] = Field(min_length=1)
    research_notes: Optional[str] = Field(default=None, max_length=10000)
    attachments: list[AttachmentSchema] = Field(default_factory=list)
    source_batch: Optional[str] = Field(default=None, max_length=200)

    def to_domain(self) -> ResearchCaseDomain:
        return ResearchCaseDomain(
            id=self.id,
            person=self.person.to_domain(),
            ayanamsa=self.ayanamsa,
            house_system=self.house_system,
            divisional_charts=list(self.divisional_charts),
            rectified=self.rectified,
            rectification_notes=self.rectification_notes,
            life_events=[e.to_domain() for e in self.life_events],
            research_notes=self.research_notes,
            attachments=[a.to_domain() for a in self.attachments],
            source_batch=self.source_batch,
        )


# ── Import (batch wrapper) ─────────────────────────────────────────────────


class ResearchCaseBatchImportSchema(BaseModel):
    """Batch import — wraps multiple cases in one request."""
    cases: list[ResearchCaseCreateSchema] = Field(min_length=1, max_length=1000)
    generate_ids: bool = True
    update_existing: bool = Field(
        default=False,
        description=(
            "When true, a case matching an already-persisted one by "
            "person name + dob + tob is updated (new life_events "
            "appended) instead of being rejected as a duplicate."
        ),
    )


# ── Responses ───────────────────────────────────────────────────────────────


class ResearchCaseImportResultSchema(BaseModel):
    """Result of importing one case."""
    research_case_id: str
    person_name: Optional[str]
    dob: date
    total_events: int
    total_snapshots_created: int
    duplicate: bool = False
    errors: list[str] = Field(default_factory=list)


class ResearchCaseImportResponseSchema(BaseModel):
    """
    Returned after importing research cases. Reports per-case results
    and overall counts.
    """
    total_cases: int
    succeeded: int
    failed: int
    results: list[ResearchCaseImportResultSchema]


class ImportJobResponseSchema(BaseModel):
    """Status of an async import job."""
    job_id: str
    status: str  # pending, running, completed, failed
    total_cases: int = 0
    processed: int = 0
    errors: list[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ResearchCaseSummarySchema(BaseModel):
    """Lightweight list entry for one research case."""
    research_case_id: str
    person_name: Optional[str]
    dob: date
    gender: Optional[str] = None
    total_events: int = 0
    validation_status: str = "passed"
    duplicate_of_id: Optional[uuid.UUID] = None
    created_at: Optional[datetime] = None


class ResearchCaseListResponseSchema(BaseModel):
    """Paginated-ish summary list of research cases."""
    total: int
    cases: list[ResearchCaseSummarySchema]


class QueryConditionSchema(BaseModel):
    """One AND-combined condition against the real Fact vocabulary, e.g.
    field="planet.saturn.retrograde", operator="equals", value="true"."""
    field: str = Field(min_length=1, max_length=200)
    operator: Literal["equals", "not_equals", "contains"] = "equals"
    value: str = Field(max_length=200)


class ResearchQueryRequestSchema(BaseModel):
    conditions: list[QueryConditionSchema] = Field(min_length=1, max_length=20)


class ResearchQueryResponseSchema(BaseModel):
    total_scanned: int
    total_matched: int
    matches: list[ResearchCaseSummarySchema]


class LifeEventSnapshotSchema(BaseModel):
    """The astrological positions captured for one life event — the
    "Chart/Astrological positions" shown on the event timeline's detail
    panel. None when no snapshot has been computed for this event yet."""
    mahadasha: Optional[str] = None
    antardasha: Optional[str] = None
    pratyantar: Optional[str] = None
    active_yogas: list[str] = Field(default_factory=list)
    transit_features: dict[str, bool] = Field(default_factory=dict)
    house_lord_statuses: dict[str, str] = Field(default_factory=dict)
    nakshatra_activations: list[str] = Field(default_factory=list)
    snapshot_version: str


class LifeEventDetailSchema(BaseModel):
    """One life event with its full descriptive + astrological detail,
    for the event timeline view."""
    id: uuid.UUID
    event_type: EventType
    event_type_label: str = "Other"
    event_date: date
    event_time: Optional[str] = None
    event_place: Optional[str] = None
    category: str
    severity: str
    description: Optional[str] = None
    notes: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    snapshot: Optional[LifeEventSnapshotSchema] = None


class ResearchCaseDetailSchema(BaseModel):
    """One research case with its full life-event timeline — powers the
    interactive event chart's node data + detail side panel."""
    research_case_id: str
    person_name: Optional[str]
    dob: date
    gender: Optional[str] = None
    life_events: list[LifeEventDetailSchema]


# ── Validation result ──────────────────────────────────────────────────────


class ValidationIssueSchema(BaseModel):
    """One issue found during validation."""
    field: str
    message: str
    severity: str = "warning"  # error | warning | info


class ResearchCaseValidationSchema(BaseModel):
    """Full validation result for a research case."""
    valid: bool
    research_case_id: Optional[str] = None
    person_dob: Optional[date] = None
    issues: list[ValidationIssueSchema] = Field(default_factory=list)
    duplicate_case: bool = False
    duplicate_events: list[str] = Field(default_factory=list)


class ResearchCaseBatchValidationSchema(BaseModel):
    """Validation results for a batch import."""
    validations: list[ResearchCaseValidationSchema]
    total_valid: int
    total_invalid: int


# ── Feature extraction ─────────────────────────────────────────────────────


class ExtractedFeatureSchema(BaseModel):
    """One normalised feature extracted from an event snapshot."""
    feature_name: str
    feature_value: str | float | bool
    feature_category: str  # yoga, dasha, transit, shadbala, house, nakshatra, varga
    event_type: EventType
    research_case_id: str
    event_date: date
    confidence: float = Field(default=1.0, ge=0, le=1)


class FeatureExtractionResponseSchema(BaseModel):
    """Response after extracting features across all snapshots."""
    total_features: int
    features_by_category: dict[str, int]
    features: list[ExtractedFeatureSchema]


# ── Pattern discovery ──────────────────────────────────────────────────────


class PatternDimensionSchema(BaseModel):
    """One dimension of a discovered pattern."""
    dimension: str  # mahadasha, transit_house, yoga, etc.
    value: str  # "Jupiter", "7th_house", "Gajakesari"
    frequency: float  # 0.0 - 1.0 (proportion of cases)
    count: int
    expected_by_chance: float = 0.0
    significance: float = Field(default=0.0, ge=0, le=1)


class DiscoveredPatternSchema(BaseModel):
    """One discovered pattern combination."""
    event_type: EventType
    pattern_id: str
    dimensions: list[PatternDimensionSchema]
    sample_size: int
    confidence_score: float = Field(default=0.0, ge=0, le=1)
    description: str


class PatternDiscoveryRequestSchema(BaseModel):
    """Request for pattern discovery over the extracted feature dataset."""
    event_type: Optional[EventType] = Field(
        default=None, description="Restrict discovery to one KP Master event type."
    )
    top_combos: int = Field(
        default=5, ge=1, le=25, description="Max single + combination patterns per type."
    )
    date_from: Optional[date] = Field(
        default=None, description="Only include life events on/after this date."
    )
    date_to: Optional[date] = Field(
        default=None, description="Only include life events on/before this date."
    )


class PatternExploreRequestSchema(BaseModel):
    """A researcher's personal 'what-if' pattern search: same shared
    dataset and formulas as /cases/patterns/discover, but with the
    caller's own significance/frequency/Wilson-z thresholds. Never
    persisted to discovered_patterns — it can't change what any other
    researcher sees, only what this response returns.
    """
    event_type: Optional[EventType] = Field(
        default=None, description="Restrict discovery to one KP Master event type."
    )
    min_significance: float = Field(
        default=0.90, ge=0.5, le=0.999,
        description="Significance floor for a dimension-value to be reported (shared default: 0.90).",
    )
    min_frequency: float = Field(
        default=0.10, ge=0.01, le=1.0,
        description="Minimum share of cases a dimension-value must appear in (shared default: 0.10).",
    )
    wilson_z: float = Field(
        default=1.0, ge=0.0, le=3.0,
        description="Wilson score z used to shrink small-count rates before testing (shared default: 1.0). Higher = more conservative toward small samples.",
    )
    top_combos: int = Field(
        default=5, ge=1, le=25, description="Max single + combination patterns per type."
    )
    date_from: Optional[date] = Field(
        default=None, description="Only include life events on/after this date."
    )
    date_to: Optional[date] = Field(
        default=None, description="Only include life events on/before this date."
    )


class PatternDiscoveryResponseSchema(BaseModel):
    """Pattern discovery results for one event type."""
    event_type: EventType
    total_cases: int
    total_events: int
    patterns: list[DiscoveredPatternSchema]
    execution_time_ms: int


class PatternHypothesisSchema(BaseModel):
    """Test a custom hypothesis against the snapshot database."""
    event_type: EventType
    conditions: dict[str, str] = Field(
        description="Dimension -> value filters, e.g. {\"mahadasha\": \"Ju\"}"
    )
    min_confidence: float = Field(default=0.0, ge=0, le=1)


class PatternHypothesisResponseSchema(BaseModel):
    """Results of testing a custom hypothesis."""
    event_type: EventType
    hypothesis: dict[str, str]
    matching_cases: int
    total_cases: int
    proportion: float
    confidence_score: float
    supporting_events: list[dict[str, Any]] = Field(default_factory=list)


# ── Pattern Discovery Dashboard (Module 27, Phase 3c) ──────────────────────
# Reads over the persisted discovered_patterns / pattern_discovery_runs
# tables — none of these trigger recomputation. See
# apps/api/services/pattern_persistence.py.


class PatternSummarySchema(BaseModel):
    """KPI row for the /research/patterns dashboard."""
    total_cases: int
    total_events: int
    total_snapshots: int
    patterns_found: int
    high_confidence_patterns: int
    knowledge_records: int = Field(
        description="Count of persisted patterns with a generated AI explanation."
    )


class PatternListItemSchema(BaseModel):
    """One row in the Top Patterns table."""
    pattern_id: str
    event_type: EventType
    description: str
    sample_size: int
    confidence_score: float = Field(ge=0, le=1)
    lift_score: float
    has_explanation: bool
    dimension_count: int = Field(description="Number of dimensions in this pattern (2+ = a combination pattern).")
    categories: list[str] = Field(
        default_factory=list,
        description="Deduplicated dimension categories present (dasha, yoga, house, transit, shadbala, varga, nakshatra, other).",
    )
    discovered_at: Optional[datetime] = None


class PatternListResponseSchema(BaseModel):
    total: int
    patterns: list[PatternListItemSchema]


class PatternQuestionRequestSchema(BaseModel):
    """A plain-language question about the shared, already-discovered
    patterns — e.g. "what correlates with Marriage?"."""
    question: str = Field(min_length=1, max_length=500)


class PatternQuestionResponseSchema(BaseModel):
    """Grounded answer: the event type the question was matched to (if
    any), the real patterns that answer drew from, and the generated
    natural-language summary. Read-only — nothing is persisted or
    recomputed; it only queries the already-discovered shared patterns.
    """
    question: str
    matched_event_type: Optional[EventType] = None
    answer: str
    patterns: list[PatternListItemSchema]
    execution_time_ms: int


class PatternDetailSchema(BaseModel):
    """Strictly read-only — never triggers an AI explanation call."""
    pattern_id: str
    event_type: EventType
    description: str
    dimensions: list[PatternDimensionSchema]
    sample_size: int
    confidence_score: float = Field(ge=0, le=1)
    lift_score: float
    supporting_case_ids: list[str] = Field(default_factory=list)
    contradicting_case_ids: list[str] = Field(default_factory=list)
    algorithm_version: str
    feature_version: str
    snapshot_versions: list[str] = Field(default_factory=list)
    explanation: Optional[str] = None
    explanation_generated_at: Optional[datetime] = None
    classical_references: list[str] = Field(default_factory=list)
    discovered_at: Optional[datetime] = None


class PatternExplainResponseSchema(BaseModel):
    """Returned only by POST .../explain — the sole path that calls the LLM."""
    pattern_id: str
    explanation: str
    explanation_generated_at: datetime


class PatternExplainAllResponseSchema(BaseModel):
    """Bulk AI Explanation Regeneration result (Advanced Research)."""
    total_patterns: int
    succeeded: int
    failed: int
    errors: list[str] = Field(default_factory=list)


class TopFactorSchema(BaseModel):
    value: str
    count: int


class TopFactorsResponseSchema(BaseModel):
    category: str
    factors: list[TopFactorSchema]


class ConfidenceBucketSchema(BaseModel):
    bucket: str  # "0-20", "20-40", "40-60", "60-80", "80-100"
    count: int


class ConfidenceDistributionResponseSchema(BaseModel):
    buckets: list[ConfidenceBucketSchema]


class PatternGraphNodeSchema(BaseModel):
    id: str
    label: str
    x: float
    y: float
    size: float
    category: str


class PatternGraphEdgeSchema(BaseModel):
    from_: str = Field(alias="from")
    to: str

    model_config = {"populate_by_name": True}


class PatternGraphResponseSchema(BaseModel):
    nodes: list[PatternGraphNodeSchema]
    edges: list[PatternGraphEdgeSchema]


class PatternTrendPointSchema(BaseModel):
    run_at: datetime
    confidence_score: float = Field(ge=0, le=1)


class PatternTrendResponseSchema(BaseModel):
    """Populates once >=2 discovery runs have touched this pattern_id;
    a single point otherwise — not hidden, just not much of a trend yet."""
    pattern_id: str
    points: list[PatternTrendPointSchema]


# ── Advanced Research tools (Module 27, Phase 3c) ──────────────────────────


class DatasetValidationReportSchema(BaseModel):
    total_cases: int
    cases_without_snapshots: list[str] = Field(default_factory=list)
    life_events_without_snapshots: int = 0
    stale_snapshot_case_ids: list[str] = Field(default_factory=list)
    duplicate_case_ids: list[str] = Field(default_factory=list)


class SnapshotRebuildResultSchema(BaseModel):
    cases_processed: int
    snapshots_created: int
    snapshot_version: str
    errors: list[str] = Field(default_factory=list)


class EvidenceRecalculationResultSchema(BaseModel):
    patterns_refreshed: int


# ── Event Category Tree (open, source-taxonomy-driven) ─────────────────────


class EventCategorySchema(BaseModel):
    """One node in the research-event category tree, nested."""
    id: str
    name: str
    level: int
    path: str
    house_number: Optional[int] = None
    karaka_planet: Optional[str] = None
    source: str
    source_doc_count: Optional[int] = None
    children: list["EventCategorySchema"] = Field(default_factory=list)


EventCategorySchema.model_rebuild()


class EventCategoryTreeResponseSchema(BaseModel):
    categories: list[EventCategorySchema]


class EventCategoryUpdateSchema(BaseModel):
    """Researcher-curation payload: attach/update Vedic metadata on an
    existing (usually auto-created) category node."""
    house_number: Optional[int] = Field(default=None, ge=1, le=12)
    karaka_planet: Optional[str] = Field(default=None, max_length=20)
    description: Optional[str] = Field(default=None, max_length=2000)


class EventTypeSchema(BaseModel):
    """One node in the research-event type tree, nested."""
    id: str
    name: str
    level: int
    path: str
    source: str
    children: list["EventTypeSchema"] = Field(default_factory=list)


EventTypeSchema.model_rebuild()


class EventTypeTreeResponseSchema(BaseModel):
    event_types: list[EventTypeSchema]


class EventTypeUpdateSchema(BaseModel):
    """Researcher-curation payload: attach/update a description on an
    existing (usually auto-created) event-type node."""
    description: Optional[str] = Field(default=None, max_length=2000)
