"""
AstroOS — Statistics Engine (Module 18, Phase 1)

Computes distributions, descriptive statistics, and contingency tables
over collections of AstrologicalSnapshot objects.

Takes already-captured snapshots — never calls any astrology engine or
the Research Engine itself. Same "compute once, reuse" discipline.
"""

from __future__ import annotations

import math
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from statistics import median as _median, stdev as _stdev
from typing import Any, Optional

from apps.api.domain.research import AstrologicalSnapshot
from apps.api.domain.statistics import (
    AggregateReport,
    Crosstab,
    DatasetMetadata,
    Distribution,
    NumericSummary,
    StatValue,
)
from apps.api.services.snapshot_accessor import SnapshotAccessor

_ENGINE_VERSION = "1.0"


def _accessor(snapshot: AstrologicalSnapshot) -> SnapshotAccessor:
    """Convenience: wrap a snapshot in an accessor."""
    return SnapshotAccessor(snapshot)


def _safe_int(value: Any) -> Optional[int]:
    """Convert value to int, returning None on failure."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _safe_float(value: Any) -> Optional[float]:
    """Convert value to float, returning None on failure."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _compute_numeric_stats(values: list[float]) -> dict[str, float]:
    """Compute descriptive statistics from a list of floats."""
    if not values:
        return {"mean": 0.0, "std_dev": 0.0, "min": 0.0, "max": 0.0,
                "median": 0.0, "q1": 0.0, "q3": 0.0, "sum": 0.0}

    n = len(values)
    sorted_vals = sorted(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    std_dev = math.sqrt(variance)

    def _percentile(sorted_data: list[float], p: float) -> float:
        k = (len(sorted_data) - 1) * p / 100.0
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_data[int(k)]
        return sorted_data[f] * (c - k) + sorted_data[c] * (k - f)

    return {
        "mean": round(mean, 4),
        "std_dev": round(std_dev, 4),
        "min": sorted_vals[0],
        "max": sorted_vals[-1],
        "median": _median(sorted_vals),
        "q1": round(_percentile(sorted_vals, 25), 4),
        "q3": round(_percentile(sorted_vals, 75), 4),
        "sum": round(sum(values), 4),
    }


class StatisticsEngine:
    """
    Stateless — takes snapshot collections per call, never holds state.
    All methods handle empty collections gracefully.
    """

    _ENGINE_VERSION = _ENGINE_VERSION

    # ── Distributions ────────────────────────────────────────────────────

    @staticmethod
    def compute_planet_house_distribution(
        snapshots: tuple[AstrologicalSnapshot, ...],
        planet: str = "jupiter",
    ) -> Distribution:
        """Frequency of *planet* appearing in houses 1-12 across *snapshots*."""
        counts: dict[str, int] = {}
        for snap in snapshots:
            acc = _accessor(snap)
            planets = acc.get("chart_ref.planets")
            if not planets:
                continue
            for p in planets:
                if getattr(p, "planet", None) == planet:
                    house = getattr(p, "house_number", None)
                    if house is not None:
                        key = str(house)
                        counts[key] = counts.get(key, 0) + 1

        bins = tuple(str(h) for h in range(1, 13))
        counts_tuple = tuple(counts.get(b, 0) for b in bins)
        total = sum(counts_tuple)
        return Distribution(
            label=f"Planet House Distribution ({planet.capitalize()})",
            variable=f"planet.{planet}.house",
            bins=bins,
            counts=counts_tuple,
            total=total,
        )

    @staticmethod
    def compute_planet_rashi_distribution(
        snapshots: tuple[AstrologicalSnapshot, ...],
        planet: str = "jupiter",
    ) -> Distribution:
        """Frequency of *planet* appearing in each rashi across *snapshots*."""
        all_rashis = [
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
        ]
        counts: dict[str, int] = {}
        for snap in snapshots:
            acc = _accessor(snap)
            planets = acc.get("chart_ref.planets")
            if not planets:
                continue
            for p in planets:
                if getattr(p, "planet", None) == planet:
                    rashi = getattr(p, "rashi", None)
                    if rashi:
                        counts[rashi] = counts.get(rashi, 0) + 1

        bins = tuple(all_rashis)
        counts_tuple = tuple(counts.get(b, 0) for b in bins)
        total = sum(counts_tuple)
        return Distribution(
            label=f"Planet Rashi Distribution ({planet.capitalize()})",
            variable=f"planet.{planet}.rashi",
            bins=bins,
            counts=counts_tuple,
            total=total,
        )

    @staticmethod
    def compute_yoga_distribution(
        snapshots: tuple[AstrologicalSnapshot, ...],
    ) -> Distribution:
        """Frequency of each present yoga across *snapshots*."""
        counts: Counter = Counter()
        for snap in snapshots:
            acc = _accessor(snap)
            yogas = acc.get("yogas")
            if not yogas:
                continue
            for y in yogas:
                if getattr(y, "is_present", False):
                    yid = getattr(y, "yoga_id", None)
                    if yid:
                        counts[yid] += 1

        bins = tuple(sorted(counts.keys()))
        counts_tuple = tuple(counts[b] for b in bins)
        return Distribution(
            label="Yoga Distribution",
            variable="yoga.is_present",
            bins=bins,
            counts=counts_tuple,
            total=sum(counts_tuple),
        )

    @staticmethod
    def compute_verification_strength_distribution(
        snapshots: tuple[AstrologicalSnapshot, ...],
    ) -> Distribution:
        """Frequency of each VerificationStrength across *snapshots* timeline."""
        strengths = ["high", "medium", "low", "unknown"]
        counts: dict[str, int] = {s: 0 for s in strengths}

        for snap in snapshots:
            acc = _accessor(snap)
            ver = acc.get("verification_ref")
            if ver is None:
                continue
            pairs = getattr(ver, "verification_pairs", None)
            if not pairs:
                continue
            for pair in pairs:
                s = getattr(pair, "strength", None)
                if s is not None:
                    key = s.value if hasattr(s, "value") else str(s)
                    if key in counts:
                        counts[key] += 1

        bins = tuple(strengths)
        counts_tuple = tuple(counts[b] for b in bins)
        return Distribution(
            label="Verification Strength Distribution",
            variable="verification.strength",
            bins=bins,
            counts=counts_tuple,
            total=sum(counts_tuple),
        )

    # ── Numeric summaries ─────────────────────────────────────────────────

    @staticmethod
    def compute_planet_house_summary(
        snapshots: tuple[AstrologicalSnapshot, ...],
        planet: str = "jupiter",
    ) -> NumericSummary:
        """Descriptive statistics for *planet*'s house number across snapshots."""
        values: list[float] = []
        for snap in snapshots:
            acc = _accessor(snap)
            planets = acc.get("chart_ref.planets")
            if not planets:
                continue
            for p in planets:
                if getattr(p, "planet", None) == planet:
                    h = _safe_float(getattr(p, "house_number", None))
                    if h is not None:
                        values.append(h)

        stats = _compute_numeric_stats(values)
        return NumericSummary(
            label=f"Planet House Summary ({planet.capitalize()})",
            variable=f"planet.{planet}.house",
            count=len(values),
            mean=stats["mean"],
            std_dev=stats["std_dev"],
            min=stats["min"],
            max=stats["max"],
            median=stats["median"],
            q1=stats["q1"],
            q3=stats["q3"],
            sum=stats["sum"],
        )

    # ── Association ───────────────────────────────────────────────────────

    @staticmethod
    def compute_crosstab(
        snapshots: tuple[AstrologicalSnapshot, ...],
        row_field: str,
        col_field: str,
    ) -> Crosstab:
        """
        Contingency table for two categorical fields.

        Both fields are evaluated via SnapshotAccessor.get() for each
        snapshot. String representations of the values are used as keys.
        """
        cell_data: dict[tuple[str, str], int] = defaultdict(int)
        row_vals: set[str] = set()
        col_vals: set[str] = set()

        for snap in snapshots:
            acc = _accessor(snap)
            rv = str(acc.get(row_field) or "none")
            cv = str(acc.get(col_field) or "none")
            row_vals.add(rv)
            col_vals.add(cv)
            cell_data[(rv, cv)] += 1

        sorted_rows = sorted(row_vals)
        sorted_cols = sorted(col_vals)

        cells: list[tuple[int, ...]] = []
        for r in sorted_rows:
            row: list[int] = []
            for c in sorted_cols:
                row.append(cell_data.get((r, c), 0))
            cells.append(tuple(row))

        return Crosstab(
            label=f"Crosstab: {row_field} x {col_field}",
            row_variable=row_field,
            column_variable=col_field,
            row_labels=tuple(sorted_rows),
            column_labels=tuple(sorted_cols),
            cells=tuple(cells),
            row_totals=tuple(sum(row) for row in cells),
        )

    # ── Aggregate report ──────────────────────────────────────────────────

    @staticmethod
    def compute_full_report(
        snapshots: tuple[AstrologicalSnapshot, ...],
        title: str = "Statistical Analysis",
        experiment_id: Optional[uuid.UUID] = None,
        filtered_sample_size: Optional[int] = None,
    ) -> AggregateReport:
        """
        Compute a complete statistical analysis across all snapshots.

        Includes planet house distribution (jupiter, sun, moon),
        yoga distribution, verification strength distribution,
        and numeric summaries for key planets.
        """
        metadata = DatasetMetadata(
            sample_size=len(snapshots),
            snapshot_count=len(snapshots),
            filtered_sample_size=filtered_sample_size,
            experiment_id=experiment_id,
            engine_version=_ENGINE_VERSION,
            generated_at=datetime.now(timezone.utc),
        )

        distributions: list[Distribution] = [
            StatisticsEngine.compute_planet_house_distribution(snapshots, "sun"),
            StatisticsEngine.compute_planet_house_distribution(snapshots, "moon"),
            StatisticsEngine.compute_yoga_distribution(snapshots),
            StatisticsEngine.compute_verification_strength_distribution(snapshots),
        ]

        numeric: list[NumericSummary] = [
            StatisticsEngine.compute_planet_house_summary(snapshots, "sun"),
            StatisticsEngine.compute_planet_house_summary(snapshots, "moon"),
        ]

        return AggregateReport(
            title=title,
            metadata=metadata,
            distributions=tuple(distributions),
            numeric_summaries=tuple(numeric),
            report_version="1.0",
        )
