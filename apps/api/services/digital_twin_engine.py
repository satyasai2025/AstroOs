"""
AstroOS — Digital Twin Engine

Core computation engine for Digital Twins. Applies chart modifications
and recomputes dependent metrics (aspects, strengths, yogas) using
existing AstroOS calculation engines.

No database I/O — the repository handles persistence.
"""

from __future__ import annotations

import copy
import logging
import uuid
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Optional

from apps.api.domain.digital_twin import (
    DigitalTwin,
    FieldDiff,
    TwinComparison,
    TwinModification,
    TwinOperation,
    TwinOperationResult,
)
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.horoscope import AspectInfo, PlanetStrength
from apps.api.services.aspect_engine import AspectEngine
from apps.api.services.graha_engine import GrahaEngine
from apps.api.services.yoga_engine import YogaEngine
from packages.shared.degrees import normalize_degrees

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rashi_from_longitude(lon: float) -> str:
    """Compute sidereal zodiac sign from longitude (0-360)."""
    signs = [
        "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
        "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena",
    ]
    normalized = normalize_degrees(lon)
    idx = int(normalized / 30.0)
    return signs[min(idx, 11)]


def _house_from_longitude(lon: float, house_cusps: list) -> int:
    """
    Determine which house a planet falls into given house cusp longitudes.
    Uses whole-sign logic by default (house number = sign index for ascendant-based).
    """
    if not house_cusps:
        return 1
    # For simplicity: assign based on first house cusp (ascendant)
    asc_lon = house_cusps[0].longitude if house_cusps else 0
    normalized = normalize_degrees(lon)
    diff = normalize_degrees(normalized - asc_lon)
    return int(diff / 30.0) + 1


_RASHI_INDEX = {
    "Mesha": 0, "Vrishabha": 1, "Mithuna": 2, "Karka": 3, "Simha": 4, "Kanya": 5,
    "Tula": 6, "Vrischika": 7, "Dhanu": 8, "Makara": 9, "Kumbha": 10, "Meena": 11,
}


def _longitude_for_rashi(rashi: str, degree_within_sign: float = 15.0) -> float:
    """Inverse of _rashi_from_longitude: midpoint longitude of a given sign."""
    idx = _RASHI_INDEX.get(rashi)
    if idx is None:
        raise ValueError(f"Unknown rashi: {rashi!r}")
    return idx * 30.0 + max(0.0, min(29.999, degree_within_sign))


def _longitude_for_house(
    target_house: int, house_cusps: list, degree_within_house: float = 15.0
) -> float:
    """Inverse of _house_from_longitude: a longitude that falls in target_house."""
    if not house_cusps:
        raise ValueError("Cannot place a planet in a house with no house cusps")
    asc_lon = house_cusps[0].longitude
    offset = (target_house - 1) * 30.0 + max(0.0, min(29.999, degree_within_house))
    return (asc_lon + offset) % 360.0


# ---------------------------------------------------------------------------
# DigitalTwinEngine
# ---------------------------------------------------------------------------

