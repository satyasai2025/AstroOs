"""
AstroOS — Phase 12 Governed RAG & Astrological AI Tests
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import get_current_user_from_bearer, get_db_session
from apps.api.domain.user import UserRole
from apps.api.main import app
from apps.api.services.entitlement_service import EntitlementService
from apps.api.tests.conftest import make_user


@pytest.fixture
def mock_scholar():
    return make_user(email="scholar@astroos.dev", role=UserRole.RESEARCHER)


@pytest.fixture
def client(mock_scholar):
    class _FakeSession:
        pass

    app.dependency_overrides[get_db_session] = lambda: _FakeSession()
    app.dependency_overrides[get_current_user_from_bearer] = lambda: mock_scholar

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_governed_rag_free_tier(client, monkeypatch):
    async def _fake_plan(self, user):
        return SimpleNamespace(plan_code="FREE", name="Free Community")

    monkeypatch.setattr(EntitlementService, "resolve_user_plan", _fake_plan)

    res = client.post(
        "/api/v1/ai/governed-rag",
        json={"query": "Explain Gaja Kesari Yoga in detail"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["plan_tier"] == "FREE"
    assert "Brihat Parashara Hora Shastra" in data["provenance_citations"][0]["source"]
    assert data["technique_isolation_valid"] is True


def test_governed_rag_research_tier(client, monkeypatch):
    async def _fake_plan(self, user):
        return SimpleNamespace(plan_code="RESEARCH", name="Research Scholar")

    monkeypatch.setattr(EntitlementService, "resolve_user_plan", _fake_plan)

    res = client.post(
        "/api/v1/ai/governed-rag",
        json={"query": "Hamsa Mahapurusha yoga formation criteria"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["plan_tier"] == "RESEARCH"
    assert "Deep Claude 3.5 / Gemini" in data["ai_backend_used"]
    assert data["grounding_score"] >= 0.95
    assert len(data["provenance_citations"]) >= 1
