"""
AstroOS — Phase 9 Account & User Dashboard API Tests
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import get_current_user_from_bearer, get_db_session
from apps.api.domain.user import UserRole
from apps.api.main import app
from apps.api.repositories.payment_repository import PaymentRepository
from apps.api.repositories.plan_repository import PlanRepository
from apps.api.repositories.subscription_repository import SubscriptionRepository
from apps.api.services.entitlement_service import EntitlementService
from apps.api.tests.conftest import make_user


@pytest.fixture
def mock_researcher():
    return make_user(email="practitioner@astroos.dev", role=UserRole.RESEARCHER)


@pytest.fixture
def client(mock_researcher):
    class _FakeAsyncSession:
        async def execute(self, query):
            from types import SimpleNamespace
            return SimpleNamespace(scalar_one=lambda: 3)

    async def _override_get_db():
        yield _FakeAsyncSession()

    app.dependency_overrides[get_db_session] = _override_get_db
    app.dependency_overrides[get_current_user_from_bearer] = lambda: mock_researcher

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_get_dashboard_summary_endpoint(client, monkeypatch, mock_researcher):
    from types import SimpleNamespace

    async def _fake_user_plan(self, user):
        return SimpleNamespace(
            plan_code="PRO",
            name="Professional Astrologer",
            limits={"saved_horoscopes": 50, "research_projects_monthly": 1, "max_storage_mb": 500},
            features={"can_view": True, "can_create": True, "can_edit": True, "can_run": True, "can_export": True},
        )

    async def _fake_sub(db, user_id):
        return SimpleNamespace(
            status="active",
            current_period_start=None,
            current_period_end=None,
        )

    async def _fake_payments(db, user_id, limit=5):
        return []

    async def _fake_count(db, user_id):
        return 0

    monkeypatch.setattr(EntitlementService, "resolve_user_plan", _fake_user_plan)
    monkeypatch.setattr(SubscriptionRepository, "get_by_user", _fake_sub)
    monkeypatch.setattr(PaymentRepository, "list_by_user", _fake_payments)
    monkeypatch.setattr(PaymentRepository, "count_by_user", _fake_count)

    res = client.get("/api/v1/dashboard/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "practitioner@astroos.dev"
    assert data["plan_code"] == "PRO"
    assert data["plan_name"] == "Professional Astrologer"
    assert data["subscription_status"] == "active"
    assert data["saved_horoscopes_limit"] == 50
    assert data["research_runs_limit"] == 1
    assert data["saved_horoscopes_count"] == 3
