"""
AstroOS — Notification & Email Repository (Phase 7)

Data access for ``email_logs`` and ``notification_preferences``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.models.notification import (
    EmailDeliveryStatus,
    EmailLogModel,
    NotificationPreferenceModel,
)


class NotificationRepository:
    """Data access layer for email logs and notification preferences."""

    # ── Email Logs ───────────────────────────────────────────────────────────

    @staticmethod
    async def get_by_id(db: AsyncSession, log_id: UUID) -> Optional[EmailLogModel]:
        result = await db.execute(
            select(EmailLogModel).where(EmailLogModel.id == log_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_idempotency_key(
        db: AsyncSession, idempotency_key: str
    ) -> Optional[EmailLogModel]:
        result = await db.execute(
            select(EmailLogModel).where(EmailLogModel.idempotency_key == idempotency_key)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_log(
        db: AsyncSession,
        *,
        recipient_email: str,
        template_name: str,
        subject: str,
        idempotency_key: str,
        user_id: Optional[UUID] = None,
        provider: str = "mock",
        status: str = EmailDeliveryStatus.QUEUED.value,
        payload: Optional[dict[str, Any]] = None,
    ) -> EmailLogModel:
        log = EmailLogModel(
            recipient_email=recipient_email,
            template_name=template_name,
            subject=subject,
            idempotency_key=idempotency_key,
            user_id=user_id,
            provider=provider,
            status=status,
            payload_json=json.dumps(payload) if payload else None,
            attempts=0,
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    @staticmethod
    async def update_status(
        db: AsyncSession,
        log: EmailLogModel,
        *,
        status: str,
        provider_message_id: Optional[str] = None,
        error_message: Optional[str] = None,
        increment_attempts: bool = True,
        sent_at: Optional[datetime] = None,
    ) -> EmailLogModel:
        log.status = status
        if increment_attempts:
            log.attempts = (log.attempts or 0) + 1
        if provider_message_id:
            log.provider_message_id = provider_message_id
        if error_message is not None:
            log.error_message = error_message
        if sent_at is not None:
            log.sent_at = sent_at
        elif status == EmailDeliveryStatus.SENT.value and not log.sent_at:
            log.sent_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(log)
        return log

    @staticmethod
    async def list_by_user(
        db: AsyncSession,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EmailLogModel]:
        result = await db.execute(
            select(EmailLogModel)
            .where(EmailLogModel.user_id == user_id)
            .order_by(EmailLogModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    @staticmethod
    async def count_by_user(db: AsyncSession, user_id: UUID) -> int:
        result = await db.execute(
            select(func.count(EmailLogModel.id)).where(EmailLogModel.user_id == user_id)
        )
        return result.scalar_one() or 0

    @staticmethod
    async def list_all(
        db: AsyncSession,
        status: Optional[str] = None,
        template_name: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EmailLogModel]:
        query = select(EmailLogModel).order_by(EmailLogModel.created_at.desc())
        if status:
            query = query.where(EmailLogModel.status == status)
        if template_name:
            query = query.where(EmailLogModel.template_name == template_name)
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return list(result.scalars().all())

    # ── Notification Preferences ─────────────────────────────────────────────

    @staticmethod
    async def get_preferences(
        db: AsyncSession, user_id: UUID
    ) -> Optional[NotificationPreferenceModel]:
        result = await db.execute(
            select(NotificationPreferenceModel).where(
                NotificationPreferenceModel.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_preferences(
        db: AsyncSession, user_id: UUID
    ) -> NotificationPreferenceModel:
        pref = await NotificationRepository.get_preferences(db, user_id)
        if pref is None:
            pref = NotificationPreferenceModel(
                user_id=user_id,
                billing_notifications=True,
                security_alerts=True,
                quota_warnings=True,
                product_updates=False,
            )
            db.add(pref)
            await db.commit()
            await db.refresh(pref)
        return pref

    @staticmethod
    async def update_preferences(
        db: AsyncSession,
        pref: NotificationPreferenceModel,
        *,
        quota_warnings: Optional[bool] = None,
        product_updates: Optional[bool] = None,
    ) -> NotificationPreferenceModel:
        if quota_warnings is not None:
            pref.quota_warnings = quota_warnings
        if product_updates is not None:
            pref.product_updates = product_updates

        await db.commit()
        await db.refresh(pref)
        return pref
