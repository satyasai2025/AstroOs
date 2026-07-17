"""
AstroOS — Research Engine (Module 17, Phase 1)

Manages research projects, experiments, and astrological snapshots. The
capture, query, and comparison layer for chart data — never performs any
astrology calculation itself.

Project management  → delegates to ResearchRepository
Experiment management → delegates to ResearchRepository
Snapshot capture    → calls existing engines, bundles results into
                      AstrologicalSnapshot, persists via repository
Snapshot query      → loads domain objects, evaluates via SnapshotAccessor
Snapshot comparison → compares two snapshots via SnapshotAccessor.compare()
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any, Optional

from apps.api.domain.research import (
    AstrologicalSnapshot,
    FieldDiff,
    ResearchExperiment,
    ResearchProject,
    SnapshotComparison,
    SnapshotCondition,
    SnapshotQuery,
)
from apps.api.services.snapshot_accessor import SnapshotAccessor


class ResearchEngine:
    """
    Constructed with a ResearchRepository. All methods are async and
    delegate persistence to the repository.

    Snapshot capture optionally takes engine references (HoroscopeEngine,
    YogaEngine, etc.) — if not provided, those sections of the snapshot
    are left as None (graceful degradation).
    """

    _SNAPSHOT_VERSION = "1.0"

    def __init__(self, research_repo=None) -> None:
        self._repo = research_repo

    # ── Project management ────────────────────────────────────────────────

    async def create_project(
        self,
        user_id: uuid.UUID,
        title: str,
        description: Optional[str] = None,
    ) -> ResearchProject:
        return await self._repo.create_project(
            user_id=user_id, title=title, description=description,
        )

    async def update_project(
        self, project_id: uuid.UUID, **fields: Any
    ) -> Optional[ResearchProject]:
        return await self._repo.update_project(project_id, **fields)

    async def get_project(
        self, project_id: uuid.UUID
    ) -> Optional[ResearchProject]:
        return await self._repo.get_project(project_id)

    async def list_projects(
        self, user_id: uuid.UUID, status: Optional[str] = None,
    ) -> tuple[ResearchProject, ...]:
        return await self._repo.list_projects(user_id, status=status)

    async def delete_project(self, project_id: uuid.UUID) -> bool:
        return await self._repo.delete_project(project_id)

    # ── Experiment management ─────────────────────────────────────────────

    async def create_experiment(
        self,
        project_id: uuid.UUID,
        title: str,
        hypothesis: str,
        methodology: str,
    ) -> ResearchExperiment:
        return await self._repo.create_experiment(
            project_id=project_id, title=title,
            hypothesis=hypothesis, methodology=methodology,
        )

    async def update_experiment(
        self, experiment_id: uuid.UUID, **fields: Any,
    ) -> Optional[ResearchExperiment]:
        return await self._repo.update_experiment(experiment_id, **fields)

    async def get_experiment(
        self, experiment_id: uuid.UUID,
    ) -> Optional[ResearchExperiment]:
        return await self._repo.get_experiment(experiment_id)

    async def list_experiments(
        self, project_id: uuid.UUID,
    ) -> tuple[ResearchExperiment, ...]:
        return await self._repo.list_experiments(project_id)

    async def assign_snapshots_to_experiment(
        self,
        experiment_id: uuid.UUID,
        snapshot_ids: list[uuid.UUID],
    ) -> Optional[ResearchExperiment]:
        return await self._repo.assign_snapshots_to_experiment(
            experiment_id, snapshot_ids,
        )

    async def complete_experiment(
        self, experiment_id: uuid.UUID, findings: str,
    ) -> Optional[ResearchExperiment]:
        return await self._repo.update_experiment(
            experiment_id, status="completed", findings=findings,
        )

    # ── Snapshot management ───────────────────────────────────────────────

    async def capture_snapshot(
        self,
        project_id: uuid.UUID,
        chart_id: uuid.UUID,
        label: Optional[str] = None,
        *,
        chart_ref: Any = None,
        yogas: Any = None,
        shadbala_components: Any = None,
        ashtakavarga_data: Any = None,
        dasha_trees: Any = None,
        divisional_charts: Any = None,
        timeline_ref: Any = None,
        verification_ref: Any = None,
        events: Any = None,
    ) -> AstrologicalSnapshot:
        """
        Bundle already-computed engine outputs into an AstrologicalSnapshot
        and persist it. This method does NOT call any engine — callers
        compute engines first and pass results here.

        This design keeps the Research Engine aligned with every other
        engine's "compute once, reuse" discipline. A future convenience
        wrapper can compute + capture in one call if needed.
        """
        captured_at = datetime.now(timezone.utc)
        snapshot = AstrologicalSnapshot(
            id=uuid.uuid4(),
            project_id=project_id,
            chart_id=chart_id,
            label=label,
            captured_at=captured_at,
            chart_ref=chart_ref,
            yogas=yogas,
            shadbala_components=shadbala_components,
            bhinnashtakavarga=ashtakavarga_data[0] if isinstance(ashtakavarga_data, tuple) and ashtakavarga_data else None,
            sarvashtakavarga=ashtakavarga_data[1] if isinstance(ashtakavarga_data, tuple) and len(ashtakavarga_data) > 1 else None,
            dasha_trees=dasha_trees,
            divisional_charts=divisional_charts,
            timeline_ref=timeline_ref,
            verification_ref=verification_ref,
            events=events,
            snapshot_version=self._SNAPSHOT_VERSION,
        )
        return await self._repo.save_snapshot(snapshot)

    async def get_snapshot(
        self, snapshot_id: uuid.UUID,
    ) -> Optional[AstrologicalSnapshot]:
        return await self._repo.get_snapshot(snapshot_id)

    async def list_snapshots(
        self, project_id: uuid.UUID,
    ) -> tuple[AstrologicalSnapshot, ...]:
        return await self._repo.list_snapshots(project_id)

    async def delete_snapshot(self, snapshot_id: uuid.UUID) -> bool:
        return await self._repo.delete_snapshot(snapshot_id)

    # ── Query ─────────────────────────────────────────────────────────────

    async def query_snapshots(
        self,
        project_id: uuid.UUID,
        query: SnapshotQuery,
    ) -> tuple[AstrologicalSnapshot, ...]:
        """
        Load all snapshots for a project and filter by SnapshotQuery
        conditions. Evaluated at the domain level via SnapshotAccessor.
        """
        snapshots = await self._repo.list_snapshots(project_id)
        if not query.conditions:
            return snapshots

        results: list[AstrologicalSnapshot] = []
        for snapshot in snapshots:
            accessor = SnapshotAccessor(snapshot)
            if accessor.search(query):
                results.append(snapshot)
        return tuple(results)

    # ── Comparison ────────────────────────────────────────────────────────

    async def compare_snapshots(
        self,
        snapshot_a_id: uuid.UUID,
        snapshot_b_id: uuid.UUID,
    ) -> Optional[SnapshotComparison]:
        """Compare two snapshots by id. Returns None if either not found."""
        a = await self._repo.get_snapshot(snapshot_a_id)
        b = await self._repo.get_snapshot(snapshot_b_id)
        if a is None or b is None:
            return None

        accessor_a = SnapshotAccessor(a)
        accessor_b = SnapshotAccessor(b)
        return accessor_a.compare(accessor_b)

    async def compare_charts(
        self,
        chart_id_a: uuid.UUID,
        chart_id_b: uuid.UUID,
        project_id: uuid.UUID,
    ) -> Optional[SnapshotComparison]:
        """Compare two charts by finding their snapshots in a project."""
        snapshots = await self._repo.list_snapshots(project_id)
        snap_a = next((s for s in snapshots if s.chart_id == chart_id_a), None)
        snap_b = next((s for s in snapshots if s.chart_id == chart_id_b), None)
        if snap_a is None or snap_b is None:
            return None

        accessor_a = SnapshotAccessor(snap_a)
        accessor_b = SnapshotAccessor(snap_b)
        return accessor_a.compare(accessor_b)
