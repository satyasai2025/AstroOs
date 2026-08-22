"""
Unit & Integration Tests for Priority 22 — Research Reproducibility & Independent Validation Engine
"""

import pytest
from fastapi.testclient import TestClient

from apps.api.domain.research_reproducibility import ReproducibilityStatus
from apps.api.main import app
from apps.api.services.research_reproducibility_engine import ResearchReproducibilityEngine


def test_reproducibility_engine_manifest_and_re_execution():
    """Verify ResearchReproducibilityEngine creates frozen manifests and independently re-executes computations."""
    engine = ResearchReproducibilityEngine.get_instance()

    # 1. Verify Manifests List
    manifests = engine.list_manifests()
    assert len(manifests) >= 2
    m1 = engine.get_manifest("man-p15-marriage")
    assert m1 is not None
    assert len(m1.manifest_sha256_hash) == 64

    # 2. Independently Re-Execute P15 Manifest
    audit = engine.re_execute_manifest("man-p15-marriage")
    assert audit is not None
    assert audit.status == ReproducibilityStatus.REPRODUCED
    assert audit.reproducibility_score_percent == 100.0
    assert len(audit.metric_diffs) >= 2
    assert all(d.is_exact_match for d in audit.metric_diffs)
    assert len(audit.independent_repro_snapshot_id) > 0


def test_reproducibility_fastapi_endpoints():
    """Verify FastAPI router endpoints for reproducibility manifests and re-execution audits."""
    client = TestClient(app)

    # 1. List Manifests
    res_list = client.get("/api/v1/research/reproducibility/manifests")
    assert res_list.status_code == 200
    data_list = res_list.json()
    assert len(data_list) >= 2

    # 2. Get Specific Manifest
    res_get = client.get("/api/v1/research/reproducibility/manifests/man-p15-marriage")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["manifest_id"] == "man-p15-marriage"

    # 3. Create Custom Manifest
    res_create = client.post(
        "/api/v1/research/reproducibility/manifests",
        json={
            "target_engine_priority": "P15_COHORT",
            "target_objective": "marriage",
            "dataset_id": "ds-marriage-28",
            "astrological_formula": 'DASHA == "7th_Lord" AND SAV_SCORE >= 28',
            "frozen_thresholds": {"min_sav": 28.0},
            "random_seed": 42,
            "monte_carlo_iterations": 50,
            "baseline_metrics": {"roc_auc": 0.9996, "permutation_p_value": 0.01961},
            "author": "Tester",
        },
    )
    assert res_create.status_code == 200
    created_data = res_create.json()
    created_id = created_data["manifest_id"]
    assert len(created_data["manifest_sha256_hash"]) == 64

    # 4. Re-Execute Manifest
    res_exec = client.post(
        "/api/v1/research/reproducibility/reproduce",
        json={"manifest_id": created_id},
    )
    assert res_exec.status_code == 200
    exec_data = res_exec.json()
    assert exec_data["status"] == "REPRODUCED"
    assert exec_data["reproducibility_score_percent"] == 100.0
