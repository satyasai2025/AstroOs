"""
AstroOS — Phase 11 Research Workspace & Project Quota Tests
"""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import get_current_user_from_bearer, get_db_session
from apps.api.domain.user import UserRole
from apps.api.main import app
from apps.api.repositories.research_repository import ResearchRepository
from apps.api.services.quota_service import QuotaService, QuotaStatus
from apps.api.tests.conftest import make_user


@pytest.fixture
def mock_researcher():
    return make_user(email="scholar@astroos.dev", role=UserRole.RESEARCHER)


@pytest.fixture
def client(mock_researcher):
    class _FakeSession:
        pass

    app.dependency_overrides[get_db_session] = lambda: _FakeSession()
    app.dependency_overrides[get_current_user_from_bearer] = lambda: mock_researcher

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_list_research_projects(client, monkeypatch, mock_researcher):
    async def _fake_list(db, user_uuid, status=None):
        return []

    monkeypatch.setattr(ResearchRepository, "list_projects", _fake_list)

    res = client.get("/api/v1/research/projects")
    assert res.status_code == 200
    data = res.json()
    assert "projects" in data
    assert data["projects"] == []


def test_create_research_project(client, monkeypatch, mock_researcher):
    proj_id = uuid4()

    async def _fake_quota(self, user, feature_key, amount=1):
        return QuotaStatus(
            allowed=True,
            current_usage=0,
            limit=10,
            period="2026-08",
            exhausted=False,
            reset_in=86400,
        )

    async def _fake_create(db, **kwargs):
        return SimpleNamespace(
            id=proj_id,
            user_id=mock_researcher.id.value,
            title="Gaja Kesari Cohort Study",
            description="Statistical study of Jupiter-Moon angular separation",
            status="active",
            created_at="2026-08-27T12:00:00Z",
            updated_at="2026-08-27T12:00:00Z",
        )

    async def _fake_consume(self, user, feature_key, amount=1):
        return True

    monkeypatch.setattr(QuotaService, "check_quota", _fake_quota)
    monkeypatch.setattr(QuotaService, "consume_quota", _fake_consume)
    monkeypatch.setattr(ResearchRepository, "create_project", _fake_create)

    res = client.post(
        "/api/v1/research/projects",
        json={
            "title": "Gaja Kesari Cohort Study",
            "description": "Statistical study of Jupiter-Moon angular separation",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Gaja Kesari Cohort Study"
    assert data["status"] == "active"
