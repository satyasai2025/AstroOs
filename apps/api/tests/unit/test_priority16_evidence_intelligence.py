"""
Unit & Integration Tests for Priority 16 — Research Knowledge & Evidence Intelligence Engine
"""

import pytest
from fastapi.testclient import TestClient

from apps.api.domain.evidence_intelligence import EvidenceGrade
from apps.api.main import app
from apps.api.services.evidence_intelligence_engine import EvidenceIntelligenceEngine


def test_evidence_intelligence_engine_queries():
    """Verify EvidenceIntelligenceEngine returns ranked techniques, grades, synergies, and conditions."""
    engine = EvidenceIntelligenceEngine()

    # 1. Query Marriage Evidence
    rep_marriage = engine.query_evidence_report("marriage")
    assert rep_marriage.target_objective == "marriage"
    assert rep_marriage.total_techniques_evaluated >= 4
    assert rep_marriage.grade_a_count >= 2
    assert len(rep_marriage.top_synergies) >= 2
    assert rep_marriage.top_synergies[0].is_synergy_confirmed is True
    assert len(rep_marriage.key_condition_rules) >= 3

    # 2. Query with Grade filter
    rep_filtered = engine.query_evidence_report("marriage", min_confidence_grade=EvidenceGrade.GRADE_A_RIGOROUS)
    assert all(t.confidence_grade == EvidenceGrade.GRADE_A_RIGOROUS for t in rep_filtered.ranked_techniques)

    # 3. Query Career Evidence
    rep_career = engine.query_evidence_report("career")
    assert rep_career.target_objective == "career"
    assert len(rep_career.top_synergies) >= 1
    assert rep_career.top_synergies[0].statistical_lift_percent > 0.0


def test_evidence_intelligence_fastapi_endpoints():
    """Verify FastAPI router endpoints for Evidence Intelligence queries, synergies, and conditions."""
    client = TestClient(app)

    # 1. Test POST /api/v1/research/evidence/query
    res_query = client.post(
        "/api/v1/research/evidence/query",
        json={"target_objective": "marriage", "min_confidence_grade": "GRADE_A_RIGOROUS"},
    )
    assert res_query.status_code == 200
    data_query = res_query.json()
    assert data_query["target_objective"] == "marriage"
    assert data_query["grade_a_count"] >= 2
    assert len(data_query["ranked_techniques"]) >= 2
    assert len(data_query["top_synergies"]) >= 1

    # 2. Test GET /api/v1/research/evidence/synergies
    res_syn = client.get("/api/v1/research/evidence/synergies?objective=marriage")
    assert res_syn.status_code == 200
    data_syn = res_syn.json()
    assert len(data_syn) >= 2
    assert data_syn[0]["synergy_multiplier"] > 1.0

    # 3. Test GET /api/v1/research/evidence/conditions
    res_cond = client.get("/api/v1/research/evidence/conditions?objective=marriage")
    assert res_cond.status_code == 200
    data_cond = res_cond.json()
    assert len(data_cond) >= 3
    assert any(c["condition_type"] == "AMPLIFIER" for c in data_cond)
    assert any(c["condition_type"] == "ATTENUATOR" for c in data_cond)
