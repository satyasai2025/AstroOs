import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone

from packages.audit_engine.snapshot.repository import SnapshotRepository
from packages.audit_engine.snapshot.models import (
    ProvenanceEvent,
    EntityHistory,
    ResearchSnapshotRecord,
)
from packages.audit_engine.snapshot.service import SnapshotService
from packages.audit_engine.snapshot.schema import ModuleName, VersionRef


class TestSnapshotRepository:
    def setup_method(self):
        """Mock session for repository testing."""
        self.session = MagicMock()
        self.repository = SnapshotRepository(self.session)

    def test_create_snapshot_orm(self):
        """Test creating a ResearchSnapshotRecord ORM object."""
        snapshot_data = {
            "name": "test-snapshot",
            "manifest": {"versions": [], "fact_checksum": "abc123"},
            "snapshot_id": "abcdef12",
            "created_at": datetime(2023, 1, 1, tzinfo=timezone.utc),
            "created_by": "test_actor",
        }
        snapshot_obj = self.repository.create_snapshot_orm(snapshot_data)

        assert snapshot_obj.name == "test-snapshot"
        assert snapshot_obj.manifest == {"versions": [], "fact_checksum": "abc123"}
        assert snapshot_obj.snapshot_id == "abcdef12"
        assert snapshot_obj.created_by == "test_actor"
        self.session.add.assert_called_with(snapshot_obj)

    def test_get_snapshot_by_snapshot_id_found(self):
        """Test retrieving a snapshot by snapshot_id when it exists."""
        mock_result = MagicMock()
        self.session.query.return_value.filter_by.return_value.one_or_none.return_value = mock_result

        result = self.repository.get_snapshot_by_snapshot_id("abcdef12")

        self.session.query.assert_called_once_with(ResearchSnapshotRecord)
        self.session.query.return_value.filter_by.assert_called_once_with(snapshot_id="abcdef12")
        assert result is mock_result

    def test_get_snapshot_by_snapshot_id_not_found(self):
        """Test retrieving a snapshot that doesn't exist."""
        self.session.query.return_value.filter_by.return_value.one_or_none.return_value = None

        result = self.repository.get_snapshot_by_snapshot_id("nonexistent")

        assert result is None

    def test_add_provenance_event(self):
        """Test staging a provenance event."""
        event = ProvenanceEvent(
            actor="test_actor",
            timestamp=datetime.now(timezone.utc),
            reason="test_event",
            source="test_source",
            module="research_snapshot",
            version="abcdef12",
        )
        self.repository.add_provenance_event(event)
        self.session.add.assert_called_with(event)

    def test_add_entity_history(self):
        """Test staging an entity history record."""
        history = EntityHistory(
            entity_type="ontology",
            entity_id="ontology_1.0",
        )
        self.repository.add_entity_history(history)
        self.session.add.assert_called_with(history)

    def test_delete_snapshot(self):
        """Test marking a snapshot for deletion."""
        snapshot = MagicMock()
        self.repository.delete_snapshot(snapshot)
        self.session.delete.assert_called_with(snapshot)

    def test_commit_session(self):
        self.repository.commit_session()
        self.session.commit.assert_called_once()

    def test_rollback_session(self):
        self.repository.rollback_session()
        self.session.rollback.assert_called_once()


class TestSnapshotService:
    def setup_method(self):
        """Set up service with mocked repository."""
        self.repository = MagicMock()
        self.service = SnapshotService(self.repository)

        self.actor = "test_actor"
        self.description = "Test Snapshot"
        self.data = {"test": "data"}
        self.config = {
            "ayanamsha": "Lahiri",
            "house_system": "Placidus",
            "node_type": "True Mean",
            "ephemeris_path": "/ephe",
            "timezone_db_version": "2021a",
        }
        self.checksum = "deadbeef" * 8
        self.timestamp = datetime(2023, 11, 30, tzinfo=timezone.utc)

    def test_create_snapshot_flow(self):
        """Test the complete flow of snapshot creation."""
        self.repository.create_snapshot_orm.return_value = MagicMock(snapshot_id="abc123ef")

        version_refs = [
            VersionRef(
                module=ModuleName.ONTOLOGY,
                version="1.0",
                git_commit="commit123",
                checksum="a" * 64,
            ),
        ]

        result = self.service.create_snapshot(
            actor=self.actor,
            data=self.data,
            config=self.config,
            checksum=self.checksum,
            timestamp=self.timestamp,
            description=self.description,
            version_refs=version_refs,
        )

        self.repository.create_snapshot_orm.assert_called_once()
        self.repository.add_provenance_event.assert_called_once()
        self.repository.add_entity_history.assert_called_once()
        assert result is self.repository.create_snapshot_orm.return_value

    def test_create_snapshot_commits_via_service(self):
        self.service.commit_session()
        self.repository.commit_session.assert_called_once()

    def test_hash_snapshot_content(self):
        """Test checksum generation."""
        result = self.service._hash_snapshot_content({"test": "data"})
        assert len(result) == 64  # SHA-256 hash is 64 hex chars

    def test_generate_snapshot_id(self):
        """Test deterministic snapshot ID generation."""
        data = {"key": "value"}
        config = {"setting": "config"}
        snapshot_id = self.service._generate_snapshot_id(data, config)
        assert len(snapshot_id) == 8
        # Run again with same inputs and verify same result
        snapshot_id2 = self.service._generate_snapshot_id(data, config)
        assert snapshot_id == snapshot_id2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
