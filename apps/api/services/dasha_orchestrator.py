"""
AstroOS — Dasha Orchestrator

Thin coordination layer between the router and DashaEngine. Looks up the
requested system in the dasha registry, dispatches to the corresponding
DashaEngine.compute_* method (off the event loop), and persists the result.

Does not perform any dasha math itself and does not change DashaEngine,
DashaRepository, or the dashas table — those remain the source of truth
for calculation and storage.
"""

from __future__ import annotations

import asyncio
import functools
import uuid
from datetime import datetime
from typing import Optional

from apps.api.domain.dasha import DashaTree
from apps.api.schemas.dasha import AyanamsaCode, HouseSystemCode
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.dasha_registry import get_dasha_engine


class DashaOrchestrator:
    """Routes a dasha computation request to the correct engine method."""

    def __init__(self, engine: DashaEngine) -> None:
        self._engine = engine

    async def run(
        self,
        system: str,
        *,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: AyanamsaCode = "lahiri",
        house_system: HouseSystemCode = "W",
        max_depth: int = 3,
        persist: bool = True,
        user_id: Optional[uuid.UUID] = None,
        subject_name: str = "Unnamed",
    ) -> DashaTree:
        """
        Compute (and optionally persist) a dasha tree for `system`.

        Raises KeyError if `system` is not registered.
        """
        descriptor = get_dasha_engine(system)
        compute_fn = getattr(self._engine, descriptor.compute_method)

        # Blocking pyswisseph call — offload to a worker thread so it does
        # not freeze the event loop.
        tree = await asyncio.to_thread(
            functools.partial(
                compute_fn,
                birth_datetime_utc=birth_datetime_utc,
                latitude=latitude,
                longitude=longitude,
                ayanamsa=ayanamsa,
                house_system=house_system,
                max_depth=max_depth,
            )
        )

        if persist:
            await self.persist(
                tree,
                birth_datetime_utc=birth_datetime_utc,
                latitude=latitude,
                longitude=longitude,
                ayanamsa=ayanamsa,
                house_system=house_system,
                user_id=user_id,
                subject_name=subject_name,
            )

        return tree

    async def persist(
        self,
        tree: DashaTree,
        *,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: AyanamsaCode = "lahiri",
        house_system: HouseSystemCode = "W",
        user_id: Optional[uuid.UUID] = None,
        subject_name: str = "Unnamed",
    ) -> uuid.UUID:
        """Persist an already-computed tree. Thin pass-through to DashaEngine."""
        return await self._engine.persist_tree(
            tree,
            birth_datetime_utc=birth_datetime_utc,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            house_system=house_system,
            user_id=user_id,
            subject_name=subject_name,
        )
