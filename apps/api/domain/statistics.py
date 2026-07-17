"""
AstroOS — Statistics Domain Objects (Module 18, Phase 1)

Distributions, cross-tabulations, descriptive statistics, and aggregate
reports computed over collections of AstrologicalSnapshot objects.

Pure Python dataclasses — no ORM/Pydantic dependency.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class StatValue:
    """A single computed statistical value."""

    label: str
    value: float
    unit: str  # "count", "percent", "mean", "std_dev", "correlation"
    description: str = ""


@dataclass(frozen=True)
class Distribution:
    """Frequency distribution over a categorical or binned variable."""

    label: str
    variable: str
    bins: tuple[str, ...]
    counts: tuple[int, ...]
    total: int


@dataclass(frozen=True)
class Crosstab:
    """Contingency table for two categorical variables."""

    label: str
    row_variable: str
    column_variable: str
    row_labels: tuple[str, ...]
    column_labels: tuple[str, ...]
    cells: tuple[tuple[int, ...], ...]  # rows x columns
    row_totals: tuple[int, ...]


@dataclass(frozen=True)
class NumericSummary:
    """Descriptive statistics for a numeric variable."""

    label: str
    variable: str
    count: int
    mean: float
    std_dev: float
    min: float
    max: float
    median: float
    q1: float
    q3: float
    sum: float


@dataclass(frozen=True)
class DatasetMetadata:
    """
    Metadata describing the dataset that produced an AggregateReport.

    Contains no statistical computations — only identification,
    provenance, and sizing fields.
    """

    sample_size: int
    snapshot_count: int
    filtered_sample_size: Optional[int] = None
    experiment_id: Optional[uuid.UUID] = None
    engine_version: str = "1.0"
    generated_at: Optional[datetime] = None


@dataclass(frozen=True)
class AggregateReport:
    """A complete statistical analysis result."""

    title: str
    metadata: DatasetMetadata
    distributions: tuple[Distribution, ...] = field(default_factory=tuple)
    crosstabs: tuple[Crosstab, ...] = field(default_factory=tuple)
    numeric_summaries: tuple[NumericSummary, ...] = field(default_factory=tuple)
    stat_values: tuple[StatValue, ...] = field(default_factory=tuple)
    report_version: str = "1.0"
