"""
AstroOS — Phase 6 Payment HTTP Endpoints API Tests
"""

from __future__ import annotations

import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import (
    get_current_user_from_bearer,
    get_db_session,
    require_admin,
)
from apps.api.domain.user import User, UserId, UserRole, UserStatus
from apps.api.main import app
from apps.api.services.payment.mock_provider import MockPaymentProvider
from apps.api.services.payment_service import PaymentService
from apps.api.tests.conftest import make_user


@pytest.fixture
def mock_user():
    return make_user(email="api_user@astroos.dev", role=UserRole.RESEARCHER)


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


def test_payment_config_endpoint(client):
    res = client.get("/api/v1/payments/config")
    assert res.status_code == 200
    data = res.json()
    assert "active_provider" in data
    assert "supported_providers" in data
    assert "mock" in data["supported_providers"]


def test_payment_checkout_endpoint(client, monkeypatch, mock_user):
    async def _fake_checkout(self, user, req):
        from apps.api.schemas.payment import CheckoutSessionResponse
        return CheckoutSessionResponse(
            session_id="mock_cs_api_test",
            checkout_url="https://astroos.local/checkout/mock_cs_api_test",
            provider="mock",
            amount=1900,
            currency="USD",
            plan_code="PRO",
        )

    monkeypatch.setattr(PaymentService, "initiate_checkout", _fake_checkout)

    res = client.post(
        "/api/v1/payments/checkout",
        json={"plan_code": "PRO", "billing_cycle": "monthly"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["session_id"] == "mock_cs_api_test"
    assert data["amount"] == 1900
    assert data["provider"] == "mock"


def test_payment_portal_endpoint(client, monkeypatch):
    async def _fake_portal(self, user, req):
        from apps.api.schemas.payment import CustomerPortalResponse
        return CustomerPortalResponse(
            portal_url="https://astroos.local/portal/mock_cus_api_test",
            provider="mock",
        )

    monkeypatch.setattr(PaymentService, "initiate_portal", _fake_portal)

    res = client.post(
        "/api/v1/payments/portal",
        json={"return_url": "http://localhost:3000/settings"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "portal_url" in data
    assert data["provider"] == "mock"


def test_payment_history_endpoint(client, monkeypatch):
    async def _fake_history(self, user_id, limit=50, offset=0):
        from apps.api.schemas.payment import PaymentHistoryResponse
        return PaymentHistoryResponse(items=[], total=0)

    monkeypatch.setattr(PaymentService, "list_user_payments", _fake_history)

    res = client.get("/api/v1/payments/history")
    assert res.status_code == 200
    data = res.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_payment_webhook_endpoint(client, monkeypatch):
    async def _fake_webhook(self, provider_name, payload_bytes, headers):
        from apps.api.schemas.payment import WebhookProcessingResult
        return WebhookProcessingResult(
            status="processed",
            provider=provider_name,
            event_id="evt_api_test_001",
            event_type="checkout.session.completed",
            message="Webhook event processed successfully.",
        )

    monkeypatch.setattr(PaymentService, "process_webhook", _fake_webhook)

    res = client.post(
        "/api/v1/payments/webhook/mock",
        json={"id": "evt_api_test_001", "event_type": "checkout.session.completed"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "processed"
    assert data["event_id"] == "evt_api_test_001"


def test_admin_payments_endpoint(client, monkeypatch):
    async def _fake_all_payments(self, status=None, provider=None, limit=50, offset=0):
        return []

    monkeypatch.setattr(PaymentService, "list_all_payments", _fake_all_payments)

    res = client.get("/api/v1/admin/payments")
    assert res.status_code == 200
    assert res.json() == []
