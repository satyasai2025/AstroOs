"""
Unit & Integration Tests for Priority 23 — Research Decision & Evidence Synthesis Engine
"""

import pytest
from fastapi.testclient import TestClient

from apps.api.domain.decision_synthesis import (
    EpistemicRuleType,
    EvidenceConfidenceTier,
)
from apps.api.main import app
from apps.api.services.decision_synthesis_engine import ResearchDecisionSynthesisEngine


def test_decision_synthesis_engine_evaluation():
    """Verify ResearchDecisionSynthesisEngine evaluates technique strength, conflicts, and P1-P22 lineage."""
    engine = ResearchDecisionSynthesisEngine.get_instance()

    # 1. Synthesize Research Decision
    conclusion = engine.synthesize_research_decision(target_objective="marriage")
    assert conclusion is not None
    assert conclusion.confidence_tier == EvidenceConfidenceTier.TIER_1_PUBLICATION_GRADE
    assert conclusion.synthesized_confidence_score >= 0.85
    assert len(conclusion.strongest_techniques) >= 3

    # 2. Verify Epistemic Separation
    types_found = {t.epistemic_type for t in conclusion.strongest_techniques}
    assert EpistemicRuleType.CLASSICAL_CANONICAL_RULE in types_found
    assert EpistemicRuleType.EMPIRICALLY_SUPPORTED_PROSPECTIVE_RULE in types_found
    assert EpistemicRuleType.DISCOVERED_HYPOTHESIS in types_found

    # 3. Verify Contradiction / Conflict Radar
    assert len(conclusion.conflicts_detected) >= 1
    assert conclusion.conflicts_detected[0].epistemic_arbitration == "TIMING_DOMINATES_CAPACITY"

    # 4. Verify Unbroken P1 to P22 Lineage Trace
    assert len(conclusion.p1_to_p22_lineage_trace) >= 22
    assert "P1_EPHEMERIS" in conclusion.p1_to_p22_lineage_trace
    assert "P22_REPRODUCIBILITY" in conclusion.p1_to_p22_lineage_trace


def test_decision_synthesis_fastapi_endpoints():
    """Verify FastAPI router endpoints for decision synthesis."""
    client = TestClient(app)

    # 1. Synthesize via POST
    res_post = client.post(
        "/api/v1/research/decision-synthesis/synthesize",
        json={"target_objective": "marriage", "include_lineage": True},
    )
    assert res_post.status_code == 200
    data = res_post.json()
    assert data["confidence_tier"] == "TIER_1_PUBLICATION_GRADE"
    assert data["synthesized_confidence_score"] >= 0.85
    assert len(data["strongest_techniques"]) >= 3
    assert len(data["conflicts_detected"]) >= 1
    assert len(data["p1_to_p22_lineage_trace"]) >= 22

    cid = data["conclusion_id"]

    # 2. List Conclusions
    res_list = client.get("/api/v1/research/decision-synthesis/conclusions")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # 3. Get Specific Conclusion
    res_get = client.get(f"/api/v1/research/decision-synthesis/conclusions/{cid}")
    assert res_get.status_code == 200
    assert res_get.json()["conclusion_id"] == cid
