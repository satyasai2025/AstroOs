"""
AstroOS — Research & Backtesting Engine (Unified v4)

Combines:
  1. Empirical backtesting & calibration against ground-truth historical datasets
     (strict Train vs Holdout partitioning, deterministic prediction synthesis, window evaluation).
  2. Research project, experiment, execution, and astrological snapshot lifecycle management.
"""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Optional, Sequence
import uuid

from apps.api.domain.prediction_orchestration import (
    PARASHARI_STANDARD_PROFILE,
    ConsensusProfile,
    PredictionSynthesisResult,
)
from apps.api.domain.research import (
    AstrologicalSnapshot,
    ExperimentExecution,
    ResearchExperiment,
    ResearchProject,
    SnapshotComparison,
    SnapshotQuery,
)
from apps.api.domain.research_calibration import (
    BacktestOutcome,
    BenchmarkDataset,
    CalibrationDatasetSplit,
    GroundTruthEvent,
    TemporalMatchStatus,
)
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.prediction_orchestrator import PredictionOrchestrator
from apps.api.services.snapshot_accessor import SnapshotAccessor

if TYPE_CHECKING:
    from apps.api.repositories.research_repository import ResearchRepository


class ResearchEngine:
    """Independent empirical research, backtesting, and project management engine."""

    _SNAPSHOT_VERSION = "1.0"

    def __init__(
        self,
        research_repo_or_wrapper: Optional[Any] = None,
        horoscope_engine: Optional[HoroscopeEngine] = None,
        dasha_engine: Optional[DashaEngine] = None,
        prediction_orchestrator: Optional[PredictionOrchestrator] = None,
        research_repo: Optional[ResearchRepository] = None,
    ) -> None:
        from apps.api.repositories.research_repository import ResearchRepository as _RR
        if isinstance(research_repo_or_wrapper, _RR) or hasattr(research_repo_or_wrapper, "get_project"):
            self._repo = research_repo_or_wrapper
            ephemeris_wrapper = None
        else:
            self._repo = research_repo
            ephemeris_wrapper = research_repo_or_wrapper

        from apps.api.config import get_settings
        settings = get_settings()
        self._wrapper = ephemeris_wrapper or EphemerisWrapper(settings.EPHEMERIS_PATH)
        self._horoscope_engine = horoscope_engine or HoroscopeEngine(self._wrapper)
        self._dasha_engine = dasha_engine or DashaEngine(self._wrapper)
        self._orchestrator = prediction_orchestrator or PredictionOrchestrator()

    # ── Project management ────────────────────────────────────────────────

    async def create_project(
        self,
        user_id: uuid.UUID,
        title: str,
        description: Optional[str] = None,
    ) -> ResearchProject:
        if not self._repo:
            raise RuntimeError("Repository not attached to ResearchEngine.")
        return await self._repo.create_project(
            user_id=user_id, title=title, description=description,
        )

    async def update_project(
        self, project_id: uuid.UUID, **fields: Any
    ) -> Optional[ResearchProject]:
        if not self._repo:
            raise RuntimeError("Repository not attached to ResearchEngine.")
        return await self._repo.update_project(project_id, **fields)

    async def get_project(
        self, project_id: uuid.UUID
    ) -> Optional[ResearchProject]:
        if not self._repo:
            raise RuntimeError("Repository not attached to ResearchEngine.")
        return await self._repo.get_project(project_id)

    async def list_projects(
        self, user_id: uuid.UUID, status: Optional[str] = None,
    ) -> tuple[ResearchProject, ...]:
        if not self._repo:
            raise RuntimeError("Repository not attached to ResearchEngine.")
        return await self._repo.list_projects(user_id, status=status)

    async def delete_project(self, project_id: uuid.UUID) -> bool:
        if not self._repo:
            raise RuntimeError("Repository not attached to ResearchEngine.")
        return await self._repo.delete_project(project_id)

    # ── Experiment management ─────────────────────────────────────────────

    async def create_experiment(
        self,
        project_id: uuid.UUID,
        title: str,
        hypothesis: str,
        methodology: str,
    ) -> ResearchExperiment:
        if not self._repo:
            raise RuntimeError("Repository not attached to ResearchEngine.")
        return await self._repo.create_experiment(
            project_id=project_id, title=title,
            hypothesis=hypothesis, methodology=methodology,
        )

    async def update_experiment(
        self, experiment_id: uuid.UUID, **fields: Any,
    ) -> Optional[ResearchExperiment]:
        if not self._repo:
            raise RuntimeError("Repository not attached to ResearchEngine.")
        return await self._repo.update_experiment(experiment_id, **fields)

    async def get_experiment(
        self, experiment_id: uuid.UUID,
    ) -> Optional[ResearchExperiment]:
        if not self._repo:
            raise RuntimeError("Repository not attached to ResearchEngine.")
        return await self._repo.get_experiment(experiment_id)

    async def list_experiments(
        self, project_id: uuid.UUID,
    ) -> tuple[ResearchExperiment, ...]:
        if not self._repo:
            raise RuntimeError("Repository not attached to ResearchEngine.")
        return await self._repo.list_experiments(project_id)

    async def assign_snapshots_to_experiment(
        self,
        experiment_id: uuid.UUID,
        snapshot_ids: list[uuid.UUID],
    ) -> Optional[ResearchExperiment]:
        if not self._repo:
            raise RuntimeError("Repository not attached to ResearchEngine.")
        return await self._repo.assign_snapshots_to_experiment(
            experiment_id, snapshot_ids,
        )

    async def complete_experiment(
        self, experiment_id: uuid.UUID, findings: str,
    ) -> Optional[ResearchExperiment]:
        if not self._repo:
            raise RuntimeError("Repository not attached to ResearchEngine.")
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
        if not self._repo:
            raise RuntimeError("Repository not attached to ResearchEngine.")
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
        if not self._repo:
            raise RuntimeError("Repository not attached to ResearchEngine.")
        return await self._repo.get_snapshot(snapshot_id)

    async def list_snapshots(
        self, project_id: uuid.UUID,
    ) -> tuple[AstrologicalSnapshot, ...]:
        if not self._repo:
            raise RuntimeError("Repository not attached to ResearchEngine.")
        return await self._repo.list_snapshots(project_id)

    async def delete_snapshot(self, snapshot_id: uuid.UUID) -> bool:
        if not self._repo:
            raise RuntimeError("Repository not attached to ResearchEngine.")
        return await self._repo.delete_snapshot(snapshot_id)

    # ── Query ─────────────────────────────────────────────────────────────

    async def query_snapshots(
        self,
        project_id: uuid.UUID,
        query: SnapshotQuery,
    ) -> tuple[AstrologicalSnapshot, ...]:
        if not self._repo:
            raise RuntimeError("Repository not attached to ResearchEngine.")
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
        if not self._repo:
            raise RuntimeError("Repository not attached to ResearchEngine.")
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
        if not self._repo:
            raise RuntimeError("Repository not attached to ResearchEngine.")
        snapshots = await self._repo.list_snapshots(project_id)
        snap_a = next((s for s in snapshots if s.chart_id == chart_id_a), None)
        snap_b = next((s for s in snapshots if s.chart_id == chart_id_b), None)
        if snap_a is None or snap_b is None:
            return None

        accessor_a = SnapshotAccessor(snap_a)
        accessor_b = SnapshotAccessor(snap_b)
        return accessor_a.compare(accessor_b)

    # ── Backtesting & Calibration Engine ──────────────────────────────────

    def split_dataset(
        self,
        dataset: BenchmarkDataset,
        train_ratio: float = 0.70,
        seed: int = 42,
    ) -> CalibrationDatasetSplit:
        """
        Deterministically partitions events into a training split (for fitting calibration curves)
        and an unseen holdout split (for independent out-of-sample validation).
        """
        events_list = list(dataset.events)
        rng = random.Random(seed)
        rng.shuffle(events_list)

        split_idx = int(round(len(events_list) * train_ratio))
        train_events = tuple(events_list[:split_idx])
        holdout_events = tuple(events_list[split_idx:])

        return CalibrationDatasetSplit(
            dataset_id=dataset.dataset_id,
            dataset_version=dataset.version,
            train_events=train_events,
            holdout_events=holdout_events,
            split_seed=seed,
            split_train_ratio=train_ratio,
        )

    def run_backtest(
        self,
        events: Sequence[GroundTruthEvent],
        profile: ConsensusProfile = PARASHARI_STANDARD_PROFILE,
        tolerance_days: int = 30,
        scan_window_years_before: int = 2,
        scan_window_years_after: int = 2,
    ) -> tuple[BacktestOutcome, ...]:
        """
        Executes backtesting over a collection of ground-truth events using the
        deterministic prediction orchestrator.
        """
        outcomes: list[BacktestOutcome] = []

        for event in events:
            outcome = self._evaluate_single_event(
                event=event,
                profile=profile,
                tolerance_days=tolerance_days,
                scan_window_years_before=scan_window_years_before,
                scan_window_years_after=scan_window_years_after,
            )
            outcomes.append(outcome)

        return tuple(outcomes)

    def _evaluate_single_event(
        self,
        event: GroundTruthEvent,
        profile: ConsensusProfile,
        tolerance_days: int,
        scan_window_years_before: int,
        scan_window_years_after: int,
    ) -> BacktestOutcome:
        """Evaluates temporal alignment between predicted event windows and ground truth."""
        # 1. Generate birth chart D1
        chart = self._horoscope_engine.generate_d1(
            birth_datetime_utc=event.birth_datetime_utc,
            latitude=event.birth_latitude,
            longitude=event.birth_longitude,
        )

        # 2. Generate Vimshottari dasha tree
        dasha_tree = self._dasha_engine.compute_vimshottari(
            birth_datetime_utc=event.birth_datetime_utc,
            latitude=event.birth_latitude,
            longitude=event.birth_longitude,
            max_depth=3,
        )

        # 3. Define temporal evaluation range around the true event date
        start_date = event.actual_date - timedelta(days=scan_window_years_before * 365)
        end_date = event.actual_date + timedelta(days=scan_window_years_after * 365)

        # 4. Synthesize candidate event windows via PredictionOrchestrator
        synth_result: PredictionSynthesisResult = self._orchestrator.predict_event_windows(
            chart=chart,
            dasha_tree=dasha_tree,
            objective=event.event_type,
            target_start=start_date,
            target_end=end_date,
            profile=profile,
        )

        # 5. Classify temporal match against ground truth event.actual_date
        exact_win = None
        tolerance_win = None
        tol_delta = timedelta(days=tolerance_days)

        for win in synth_result.candidate_windows:
            if win.start_date <= event.actual_date <= win.end_date:
                exact_win = win
                break
            elif (win.start_date - tol_delta) <= event.actual_date <= (win.end_date + tol_delta):
                if tolerance_win is None or win.peak_score > tolerance_win.peak_score:
                    tolerance_win = win

        if exact_win is not None:
            offset = (exact_win.peak_date - event.actual_date).days
            return BacktestOutcome(
                event_id=event.event_id,
                actual_date=event.actual_date,
                predicted_window_start=exact_win.start_date,
                predicted_window_end=exact_win.end_date,
                peak_predicted_date=exact_win.peak_date,
                deterministic_score=exact_win.peak_score,
                match_status=TemporalMatchStatus.WINDOW_EXACT_HIT,
                peak_offset_days=offset,
                tolerance_days_used=tolerance_days,
                evidence_drivers=exact_win.primary_drivers,
            )

        if tolerance_win is not None:
            offset = (tolerance_win.peak_date - event.actual_date).days
            return BacktestOutcome(
                event_id=event.event_id,
                actual_date=event.actual_date,
                predicted_window_start=tolerance_win.start_date,
                predicted_window_end=tolerance_win.end_date,
                peak_predicted_date=tolerance_win.peak_date,
                deterministic_score=tolerance_win.peak_score,
                match_status=TemporalMatchStatus.WINDOW_TOLERANCE_HIT,
                peak_offset_days=offset,
                tolerance_days_used=tolerance_days,
                evidence_drivers=tolerance_win.primary_drivers,
            )

        # Temporal Miss
        if synth_result.candidate_windows:
            best_win = synth_result.candidate_windows[0]
            offset = (best_win.peak_date - event.actual_date).days
            return BacktestOutcome(
                event_id=event.event_id,
                actual_date=event.actual_date,
                predicted_window_start=best_win.start_date,
                predicted_window_end=best_win.end_date,
                peak_predicted_date=best_win.peak_date,
                deterministic_score=best_win.peak_score,
                match_status=TemporalMatchStatus.TEMPORAL_MISS,
                peak_offset_days=offset,
                tolerance_days_used=tolerance_days,
                evidence_drivers=best_win.primary_drivers,
            )

        return BacktestOutcome(
            event_id=event.event_id,
            actual_date=event.actual_date,
            predicted_window_start=None,
            predicted_window_end=None,
            peak_predicted_date=None,
            deterministic_score=0,
            match_status=TemporalMatchStatus.TEMPORAL_MISS,
            peak_offset_days=None,
            tolerance_days_used=tolerance_days,
            evidence_drivers=(),
        )