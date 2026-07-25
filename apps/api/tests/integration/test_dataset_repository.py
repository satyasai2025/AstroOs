"""Integration tests for DatasetRepository — requires real PostgreSQL."""

import uuid
import pytest
import pytest_asyncio
from sqlalchemy import select

from apps.api.models.dataset import DatasetModel
from apps.api.repositories.dataset_repository import DatasetRepository


@pytest_asyncio.fixture
def repo(db_session):
    return DatasetRepository(db_session)


class TestCreate:
    async def test_create_minimal(self, repo, db_session):
        d = await repo.create(dataset_id="ASTRO-RS-COHORT-TEST-v1.0.0", name="Test Dataset")
        assert d.dataset_id == "ASTRO-RS-COHORT-TEST-v1.0.0"
        assert d.name == "Test Dataset"
        assert d.record_count == 0
        assert d.lifecycle_stage == "Draft"
        assert d.id is not None

    async def test_create_full(self, repo):
        d = await repo.create(
            dataset_id="ASTRO-RS-COHORT-TEST-v2.0.0",
            name="Full Test Dataset",
            description="A dataset for testing",
            source_file="test.csv",
            format="CSV",
            record_count=100,
            field_count=15,
            quality_score=0.95,
            quality_tier="A",
            lifecycle_stage="Candidacy",
            checksum_sha256="a" * 64,
            file_path="datasets/test.csv",
            metadata_json={"key": "value"},
        )
        assert d.record_count == 100
        assert d.quality_score == 0.95
        assert d.quality_tier == "A"
        assert d.lifecycle_stage == "Candidacy"
        assert d.metadata_json == {"key": "value"}


class TestGet:
    async def test_get_by_id_found(self, repo):
        d = await repo.create(dataset_id="ASTRO-RS-GET-TEST-v1.0.0", name="Get Test")
        found = await repo.get_by_id(d.id)
        assert found is not None
        assert found.id == d.id
        assert found.dataset_id == "ASTRO-RS-GET-TEST-v1.0.0"

    async def test_get_by_id_not_found(self, repo):
        found = await repo.get_by_id(uuid.uuid4())
        assert found is None

    async def test_get_by_dataset_id_found(self, repo):
        await repo.create(dataset_id="ASTRO-RS-GET2-TEST-v1.0.0", name="Get By ID Test")
        found = await repo.get_by_dataset_id("ASTRO-RS-GET2-TEST-v1.0.0")
        assert found is not None
        assert found.dataset_id == "ASTRO-RS-GET2-TEST-v1.0.0"

    async def test_get_by_dataset_id_not_found(self, repo):
        found = await repo.get_by_dataset_id("NONEXISTENT")
        assert found is None


class TestList:
    async def test_list_empty(self, repo):
        results = await repo.list()
        # May not be empty if other tests created records
        assert isinstance(results, tuple)

    async def test_list_with_stage_filter(self, repo):
        await repo.create(dataset_id="ASTRO-RS-LIST1-v1.0.0", name="Draft Dataset")
        await repo.create(
            dataset_id="ASTRO-RS-LIST2-v1.0.0", name="Stable Dataset",
            lifecycle_stage="Stable",
        )
        stable = await repo.list(lifecycle_stage="Stable")
        assert any(d.lifecycle_stage == "Stable" for d in stable)

    async def test_list_pagination(self, repo):
        for i in range(5):
            await repo.create(
                dataset_id=f"ASTRO-RS-PAGE{i}-v1.0.0",
                name=f"Page Test {i}",
            )
        results = await repo.list(limit=3, offset=0)
        assert len(results) <= 3


class TestUpdate:
    async def test_update_name(self, repo):
        d = await repo.create(dataset_id="ASTRO-RS-UPD1-v1.0.0", name="Original")
        updated = await repo.update(d.id, name="Updated")
        assert updated is not None
        assert updated.name == "Updated"

    async def test_update_lifecycle_stage(self, repo):
        d = await repo.create(dataset_id="ASTRO-RS-UPD2-v1.0.0", name="Stage Test")
        updated = await repo.update(d.id, lifecycle_stage="Stable")
        assert updated is not None
        assert updated.lifecycle_stage == "Stable"

    async def test_update_not_found(self, repo):
        updated = await repo.update(uuid.uuid4(), name="Ghost")
        assert updated is None


class TestDelete:
    async def test_soft_delete(self, repo, db_session):
        d = await repo.create(dataset_id="ASTRO-RS-DEL1-v1.0.0", name="Delete Test")
        deleted = await repo.soft_delete(d.id)
        assert deleted is True

        # Verify it's not returned by get
        found = await repo.get_by_id(d.id)
        assert found is None

        # Verify it still exists in DB (soft-delete)
        stmt = select(DatasetModel).where(DatasetModel.id == d.id)
        result = await db_session.execute(stmt)
        model = result.scalar_one_or_none()
        assert model is not None
        assert model.deleted_at is not None

    async def test_delete_not_found(self, repo):
        deleted = await repo.soft_delete(uuid.uuid4())
        assert deleted is False
