"""
AstroOS — Priority 11: Scientific Experiment Router
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, List
from fastapi import APIRouter, HTTPException, status

from apps.api.domain.experiment_lineage import (
    CalibrationProvenanceSnapshot,
    DatasetProvenanceSnapshot,
    ExperimentMetrics,
    OrchestratorConfigSnapshot,
    TechniqueProvenanceSnapshot,
)
from apps.api.schemas.experiment import (
    CompareExperimentsRequest,
    ExperimentCreateRequest,
    ExperimentImportRequest,
    SnapshotFreezeRequest,
)
from apps.api.services.experiment_service import ExperimentRegistry

router = APIRouter(prefix="/research/experiments", tags=["Research Experiments"])


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_experiment(req: ExperimentCreateRequest) -> dict[str, Any]:
    """Create a new research experiment container."""
    reg = ExperimentRegistry.get_instance()
    meta = reg.create_experiment(
        name=req.name,
        description=req.description,
        author=req.author,
        tags=tuple(req.tags),
    )
    return {
        "experiment_id": meta.experiment_id,
        "name": meta.name,
        "description": meta.description,
        "author": meta.author,
        "created_at": meta.created_at.isoformat(),
        "tags": list(meta.tags),
    }


@router.get("", status_code=status.HTTP_200_OK)
@router.get("/", status_code=status.HTTP_200_OK)
def list_experiments() -> List[dict[str, Any]]:
    """List all registered research experiments."""
    reg = ExperimentRegistry.get_instance()
    experiments = reg.list_experiments()
    out = []
    for e in experiments:
        lineage = reg.get_lineage(e.experiment_id)
        snapshot_count = len(lineage.snapshots) if lineage else 0
        out.append(
            {
                "experiment_id": e.experiment_id,
                "name": e.name,
                "description": e.description,
                "author": e.author,
                "created_at": e.created_at.isoformat(),
                "status": e.status,
                "tags": list(e.tags),
                "snapshot_count": snapshot_count,
            }
        )
    return out


@router.get("/{experiment_id}", status_code=status.HTTP_200_OK)
def get_experiment(experiment_id: str) -> dict[str, Any]:
    """Inspect experiment details and lineage DAG."""
    reg = ExperimentRegistry.get_instance()
    meta = reg.get_experiment(experiment_id)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment '{experiment_id}' not found",
        )

    lineage = reg.get_lineage(experiment_id)
    snapshots_json = []
    if lineage:
        for s in lineage.snapshots:
            snapshots_json.append(
                {
                    "snapshot_id": s.snapshot_id,
                    "parent_snapshot_id": s.parent_snapshot_id,
                    "timestamp": s.timestamp.isoformat(),
                    "sha256_hash": s.snapshot_sha256_hash,
                    "dataset_id": s.dataset.dataset_id,
                    "metrics": {
                        "brier_score": s.metrics.brier_score,
                        "log_loss": s.metrics.log_loss,
                        "f1_score": s.metrics.f1_score,
                        "roc_auc": s.metrics.roc_auc,
                    },
                }
            )

    return {
        "experiment_id": meta.experiment_id,
        "name": meta.name,
        "description": meta.description,
        "author": meta.author,
        "created_at": meta.created_at.isoformat(),
        "status": meta.status,
        "tags": list(meta.tags),
        "snapshots": snapshots_json,
        "dag_edges": lineage.dag_edges if lineage else [],
    }


@router.post("/{experiment_id}/snapshots", status_code=status.HTTP_201_CREATED)
def freeze_snapshot(experiment_id: str, req: SnapshotFreezeRequest) -> dict[str, Any]:
    """Freeze an immutable snapshot tying together dataset, rules, weights, and metrics."""
    reg = ExperimentRegistry.get_instance()
    meta = reg.get_experiment(experiment_id)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment '{experiment_id}' not found",
        )

    ds = DatasetProvenanceSnapshot(
        dataset_id=req.dataset_id,
        dataset_version=req.dataset_version,
        sha256_hash=req.dataset_hash,
        record_count=req.record_count,
    )

    combined_tech_str = json.dumps({"rules": req.dsl_rule_ids, "classical": req.classical_techniques})
    tech_hash = hashlib.sha256(combined_tech_str.encode()).hexdigest()
    tech = TechniqueProvenanceSnapshot(
        dsl_rule_ids=tuple(req.dsl_rule_ids),
        dsl_hashes=tuple(hashlib.sha256(r.encode()).hexdigest() for r in req.dsl_rule_ids),
        classical_techniques=tuple(req.classical_techniques),
        combined_sha256_hash=tech_hash,
    )

    cal_hash = hashlib.sha256(json.dumps(req.technique_weights, sort_keys=True).encode()).hexdigest()
    cal = CalibrationProvenanceSnapshot(
        profile_id=req.calibration_profile_id,
        status=req.calibration_status,
        technique_weights=req.technique_weights,
        primary_brier_score=req.primary_brier_score,
        primary_log_loss=req.primary_log_loss,
        sha256_hash=cal_hash,
    )

    orch = OrchestratorConfigSnapshot(
        consensus_profile_id=req.consensus_profile_id,
        minimum_activation_threshold=req.minimum_activation_threshold,
        conflict_penalty_multiplier=req.conflict_penalty_multiplier,
    )

    metrics = ExperimentMetrics(
        brier_score=req.primary_brier_score,
        log_loss=req.primary_log_loss,
        precision=req.precision,
        recall=req.recall,
        f1_score=req.f1_score,
        roc_auc=req.roc_auc,
        roc_auc_status=req.roc_auc_status,
        sample_size_n=req.sample_size_n,
        hit_rate=req.hit_rate,
    )

    snapshot = reg.freeze_snapshot(
        experiment_id=experiment_id,
        dataset=ds,
        techniques=tech,
        calibration=cal,
        orchestrator=orch,
        metrics=metrics,
        execution_params=req.execution_params,
        parent_snapshot_id=req.parent_snapshot_id,
    )

    return {
        "snapshot_id": snapshot.snapshot_id,
        "experiment_id": snapshot.experiment_id,
        "parent_snapshot_id": snapshot.parent_snapshot_id,
        "timestamp": snapshot.timestamp.isoformat(),
        "sha256_hash": snapshot.snapshot_sha256_hash,
        "dataset_hash": ds.sha256_hash,
        "metrics": {
            "brier_score": metrics.brier_score,
            "log_loss": metrics.log_loss,
            "f1_score": metrics.f1_score,
            "roc_auc": metrics.roc_auc,
        },
    }


@router.get("/{experiment_id}/snapshots/{snapshot_id}", status_code=status.HTTP_200_OK)
def get_snapshot(experiment_id: str, snapshot_id: str) -> dict[str, Any]:
    """Retrieve full immutable snapshot details."""
    reg = ExperimentRegistry.get_instance()
    snap = reg.get_snapshot(experiment_id, snapshot_id)
    if not snap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot '{snapshot_id}' not found in experiment '{experiment_id}'",
        )

    return {
        "snapshot_id": snap.snapshot_id,
        "experiment_id": snap.experiment_id,
        "parent_snapshot_id": snap.parent_snapshot_id,
        "timestamp": snap.timestamp.isoformat(),
        "schema_version": snap.schema_version,
        "snapshot_sha256_hash": snap.snapshot_sha256_hash,
        "dataset": {
            "dataset_id": snap.dataset.dataset_id,
            "dataset_version": snap.dataset.dataset_version,
            "sha256_hash": snap.dataset.sha256_hash,
            "record_count": snap.dataset.record_count,
        },
        "techniques": {
            "dsl_rule_ids": list(snap.techniques.dsl_rule_ids),
            "classical_techniques": list(snap.techniques.classical_techniques),
            "combined_sha256_hash": snap.techniques.combined_sha256_hash,
        },
        "calibration": {
            "profile_id": snap.calibration.profile_id,
            "status": snap.calibration.status,
            "technique_weights": snap.calibration.technique_weights,
            "sha256_hash": snap.calibration.sha256_hash,
        },
        "metrics": {
            "brier_score": snap.metrics.brier_score,
            "log_loss": snap.metrics.log_loss,
            "precision": snap.metrics.precision,
            "recall": snap.metrics.recall,
            "f1_score": snap.metrics.f1_score,
            "roc_auc": snap.metrics.roc_auc,
            "roc_auc_status": snap.metrics.roc_auc_status,
            "sample_size_n": snap.metrics.sample_size_n,
            "hit_rate": snap.metrics.hit_rate,
        },
    }


@router.post("/compare", status_code=status.HTTP_200_OK)
@router.post("/compare/", status_code=status.HTTP_200_OK)
def compare_experiments(req: CompareExperimentsRequest) -> dict[str, Any]:
    """Side-by-side comparison of two experiment snapshots."""
    reg = ExperimentRegistry.get_instance()
    try:
        diff = reg.compare_snapshots(
            exp1_id=req.exp1_id,
            snap1_id=req.snapshot1_id,
            exp2_id=req.exp2_id,
            snap2_id=req.snapshot2_id,
        )
        return {
            "exp1_id": diff.exp1_id,
            "exp2_id": diff.exp2_id,
            "snapshot1_id": diff.snapshot1_id,
            "snapshot2_id": diff.snapshot2_id,
            "dataset_changed": diff.dataset_changed,
            "rules_changed": diff.rules_changed,
            "weights_changed": diff.weights_changed,
            "summary": diff.summary,
            "metric_deltas": [
                {
                    "metric_name": d.metric_name,
                    "exp1_value": d.exp1_value,
                    "exp2_value": d.exp2_value,
                    "absolute_delta": d.absolute_delta,
                    "percentage_delta": d.percentage_delta,
                    "improvement_status": d.improvement_status,
                }
                for d in diff.metric_deltas
            ],
        }
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{experiment_id}/snapshots/{snapshot_id}/export", status_code=status.HTTP_200_OK)
def export_snapshot(experiment_id: str, snapshot_id: str) -> dict[str, str]:
    """Export snapshot JSON bundle for portability."""
    reg = ExperimentRegistry.get_instance()
    try:
        json_bundle = reg.export_snapshot_json(experiment_id, snapshot_id)
        return {"bundle_json": json_bundle}
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/import", status_code=status.HTTP_201_CREATED)
@router.post("/import/", status_code=status.HTTP_201_CREATED)
def import_snapshot(req: ExperimentImportRequest) -> dict[str, Any]:
    """Import snapshot JSON bundle with tamper verification."""
    reg = ExperimentRegistry.get_instance()
    try:
        snap = reg.import_snapshot_json(req.bundle_json)
        return {
            "snapshot_id": snap.snapshot_id,
            "experiment_id": snap.experiment_id,
            "status": "IMPORTED_SUCCESS",
            "sha256_hash": snap.snapshot_sha256_hash,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
