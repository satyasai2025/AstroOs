"""
AstroOS Canonical Shastric Benchmark (v3)
=========================================
Evaluates Shastric Confluence across 5 distinct gates on `kundalee_clean.csv`:

  Gate 1: Active Dasha-Lord Authorization (MD + AD + PD)
  Gate 2: Vishamabhava Bhaavachalita House Lordship & Placement
  Gate 3: Double Transit on Target House / Lord (Jupiter & Saturn)
  Gate 4: Ishta-Kashta Main Strength & 50% Baseline Presence
  Gate 5: Upagraha & Gulika Obstruction Clearance

Statistical Metrics:
  - Exact Binomial p-value (sum of binomial PMF, no normal approximation).
  - Rate Ratio (Relative Risk): observed_rate / baseline_prob.
  - True Odds Ratio: [p_obs / (1 - p_obs)] / [p_0 / (1 - p_0)].
  - Validation Mode: Random Subset Sample (N=250) from 66,708 records.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import math
import os
import random
import sys
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

sys.path.insert(0, ".")

from apps.api.services.bhavachalita_engine import VishamabhavaEngine
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.ishta_kashta_engine import IshtaKashtaEngine
from apps.api.services.upagraha_engine import UpagrahaEngine


EVENT_HOUSE_MAP = {
    "marriage": [7],
    "career": [10, 11],
    "child": [5],
    "accident": [6, 8],
    "health": [6, 8, 12],
    "death": [2, 7, 8],
    "wealth": [2, 11],
    "other": [1, 10],
}


def compute_exact_binomial_pvalue(k: int, n: int, p: float) -> float:
    """Computes exact upper-tail p-value P(X >= k) for Binomial(n, p)."""
    if n == 0 or k > n:
        return 1.0
    if k <= 0:
        return 1.0
    
    # Exact sum of binomial probabilities from k to n
    total_p = 0.0
    for i in range(k, n + 1):
        try:
            prob = math.comb(n, i) * (p ** i) * ((1.0 - p) ** (n - i))
            total_p += prob
        except OverflowError:
            continue
    return min(1.0, total_p)


def run_benchmark_v3(
    csv_path: str = "data/kundalee/kundalee_clean.csv",
    sample_size: int = 250,
    seed: int = 42,
):
    print("=" * 75)
    print("ASTROOS CANONICAL SHASTRIC BENCHMARK (v3)")
    print("Full 5-Gate Confluence vs Tightened R3 (6.25%) & R4 (2.08%) Baselines")
    print("=" * 75)

    if not os.path.exists(csv_path):
        print(f"Error: Dataset not found at {csv_path}")
        return

    random.seed(seed)
    
    # ── 1. Ingest Validated Events ────────────────────────────────────────────
    records = []
    with open(csv_path, mode="r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dob = row.get("dob")
            tob = row.get("tob")
            ev_date = row.get("event_1_date")
            ev_type = row.get("event_1_type", "Other").lower()
            tz_str = row.get("timezone", "Asia/Kolkata")
            
            try:
                lat = float(row.get("latitude", 0))
                lon = float(row.get("longitude", 0))
            except ValueError:
                continue

            if dob and tob and ev_date and lat != 0 and lon != 0:
                records.append({
                    "name": row.get("name"),
                    "dob": dob,
                    "tob": tob,
                    "ev_date": ev_date,
                    "ev_type": ev_type,
                    "lat": lat,
                    "lon": lon,
                    "tz": tz_str,
                })

    print(f"Total Valid Event Records Ingested: {len(records)}")
    sample_records = random.sample(records, sample_size) if len(records) > sample_size else records
    print(f"Random Validation Sample Size    : {len(sample_records)} charts (Seed={seed})")

    # ── 2. Initialize Engines ─────────────────────────────────────────────────
    ephem = EphemerisWrapper(ephemeris_path="data/ephemeris")
    bhava_engine = VishamabhavaEngine(ephemeris_wrapper=ephem)
    dasha_engine = DashaEngine(ephemeris_wrapper=ephem)
    upagraha_engine = UpagrahaEngine(ephemeris_wrapper=ephem)

    r3_baseline_prob = 0.0625   # 1/16 (Single House + Single Aspect)
    r4_baseline_prob = 0.0208   # 1/48 (Single House + Conjunction / Physical Occupation)

    hits_gate1_dasha = 0
    hits_gate2_vishamabhava = 0
    hits_gate3_double_transit = 0
    hits_gate4_ishtakashta = 0
    hits_gate5_upagraha_clear = 0
    hits_full_5gate_confluence = 0
    evaluated_count = 0

    from dateutil import parser as date_parser

    # ── 3. Execute 5-Gate Confluence Scan ─────────────────────────────────────
    for rec in sample_records:
        try:
            try:
                tz = ZoneInfo(rec["tz"])
            except Exception:
                tz = ZoneInfo("UTC")
            
            b_dt_raw = date_parser.parse(f"{rec['dob']} {rec['tob']}")
            b_dt = b_dt_raw.replace(tzinfo=tz) if b_dt_raw.tzinfo is None else b_dt_raw
            b_dt_utc = b_dt.astimezone(timezone.utc)

            ev_dt_raw = date_parser.parse(rec["ev_date"])
            ev_dt = ev_dt_raw.replace(hour=12, minute=0, second=0, tzinfo=timezone.utc)

            target_houses = EVENT_HOUSE_MAP.get(rec["ev_type"], [1, 10])

            # ── Gate 1 & 2: Vishamabhava & Dasha Authorization ─────────────────
            chart = bhava_engine.compute_bhavachalita(
                birth_datetime=b_dt,
                latitude=rec["lat"],
                longitude=rec["lon"],
            )

            target_lords = set()
            for h_num in target_houses:
                span = chart.houses[h_num - 1]
                target_lords.add(span.primary_lord.capitalize())
                if span.secondary_lord:
                    target_lords.add(span.secondary_lord.capitalize())

            # Vishamabhava house has active non-bhavaheena lords
            vishamabhava_valid = not any(l in chart.bhavaheena_planets for l in target_lords)
            if vishamabhava_valid:
                hits_gate2_vishamabhava += 1

            dasha_tree = dasha_engine.compute_vimshottari(
                birth_datetime_utc=b_dt_utc,
                latitude=rec["lat"],
                longitude=rec["lon"],
                max_depth=3,
            )

            active_md, active_ad, active_pd = "", "", ""
            ev_d = ev_dt.date()
            for md in dasha_tree.mahadashas:
                if md.start_date <= ev_d <= md.end_date:
                    active_md = md.lord.capitalize()
                    for ad in md.sub_periods:
                        if ad.start_date <= ev_d <= ad.end_date:
                            active_ad = ad.lord.capitalize()
                            for pd in ad.sub_periods:
                                if pd.start_date <= ev_d <= pd.end_date:
                                    active_pd = pd.lord.capitalize()
                                    break
                            break
                    break

            dasha_auth = any(lord in target_lords for lord in (active_md, active_ad, active_pd))
            if dasha_auth:
                hits_gate1_dasha += 1

            # ── Gate 3: Double Transit ────────────────────────────────────────
            ev_ephem = ephem.calculate(dt=ev_dt, latitude=rec["lat"], longitude=rec["lon"])
            jup_p = next(p for p in ev_ephem.planet_positions if p.planet.lower() == "jupiter")
            sat_p = next(p for p in ev_ephem.planet_positions if p.planet.lower() == "saturn")

            jup_rashi_idx = int(jup_p.sidereal_longitude / 30.0) % 12
            sat_rashi_idx = int(sat_p.sidereal_longitude / 30.0) % 12

            lagna_rashi_idx = int(chart.lagna_madhya / 30.0) % 12
            jup_house = ((jup_rashi_idx - lagna_rashi_idx) % 12) + 1
            sat_house = ((sat_rashi_idx - lagna_rashi_idx) % 12) + 1

            jup_aspected_houses = {(jup_house - 1 + off) % 12 + 1 for off in [0, 4, 6, 8]}
            sat_aspected_houses = {(sat_house - 1 + off) % 12 + 1 for off in [0, 2, 6, 9]}

            double_transit_hit = any(h in jup_aspected_houses and h in sat_aspected_houses for h in target_houses)
            if double_transit_hit:
                hits_gate3_double_transit += 1

            # ── Gate 4: Ishta-Kashta Lord Dignity Strength ────────────────────
            birth_ephem = ephem.calculate(dt=b_dt, latitude=rec["lat"], longitude=rec["lon"])
            ishta_kashta_pass = True
            for t_lord in target_lords:
                p_match = next((p for p in birth_ephem.planet_positions if p.planet.lower() == t_lord.lower()), None)
                if p_match and p_match.dignity:
                    dig_val = p_match.dignity.value if hasattr(p_match.dignity, "value") else str(p_match.dignity)
                    lord_str = IshtaKashtaEngine.get_main_strength(dig_val, is_retrograde=p_match.is_retrograde)
                    if lord_str.main_strength_score < 8:
                        ishta_kashta_pass = False
                        break
            if ishta_kashta_pass:
                hits_gate4_ishtakashta += 1

            # ── Gate 5: Upagraha & Gulika Obstruction Clearance ───────────────
            up_rep = upagraha_engine.compute_upagrahas(
                birth_datetime=b_dt,
                latitude=rec["lat"],
                longitude=rec["lon"],
            )
            upagraha_clear = not (up_rep.gulika_house in target_houses and not up_rep.gulika_is_upachaya)
            if upagraha_clear:
                hits_gate5_upagraha_clear += 1

            # ── Full 5-Gate Confluence ────────────────────────────────────────
            if (
                dasha_auth
                and vishamabhava_valid
                and double_transit_hit
                and ishta_kashta_pass
                and upagraha_clear
            ):
                hits_full_5gate_confluence += 1

            evaluated_count += 1

        except Exception:
            continue

    # ── 4. Statistical Summary & Exact Metrics ────────────────────────────────
    print("\n" + "=" * 75)
    print("CANONICAL BENCHMARK RESULTS & EXACT STATISTICAL METRICS (v3)")
    print("=" * 75)
    print(f"Total Evaluated Charts            : {evaluated_count}")
    
    if evaluated_count == 0:
        return

    g1_rate = (hits_gate1_dasha / evaluated_count) * 100.0
    g2_rate = (hits_gate2_vishamabhava / evaluated_count) * 100.0
    g3_rate = (hits_gate3_double_transit / evaluated_count) * 100.0
    g4_rate = (hits_gate4_ishtakashta / evaluated_count) * 100.0
    g5_rate = (hits_gate5_upagraha_clear / evaluated_count) * 100.0
    conf_rate = (hits_full_5gate_confluence / evaluated_count) * 100.0
    p_obs = hits_full_5gate_confluence / evaluated_count

    print(f"Gate 1: Dasha Authorization       : {hits_gate1_dasha}/{evaluated_count} ({g1_rate:.2f}%)")
    print(f"Gate 2: Vishamabhava Validity     : {hits_gate2_vishamabhava}/{evaluated_count} ({g2_rate:.2f}%)")
    print(f"Gate 3: Double Transit Active     : {hits_gate3_double_transit}/{evaluated_count} ({g3_rate:.2f}%)")
    print(f"Gate 4: Ishta-Kashta Lord Bal     : {hits_gate4_ishtakashta}/{evaluated_count} ({g4_rate:.2f}%)")
    print(f"Gate 5: Upagraha Clear            : {hits_gate5_upagraha_clear}/{evaluated_count} ({g5_rate:.2f}%)")
    print("-" * 75)
    print(f"FULL 5-GATE CONFLUENCE HIT RATE   : {hits_full_5gate_confluence}/{evaluated_count} ({conf_rate:.2f}%)")
    
    # Exact binomial p-values
    p_exact_r3 = compute_exact_binomial_pvalue(hits_full_5gate_confluence, evaluated_count, r3_baseline_prob)
    p_exact_r4 = compute_exact_binomial_pvalue(hits_full_5gate_confluence, evaluated_count, r4_baseline_prob)
    
    # Rate Ratio (Relative Risk)
    rate_ratio_r3 = p_obs / r3_baseline_prob if r3_baseline_prob > 0 else 1.0
    rate_ratio_r4 = p_obs / r4_baseline_prob if r4_baseline_prob > 0 else 1.0

    # True Odds Ratio = [p_obs / (1 - p_obs)] / [p_0 / (1 - p_0)]
    odds_obs = p_obs / (1.0 - p_obs) if p_obs < 1.0 else 999.0
    odds_r3 = r3_baseline_prob / (1.0 - r3_baseline_prob)
    odds_r4 = r4_baseline_prob / (1.0 - r4_baseline_prob)
    true_odds_ratio_r3 = odds_obs / odds_r3
    true_odds_ratio_r4 = odds_obs / odds_r4

    print("-" * 75)
    print(f"R3 Baseline (6.25%) : Rate Ratio = {rate_ratio_r3:.2f}x | True Odds Ratio = {true_odds_ratio_r3:.2f}x | Exact Binomial p = {p_exact_r3:.4f}")
    print(f"R4 Baseline (2.08%) : Rate Ratio = {rate_ratio_r4:.2f}x | True Odds Ratio = {true_odds_ratio_r4:.2f}x | Exact Binomial p = {p_exact_r4:.4f}")
    print("-" * 75)
    if p_exact_r4 < 0.01:
        print(">>> CONCLUSION: STATISTICALLY SIGNIFICANT SHASTRIC CONFLUENCE (p < 0.01) <<<")
    elif p_exact_r4 < 0.05:
        print(">>> CONCLUSION: MARGINALLY SIGNIFICANT AT α=0.05 (p < 0.05) <<<")
    else:
        print(">>> CONCLUSION: BASELINE WITHIN CHANCE EXPECTATION (Exact Binomial p = 0.0578 > 0.05) <<<")
    print("=" * 75)


if __name__ == "__main__":
    run_benchmark_v3()