class DigitalTwinEngine:
    """
    Computes modified D1 charts from Digital Twin specifications.

    Composes AspectEngine and GrahaEngine to recalculate dependent data
    after modifications are applied.
    """

    def __init__(
        self,
        aspect_engine: Optional[AspectEngine] = None,
        graha_engine: Optional[GrahaEngine] = None,
        yoga_engine: Optional[YogaEngine] = None,
    ) -> None:
        self._aspect_engine = aspect_engine
        self._graha_engine = graha_engine
        self._yoga_engine = yoga_engine

    # ── Core: apply modifications ─────────────────────────────────────

    def apply_modifications(
        self,
        original_chart: D1Chart,
        modifications: tuple[TwinModification, ...],
    ) -> D1Chart:
        """
        Apply a list of modifications to an original D1Chart and return
        a new, fully recomputed D1Chart with modifications.

        This is a pure function — no side effects, no database writes.
        """
        if not modifications:
            return original_chart

        # Work with a mutable copy (deep copy to avoid mutating original)
        chart = copy.deepcopy(original_chart)

        # ── Apply each modification ───────────────────────────────────

        for mod in modifications:
            mod_type = mod.modification_type.value if hasattr(mod.modification_type, "value") else mod.modification_type

            if mod_type == "planet_position":
                chart = self._apply_planet_position(chart, mod)
            elif mod_type == "planet_strength":
                chart = self._apply_planet_strength(chart, mod)
            elif mod_type == "house_cusp":
                chart = self._apply_house_cusp(chart, mod)
            elif mod_type == "ascendant":
                chart = self._apply_ascendant(chart, mod)
            elif mod_type == "birth_time":
                chart = self._apply_birth_time(chart, mod)
            elif mod_type == "ayanamsa":
                chart = self._apply_ayanamsa(chart, mod)
            elif mod_type == "aspect":
                chart = self._apply_aspect_modification(chart, mod)
            elif mod_type == "retrograde":
                chart, _ = self._op_retrograde_planet(chart, {"planet": mod.target_id})
            else:
                logger.warning(f"Unknown modification type: {mod_type}")

        # ── Recompute dependent data ──────────────────────────────────

        chart = self._recompute_aspects(chart)
        chart = self._recompute_strengths(chart)

        return chart

    # ── Core: apply a single simulation operation ─────────────────────

    def apply_operation(
        self,
        chart: D1Chart,
        operation: TwinOperation,
    ) -> tuple[D1Chart, TwinOperationResult]:
        """
        Apply one named simulation operation to a chart and return the
        updated chart plus a result describing what changed.

        Supported operation_type values:
          - retrograde_planet:    params={"planet": str}
          - move_planet_to_house: params={"planet": str, "house": int (1-12)}
          - move_planet_to_sign:  params={"planet": str, "rashi": str}
          - conjunct_planets:     params={"planet": str, "with_planet": str}

        step_forward (time-shift recomputation) is deliberately NOT
        supported here — it would require re-running Swiss Ephemeris with
        a shifted birth datetime, which this pure, DB-free engine has no
        access to. Returns success=False with a clear error instead of
        silently pretending to compute it.
        """
        op_type = operation.operation_type
        params = operation.params

        handlers = {
            "retrograde_planet": self._op_retrograde_planet,
            "move_planet_to_house": self._op_move_planet_to_house,
            "move_planet_to_sign": self._op_move_planet_to_sign,
            "conjunct_planets": self._op_conjunct_planets,
        }

        if op_type == "step_forward":
            return chart, TwinOperationResult(
                operation_type=op_type,
                success=False,
                changes=(),
                error=(
                    "step_forward requires re-running Swiss Ephemeris with "
                    "a shifted birth time — not implemented."
                ),
            )

        handler = handlers.get(op_type)
        if handler is None:
            return chart, TwinOperationResult(
                operation_type=op_type,
                success=False,
                changes=(),
                error=f"Unknown operation_type: {op_type!r}",
            )

        try:
            new_chart, changes = handler(chart, params)
        except (KeyError, ValueError) as e:
            return chart, TwinOperationResult(
                operation_type=op_type,
                success=False,
                changes=(),
                error=str(e),
            )

        new_chart = self._recompute_aspects(new_chart)
        new_chart = self._recompute_strengths(new_chart)

        return new_chart, TwinOperationResult(
            operation_type=op_type,
            success=True,
            changes=tuple(changes),
        )

    def _op_retrograde_planet(
        self, chart: D1Chart, params: dict
    ) -> tuple[D1Chart, list[FieldDiff]]:
        planet_name = params["planet"]
        new_planets = []
        changes: list[FieldDiff] = []
        found = False
        for p in chart.planets:
            if p.planet == planet_name:
                found = True
                new_retro = not p.is_retrograde
                changes.append(FieldDiff(
                    field_path=f"planets.{planet_name}.is_retrograde",
                    label=f"{planet_name} retrograde",
                    old_value=p.is_retrograde,
                    new_value=new_retro,
                    significance="medium",
                ))
                new_planets.append(replace(p, is_retrograde=new_retro))
            else:
                new_planets.append(p)
        if not found:
            raise ValueError(f"Planet not found: {planet_name!r}")
        return replace(chart, planets=new_planets), changes

    def _op_move_planet_to_house(
        self, chart: D1Chart, params: dict
    ) -> tuple[D1Chart, list[FieldDiff]]:
        planet_name = params["planet"]
        target_house = int(params["house"])
        if not (1 <= target_house <= 12):
            raise ValueError(f"house must be 1-12, got {target_house}")
        new_lon = _longitude_for_house(target_house, chart.houses)
        return self._move_planet_to_longitude(chart, planet_name, new_lon)

    def _op_move_planet_to_sign(
        self, chart: D1Chart, params: dict
    ) -> tuple[D1Chart, list[FieldDiff]]:
        planet_name = params["planet"]
        new_lon = _longitude_for_rashi(params["rashi"])
        return self._move_planet_to_longitude(chart, planet_name, new_lon)

    def _op_conjunct_planets(
        self, chart: D1Chart, params: dict
    ) -> tuple[D1Chart, list[FieldDiff]]:
        planet_name = params["planet"]
        with_planet = params["with_planet"]
        target = next((p for p in chart.planets if p.planet == with_planet), None)
        if target is None:
            raise ValueError(f"Planet not found: {with_planet!r}")
        return self._move_planet_to_longitude(
            chart, planet_name, target.sidereal_longitude
        )

    def _move_planet_to_longitude(
        self, chart: D1Chart, planet_name: str, new_lon: float
    ) -> tuple[D1Chart, list[FieldDiff]]:
        new_planets = []
        changes: list[FieldDiff] = []
        found = False
        for p in chart.planets:
            if p.planet == planet_name:
                found = True
                new_rashi = _rashi_from_longitude(new_lon)
                new_house = _house_from_longitude(new_lon, chart.houses)
                if abs(new_lon - p.sidereal_longitude) > 0.0001:
                    changes.append(FieldDiff(
                        field_path=f"planets.{planet_name}.sidereal_longitude",
                        label=f"{planet_name} longitude",
                        old_value=p.sidereal_longitude,
                        new_value=new_lon,
                        delta=new_lon - p.sidereal_longitude,
                        significance="high",
                    ))
                new_planets.append(replace(
                    p,
                    sidereal_longitude=new_lon,
                    rashi=new_rashi,
                    house_number=new_house,
                ))
            else:
                new_planets.append(p)
        if not found:
            raise ValueError(f"Planet not found: {planet_name!r}")
        return replace(chart, planets=new_planets), changes

    # ── Individual modification applicators ───────────────────────────

    def _apply_planet_position(self, chart: D1Chart, mod: TwinModification) -> D1Chart:
        """Modify a planet's sidereal longitude and recompute rashi/house."""
        new_planets = []
        for planet in chart.planets:
            if planet.planet == mod.target_id:
                new_lon = float(mod.new_value)
                new_rashi = _rashi_from_longitude(new_lon)
                new_house = _house_from_longitude(new_lon, chart.houses)
                new_planets.append(replace(
                    planet,
                    sidereal_longitude=new_lon,
                    rashi=new_rashi,
                    house_number=new_house,
                ))
            else:
                new_planets.append(planet)

        return replace(chart, planets=new_planets)

    def _apply_planet_strength(self, chart: D1Chart, mod: TwinModification) -> D1Chart:
        """Override a planet's strength score directly."""
        new_strengths = []
        for ps in chart.planet_strengths:
            if ps.planet == mod.target_id:
                new_score = float(mod.new_value)
                new_strengths.append(replace(ps, strength_score=new_score))
            else:
                new_strengths.append(ps)

        return replace(chart, planet_strengths=new_strengths)

    def _apply_house_cusp(self, chart: D1Chart, mod: TwinModification) -> D1Chart:
        """Modify a house cusp longitude."""
        new_houses = []
        for house in chart.houses:
            house_label = f"house_{house.house_number}"
            if house_label == mod.target_id:
                new_lon = float(mod.new_value)
                new_rashi = _rashi_from_longitude(new_lon)
                new_houses.append(replace(
                    house,
                    longitude=new_lon,
                    sidereal_longitude=new_lon,
                    rashi=new_rashi,
                ))
            else:
                new_houses.append(house)

        # Recompute planet houses based on new cusps
        new_planets = []
        for planet in chart.planets:
            new_house = _house_from_longitude(planet.sidereal_longitude, new_houses)
            new_planets.append(replace(planet, house_number=new_house))

        return replace(chart, houses=new_houses, planets=new_planets)

    def _apply_ascendant(self, chart: D1Chart, mod: TwinModification) -> D1Chart:
        """Modify ascendant longitude."""
        new_lon = float(mod.new_value)
        new_rashi = _rashi_from_longitude(new_lon)
        new_asc = replace(
            chart.ascendant,
            longitude=new_lon,
            sidereal_longitude=new_lon,
            rashi=new_rashi,
            rashi_degree=new_lon % 30.0,
        )

        # Recompute all planet houses (ascendant drives house assignment)
        new_planets = []
        for planet in chart.planets:
            # Use first house cusp as reference; if ascendant changed, house boundaries shift
            asc_cusp = chart.houses[0] if chart.houses else None
            if asc_cusp:
                normalized = normalize_degrees(planet.sidereal_longitude)
                diff = normalize_degrees(normalized - new_lon)
                new_house = int(diff / 30.0) + 1
            else:
                new_house = planet.house_number
            new_planets.append(replace(planet, house_number=new_house))

        return replace(chart, ascendant=new_asc, planets=new_planets)

    def _apply_birth_time(self, chart: D1Chart, mod: TwinModification) -> D1Chart:
        """
        Apply a time shift to the birth chart.

        new_value should be a dict: {"hours": float, "minutes": float}
        representing the time delta to apply.
        """
        if not isinstance(mod.new_value, dict):
            return chart

        # For now, store as a note — full ephemeris re-query would be needed
        # to properly shift birth time. This is a placeholder for future
        # enhancement where we would re-run ephemeris_wrapper with adjusted datetime.
        logger.info(f"Birth time modification recorded: {mod.new_value}")
        return chart

    def _apply_ayanamsa(self, chart: D1Chart, mod: TwinModification) -> D1Chart:
        """Modify the ayanamsa system and recompute sidereal positions."""
        new_ayanamsa = str(mod.new_value)
        # Ayanamsa change would require re-running Swiss Ephemeris with the new
        # ayanamsa system. For now, store the change and log it.
        logger.info(f"Ayanamsa modification recorded: {new_ayanamsa}")
        return replace(chart, ayanamsa_system=new_ayanamsa)

    def _apply_aspect_modification(self, chart: D1Chart, mod: TwinModification) -> D1Chart:
        """
        Add or remove an aspect between two planets.

        new_value: {"action": "add"|"remove", "aspect_type": str}
        """
        if not isinstance(mod.new_value, dict):
            return chart

        action = mod.new_value.get("action", "add")
        aspect_type = mod.new_value.get("aspect_type", "conjunction")
        planet_ids = mod.target_id.split("-")
        if len(planet_ids) != 2:
            return chart

        from_planet, to_planet = planet_ids

        if action == "remove":
            new_aspects = [
                a for a in chart.aspects
                if not (a.from_planet == from_planet and a.to_planet == to_planet)
            ]
            return replace(chart, aspects=new_aspects)
        elif action == "add":
            new_aspect = AspectInfo(
                from_planet=from_planet,
                to_planet=to_planet,
                aspect_type=aspect_type,
                orb_degrees=0.0,
                is_applying=False,
            )
            return replace(chart, aspects=tuple(list(chart.aspects) + [new_aspect]))
        return chart

    # ── Recomputation helpers ─────────────────────────────────────────

    def _recompute_aspects(self, chart: D1Chart) -> D1Chart:
        """Recompute aspects based on current planet positions."""
        if self._aspect_engine is None:
            return chart

        try:
            new_aspects = self._aspect_engine.compute(chart.planets)
            return replace(chart, aspects=tuple(new_aspects))
        except Exception as e:
            logger.warning(f"Aspect recomputation failed, keeping original: {e}")
            return chart

    def _recompute_strengths(self, chart: D1Chart) -> D1Chart:
        """
        Recompute planet strengths based on current positions and dignity.

        Uses GrahaEngine — the same dignity+positional strength scorer
        the real chart-generation pipeline uses for D1Chart.planet_strengths
        (see horoscope_engine.py). ShadbalaEngine is a different, six-fold
        strength system with no single "recompute all strengths" method
        matching this field's shape — using it here would have been wrong
        regardless of the method name.
        """
        if self._graha_engine is None:
            return chart

        try:
            new_strengths = self._graha_engine.compute_strength(chart.planets)
            return replace(chart, planet_strengths=tuple(new_strengths))
        except Exception as e:
            logger.warning(f"Strength recomputation failed, keeping original: {e}")
            return chart

    # ── Comparison ────────────────────────────────────────────────────

    def compare_charts(
        self,
        original: D1Chart,
        twin: D1Chart,
        modifications: tuple[TwinModification, ...],
    ) -> TwinComparison:
        """
        Generate a detailed comparison between original and modified charts.
        Returns field-level diffs and aggregated metrics.
        """
        diffs: list[FieldDiff] = []

        # Compare planets
        orig_planets = {p.planet: p for p in original.planets}
        twin_planets = {p.planet: p for p in twin.planets}

        for planet_name in orig_planets:
            orig = orig_planets[planet_name]
            modified = twin_planets.get(planet_name)

            if modified is None:
                continue

            # Longitude diff
            lon_diff = modified.sidereal_longitude - orig.sidereal_longitude
            if abs(lon_diff) > 0.001:
                diffs.append(FieldDiff(
                    field_path=f"planets.{planet_name}.sidereal_longitude",
                    label=f"{planet_name} longitude",
                    old_value=orig.sidereal_longitude,
                    new_value=modified.sidereal_longitude,
                    delta=lon_diff,
                    significance="high" if abs(lon_diff) > 15.0 else "medium",
                ))

            # House diff
            if modified.house_number != orig.house_number:
                diffs.append(FieldDiff(
                    field_path=f"planets.{planet_name}.house_number",
                    label=f"{planet_name} house",
                    old_value=orig.house_number,
                    new_value=modified.house_number,
                    delta=float(modified.house_number - orig.house_number),
                    significance="high",
                ))

            # Sign diff
            if modified.rashi != orig.rashi:
                diffs.append(FieldDiff(
                    field_path=f"planets.{planet_name}.rashi",
                    label=f"{planet_name} sign",
                    old_value=orig.rashi,
                    new_value=modified.rashi,
                    significance="high",
                ))

        # Compare ascendant
        if original.ascendant.sidereal_longitude != twin.ascendant.sidereal_longitude:
            diffs.append(FieldDiff(
                field_path="ascendant.sidereal_longitude",
                label="Ascendant longitude",
                old_value=original.ascendant.sidereal_longitude,
                new_value=twin.ascendant.sidereal_longitude,
                delta=twin.ascendant.sidereal_longitude - original.ascendant.sidereal_longitude,
                significance="critical",
            ))

        # Strengths comparison
        orig_strengths = {ps.planet: ps.strength_score for ps in original.planet_strengths}
        twin_strengths = {ps.planet: ps.strength_score for ps in twin.planet_strengths}

        for planet_name in orig_strengths:
            orig_val = orig_strengths[planet_name]
            twin_val = twin_strengths.get(planet_name)
            if twin_val is not None and abs(twin_val - orig_val) > 0.001:
                diffs.append(FieldDiff(
                    field_path=f"planet_strengths.{planet_name}.strength_score",
                    label=f"{planet_name} strength score",
                    old_value=orig_val,
                    new_value=twin_val,
                    delta=twin_val - orig_val,
                    significance="medium" if abs(twin_val - orig_val) > 1.0 else "low",
                ))

        # Metrics summary
        metrics_before = {
            "total_strength": sum(ps.strength_score for ps in original.planet_strengths),
            "aspect_count": len(original.aspects),
            "planet_count": len(original.planets),
        }
        metrics_after = {
            "total_strength": sum(ps.strength_score for ps in twin.planet_strengths),
            "aspect_count": len(twin.aspects),
            "planet_count": len(twin.planets),
        }

        # Build summary
        significant_diffs = [d for d in diffs if d.significance in ("high", "critical")]
        if not significant_diffs:
            summary = "No significant differences detected."
        else:
            labels = [d.label for d in significant_diffs[:5]]
            summary = f"Significant changes in: {', '.join(labels)}."

        return TwinComparison(
            twin_id=uuid.uuid4(),  # placeholder; actual ID filled by service layer
            original_chart_id=uuid.uuid4(),  # placeholder
            total_modifications=len(modifications),
            field_diffs=tuple(diffs),
            metrics_before=metrics_before,
            metrics_after=metrics_after,
            summary=summary,
        )

    # ── Cached state computation ──────────────────────────────────────

    def compute_cached_state(
        self,
        chart: D1Chart,
        yoga_engine: Optional[YogaEngine] = None,
    ) -> dict:
        """
        Compute and return the cached chart state to store on the twin.
        This is called once after creation/recalculation.
        """
        engine = yoga_engine or self._yoga_engine
        yoga_names: list[str] = []

        if engine is not None:
            try:
                yoga_results = engine.detect_yogas(chart)
                yoga_names = [y.title for y in yoga_results]
            except Exception as e:
                logger.warning(f"Yoga detection failed during caching: {e}")

        return {
            "yoga_names": yoga_names,
            "strengths_count": len(chart.planet_strengths),
            "aspect_count": len(chart.aspects),
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }
