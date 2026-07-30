"""
AstroOS — Digital Twin Domain Model

Frozen dataclasses representing the core Digital Twin domain.
These objects are passed between service layer functions.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Tuple

from apps.api.domain.horoscope import D1Chart


@dataclass(frozen=True)
class TwinModification:
    """An individual modification to a chart within a twin."""
    id: uuid.UUID
    modification_type: str
    target_id: str
    old_value: Any = None
    new_value: Any = None
    reason: str | None = None
    created_at: datetime | None = None


@dataclass(frozen=True)
class DigitalTwin:
    """Aggregate root for a digital twin scenario."""
    id: uuid.UUID
    user_id: uuid.UUID
    original_chart_id: uuid.UUID
    name: str
    description: str | None = None
    modifications: Tuple[TwinModification, ...] = field(default_factory=tuple)
    status: str = "active"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    version: int = 1

    def latest_version(self) -> "DigitalTwin":
        """Return self, allowing future immutable versioning logic."""
        return self


@dataclass(frozen=True)
class FieldDiff:
    """A single field-level difference between two charts."""
    field_path: str
    label: str
    old_value: Any
    new_value: Any
    delta: float | None = None
    significance: str = "low"


@dataclass(frozen=True)
class TwinComparison:
    """Full comparison result between original and twin chart."""
    twin_id: uuid.UUID
    original_chart_id: uuid.UUID
    total_modifications: int
    field_diffs: Tuple[FieldDiff, ...] = field(default_factory=tuple)
    metrics_before: dict[str, Any] | None = None
    metrics_after: dict[str, Any] | None = None
    summary: str | None = None


@dataclass(frozen=True)
class TwinOperation:
    """A single simulation operation."""
    operation_type: str
    params: dict[str, Any] = field(default_factory=dict)
    duration_steps: int = 1


@dataclass(frozen=True)
class TwinOperationResult:
    """Result of applying a single simulation operation."""
    operation_type: str
    success: bool
    changes: tuple[FieldDiff, ...] = field(default_factory=tuple)
    error: str | None = None
