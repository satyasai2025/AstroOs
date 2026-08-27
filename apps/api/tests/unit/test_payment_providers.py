"""
AstroOS — Phase 6 Payment Provider Adapter Tests
"""

from __future__ import annotations

import hashlib
import hmac
import json
import pytest

from apps.api.services.payment.base import (
    CheckoutSessionResult,
    CustomerPortalResult,
    StandardWebhookEvent,
)
from apps.api.services.payment.factory import get_payment_provider
from apps.api.services.payment.mock_provider import MockPaymentProvider
from apps.api.services.payment.razorpay_provider import RazorpayPaymentProvider
from apps.api.services.payment.stripe_provider import StripePaymentProvider


@pytest.mark.asyncio
async def test_mock_provider_checkout_and_portal():
    provider = MockPaymentProvider()
    assert provider.provider_name == "mock"

    res = await provider.create_checkout_session(
        user_id="11111111-1111-1111-1111-111111111111",
        user_email="user@test.com",
        plan_code="PRO",
        amount=1900,
        currency="USD",
        billing_cycle="monthly",
    )
    assert isinstance(res, CheckoutSessionResult)
    assert res.provider == "mock"
    assert res.amount == 1900
    assert "mock_cs_" in res.session_id

    portal_res = await provider.create_portal_session(customer_id="mock_cus_123")
    assert isinstance(portal_res, CustomerPortalResult)
    assert "mock_cus_123" in portal_res.portal_url


def test_mock_provider_webhook_signature_and_parsing():
    provider = MockPaymentProvider()
    payload = json.dumps({
        "id": "evt_mock_001",
        "event_type": "checkout.session.completed",
        "data": {
            "user_id": "11111111-1111-1111-1111-111111111111",
            "plan_code": "PRO",
            "amount": 1900,
            "currency": "USD",
            "customer_id": "mock_cus_001",
            "payment_id": "mock_pi_001",
        }
    }).encode("utf-8")

    sig = provider.generate_mock_signature(payload)
    assert provider.verify_webhook_signature(payload, {"x-mock-signature": sig}) is True
    assert provider.verify_webhook_signature(payload, {"x-mock-signature": "invalid_sig"}) is False
    assert provider.verify_webhook_signature(payload, {"x-mock-skip-signature": "true"}) is True

    event = provider.parse_webhook_event(payload, {})
    assert isinstance(event, StandardWebhookEvent)
    assert event.event_id == "evt_mock_001"
    assert event.event_type == "checkout.session.completed"
    assert event.user_id == "11111111-1111-1111-1111-111111111111"
    assert event.plan_code == "PRO"
    assert event.amount == 1900


@pytest.mark.asyncio
async def test_stripe_provider_checkout_portal_and_signature():
    provider = StripePaymentProvider(
        api_key=None,  # Triggers simulated sandbox mode
        webhook_secret="whsec_test_secret_stripe",
    )
    assert provider.provider_name == "stripe"

    res = await provider.create_checkout_session(
        user_id="22222222-2222-2222-2222-222222222222",
        user_email="stripe_user@test.com",
        plan_code="RESEARCH",
        amount=4900,
        currency="USD",
    )
    assert res.provider == "stripe"
    assert "cs_test_" in res.session_id

    portal_res = await provider.create_portal_session(customer_id="cus_test_123")
    assert "cus_test_123" in portal_res.portal_url

    # Signature verification
    raw_payload = json.dumps({"id": "evt_stripe_1", "type": "checkout.session.completed"}).encode("utf-8")
    t = "1600000000"
    signed_payload = f"{t}.".encode("utf-8") + raw_payload
    v1_sig = hmac.new(b"whsec_test_secret_stripe", signed_payload, hashlib.sha256).hexdigest()
    header_val = f"t={t},v1={v1_sig}"

    assert provider.verify_webhook_signature(raw_payload, {"stripe-signature": header_val}) is True
    assert provider.verify_webhook_signature(raw_payload, {"stripe-signature": "t=1,v1=wrong"}) is False
    assert provider.verify_webhook_signature(raw_payload, {}) is False


def test_stripe_provider_event_parsing():
    provider = StripePaymentProvider()
    payload = json.dumps({
        "id": "evt_stripe_999",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_999",
                "customer": "cus_999",
                "payment_intent": "pi_stripe_999",
                "amount_total": 1900,
                "currency": "usd",
                "metadata": {
                    "user_id": "33333333-3333-3333-3333-333333333333",
                    "plan_code": "PRO",
                }
            }
        }
    }).encode("utf-8")

    event = provider.parse_webhook_event(payload, {})
    assert event.event_id == "evt_stripe_999"
    assert event.event_type == "checkout.session.completed"
    assert event.user_id == "33333333-3333-3333-3333-333333333333"
    assert event.plan_code == "PRO"
    assert event.customer_id == "cus_999"
    assert event.payment_id == "pi_stripe_999"
    assert event.order_id == "cs_test_999"
    assert event.amount == 1900
    assert event.currency == "USD"


@pytest.mark.asyncio
async def test_razorpay_provider_checkout_portal_and_signature():
    provider = RazorpayPaymentProvider(
        key_id=None,
        key_secret=None,
        webhook_secret="rzp_whsec_test_secret",
    )
    assert provider.provider_name == "razorpay"

    res = await provider.create_checkout_session(
        user_id="44444444-4444-4444-4444-444444444444",
        user_email="rzp_user@test.com",
        plan_code="PRO",
        amount=1900,
        currency="INR",
    )
    assert res.provider == "razorpay"
    assert "order_test_" in res.session_id

    portal_res = await provider.create_portal_session(customer_id="rzp_cus_123")
    assert "rzp_cus_123" in portal_res.portal_url

    # Signature verification
    raw_payload = json.dumps({"event": "payment.captured", "id": "rzp_evt_01"}).encode("utf-8")
    expected_sig = hmac.new(b"rzp_whsec_test_secret", raw_payload, hashlib.sha256).hexdigest()

    assert provider.verify_webhook_signature(raw_payload, {"x-razorpay-signature": expected_sig}) is True
    assert provider.verify_webhook_signature(raw_payload, {"x-razorpay-signature": "wrong"}) is False


def test_razorpay_provider_event_parsing():
    provider = RazorpayPaymentProvider()
    payload = json.dumps({
        "id": "rzp_evt_123",
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_rzp_999",
                    "order_id": "order_rzp_999",
                    "amount": 190000,
                    "currency": "INR",
                    "customer_id": "cust_rzp_123",
                    "notes": {
                        "user_id": "55555555-5555-5555-5555-555555555555",
                        "plan_code": "PRO",
                    }
                }
            }
        }
    }).encode("utf-8")

    event = provider.parse_webhook_event(payload, {})
    assert event.event_id == "rzp_evt_123"
    assert event.event_type == "payment.captured"
    assert event.user_id == "55555555-5555-5555-5555-555555555555"
    assert event.plan_code == "PRO"
    assert event.payment_id == "pay_rzp_999"
    assert event.order_id == "order_rzp_999"
    assert event.amount == 190000
    assert event.currency == "INR"


def test_factory_resolves_all_providers():
    assert isinstance(get_payment_provider("mock"), MockPaymentProvider)
    assert isinstance(get_payment_provider("stripe"), StripePaymentProvider)
    assert isinstance(get_payment_provider("razorpay"), RazorpayPaymentProvider)

    with pytest.raises(ValueError, match="Unsupported payment provider"):
        get_payment_provider("paypal")
