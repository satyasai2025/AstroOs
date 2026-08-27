"""
AstroOS — Notification & Email Service (Phase 7)

Core service managing:
  - Idempotent transactional email sending
  - User notification preference checks (mandatory vs configurable)
  - Retry policy with exponential backoff
  - Delivery audit logging in ``email_logs``
  - Event consumer helpers for payments, subscriptions, quotas, and security
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Mapping, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import get_settings
from apps.api.models.notification import (
    EmailDeliveryStatus,
    EmailLogModel,
    NotificationPreferenceModel,
)
from apps.api.repositories.notification_repository import NotificationRepository
from apps.api.services.notification.providers.base import (
    EmailDeliveryProviderBase,
    EmailDeliveryResult,
)
from apps.api.services.notification.providers.factory import get_email_provider
from apps.api.services.notification.template_engine import TemplateEngine

logger = logging.getLogger(__name__)


class NotificationService:
    """Application service for managing notifications and transactional email delivery."""

    def __init__(
        self,
        db: AsyncSession,
        provider: Optional[EmailDeliveryProviderBase] = None,
    ) -> None:
        self._db = db
        self._provider = provider or get_email_provider()
        self._settings = get_settings()

    # ── Core Dispatcher ───────────────────────────────────────────────────────

    async def send_transactional_email(
        self,
        *,
        to_email: str,
        template_name: str,
        context: Mapping[str, Any],
        idempotency_key: str,
        user_id: Optional[UUID] = None,
        category: str = "billing",
    ) -> EmailLogModel:
        """
        Render, idempotently dispatch, and log a transactional email.
        """
        # 1. Check user preferences for non-mandatory categories
        if user_id and category not in ("billing", "security", "password_reset"):
            pref = await NotificationRepository.get_preferences(self._db, user_id)
            if pref:
                if category == "quota" and not pref.quota_warnings:
                    logger.info("[NotificationService] Skipping quota warning for user %s (opted out)", user_id)
                    return await self._record_skipped(to_email, template_name, idempotency_key, user_id, "User opted out of quota warnings")
                elif category == "product" and not pref.product_updates:
                    logger.info("[NotificationService] Skipping product update for user %s (opted out)", user_id)
                    return await self._record_skipped(to_email, template_name, idempotency_key, user_id, "User opted out of product updates")

        # 2. Check idempotency
        existing_log = await NotificationRepository.get_by_idempotency_key(
            self._db, idempotency_key
        )
        if existing_log:
            logger.info("[NotificationService] Idempotent skip: email already processed (key=%s, status=%s)", idempotency_key, existing_log.status)
            return existing_log

        # 3. Render template
        rendered = TemplateEngine.render(template_name, context)

        # 4. Create initial queued log entry
        log_entry = await NotificationRepository.create_log(
            self._db,
            recipient_email=to_email,
            template_name=template_name,
            subject=rendered.subject,
            idempotency_key=idempotency_key,
            user_id=user_id,
            provider=self._provider.provider_name,
            status=EmailDeliveryStatus.QUEUED.value,
            payload=dict(context),
        )

        # 5. Execute delivery with retry
        max_attempts = max(1, self._settings.EMAIL_MAX_RETRIES)
        backoff_base = self._settings.EMAIL_RETRY_BACKOFF_BASE
        last_error = None
        result = None

        for attempt in range(max_attempts):
            result = await self._provider.send_email(
                to_email=to_email,
                subject=rendered.subject,
                html_body=rendered.html_body,
                text_body=rendered.text_body,
                metadata={"log_id": str(log_entry.id), "template": template_name},
            )

            if result.success:
                log_entry = await NotificationRepository.update_status(
                    self._db,
                    log_entry,
                    status=EmailDeliveryStatus.SENT.value,
                    provider_message_id=result.message_id,
                    error_message=None,
                    sent_at=datetime.now(timezone.utc),
                )
                return log_entry
            else:
                last_error = result.error_message or "Unknown delivery error"
                logger.warning(
                    "[NotificationService] Attempt %d/%d failed for %s: %s",
                    attempt + 1,
                    max_attempts,
                    to_email,
                    last_error,
                )
                if attempt < max_attempts - 1:
                    await asyncio.sleep(backoff_base * (2 ** attempt))

        # All attempts exhausted
        log_entry = await NotificationRepository.update_status(
            self._db,
            log_entry,
            status=EmailDeliveryStatus.FAILED.value,
            error_message=last_error,
        )
        return log_entry

    async def _record_skipped(
        self,
        to_email: str,
        template_name: str,
        idempotency_key: str,
        user_id: Optional[UUID],
        reason: str,
    ) -> EmailLogModel:
        return await NotificationRepository.create_log(
            self._db,
            recipient_email=to_email,
            template_name=template_name,
            subject=f"[Skipped] {template_name}",
            idempotency_key=idempotency_key,
            user_id=user_id,
            provider=self._provider.provider_name,
            status="skipped",
            payload={"skip_reason": reason},
        )

    # ── Convenience Event Handlers ───────────────────────────────────────────

    async def send_payment_success_notification(
        self,
        *,
        to_email: str,
        user_id: UUID,
        amount: int,
        currency: str,
        plan_name: str,
        transaction_id: str,
        receipt_url: Optional[str] = None,
        payment_id: Optional[str] = None,
    ) -> EmailLogModel:
        key = f"pay_success_{payment_id or transaction_id}"
        return await self.send_transactional_email(
            to_email=to_email,
            template_name="payment_success",
            context={
                "amount": amount,
                "amount_formatted": f"{(amount / 100):.2f}",
                "currency": currency,
                "plan_name": plan_name,
                "transaction_id": transaction_id,
                "receipt_url": receipt_url or "#",
            },
            idempotency_key=key,
            user_id=user_id,
            category="billing",
        )

    async def send_payment_failed_notification(
        self,
        *,
        to_email: str,
        user_id: UUID,
        error_message: str,
        payment_id: str,
    ) -> EmailLogModel:
        key = f"pay_failed_{payment_id}"
        return await self.send_transactional_email(
            to_email=to_email,
            template_name="payment_failed",
            context={
                "error_message": error_message,
                "portal_url": "http://localhost:3000/settings/billing",
            },
            idempotency_key=key,
            user_id=user_id,
            category="billing",
        )

    async def send_subscription_activated_notification(
        self,
        *,
        to_email: str,
        user_id: UUID,
        plan_name: str,
        horoscope_limit: int,
        research_limit: int,
        sub_id: UUID,
        event_version: int = 1,
    ) -> EmailLogModel:
        key = f"sub_activated_{sub_id}_v{event_version}"
        return await self.send_transactional_email(
            to_email=to_email,
            template_name="subscription_activated",
            context={
                "plan_name": plan_name,
                "saved_horoscopes_limit": horoscope_limit,
                "research_limit": research_limit,
            },
            idempotency_key=key,
            user_id=user_id,
            category="billing",
        )

    async def send_subscription_renewed_notification(
        self,
        *,
        to_email: str,
        user_id: UUID,
        plan_name: str,
        next_billing_date: str,
        sub_id: UUID,
        event_key: str,
    ) -> EmailLogModel:
        key = f"sub_renewed_{sub_id}_{event_key}"
        return await self.send_transactional_email(
            to_email=to_email,
            template_name="subscription_renewed",
            context={
                "plan_name": plan_name,
                "next_billing_date": next_billing_date,
            },
            idempotency_key=key,
            user_id=user_id,
            category="billing",
        )

    async def send_subscription_cancelled_notification(
        self,
        *,
        to_email: str,
        user_id: UUID,
        plan_name: str,
        period_end_date: str,
        sub_id: UUID,
    ) -> EmailLogModel:
        key = f"sub_cancelled_{sub_id}"
        return await self.send_transactional_email(
            to_email=to_email,
            template_name="subscription_cancelled",
            context={
                "plan_name": plan_name,
                "period_end_date": period_end_date,
            },
            idempotency_key=key,
            user_id=user_id,
            category="billing",
        )

    async def send_quota_warning_notification(
        self,
        *,
        to_email: str,
        user_id: UUID,
        metric_name: str,
        used: int,
        limit: int,
        percentage: int,
        quota_period_key: str,
    ) -> EmailLogModel:
        key = f"quota_{metric_name}_{user_id}_{quota_period_key}_{percentage}"
        return await self.send_transactional_email(
            to_email=to_email,
            template_name="quota_warning",
            context={
                "metric_name": metric_name,
                "used": used,
                "limit": limit,
                "percentage": percentage,
            },
            idempotency_key=key,
            user_id=user_id,
            category="quota",
        )

    async def send_password_reset_notification(
        self,
        *,
        to_email: str,
        reset_link: str,
        token_id: str,
        user_id: Optional[UUID] = None,
    ) -> EmailLogModel:
        key = f"pwd_reset_{token_id}"
        return await self.send_transactional_email(
            to_email=to_email,
            template_name="password_reset",
            context={
                "reset_link": reset_link,
                "ttl_minutes": self._settings.PASSWORD_RESET_TOKEN_TTL_MINUTES,
            },
            idempotency_key=key,
            user_id=user_id,
            category="password_reset",
        )

    async def send_security_alert_notification(
        self,
        *,
        to_email: str,
        user_id: UUID,
        action: str,
        ip_address: str,
        action_id: str,
    ) -> EmailLogModel:
        key = f"sec_alert_{user_id}_{action_id}"
        return await self.send_transactional_email(
            to_email=to_email,
            template_name="security_alert",
            context={
                "action": action,
                "ip_address": ip_address,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            },
            idempotency_key=key,
            user_id=user_id,
            category="security",
        )
