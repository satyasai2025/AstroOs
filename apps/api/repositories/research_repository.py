"""
AstroOS — Research Repository (Module 17, Phase B — Enhanced)

Persistence for research projects, experiments, executions, and snapshots.
Phase B replaces the project-column hack for experiments with dedicated
research_experiments and experiment_executions tables (migration 0009).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.research import (
    AstrologicalSnapshot,
    ExperimentExecution,
    ResearchExperiment,
    ResearchProject,
)
from apps.api.models.astrology import (
    ExperimentExecutionModel,
    ResearchExperimentModel,
    ResearchProjectModel,
    ResearchSnapshotModel,
)


def _project_to_domain(m: ResearchProjectModel) -> ResearchProject:
    return ResearchProject(
        id=m.id, user_id=m.user_id, title=m.title,
        description=m.hypothesis, status=m.status,
        created_at=m.created_at, updated_at=m.updated_at,
        dataset_id=m.dataset_id,
    )


def _experiment_to_domain(m: ResearchExperimentModel) -> ResearchExperiment:
    return ResearchExperiment(
        id=m.id, project_id=m.project_id, title=m.title,
        hypothesis=m.hypothesis or "", methodology=m.methodology or "",
        status=m.status, findings=m.findings,
        rule_registry_hash=m.rule_registry_hash,
        dataset_id=m.dataset_id,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def _execution_to_domain(m: ExperimentExecutionModel) -> ExperimentExecution:
    return ExperimentExecution(
        id=m.id, experiment_id=m.experiment_id,
        snapshot_id=m.snapshot_id,
        execution_order=m.execution_order, notes=m.notes,
        created_at=m.created_at,
    )


def _snapshot_to_domain(m: ResearchSnapshotModel) -> AstrologicalSnapshot:
    data = json.loads(m.snapshot_json) if m.snapshot_json else {}
    return AstrologicalSnapshot(
        id=m.id, project_id=m.project_id, chart_id=m.chart_id,
        label=m.label,
        captured_at=m.created_at or datetime.now(timezone.utc),
        chart_ref=None,
        dataset_id=data.get("dataset_id"),
        snapshot_version=data.get("version", "1.0"),
    )


class ResearchRepository:
    """Data access for research projects, experiments, and snapshots."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Projects ──────────────────────────────────────────────────────────

    async def create_project(
        self, user_id: uuid.UUID, title: str,
        description: Optional[str] = None,
        dataset_id: Optional[uuid.UUID] = None,
    ) -> ResearchProject:
        m = ResearchProjectModel(
            user_id=user_id, title=title,
            hypothesis=description, status="active",
            dataset_id=dataset_id,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _project_to_domain(m)

    async def get_project(
        self, project_id: uuid.UUID,
    ) -> Optional[ResearchProject]:
        stmt = select(ResearchProjectModel).where(
            ResearchProjectModel.id == project_id,
            ResearchProjectModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _project_to_domain(row) if row else None

    async def list_projects(
        self, user_id: uuid.UUID, status: Optional[str] = None,
    ) -> tuple[ResearchProject, ...]:
        stmt = (
            select(ResearchProjectModel)
            .where(ResearchProjectModel.user_id == user_id)
            .where(ResearchProjectModel.deleted_at.is_(None))
        )
        if status:
            stmt = stmt.where(ResearchProjectModel.status == status)
        stmt = stmt.order_by(ResearchProjectModel.created_at.desc())
        rows = (await self._session.execute(stmt)).scalars().all()
        return tuple(_project_to_domain(r) for r in rows)

    async def update_project(
        self, project_id: uuid.UUID, **fields: Any,
    ) -> Optional[ResearchProject]:
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
            .values(**orm_fields).returning(ResearchProjectModel.id)
        )
        if (await self._session.execute(stmt)).scalar_one_or_none() is None:
            return None
        return await self.get_project(project_id)

    async def delete_project(self, project_id: uuid.UUID) -> bool:
        now = datetime.now(timezone.utc)
        stmt = (
            update(ResearchProjectModel)
            .where(ResearchProjectModel.id == project_id)
            .where(ResearchProjectModel.deleted_at.is_(None))
            .values(deleted_at=now).returning(ResearchProjectModel.id)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none() is not None

    # ── Experiments (dedicated table) ─────────────────────────────────────

    async def create_experiment(
        self, project_id: uuid.UUID, title: str,
        hypothesis: str, methodology: str,
        rule_registry_hash: Optional[str] = None,
        dataset_id: Optional[uuid.UUID] = None,
    ) -> ResearchExperiment:
        m = ResearchExperimentModel(
            project_id=project_id, title=title,
            hypothesis=hypothesis, methodology=methodology,
            status="draft", rule_registry_hash=rule_registry_hash,
            dataset_id=dataset_id,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _experiment_to_domain(m)

    async def get_experiment(
        self, experiment_id: uuid.UUID,
    ) -> Optional[ResearchExperiment]:
        stmt = select(ResearchExperimentModel).where(
            ResearchExperimentModel.id == experiment_id,
            ResearchExperimentModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _experiment_to_domain(row) if row else None

    async def list_experiments(
        self, project_id: uuid.UUID,
    ) -> tuple[ResearchExperiment, ...]:
        stmt = (
            select(ResearchExperimentModel)
            .where(ResearchExperimentModel.project_id == project_id)
            .where(ResearchExperimentModel.deleted_at.is_(None))
            .order_by(ResearchExperimentModel.created_at.desc())
        )
        return tuple(
            _experiment_to_domain(r)
            for r in (await self._session.execute(stmt)).scalars().all()
        )

    async def update_experiment(
        self, experiment_id: uuid.UUID, **fields: Any,
    ) -> Optional[ResearchExperiment]:
        orm_fields: dict[str, Any] = {}
        for key in ("title", "hypothesis", "methodology", "status", "findings", "rule_registry_hash"):
            if key in fields:
                orm_fields[key] = fields[key]

        if not orm_fields:
            return await self.get_experiment(experiment_id)

        stmt = (
            update(ResearchExperimentModel)
            .where(ResearchExperimentModel.id == experiment_id)
            .where(ResearchExperimentModel.deleted_at.is_(None))
            .values(**orm_fields).returning(ResearchExperimentModel.id)
        )
        if (await self._session.execute(stmt)).scalar_one_or_none() is None:
            return None
        return await self.get_experiment(experiment_id)

    async def delete_experiment(self, experiment_id: uuid.UUID) -> bool:
        now = datetime.now(timezone.utc)
        stmt = (
            update(ResearchExperimentModel)
            .where(ResearchExperimentModel.id == experiment_id)
            .where(ResearchExperimentModel.deleted_at.is_(None))
            .values(deleted_at=now).returning(ResearchExperimentModel.id)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none() is not None

    # ── Experiment Executions ─────────────────────────────────────────────

    async def create_execution(
        self, experiment_id: uuid.UUID,
        snapshot_id: Optional[uuid.UUID] = None,
        execution_order: int = 0,
        notes: Optional[str] = None,
    ) -> ExperimentExecution:
        m = ExperimentExecutionModel(
            experiment_id=experiment_id, snapshot_id=snapshot_id,
            execution_order=execution_order, notes=notes,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _execution_to_domain(m)

    async def list_executions(
        self, experiment_id: uuid.UUID,
    ) -> tuple[ExperimentExecution, ...]:
        stmt = (
            select(ExperimentExecutionModel)
            .where(ExperimentExecutionModel.experiment_id == experiment_id)
            .order_by(ExperimentExecutionModel.execution_order)
        )
        return tuple(
            _execution_to_domain(r)
            for r in (await self._session.execute(stmt)).scalars().all()
        )

    # ── Snapshots ─────────────────────────────────────────────────────────

    async def save_snapshot(
        self, snapshot: AstrologicalSnapshot,
    ) -> AstrologicalSnapshot:
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
        if snapshot.dataset_id is not None:
            serialized["dataset_id"] = str(snapshot.dataset_id)

        m = ResearchSnapshotModel(
            id=snapshot.id, project_id=snapshot.project_id,
            chart_id=snapshot.chart_id, label=snapshot.label,
            snapshot_json=json.dumps(serialized),
        )
        m = await self._session.merge(m)
        await self._session.flush()
        return snapshot

    async def get_snapshot(
        self, snapshot_id: uuid.UUID,
    ) -> Optional[AstrologicalSnapshot]:
        stmt = select(ResearchSnapshotModel).where(
            ResearchSnapshotModel.id == snapshot_id,
            ResearchSnapshotModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
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
        return tuple(
            _snapshot_to_domain(r)
            for r in (await self._session.execute(stmt)).scalars().all()
        )

    async def delete_snapshot(self, snapshot_id: uuid.UUID) -> bool:
        now = datetime.now(timezone.utc)
        stmt = (
            update(ResearchSnapshotModel)
            .where(ResearchSnapshotModel.id == snapshot_id)
            .where(ResearchSnapshotModel.deleted_at.is_(None))
            .values(deleted_at=now).returning(ResearchSnapshotModel.id)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none() is not None
