"""
AstroOS — Digital Twin Service

Application-layer service that orchestrates twin operations.
Uses DigitalTwinEngine for comparison and simulation logic.
"""

from __future__ import annotations

import uuid
from typing import Optional

from apps.api.domain.digital_twin import TwinModification, TwinOperation
from apps.api.domain.horoscope import D1Chart
from apps.api.repositories.birth_chart_repository import BirthChartRepository
from apps.api.repositories.digital_twin_repository import DigitalTwinRepository
from apps.api.schemas.digital_twin import (
    DigitalTwinCreate,
    DigitalTwinListResponse,
    DigitalTwinResponse,
    TwinModificationRequest,
    TwinModificationResponse,
    TwinComparisonResponse,
)
from apps.api.services.aspect_engine import AspectEngine
from apps.api.services.digital_twin_engine import DigitalTwinEngine
from apps.api.services.graha_engine import GrahaEngine
from apps.api.services.horoscope_engine import HoroscopeEngine


class DigitalTwinService:
    def __init__(
        self,
        repository: DigitalTwinRepository,
        chart_repo: Optional[BirthChartRepository] = None,
        horoscope_engine: Optional[HoroscopeEngine] = None,
    ) -> None:
        self.repo = repository
        self.chart_repo = chart_repo
        self.horoscope_engine = horoscope_engine
        self.engine = DigitalTwinEngine(
            aspect_engine=AspectEngine(),
            graha_engine=GrahaEngine(),
        )

    async def create_twin(
        self, user_id: uuid.UUID, request: DigitalTwinCreate
    ) -> DigitalTwinResponse:
        """Create a new digital twin from an original birth chart."""
        twin_data = {
            "user_id": user_id,
            "original_chart_id": request.original_chart_id,
            "name": request.name,
            "description": request.description,
            "status": "active",
            "version": 1,
            "modifications_json": None,
        }
        twin_model = await self.repo.create_twin(twin_data)

        # Add initial modifications if provided
        for mod in request.modifications:
            mod_data = {
                "modification_type": mod.modification_type,
                "target_id": mod.target_id,
                "new_value": mod.new_value,
                "reason": mod.reason,
            }
            await self.repo.add_modification(twin_model.id, mod_data)

        # Reload with modifications
        twin_model = await self.repo.get_twin(twin_model.id)
        return self._model_to_response(twin_model)

    async def get_twin(self, twin_id: uuid.UUID) -> Optional[DigitalTwinResponse]:
        """Fetch a twin by ID, or None if not found / deleted."""
        twin = await self.repo.get_twin(twin_id)
        if not twin:
            return None
        return self._model_to_response(twin)

    async def list_twins_by_chart(
        self, user_id: uuid.UUID, chart_id: uuid.UUID
    ) -> list[DigitalTwinListResponse]:
        """List all active twins for a user, optionally filtered by chart."""
        twins = await self.repo.get_twins_by_chart(chart_id)
        twins = [t for t in twins if t.user_id == user_id]
        return [
            DigitalTwinListResponse(
                id=t.id,
                name=t.name,
                description=t.description,
                original_chart_id=t.original_chart_id,
                status=t.status,
                version=t.version,
                created_at=t.created_at,
            )
            for t in twins
        ]

    async def add_modification(
        self, twin_id: uuid.UUID, request: TwinModificationRequest
    ) -> Optional[DigitalTwinResponse]:
        """Append an immutable modification to an existing twin."""
        twin = await self.repo.get_twin(twin_id)
        if not twin:
            return None

        mod_data = {
            "modification_type": request.modification_type,
            "target_id": request.target_id,
            "new_value": request.new_value,
            "reason": request.reason,
        }
        await self.repo.add_modification(twin_id, mod_data)

        # Bump version
        await self.repo.update_twin(twin_id, version=twin.version + 1)

        # Reload and return
        twin = await self.repo.get_twin(twin_id)
        return self._model_to_response(twin) if twin else None

    async def compare_to_original(
        self, twin_id: uuid.UUID
    ) -> Optional[TwinComparisonResponse]:
        """
        Compute field-level diffs between the twin's modified state
        and the original birth chart.

        The original chart isn't reconstructed from persisted rows —
        birth_charts only stores a D1 summary (lagna, moon nakshatra),
        not the full computed chart (aspects, panchanga, etc. are never
        persisted). Swiss Ephemeris calculation is a pure function of the
        birth parameters, so recomputing from the stored
        birth_datetime_utc/lat/lon/ayanamsa/house_system via the same
        HoroscopeEngine used at creation time reproduces the exact
        original chart without needing a separate DB-row-to-domain
        reconstruction path.
        """
        twin = await self.repo.get_twin(twin_id)
        if not twin:
            return None

        loaded = await self._load_original_chart(twin)
        if not loaded:
            return None
        original_chart, modifications = loaded

        twin_chart = self.engine.apply_modifications(original_chart, modifications)
        comparison = self.engine.compare_charts(original_chart, twin_chart, modifications)

        return TwinComparisonResponse(
            twin_id=twin.id,
            original_chart_id=twin.original_chart_id,
            total_modifications=comparison.total_modifications,
            field_diffs=[
                {
                    "field_path": d.field_path,
                    "label": d.label,
                    "old_value": d.old_value,
                    "new_value": d.new_value,
                    "delta": d.delta,
                    "significance": d.significance,
                }
                for d in comparison.field_diffs
            ],
            metrics_before=comparison.metrics_before,
            metrics_after=comparison.metrics_after,
            summary=comparison.summary,
        )

    async def simulate_operations(
        self,
        twin_id: uuid.UUID,
        operations: list[dict],
    ) -> Optional[list[dict]]:
        """
        Run a sequence of simulation operations against the twin.

        Each operation dict: {"operation_type": "...", "params": {...}}.
        Operations are applied in order against the twin's *current*
        state (original chart + existing modifications already applied).
        Each successful operation is persisted as a new modification —
        translated into whichever existing modification_type
        (planet_position / retrograde) reproduces the same change via
        apply_modifications — so a twin's history stays replayable and
        simulated changes aren't lost between requests.

        Returns None if the twin doesn't exist. Per-operation failures
        (bad params, unknown planet, unsupported operation_type) don't
        raise — they come back as a result with success=False and an
        error message, and don't get persisted.
        """
        twin = await self.repo.get_twin(twin_id)
        if not twin:
            return None

        loaded = await self._load_original_chart(twin)
        if not loaded:
            return None
        original_chart, modifications = loaded

        current_chart = self.engine.apply_modifications(original_chart, modifications)

        results = []
        applied_any = False
        for op_dict in operations:
            operation = TwinOperation(
                operation_type=op_dict.get("operation_type", ""),
                params=op_dict.get("params", {}),
                duration_steps=op_dict.get("duration_steps", 1),
            )
            current_chart, result = self.engine.apply_operation(current_chart, operation)
            results.append({
                "operation_type": result.operation_type,
                "success": result.success,
                "changes": [
                    {
                        "field_path": c.field_path,
                        "label": c.label,
                        "old_value": c.old_value,
                        "new_value": c.new_value,
                        "delta": c.delta,
                        "significance": c.significance,
                    }
                    for c in result.changes
                ],
                "error": result.error,
            })

            if result.success:
                applied_any = True
                await self._persist_operation_as_modification(twin_id, operation, result)

        if applied_any:
            await self.repo.update_twin(twin_id, version=twin.version + len(
                [r for r in results if r["success"]]
            ))

        return results

    async def _persist_operation_as_modification(
        self, twin_id: uuid.UUID, operation: TwinOperation, result
    ) -> None:
        """
        Record a successful operation as a plain modification, using
        whichever field it actually changed — keeps operations and
        modifications in one consistent, replayable history instead of
        two disconnected mechanisms.
        """
        if operation.operation_type == "retrograde_planet":
            await self.repo.add_modification(twin_id, {
                "modification_type": "retrograde",
                "target_id": operation.params.get("planet", ""),
                "new_value": None,
                "reason": f"Simulation operation: {operation.operation_type}",
            })
            return

        lon_change = next(
            (c for c in result.changes if c.field_path.endswith(".sidereal_longitude")),
            None,
        )
        if lon_change is None:
            return  # e.g. conjunct_planets where the planet was already there

        planet_name = lon_change.field_path.split(".")[1]
        await self.repo.add_modification(twin_id, {
            "modification_type": "planet_position",
            "target_id": planet_name,
            "new_value": lon_change.new_value,
            "reason": f"Simulation operation: {operation.operation_type}",
        })

    async def _load_original_chart(
        self, twin
    ) -> Optional[tuple[D1Chart, tuple[TwinModification, ...]]]:
        """
        Recompute the original D1 chart from its stored birth parameters
        and convert the twin's persisted modifications into domain
        objects. Shared by compare_to_original and simulate_operations.

        The original chart isn't reconstructed from persisted rows —
        birth_charts only stores a D1 summary (lagna, moon nakshatra),
        not the full computed chart (aspects, panchanga, etc. are never
        persisted). Swiss Ephemeris calculation is a pure function of the
        birth parameters, so recomputing from the stored
        birth_datetime_utc/lat/lon/ayanamsa/house_system via the same
        HoroscopeEngine used at creation time reproduces the exact
        original chart without needing a separate DB-row-to-domain
        reconstruction path.
        """
        if not (self.chart_repo and self.horoscope_engine):
            raise RuntimeError(
                "DigitalTwinService requires chart_repo and "
                "horoscope_engine to be provided at construction time "
                "to load original charts."
            )

        chart_row = await self.chart_repo.get_by_id(twin.original_chart_id)
        if not chart_row:
            return None

        original_chart = self.horoscope_engine.generate_d1(
            birth_datetime_utc=chart_row.birth_datetime_utc,
            latitude=float(chart_row.birth_latitude),
            longitude=float(chart_row.birth_longitude),
            ayanamsa=chart_row.ayanamsa,
            house_system=chart_row.house_system,
        )

        modifications = tuple(
            TwinModification(
                id=m.id,
                modification_type=m.modification_type,
                target_id=m.target_id,
                old_value=m.old_value,
                new_value=m.new_value,
                reason=m.reason,
                created_at=m.created_at,
            )
            for m in (twin.modifications or [])
        )

        return original_chart, modifications

    async def delete_twin(self, twin_id: uuid.UUID) -> bool:
        """Soft-delete a digital twin."""
        return await self.repo.delete_twin(twin_id)

    # ── Internal helpers ────────────────────────────────────────────────────────

    def _model_to_response(self, twin_model) -> DigitalTwinResponse:
        """Convert ORM model → Pydantic response schema."""
        modifications = [
            TwinModificationResponse(
                id=m.id,
                modification_type=m.modification_type,
                target_id=m.target_id,
                old_value=m.old_value,
                new_value=m.new_value,
                reason=m.reason,
                created_at=m.created_at,
            )
            for m in (twin_model.modifications or [])
        ]

        return DigitalTwinResponse(
            id=twin_model.id,
            original_chart_id=twin_model.original_chart_id,
            name=twin_model.name,
            description=twin_model.description,
            status=twin_model.status,
            version=twin_model.version,
            modifications=modifications,
            created_at=twin_model.created_at,
            updated_at=twin_model.updated_at,
        )