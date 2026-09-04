"""
AstroOS — Dataset Service

Orchestrates dataset registry operations. Following the ResearchEngine
pattern: thin delegation to repository for CRUD, with cross-cutting
orchestration for post-import registration.

Designed to be called AFTER the file-based import pipeline completes.
Database persistence is optional — if the DB is unavailable, the import
still succeeds and this service reports that persistence was skipped.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from apps.api.domain.dataset import Dataset
from apps.api.repositories.dataset_repository import DatasetRepository


class DatasetService:
    """Manages the dataset registry."""

    def __init__(self, repo: DatasetRepository) -> None:
        self._repo = repo

    async def create_dataset(self, **kwargs: Any) -> Dataset:
        """Create a new dataset record."""
        return await self._repo.create(**kwargs)

    async def get_by_id(self, dataset_id: uuid.UUID) -> Optional[Dataset]:
        return await self._repo.get_by_id(dataset_id)

    async def get_by_dataset_id(self, dataset_id_str: str) -> Optional[Dataset]:
        return await self._repo.get_by_dataset_id(dataset_id_str)

    async def list_datasets(
        self,
        lifecycle_stage: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[Dataset, ...]:
        return await self._repo.list(
            lifecycle_stage=lifecycle_stage, limit=limit, offset=offset,
        )

    async def update_dataset(self, dataset_id: uuid.UUID, **fields: Any) -> Optional[Dataset]:
        return await self._repo.update(dataset_id, **fields)

    async def delete_dataset(self, dataset_id: uuid.UUID) -> bool:
        return await self._repo.soft_delete(dataset_id)

    async def record_import(
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
        checksum_sha256: Optional[str] = None,
        file_path: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
        created_by: Optional[uuid.UUID] = None,
    ) -> Optional[Dataset]:
        """Record a completed import in the database.

        This is called AFTER the file-based pipeline succeeds. Returns None
        if persistence fails (caller should log but not fail the import).
        """
        try:
            return await self._repo.create(
                dataset_id=dataset_id,
                name=name,
                description=description,
                source_file=source_file,
                format=format,
                record_count=record_count,
                field_count=field_count,
                quality_score=quality_score,
                quality_tier=quality_tier,
                lifecycle_stage="Candidacy",
                checksum_sha256=checksum_sha256,
                file_path=file_path,
                metadata_json=metadata_json,
                created_by=created_by,
            )
        except Exception:
            return None
