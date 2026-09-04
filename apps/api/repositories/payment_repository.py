"""
AstroOS — Payment Repository (Phase 6)

Data access for ``payments``, ``payment_customers``, and ``payment_webhook_events``.
Static-method style adhering to repository patterns in AstroOS.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.models.payment import (
    PaymentCustomerModel,
    PaymentModel,
    PaymentProviderType,
    PaymentStatus,
    PaymentWebhookEventModel,
)


class PaymentRepository:
    """Data access for Payment, Customer mapping, and Webhook logs."""

    # ── Payments ─────────────────────────────────────────────────────────────

    @staticmethod
    async def get_by_id(db: AsyncSession, payment_id: UUID) -> Optional[PaymentModel]:
        result = await db.execute(
            select(PaymentModel).where(PaymentModel.id == payment_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_provider_payment_id(
        db: AsyncSession, provider: str, provider_payment_id: str
    ) -> Optional[PaymentModel]:
        result = await db.execute(
            select(PaymentModel).where(
                PaymentModel.provider == provider,
                PaymentModel.provider_payment_id == provider_payment_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_provider_order_id(
        db: AsyncSession, provider_order_id: str
    ) -> Optional[PaymentModel]:
        result = await db.execute(
            select(PaymentModel).where(
                PaymentModel.provider_order_id == provider_order_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_user(
        db: AsyncSession,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PaymentModel]:
        result = await db.execute(
            select(PaymentModel)
            .where(PaymentModel.user_id == user_id)
            .order_by(PaymentModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    @staticmethod
    async def count_by_user(db: AsyncSession, user_id: UUID) -> int:
        result = await db.execute(
            select(func.count(PaymentModel.id)).where(PaymentModel.user_id == user_id)
        )
        return result.scalar_one() or 0

    @staticmethod
    async def list_all(
        db: AsyncSession,
        status: Optional[str] = None,
        provider: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PaymentModel]:
        query = select(PaymentModel).order_by(PaymentModel.created_at.desc())
        if status:
            query = query.where(PaymentModel.status == status)
        if provider:
            query = query.where(PaymentModel.provider == provider)
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def create_payment(
        db: AsyncSession,
        *,
        user_id: UUID,
        amount: int,
        currency: str = "INR",
        base_amount: Optional[int] = None,
        tax_amount: Optional[int] = None,
        tax_rate: Optional[float] = None,
        provider: str = PaymentProviderType.MOCK.value,
        subscription_id: Optional[UUID] = None,
        plan_id: Optional[UUID] = None,
        status_value: str = PaymentStatus.PENDING.value,
        provider_payment_id: Optional[str] = None,
        provider_order_id: Optional[str] = None,
        payment_method: Optional[str] = None,
        receipt_url: Optional[str] = None,
        payload: Optional[dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> PaymentModel:
        payment = PaymentModel(
            user_id=user_id,
            amount=amount,
            base_amount=base_amount,
            tax_amount=tax_amount,
            tax_rate=tax_rate,
            currency=currency,
            provider=provider,
            subscription_id=subscription_id,
            plan_id=plan_id,
            status=status_value,
            provider_payment_id=provider_payment_id,
            provider_order_id=provider_order_id,
            payment_method=payment_method,
            receipt_url=receipt_url,
            payload_json=json.dumps(payload) if payload else None,
            error_message=error_message,
        )
        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        return payment

    @staticmethod
    async def update_payment_status(
        db: AsyncSession,
        payment: PaymentModel,
        *,
        status_value: str,
        provider_payment_id: Optional[str] = None,
        receipt_url: Optional[str] = None,
        error_message: Optional[str] = None,
        payload: Optional[dict[str, Any]] = None,
    ) -> PaymentModel:
        payment.status = status_value
        if provider_payment_id:
            payment.provider_payment_id = provider_payment_id
        if receipt_url:
            payment.receipt_url = receipt_url
        if error_message:
            payment.error_message = error_message
        if payload:
            payment.payload_json = json.dumps(payload)
        await db.commit()
        await db.refresh(payment)
        return payment

    # ── Customers ────────────────────────────────────────────────────────────

    @staticmethod
    async def get_customer(
        db: AsyncSession, user_id: UUID, provider: str
    ) -> Optional[PaymentCustomerModel]:
        result = await db.execute(
            select(PaymentCustomerModel).where(
                PaymentCustomerModel.user_id == user_id,
                PaymentCustomerModel.provider == provider,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_id_by_customer_id(
        db: AsyncSession, provider: str, provider_customer_id: str
    ) -> Optional[UUID]:
        result = await db.execute(
            select(PaymentCustomerModel.user_id).where(
                PaymentCustomerModel.provider == provider,
                PaymentCustomerModel.provider_customer_id == provider_customer_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def upsert_customer(
        db: AsyncSession,
        *,
        user_id: UUID,
        provider: str,
        provider_customer_id: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> PaymentCustomerModel:
        customer = await PaymentRepository.get_customer(db, user_id, provider)
        if customer:
            customer.provider_customer_id = provider_customer_id
            if metadata:
                customer.metadata_json = json.dumps(metadata)
        else:
            customer = PaymentCustomerModel(
                user_id=user_id,
                provider=provider,
                provider_customer_id=provider_customer_id,
                metadata_json=json.dumps(metadata) if metadata else None,
            )
            db.add(customer)
        await db.commit()
        await db.refresh(customer)
        return customer

    # ── Webhooks & Idempotency ───────────────────────────────────────────────

    @staticmethod
    async def is_event_processed(
        db: AsyncSession, provider: str, provider_event_id: str
    ) -> bool:
        result = await db.execute(
            select(PaymentWebhookEventModel.id).where(
                PaymentWebhookEventModel.provider == provider,
                PaymentWebhookEventModel.provider_event_id == provider_event_id,
                PaymentWebhookEventModel.status == "processed",
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def record_webhook_event(
        db: AsyncSession,
        *,
        provider: str,
        provider_event_id: str,
        event_type: str,
        status: str = "processed",
        payload: Optional[dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> PaymentWebhookEventModel:
        event = PaymentWebhookEventModel(
            provider=provider,
            provider_event_id=provider_event_id,
            event_type=event_type,
            status=status,
            payload_json=json.dumps(payload) if payload else None,
            error_message=error_message,
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event
