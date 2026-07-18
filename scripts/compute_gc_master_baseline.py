"""
AstroOS — GC-MASTER Baseline Computation Script

Populates expected_planets, expected_house_cusps, and expected_vargas
in GC-MASTER-v1.0.0.json by computing charts for each reference birth
record using the active ephemeris.

Run whenever the ephemeris or calculation engine changes:
    PYTHONPATH=. python scripts/compute_gc_master_baseline.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.api.services.divisional_engine import DivisionalEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine

_GC_MASTER_PATH = Path(__file__).parent.parent / "datasets" / "gc-master" / "GC-MASTER-v1.0.0.json"
_EPHEMERIS_PATH = str(Path(__file__).parent.parent / "data" / "ephemeris")
_HOUSE_SYSTEMS = ["W", "P", "K", "E"]


def _load_gc_master() -> dict:
    with open(_GC_MASTER_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save_gc_master(data: dict) -> None:
    with open(_GC_MASTER_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Written to {_GC_MASTER_PATH}")


def _build_expected_planet_map(chart) -> dict[str, dict]:
    planets = {}
    for position in chart.planets:
        planets[position.planet] = {
            "longitude": round(position.sidereal_longitude, 6),
            "rashi": position.rashi,
            "rashi_degree": round(position.rashi_degree, 6),
            "house_number": position.house_number,
            "nakshatra": position.nakshatra,
            "pada": position.pada,
        }
    return planets


def _build_house_cusp_map(chart) -> dict[str, float]:
    """Extract per-house sidereal cusp values from a D1Chart."""
    cusps = {}
    for hc in chart.houses:
        cusps[str(hc.house_number)] = round(hc.sidereal_longitude, 6)
    return cusps


def _build_varga_map(vargas: dict) -> dict[str, dict]:
    """Extract per-planet per-varga rashi/house from all divisional charts."""
    result = {}
    for varga_code, vc in vargas.items():
        planets = {}
        for pos in vc.planet_positions:
            planets[pos.planet] = {
                "rashi": pos.varga_rashi,
                "house": pos.varga_house_number,
            }
        result[varga_code] = planets
    return result


def main() -> None:
    data = _load_gc_master()
    wrapper = EphemerisWrapper(ephemeris_path=_EPHEMERIS_PATH)
    horoscope = HoroscopeEngine(wrapper)
    divisional = DivisionalEngine(wrapper)

    references = data.get("references", [])
    print("GC-MASTER Baseline Computation")
    print(f"  Dataset: {data.get('dataset_id')} v{data.get('version')}")
    print(f"  References: {len(references)}")
    print()

    for ref in references:
        chart_id = ref["chart_id"]
        name = ref["person_name"]
        tier = ref.get("confidence_tier", "C")
        birth = ref["birth_data"]

        print(f"  [{tier}] {chart_id} - {name}")

        dt_str = f"{birth['date']}T{birth['time_utc']}"
        try:
            birth_dt = datetime.fromisoformat(dt_str)
        except ValueError:
            birth_dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
        birth_dt = birth_dt.replace(tzinfo=timezone.utc)
        lat, lon = birth["latitude"], birth["longitude"]

        try:
            # Compute D1 chart (Lahiri, Whole Sign).
            chart = horoscope.generate_d1(
                birth_datetime_utc=birth_dt, latitude=lat, longitude=lon,
                ayanamsa="lahiri", house_system="W",
            )
            ref["expected_planets"] = _build_expected_planet_map(chart)
            ref["expected_house_cusps"] = {"W": _build_house_cusp_map(chart)}
            print(f"    planets: {len(ref['expected_planets'])}")

            # Compute vargas.
            vargas = divisional.compute_all(
                birth_datetime_utc=birth_dt, latitude=lat, longitude=lon,
                ayanamsa="lahiri", house_system="W",
            )
            ref["expected_vargas"] = _build_varga_map(vargas)
            print(f"    vargas: {len(ref['expected_vargas'])} computed")

            # Compute house cusps for remaining house systems.
            for hs in _HOUSE_SYSTEMS[1:]:
                chart_hs = horoscope.generate_d1(
                    birth_datetime_utc=birth_dt, latitude=lat, longitude=lon,
                    ayanamsa="lahiri", house_system=hs,
                )
                ref["expected_house_cusps"][hs] = _build_house_cusp_map(chart_hs)
            print(f"    house_systems: {list(ref['expected_house_cusps'].keys())}")

        except Exception as exc:
            print(f"    !! ERROR: {exc}")
            ref.setdefault("expected_planets", {})
            ref.setdefault("expected_house_cusps", {})
            ref.setdefault("expected_vargas", {})

    data["status"] = "STABLE"
    _save_gc_master(data)
    print(f"\nDone. Dataset status updated to STABLE.")


if __name__ == "__main__":
    main()
