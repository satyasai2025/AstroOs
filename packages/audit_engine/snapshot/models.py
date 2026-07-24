"""
ORM models for snapshot persistence.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
import uuid

Base = declarative_base()


class ProvenanceEvent(Base):
    """Event sourcing table for all provenance events."""
    __tablename__ = "provenance_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    reason = Column(String, nullable=False)
    source = Column(String, nullable=False)  # manual, migration, pipeline, api
    module = Column(String, nullable=False, index=True)  # facts, ontology, rules, etc.
    version = Column(String, nullable=False)

    # Relationships
    entity_histories = relationship("EntityHistory", back_populates="event", cascade="all, delete-orphan")


class EntityHistory(Base):
    """Tracks which entities were affected by each provenance event."""
    __tablename__ = "entity_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("provenance_events.id"), nullable=False)
    entity_type = Column(String, nullable=False, index=True)  # fact, ontology_node, rule, etc.
    entity_id = Column(String, nullable=False, index=True)  # UUID or identifier of the entity

    event = relationship("ProvenanceEvent", back_populates="entity_histories")


class ResearchSnapshotRecord(Base):
    """Database record for storing snapshots."""
    __tablename__ = "research_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    manifest = Column(JSON, nullable=False)  # Full SnapshotManifest as JSON
    snapshot_id = Column(String(64), nullable=False, unique=True)  # Hash of manifest
    created_at = Column(DateTime(timezone=True), nullable=False)
    created_by = Column(String, nullable=False)

    # Convenience accessors for common manifest fields
    @property
    def versions(self):
        return self.manifest.get('versions', [])

    @property
    def calculation_config(self):
        return self.manifest.get('calculation_config', {})

    @property
    def fact_checksum(self):
        return self.manifest.get('fact_checksum', '')

    @property
    def dataset_checksum(self):
        return self.manifest.get('dataset_checksum', '')