"""
AstroOS — Technique Intelligence: ORM Models

Persistence for the generic Technique framework. Three tables:

  techniques                 — a versioned, provenance-tracked technique. The
                               full evaluable definition (rule_refs, source
                               references, required inputs) is serialised into
                               `definition_json`; the columns hold the fields
                               the DB needs to index/filter on.
  technique_sources          — provenance lineage: which sources a technique
                               was extracted from (PDF, YouTube, book, ...).
  technique_validation_cases — research/validation records per rule per chart.

Versioning follows the soft-append convention introduced in migration 0008
(knowledge versioning): an update creates a NEW row with an incremented
`version`; the prior row is retained and its `superseded_by` points to the
replacement. A version used in a validated analysis must never be mutated —
history stays reconstructible. Composite index on (technique_key, version).

All models inherit AstroBase (UUID PK, created/updated/deleted_at).
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.models.base import AstroBase


class TechniqueModel(AstroBase):
    """One immutable version of a technique."""

    __tablename__ = "techniques"

    technique_key: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        doc="Stable slug, e.g. 'eye_health', 'marriage_timing'. Not unique — "
            "many versions share a key.",
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tradition: Mapped[str] = mapped_column(
        String(50), nullable=False, default="",
        doc="Parashari | Jaimini | Nadi | KP | ...",
    )
    objective: Mapped[str] = mapped_column(
        String(100), nullable=False, default="", index=True,
        doc="Intent key a resolver matches, e.g. 'ocular_health'.",
    )
    provenance: Mapped[str] = mapped_column(
        String(30), nullable=False, default="untested",
        doc="ProvenanceStatus value — source-derivation axis, NOT lifecycle.",
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="research",
        doc="Lifecycle: research | draft | validated | deprecated | ...",
    )
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1",
    )
    version_comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    superseded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("techniques.id", ondelete="SET NULL"),
        nullable=True,
        doc="Points to the replacing version's row, or NULL if current.",
    )
    definition_json: Mapped[str] = mapped_column(
        Text, nullable=False, default="{}",
        doc="JSON-serialised TechniqueDefinition (rule_refs, source_references, "
            "required_inputs, dependencies, unresolved_inconsistencies).",
    )

    def __repr__(self) -> str:
        return f"<Technique {self.technique_key} v{self.version} ({self.status})>"


class TechniqueSourceModel(AstroBase):
    """One source a technique was extracted from — provenance lineage."""

    __tablename__ = "technique_sources"

    technique_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("techniques.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    source_type: Mapped[str] = mapped_column(
        String(40), nullable=False, default="",
        doc="pdf | youtube | book | classical_text | research_paper | notes | user",
    )
    reference: Mapped[str] = mapped_column(
        String(500), nullable=False, default="",
        doc="Citation / URL / file reference.",
    )
    excerpt: Mapped[str | None] = mapped_column(
        Text, nullable=True, doc="The relevant source excerpt, verbatim.",
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<TechniqueSource {self.source_type} for {self.technique_id}>"


class TechniqueValidationCaseModel(AstroBase):
    """A validation/research record: one rule tested against one chart."""

    __tablename__ = "technique_validation_cases"

    technique_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("techniques.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    rule_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    chart_ref: Mapped[str | None] = mapped_column(
        String(200), nullable=True,
        doc="Reference to the chart/case tested (id or descriptor).",
    )
    expected_result: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    observed_result: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    match_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="untested",
        doc="match | mismatch | partial | untested",
    )
    evidence_json: Mapped[str] = mapped_column(
        Text, nullable=False, default="{}",
        doc="JSON-serialised triggers/evidence backing the observation.",
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<TechniqueValidationCase {self.rule_id} "
            f"{self.match_status} tech={self.technique_id}>"
        )
