"""
AstroOS — Outbound Email

Plain stdlib smtplib, run off the event loop via asyncio.to_thread — no new
async-SMTP dependency needed for what is currently a single transactional
email.

If SMTP_HOST is unset (the safe local-development default — see config.py),
sending is skipped and the message is logged instead, so password-reset can
be exercised end-to-end without standing up a mail server.
"""

import asyncio
import logging
import smtplib
from email.message import EmailMessage

from apps.api.config import get_settings

logger = logging.getLogger(__name__)

_settings = get_settings()


def _send_sync(to_email: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = _settings.SMTP_FROM_EMAIL
    message["To"] = to_email
    message.set_content(body)

    with smtplib.SMTP(_settings.SMTP_HOST, _settings.SMTP_PORT, timeout=10) as smtp:
        if _settings.SMTP_USE_TLS:
            smtp.starttls()
        if _settings.SMTP_USERNAME and _settings.SMTP_PASSWORD:
            smtp.login(_settings.SMTP_USERNAME, _settings.SMTP_PASSWORD)
        smtp.send_message(message)


async def send_password_reset_email(to_email: str, reset_link: str) -> None:
    """Send (or, with no SMTP configured, log) a password-reset email."""
    subject = "Reset your AstroOS password"
    body = (
        "We received a request to reset your AstroOS password.\n\n"
        f"Reset it here: {reset_link}\n\n"
        f"This link expires in {_settings.PASSWORD_RESET_TOKEN_TTL_MINUTES} minutes. "
        "If you didn't request this, you can safely ignore this email."
    )

    if not _settings.SMTP_HOST:
        logger.warning(
            "SMTP_HOST not configured — logging password reset link instead "
            "of emailing it. to=%s link=%s",
            to_email,
            reset_link,
        )
        return

    await asyncio.to_thread(_send_sync, to_email, subject, body)
