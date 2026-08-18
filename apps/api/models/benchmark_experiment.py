"""
AstroOS — Benchmark Experiment ORM Model

Persists benchmark experiment runs, locked dataset splits, profile comparisons,
calibration parameters, and cryptographic result hashes for scientific reproducibility.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.models.base import AstroBase


class BenchmarkExperimentModel(AstroBase):
    __tablename__ = "benchmark_experiments"

    experiment_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True,
        comment="Human-readable deterministic experiment ID (e.g. EXP-BENCH-CAREER-001-42-a1b2c3d4)",
    )
    benchmark_id: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="Target benchmark corpus identifier (e.g. BENCH-CAREER-001)",
    )
    benchmark_version: Mapped[str] = mapped_column(
        String(20), nullable=False, default="1.0.0",
    )
    content_hash_sha256: Mapped[str] = mapped_column(
        String(64), nullable=False,
        comment="SHA-256 content hash of the locked benchmark dataset",
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="COMPLETED",
        comment="PENDING | RUNNING | COMPLETED | FAILED",
    )
    split_seed: Mapped[int] = mapped_column(Integer, nullable=False, default=42)
    split_train_ratio: Mapped[float] = mapped_column(Float, nullable=False, default=0.70)
    tolerance_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    profile_ids: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list,
        comment="List of evaluated consensus profile IDs",
    )
    baseline_profile_id: Mapped[str] = mapped_column(
        String(100), nullable=False, default="parashari_standard_v1",
    )
    train_event_ids: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list,
        comment="Exact locked training event IDs",
    )
    holdout_event_ids: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list,
        comment="Exact locked holdout event IDs",
    )
    results_summary: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict,
        comment="Detailed metrics rows per profile (Holdout N, Hit Rate, Brier, MAE...)",
    )
    baseline_comparisons: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list,
        comment="Deltas against baseline profile",
    )
    calibration_models: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict,
        comment="Fitted calibration parameters/pools per profile",
    )
    results_hash_sha256: Mapped[str] = mapped_column(
        String(64), nullable=False,
        comment="Deterministic SHA-256 hash of the experiment evaluation results",
    )
    duration_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )