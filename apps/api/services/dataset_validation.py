"""
AstroOS — Dataset Validation Service (Module 27, Phase 3c)

Read-only integrity report over already-imported research case data — an
Advanced Research maintenance tool. Distinct from the existing
POST /cases/validate (apps.api.routers.research), which validates a
not-yet-persisted batch payload before import; this instead audits data
that's already in the database, e.g. after a partial import or an engine
version bump that left some cases on an older snapshot_version.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.models.research_case import ResearchCaseModel
from apps.api.services.import_service import CURRENT_SNAPSHOT_VERSION


@dataclass(frozen=True)
class DatasetValidationReport:
    total_cases: int
    cases_without_snapshots: list[str] = field(default_factory=list)
    life_events_without_snapshots: int = 0
    stale_snapshot_case_ids: list[str] = field(default_factory=list)
    duplicate_case_ids: list[str] = field(default_factory=list)


class DatasetValidationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def validate(self) -> DatasetValidationReport:
        case_models = (
            await self._session.execute(
                select(ResearchCaseModel).where(ResearchCaseModel.deleted_at.is_(None))
            )
        ).scalars().all()

        cases_without_snapshots: list[str] = []
        stale_case_ids: list[str] = []
        duplicate_case_ids: list[str] = []
        life_events_without_snapshots = 0

        for case in case_models:
            if case.duplicate_of_id is not None:
                duplicate_case_ids.append(case.research_case_id)

            has_any_snapshot = False
            has_current_version = False
            for event in case.life_events:
                if not event.snapshots:
                    life_events_without_snapshots += 1
                    continue
                has_any_snapshot = True
                if any(s.snapshot_version == CURRENT_SNAPSHOT_VERSION for s in event.snapshots):
                    has_current_version = True

            if case.life_events and not has_any_snapshot:
                cases_without_snapshots.append(case.research_case_id)
            elif has_any_snapshot and not has_current_version:
                stale_case_ids.append(case.research_case_id)

        return DatasetValidationReport(
            total_cases=len(case_models),
            cases_without_snapshots=cases_without_snapshots,
            life_events_without_snapshots=life_events_without_snapshots,
            stale_snapshot_case_ids=stale_case_ids,
            duplicate_case_ids=duplicate_case_ids,
        )
