"""
AstroOS — Phase 10 Tiered Reports & Downloads Tests
"""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import get_current_user_from_bearer, get_db_session
from apps.api.domain.user import UserRole
from apps.api.main import app
from apps.api.repositories.report_history_repository import ReportHistoryRepository
from apps.api.services.entitlement_service import EntitlementService
from apps.api.tests.conftest import make_user


@pytest.fixture
def mock_free_user():
    return make_user(email="free_practitioner@astroos.dev", role=UserRole.RESEARCHER)


@pytest.fixture
def mock_pro_user():
    return make_user(email="pro_practitioner@astroos.dev", role=UserRole.RESEARCHER)


@pytest.fixture
def client_free(mock_free_user):
    class _FakeSession:
        pass

    app.dependency_overrides[get_db_session] = lambda: _FakeSession()
    app.dependency_overrides[get_current_user_from_bearer] = lambda: mock_free_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_free_user_generate_2page_report(client_free, monkeypatch, mock_free_user):
    async def _fake_user_plan(self, user):
        return SimpleNamespace(plan_code="FREE", name="Free Community")

    async def _fake_create_report(db, **kwargs):
        return SimpleNamespace(
            id=uuid4(),
            user_id=mock_free_user.id.value,
            chart_id=kwargs.get("chart_id"),
            subject_name=kwargs.get("subject_name", "Subject"),
            report_tier="free_2page",
            export_format="pdf",
            page_count=2,
            file_size_bytes=1500,
            download_url="/api/v1/reports/tiered/test/download",
            created_at="2026-08-27T12:00:00Z",
        )

    monkeypatch.setattr(EntitlementService, "resolve_user_plan", _fake_user_plan)
    monkeypatch.setattr(ReportHistoryRepository, "create_report", _fake_create_report)

    res = client_free.post(
        "/api/v1/reports/tiered/generate",
        json={"subject_name": "Test Subject", "report_tier": "free_2page"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["report_tier"] == "free_2page"
    assert data["page_count"] == 2


def test_free_user_pro_report_forbidden(client_free, monkeypatch):
    async def _fake_user_plan(self, user):
        return SimpleNamespace(plan_code="FREE", name="Free Community")

    monkeypatch.setattr(EntitlementService, "resolve_user_plan", _fake_user_plan)

    res = client_free.post(
        "/api/v1/reports/tiered/generate",
        json={"subject_name": "Test Subject", "report_tier": "pro_5page"},
    )
    assert res.status_code == 403
    assert "PRO or RESEARCH" in res.json()["detail"]


def test_pro_user_generate_5page_report(client_free, monkeypatch, mock_free_user):
    async def _fake_user_plan(self, user):
        return SimpleNamespace(plan_code="PRO", name="Professional Astrologer")

    async def _fake_create_report(db, **kwargs):
        return SimpleNamespace(
            id=uuid4(),
            user_id=mock_free_user.id.value,
            chart_id=kwargs.get("chart_id"),
            subject_name="Pro Subject",
            report_tier="pro_5page",
            export_format="pdf",
            page_count=5,
            file_size_bytes=4500,
            download_url="/api/v1/reports/tiered/test-pro/download",
            created_at="2026-08-27T12:00:00Z",
        )

    monkeypatch.setattr(EntitlementService, "resolve_user_plan", _fake_user_plan)
    monkeypatch.setattr(ReportHistoryRepository, "create_report", _fake_create_report)

    res = client_free.post(
        "/api/v1/reports/tiered/generate",
        json={"subject_name": "Pro Subject", "report_tier": "pro_5page"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["report_tier"] == "pro_5page"
    assert data["page_count"] == 5


def test_report_history_endpoint(client_free, monkeypatch):
    async def _fake_list(db, user_uuid, limit=20, offset=0):
        return []

    async def _fake_count(db, user_uuid):
        return 0

    monkeypatch.setattr(ReportHistoryRepository, "list_by_user", _fake_list)
    monkeypatch.setattr(ReportHistoryRepository, "count_by_user", _fake_count)

    res = client_free.get("/api/v1/reports/tiered/history")
    assert res.status_code == 200
    data = res.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_download_report_endpoint(client_free, monkeypatch):
    test_id = uuid4()

    async def _fake_get_by_id(db, report_id):
        return SimpleNamespace(
            id=test_id,
            report_tier="free_2page",
            subject_name="Alex",
            document_content="<html><body>AstroOS Report</body></html>",
        )

    monkeypatch.setattr(ReportHistoryRepository, "get_by_id", _fake_get_by_id)

    res = client_free.get(f"/api/v1/reports/tiered/{test_id}/download")
    assert res.status_code == 200
    assert "AstroOS Report" in res.text
    assert res.headers["content-type"].startswith("text/html")
