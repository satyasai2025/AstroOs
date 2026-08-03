"""
AstroOS — Pattern Persistence Service (Module 27, Phase 3c)

Bridges the pure in-memory PatternDiscoveryService (apps.api.services.
pattern_discovery.py — no DB access by design) with the discovered_patterns /
pattern_discovery_runs tables. Every discovery run is persisted here,
stamped with the algorithm/feature engine versions and the exact
supporting/contradicting research_case_id sets and snapshot versions that
produced each pattern — the reproducibility trail the user asked for.

Reads for the dashboard (GET /cases/patterns*) never call
PatternDiscoveryService directly — they read these tables. Only
POST /cases/patterns/discover and Advanced Research > Evidence
Recalculation write to them.
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.research_case import DiscoveredPattern, ExtractedFeature, PatternDimension
from apps.api.models.pattern import DiscoveredPatternModel, PatternDiscoveryRunModel
from apps.api.models.research_case import EventSnapshotModel, LifeEventModel, ResearchCaseModel
from apps.api.services import feature_extraction, pattern_discovery
from apps.api.services.classical_references import get_references_for_pattern
from apps.api.services.feature_extraction import FeatureExtractionService
from apps.api.services.pattern_discovery import PatternDiscoveryService


def dimensions_to_json(dimensions: list[PatternDimension]) -> list[dict]:
    return [
        {
            "dimension": d.dimension,
            "value": d.value,
            "frequency": d.frequency,
            "count": d.count,
            "expected_by_chance": d.expected_by_chance,
            "significance": d.significance,
        }
        for d in dimensions
    ]


def dimensions_from_json(raw: list[dict]) -> list[PatternDimension]:
    return [
        PatternDimension(
            dimension=d["dimension"],
            value=d["value"],
            frequency=d["frequency"],
            count=d["count"],
            expected_by_chance=d.get("expected_by_chance", 0.0),
            significance=d.get("significance", 0.0),
        )
        for d in raw
    ]


class PatternPersistenceService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._engine = PatternDiscoveryService()

    async def _snapshot_versions_for(self, case_ids: list[str], event_type: str) -> list[str]:
        if not case_ids:
            return []
        rows = await self._session.execute(
            select(EventSnapshotModel.snapshot_version)
            .join(LifeEventModel, EventSnapshotModel.life_event_id == LifeEventModel.id)
            .join(ResearchCaseModel, LifeEventModel.research_case_id == ResearchCaseModel.id)
            .where(
                ResearchCaseModel.research_case_id.in_(case_ids),
                LifeEventModel.event_type == event_type,
            )
            .distinct()
        )
        return sorted({row[0] for row in rows.all()})

    async def persist_discovery(
        self,
        patterns: list[DiscoveredPattern],
        *,
        all_features: list[ExtractedFeature],
        event_type: str | None,
        total_cases: int,
        total_events: int,
        execution_time_ms: int,
    ) -> PatternDiscoveryRunModel:
        """Upsert every discovered pattern (keyed by pattern_id) and record
        a new PatternDiscoveryRunModel row for this invocation.

        A discovery run is authoritative for its scope (one event_type, or
        every event_type present in ``all_features`` when ``event_type`` is
        None): existing persisted patterns for those event type(s) are
        deleted first, then this run's patterns are inserted fresh. Without
        this, a pattern that stops qualifying after an algorithm/threshold
        change (e.g. a stricter significance test) would never be removed —
        upsert-by-pattern_id only ever adds or updates, so its old,
        now-invalid row would linger forever alongside newer runs.
        """
        scoped_event_types = (
            {event_type} if event_type is not None else {f.event_type for f in all_features}
        )
        if scoped_event_types:
            await self._session.execute(
                delete(DiscoveredPatternModel).where(
                    DiscoveredPatternModel.event_type.in_(scoped_event_types)
                )
            )

        run = PatternDiscoveryRunModel(
            event_type=event_type,
            total_cases=total_cases,
            total_events=total_events,
            execution_time_ms=execution_time_ms,
            algorithm_version=pattern_discovery.ALGORITHM_VERSION,
            feature_version=feature_extraction.FEATURE_VERSION,
        )
        self._session.add(run)
        await self._session.flush()  # populate run.id

        for pattern in patterns:
            case_ids = sorted(pattern.supporting_case_ids)
            contradicting = sorted(
                self._engine.find_contradicting_cases(
                    all_features, event_type=pattern.event_type, dimensions=pattern.dimensions
                )
            )
            snapshot_versions = await self._snapshot_versions_for(case_ids, pattern.event_type)
            references = get_references_for_pattern(pattern)

            # Every existing pattern for this event type was just deleted
            # above, so this is always a fresh insert, never an update.
            self._session.add(
                DiscoveredPatternModel(
                    pattern_id=pattern.pattern_id,
                    event_type=pattern.event_type,
                    description=pattern.description,
                    sample_size=pattern.sample_size,
                    confidence_score=pattern.confidence_score,
                    lift_score=pattern.lift_score,
                    dimensions_json=dimensions_to_json(pattern.dimensions),
                    classical_references_json=references,
                    supporting_case_ids_json=case_ids,
                    contradicting_case_ids_json=contradicting,
                    snapshot_versions_json=snapshot_versions,
                    algorithm_version=pattern_discovery.ALGORITHM_VERSION,
                    feature_version=feature_extraction.FEATURE_VERSION,
                    discovery_run_id=run.id,
                )
            )

        return run

    async def recalculate_evidence(self) -> int:
        """Advanced Research tool: re-derive supporting/contradicting case
        IDs, lift, and snapshot versions for every existing persisted
        pattern against CURRENT snapshot data — without running discovery
        again, so no new patterns appear or disappear. Run this right after
        a Snapshot Rebuild. Returns the number of patterns refreshed.
        """
        all_patterns = (
            await self._session.execute(select(DiscoveredPatternModel))
        ).scalars().all()
        if not all_patterns:
            return 0

        all_features = await FeatureExtractionService(self._session).extract_all()
        by_case: dict[str, list[ExtractedFeature]] = {}
        for f in all_features:
            by_case.setdefault(f.research_case_id, []).append(f)

        refreshed = 0
        for row in all_patterns:
            conditions = {(d["dimension"], d["value"]) for d in row.dimensions_json}
            supporting = sorted(
                case_id
                for case_id, feats in by_case.items()
                if any(f.event_type == row.event_type for f in feats)
                and conditions.issubset({(f.feature_name, str(f.feature_value)) for f in feats})
            )
            dimensions = dimensions_from_json(row.dimensions_json)
            contradicting = sorted(
                self._engine.find_contradicting_cases(
                    all_features, event_type=row.event_type, dimensions=dimensions
                )
            )

            row.supporting_case_ids_json = supporting
            row.contradicting_case_ids_json = contradicting
            row.lift_score = max((d.lift_score for d in dimensions), default=0.0)
            row.snapshot_versions_json = await self._snapshot_versions_for(supporting, row.event_type)
            refreshed += 1
        return refreshed
