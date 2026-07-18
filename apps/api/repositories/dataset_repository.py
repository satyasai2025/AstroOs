"""
AstroOS — Dataset Repository

All database I/O for the Dataset aggregate lives here. Returns domain
objects (apps.api.domain.dataset.Dataset), never the ORM model directly.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.dataset import Dataset
from apps.api.models.dataset import DatasetModel

_UNSET = object()


def _model_to_domain(model: DatasetModel) -> Dataset:
    """Convert ORM row -> domain Dataset."""
    return Dataset(
        id=model.id,
        dataset_id=model.dataset_id,
        name=model.name,
        description=model.description,
        source_file=model.source_file,
        format=model.format,
        record_count=model.record_count,
        field_count=model.field_count,
        quality_score=float(model.quality_score) if model.quality_score else None,
        quality_tier=model.quality_tier,
        lifecycle_stage=model.lifecycle_stage,
        checksum_sha256=model.checksum_sha256,
        file_path=model.file_path,
        metadata_json=model.metadata_json,
        created_by=model.created_by,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class DatasetRepository:
    """Data access for the Dataset aggregate."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        dataset_id: str,
        name: str,
        *,
        description: Optional[str] = None,
        source_file: Optional[str] = None,
        format: Optional[str] = None,
        record_count: int = 0,
        field_count: int = 0,
        quality_score: Optional[float] = None,
        quality_tier: Optional[str] = None,
        lifecycle_stage: str = "Draft",
        checksum_sha256: Optional[str] = None,
        file_path: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
        created_by: Optional[uuid.UUID] = None,
    ) -> Dataset:
        model = DatasetModel(
            dataset_id=dataset_id,
            name=name,
            description=description,
            source_file=source_file,
            format=format,
            record_count=record_count,
            field_count=field_count,
            quality_score=quality_score,
            quality_tier=quality_tier,
            lifecycle_stage=lifecycle_stage,
            checksum_sha256=checksum_sha256,
            file_path=file_path,
            metadata_json=metadata_json,
            created_by=created_by,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _model_to_domain(model)

    async def get_by_id(self, dataset_id: uuid.UUID) -> Optional[Dataset]:
        """Look up by UUID primary key."""
        stmt = select(DatasetModel).where(
            DatasetModel.id == dataset_id,
            DatasetModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _model_to_domain(row) if row else None

    async def get_by_dataset_id(self, dataset_id_str: str) -> Optional[Dataset]:
        """Look up by external dataset_id string (e.g. ASTRO-RS-COHORT-v2.0.0)."""
        stmt = select(DatasetModel).where(
            DatasetModel.dataset_id == dataset_id_str,
            DatasetModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _model_to_domain(row) if row else None

    async def list(
        self,
        *,
        lifecycle_stage: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[Dataset, ...]:
        """List datasets, with optional lifecycle_stage filter."""
        stmt = (
            select(DatasetModel)
            .where(DatasetModel.deleted_at.is_(None))
            .order_by(DatasetModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if lifecycle_stage:
            stmt = stmt.where(DatasetModel.lifecycle_stage == lifecycle_stage)
        result = await self._session.execute(stmt)
        return tuple(_model_to_domain(row) for row in result.scalars().all())

    async def update(
        self,
        dataset_id: uuid.UUID,
        *,
        name: Any = _UNSET,
        description: Any = _UNSET,
        record_count: Any = _UNSET,
        quality_score: Any = _UNSET,
        quality_tier: Any = _UNSET,
        lifecycle_stage: Any = _UNSET,
        checksum_sha256: Any = _UNSET,
        file_path: Any = _UNSET,
        metadata_json: Any = _UNSET,
    ) -> Optional[Dataset]:
        """Partial update. Returns None if not found (or soft-deleted)."""
        values: Dict[str, Any] = {}
        if name is not _UNSET:
            values["name"] = name
        if description is not _UNSET:
            values["description"] = description
        if record_count is not _UNSET:
            values["record_count"] = record_count
        if quality_score is not _UNSET:
            values["quality_score"] = quality_score
        if quality_tier is not _UNSET:
            values["quality_tier"] = quality_tier
        if lifecycle_stage is not _UNSET:
            values["lifecycle_stage"] = lifecycle_stage
        if checksum_sha256 is not _UNSET:
            values["checksum_sha256"] = checksum_sha256
        if file_path is not _UNSET:
            values["file_path"] = file_path
        if metadata_json is not _UNSET:
            values["metadata_json"] = metadata_json

        if not values:
            return await self.get_by_id(dataset_id)

        stmt = (
            update(DatasetModel)
            .where(DatasetModel.id == dataset_id)
            .where(DatasetModel.deleted_at.is_(None))
            .values(**values)
            .returning(DatasetModel.id)
        )
        result = await self._session.execute(stmt)
        if result.scalar_one_or_none() is None:
            return None
        return await self.get_by_id(dataset_id)

    async def soft_delete(self, dataset_id: uuid.UUID) -> bool:
        """Soft-delete a dataset. Returns True if deleted, False if not found."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(DatasetModel)
            .where(DatasetModel.id == dataset_id)
            .where(DatasetModel.deleted_at.is_(None))
            .values(deleted_at=now)
            .returning(DatasetModel.id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None
