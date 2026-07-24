"""
Snapshot Service -- business logic for snapshot creation and provenance.

Responsibilities:
- Validate input, build the SnapshotManifest
- Generate the deterministic snapshot_id
- Emit one ProvenanceEvent per snapshot creation
- Record EntityHistory rows for each versioned module in the manifest
- Own the transaction boundary (commit/rollback); SnapshotRepository is a
  pure persistence layer and never commits on its own.

Schema note: ProvenanceEvent/EntityHistory here match the canonical,
applied schema (models.py + database/versions/0012_snapshot_phase4.py) --
actor/timestamp/reason/source/module/version, no event_type/checksum/
previous_hash. Those fields exist only in an unapplied draft (temp.txt)
and require a new ADR + migration before this service can use them.
"""

from __future__ import annotations

import hashlib
import json
import uuid as uuid_lib
from datetime import datetime
from typing import Any, Dict, List, Optional

from packages.audit_engine.snapshot.schema import (
    CalculationConfig,
    SnapshotManifest,
    VersionRef,
)

from .models import EntityHistory, ProvenanceEvent, ResearchSnapshotRecord
from .repository import SnapshotRepository


class SnapshotService:
    def __init__(self, repository: SnapshotRepository) -> None:
        self.repository = repository

    def create_snapshot(
        self,
        actor: str,
        data: Dict[str, Any],
        config: Dict[str, Any],
        checksum: str,
        timestamp: datetime,
        description: Optional[str] = None,
        version_refs: Optional[List[VersionRef]] = None,
    ) -> ResearchSnapshotRecord:
        """Stage a research snapshot plus its provenance event and entity
        history records. Does not commit -- call commit_session() once the
        whole unit of work is staged.
        """
        version_refs = version_refs or []
        snapshot_id = self._generate_snapshot_id(data, config)

        manifest = SnapshotManifest(
            versions=version_refs,
            calculation_config=CalculationConfig(**config),
            fact_checksum=checksum,
            dataset_checksum=checksum,
            timestamp=timestamp,
            description=description,
        )

        snapshot = self.repository.create_snapshot_orm(
            {
                "name": description or f"snapshot-{snapshot_id}",
                "manifest": manifest.model_dump(mode="json"),
                "snapshot_id": snapshot_id,
                "created_at": timestamp,
                "created_by": actor,
            }
        )

        event = ProvenanceEvent(
            id=uuid_lib.uuid4(),
            actor=actor,
            timestamp=timestamp,
            reason=description or "snapshot_created",
            source="snapshot_service",
            module="research_snapshot",
            version=snapshot_id,
        )
        self.repository.add_provenance_event(event)

        for ref in version_refs:
            history = EntityHistory(
                event_id=event.id,
                entity_type=ref.module.value,
                entity_id=f"{ref.module.value}_{ref.version}",
            )
            self.repository.add_entity_history(history)

        return snapshot

    def _generate_snapshot_id(self, data: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Deterministic 8-char ID from a hash of data + config."""
        combined = json.dumps({"data": data, "config": config}, sort_keys=True, default=str)
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()[:8]

    def _hash_snapshot_content(self, data: Dict[str, Any]) -> str:
        """Full SHA-256 hex digest of arbitrary snapshot content."""
        return hashlib.sha256(
            json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

    def commit_session(self) -> None:
        self.repository.commit_session()

    def rollback_session(self) -> None:
        self.repository.rollback_session()
