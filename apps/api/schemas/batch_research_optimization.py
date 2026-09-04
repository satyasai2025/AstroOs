"""
AstroOS — Large-Scale Batch Research Optimization Schemas (Priority 18)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class BatchWorkerMetricsItem(BaseModel):
    worker_id: str
    processed_count: int
    active_chunk_index: int
    throughput_charts_per_sec: float
    memory_mb: float
    cpu_utilization_percent: float


class BatchJobCheckpointItem(BaseModel):
    checkpoint_id: str
    job_id: str
    chunk_index: int
    processed_subjects: int
    running_brier_sum: float
    running_log_loss_sum: float
    running_hits_count: int
    checkpoint_sha256_hash: str
    timestamp: datetime


class SubmitBatchJobRequest(BaseModel):
    dataset_id: str = Field(default="ds-marriage-28", description="Target cohort benchmark dataset ID")
    target_objective: str = Field(default="marriage", description="Astrological event objective")
    total_subjects_target: int = Field(default=1000, description="Total subjects to process in cohort run")
    chunk_size: int = Field(default=250, description="Subjects per streaming chunk")
    max_workers: int = Field(default=4, description="Parallel compute workers")
    enable_ephemeris_cache: bool = Field(default=True, description="Enable high-speed ephemeris caching")
    checkpoint_interval_chunks: int = Field(default=2, description="Chunks between state checkpoints")
    monte_carlo_permutations: int = Field(default=50, description="Monte Carlo permutation samples per chunk")


class BatchJobReportResponse(BaseModel):
    job_id: str
    dataset_id: str
    target_objective: str
    status: str
    total_subjects_evaluated: int
    total_runtime_seconds: float
    average_throughput_charts_per_sec: float
    cache_hit_rate_percent: float
    aggregate_brier_score: float
    aggregate_log_loss: float
    aggregate_roc_auc: float
    aggregate_hit_rate: float
    checkpoints_saved: int
    worker_metrics: List[BatchWorkerMetricsItem]
    started_at: datetime
    completed_at: Optional[datetime] = None
