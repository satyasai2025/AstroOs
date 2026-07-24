from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from .models import EntityHistory, ProvenanceEvent, ResearchSnapshotRecord


class SnapshotRepository:
    """Persistence layer for research snapshots and their provenance trail.

    Pure persistence: no business logic, no manifest/checksum construction.
    Transaction boundaries (commit/rollback) are owned by the caller
    (SnapshotService), per the Router -> Service -> Repository -> ORM
    layering documented in docs/persistence-layer-report.md.

    Schema is the canonical one: the applied migration
    database/versions/0012_snapshot_phase4.py and this package's models.py.
    No event_type/checksum/previous_hash fields -- those belong to an
    unapplied draft (temp.txt) and require a new ADR + migration before use.
    """

    def __init__(self, session: Session) -> None:
        self.session: Session = session

    # -- ResearchSnapshotRecord ----------------------------------------

    def create_snapshot_orm(self, snapshot_data: dict) -> ResearchSnapshotRecord:
        """Stage a new ResearchSnapshotRecord. Does not commit."""
        snapshot = ResearchSnapshotRecord(
            name=snapshot_data["name"],
            manifest=snapshot_data["manifest"],
            snapshot_id=snapshot_data["snapshot_id"],
            created_at=snapshot_data["created_at"],
            created_by=snapshot_data["created_by"],
        )
        self.session.add(snapshot)
        return snapshot

    def get_snapshot_by_snapshot_id(self, snapshot_id: str) -> Optional[ResearchSnapshotRecord]:
        """Look up a snapshot by its content-hash snapshot_id (not the DB primary key)."""
        return (
            self.session.query(ResearchSnapshotRecord)
            .filter_by(snapshot_id=snapshot_id)
            .one_or_none()
        )

    def get_snapshot_by_name(self, name: str) -> Optional[ResearchSnapshotRecord]:
        return (
            self.session.query(ResearchSnapshotRecord)
            .filter_by(name=name)
            .one_or_none()
        )

    def delete_snapshot(self, snapshot: ResearchSnapshotRecord) -> None:
        self.session.delete(snapshot)

    # -- ProvenanceEvent / EntityHistory ---------------------------------

    def add_provenance_event(self, event: ProvenanceEvent) -> None:
        self.session.add(event)

    def add_entity_history(self, history: EntityHistory) -> None:
        self.session.add(history)

    # -- Transaction boundary --------------------------------------------
    # Exposed so SnapshotService can control the unit of work explicitly;
    # the repository never commits/rolls back on its own.

    def commit_session(self) -> None:
        self.session.commit()

    def rollback_session(self) -> None:
        self.session.rollback()
