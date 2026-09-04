"""
AstroOS — Report History Repository (Phase 10)
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.models.report_history import ReportHistoryModel


class ReportHistoryRepository:
    """Data access for generated report history."""

    @staticmethod
    async def create_report(
        db: AsyncSession,
        *,
        user_id: UUID,
        chart_id: Optional[UUID] = None,
        subject_name: str = "Subject",
        report_tier: str = "free_2page",
        export_format: str = "pdf",
        page_count: int = 2,
        file_size_bytes: int = 0,
        document_content: Optional[str] = None,
        download_url: Optional[str] = None,
    ) -> ReportHistoryModel:
        record = ReportHistoryModel(
            user_id=user_id,
            chart_id=chart_id,
            subject_name=subject_name,
            report_tier=report_tier,
            export_format=export_format,
            page_count=page_count,
            file_size_bytes=file_size_bytes,
            document_content=document_content,
            download_url=download_url,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record

    @staticmethod
    async def get_by_id(db: AsyncSession, report_id: UUID) -> Optional[ReportHistoryModel]:
        result = await db.execute(
            select(ReportHistoryModel).where(ReportHistoryModel.id == report_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_user(
        db: AsyncSession,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ReportHistoryModel]:
        result = await db.execute(
            select(ReportHistoryModel)
            .where(ReportHistoryModel.user_id == user_id)
            .order_by(ReportHistoryModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    @staticmethod
    async def count_by_user(db: AsyncSession, user_id: UUID) -> int:
        result = await db.execute(
            select(func.count(ReportHistoryModel.id)).where(
                ReportHistoryModel.user_id == user_id
            )
        )
        return result.scalar_one() or 0
