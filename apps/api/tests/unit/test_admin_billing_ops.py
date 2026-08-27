"""
AstroOS — Phase 13 Admin / Ops / Billing Console Tests
"""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import get_current_user_from_bearer, get_db_session
from apps.api.routers.admin_auth import require_admin_token
from apps.api.domain.user import UserRole
from apps.api.main import app
from apps.api.models.payment import PaymentStatus
from apps.api.tests.conftest import make_user


@pytest.fixture
def mock_admin():
    return make_user(email="admin@astroos.dev", role=UserRole.ADMIN)


@pytest.fixture
def client_admin(mock_admin):
    class _FakeSession:
        async def execute(self, query):
            class _Result:
                def scalars(self):
                    return SimpleNamespace(all=lambda: [])
                def scalar_one(self):
                    return 0
                def scalar_one_or_none(self):
                    return SimpleNamespace(
                        id=uuid4(),
                        status=PaymentStatus.SUCCEEDED.value,
                        user_id=mock_admin.id.value,
                        plan_code="PRO",
                        amount=235882,
                        base_amount=199900,
                        tax_amount=35982,
                        tax_rate=18.0,
                        currency="INR",
                        provider="razorpay",
                        billing_cycle="monthly",
                        provider_payment_id="pay_123",
                        provider_order_id="order_123",
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
            return _Result()

        async def commit(self):
            pass

        async def refresh(self, obj):
            pass

    app.dependency_overrides[get_db_session] = lambda: _FakeSession()
    app.dependency_overrides[get_current_user_from_bearer] = lambda: mock_admin
    app.dependency_overrides[require_admin_token] = lambda: {"sub": "admin", "role": "ADMIN"}

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_admin_list_payments(client_admin):
    res = client_admin.get("/api/v1/admin/billing/payments")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data


def test_admin_list_subscriptions(client_admin):
    res = client_admin.get("/api/v1/admin/billing/subscriptions")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data


def test_admin_refund_payment(client_admin):
    test_id = uuid4()
    res = client_admin.post(f"/api/v1/admin/billing/refunds/{test_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "refunded"
    assert data["currency"] == "INR"


def test_admin_list_email_logs(client_admin):
    res = client_admin.get("/api/v1/admin/notifications/logs")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
