"""
AstroOS — Feature Extraction Service (Module 27, Phase 3a)

The bridge between raw, immutable EventSnapshots and the pattern-discovery
engine. Every astrological observation inside a snapshot (active yogas,
dasha chain, transit features, shadbala strengths, house-lord statuses,
varga/nakshatra activations) is normalised into a flat, searchable
``ExtractedFeature`` record keyed to (event_type, research_case_id).

Why a dedicated extraction layer (per the plan):
  * Snapshots are stored as JSON blobs (transit_features, shadbala_values,
    active_yogas, ...). Pattern discovery must not know about that storage
    format — it should aggregate over normalised feature rows.
  * A single "Ju in 7th aspect" observation can be counted many ways;
    extraction decides once how each observation is named and categorised,
    so downstream statistics are reproducible.
  * Extraction is stateless and idempotent: run it after any batch import
    to refresh the feature dataset for pattern discovery.

Feature categories (feature_category): yoga, dasha, transit, shadbala,
house, nakshatra, varga. Confidence is carried through from the snapshot;
a JSON parse failure degrades to a lower confidence rather than dropping
the observation (same best-effort-with-explicit-gap discipline as
apps/api/services/import_service.py).
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from datetime import date
from typing import Any, Iterable

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from apps.api.domain.research_case import ExtractedFeature
from apps.api.models.research_case import (
    EventSnapshotModel,
    LifeEventModel,
    ResearchCaseModel,
)

logger = logging.getLogger(__name__)

# Bumped by hand whenever the normalisation logic below changes materially.
# Stamped onto every persisted DiscoveredPattern row alongside
# pattern_discovery.ALGORITHM_VERSION for full reproducibility.
FEATURE_VERSION = "1.1.0"

# Categories whose observations are parsed from a JSON list/dict column.
_LIST_FIELDS = ("active_yogas", "nakshatra_activations")
_DICT_FIELDS = (
    "transit_features",
    "shadbala_values",
    "varga_activations",
    "house_lord_statuses",
)


def _as_list(raw: str | None) -> list[Any]:
    """Parse a JSON list column; tolerate null/empty/`[]`."""
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except (ValueError, TypeError):
        logger.warning("Unparsable JSON list: %r", raw)
        return []
    return value if isinstance(value, list) else []


def _as_plain_event_type(value: Any) -> str:
    """Coerce a SQLAlchemy Core row's Enum-typed column to a plain string.

    ``LifeEventModel.event_type`` is a ``SAEnum(_EventType, ...)`` column;
    even in a Core (non-ORM-entity) ``select()``, SQLAlchemy's result
    processor deserializes it back into the Python ``_EventType`` enum
    member, not a plain str — despite ``_EventType`` mixing in ``str``. On
    this Python version, f-string-interpolating that member (as
    pattern_discovery.py's description text does) renders as the ugly
    "_EventType.DEATH_PARENT" rather than "death_parent", since Enum's
    __format__ takes priority over str's in the MRO. Normalise once, here,
    at the single place every feature's event_type value originates.
    """
    return value.value if hasattr(value, "value") else str(value)


def _latest_snapshot_entity():
    """Build a mapped entity + row-number column selecting only the newest
    ``EventSnapshotModel`` row per ``life_event_id``.

    ``EventSnapshotModel`` is versioned and append-only (see its docstring
    and ``ResearchCaseImportService.rebuild_all_snapshots``) — a life event
    can have snapshot rows from more than one ``snapshot_version``. Without
    this, extraction would double-count features from every event that has
    been re-snapshotted, inflating frequencies for whichever categories
    both versions happen to share.
    """
    ranked = select(
        EventSnapshotModel,
        func.row_number()
        .over(
            partition_by=EventSnapshotModel.life_event_id,
            order_by=EventSnapshotModel.created_at.desc(),
        )
        .label("rn"),
    ).subquery()
    return aliased(EventSnapshotModel, ranked), ranked.c.rn


def _as_dict(raw: str | None) -> dict[str, Any]:
    """Parse a JSON dict column; tolerate null/empty/`{}`."""
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except (ValueError, TypeError):
        logger.warning("Unparsable JSON dict: %r", raw)
        return {}
    return value if isinstance(value, dict) else {}


class FeatureExtractionService:
    """
    Reads EventSnapshots joined with their LifeEvent + ResearchCase and
    emits normalised ExtractedFeature rows.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def extract_all(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[ExtractedFeature]:
        """
        Extract features across every non-deleted research case.

        ``date_from``/``date_to`` optionally bound ``LifeEventModel.event_date``
        (inclusive) — used by the dashboard's Date Range filter.

        Returns a flat list of ExtractedFeature; ordering is not guaranteed
        and callers should not rely on it.
        """
        LatestSnapshot, rn = _latest_snapshot_entity()
        query = (
            select(
                ResearchCaseModel.research_case_id,
                LifeEventModel.event_type,
                LifeEventModel.event_date,
                LatestSnapshot,
            )
            .join(LifeEventModel, LatestSnapshot.life_event_id == LifeEventModel.id)
            .join(ResearchCaseModel, LifeEventModel.research_case_id == ResearchCaseModel.id)
            .where(ResearchCaseModel.deleted_at.is_(None))
            .where(rn == 1)
        )
        if date_from is not None:
            query = query.where(LifeEventModel.event_date >= date_from)
        if date_to is not None:
            query = query.where(LifeEventModel.event_date <= date_to)
        rows = (await self._session.execute(query)).all()

        features: list[ExtractedFeature] = []
        for research_case_id, event_type, event_date, snapshot in rows:
            features.extend(
                self._from_snapshot(
                    research_case_id, _as_plain_event_type(event_type), event_date, snapshot
                )
            )
        return features

    async def extract_by_event_type(self, event_type: str) -> list[ExtractedFeature]:
        """Extract features only for one KP Master event type."""
        LatestSnapshot, rn = _latest_snapshot_entity()
        rows = (
            await self._session.execute(
                select(
                    ResearchCaseModel.research_case_id,
                    LifeEventModel.event_type,
                    LifeEventModel.event_date,
                    LatestSnapshot,
                )
                .join(LifeEventModel, LatestSnapshot.life_event_id == LifeEventModel.id)
                .join(ResearchCaseModel, LifeEventModel.research_case_id == ResearchCaseModel.id)
                .where(LifeEventModel.event_type == event_type)
                .where(ResearchCaseModel.deleted_at.is_(None))
                .where(rn == 1)
            )
        ).all()

        features: list[ExtractedFeature] = []
        for research_case_id, event_type, event_date, snapshot in rows:
            features.extend(
                self._from_snapshot(
                    research_case_id, _as_plain_event_type(event_type), event_date, snapshot
                )
            )
        return features

    def _from_snapshot(
        self,
        research_case_id: str,
        event_type: str,
        event_date: date,
        snapshot: EventSnapshotModel,
    ) -> list[ExtractedFeature]:
        """Normalise one snapshot into feature rows."""
        features: list[ExtractedFeature] = []

        # ── Dasha chain (structured columns, not JSON) ─────────────────────
        dasha_parts = (
            ("mahadasha", snapshot.mahadasha),
            ("antardasha", snapshot.antardasha),
            ("pratyantar", snapshot.pratyantar),
        )
        for dimension, lord in dasha_parts:
            if lord:
                features.append(
                    ExtractedFeature(
                        feature_name=f"dasha_{dimension}",
                        feature_value=lord,
                        feature_category="dasha",
                        event_type=event_type,
                        research_case_id=research_case_id,
                        event_date=event_date,
                    )
                )

        # ── List-typed columns (yogas, nakshatras) ─────────────────────────
        list_sources: list[tuple[str, str, Iterable[Any]]] = []
        for col in _LIST_FIELDS:
            list_sources.append((col, col.replace("_", " ").rstrip("s"), _as_list(getattr(snapshot, col))))
        # varga_activations is a dict but each entry is an activation record
        varga = _as_dict(snapshot.varga_activations)
        list_sources.append(("varga_activations", "varga", varga.items()))

        for col, label, items in list_sources:
            for item in items:
                if isinstance(item, tuple):  # (chart_graha, strength) from varga dict
                    key, strength = item
                    features.append(
                        ExtractedFeature(
                            feature_name=f"{label}_{key}",
                            feature_value=str(strength),
                            feature_category="varga",
                            event_type=event_type,
                            research_case_id=research_case_id,
                            event_date=event_date,
                        )
                    )
                elif isinstance(item, str):
                    features.append(
                        ExtractedFeature(
                            feature_name=f"{label}_{item}",
                            feature_value=True,
                            feature_category="varga" if label == "varga" else "yoga" if col == "active_yogas" else "nakshatra",
                            event_type=event_type,
                            research_case_id=research_case_id,
                            event_date=event_date,
                        )
                    )

        # ── Dict-typed columns (transits, shadbala, house lords) ───────────
        dict_sources: list[tuple[str, str, dict[str, Any]]] = [
            ("transit_features", "transit", _as_dict(snapshot.transit_features)),
            ("shadbala_values", "shadbala", _as_dict(snapshot.shadbala_values)),
            ("house_lord_statuses", "house", _as_dict(snapshot.house_lord_statuses)),
        ]
        for col, label, mapping in dict_sources:
            for key, value in mapping.items():
                features.append(
                    ExtractedFeature(
                        feature_name=f"{label}_{key}",
                        feature_value=value,
                        feature_category=label,
                        event_type=event_type,
                        research_case_id=research_case_id,
                        event_date=event_date,
                    )
                )

        return features


def summarize(features: list[ExtractedFeature]) -> dict[str, int]:
    """Count features per category (used for response payloads)."""
    counter: Counter[str] = Counter(f.feature_category for f in features)
    return dict(counter)
