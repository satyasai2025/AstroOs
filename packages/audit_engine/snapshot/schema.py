from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class ModuleName(str, Enum):
    ONTOLOGY = "ontology"
    RULES = "rules"
    CALCULATION_ENGINE = "calculation_engine"
    EPHEMERIS = "ephemeris"
    DATASET = "dataset"
    FACTS = "facts"
    TIMEZONE_DB = "timezone_db"
    # Add more as needed


class VersionRef(BaseModel):
    """Reference to a specific version of a module or data."""
    module: ModuleName
    version: str = Field(..., description="Human-readable version (e.g., git tag, release version)")
    git_commit: str = Field(..., description="Git commit hash for the module's source code")
    checksum: str = Field(..., description="SHA256 checksum of the module's content or data")

    @field_validator('checksum')
    @classmethod
    def checksum_must_be_hex(cls, v: str) -> str:
        if not all(c in '0123456789abcdefABCDEF' for c in v):
            raise ValueError('checksum must be a hexadecimal string')
        if len(v) != 64:
            raise ValueError('checksum must be 64 characters long (SHA256)')
        return v.lower()


class CalculationConfig(BaseModel):
    """Immutable configuration affecting astronomical calculations."""
    ayanamsha: str = Field(..., description="Ayanamsha value or name (e.g., 'Lahiri', 'Raman')")
    house_system: str = Field(..., description="House system (e.g., 'Placidus', 'Koch', 'Equal')")
    node_type: str = Field(..., description="Lunar node type (True Mean, True Oscillating, etc.)")
    ephemeris_path: str = Field(..., description="Path or identifier for Swiss Ephemeris files")
    timezone_db_version: str = Field(..., description="Version of timezone database (e.g., '2021a')")
    calculation_settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional calculation flags (e.g., precision, flags for nutation, etc.)"
    )
    enabled_modules: List[str] = Field(
        default_factory=list,
        description="List of enabled feature modules (e.g., ['shadbala', 'ashtakavarga'])"
    )
    rule_ordering: List[str] = Field(
        default_factory=list,
        description="Ordered list of rule IDs as they should be executed"
    )


class SnapshotManifest(BaseModel):
    """
    Immutable manifest representing the exact state of a research experiment.
    This is the canonical representation used for reproducibility.
    """
    model_config = ConfigDict(frozen=True)

    versions: List[VersionRef] = Field(
        ..., description="List of version references for all modules and data"
    )
    calculation_config: CalculationConfig = Field(
        ..., description="Immutable calculation configuration"
    )
    fact_checksum: str = Field(
        ..., description="SHA256 checksum of the facts dataset at snapshot time"
    )
    dataset_checksum: str = Field(
        ..., description="SHA256 checksum of the input dataset used"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when the snapshot was created"
    )
    description: Optional[str] = Field(
        None, description="Optional human-readable description of the experiment"
    )

    @field_serializer('timestamp', when_used='json')
    def _serialize_timestamp(self, v: datetime) -> str:
        # Matches the old Pydantic v1 json_encoders behavior exactly: only
        # applies during JSON serialization, never to plain dict()/model_dump().
        return v.isoformat() + 'Z' if v.tzinfo is None else v.isoformat()

    # Computed field: hash of the entire manifest for integrity
    @property
    def snapshot_id(self) -> str:
        import hashlib
        import json
        manifest_json = json.dumps(self.model_dump(mode="json"), sort_keys=True)
        return hashlib.sha256(manifest_json.encode('utf-8')).hexdigest()
