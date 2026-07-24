"""
AstroOS — Analytics-to-Knowledge-Graph Integration (Phase III Bridge)

Correlates Knowledge Graph entities with analytic dataset cohorts and
computes entity frequency distributions. Uses the pure-local
StatisticalEngine / QueryBuilder from analytics_engine.py — no external
statistical libraries, no LLM calls.

Two primary operations:
  - correlate_entity_with_dataset() — statistical association between a KG
    entity (its presence/absence) and numeric fields in a research dataset.
  - entity_frequency() — count how often each KG entity appears in a
    specified column across a dataset.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from apps.api.services.knowledge_graph_engine import KnowledgeGraphEngine
from apps.api.services.analytics_engine import StatisticalEngine


@dataclass
class EntityCorrelation:
    """
    The result of correlating a KG entity's presence with a numeric field
    in a dataset.
    """
    entity_id: str
    entity_label: str
    entity_type: str
    field_x: str                          # The entity-presence field
    field_y: str                          # The numeric outcome field
    present_count: int                    # Records where entity is present
    absent_count: int                     # Records where entity is absent
    present_mean: float                   # Mean of field_y for present group
    absent_mean: float                    # Mean of field_y for absent group
    effect_size: float                    # Cohen's d approximation
    interpretation: str                   # Descriptive interpretation


@dataclass
class EntityFrequency:
    """Frequency count for a single KG entity."""
    entity_id: str
    entity_label: str
    entity_type: str
    count: int
    proportion: float                     # count / total_records


@dataclass
class FrequencyDistribution:
    """Complete entity frequency distribution across a dataset."""
    entities: list[EntityFrequency] = field(default_factory=list)
    total_records: int = 0
    unique_entities: int = 0


class GraphAnalytics:
    """
    Correlate KG entities with analytics cohorts and compute entity
    frequency distributions over research datasets.

    All computation is pure local using StatisticalEngine from
    analytics_engine.py — zero external dependencies.
    """

    def __init__(self, engine: KnowledgeGraphEngine) -> None:
        self._engine = engine
        self._stats = StatisticalEngine()

    # ── Correlation ──────────────────────────────────────────────────────────

    def correlate_entity_with_dataset(
        self,
        entity_id: str,
        dataset: list[dict[str, Any]],
        entity_field: str = "entity_id",
        numeric_field: str = None,
    ) -> EntityCorrelation | None:
        """
        For a given KG entity, split the dataset into records where the
        entity is present vs absent (based on entity_field), then compute
        the difference in means of numeric_field between the two groups.

        Parameters
        ----------
        entity_id : str
            KG entity id (e.g. "GRAHA-SUN", "RASHI-ARIES").
        dataset : list[dict]
            List of records. Each record is a dict.
        entity_field : str
            The key in each record whose value is compared to entity_id.
            Supports both scalar (str) and list (the entity is considered
            present if the list contains entity_id) values.
        numeric_field : str, optional
            The numeric field to compare between present/absent groups.
            If None, returns a basic prevalence count without a t-test.

        Returns
        -------
        EntityCorrelation or None
            None if the entity_id is not found in the KG.
        """
        # Validate entity exists in KG
        entity = self._engine._registry.get_entity(entity_id)
        if entity is None:
            return None

        # Split dataset into present/absent groups
        present_vals: list[float] = []
        absent_vals: list[float] = []

        for record in dataset:
            raw = record.get(entity_field)
            is_present: bool = False

            if isinstance(raw, list):
                is_present = entity_id in raw or entity.name.lower() in (str(r).lower() for r in raw)
            elif isinstance(raw, str):
                is_present = (
                    raw.lower() == entity_id.lower()
                    or raw.lower() == entity.name.lower()
                )
            else:
                is_present = str(raw).lower() in (entity_id.lower(), entity.name.lower())

            val = record.get(numeric_field) if numeric_field else None
            if val is not None and isinstance(val, (int, float)):
                if is_present:
                    present_vals.append(float(val))
                else:
                    absent_vals.append(float(val))

        present_count = len(present_vals)
        absent_count = len(absent_vals)

        if numeric_field is None or present_count < 2 or absent_count < 2:
            # Not enough data for a meaningful test — return prevalence only
            return EntityCorrelation(
                entity_id=entity_id,
                entity_label=entity.name,
                entity_type=entity.entity_type,
                field_x=entity_field,
                field_y=numeric_field or "(none)",
                present_count=present_count,
                absent_count=absent_count,
                present_mean=sum(present_vals) / max(present_count, 1),
                absent_mean=sum(absent_vals) / max(absent_count, 1),
                effect_size=0.0,
                interpretation=(
                    "insufficient data for significance testing"
                    if present_count < 2 or absent_count < 2
                    else "correlation available"
                ),
            )

        # Run Welch's t-test
        # present_vals and absent_vals: both have >=2 elements here
        import math
        import statistics

        mean_p = statistics.mean(present_vals)
        mean_a = statistics.mean(absent_vals)
        var_p = statistics.variance(present_vals)
        var_a = statistics.variance(absent_vals)

        # Cohen's d (pooled)
        pooled_std = math.sqrt(
            ((present_count - 1) * var_p + (absent_count - 1) * var_a)
            / (present_count + absent_count - 2)
        ) if (present_count + absent_count > 2) else 1.0
        cohens_d = (mean_p - mean_a) / pooled_std if pooled_std > 0 else 0.0

        # Interpretation
        abs_d = abs(cohens_d)
        if abs_d < 0.2:
            interp = "negligible effect"
        elif abs_d < 0.5:
            interp = "small effect"
        elif abs_d < 0.8:
            interp = "medium effect"
        else:
            interp = "large effect"

        return EntityCorrelation(
            entity_id=entity_id,
            entity_label=entity.name,
            entity_type=entity.entity_type,
            field_x=entity_field,
            field_y=numeric_field,
            present_count=present_count,
            absent_count=absent_count,
            present_mean=mean_p,
            absent_mean=mean_a,
            effect_size=round(cohens_d, 4),
            interpretation=interp,
        )

    def correlate_multiple(
        self,
        entity_ids: list[str],
        dataset: list[dict[str, Any]],
        entity_field: str = "entity_id",
        numeric_field: str = None,
    ) -> list[EntityCorrelation]:
        """
        Run correlate_entity_with_dataset for each entity_id in the list.
        Entities not found in the KG are silently skipped.
        """
        results: list[EntityCorrelation] = []
        for eid in entity_ids:
            corr = self.correlate_entity_with_dataset(
                entity_id=eid,
                dataset=dataset,
                entity_field=entity_field,
                numeric_field=numeric_field,
            )
            if corr is not None:
                results.append(corr)
        return results

    # ── Frequency Distribution ──────────────────────────────────────────────

    def entity_frequency(
        self,
        dataset: list[dict[str, Any]],
        entity_field: str,
        top_n: int = 50,
    ) -> FrequencyDistribution:
        """
        Compute the frequency distribution of KG entities referenced in a
        dataset column.

        Parameters
        ----------
        dataset : list[dict]
            List of records.
        entity_field : str
            The key in each record whose value identifies one or more KG
            entities. Supports scalar strings and lists of strings.
        top_n : int
            Return only the top N most frequent entities (default 50).

        Returns
        -------
        FrequencyDistribution
        """
        counter: Counter[str] = Counter()

        for record in dataset:
            raw = record.get(entity_field)
            if raw is None:
                continue
            if isinstance(raw, list):
                for item in raw:
                    key = self._resolve_entity_id(str(item))
                    if key:
                        counter[key] += 1
            elif isinstance(raw, str):
                key = self._resolve_entity_id(raw)
                if key:
                    counter[key] += 1
            else:
                key = self._resolve_entity_id(str(raw))
                if key:
                    counter[key] += 1

        total = sum(counter.values())
        entities: list[EntityFrequency] = []

        for eid, count in counter.most_common(top_n):
            entity = self._engine._registry.get_entity(eid)
            label = entity.name if entity else eid
            etype = entity.entity_type if entity else "unknown"
            entities.append(EntityFrequency(
                entity_id=eid,
                entity_label=label,
                entity_type=etype,
                count=count,
                proportion=round(count / total, 4) if total > 0 else 0.0,
            ))

        return FrequencyDistribution(
            entities=entities,
            total_records=len(dataset),
            unique_entities=len(counter),
        )

    def _resolve_entity_id(self, raw: str) -> str | None:
        """
        Try to interpret a raw string as a KG entity ID.
        Checks direct ID match first, then name match via registry.
        """
        cleaned = raw.strip()

        # Direct entity_id match
        if self._engine._registry.get_entity(cleaned):
            return cleaned

        # Name match (case-insensitive)
        for entity in self._engine._registry.all_entities():
            if entity.name.lower() == cleaned.lower():
                return entity.entity_id
            if entity.entity_id.lower() == cleaned.lower():
                return entity.entity_id

        # Check if it looks like a known alias
        from apps.api.services.entity_linking import (
            PLANET_ALIASES, RASHI_ALIASES, HOUSE_ALIASES,
        )

        lookup = cleaned.lower()
        for canonical, aliases in PLANET_ALIASES.items():
            if lookup == canonical or lookup in aliases:
                eid = f"GRAHA-{canonical.upper()}"
                if self._engine._registry.get_entity(eid):
                    return eid
        for canonical, aliases in RASHI_ALIASES.items():
            if lookup == canonical or lookup in aliases:
                eid = f"RASHI-{canonical.upper()}"
                if self._engine._registry.get_entity(eid):
                    return eid
        for num_str, aliases in HOUSE_ALIASES.items():
            if lookup == num_str or lookup in aliases:
                eid = f"BHAVA-{num_str}"
                if self._engine._registry.get_entity(eid):
                    return eid

        return None
