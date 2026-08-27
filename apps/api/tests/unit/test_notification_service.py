"""
AstroOS — Phase 7 Notification Service & Event Ingestion Tests
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from apps.api.domain.user import UserRole
from apps.api.models.notification import EmailDeliveryStatus
from apps.api.repositories.notification_repository import NotificationRepository
from apps.api.services.notification.providers.mock_provider import MockEmailProvider
from apps.api.services.notification_service import NotificationService
from apps.api.tests.conftest import make_user

NOW = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)


class _MemDB:
    def __init__(self):
        self.logs = {}
        self.preferences = {}

    def add(self, obj):
        if hasattr(obj, "id") and not getattr(obj, "id", None):
            obj.id = uuid4()
        if type(obj).__name__ == "EmailLogModel":
            self.logs[obj.idempotency_key] = obj
        elif type(obj).__name__ == "NotificationPreferenceModel":
            self.preferences[obj.user_id] = obj

    async def commit(self):
        pass

    async def flush(self):
        pass

    async def refresh(self, obj):
        pass


@pytest.fixture
def mem_db(monkeypatch):
    db = _MemDB()

    async def _mock_get_by_idempotency_key(session, key):
        return db.logs.get(key)

    async def _mock_get_by_id(session, log_id):
        for log in db.logs.values():
            if log.id == log_id:
                return log
        return None

    async def _mock_create_log(session, **kwargs):
        log = SimpleNamespace(
            id=uuid4(),
            recipient_email=kwargs["recipient_email"],
            template_name=kwargs["template_name"],
            subject=kwargs["subject"],
            idempotency_key=kwargs["idempotency_key"],
            user_id=kwargs.get("user_id"),
            provider=kwargs.get("provider", "mock"),
            status=kwargs.get("status", "queued"),
            payload_json=json.dumps(kwargs.get("payload")) if kwargs.get("payload") else None,
            attempts=0,
            error_message=None,
            sent_at=None,
            created_at=NOW,
        )
        db.logs[log.idempotency_key] = log
        return log

    async def _mock_update_status(session, log, **kwargs):
        log.status = kwargs.get("status", log.status)
        log.attempts = (log.attempts or 0) + 1
        if "provider_message_id" in kwargs:
            log.provider_message_id = kwargs["provider_message_id"]
        if "error_message" in kwargs:
            log.error_message = kwargs["error_message"]
        if "sent_at" in kwargs and kwargs["sent_at"]:
            log.sent_at = kwargs["sent_at"]
        return log

    async def _mock_get_preferences(session, user_id):
        return db.preferences.get(user_id)

    async def _mock_get_or_create_preferences(session, user_id):
        pref = db.preferences.get(user_id)
        if not pref:
            pref = SimpleNamespace(
                id=uuid4(),
                user_id=user_id,
                billing_notifications=True,
                security_alerts=True,
                quota_warnings=True,
                product_updates=False,
            )
            db.preferences[user_id] = pref
        return pref

    monkeypatch.setattr(NotificationRepository, "get_by_idempotency_key", _mock_get_by_idempotency_key)
    monkeypatch.setattr(NotificationRepository, "get_by_id", _mock_get_by_id)
    monkeypatch.setattr(NotificationRepository, "create_log", _mock_create_log)
    monkeypatch.setattr(NotificationRepository, "update_status", _mock_update_status)
    monkeypatch.setattr(NotificationRepository, "get_preferences", _mock_get_preferences)
    monkeypatch.setattr(NotificationRepository, "get_or_create_preferences", _mock_get_or_create_preferences)

    return db


@pytest.fixture
def test_user():
    return make_user(email="notify_tester@astroos.dev", role=UserRole.RESEARCHER)


@pytest.mark.asyncio
async def test_idempotent_email_delivery(mem_db, test_user):
    MockEmailProvider.clear_sent_emails()
    provider = MockEmailProvider()
    svc = NotificationService(mem_db, provider=provider)

    key = "test_idempotent_key_001"
    ctx = {"plan_name": "PRO", "amount": 1900, "amount_formatted": "19.00", "currency": "USD", "transaction_id": "tx_1"}

    # First send: executes delivery
    log1 = await svc.send_transactional_email(
        to_email=test_user.email,
        template_name="payment_success",
        context=ctx,
        idempotency_key=key,
        user_id=test_user.id.value,
        category="billing",
    )
    assert log1.status == "sent"
    assert len(MockEmailProvider.get_sent_emails()) == 1

    # Second send with same idempotency key: returns existing log without sending duplicate
    log2 = await svc.send_transactional_email(
        to_email=test_user.email,
        template_name="payment_success",
        context=ctx,
        idempotency_key=key,
        user_id=test_user.id.value,
        category="billing",
    )
    assert log2.id == log1.id
    assert len(MockEmailProvider.get_sent_emails()) == 1


@pytest.mark.asyncio
async def test_mandatory_vs_configurable_preferences(mem_db, test_user):
    MockEmailProvider.clear_sent_emails()
    provider = MockEmailProvider()
    svc = NotificationService(mem_db, provider=provider)

    # Set user preferences: opted out of quota warnings
    mem_db.preferences[test_user.id.value] = SimpleNamespace(
        id=uuid4(),
        user_id=test_user.id.value,
        billing_notifications=True,
        security_alerts=True,
        quota_warnings=False,  # Opted out
        product_updates=False,
    )

    # Quota warning is skipped
    quota_log = await svc.send_quota_warning_notification(
        to_email=test_user.email,
        user_id=test_user.id.value,
        metric_name="saved horoscopes",
        used=5,
        limit=5,
        percentage=100,
        quota_period_key="2026-08",
    )
    assert quota_log.status == "skipped"
    assert len(MockEmailProvider.get_sent_emails()) == 0

    # Mandatory billing notification cannot be skipped
    bill_log = await svc.send_payment_failed_notification(
        to_email=test_user.email,
        user_id=test_user.id.value,
        error_message="Card declined",
        payment_id="pay_fail_123",
    )
    assert bill_log.status == "sent"
    assert len(MockEmailProvider.get_sent_emails()) == 1


@pytest.mark.asyncio
async def test_notification_convenience_event_handlers(mem_db, test_user):
    MockEmailProvider.clear_sent_emails()
    provider = MockEmailProvider()
    svc = NotificationService(mem_db, provider=provider)

    # 1. Payment Success
    p_log = await svc.send_payment_success_notification(
        to_email=test_user.email,
        user_id=test_user.id.value,
        amount=4900,
        currency="USD",
        plan_name="RESEARCH",
        transaction_id="tx_research_01",
        payment_id="pi_001",
    )
    assert p_log.status == "sent"

    # 2. Subscription Activated
    sub_id = uuid4()
    s_log = await svc.send_subscription_activated_notification(
        to_email=test_user.email,
        user_id=test_user.id.value,
        plan_name="RESEARCH",
        horoscope_limit=100,
        research_limit=3,
        sub_id=sub_id,
        event_version=1,
    )
    assert s_log.status == "sent"

    # 3. Subscription Renewed
    r_log = await svc.send_subscription_renewed_notification(
        to_email=test_user.email,
        user_id=test_user.id.value,
        plan_name="RESEARCH",
        next_billing_date="2026-09-27",
        sub_id=sub_id,
        event_key="evt_renew_1",
    )
    assert r_log.status == "sent"

    # 4. Subscription Cancelled
    c_log = await svc.send_subscription_cancelled_notification(
        to_email=test_user.email,
        user_id=test_user.id.value,
        plan_name="RESEARCH",
        period_end_date="2026-09-27",
        sub_id=sub_id,
    )
    assert c_log.status == "sent"

    # 5. Password Reset
    pwd_log = await svc.send_password_reset_notification(
        to_email=test_user.email,
        reset_link="https://astroos.local/reset?token=xyz",
        token_id="tok_123",
        user_id=test_user.id.value,
    )
    assert pwd_log.status == "sent"

    # 6. Security Alert
    sec_log = await svc.send_security_alert_notification(
        to_email=test_user.email,
        user_id=test_user.id.value,
        action="Password Changed",
        ip_address="192.168.1.50",
        action_id="sec_act_001",
    )
    assert sec_log.status == "sent"

    sent = MockEmailProvider.get_sent_emails()
    assert len(sent) == 6
