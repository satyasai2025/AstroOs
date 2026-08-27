"""
AstroOS — Phase 7 Email Delivery Provider Tests
"""

from __future__ import annotations

import pytest

from apps.api.services.notification.providers.base import EmailDeliveryResult
from apps.api.services.notification.providers.factory import get_email_provider
from apps.api.services.notification.providers.mock_provider import MockEmailProvider
from apps.api.services.notification.providers.resend_provider import ResendEmailProvider
from apps.api.services.notification.providers.smtp_provider import SmtpEmailProvider


@pytest.mark.asyncio
async def test_mock_email_provider():
    MockEmailProvider.clear_sent_emails()
    provider = MockEmailProvider()
    assert provider.provider_name == "mock"

    res = await provider.send_email(
        to_email="test@astroos.dev",
        subject="Test Subject",
        html_body="<p>Test HTML</p>",
        text_body="Test Text",
    )
    assert isinstance(res, EmailDeliveryResult)
    assert res.success is True
    assert res.provider == "mock"
    assert "mock_msg_" in res.message_id

    sent = MockEmailProvider.get_sent_emails()
    assert len(sent) == 1
    assert sent[0].to_email == "test@astroos.dev"
    assert sent[0].subject == "Test Subject"
    assert sent[0].text_body == "Test Text"

    # Test failure simulation
    failing_provider = MockEmailProvider(should_fail=True, failure_error="Simulated network error")
    fail_res = await failing_provider.send_email(
        to_email="fail@astroos.dev",
        subject="Fail",
        html_body="",
        text_body="",
    )
    assert fail_res.success is False
    assert fail_res.error_message == "Simulated network error"


@pytest.mark.asyncio
async def test_smtp_email_provider_unconfigured_fallback():
    provider = SmtpEmailProvider(host=None)
    assert provider.provider_name == "smtp"

    res = await provider.send_email(
        to_email="smtp_fallback@astroos.dev",
        subject="SMTP Fallback",
        html_body="<p>Body</p>",
        text_body="Body",
    )
    assert res.success is True
    assert res.provider == "smtp"
    assert "logged_smtp_" in res.message_id


@pytest.mark.asyncio
async def test_resend_email_provider_unconfigured_fallback():
    provider = ResendEmailProvider(api_key=None)
    assert provider.provider_name == "resend"

    res = await provider.send_email(
        to_email="resend_fallback@astroos.dev",
        subject="Resend Fallback",
        html_body="<p>Body</p>",
        text_body="Body",
    )
    assert res.success is True
    assert res.provider == "resend"
    assert "sim_resend_" in res.message_id


def test_factory_resolves_all_email_providers():
    assert isinstance(get_email_provider("mock"), MockEmailProvider)
    assert isinstance(get_email_provider("smtp"), SmtpEmailProvider)
    assert isinstance(get_email_provider("resend"), ResendEmailProvider)

    with pytest.raises(ValueError, match="Unsupported email provider"):
        get_email_provider("sendgrid")
