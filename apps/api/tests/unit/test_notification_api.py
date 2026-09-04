"""
AstroOS — Phase 7 Notification API Endpoints Tests
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import (
    get_current_user_from_bearer,
    get_db_session,
    require_admin,
)
from apps.api.domain.user import UserRole
from apps.api.main import app
from apps.api.repositories.notification_repository import NotificationRepository
from apps.api.services.notification_service import NotificationService
from apps.api.tests.conftest import make_user


@pytest.fixture
def mock_user():
    return make_user(email="notify_user@astroos.dev", role=UserRole.RESEARCHER)


@pytest.fixture
def mock_admin():
    return make_user(email="admin@astroos.dev", role=UserRole.ADMIN)


@pytest.fixture
def client(mock_user, mock_admin):
    class _FakeAsyncSession:
        pass

    async def _override_get_db():
        yield _FakeAsyncSession()

    app.dependency_overrides[get_db_session] = _override_get_db
    app.dependency_overrides[get_current_user_from_bearer] = lambda: mock_user
    app.dependency_overrides[require_admin] = lambda: mock_admin

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_get_notification_preferences(client, monkeypatch, mock_user):
    from types import SimpleNamespace

    async def _fake_get_or_create(db, user_id):
        return SimpleNamespace(
            user_id=mock_user.id.value,
            billing_notifications=True,
            security_alerts=True,
            quota_warnings=True,
            product_updates=False,
        )

    monkeypatch.setattr(NotificationRepository, "get_or_create_preferences", _fake_get_or_create)

    res = client.get("/api/v1/notifications/preferences")
    assert res.status_code == 200
    data = res.json()
    assert data["billing_notifications"] is True
    assert data["security_alerts"] is True
    assert data["quota_warnings"] is True
    assert data["product_updates"] is False


def test_update_notification_preferences(client, monkeypatch, mock_user):
    from types import SimpleNamespace

    async def _fake_get_or_create(db, user_id):
        return SimpleNamespace(
            user_id=mock_user.id.value,
            billing_notifications=True,
            security_alerts=True,
            quota_warnings=True,
            product_updates=False,
        )

    async def _fake_update(db, pref, **kwargs):
        if kwargs.get("quota_warnings") is not None:
            pref.quota_warnings = kwargs["quota_warnings"]
        if kwargs.get("product_updates") is not None:
            pref.product_updates = kwargs["product_updates"]
        return pref

    monkeypatch.setattr(NotificationRepository, "get_or_create_preferences", _fake_get_or_create)
    monkeypatch.setattr(NotificationRepository, "update_preferences", _fake_update)

    res = client.put(
        "/api/v1/notifications/preferences",
        json={"quota_warnings": False, "product_updates": True},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["quota_warnings"] is False
    assert data["product_updates"] is True
    # Mandatory remains true
    assert data["billing_notifications"] is True


def test_get_notification_history(client, monkeypatch):
    async def _fake_list(db, user_id, limit=50, offset=0):
        return []

    async def _fake_count(db, user_id):
        return 0

    monkeypatch.setattr(NotificationRepository, "list_by_user", _fake_list)
    monkeypatch.setattr(NotificationRepository, "count_by_user", _fake_count)

    res = client.get("/api/v1/notifications/history")
    assert res.status_code == 200
    data = res.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_admin_notification_logs(client, monkeypatch):
    async def _fake_list_all(db, status=None, template_name=None, limit=50, offset=0):
        return []

    monkeypatch.setattr(NotificationRepository, "list_all", _fake_list_all)

    res = client.get("/api/v1/admin/notifications/logs")
    assert res.status_code == 200
    assert res.json() == []


def test_admin_test_email(client, monkeypatch):
    from types import SimpleNamespace

    async def _fake_send(self, to_email, template_name, context, idempotency_key, **kwargs):
        return SimpleNamespace(
            id=uuid4(),
            status="sent",
            provider="mock",
        )

    monkeypatch.setattr(NotificationService, "send_transactional_email", _fake_send)

    res = client.post(
        "/api/v1/admin/notifications/test",
        json={"to_email": "tester@astroos.dev", "template_name": "payment_success"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["template_name"] == "payment_success"
    assert data["recipient"] == "tester@astroos.dev"
