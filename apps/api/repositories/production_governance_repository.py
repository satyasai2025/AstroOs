"""
AstroOS — Production Governance Repository

Handles durable persistence and retrieval of production profile versions,
active baselines, and human reviewer sign-offs with PostgreSQL & in-memory support.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.production_governance import (
    ExperimentSignoff,
    ProductionProfileVersion,
    SignoffStatus,
)
from apps.api.models.production_governance import (
    ExperimentSignoffModel,
    ProductionProfileVersionModel,
)


class ProductionGovernanceRepository:
    """Repository for production profile lifecycle management and experiment sign-offs."""

    _in_memory_profiles: dict[str, list[ProductionProfileVersion]] = {}
    _in_memory_signoffs: dict[str, list[ExperimentSignoff]] = {}

    def __init__(self, session: Optional[AsyncSession] = None) -> None:
        self._session = session

    @classmethod
    def clear_in_memory(cls) -> None:
        cls._in_memory_profiles.clear()
        cls._in_memory_signoffs.clear()

    async def get_active_baseline_profile(self, benchmark_id: str) -> ProductionProfileVersion:
        """Retrieves the active baseline profile for a benchmark, seeding default if absent."""
        if self._session is not None:
            stmt = select(ProductionProfileVersionModel).where(
                ProductionProfileVersionModel.benchmark_id == benchmark_id,
                ProductionProfileVersionModel.is_active_baseline.is_(True),
            )
            res = await self._session.execute(stmt)
            model = res.scalar_one_or_none()
            if model:
                return ProductionProfileVersion(
                    profile_id=model.profile_id,
                    version=model.version,
                    benchmark_id=model.benchmark_id,
                    is_active_baseline=model.is_active_baseline,
                    promoted_from_experiment_id=model.promoted_from_experiment_id,
                    approved_by=model.approved_by,
                    promoted_at=model.promoted_at,
                    notes=model.notes,
                    config_json=model.config_json,
                )

        # Fallback to in-memory store
        profiles = self._in_memory_profiles.get(benchmark_id, [])
        active = next((p for p in profiles if p.is_active_baseline), None)
        if active:
            return active

        # Default fallback baseline
        default_base = ProductionProfileVersion(
            profile_id="parashari_standard_v1",
            version="1.0.0",
            benchmark_id=benchmark_id,
            is_active_baseline=True,
            promoted_from_experiment_id="CANONICAL-INIT",
            approved_by="SYSTEM_GENESIS",
            promoted_at=datetime.now(timezone.utc),
            notes="Default Parashari Standard consensus profile initialized at genesis.",
        )
        if benchmark_id not in self._in_memory_profiles:
            self._in_memory_profiles[benchmark_id] = []
        self._in_memory_profiles[benchmark_id].append(default_base)
        return default_base

    async def promote_profile_to_production(
        self,
        profile_id: str,
        version: str,
        benchmark_id: str,
        experiment_id: str,
        reviewer_id: str,
        notes: str = "",
    ) -> ProductionProfileVersion:
        """Promotes a profile to production and marks it as the active baseline for the benchmark."""
        now = datetime.now(timezone.utc)
        promoted = ProductionProfileVersion(
            profile_id=profile_id,
            version=version,
            benchmark_id=benchmark_id,
            is_active_baseline=True,
            promoted_from_experiment_id=experiment_id,
            approved_by=reviewer_id,
            promoted_at=now,
            notes=notes,
        )

        if self._session is not None:
            # Deactivate existing baselines for this benchmark
            stmt_deactivate = (
                update(ProductionProfileVersionModel)
                .where(ProductionProfileVersionModel.benchmark_id == benchmark_id)
                .values(is_active_baseline=False)
            )
            await self._session.execute(stmt_deactivate)

            model = ProductionProfileVersionModel(
                id=uuid.uuid4(),
                profile_id=profile_id,
                version=version,
                benchmark_id=benchmark_id,
                is_active_baseline=True,
                promoted_from_experiment_id=experiment_id,
                approved_by=reviewer_id,
                promoted_at=now,
                notes=notes,
            )
            self._session.add(model)
            await self._session.flush()

        # In-memory update
        if benchmark_id not in self._in_memory_profiles:
            self._in_memory_profiles[benchmark_id] = []

        # Deactivate existing
        self._in_memory_profiles[benchmark_id] = [
            ProductionProfileVersion(
                profile_id=p.profile_id,
                version=p.version,
                benchmark_id=p.benchmark_id,
                is_active_baseline=False,
                promoted_from_experiment_id=p.promoted_from_experiment_id,
                approved_by=p.approved_by,
                promoted_at=p.promoted_at,
                notes=p.notes,
            )
            for p in self._in_memory_profiles[benchmark_id]
        ]
        self._in_memory_profiles[benchmark_id].append(promoted)
        return promoted

    async def record_signoff(
        self,
        experiment_id: str,
        status: SignoffStatus,
        reviewer_id: str,
        notes: str = "",
    ) -> ExperimentSignoff:
        """Records a human reviewer sign-off on an experiment."""
        signoff_id = f"SIGNOFF-{experiment_id}-{uuid.uuid4().hex[:6]}"
        now = datetime.now(timezone.utc)
        signoff = ExperimentSignoff(
            signoff_id=signoff_id,
            experiment_id=experiment_id,
            status=status,
            reviewer_id=reviewer_id,
            notes=notes,
            signed_at=now,
        )

        if self._session is not None:
            model = ExperimentSignoffModel(
                id=uuid.uuid4(),
                signoff_id=signoff_id,
                experiment_id=experiment_id,
                status=status.value,
                reviewer_id=reviewer_id,
                notes=notes,
                signed_at=now,
            )
            self._session.add(model)
            await self._session.flush()

        if experiment_id not in self._in_memory_signoffs:
            self._in_memory_signoffs[experiment_id] = []
        self._in_memory_signoffs[experiment_id].append(signoff)
        return signoff

    async def get_signoff(self, experiment_id: str) -> Optional[ExperimentSignoff]:
        """Retrieves the latest sign-off for an experiment."""
        if self._session is not None:
            stmt = (
                select(ExperimentSignoffModel)
                .where(ExperimentSignoffModel.experiment_id == experiment_id)
                .order_by(ExperimentSignoffModel.signed_at.desc())
            )
            res = await self._session.execute(stmt)
            model = res.scalar_one_or_none()
            if model:
                return ExperimentSignoff(
                    signoff_id=model.signoff_id,
                    experiment_id=model.experiment_id,
                    status=SignoffStatus(model.status),
                    reviewer_id=model.reviewer_id,
                    notes=model.notes,
                    signed_at=model.signed_at,
                )

        signoffs = self._in_memory_signoffs.get(experiment_id, [])
        return signoffs[-1] if signoffs else None

    async def list_production_profiles(self, benchmark_id: str) -> list[ProductionProfileVersion]:
        """Lists all versioned production profiles for a benchmark."""
        # Ensure default is seeded
        _ = await self.get_active_baseline_profile(benchmark_id)

        if self._session is not None:
            stmt = (
                select(ProductionProfileVersionModel)
                .where(ProductionProfileVersionModel.benchmark_id == benchmark_id)
                .order_by(ProductionProfileVersionModel.promoted_at.desc())
            )
            res = await self._session.execute(stmt)
            models = res.scalars().all()
            if models:
                return [
                    ProductionProfileVersion(
                        profile_id=m.profile_id,
                        version=m.version,
                        benchmark_id=m.benchmark_id,
                        is_active_baseline=m.is_active_baseline,
                        promoted_from_experiment_id=m.promoted_from_experiment_id,
                        approved_by=m.approved_by,
                        promoted_at=m.promoted_at,
                        notes=m.notes,
                        config_json=m.config_json,
                    )
                    for m in models
                ]

        return self._in_memory_profiles.get(benchmark_id, [])