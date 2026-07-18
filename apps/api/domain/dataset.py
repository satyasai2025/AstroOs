"""
AstroOS — Dataset Domain Object

Pure Python dataclass — no ORM/Pydantic dependency.
Represents an imported dataset record in the platform.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Dataset:
    """An imported dataset registered in the platform."""

    id: uuid.UUID
    dataset_id: str
    name: str
    description: Optional[str] = None
    source_file: Optional[str] = None
    format: Optional[str] = None
    record_count: int = 0
    field_count: int = 0
    quality_score: Optional[float] = None
    quality_tier: Optional[str] = None
    lifecycle_stage: str = "Draft"
    checksum_sha256: Optional[str] = None
    file_path: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_by: Optional[uuid.UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
