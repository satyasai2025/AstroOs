"""
AstroOS — SnapshotAccessor (Module 17, Phase 1)

Navigates an AstrologicalSnapshot domain object by dotted-path keys and
evaluates SnapshotConditions against it. Abstracts the access path so
consumers never depend on the internal structure of the snapshot.

If the storage format changes in the future, only this accessor (or a
replacement) needs to change — query and comparison logic stays the same.
"""

from __future__ import annotations

from typing import Any, Optional

from apps.api.domain.research import (
    AstrologicalSnapshot,
    FieldDiff,
    SnapshotComparison,
    SnapshotCondition,
    SnapshotQuery,
)


class SnapshotAccessor:
    """
    Wraps an AstrologicalSnapshot and provides navigation methods.

    Dotted path navigation walks Python object attributes (getattr) and
    sequence/dict indices (__getitem__):

      "chart_ref.planets.0.house_number"
        → snapshot.chart_ref.planets[0].house_number

      "yogas.0.is_present"
        → snapshot.yogas[0].is_present

      "shadbala_components.naisargika_bala"
        → snapshot.shadbala_components["naisargika_bala"]
    """

    def __init__(self, snapshot: AstrologicalSnapshot) -> None:
        self._snapshot = snapshot

    @property
    def snapshot(self) -> AstrologicalSnapshot:
        return self._snapshot

    # ── Navigation ───────────────────────────────────────────────────────

    def get(self, field: str) -> Any:
        """
        Navigate a dotted path through the snapshot domain object.

        Returns the value at the end of the path, or None if any segment
        along the path is None or does not exist.
        """
        segments = field.split(".")
        current: Any = self._snapshot

        for segment in segments:
            if current is None:
                return None

            # List index access: "0", "1", etc.
            if isinstance(current, (list, tuple)):
                try:
                    current = current[int(segment)]
                except (IndexError, ValueError):
                    return None
            # Dict key access
            elif isinstance(current, dict):
                try:
                    current = current[segment]
                except (KeyError, ValueError):
                    return None
            # Object attribute access
            else:
                try:
                    current = getattr(current, segment)
                except AttributeError:
                    return None

        return current

    # ── Condition evaluation ──────────────────────────────────────────────

    def matches(self, condition: SnapshotCondition) -> bool:
        """Evaluate one SnapshotCondition against the wrapped snapshot."""
        actual = self.get(condition.field)

        if actual is None:
            return False

        op = condition.operator
        expected = condition.value

        try:
            if op == "==":
                return actual == expected
            elif op == "!=":
                return actual != expected
            elif op == ">":
                return actual > expected
            elif op == "<":
                return actual < expected
            elif op == ">=":
                return actual >= expected
            elif op == "<=":
                return actual <= expected
            elif op == "in":
                return actual in expected if isinstance(expected, (list, tuple, dict, set)) else False
            else:
                return False
        except TypeError:
            return False

    def search(self, query: SnapshotQuery) -> bool:
        """AND over all conditions in the query."""
        return all(self.matches(c) for c in query.conditions)

    # ── Comparison ────────────────────────────────────────────────────────

    def compare(self, other: SnapshotAccessor) -> SnapshotComparison:
        """
        Deep-compare two snapshots by enumerating all accessible fields.

        Returns a SnapshotComparison listing matching and differing fields.
        Only scalar fields (bool, int, float, str, None) are compared;
        compound fields (objects, lists, dicts) are noted as differing if
        their string representations differ.
        """
        matching: list[str] = []
        differing: list[FieldDiff] = []

        # Enumerate known top-level fields.
        fields = [
            "snapshot_version", "label", "chart_ref.ayanamsa_system",
            "chart_ref.house_system",
        ]

        # Planet fields.
        chart_self = self._snapshot.chart_ref
        chart_other = other._snapshot.chart_ref
        if chart_self is not None and chart_other is not None and chart_self.planets and chart_other.planets:
            for i, _ in enumerate(chart_self.planets):
                fields.extend([
                    f"chart_ref.planets.{i}.planet",
                    f"chart_ref.planets.{i}.rashi",
                    f"chart_ref.planets.{i}.house_number",
                    f"chart_ref.planets.{i}.is_retrograde",
                ])

        # Yoga fields.
        if self._snapshot.yogas and other._snapshot.yogas:
            for i, _ in enumerate(self._snapshot.yogas):
                fields.extend([
                    f"yogas.{i}.yoga_id",
                    f"yogas.{i}.is_present",
                    f"yogas.{i}.strength",
                ])

        # Ashtakavarga.
        fields.append("sarvashtakavarga.total_bindus")

        # Compare each field.
        for field in fields:
            val_a = self.get(field)
            val_b = other.get(field)
            if val_a == val_b:
                matching.append(field)
            else:
                differing.append(FieldDiff(field=field, value_a=val_a, value_b=val_b))

        return SnapshotComparison(
            snapshot_a_id=self._snapshot.id,
            snapshot_b_id=other._snapshot.id,
            chart_id_a=self._snapshot.chart_id,
            chart_id_b=other._snapshot.chart_id,
            matching_fields=tuple(matching),
            differing_fields=tuple(differing),
        )
