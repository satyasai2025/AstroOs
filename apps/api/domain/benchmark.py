"""
AstroOS — Benchmark Domain Objects (Module 16, Phase C)

Benchmark results for validating computed charts against golden-reference
expectations (GC-MASTER dataset). Pure Python dataclasses — no ORM/Pydantic
dependency. Phase C adds house cusp and varga benchmark types.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class PlanetBenchmark:
    """One planet's computed vs expected position."""
    planet: str
    computed_longitude: float
    expected_longitude: float
    error_degrees: float
    within_tolerance: bool


@dataclass(frozen=True)
class HouseBenchmark:
    """One house cusp's computed vs expected position."""
    house_number: int
    computed_cusp: float
    expected_cusp: float
    error_degrees: float
    within_tolerance: bool


@dataclass(frozen=True)
class VargaBenchmark:
    """One planet's placement in one divisional chart."""
    varga_code: str
    planet: str
    computed_rashi: str
    expected_rashi: str
    matched: bool


@dataclass(frozen=True)
class BenchmarkResult:
    """Result of validating one chart against a GC-MASTER reference."""
    chart_id: uuid.UUID
    reference_id: str
    reference_name: str
    planets: tuple[PlanetBenchmark, ...]
    mean_error: float
    max_error: float
    passed: bool
    tolerance: float
    timestamp: datetime
    ayanamsa: str = "lahiri"
    house_system: str = "W"


@dataclass(frozen=True)
class HouseBenchmarkResult:
    """Result of validating house cusps for one house system."""
    reference_id: str
    reference_name: str
    house_system: str
    cusps: tuple[HouseBenchmark, ...]
    mean_error: float
    max_error: float
    passed: bool
    tolerance: float


@dataclass(frozen=True)
class VargaBenchmarkResult:
    """Result of validating divisional charts."""
    reference_id: str
    reference_name: str
    vargas: tuple[VargaBenchmark, ...]
    total_checks: int
    matched: int
    failed: int


@dataclass(frozen=True)
class BenchmarkSummary:
    """Aggregate benchmark results across multiple charts and families."""
    total_charts: int
    passed: int
    failed: int
    results: tuple[BenchmarkResult, ...]
    overall_mean_error: float
    house_results: tuple[HouseBenchmarkResult, ...] = ()
    varga_results: tuple[VargaBenchmarkResult, ...] = ()
    family_summary: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
