"""
AstroOS — Benchmark Engine (Module 16, Phase C — Expanded)

Validates computed charts against the GC-MASTER golden-reference dataset
across three benchmark families:
  - BM-CALC:  Planet position accuracy (9 grahas)
  - BM-HOUSE: House cusp accuracy (4 house systems)
  - BM-VARGA: Divisional chart accuracy (15 vargas)
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from apps.api.domain.benchmark import (
    BenchmarkResult,
    BenchmarkSummary,
    HouseBenchmark,
    HouseBenchmarkResult,
    PlanetBenchmark,
    VargaBenchmark,
    VargaBenchmarkResult,
)
from apps.api.domain.divisional import VargaChart
from apps.api.domain.horoscope import D1Chart


def _positional_error(computed: float, expected: float) -> float:
    """Shortest angular distance in degrees (0-180)."""
    raw = abs(computed - expected)
    return min(raw, 360.0 - raw)


_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
_ALL_NINE = _CLASSICAL_SEVEN + ["rahu", "ketu"]

_DEFAULT_TOLERANCE = 0.5  # degrees — Tier B default
_TIER_A_TOLERANCE = 0.1  # degrees — Tier A (verified births)

# House system tolerances per BM-HOUSE spec
_HOUSE_TOLERANCES = {"W": 0.001, "P": 0.1, "K": 0.1, "E": 0.001}

_RASHI_ORDER = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]


def _rashi_index(rashi: str) -> int:
    """Convert rashi name to 0-indexed position."""
    try:
        return _RASHI_ORDER.index(rashi.lower())
    except ValueError:
        return 0


class BenchmarkEngine:
    """
    Validates charts against GC-MASTER golden reference data.
    Supports CALC (planet positions), HOUSE (house cusps), and
    VARGA (divisional charts) benchmark families.
    """

    def __init__(
        self,
        gc_master_path: str | None = None,
        tolerance: float = _DEFAULT_TOLERANCE,
    ) -> None:
        if gc_master_path is None:
            gc_master_path = os.getenv(
                "GC_MASTER_PATH",
                str(Path(__file__).parent.parent.parent.parent
                    / "datasets" / "gc-master" / "GC-MASTER-v1.0.0.json"),
            )
        self._gc_master: dict[str, Any] = {}
        self._tolerance = tolerance
        self._load_gc_master(gc_master_path)

    def _load_gc_master(self, path: str) -> None:
        p = Path(path)
        if p.is_file():
            with open(p, encoding="utf-8") as f:
                self._gc_master = json.load(f)
        else:
            self._gc_master = {}

    @property
    def is_loaded(self) -> bool:
        return bool(self._gc_master)

    @property
    def reference_count(self) -> int:
        return len(self._gc_master.get("references", []))

    def get_reference_for_chart(
        self, chart: D1Chart,
    ) -> Optional[dict[str, Any]]:
        references = self._gc_master.get("references", [])
        if not references:
            return None
        chart_date = chart.birth_date.isoformat() if hasattr(chart, "birth_date") else None
        for ref in references:
            if ref.get("birth_data", {}).get("date") == chart_date:
                return ref
        chart_name = getattr(chart, "subject_name", "").lower()
        if chart_name:
            for ref in references:
                ref_name = ref.get("person_name", "").lower()
                if chart_name in ref_name or ref_name in chart_name:
                    return ref
        return None

    # ── Reference lookup helpers ─────────────────────────────────────────

    def _get_reference_by_id(self, reference_id: str) -> Optional[dict[str, Any]]:
        for ref in self._gc_master.get("references", []):
            if ref.get("chart_id") == reference_id:
                return ref
        return None

    def _get_reference_by_name(self, name: str) -> Optional[dict[str, Any]]:
        name_lower = name.lower()
        for ref in self._gc_master.get("references", []):
            ref_name = ref.get("person_name", "").lower()
            if name_lower in ref_name or ref_name in name_lower:
                return ref
        return None

    def _resolve_reference(
        self,
        reference_id: str | None = None,
        subject_name: str | None = None,
        chart: D1Chart | None = None,
    ) -> Optional[dict[str, Any]]:
        if reference_id:
            return self._get_reference_by_id(reference_id)
        if subject_name:
            ref = self._get_reference_by_name(subject_name)
            if ref:
                return ref
        if chart is not None:
            return self.get_reference_for_chart(chart)
        return None

    # ── BM-CALC: Planet position validation ─────────────────────────────

    def validate_chart(
        self,
        chart: D1Chart,
        reference_id: str | None = None,
        subject_name: str | None = None,
    ) -> BenchmarkResult:
        ref = self._resolve_reference(reference_id, subject_name, chart)
        if ref is None:
            return BenchmarkResult(
                chart_id=chart.id if hasattr(chart, "id") else None,
                reference_id=reference_id or "unknown",
                reference_name="No matching reference found",
                planets=(),
                mean_error=0.0, max_error=0.0,
                passed=False, tolerance=self._tolerance,
                timestamp=datetime.now(timezone.utc),
            )
        tier = ref.get("confidence_tier", "C")
        tolerance = _TIER_A_TOLERANCE if tier == "A" else self._tolerance
        expected_planets = ref.get("expected_planets", {})

        planets: list[PlanetBenchmark] = []
        total_error = 0.0
        max_error = 0.0
        planet_count = 0

        for position in chart.planets:
            planet = position.planet
            if planet not in expected_planets:
                continue
            computed_lon = position.sidereal_longitude
            expected_lon = expected_planets[planet].get("longitude", 0.0)
            error = _positional_error(computed_lon, expected_lon)
            total_error += error
            max_error = max(max_error, error)
            planet_count += 1
            planets.append(PlanetBenchmark(
                planet=planet,
                computed_longitude=computed_lon,
                expected_longitude=expected_lon,
                error_degrees=round(error, 4),
                within_tolerance=error <= tolerance,
            ))

        mean_error = round(total_error / planet_count, 4) if planet_count > 0 else 0.0
        passed = all(p.within_tolerance for p in planets)

        return BenchmarkResult(
            chart_id=chart.id if hasattr(chart, "id") else None,
            reference_id=ref.get("chart_id", reference_id or "unknown"),
            reference_name=ref.get("person_name", "Unknown"),
            planets=tuple(planets),
            mean_error=mean_error,
            max_error=round(max_error, 4),
            passed=passed,
            tolerance=tolerance,
            timestamp=datetime.now(timezone.utc),
        )

    # ── BM-HOUSE: House cusp validation ─────────────────────────────────

    def validate_house_cusps(
        self,
        chart: D1Chart,
        house_system: str = "W",
        reference_id: str | None = None,
        subject_name: str | None = None,
    ) -> HouseBenchmarkResult:
        """Validate computed house cusps against GC-MASTER expected data."""
        ref = self._resolve_reference(reference_id, subject_name, chart)
        if ref is None:
            return HouseBenchmarkResult(
                reference_id=reference_id or "unknown",
                reference_name="No matching reference found",
                house_system=house_system,
                cusps=(),
                mean_error=0.0, max_error=0.0,
                passed=False,
                tolerance=_HOUSE_TOLERANCES.get(house_system, 0.5),
            )

        expected_houses = ref.get("expected_house_cusps", {}).get(house_system, {})
        tolerance = _HOUSE_TOLERANCES.get(house_system, 0.5)

        cusps: list[HouseBenchmark] = []
        total_error = 0.0
        max_error = 0.0
        count = 0

        for hc in chart.houses:
            sn = str(hc.house_number)
            if sn not in expected_houses:
                continue
            expected_cusp = expected_houses[sn]
            error = _positional_error(hc.sidereal_longitude, expected_cusp)
            total_error += error
            max_error = max(max_error, error)
            count += 1
            cusps.append(HouseBenchmark(
                house_number=hc.house_number,
                computed_cusp=hc.sidereal_longitude,
                expected_cusp=expected_cusp,
                error_degrees=round(error, 4),
                within_tolerance=error <= tolerance,
            ))

        mean_error = round(total_error / count, 4) if count > 0 else 0.0
        passed = all(c.within_tolerance for c in cusps) if cusps else False

        return HouseBenchmarkResult(
            reference_id=ref.get("chart_id", reference_id or "unknown"),
            reference_name=ref.get("person_name", "Unknown"),
            house_system=house_system,
            cusps=tuple(cusps),
            mean_error=mean_error,
            max_error=round(max_error, 4),
            passed=passed,
            tolerance=tolerance,
        )

    # ── BM-VARGA: Divisional chart validation ───────────────────────────

    def validate_varga(
        self,
        varga_chart: VargaChart,
        reference_id: str | None = None,
        subject_name: str | None = None,
    ) -> VargaBenchmarkResult:
        """Validate a divisional chart against GC-MASTER expected data."""
        ref = self._resolve_reference(reference_id, subject_name)
        if ref is None:
            return VargaBenchmarkResult(
                reference_id=reference_id or "unknown",
                reference_name="No matching reference found",
                vargas=(),
                total_checks=0, matched=0, failed=0,
            )

        expected_vargas = ref.get("expected_vargas", {})
        vc = varga_chart.varga
        expected = expected_vargas.get(vc, {})

        benchmarks: list[VargaBenchmark] = []
        matched = 0
        failed = 0

        for pos in varga_chart.planet_positions:
            planet = pos.planet
            expected_planet = expected.get(planet, {})
            expected_rashi = expected_planet.get("rashi", "")
            rashi_match = pos.varga_rashi == expected_rashi if expected_rashi else True
            if rashi_match:
                matched += 1
            else:
                failed += 1
            benchmarks.append(VargaBenchmark(
                varga_code=vc,
                planet=planet,
                computed_rashi=pos.varga_rashi,
                expected_rashi=expected_rashi,
                matched=rashi_match,
            ))

        return VargaBenchmarkResult(
            reference_id=ref.get("chart_id", reference_id or "unknown"),
            reference_name=ref.get("person_name", "Unknown"),
            vargas=tuple(benchmarks),
            total_checks=len(benchmarks),
            matched=matched,
            failed=failed,
        )

    # ── BM-ALL: Aggregate validation ────────────────────────────────────

    def validate_all(
        self,
        chart: D1Chart,
        vargas: dict[str, VargaChart] | None = None,
        house_systems: list[str] | None = None,
        reference_id: str | None = None,
        subject_name: str | None = None,
    ) -> BenchmarkSummary:
        """
        Run all validations (CALC + HOUSE + VARGA) and return an
        aggregate BenchmarkSummary.
        """
        calc_result = self.validate_chart(chart, reference_id, subject_name)

        house_results: list[HouseBenchmarkResult] = []
        if house_systems:
            for hs in house_systems:
                hr = self.validate_house_cusps(chart, hs, reference_id, subject_name)
                house_results.append(hr)

        varga_results: list[VargaBenchmarkResult] = []
        if vargas:
            for vc in sorted(vargas.keys()):
                vr = self.validate_varga(vargas[vc], reference_id, subject_name)
                varga_results.append(vr)

        all_results = [calc_result]
        total_passed = 1 if calc_result.passed else 0
        total_failed = 0 if calc_result.passed else 1

        all_house_passed = all(h.passed for h in house_results)
        all_varga_passed = all(v.failed == 0 for v in varga_results)

        if house_results:
            total_passed += (1 if all_house_passed else 0)
            total_failed += (0 if all_house_passed else 1)
        if varga_results:
            total_passed += (1 if all_varga_passed else 0)
            total_failed += (0 if all_varga_passed else 1)

        family_summary = {
            "calc": {"passed": 1 if calc_result.passed else 0, "failed": 0 if calc_result.passed else 1, "mean_error": calc_result.mean_error},
        }
        if house_results:
            house_mean = sum(h.mean_error for h in house_results) / len(house_results)
            family_summary["house"] = {"passed": sum(1 for h in house_results if h.passed), "failed": sum(1 for h in house_results if not h.passed), "mean_error": round(house_mean, 4)}
        if varga_results:
            varga_total = sum(v.total_checks for v in varga_results)
            varga_matched = sum(v.matched for v in varga_results)
            varga_failed = sum(v.failed for v in varga_results)
            family_summary["varga"] = {"passed": varga_matched, "failed": varga_failed, "total_checks": varga_total}

        return BenchmarkSummary(
            total_charts=1,
            passed=total_passed,
            failed=total_failed,
            results=tuple(all_results),
            overall_mean_error=calc_result.mean_error,
            house_results=tuple(house_results),
            varga_results=tuple(varga_results),
            family_summary=family_summary,
        )

    def validate_all_references(
        self,
        horoscope_engine: Any,
        divisional_engine: Any,
        house_systems: list[str] | None = None,
        include_vargas: bool = True,
    ) -> BenchmarkSummary:
        """
        Run benchmark validation against EVERY GC-MASTER reference chart.
        Computes per-house-system charts for accurate house cusp validation.
        """
        refs = self._gc_master.get("references", [])
        if not refs:
            return BenchmarkSummary(
                total_charts=0, passed=0, failed=0,
                results=(), overall_mean_error=0.0,
            )

        all_results: list[BenchmarkResult] = []
        all_house: list[HouseBenchmarkResult] = []
        all_varga: list[VargaBenchmarkResult] = []
        total_passed_charts = 0
        total_failed_charts = 0
        hs_list = house_systems or []

        for ref in refs:
            chart_id_str = ref.get("chart_id", "unknown")
            birth = ref.get("birth_data", {})
            dt_str = f"{birth.get('date', '')}T{birth.get('time_utc', '')}"
            try:
                from datetime import datetime as dt_cls
                birth_dt = dt_cls.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                continue
            lat = birth.get("latitude", 0)
            lon = birth.get("longitude", 0)

            chart = horoscope_engine.generate_d1(
                birth_datetime_utc=birth_dt, latitude=lat, longitude=lon,
                ayanamsa="lahiri", house_system="W",
            )

            vargas = None
            if include_vargas and divisional_engine is not None:
                vargas = divisional_engine.compute_all(
                    birth_datetime_utc=birth_dt, latitude=lat, longitude=lon,
                    ayanamsa="lahiri", house_system="W",
                )

            calc_result = self.validate_chart(chart, reference_id=chart_id_str)
            all_results.append(calc_result)
            chart_pass = 1 if calc_result.passed else 0
            chart_fail = 0 if calc_result.passed else 1

            # House cusp validation: compute per-house-system chart.
            house_pass_count = 0
            house_fail_count = 0
            for hs in hs_list:
                hs_chart = horoscope_engine.generate_d1(
                    birth_datetime_utc=birth_dt, latitude=lat, longitude=lon,
                    ayanamsa="lahiri", house_system=hs,
                )
                hr = self.validate_house_cusps(hs_chart, hs, reference_id=chart_id_str)
                all_house.append(hr)
                if hr.passed:
                    house_pass_count += 1
                else:
                    house_fail_count += 1

            # Varga validation.
            varga_pass = 0
            varga_fail = 0
            if vargas:
                for vc in sorted(vargas.keys()):
                    vr = self.validate_varga(vargas[vc], reference_id=chart_id_str)
                    all_varga.append(vr)
                    if vr.failed == 0:
                        varga_pass += 1
                    else:
                        varga_fail += 1

            if chart_fail == 0:
                total_passed_charts += 1
            else:
                total_failed_charts += 1

        all_mean = sum(r.mean_error for r in all_results) / len(all_results) if all_results else 0.0

        calc_passed = sum(1 for r in all_results if r.passed)
        calc_failed = sum(1 for r in all_results if not r.passed)
        house_passed = sum(1 for h in all_house if h.passed)
        house_failed = sum(1 for h in all_house if not h.passed)
        house_mean = sum(h.mean_error for h in all_house) / len(all_house) if all_house else 0.0
        varga_total = sum(v.total_checks for v in all_varga)
        varga_matched = sum(v.matched for v in all_varga)
        varga_failed_total = sum(v.failed for v in all_varga)

        family = {
            "calc": {"passed": calc_passed, "failed": calc_failed, "mean_error": round(all_mean, 4)},
        }
        if all_house:
            family["house"] = {"passed": house_passed, "failed": house_failed, "mean_error": round(house_mean, 4)}
        if all_varga:
            family["varga"] = {"passed": varga_matched, "failed": varga_failed_total, "total_checks": varga_total}

        return BenchmarkSummary(
            total_charts=len(refs),
            passed=total_passed_charts,
            failed=total_failed_charts,
            results=tuple(all_results),
            overall_mean_error=round(all_mean, 4),
            house_results=tuple(all_house),
            varga_results=tuple(all_varga),
            family_summary=family,
        )
