"""
AstroOS — Rajesh (Raj) Canonical Shastric Synthesis & Actionable Playbook
========================================================================
Executes the full 3-Chart Synthesis (D1 Bhaavachalita + D10/D24 Vargas + VPC/SCD)
and generates the complete deterministic milestone timeline and playbook for Raj:

  1. D1 Vishamabhava Bhaavachalita & Tri-Lagna Sudarshana Chakra (SC)
  2. D10 Dashamsha (Career) & D24 Chaturvimsamsha (Vidya) Vimshopaka Synthesis
  3. VPC Solar Returns & SCD Monthly Entries (2024 - 2028)
  4. Vimshottari MD / AD / PD Dasha Hierarchy
  5. TPhalitCore Signed Numerical State & Deterministic Playbook
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import sys

sys.path.insert(0, ".")

from apps.api.domain.tphalit_core import ChartLevelEnum
from apps.api.services.bhavachalita_engine import VishamabhavaEngine
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.divisional_synthesis_engine import DivisionalSynthesisEngine, VimshopakaScheme
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.sudarshana_chakra_engine import SudarshanaChakraEngine
from apps.api.services.tphalit_core_engine import TPhalitCoreEngine
from apps.api.services.upagraha_engine import UpagrahaEngine
from apps.api.services.vpc_engine import VPCEngine


def run_raj_synthesis():
    print("=" * 80)
    print("ASTROOS CANONICAL SHASTRIC SYNTHESIS: RAJESH (RAJ)")
    print("=" * 80)

    # 1. Subject Details
    birth_dt_utc = datetime(1971, 6, 29, 23, 27, 40, tzinfo=timezone.utc)
    lat, lon = 28.6139, 77.2090  # New Delhi
    print(f"Birth DateTime (UTC): {birth_dt_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Location            : Lat {lat:.4f}, Lon {lon:.4f}\n")

    # 2. Initialize Engines
    ephem = EphemerisWrapper(ephemeris_path="data/ephemeris")
    bhava_engine = VishamabhavaEngine(ephemeris_wrapper=ephem)
    sc_engine = SudarshanaChakraEngine(ephemeris_wrapper=ephem)
    div_engine = DivisionalSynthesisEngine(ephemeris_wrapper=ephem)
    vpc_engine = VPCEngine(ephemeris_wrapper=ephem)
    dasha_engine = DashaEngine(ephemeris_wrapper=ephem)
    upagraha_engine = UpagrahaEngine(ephemeris_wrapper=ephem)
    tphalit_engine = TPhalitCoreEngine(ephemeris_wrapper=ephem)

    # ── A. D1 Vishamabhava Bhaavachalita ──────────────────────────────────────
    chart = bhava_engine.compute_bhavachalita(birth_datetime=birth_dt_utc, latitude=lat, longitude=lon)
    print("-" * 80)

    print(f"1. D1 VISHAMABHAVA BHAAVACHALITA (Lagna-Madhya: {chart.lagna_madhya:.2f} deg, Madhya-Lagna: {chart.madhya_lagna:.2f} deg)")
    print("-" * 80)

    print(f"Bhava-heena Planets: {list(chart.bhavaheena_planets) if chart.bhavaheena_planets else 'None'}")
    for h in chart.houses:
        sec = f", Sec: {h.secondary_lord} ({h.secondary_rashi})" if h.secondary_lord else ""
        print(f"  House {h.house_number:2d}: {h.start_sandhi:6.2f} deg -> [{h.madhya:6.2f} deg {h.primary_lord} ({h.primary_rashi})] -> {h.end_sandhi:6.2f} deg (Span: {h.total_span_deg:.2f} deg{sec})")

    # ── B. Tri-Lagna Sudarshana Chakra (SC) ───────────────────────────────────
    b_ephem = ephem.calculate(dt=birth_dt_utc, latitude=lat, longitude=lon)
    sun_p = next(p for p in b_ephem.planet_positions if p.planet.lower() == "sun")
    moon_p = next(p for p in b_ephem.planet_positions if p.planet.lower() == "moon")

    sc_rep = sc_engine.analyze(
        lagna_deg=chart.lagna_madhya,
        sun_deg=sun_p.sidereal_longitude,
        moon_deg=moon_p.sidereal_longitude,
    )
    print("\n" + "-" * 80)

    print(f"2. TRI-LAGNA SUDARSHANA CHAKRA (LK: {sc_rep.lagna_rashi}, SK: {sc_rep.sun_rashi}, CK: {sc_rep.moon_rashi})")
    print(f"Tri-Lagna Active: {sc_rep.is_tri_lagna_active} (Sun/Moon in Lagna: {sc_rep.sun_in_lagna or sc_rep.moon_in_lagna})")
    print("-" * 80)

    for p_name, prof in sc_rep.profiles.items():
        pol = "Benefic (+)" if prof.is_functional_benefic else ("Malefic (-)" if prof.is_functional_malefic else "Neutral (0)")
        print(f"  {p_name:7s} | LK: {prof.lk_houses_owned} (Score: {prof.lk_functional_score:+d}) | SK: {prof.sk_houses_owned} (Score: {prof.sk_functional_score:+d}) | CK: {prof.ck_houses_owned} (Score: {prof.ck_functional_score:+d}) | Net: {prof.net_functional_score:+d} [{pol}]")

    # ── C. Divisional Synthesis: D10 (Karma) & D24 (Vidya) ────────────────────
    print("\n" + "-" * 80)

    print("3. DIVISIONAL SYNTHESIS & VIMSHOPAKA BALA (D1 vs D10 Career vs D24 Vidya)")
    print("-" * 80)

    for p in b_ephem.planet_positions:
        if p.planet.lower() in ["rahu", "ketu"]:
            continue
        d10_rep = div_engine.synthesize_d1_vs_divisional(
            planet=p.planet,
            sidereal_lon=p.sidereal_longitude,
            target_varga=10,
            scheme=VimshopakaScheme.DASHAVARGA,
        )
        print(f"  {p.planet.capitalize():7s} -> D1 ({d10_rep.d1_strength.dignity_label:11s}, S_eff={d10_rep.d1_strength.effective_strength:4.1f}) vs D10 ({d10_rep.divisional_strength.dignity_label:11s}, S_eff={d10_rep.divisional_strength.effective_strength:4.1f}) | Verdict: {d10_rep.verdict.value}")

    # ── D. VPC Solar Returns & SCD Progression (2024 - 2027) ──────────────────
    print("\n" + "-" * 80)

    print("4. VPC SOLAR RETURNS & SCD ANNUAL PROGRESSED HOUSES (2024 - 2027)")
    print("-" * 80)

    for yr in [2024, 2025, 2026, 2027]:
        vpc = vpc_engine.compute_vpc(
            birth_datetime_utc=birth_dt_utc,
            target_year=yr,
            latitude=lat,
            longitude=lon,
        )
        print(f"  Year {yr} (Age {vpc.completed_years}) | Solar Return UTC: {vpc.vpc_datetime_utc.strftime('%Y-%m-%d %H:%M:%S')} | SCD House: H{vpc.scd_annual_house}")
        print(f"    Month 1 (H{vpc.monthly_scd_entries[0].scd_house}): {vpc.monthly_scd_entries[0].entry_datetime_utc.strftime('%Y-%m-%d')} | Month 4 (H{vpc.monthly_scd_entries[3].scd_house}): {vpc.monthly_scd_entries[3].entry_datetime_utc.strftime('%Y-%m-%d')} | Month 7 (H{vpc.monthly_scd_entries[6].scd_house}): {vpc.monthly_scd_entries[6].entry_datetime_utc.strftime('%Y-%m-%d')}")

    # ── E. Active Vimshottari Dashas (2024 - 2027) ────────────────────────────
    dasha_tree = dasha_engine.compute_vimshottari(
        birth_datetime_utc=birth_dt_utc,
        latitude=lat,
        longitude=lon,
        max_depth=3,
    )
    print("\n" + "-" * 80)

    print("5. CURRENT & UPCOMING VIMSHOTTARI DASHAS (Level 1 MD / Level 2 AD / Level 3 PD)")
    print("-" * 80)

    eval_start = datetime(2024, 1, 1).date()
    eval_end = datetime(2027, 12, 31).date()

    for md in dasha_tree.mahadashas:
        if md.end_date < eval_start or md.start_date > eval_end:
            continue
        for ad in md.sub_periods:
            if ad.end_date < eval_start or ad.start_date > eval_end:
                continue
            for pd in ad.sub_periods:
                if pd.end_date < eval_start or pd.start_date > eval_end:
                    continue
                print(f"  {pd.start_date.strftime('%Y-%m-%d')} -> {pd.end_date.strftime('%Y-%m-%d')} | MD: {md.lord.capitalize():7s} | AD: {ad.lord.capitalize():7s} | PD: {pd.lord.capitalize():7s}")

    # ── F. TPhalitCore Feature Vector Extraction ──────────────────────────────
    fv = tphalit_engine.extract_features(
        birth_datetime_utc=birth_dt_utc,
        latitude=lat,
        longitude=lon,
        topic_id=1,
    )
    print("\n" + "-" * 80)

    print("6. TPHALITCORE SIGNED NUMERICAL FEATURE STATE")
    print("-" * 80)

    print(f"Deterministic Score: {fv.DeterministicScore:+.4f}")
    print("Block Totals:")
    for b_name, b_val in fv.BlockTotals.items():
        print(f"  * {b_name:15s}: {b_val:+.4f}")


    print("\n" + "=" * 80)
    print(">>> CANONICAL SHASTRIC SYNTHESIS COMPLETED SUCCESSFULLY <<<")
    print("=" * 80)


if __name__ == "__main__":
    run_raj_synthesis()
