"""
AstroOS — Priority 11: Scientific Experiment Service & Diff Engine
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import date, datetime
from typing import Any, Optional

from apps.api.domain.experiment_lineage import (
    CalibrationProvenanceSnapshot,
    DatasetProvenanceSnapshot,
    ExperimentDiffResult,
    ExperimentLineage,
    ExperimentMetadata,
    ExperimentMetrics,
    ExperimentSnapshot,
    MetricDelta,
    OrchestratorConfigSnapshot,
    TechniqueProvenanceSnapshot,
)


class ExperimentDiffEngine:
    """Computes side-by-side comparative diffs between two experiment snapshots."""

    @staticmethod
    def compare(
        exp1: ExperimentSnapshot,
        exp2: ExperimentSnapshot,
    ) -> ExperimentDiffResult:
        m1 = exp1.metrics
        m2 = exp2.metrics

        deltas: list[MetricDelta] = []

        # 1. Brier Score (lower is better)
        brier_diff = round(m2.brier_score - m1.brier_score, 4)
        brier_pct = round((brier_diff / m1.brier_score) * 100, 2) if m1.brier_score != 0 else 0.0
        brier_status = "IMPROVED" if brier_diff < 0 else "DEGRADED" if brier_diff > 0 else "UNCHANGED"
        deltas.append(
            MetricDelta(
                metric_name="Brier Score (Primary)",
                exp1_value=m1.brier_score,
                exp2_value=m2.brier_score,
                absolute_delta=brier_diff,
                percentage_delta=brier_pct,
                improvement_status=brier_status,
            )
        )

        # 2. Log Loss (lower is better)
        ll_diff = round(m2.log_loss - m1.log_loss, 4)
        ll_pct = round((ll_diff / m1.log_loss) * 100, 2) if m1.log_loss != 0 else 0.0
        ll_status = "IMPROVED" if ll_diff < 0 else "DEGRADED" if ll_diff > 0 else "UNCHANGED"
        deltas.append(
            MetricDelta(
                metric_name="Log Loss (Primary)",
                exp1_value=m1.log_loss,
                exp2_value=m2.log_loss,
                absolute_delta=ll_diff,
                percentage_delta=ll_pct,
                improvement_status=ll_status,
            )
        )

        # 3. F1 Score (higher is better)
        f1_diff = round(m2.f1_score - m1.f1_score, 4)
        f1_pct = round((f1_diff / m1.f1_score) * 100, 2) if m1.f1_score != 0 else 0.0
        f1_status = "IMPROVED" if f1_diff > 0 else "DEGRADED" if f1_diff < 0 else "UNCHANGED"
        deltas.append(
            MetricDelta(
                metric_name="F1 Score (Diagnostic)",
                exp1_value=m1.f1_score,
                exp2_value=m2.f1_score,
                absolute_delta=f1_diff,
                percentage_delta=f1_pct,
                improvement_status=f1_status,
            )
        )

        # 4. ROC-AUC (higher is better, conditional)
        if m1.roc_auc is not None and m2.roc_auc is not None:
            auc_diff = round(m2.roc_auc - m1.roc_auc, 4)
            auc_pct = round((auc_diff / m1.roc_auc) * 100, 2) if m1.roc_auc != 0 else 0.0
            auc_status = "IMPROVED" if auc_diff > 0 else "DEGRADED" if auc_diff < 0 else "UNCHANGED"
            deltas.append(
                MetricDelta(
                    metric_name="ROC-AUC (Diagnostic)",
                    exp1_value=m1.roc_auc,
                    exp2_value=m2.roc_auc,
                    absolute_delta=auc_diff,
                    percentage_delta=auc_pct,
                    improvement_status=auc_status,
                )
            )
        else:
            deltas.append(
                MetricDelta(
                    metric_name="ROC-AUC (Diagnostic)",
                    exp1_value=m1.roc_auc_status if m1.roc_auc is None else m1.roc_auc,
                    exp2_value=m2.roc_auc_status if m2.roc_auc is None else m2.roc_auc,
                    absolute_delta=None,
                    percentage_delta=None,
                    improvement_status="NOT_APPLICABLE",
                )
            )

        # 5. Cohort / Sample Size N
        n_diff = m2.sample_size_n - m1.sample_size_n
        deltas.append(
            MetricDelta(
                metric_name="Holdout Cohort Size N",
                exp1_value=m1.sample_size_n,
                exp2_value=m2.sample_size_n,
                absolute_delta=float(n_diff),
                percentage_delta=None,
                improvement_status="UNCHANGED" if n_diff == 0 else "NOT_APPLICABLE",
            )
        )

        dataset_changed = exp1.dataset.sha256_hash != exp2.dataset.sha256_hash
        rules_changed = exp1.techniques.combined_sha256_hash != exp2.techniques.combined_sha256_hash
        weights_changed = exp1.calibration.sha256_hash != exp2.calibration.sha256_hash

        summary = (
            f"Comparison of Snapshot '{exp1.snapshot_id}' vs '{exp2.snapshot_id}': "
            f"Brier Score delta = {brier_diff} ({brier_status}), "
            f"Log Loss delta = {ll_diff} ({ll_status}), "
            f"Dataset Changed = {dataset_changed}, Rules Changed = {rules_changed}, Weights Changed = {weights_changed}."
        )

        return ExperimentDiffResult(
            exp1_id=exp1.experiment_id,
            exp2_id=exp2.experiment_id,
            snapshot1_id=exp1.snapshot_id,
            snapshot2_id=exp2.snapshot_id,
            metric_deltas=tuple(deltas),
            dataset_changed=dataset_changed,
            rules_changed=rules_changed,
            weights_changed=weights_changed,
            summary=summary,
        )


class ExperimentRegistry:
    """
    Local-First Persistent Experiment Registry & Lineage Engine.
    Strictly append-only: Never overwrites historical snapshots.
    """

    _instance: Optional[ExperimentRegistry] = None

    def __init__(self) -> None:
        self._EXPERIMENTS: dict[str, ExperimentMetadata] = {}
        self._SNAPSHOTS: dict[str, list[ExperimentSnapshot]] = {}
        self._seed_default_experiments()

    @classmethod
    def get_instance(cls) -> ExperimentRegistry:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _seed_default_experiments(self) -> None:
        if "exp-parashari-baseline" in self._EXPERIMENTS:
            return

        exp1 = ExperimentMetadata(
            experiment_id="exp-parashari-baseline",
            name="Parashari Baseline Marriage Research",
            description="Baseline Parashari marriage prediction experiment across 100 historical charts",
            author="Dr. V. Raman",
            created_at=datetime(2026, 8, 1, 10, 0),
            tags=("parashari", "marriage", "baseline"),
        )
        self._EXPERIMENTS[exp1.experiment_id] = exp1

        ds1 = DatasetProvenanceSnapshot(
            dataset_id="ds-marriage-100",
            dataset_version="1.0",
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            record_count=100,
        )
        tech1 = TechniqueProvenanceSnapshot(
            dsl_rule_ids=("parashari-7th-lord-v1",),
            dsl_hashes=("hash-7th-lord",),
            classical_techniques=("vimshottari_dasha", "transit_jupiter"),
            combined_sha256_hash="tech-hash-111",
        )
        cal1 = CalibrationProvenanceSnapshot(
            profile_id="cand-parashari-v1",
            status="ACTIVE",
            technique_weights={"natal_promise_weight": 0.85, "dasha_weight": 0.65, "transit_weight": 0.50},
            primary_brier_score=0.045,
            primary_log_loss=0.140,
            sha256_hash="cal-hash-111",
        )
        orch1 = OrchestratorConfigSnapshot(
            consensus_profile_id="cand-parashari-v1",
            minimum_activation_threshold=60,
            conflict_penalty_multiplier=1.25,
        )
        metrics1 = ExperimentMetrics(
            brier_score=0.045,
            log_loss=0.140,
            precision=0.88,
            recall=0.85,
            f1_score=0.865,
            roc_auc=0.910,
            roc_auc_status="VALID",
            sample_size_n=30,
            hit_rate=0.867,
        )
        snap1_hash = ExperimentSnapshot.compute_sha256(exp1.experiment_id, ds1, tech1, cal1, metrics1)
        snap1 = ExperimentSnapshot(
            snapshot_id="snap-baseline-v1",
            experiment_id=exp1.experiment_id,
            parent_snapshot_id=None,
            timestamp=datetime(2026, 8, 1, 10, 5),
            schema_version="1.0",
            dataset=ds1,
            techniques=tech1,
            calibration=cal1,
            orchestrator=orch1,
            metrics=metrics1,
            execution_params={"split_train_ratio": 0.70, "seed": 42},
            snapshot_sha256_hash=snap1_hash,
        )
        self._SNAPSHOTS[exp1.experiment_id] = [snap1]

    def create_experiment(
        self,
        name: str,
        description: str,
        author: str = "researcher",
        tags: tuple[str, ...] = (),
    ) -> ExperimentMetadata:
        exp_id = f"exp-{uuid.uuid4().hex[:8]}"
        meta = ExperimentMetadata(
            experiment_id=exp_id,
            name=name,
            description=description,
            author=author,
            created_at=datetime.now(),
            tags=tags,
        )
        self._EXPERIMENTS[exp_id] = meta
        self._SNAPSHOTS[exp_id] = []
        return meta

    def freeze_snapshot(
        self,
        experiment_id: str,
        dataset: DatasetProvenanceSnapshot,
        techniques: TechniqueProvenanceSnapshot,
        calibration: CalibrationProvenanceSnapshot,
        orchestrator: OrchestratorConfigSnapshot,
        metrics: ExperimentMetrics,
        execution_params: Optional[dict[str, Any]] = None,
        parent_snapshot_id: Optional[str] = None,
    ) -> ExperimentSnapshot:
        if experiment_id not in self._EXPERIMENTS:
            raise KeyError(f"Experiment '{experiment_id}' not found")

        history = self._SNAPSHOTS.get(experiment_id, [])
        if not parent_snapshot_id and history:
            parent_snapshot_id = history[-1].snapshot_id

        snapshot_id = f"snap-{uuid.uuid4().hex[:8]}"
        sha256_hash = ExperimentSnapshot.compute_sha256(experiment_id, dataset, techniques, calibration, metrics)

        snapshot = ExperimentSnapshot(
            snapshot_id=snapshot_id,
            experiment_id=experiment_id,
            parent_snapshot_id=parent_snapshot_id,
            timestamp=datetime.now(),
            schema_version="1.0",
            dataset=dataset,
            techniques=techniques,
            calibration=calibration,
            orchestrator=orchestrator,
            metrics=metrics,
            execution_params=execution_params or {"split_train_ratio": 0.70, "seed": 42},
            snapshot_sha256_hash=sha256_hash,
        )

        # Append-only: Never overwrite existing snapshots
        self._SNAPSHOTS[experiment_id].append(snapshot)
        return snapshot

    def list_experiments(self) -> list[ExperimentMetadata]:
        return list(self._EXPERIMENTS.values())

    def get_experiment(self, experiment_id: str) -> Optional[ExperimentMetadata]:
        return self._EXPERIMENTS.get(experiment_id)

    def get_lineage(self, experiment_id: str) -> Optional[ExperimentLineage]:
        if experiment_id not in self._EXPERIMENTS:
            return None

        snapshots = tuple(self._SNAPSHOTS.get(experiment_id, []))
        dag_edges: list[tuple[str, str]] = []
        for s in snapshots:
            if s.parent_snapshot_id:
                dag_edges.append((s.parent_snapshot_id, s.snapshot_id))

        return ExperimentLineage(
            experiment_id=experiment_id,
            snapshots=snapshots,
            dag_edges=tuple(dag_edges),
        )

    def get_snapshot(self, experiment_id: str, snapshot_id: str) -> Optional[ExperimentSnapshot]:
        history = self._SNAPSHOTS.get(experiment_id, [])
        for s in history:
            if s.snapshot_id == snapshot_id:
                return s
        return None

    def compare_snapshots(
        self,
        exp1_id: str,
        snap1_id: str,
        exp2_id: str,
        snap2_id: str,
    ) -> ExperimentDiffResult:
        s1 = self.get_snapshot(exp1_id, snap1_id)
        s2 = self.get_snapshot(exp2_id, snap2_id)
        if not s1:
            raise KeyError(f"Snapshot '{snap1_id}' not found in experiment '{exp1_id}'")
        if not s2:
            raise KeyError(f"Snapshot '{snap2_id}' not found in experiment '{exp2_id}'")

        return ExperimentDiffEngine.compare(s1, s2)

    def export_snapshot_json(self, experiment_id: str, snapshot_id: str) -> str:
        s = self.get_snapshot(experiment_id, snapshot_id)
        if not s:
            raise KeyError(f"Snapshot '{snapshot_id}' not found")

        meta = self.get_experiment(experiment_id)
        payload = {
            "format": "AstroOS_Experiment_Snapshot_Bundle",
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "experiment": {
                "experiment_id": meta.experiment_id if meta else experiment_id,
                "name": meta.name if meta else "Imported Experiment",
                "description": meta.description if meta else "",
                "author": meta.author if meta else "researcher",
                "tags": list(meta.tags) if meta else [],
            },
            "snapshot": {
                "snapshot_id": s.snapshot_id,
                "parent_snapshot_id": s.parent_snapshot_id,
                "timestamp": s.timestamp.isoformat(),
                "schema_version": s.schema_version,
                "dataset": {
                    "dataset_id": s.dataset.dataset_id,
                    "dataset_version": s.dataset.dataset_version,
                    "sha256_hash": s.dataset.sha256_hash,
                    "record_count": s.dataset.record_count,
                },
                "techniques": {
                    "dsl_rule_ids": list(s.techniques.dsl_rule_ids),
                    "dsl_hashes": list(s.techniques.dsl_hashes),
                    "classical_techniques": list(s.techniques.classical_techniques),
                    "combined_sha256_hash": s.techniques.combined_sha256_hash,
                },
                "calibration": {
                    "profile_id": s.calibration.profile_id,
                    "status": s.calibration.status,
                    "technique_weights": s.calibration.technique_weights,
                    "primary_brier_score": s.calibration.primary_brier_score,
                    "primary_log_loss": s.calibration.primary_log_loss,
                    "sha256_hash": s.calibration.sha256_hash,
                },
                "orchestrator": {
                    "consensus_profile_id": s.orchestrator.consensus_profile_id,
                    "minimum_activation_threshold": s.orchestrator.minimum_activation_threshold,
                    "conflict_penalty_multiplier": s.orchestrator.conflict_penalty_multiplier,
                },
                "metrics": {
                    "brier_score": s.metrics.brier_score,
                    "log_loss": s.metrics.log_loss,
                    "precision": s.metrics.precision,
                    "recall": s.metrics.recall,
                    "f1_score": s.metrics.f1_score,
                    "roc_auc": s.metrics.roc_auc,
                    "roc_auc_status": s.metrics.roc_auc_status,
                    "sample_size_n": s.metrics.sample_size_n,
                    "hit_rate": s.metrics.hit_rate,
                },
                "execution_params": s.execution_params,
                "snapshot_sha256_hash": s.snapshot_sha256_hash,
            },
        }
        return json.dumps(payload, indent=2)

    def import_snapshot_json(self, json_str: str) -> ExperimentSnapshot:
        data = json.loads(json_str)
        if data.get("format") != "AstroOS_Experiment_Snapshot_Bundle":
            raise ValueError("Invalid bundle format. Expected 'AstroOS_Experiment_Snapshot_Bundle'")

        exp_data = data["experiment"]
        snap_data = data["snapshot"]

        exp_id = exp_data["experiment_id"]
        if exp_id not in self._EXPERIMENTS:
            self._EXPERIMENTS[exp_id] = ExperimentMetadata(
                experiment_id=exp_id,
                name=exp_data["name"],
                description=exp_data["description"],
                author=exp_data["author"],
                created_at=datetime.now(),
                tags=tuple(exp_data.get("tags", [])),
            )
            self._SNAPSHOTS[exp_id] = []

        ds = DatasetProvenanceSnapshot(
            dataset_id=snap_data["dataset"]["dataset_id"],
            dataset_version=snap_data["dataset"]["dataset_version"],
            sha256_hash=snap_data["dataset"]["sha256_hash"],
            record_count=snap_data["dataset"]["record_count"],
        )
        tech = TechniqueProvenanceSnapshot(
            dsl_rule_ids=tuple(snap_data["techniques"]["dsl_rule_ids"]),
            dsl_hashes=tuple(snap_data["techniques"]["dsl_hashes"]),
            classical_techniques=tuple(snap_data["techniques"]["classical_techniques"]),
            combined_sha256_hash=snap_data["techniques"]["combined_sha256_hash"],
        )
        cal = CalibrationProvenanceSnapshot(
            profile_id=snap_data["calibration"]["profile_id"],
            status=snap_data["calibration"]["status"],
            technique_weights=snap_data["calibration"]["technique_weights"],
            primary_brier_score=snap_data["calibration"]["primary_brier_score"],
            primary_log_loss=snap_data["calibration"]["primary_log_loss"],
            sha256_hash=snap_data["calibration"]["sha256_hash"],
        )
        orch = OrchestratorConfigSnapshot(
            consensus_profile_id=snap_data["orchestrator"]["consensus_profile_id"],
            minimum_activation_threshold=snap_data["orchestrator"]["minimum_activation_threshold"],
            conflict_penalty_multiplier=snap_data["orchestrator"]["conflict_penalty_multiplier"],
        )
        metrics = ExperimentMetrics(
            brier_score=snap_data["metrics"]["brier_score"],
            log_loss=snap_data["metrics"]["log_loss"],
            precision=snap_data["metrics"]["precision"],
            recall=snap_data["metrics"]["recall"],
            f1_score=snap_data["metrics"]["f1_score"],
            roc_auc=snap_data["metrics"]["roc_auc"],
            roc_auc_status=snap_data["metrics"]["roc_auc_status"],
            sample_size_n=snap_data["metrics"]["sample_size_n"],
            hit_rate=snap_data["metrics"]["hit_rate"],
        )

        # Verify Tamper Detection Hash
        expected_hash = ExperimentSnapshot.compute_sha256(exp_id, ds, tech, cal, metrics)
        if snap_data["snapshot_sha256_hash"] != expected_hash:
            raise ValueError(
                f"Tamper detection failed! Snapshot hash '{snap_data['snapshot_sha256_hash']}' "
                f"does not match expected payload hash '{expected_hash}'."
            )

        snapshot = ExperimentSnapshot(
            snapshot_id=snap_data["snapshot_id"],
            experiment_id=exp_id,
            parent_snapshot_id=snap_data.get("parent_snapshot_id"),
            timestamp=datetime.fromisoformat(snap_data["timestamp"]),
            schema_version=snap_data.get("schema_version", "1.0"),
            dataset=ds,
            techniques=tech,
            calibration=cal,
            orchestrator=orch,
            metrics=metrics,
            execution_params=snap_data.get("execution_params", {}),
            snapshot_sha256_hash=snap_data["snapshot_sha256_hash"],
        )

        self._SNAPSHOTS[exp_id].append(snapshot)
        return snapshot
