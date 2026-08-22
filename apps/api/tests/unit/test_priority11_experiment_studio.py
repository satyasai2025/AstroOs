"""
AstroOS — Priority 11: Unit & Integration Tests for Experiment Lineage,
Versioning, Immutability, Tamper Detection & Comparative Diff Engine
"""

import json
import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import require_authenticated
from apps.api.domain.experiment_lineage import (
    CalibrationProvenanceSnapshot,
    DatasetProvenanceSnapshot,
    ExperimentMetrics,
    OrchestratorConfigSnapshot,
    TechniqueProvenanceSnapshot,
)
from apps.api.main import app
from apps.api.services.experiment_service import ExperimentRegistry


@pytest.fixture
def api_client():
    app.dependency_overrides[require_authenticated] = lambda: {"sub": "exp_tester"}
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_create_experiment_and_metadata():
    reg = ExperimentRegistry.get_instance()
    exp = reg.create_experiment(
        name="Test Marriage Model Experiment",
        description="Testing Parashari vs Jaimini",
        author="Dr. Raman",
        tags=("test", "marriage"),
    )
    assert exp.experiment_id.startswith("exp-")
    assert exp.name == "Test Marriage Model Experiment"
    assert exp.status == "ACTIVE"


def test_freeze_snapshot_and_sha256_hashing():
    reg = ExperimentRegistry.get_instance()
    exp = reg.create_experiment("Snapshot Hash Experiment", "Hash verification")

    ds = DatasetProvenanceSnapshot(
        dataset_id="ds-test-100",
        dataset_version="1.0",
        sha256_hash="hash-ds-12345",
        record_count=100,
    )
    tech = TechniqueProvenanceSnapshot(
        dsl_rule_ids=("rule-01",),
        dsl_hashes=("hash-rule-01",),
        classical_techniques=("dasha",),
        combined_sha256_hash="hash-tech-12345",
    )
    cal = CalibrationProvenanceSnapshot(
        profile_id="prof-01",
        status="DRAFT_CANDIDATE",
        technique_weights={"w1": 0.8},
        primary_brier_score=0.05,
        primary_log_loss=0.15,
        sha256_hash="hash-cal-12345",
    )
    orch = OrchestratorConfigSnapshot("prof-01", 60, 1.2)
    metrics = ExperimentMetrics(0.05, 0.15, 0.85, 0.80, 0.825, 0.90, "VALID", 30, 0.85)

    snap = reg.freeze_snapshot(exp.experiment_id, ds, tech, cal, orch, metrics)
    assert snap.snapshot_id.startswith("snap-")
    assert len(snap.snapshot_sha256_hash) == 64  # Valid SHA-256 length


def test_immutable_snapshot_append_only():
    reg = ExperimentRegistry.get_instance()
    exp = reg.create_experiment("Append Only Experiment", "Immutability check")

    ds = DatasetProvenanceSnapshot("ds-1", "1.0", "h-ds", 50)
    tech = TechniqueProvenanceSnapshot(("r1",), ("h-r1",), ("t1",), "h-tech")
    cal = CalibrationProvenanceSnapshot("p1", "ACTIVE", {"w": 0.5}, 0.1, 0.2, "h-cal")
    orch = OrchestratorConfigSnapshot("p1", 50, 1.0)
    metrics = ExperimentMetrics(0.1, 0.2, 0.8, 0.8, 0.8, 0.85, "VALID", 20, 0.8)

    s1 = reg.freeze_snapshot(exp.experiment_id, ds, tech, cal, orch, metrics)
    s2 = reg.freeze_snapshot(exp.experiment_id, ds, tech, cal, orch, metrics, parent_snapshot_id=s1.snapshot_id)

    lineage = reg.get_lineage(exp.experiment_id)
    assert lineage is not None
    assert len(lineage.snapshots) == 2
    assert s2.parent_snapshot_id == s1.snapshot_id


def test_compare_experiments_and_metric_deltas():
    reg = ExperimentRegistry.get_instance()
    exp1 = reg.create_experiment("Exp 1", "Baseline")
    exp2 = reg.create_experiment("Exp 2", "Improved Model")

    ds1 = DatasetProvenanceSnapshot("ds-1", "1.0", "hash-ds-1", 100)
    ds2 = DatasetProvenanceSnapshot("ds-1", "1.0", "hash-ds-1", 100)

    tech1 = TechniqueProvenanceSnapshot(("r1",), ("hr1",), ("t1",), "htech-1")
    tech2 = TechniqueProvenanceSnapshot(("r1", "r2"), ("hr1", "hr2"), ("t1",), "htech-2")

    cal1 = CalibrationProvenanceSnapshot("p1", "ACTIVE", {"w1": 0.5}, 0.08, 0.20, "hcal-1")
    cal2 = CalibrationProvenanceSnapshot("p2", "ACTIVE", {"w1": 0.8}, 0.04, 0.12, "hcal-2")

    orch = OrchestratorConfigSnapshot("p1", 60, 1.2)

    m1 = ExperimentMetrics(0.08, 0.20, 0.75, 0.70, 0.724, 0.80, "VALID", 30, 0.75)
    m2 = ExperimentMetrics(0.04, 0.12, 0.88, 0.85, 0.865, 0.92, "VALID", 30, 0.88)

    s1 = reg.freeze_snapshot(exp1.experiment_id, ds1, tech1, cal1, orch, m1)
    s2 = reg.freeze_snapshot(exp2.experiment_id, ds2, tech2, cal2, orch, m2)

    diff = reg.compare_snapshots(exp1.experiment_id, s1.snapshot_id, exp2.experiment_id, s2.snapshot_id)

    assert diff.dataset_changed is False
    assert diff.rules_changed is True
    assert diff.weights_changed is True

    # Check Brier Score improvement (0.04 - 0.08 = -0.04)
    brier_delta = next(d for d in diff.metric_deltas if "Brier" in d.metric_name)
    assert brier_delta.improvement_status == "IMPROVED"
    assert brier_delta.absolute_delta == -0.04


