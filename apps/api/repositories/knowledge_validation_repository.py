"""
AstroOS — Knowledge Validation Repository

Async SQLAlchemy persistence for validation decisions and audit trail.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.knowledge_validation import (
    ValidationAuditEntry,
    ValidationCheckResult,
    ValidationDecisionRecord,
    ValidationStatus,
)
from apps.api.models.knowledge_validation import (
    KnowledgeValidationAuditLog,
    KnowledgeValidationRecord,
)


class KnowledgeValidationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Records ─────────────────────────────────────────────────────────────

    async def create_validation_record(
        self, record: KnowledgeValidationRecord
    ) -> KnowledgeValidationRecord:
        self._session.add(record)
        await self._session.flush()
        await self._session.refresh(record)
        return record

    async def get_validation_record(
        self, knowledge_item_id: uuid.UUID, knowledge_item_type: str
    ) -> Optional[KnowledgeValidationRecord]:
        stmt = (
            select(KnowledgeValidationRecord)
            .where(
                KnowledgeValidationRecord.knowledge_item_id == knowledge_item_id,
                KnowledgeValidationRecord.knowledge_item_type == knowledge_item_type,
                KnowledgeValidationRecord.deleted_at.is_(None),
            )
            .order_by(desc(KnowledgeValidationRecord.validated_at))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_validation(
        self, knowledge_item_id: uuid.UUID
    ) -> Optional[KnowledgeValidationRecord]:
        """Get the latest validation for a document or chunk regardless of type."""
        stmt = (
            select(KnowledgeValidationRecord)
            .where(
                KnowledgeValidationRecord.knowledge_item_id == knowledge_item_id,
                KnowledgeValidationRecord.deleted_at.is_(None),
            )
            .order_by(desc(KnowledgeValidationRecord.validated_at))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def is_validated(self, knowledge_item_id: uuid.UUID) -> bool:
        """Quick check if a knowledge item has an APPROVED validation."""
        stmt = (
            select(KnowledgeValidationRecord.validated_at)
            .where(
                KnowledgeValidationRecord.knowledge_item_id == knowledge_item_id,
                KnowledgeValidationRecord.validation_status == ValidationStatus.APPROVED.value,
                KnowledgeValidationRecord.deleted_at.is_(None),
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def list_validation_candidates(
        self,
        validation_status: Optional[str] = None,
        technique_framework: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[KnowledgeValidationRecord]:
        stmt = (
            select(KnowledgeValidationRecord)
            .where(KnowledgeValidationRecord.deleted_at.is_(None))
        )
        if validation_status:
            stmt = stmt.where(
                KnowledgeValidationRecord.validation_status == validation_status
            )
        if technique_framework:
            stmt = stmt.where(
                KnowledgeValidationRecord.technique_framework == technique_framework
            )
        stmt = (
            stmt.order_by(desc(KnowledgeValidationRecord.validated_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def update_promotion_eligibility(
        self,
        validation_id: uuid.UUID,
        eligible: bool,
        targets: list,
    ) -> Optional[KnowledgeValidationRecord]:
        stmt = (
            select(KnowledgeValidationRecord)
            .where(
                KnowledgeValidationRecord.validation_id == validation_id,
                KnowledgeValidationRecord.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        if record:
            record.is_eligible_for_promotion = eligible
            record.eligible_promotion_targets = targets
            await self._session.flush()
        return record

    # ── Audit ────────────────────────────────────────────────────────────────

    async def add_audit_entry(
        self, entry: KnowledgeValidationAuditLog
    ) -> KnowledgeValidationAuditLog:
        self._session.add(entry)
        await self._session.flush()
        await self._session.refresh(entry)
        return entry

    async def get_audit_trail(
        self, validation_id: uuid.UUID, limit: int = 100
    ) -> Sequence[KnowledgeValidationAuditLog]:
        stmt = (
            select(KnowledgeValidationAuditLog)
            .where(
                KnowledgeValidationAuditLog.validation_id == validation_id,
                KnowledgeValidationAuditLog.deleted_at.is_(None),
            )
            .order_by(desc(KnowledgeValidationAuditLog.timestamp))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_full_validation_record_with_audit(
        self, validation_id: uuid.UUID
    ) -> Optional[KnowledgeValidationRecord]:
        stmt = (
            select(KnowledgeValidationRecord)
            .where(
                KnowledgeValidationRecord.validation_id == validation_id,
                KnowledgeValidationRecord.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()