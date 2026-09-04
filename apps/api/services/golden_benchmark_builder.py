"""
AstroOS — Golden Benchmark Native Builder & Canonical Exporter
=============================================================
Builds and exports golden benchmark native charts according to the exact
canonical schema:
{
  "native_id": "D01",
  "birth": {"date": "...", "time": "...", "lat": ..., "lon": ..., "tz": ...},
  "graha_longitudes": {"sun": ..., "moon": ..., ...},
  "bhava_positions": {...},
  "vargas": {"D9": {...}, "D60": {...}},
  "dashas": {"vimshottari": {"mahadasha": [...], "antardasha": [...]},
              "ashtottari": {...}, "kcd": {...}, "yogini": {...}},
  "provenance": {"source_offset": ..., "extraction_script_version": "0.1", "jha_verified": False}
}
"""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from apps.api.services.ashtottari_dasha import compute_ashtottari_dasha_tree
from apps.api.services.d60_deities import evaluate_chart_d60_deities
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.jha_vimsottari import JhaVimsottariEngine
from apps.api.services.kalachakra_dasha_engine import KalachakraDashaEngine
from apps.api.services.yogini_dasha import compute_yogini_dasha_tree


class GoldenBenchmarkBuilder:
    """Constructs fully evaluated golden benchmark records matching the canonical schema."""

    def __init__(self, ephemeris_path: str = "data/ephemeris") -> None:
        self._wrapper = EphemerisWrapper(ephemeris_path=ephemeris_path)
        self.vimsottari = JhaVimsottariEngine(self._wrapper)

    def build_native_record(
        self,
        native_id: str,
        birth_date_str: str,  # YYYY-MM-DD
        birth_time_str: str,  # HH:MM or HH:MM:SS
        lat: float,
        lon: float,
        tz_name: str = "UTC",
        source_offset: Optional[int] = None,
        script_version: str = "1.0",
        jha_verified: bool = False,
    ) -> dict[str, Any]:
        """Builds a single canonical golden benchmark record."""
        # 1. Parse Datetime
        b_date = date.fromisoformat(birth_date_str)
        t_parts = [int(p) for p in birth_time_str.split(":")]
        b_time = time(t_parts[0], t_parts[1], t_parts[2] if len(t_parts) > 2 else 0)

        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = timezone.utc

        dt_local = datetime.combine(b_date, b_time, tzinfo=tz)
        dt_utc = dt_local.astimezone(timezone.utc)

        # 2. Ephemeris calculation (Lahiri Nirayana)
        eph = self._wrapper.calculate(dt_utc, latitude=lat, longitude=lon, ayanamsa="lahiri")

        graha_longitudes: dict[str, float] = {}
        for p in eph.planet_positions:
            graha_longitudes[p.planet.lower()] = round(p.sidereal_longitude, 6)
        if eph.ascendant:
            graha_longitudes["ascendant"] = round(eph.ascendant.sidereal_longitude, 6)

        moon_lon = graha_longitudes.get("moon", 0.0)

        # 3. Bhava Positions (12 Houses)
        bhava_positions: dict[int, float] = {}
        for cusp in eph.house_cusps:
            bhava_positions[cusp.house_number] = round(cusp.sidereal_longitude, 6)

        # 4. Vargas (D9 and D60)
        d9_positions: dict[str, float] = {}
        for p, p_lon in graha_longitudes.items():
            d9_positions[p] = round((p_lon * 9.0) % 360.0, 6)

        d60_eval = evaluate_chart_d60_deities(graha_longitudes, tradition="bphs")

        # 5. Dashas
        # A. Vimshottari (120 Years - Surya Siddhanta Solar)
        v_tree = self.vimsottari.compute_varga_dasha_tree(
            birth_datetime=dt_utc,
            latitude=lat,
            longitude=lon,
            varga_code="D1",
            max_depth=2,
            year_convention="surya_siddhanta_solar",
        )

        v_mahadashas = []
        v_antardashas = []
        for md in v_tree.mahadashas:
            v_mahadashas.append({
                "lord": md.lord,
                "start": str(md.start_date),
                "end": str(md.end_date),
                "duration_days": md.duration_days,
            })
            for ad in md.sub_periods:
                v_antardashas.append({
                    "maha_lord": md.lord,
                    "antar_lord": ad.lord,
                    "start": str(ad.start_date),
                    "end": str(ad.end_date),
                    "duration_days": ad.duration_days,
                })

        # B. Ashtottari (108 Years - True Tithi)
        ashtottari_tree = compute_ashtottari_dasha_tree(
            birth_datetime=dt_utc,
            moon_longitude=moon_lon,
            num_cycles=1,
        )

        # C. Yogini (36 Years - Mean Tithi)
        yogini_tree = compute_yogini_dasha_tree(
            birth_datetime=dt_utc,
            moon_longitude=moon_lon,
            num_cycles=2,
        )

        # D. Kalachakra (KCD - Canonical Savya/Apasavya & Deha/Jeeva)
        kcd_engine = KalachakraDashaEngine()
        kcd_res = kcd_engine.compute_kalachakra_dasha(
            birth_datetime=dt_utc,
            moon_longitude=moon_lon,
            num_cycles=1,
        )

        dashas = {
            "vimshottari": {
                "cycle_years": 120,
                "year_basis": "surya_siddhanta_solar",
                "balance_at_birth_years": round(v_tree.balance_at_birth, 4),
                "trigger_planet": v_tree.trigger_planet,
                "mahadasha": v_mahadashas,
                "antardasha": v_antardashas,
            },
            "ashtottari": {
                "cycle_years": 108,
                "year_basis": "exact_true_tithi",
                "starting_lord": ashtottari_tree["starting_lord"],
                "balance_at_birth_years": ashtottari_tree["balance_at_birth_years"],
                "mahadasha": ashtottari_tree["mahadashas"],
            },
            "kcd": {
                "cycle_type": kcd_res["cycle_type"],
                "year_basis": "mean_tithi",
                "navamsha_sign": kcd_res["navamsha_sign"],
                "deha_rashi": kcd_res["deha_rashi"],
                "jeeva_rashi": kcd_res["jeeva_rashi"],
                "total_sequence_years": kcd_res["total_sequence_years"],
                "balance_at_birth_years": kcd_res["balance_years"],
                "mahadasha": kcd_res["mahadashas"],
            },
            "yogini": {
                "cycle_years": 36,
                "year_basis": "mean_tithi",
                "starting_yogini": yogini_tree["starting_yogini"],
                "balance_at_birth_years": yogini_tree["balance_at_birth_years"],
                "mahadasha": yogini_tree["mahadashas"],
            },
        }

        # 6. Assemble record
        return {
            "native_id": native_id,
            "birth": {
                "date": birth_date_str,
                "time": birth_time_str,
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "tz": tz_name,
            },
            "graha_longitudes": graha_longitudes,
            "bhava_positions": bhava_positions,
            "vargas": {
                "D9": d9_positions,
                "D60": d60_eval,
            },
            "dashas": dashas,
            "provenance": {
                "source_offset": source_offset or 527600,
                "extraction_script_version": script_version,
                "engine": "AstroOS Canonical Siddhantic Engine",
                "jha_verified": jha_verified,
            },
        }