def test_export_and_import_snapshot_bundle():
    reg = ExperimentRegistry.get_instance()
    exp = reg.create_experiment("Export Test Exp", "Exportability check")

    ds = DatasetProvenanceSnapshot("ds-exp", "1.0", "hash-ds-exp", 80)
    tech = TechniqueProvenanceSnapshot(("rule-exp",), ("hash-rule",), ("t1",), "hash-tech-exp")
    cal = CalibrationProvenanceSnapshot("p-exp", "ACTIVE", {"w": 0.7}, 0.06, 0.16, "hash-cal-exp")
    orch = OrchestratorConfigSnapshot("p-exp", 60, 1.0)
    metrics = ExperimentMetrics(0.06, 0.16, 0.82, 0.80, 0.81, 0.88, "VALID", 25, 0.82)

    s = reg.freeze_snapshot(exp.experiment_id, ds, tech, cal, orch, metrics)

    json_bundle = reg.export_snapshot_json(exp.experiment_id, s.snapshot_id)
    assert "AstroOS_Experiment_Snapshot_Bundle" in json_bundle

    imported_snap = reg.import_snapshot_json(json_bundle)
    assert imported_snap.snapshot_id == s.snapshot_id
    assert imported_snap.snapshot_sha256_hash == s.snapshot_sha256_hash


def test_tamper_detection_on_import():
    reg = ExperimentRegistry.get_instance()
    exp = reg.create_experiment("Tamper Detection Exp", "Security check")

    ds = DatasetProvenanceSnapshot("ds-sec", "1.0", "hash-ds-sec", 50)
    tech = TechniqueProvenanceSnapshot(("r-sec",), ("hr-sec",), ("t1",), "htech-sec")
    cal = CalibrationProvenanceSnapshot("p-sec", "ACTIVE", {"w": 0.5}, 0.10, 0.30, "hcal-sec")
    orch = OrchestratorConfigSnapshot("p-sec", 50, 1.0)
    metrics = ExperimentMetrics(0.10, 0.30, 0.70, 0.70, 0.70, 0.75, "VALID", 20, 0.70)

    s = reg.freeze_snapshot(exp.experiment_id, ds, tech, cal, orch, metrics)
    json_bundle = reg.export_snapshot_json(exp.experiment_id, s.snapshot_id)

    # Tamper with Brier Score in JSON without updating sha256_hash
    data = json.loads(json_bundle)
    data["snapshot"]["metrics"]["brier_score"] = 0.001  # Fabricated score!

    tampered_bundle = json.dumps(data)

    with pytest.raises(ValueError, match="Tamper detection failed"):
        reg.import_snapshot_json(tampered_bundle)


def test_api_endpoints_integration(api_client):
    # 1. Create Experiment
    create_resp = api_client.post(
        "/api/v1/research/experiments/",
        json={
            "name": "API Test Marriage Model",
            "description": "API integration verification",
            "author": "Tester",
            "tags": ["api", "marriage"],
        },
    )
    assert create_resp.status_code == 201
    exp_id = create_resp.json()["experiment_id"]

    # 2. Freeze Snapshot
    freeze_resp = api_client.post(
        f"/api/v1/research/experiments/{exp_id}/snapshots",
        json={
            "dataset_id": "ds-api-100",
            "dataset_version": "1.0",
            "record_count": 100,
            "dataset_hash": "hash-api-ds",
            "dsl_rule_ids": ["rule-api-1"],
            "classical_techniques": ["vimshottari"],
            "calibration_profile_id": "prof-api-1",
            "calibration_status": "ACTIVE",
            "technique_weights": {"natal": 0.8},
            "primary_brier_score": 0.05,
            "primary_log_loss": 0.15,
            "precision": 0.85,
            "recall": 0.80,
            "f1_score": 0.825,
            "roc_auc": 0.90,
            "roc_auc_status": "VALID",
            "sample_size_n": 30,
            "hit_rate": 0.85,
        },
    )
    assert freeze_resp.status_code == 201
    snap_id = freeze_resp.json()["snapshot_id"]

    # 3. Get Experiment & Lineage
    get_resp = api_client.get(f"/api/v1/research/experiments/{exp_id}")
    assert get_resp.status_code == 200
    assert len(get_resp.json()["snapshots"]) >= 1

    # 4. Compare Baseline vs API Experiment
    baseline_resp = api_client.get("/api/v1/research/experiments/exp-parashari-baseline")
    assert baseline_resp.status_code == 200
    baseline_snap_id = baseline_resp.json()["snapshots"][0]["snapshot_id"]

    compare_resp = api_client.post(
        "/api/v1/research/experiments/compare",
        json={
            "exp1_id": "exp-parashari-baseline",
            "snapshot1_id": baseline_snap_id,
            "exp2_id": exp_id,
            "snapshot2_id": snap_id,
        },
    )
    assert compare_resp.status_code == 200
    comp_json = compare_resp.json()
    assert len(comp_json["metric_deltas"]) >= 4
