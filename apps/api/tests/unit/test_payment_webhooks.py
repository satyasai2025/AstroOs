"""
AstroOS — Phase 6 Payment Webhook Cryptographic & Signature Tests
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from uuid import uuid4

import pytest

from apps.api.services.payment.mock_provider import MockPaymentProvider
from apps.api.services.payment.razorpay_provider import RazorpayPaymentProvider
from apps.api.services.payment.stripe_provider import StripePaymentProvider


def test_stripe_signature_verification_valid():
    secret = "whsec_live_test_secret_123"
    provider = StripePaymentProvider(webhook_secret=secret)

    payload = json.dumps({"id": "evt_test", "type": "payment_intent.succeeded"}).encode("utf-8")
    t = str(int(time.time()))
    signed_payload = f"{t}.".encode("utf-8") + payload
    v1 = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    header = f"t={t},v1={v1}"

    assert provider.verify_webhook_signature(payload, {"stripe-signature": header}) is True


def test_stripe_signature_verification_invalid_secret_or_tampered():
    secret = "whsec_correct_secret"
    provider = StripePaymentProvider(webhook_secret=secret)

    payload = json.dumps({"id": "evt_test", "type": "payment_intent.succeeded"}).encode("utf-8")
    tampered_payload = json.dumps({"id": "evt_test", "type": "payment_intent.succeeded", "tampered": True}).encode("utf-8")

    t = str(int(time.time()))
    signed_payload = f"{t}.".encode("utf-8") + payload
    v1 = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    header = f"t={t},v1={v1}"

    # Tampered payload fails
    assert provider.verify_webhook_signature(tampered_payload, {"stripe-signature": header}) is False

    # Wrong secret fails
    wrong_provider = StripePaymentProvider(webhook_secret="whsec_wrong_secret")
    assert wrong_provider.verify_webhook_signature(payload, {"stripe-signature": header}) is False


def test_razorpay_signature_verification_valid():
    secret = "rzp_whsec_secret_456"
    provider = RazorpayPaymentProvider(webhook_secret=secret)

    payload = json.dumps({"event": "order.paid", "id": "rzp_order_01"}).encode("utf-8")
    expected_sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    assert provider.verify_webhook_signature(payload, {"x-razorpay-signature": expected_sig}) is True


def test_razorpay_signature_verification_tampered():
    secret = "rzp_whsec_secret_456"
    provider = RazorpayPaymentProvider(webhook_secret=secret)

    payload = json.dumps({"event": "order.paid", "id": "rzp_order_01"}).encode("utf-8")
    tampered_payload = json.dumps({"event": "order.paid", "id": "rzp_order_01", "tampered": True}).encode("utf-8")
    expected_sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    assert provider.verify_webhook_signature(tampered_payload, {"x-razorpay-signature": expected_sig}) is False


def test_mock_signature_verification_valid_and_invalid():
    provider = MockPaymentProvider()
    payload = b'{"hello": "world"}'
    sig = provider.generate_mock_signature(payload)

    assert provider.verify_webhook_signature(payload, {"x-mock-signature": sig}) is True
    assert provider.verify_webhook_signature(payload, {"x-mock-signature": "bogus"}) is False
    assert provider.verify_webhook_signature(payload, {}) is False
    assert provider.verify_webhook_signature(payload, {"x-mock-skip-signature": "true"}) is True
