"""
Unit & Integration Tests for Priority 19 — Research Discovery & Hypothesis Mining Engine
"""

import pytest
from fastapi.testclient import TestClient

from apps.api.domain.hypothesis_mining import HypothesisStatus
from apps.api.main import app
from apps.api.services.hypothesis_mining_engine import HypothesisMiningEngine


def test_hypothesis_mining_engine_pattern_extraction_and_replication():
    """Verify HypothesisMiningEngine extracts combinations, applies FDR control, and validates on holdout."""
    engine = HypothesisMiningEngine.get_instance()

    report = engine.run_hypothesis_mining(
        discovery_dataset_id="ds-marriage-28",
        holdout_dataset_id="ds-marriage-100",
        target_objective="marriage",
        min_support_percent=15.0,
        min_statistical_lift=1.35,
        max_fdr_q_value=0.05,
    )

    assert report is not None
    assert report.total_combinations_evaluated > 0
    assert report.candidate_hypotheses_count >= 3
    assert report.replicated_validated_count >= 2
    assert len(report.top_hypotheses) >= 3

    # Check top hypothesis multi-criteria validation
    top_hypo = report.top_hypotheses[0]
    assert top_hypo.status == HypothesisStatus.REPLICATED_VALIDATED
    assert top_hypo.discovery_statistical_lift >= 1.35
    assert top_hypo.discovery_fdr_q_value <= 0.05
    assert len(top_hypo.pattern_primitives) >= 2
    assert len(top_hypo.replication_records) == 1
    assert top_hypo.replication_records[0].is_replication_confirmed is True
    assert len(top_hypo.lineage_snapshot_id) > 0


def test_hypothesis_mining_fastapi_endpoints():
    """Verify FastAPI router endpoints for triggering mining and querying discovered hypotheses."""
    client = TestClient(app)

    # 1. Run Mining
    res_mine = client.post(
        "/api/v1/research/mining/mine",
        json={
            "discovery_dataset_id": "ds-marriage-28",
            "holdout_dataset_id": "ds-marriage-100",
            "target_objective": "marriage",
            "min_support_percent": 15.0,
            "min_statistical_lift": 1.35,
            "max_fdr_q_value": 0.05,
        },
    )
    assert res_mine.status_code == 200
    data_mine = res_mine.json()
    assert data_mine["replicated_validated_count"] >= 2
    top_hypo = data_mine["top_hypotheses"][0]
    hypo_id = top_hypo["hypothesis_id"]

    # 2. List Hypotheses
    res_list = client.get("/api/v1/research/mining/hypotheses?objective=marriage")
    assert res_list.status_code == 200
    data_list = res_list.json()
    assert len(data_list) >= 3

    # 3. Get Specific Hypothesis
    res_get = client.get(f"/api/v1/research/mining/hypotheses/{hypo_id}")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["hypothesis_id"] == hypo_id
    assert data_get["status"] == "REPLICATED_VALIDATED"
    assert len(data_get["replication_records"]) == 1
