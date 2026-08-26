"""
Unit tests for Knowledge Reliability FastAPI Router endpoints.
"""

import uuid
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.routers import knowledge_reliability


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(knowledge_reliability.router, prefix="/api/v1")
    return TestClient(app)


def test_source_registration_and_retrieval(client: TestClient):
    source_id = str(uuid.uuid4())
    req_body = {
        "source_id": source_id,
        "source_name": "Phaladeepika (Mantreswara)",
        "tier": "AUTHENTICATED_CLASSICAL",
        "provenance": {
            "edition_title": "Phaladeepika English Translation",
            "publisher": "Motilal Banarsidass",
            "publication_year": 1950,
            "editor_or_translator": "V. Subrahmanya Sastri",
            "is_critical_edition": True,
        },
        "scholarly_eval": {
            "tradition": "Classical / Mantreswara",
            "methodology_clarity_notes": "Celebrated 13th century classic.",
            "primary_commentaries": ["Gopesh Kumar Ojha commentary"],
            "known_disputed_passages": [],
        },
        "review_status": "PEER_REVIEWED",
        "empirical_citations": ["BENCH-CAREER-001"],
        "known_failures_or_contradictions": [],
    }

    res_post = client.post("/api/v1/knowledge/reliability/sources/register", json=req_body)
    assert res_post.status_code == 201
    data = res_post.json()
    assert data["source_name"] == "Phaladeepika (Mantreswara)"
    assert data["tier"] == "AUTHENTICATED_CLASSICAL"

    res_get = client.get(f"/api/v1/knowledge/reliability/sources/{source_id}")
    assert res_get.status_code == 200
    get_data = res_get.json()
    assert get_data["source_id"] == source_id


def test_rule_documentation_and_lifecycle_transitions(client: TestClient):
    source_id = str(uuid.uuid4())
    # 1. Register Source
    client.post(
        "/api/v1/knowledge/reliability/sources/register",
        json={
            "source_id": source_id,
            "source_name": "Saravali",
            "tier": "AUTHENTICATED_CLASSICAL",
            "provenance": {"edition_title": "Saravali", "publisher": "Ranjan", "publication_year": 1983},
            "scholarly_eval": {"tradition": "Parashari", "methodology_clarity_notes": "Kalyanavarma's classic."},
        },
    )

    # 2. Document Rule (AI Extractor)
    rule_id = f"RULE-SARAVALI-{uuid.uuid4().hex[:6]}"
    doc_res = client.post(
        "/api/v1/knowledge/reliability/rules/document",
        json={
            "rule_id": rule_id,
            "rule_name": "Venus in 12th House Exaltation Dignity",
            "technique_framework": "Parashari",
            "source_id": source_id,
            "passage_reference": "Saravali Chapter 28, Sloka 12",
            "original_text_excerpt": "vyaye shukra sthite...",
            "extracted_by_actor_id": "ai-bot",
            "extracted_by_role": "AI_AGENT",
            "rule_definition_id": "DEF-VENUS-12H",
            "extraction_method": "AI_ASSISTED_EXTRACTION",
        },
    )
    assert doc_res.status_code == 201
    rule_data = doc_res.json()
    assert rule_data["lifecycle_state"] == "DOCUMENTED"
    assert rule_data["evidence_level"] == "UNVALIDATED"

    # 3. AI Transition Attempt to REVIEWED -> Must be 403 Forbidden
    ai_trans = client.post(
        f"/api/v1/knowledge/reliability/rules/{rule_id}/transition",
        json={
            "target_state": "REVIEWED",
            "actor_id": "ai-bot",
            "actor_role": "AI_AGENT",
        },
    )
    assert ai_trans.status_code == 403

    # 4. Human Expert Transition to REVIEWED -> Must succeed
    human_trans = client.post(
        f"/api/v1/knowledge/reliability/rules/{rule_id}/transition",
        json={
            "target_state": "REVIEWED",
            "actor_id": "expert-scholar",
            "actor_role": "HUMAN_EXPERT",
            "notes": "Reviewed and verified.",
        },
    )
    assert human_trans.status_code == 200
    assert human_trans.json()["lifecycle_state"] == "REVIEWED"

    # 5. Provenance Trace Endpoint
    trace_res = client.get(f"/api/v1/knowledge/reliability/rules/{rule_id}/provenance-trace")
    assert trace_res.status_code == 200
    assert trace_res.json()["passage_reference"] == "Saravali Chapter 28, Sloka 12"


def test_independent_confirmations_calculation(client: TestClient):
    fam_id = f"FAM-MANGAL-{uuid.uuid4().hex[:6]}"
    # Register family
    client.post(
        "/api/v1/knowledge/reliability/families/register",
        json={
            "family_id": fam_id,
            "name": "Kuja Dosha Placements",
            "underlying_principle": "Mars in 1, 2, 4, 7, 8, 12 from Lagna or Moon",
            "tradition": "Parashari",
            "member_rule_ids": ["RULE-KD-1H", "RULE-KD-4H", "RULE-KD-7H", "RULE-KD-8H"],
            "max_independent_dof": 1,
        },
    )

    calc_res = client.post(
        "/api/v1/knowledge/reliability/families/independent-confirmations",
        json={"rule_ids": ["RULE-KD-1H", "RULE-KD-4H", "RULE-KD-7H", "RULE-KD-8H", "RULE-UNRELATED-01"]},
    )
    assert calc_res.status_code == 200
    calc_data = calc_res.json()
    assert calc_data["total_rules_matched"] == 5
    assert calc_data["independent_confirmations_dof"] == 2
