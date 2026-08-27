"""
AstroOS — Phase 6 Payment Service & Webhook Orchestration Tests
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from apps.api.domain.user import User, UserId, UserRole, UserStatus
from apps.api.models.payment import PaymentModel, PaymentStatus
from apps.api.models.subscription import SubscriptionEventType, SubscriptionStatus
from apps.api.repositories.payment_repository import PaymentRepository
from apps.api.repositories.plan_repository import PlanRepository
from apps.api.repositories.subscription_repository import SubscriptionRepository
from apps.api.schemas.payment import (
    CheckoutSessionRequest,
    CustomerPortalRequest,
)
from apps.api.services.payment.mock_provider import MockPaymentProvider
from apps.api.services.payment_service import PaymentService

NOW = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)


class _MemDB:
    def __init__(self):
        self.plans = {
            "PRO": SimpleNamespace(id=uuid4(), plan_code="PRO", name="Pro", is_active=True),
            "RESEARCH": SimpleNamespace(id=uuid4(), plan_code="RESEARCH", name="Research", is_active=True),
            "FREE": SimpleNamespace(id=uuid4(), plan_code="FREE", name="Free", is_active=True),
            "INACTIVE": SimpleNamespace(id=uuid4(), plan_code="INACTIVE", name="Inactive", is_active=False),
        }
        self.subscriptions = {}
        self.sub_events = []
        self.payments = {}
        self.customers = {}
        self.webhook_events = {}

    def add(self, obj):
        if hasattr(obj, "id") and not getattr(obj, "id", None):
            obj.id = uuid4()
        if type(obj).__name__ == "PaymentModel":
            self.payments[obj.id] = obj
        elif type(obj).__name__ == "SubscriptionModel":
            self.subscriptions[obj.user_id] = obj
        elif type(obj).__name__ == "PaymentCustomerModel":
            self.customers[(obj.user_id, obj.provider)] = obj
        elif type(obj).__name__ == "PaymentWebhookEventModel":
            self.webhook_events[(obj.provider, obj.provider_event_id)] = obj
        elif type(obj).__name__ == "SubscriptionEventModel":
            self.sub_events.append(obj)

    async def commit(self):
        pass

    async def flush(self):
        pass

    async def refresh(self, obj):
        pass


@pytest.fixture
def mem_db(monkeypatch):
    db = _MemDB()

    async def _mock_get_by_code(session, code):
        return db.plans.get(code.upper())

    async def _mock_get_sub_by_user(session, user_id):
        return db.subscriptions.get(user_id)

    async def _mock_get_sub_by_id(session, sub_id):
        for s in db.subscriptions.values():
            if s.id == sub_id:
                return s
        return None

    async def _mock_create_sub(session, **kwargs):
        sub = SimpleNamespace(
            id=uuid4(),
            user_id=kwargs["user_id"],
            plan_id=kwargs["plan_id"],
            status=kwargs.get("status_value", "active"),
            current_period_start=kwargs.get("current_period_start", NOW),
            current_period_end=kwargs.get("current_period_end"),
            trial_end=kwargs.get("trial_end"),
            event_version=1,
            ended_at=None,
        )
        db.subscriptions[kwargs["user_id"]] = sub
        return sub

    async def _mock_append_event(session, **kwargs):
        ev = SimpleNamespace(
            id=uuid4(),
            subscription=kwargs["subscription"],
            event_type=kwargs["event_type"] if isinstance(kwargs["event_type"], str) else kwargs["event_type"].value,
            from_status=kwargs.get("from_status"),
            to_status=kwargs.get("to_status"),
            payload_json=kwargs.get("payload_json"),
            created_at=NOW,
        )
        db.sub_events.append(ev)
        return ev

    async def _mock_save_sub(session, sub):
        db.subscriptions[sub.user_id] = sub
        return sub

    async def _mock_update_fields(sub, **fields):
        for k, v in fields.items():
            setattr(sub, k, v)
        return sub

    async def _mock_get_customer(session, user_id, provider):
        return db.customers.get((user_id, provider))

    async def _mock_upsert_customer(session, **kwargs):
        cust = SimpleNamespace(
            id=uuid4(),
            user_id=kwargs["user_id"],
            provider=kwargs["provider"],
            provider_customer_id=kwargs["provider_customer_id"],
            metadata_json=None,
        )
        db.customers[(kwargs["user_id"], kwargs["provider"])] = cust
        return cust

    async def _mock_get_user_id_by_customer_id(session, provider, provider_customer_id):
        for (uid, prov), cust in db.customers.items():
            if prov == provider and cust.provider_customer_id == provider_customer_id:
                return uid
        return None

    async def _mock_create_payment(session, **kwargs):
        p = SimpleNamespace(
            id=uuid4(),
            user_id=kwargs["user_id"],
            plan_id=kwargs.get("plan_id"),
            subscription_id=kwargs.get("subscription_id"),
            amount=kwargs["amount"],
            currency=kwargs.get("currency", "USD"),
            provider=kwargs.get("provider", "mock"),
            status=kwargs.get("status_value", "pending"),
            provider_payment_id=kwargs.get("provider_payment_id"),
            provider_order_id=kwargs.get("provider_order_id"),
            payment_method=kwargs.get("payment_method"),
            receipt_url=kwargs.get("receipt_url"),
            payload_json=json.dumps(kwargs.get("payload")) if kwargs.get("payload") else None,
            error_message=kwargs.get("error_message"),
            created_at=NOW,
            updated_at=NOW,
        )
        db.payments[p.id] = p
        return p

    async def _mock_get_by_provider_order_id(session, order_id):
        for p in db.payments.values():
            if p.provider_order_id == order_id:
                return p
        return None

    async def _mock_get_by_provider_payment_id(session, provider, payment_id):
        for p in db.payments.values():
            if p.provider == provider and p.provider_payment_id == payment_id:
                return p
        return None

    async def _mock_update_payment_status(session, p, **kwargs):
        p.status = kwargs.get("status_value", p.status)
        if "provider_payment_id" in kwargs and kwargs["provider_payment_id"]:
            p.provider_payment_id = kwargs["provider_payment_id"]
        if "receipt_url" in kwargs and kwargs["receipt_url"]:
            p.receipt_url = kwargs["receipt_url"]
        return p

    async def _mock_is_event_processed(session, provider, event_id):
        return (provider, event_id) in db.webhook_events

    async def _mock_record_webhook_event(session, **kwargs):
        ev = SimpleNamespace(
            id=uuid4(),
            provider=kwargs["provider"],
            provider_event_id=kwargs["provider_event_id"],
            event_type=kwargs["event_type"],
            status=kwargs.get("status", "processed"),
            processed_at=NOW,
        )
        db.webhook_events[(kwargs["provider"], kwargs["provider_event_id"])] = ev
        return ev

    async def _mock_list_payments_by_user(session, user_id, limit=50, offset=0):
        return [p for p in db.payments.values() if p.user_id == user_id]

    async def _mock_count_payments_by_user(session, user_id):
        return len([p for p in db.payments.values() if p.user_id == user_id])

    monkeypatch.setattr(PlanRepository, "get_by_code", _mock_get_by_code)
    monkeypatch.setattr(SubscriptionRepository, "get_by_user", _mock_get_sub_by_user)
    monkeypatch.setattr(SubscriptionRepository, "get_by_id", _mock_get_sub_by_id)
    monkeypatch.setattr(SubscriptionRepository, "create_subscription", _mock_create_sub)
    monkeypatch.setattr(SubscriptionRepository, "append_event", _mock_append_event)
    monkeypatch.setattr(SubscriptionRepository, "save", _mock_save_sub)
    monkeypatch.setattr(SubscriptionRepository, "update_fields", _mock_update_fields)

    monkeypatch.setattr(PaymentRepository, "get_customer", _mock_get_customer)
    monkeypatch.setattr(PaymentRepository, "upsert_customer", _mock_upsert_customer)
    monkeypatch.setattr(PaymentRepository, "get_user_id_by_customer_id", _mock_get_user_id_by_customer_id)
    monkeypatch.setattr(PaymentRepository, "create_payment", _mock_create_payment)
    monkeypatch.setattr(PaymentRepository, "get_by_provider_order_id", _mock_get_by_provider_order_id)
    monkeypatch.setattr(PaymentRepository, "get_by_provider_payment_id", _mock_get_by_provider_payment_id)
    monkeypatch.setattr(PaymentRepository, "update_payment_status", _mock_update_payment_status)
    monkeypatch.setattr(PaymentRepository, "is_event_processed", _mock_is_event_processed)
    monkeypatch.setattr(PaymentRepository, "record_webhook_event", _mock_record_webhook_event)
    monkeypatch.setattr(PaymentRepository, "list_by_user", _mock_list_payments_by_user)
    monkeypatch.setattr(PaymentRepository, "count_by_user", _mock_count_payments_by_user)

    return db


from apps.api.tests.conftest import make_user


@pytest.fixture
def test_user():
    return make_user(email="checkout_tester@astroos.dev", role=UserRole.RESEARCHER)


@pytest.mark.asyncio
async def test_initiate_checkout_success(mem_db, test_user):
    svc = PaymentService(mem_db, provider=MockPaymentProvider())
    req = CheckoutSessionRequest(plan_code="PRO", billing_cycle="monthly", currency="USD")

    res = await svc.initiate_checkout(test_user, req)
    assert res.provider == "mock"
    assert res.amount == 1900
    assert res.currency == "USD"
    assert res.plan_code == "PRO"
    assert "mock_cs_" in res.session_id

    # Verify pending payment created in db
    payments = list(mem_db.payments.values())
    assert len(payments) == 1
    assert payments[0].status == "pending"
    assert payments[0].provider_order_id == res.session_id


@pytest.mark.asyncio
async def test_initiate_checkout_invalid_plan(mem_db, test_user):
    svc = PaymentService(mem_db, provider=MockPaymentProvider())
    req = CheckoutSessionRequest(plan_code="NONEXISTENT")

    with pytest.raises(LookupError, match="Plan 'NONEXISTENT' is not available"):
        await svc.initiate_checkout(test_user, req)


@pytest.mark.asyncio
async def test_initiate_portal(mem_db, test_user):
    svc = PaymentService(mem_db, provider=MockPaymentProvider())
    req = CustomerPortalRequest(return_url="http://localhost:3000/dashboard")

    res = await svc.initiate_portal(test_user, req)
    assert res.provider == "mock"
    assert "http://localhost:3000/dashboard" in res.portal_url


@pytest.mark.asyncio
async def test_webhook_checkout_completed_activates_subscription(mem_db, test_user):
    svc = PaymentService(mem_db, provider=MockPaymentProvider())
    provider = MockPaymentProvider()

    payload_data = {
        "id": "evt_checkout_001",
        "event_type": "checkout.session.completed",
        "data": {
            "user_id": str(test_user.id.value),
            "plan_code": "PRO",
            "amount": 1900,
            "currency": "USD",
            "customer_id": "cus_mock_999",
            "payment_id": "pi_mock_999",
            "order_id": "mock_cs_12345",
        }
    }
    payload_bytes = json.dumps(payload_data).encode("utf-8")
    sig = provider.generate_mock_signature(payload_bytes)

    result = await svc.process_webhook(
        "mock",
        payload_bytes,
        {"x-mock-signature": sig},
    )

    assert result.status == "processed"
    assert result.event_id == "evt_checkout_001"

    # Verify subscription activated in db
    sub = mem_db.subscriptions.get(test_user.id.value)
    assert sub is not None
    assert sub.status == "active"

    # Verify customer mapping saved
    cust = mem_db.customers.get((test_user.id.value, "mock"))
    assert cust is not None
    assert cust.provider_customer_id == "cus_mock_999"


@pytest.mark.asyncio
async def test_webhook_idempotency_ignores_duplicate_event(mem_db, test_user):
    svc = PaymentService(mem_db, provider=MockPaymentProvider())
    provider = MockPaymentProvider()

    payload_data = {
        "id": "evt_duplicate_001",
        "event_type": "checkout.session.completed",
        "data": {
            "user_id": str(test_user.id.value),
            "plan_code": "PRO",
        }
    }
    payload_bytes = json.dumps(payload_data).encode("utf-8")
    sig = provider.generate_mock_signature(payload_bytes)

    # First call: processed
    res1 = await svc.process_webhook("mock", payload_bytes, {"x-mock-signature": sig})
    assert res1.status == "processed"

    # Second call: ignored (idempotent skip)
    res2 = await svc.process_webhook("mock", payload_bytes, {"x-mock-signature": sig})
    assert res2.status == "ignored"


@pytest.mark.asyncio
async def test_webhook_recurring_payment_extends_period(mem_db, test_user):
    svc = PaymentService(mem_db, provider=MockPaymentProvider())
    provider = MockPaymentProvider()

    # Pre-create active subscription
    plan = mem_db.plans["PRO"]
    sub = SimpleNamespace(
        id=uuid4(),
        user_id=test_user.id.value,
        plan_id=plan.id,
        status="active",
        current_period_start=NOW,
        current_period_end=NOW + timedelta(days=30),
        event_version=1,
    )
    mem_db.subscriptions[test_user.id.value] = sub

    payload_data = {
        "id": "evt_renewal_001",
        "event_type": "invoice.payment_succeeded",
        "data": {
            "user_id": str(test_user.id.value),
            "amount": 1900,
            "period_end": int((NOW + timedelta(days=60)).timestamp()),
            "payment_id": "pi_renew_001",
        }
    }
    payload_bytes = json.dumps(payload_data).encode("utf-8")
    sig = provider.generate_mock_signature(payload_bytes)

    res = await svc.process_webhook("mock", payload_bytes, {"x-mock-signature": sig})
    assert res.status == "processed"

    # Verify event logged
    event_types = [e.event_type for e in mem_db.sub_events]
    assert "renewed" in event_types
    assert "period_extended" in event_types


@pytest.mark.asyncio
async def test_webhook_payment_failed_marks_past_due(mem_db, test_user):
    svc = PaymentService(mem_db, provider=MockPaymentProvider())
    provider = MockPaymentProvider()

    plan = mem_db.plans["PRO"]
    sub = SimpleNamespace(
        id=uuid4(),
        user_id=test_user.id.value,
        plan_id=plan.id,
        status="active",
        current_period_start=NOW,
        current_period_end=NOW + timedelta(days=30),
        event_version=1,
        cancel_at_period_end=False,
        cancelled_at=None,
    )
    mem_db.subscriptions[test_user.id.value] = sub

    payload_data = {
        "id": "evt_failed_001",
        "event_type": "invoice.payment_failed",
        "data": {
            "user_id": str(test_user.id.value),
            "amount": 1900,
            "error_message": "insufficient_funds",
            "payment_id": "pi_fail_001",
        }
    }
    payload_bytes = json.dumps(payload_data).encode("utf-8")
    sig = provider.generate_mock_signature(payload_bytes)

    res = await svc.process_webhook("mock", payload_bytes, {"x-mock-signature": sig})
    assert res.status == "processed"
    assert sub.status == SubscriptionStatus.PAST_DUE_CANCELLED.value
