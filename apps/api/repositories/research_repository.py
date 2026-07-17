"""
AstroOS — Research Repository (Module 17, Phase 1)

Persistence for research projects, experiments, and astrological snapshots.
Uses the existing `research_projects` and `research_snapshots` tables
(migration 0002). ResearchExperiment data is stored in the project table's
existing hypothesis/methodology/conclusions columns for Phase 1 (one
active experiment per project); a future migration can add a dedicated
experiments table.

Returns domain objects, never ORM models directly — same convention as
every other repository in this codebase.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.research import (
    AstrologicalSnapshot,
    ResearchExperiment,
    ResearchProject,
)
from apps.api.models.astrology import ResearchProjectModel, ResearchSnapshotModel

# Fields on ResearchProject that map to ResearchExperiment.
_EXPERIMENT_FIELDS = {"hypothesis", "methodology", "conclusions"}


def _project_to_domain(model: ResearchProjectModel) -> ResearchProject:
    return ResearchProject(
        id=model.id,
        user_id=model.user_id,
        title=model.title,
        description=model.hypothesis,  # reuse hypothesis column as description for now
        status=model.status,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _project_to_experiment(model: ResearchProjectModel) -> ResearchExperiment:
    return ResearchExperiment(
        id=model.id,
        project_id=model.id,
        title=model.title,
        hypothesis=model.hypothesis or "",
        methodology=model.methodology or "",
        status="completed" if model.conclusions else "draft",
        findings=model.conclusions,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _snapshot_to_domain(model: ResearchSnapshotModel) -> AstrologicalSnapshot:
    data = json.loads(model.snapshot_json) if model.snapshot_json else {}
    return AstrologicalSnapshot(
        id=model.id,
        project_id=model.project_id,
        chart_id=model.chart_id,
        label=model.label,
        captured_at=model.created_at or datetime.now(timezone.utc),
        chart_ref=None,  # populated from chart_id lookup when accessed
        snapshot_version=data.get("version", "1.0"),
    )


class ResearchRepository:
    """Data access for research projects and snapshots."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Projects ──────────────────────────────────────────────────────────

    async def create_project(
        self,
        user_id: uuid.UUID,
        title: str,
        description: Optional[str] = None,
    ) -> ResearchProject:
        model = ResearchProjectModel(
            user_id=user_id,
            title=title,
            hypothesis=description,  # reuse hypothesis column for description
            status="active",
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _project_to_domain(model)

    async def get_project(
        self, project_id: uuid.UUID,
    ) -> Optional[ResearchProject]:
        stmt = select(ResearchProjectModel).where(
            ResearchProjectModel.id == project_id,
            ResearchProjectModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _project_to_domain(row) if row else None

    async def list_projects(
        self, user_id: uuid.UUID,
        status: Optional[str] = None,
    ) -> tuple[ResearchProject, ...]:
        stmt = (
            select(ResearchProjectModel)
            .where(ResearchProjectModel.user_id == user_id)
            .where(ResearchProjectModel.deleted_at.is_(None))
        )
        if status:
            stmt = stmt.where(ResearchProjectModel.status == status)
        stmt = stmt.order_by(ResearchProjectModel.created_at.desc())
        result = await self._session.execute(stmt)
        return tuple(_project_to_domain(row) for row in result.scalars().all())

    async def update_project(
        self, project_id: uuid.UUID, **fields: Any,
    ) -> Optional[ResearchProject]:
        # Map domain fields back to ORM fields.
        orm_fields: dict[str, Any] = {}
        if "title" in fields:
            orm_fields["title"] = fields["title"]
        if "description" in fields:
            orm_fields["hypothesis"] = fields["description"]
        if "status" in fields:
            orm_fields["status"] = fields["status"]

        if not orm_fields:
            return await self.get_project(project_id)

        stmt = (
            update(ResearchProjectModel)
            .where(ResearchProjectModel.id == project_id)
            .where(ResearchProjectModel.deleted_at.is_(None))
            .values(**orm_fields)
            .returning(ResearchProjectModel.id)
        )
        result = await self._session.execute(stmt)
        if result.scalar_one_or_none() is None:
            return None
        return await self.get_project(project_id)

    async def delete_project(self, project_id: uuid.UUID) -> bool:
        now = datetime.now(timezone.utc)
        stmt = (
            update(ResearchProjectModel)
            .where(ResearchProjectModel.id == project_id)
            .where(ResearchProjectModel.deleted_at.is_(None))
            .values(deleted_at=now)
            .returning(ResearchProjectModel.id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    # ── Experiments (stored in project table) ─────────────────────────────

    async def create_experiment(
        self,
        project_id: uuid.UUID,
        title: str,
        hypothesis: str,
        methodology: str,
    ) -> ResearchExperiment:
        # Update the existing project row with experiment data.
        stmt = (
            update(ResearchProjectModel)
            .where(ResearchProjectModel.id == project_id)
            .where(ResearchProjectModel.deleted_at.is_(None))
            .values(title=title, hypothesis=hypothesis, methodology=methodology, conclusions=None)
            .returning(ResearchProjectModel.id)
        )
        result = await self._session.execute(stmt)
        if result.scalar_one_or_none() is None:
            raise ValueError(f"Project {project_id} not found or deleted")

        # Re-fetch to get the full model.
        model = await self._session.get(ResearchProjectModel, project_id)
        return _project_to_experiment(model)

    async def get_experiment(
        self, experiment_id: uuid.UUID,
    ) -> Optional[ResearchExperiment]:
        project = await self.get_project(experiment_id)
        if project is None:
            return None
        model = await self._session.get(ResearchProjectModel, experiment_id)
        return _project_to_experiment(model)

    async def list_experiments(
        self, project_id: uuid.UUID,
    ) -> tuple[ResearchExperiment, ...]:
        """Return experiments for a project. Phase 1: returns one."""
        model = await self._session.get(ResearchProjectModel, project_id)
        if model is None or model.deleted_at is not None:
            return ()
        return (_project_to_experiment(model),)

    async def assign_snapshots_to_experiment(
        self,
        experiment_id: uuid.UUID,
        snapshot_ids: list[uuid.UUID],
    ) -> Optional[ResearchExperiment]:
        # Phase 1: snapshots are linked to the project.
        # No schema change needed — snapshot.project_id already links them.
        project = await self.get_project(experiment_id)
        if project is None:
            return None
        return await self.get_experiment(experiment_id)

    async def update_experiment(
        self, experiment_id: uuid.UUID, **fields: Any,
    ) -> Optional[ResearchExperiment]:
        orm_fields: dict[str, Any] = {}
        if "title" in fields:
            orm_fields["title"] = fields["title"]
        if "hypothesis" in fields:
            orm_fields["hypothesis"] = fields["hypothesis"]
        if "methodology" in fields:
            orm_fields["methodology"] = fields["methodology"]
        if "findings" in fields:
            orm_fields["conclusions"] = fields["findings"]
        if "status" in fields:
            orm_fields["status"] = fields["status"]

        if not orm_fields:
            return await self.get_experiment(experiment_id)

        stmt = (
            update(ResearchProjectModel)
            .where(ResearchProjectModel.id == experiment_id)
            .where(ResearchProjectModel.deleted_at.is_(None))
            .values(**orm_fields)
            .returning(ResearchProjectModel.id)
        )
        result = await self._session.execute(stmt)
        if result.scalar_one_or_none() is None:
            return None
        return await self.get_experiment(experiment_id)

    # ── Snapshots ─────────────────────────────────────────────────────────

    async def save_snapshot(
        self, snapshot: AstrologicalSnapshot,
    ) -> AstrologicalSnapshot:
        """Persist a snapshot, serializing engine data to JSON."""
        serialized: dict[str, Any] = {
            "version": snapshot.snapshot_version,
            "captured_at": snapshot.captured_at.isoformat(),
        }
        if snapshot.yogas is not None:
            serialized["yogas"] = [
                {"yoga_id": y.yoga_id, "is_present": y.is_present,
                 "strength": y.strength.value if y.strength else None}
                for y in snapshot.yogas
            ]
        if snapshot.sarvashtakavarga is not None:
            serialized["sarvashtakavarga_total"] = snapshot.sarvashtakavarga.total_bindus

        model = ResearchSnapshotModel(
            id=snapshot.id,
            project_id=snapshot.project_id,
            chart_id=snapshot.chart_id,
            label=snapshot.label,
            snapshot_json=json.dumps(serialized),
        )
        # Use merge for idempotent re-save.
        model = await self._session.merge(model)
        await self._session.flush()
        return snapshot

    async def get_snapshot(
        self, snapshot_id: uuid.UUID,
    ) -> Optional[AstrologicalSnapshot]:
        stmt = select(ResearchSnapshotModel).where(
            ResearchSnapshotModel.id == snapshot_id,
            ResearchSnapshotModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _snapshot_to_domain(row) if row else None

    async def list_snapshots(
        self, project_id: uuid.UUID,
    ) -> tuple[AstrologicalSnapshot, ...]:
        stmt = (
            select(ResearchSnapshotModel)
            .where(ResearchSnapshotModel.project_id == project_id)
            .where(ResearchSnapshotModel.deleted_at.is_(None))
            .order_by(ResearchSnapshotModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return tuple(_snapshot_to_domain(row) for row in result.scalars().all())

    async def delete_snapshot(self, snapshot_id: uuid.UUID) -> bool:
        now = datetime.now(timezone.utc)
        stmt = (
            update(ResearchSnapshotModel)
            .where(ResearchSnapshotModel.id == snapshot_id)
            .where(ResearchSnapshotModel.deleted_at.is_(None))
            .values(deleted_at=now)
            .returning(ResearchSnapshotModel.id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None
