"""
AstroOS — Large-Scale Distributed / Local Cohort Research Optimization Domain Models (Priority 18)

Defines domain dataclasses for:
  - Batch Job Lifecycle & Execution Configuration
  - Chunked Streaming & Fault-Tolerant Checkpointing
  - Multi-Worker Real-Time Throughput Metrics
  - Online Streamed Statistical Aggregates (Welford running Brier, LogLoss, ROC-AUC)
  - Final Batch Research Execution Reports
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class BatchJobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class BatchWorkerMetrics:
    """Real-time performance metrics for an individual parallel compute worker."""
    worker_id: str
    processed_count: int
    active_chunk_index: int
    throughput_charts_per_sec: float
    memory_mb: float
    cpu_utilization_percent: float


@dataclass(frozen=True)
class BatchJobCheckpoint:
    """Immutable state snapshot allowing mid-job pause, fault-recovery, and resume."""
    checkpoint_id: str
    job_id: str
    chunk_index: int
    processed_subjects: int
    running_brier_sum: float
    running_log_loss_sum: float
    running_hits_count: int
    checkpoint_sha256_hash: str
    timestamp: datetime


@dataclass(frozen=True)
class BatchExecutionConfig:
    """Configuration parameters for large-scale cohort execution."""
    job_id: str
    dataset_id: str
    target_objective: str
    total_subjects_target: int
    chunk_size: int = 250
    max_workers: int = 4
    enable_ephemeris_cache: bool = True
    checkpoint_interval_chunks: int = 2
    monte_carlo_permutations: int = 50


@dataclass(frozen=True)
class BatchJobReport:
    """Comprehensive statistical aggregation report produced upon completion of a large-scale batch job."""
    job_id: str
    dataset_id: str
    target_objective: str
    status: BatchJobStatus
    total_subjects_evaluated: int
    total_runtime_seconds: float
    average_throughput_charts_per_sec: float
    cache_hit_rate_percent: float
    aggregate_brier_score: float
    aggregate_log_loss: float
    aggregate_roc_auc: float
    aggregate_hit_rate: float
    checkpoints_saved: int
    worker_metrics: tuple[BatchWorkerMetrics, ...]
    started_at: datetime
    completed_at: Optional[datetime] = None
