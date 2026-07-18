"""
AstroOS — Datasets CRUD Router

HTTP adapter layer for the Dataset registry. Delegates all logic to
DatasetService. No business logic lives here — only request parsing,
DTO/schema conversion, and HTTP error mapping.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError

from apps.api.dependencies import get_dataset_service, get_current_user_from_bearer
from apps.api.domain.dataset import Dataset
from apps.api.schemas.dataset import (
    DatasetCreateRequest,
    DatasetListResponse,
    DatasetResponse,
    DatasetUpdateRequest,
)
from apps.api.services.dataset_service import DatasetService

router = APIRouter(prefix="/api/v1/datasets", tags=["Datasets"])


# ── DTO -> Schema converter ─────────────────────────────────────────────────


def _dataset_to_response(d: Dataset) -> DatasetResponse:
    return DatasetResponse(
        id=d.id,
        dataset_id=d.dataset_id,
        name=d.name,
        description=d.description,
        source_file=d.source_file,
        format=d.format,
        record_count=d.record_count,
        field_count=d.field_count,
        quality_score=d.quality_score,
        quality_tier=d.quality_tier,
        lifecycle_stage=d.lifecycle_stage,
        checksum_sha256=d.checksum_sha256,
        file_path=d.file_path,
        created_by=d.created_by,
        created_at=d.created_at,
        updated_at=d.updated_at,
    )


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new dataset.",
)
async def create_dataset(
    body: DatasetCreateRequest,
    service: DatasetService = Depends(get_dataset_service),
    _=Depends(get_current_user_from_bearer),
) -> DatasetResponse:
    try:
        d = await service.create_dataset(**body.model_dump())
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A dataset with this ID already exists.",
        ) from exc
    return _dataset_to_response(d)


@router.get(
    "/{dataset_id}",
    response_model=DatasetResponse,
    summary="Retrieve a dataset by UUID.",
)
async def get_dataset(
    dataset_id: uuid.UUID,
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetResponse:
    d = await service.get_by_id(dataset_id)
    if d is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")
    return _dataset_to_response(d)


@router.get(
    "/by-id/{external_id}",
    response_model=DatasetResponse,
    summary="Retrieve a dataset by external dataset_id string.",
)
async def get_dataset_by_external_id(
    external_id: str,
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetResponse:
    d = await service.get_by_dataset_id(external_id)
    if d is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")
    return _dataset_to_response(d)


@router.get(
    "",
    response_model=DatasetListResponse,
    summary="List datasets.",
)
async def list_datasets(
    lifecycle_stage: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetListResponse:
    records = await service.list_datasets(
        lifecycle_stage=lifecycle_stage, limit=limit, offset=offset,
    )
    return DatasetListResponse(
        datasets=[_dataset_to_response(r) for r in records],
        total=len(records),
    )


@router.patch(
    "/{dataset_id}",
    response_model=DatasetResponse,
    summary="Partially update a dataset.",
)
async def update_dataset(
    dataset_id: uuid.UUID,
    body: DatasetUpdateRequest,
    service: DatasetService = Depends(get_dataset_service),
    _=Depends(get_current_user_from_bearer),
) -> DatasetResponse:
    provided_fields = body.model_dump(exclude_unset=True)
    d = await service.update_dataset(dataset_id, **provided_fields)
    if d is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")
    return _dataset_to_response(d)


@router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a dataset.",
)
async def delete_dataset(
    dataset_id: uuid.UUID,
    service: DatasetService = Depends(get_dataset_service),
    _=Depends(get_current_user_from_bearer),
) -> None:
    deleted = await service.delete_dataset(dataset_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")
