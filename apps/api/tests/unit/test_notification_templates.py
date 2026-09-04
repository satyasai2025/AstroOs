"""
AstroOS — Phase 7 Transactional Email Templates Tests
"""

from __future__ import annotations

import pytest

from apps.api.services.notification.template_engine import RenderedEmail, TemplateEngine


def test_payment_success_template():
    res = TemplateEngine.render(
        "payment_success",
        {
            "plan_name": "PRO",
            "amount": 1900,
            "amount_formatted": "19.00",
            "currency": "USD",
            "transaction_id": "tx_9999",
            "receipt_url": "https://astroos.local/r/123",
            "billing_cycle": "monthly",
        },
    )
    assert isinstance(res, RenderedEmail)
    assert "Payment Receipt: AstroOS PRO Plan" in res.subject
    assert "19.00 USD" in res.html_body
    assert "PRO" in res.text_body
    assert "https://astroos.local/r/123" in res.html_body


def test_payment_failed_template():
    res = TemplateEngine.render(
        "payment_failed",
        {"error_message": "Card expired", "portal_url": "https://astroos.local/billing"},
    )
    assert "Payment Failed" in res.subject
    assert "Card expired" in res.html_body
    assert "Grace Period" in res.text_body


def test_subscription_activated_template():
    res = TemplateEngine.render(
        "subscription_activated",
        {
            "plan_name": "RESEARCH",
            "saved_horoscopes_limit": 100,
            "research_limit": 3,
        },
    )
    assert "Welcome to AstroOS RESEARCH!" in res.subject
    assert "100" in res.html_body
    assert "3" in res.text_body


def test_subscription_renewed_template():
    res = TemplateEngine.render(
        "subscription_renewed",
        {"plan_name": "PRO", "next_billing_date": "2026-09-27"},
    )
    assert "Subscription Renewed: AstroOS PRO" in res.subject
    assert "2026-09-27" in res.html_body


def test_subscription_cancelled_template():
    res = TemplateEngine.render(
        "subscription_cancelled",
        {"plan_name": "PRO", "period_end_date": "2026-09-27"},
    )
    assert "Cancellation Confirmation: AstroOS PRO" in res.subject
    assert "2026-09-27" in res.text_body


def test_subscription_expired_template():
    res = TemplateEngine.render("subscription_expired", {})
    assert "Subscription Lapsed" in res.subject
    assert "FREE" in res.html_body


def test_quota_warning_template():
    res = TemplateEngine.render(
        "quota_warning",
        {
            "metric_name": "saved horoscopes",
            "used": 4,
            "limit": 5,
            "percentage": 80,
        },
    )
    assert "80% of saved horoscopes used" in res.subject
    assert "4 / 5" in res.html_body


def test_password_reset_template():
    res = TemplateEngine.render(
        "password_reset",
        {"reset_link": "https://astroos.local/reset?token=xyz", "ttl_minutes": 30},
    )
    assert "Reset your AstroOS password" in res.subject
    assert "https://astroos.local/reset?token=xyz" in res.html_body
    assert "30 minutes" in res.text_body


def test_security_alert_template():
    res = TemplateEngine.render(
        "security_alert",
        {"action": "Password Modified", "timestamp": "2026-08-27 12:00:00 UTC", "ip_address": "127.0.0.1"},
    )
    assert "Security Alert: Password Modified" in res.subject
    assert "127.0.0.1" in res.html_body


def test_unknown_template_raises_value_error():
    with pytest.raises(ValueError, match="Unknown email template"):
        TemplateEngine.render("nonexistent_template", {})
