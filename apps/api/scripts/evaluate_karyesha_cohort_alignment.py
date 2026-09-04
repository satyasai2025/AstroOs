"""
AstroOS — Karyesha Alignment Cohort Benchmark
=============================================
Evaluates Karyesha activation rates across n = 120 verified marriage nativities.
"""

import csv
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.karyesha_engine import KaryeshaEngine, DomainEnum
from apps.api.services.dataset_hygiene_v1 import parse_date_flex

def run_karyesha_benchmark(target_n: int = 120):
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    dasha_engine = DashaEngine(wrapper)
    karyesha_engine = KaryeshaEngine(wrapper)

    pristine_csv_path = Path("data/shastric_rules/kundalee_pristine_full.csv")

    evaluated_cases = []
    active_karyesha_count = 0
    high_confluence_count = 0
    reasonable_confluence_count = 0
    sun_md_active_karyesha_count = 0
    sun_md_total = 0

    with pristine_csv_path.open("r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if len(evaluated_cases) >= target_n:
                break

            gender = row.get("gender", "Male")
            rodden = row.get("rodden_rating", "")
            if rodden not in ("AA", "A"):
                continue

            b_dt_str = row.get("birth_dt_utc", "")
            if not b_dt_str:
                continue

            try:
                b_dt = datetime.fromisoformat(b_dt_str)
                lat = float(row.get("latitude", 0.0))
                lon = float(row.get("longitude", 0.0))
            except Exception:
                continue

            for ev_num in (1, 2, 3):
                ev_type = row.get(f"event_{ev_num}_type", "")
                ev_date_str = row.get(f"event_{ev_num}_date", "")
                if ev_type.lower() == "marriage" and ev_date_str:
                    e_date = parse_date_flex(ev_date_str)
                    if not e_date:
                        continue

                    age_years = (e_date - b_dt.date()).days / 365.25
                    if age_years < 15.0 or age_years > 75.0:
                        continue

                    try:
                        dtree = dasha_engine.compute_vimshottari(
                            birth_datetime_utc=b_dt, latitude=lat, longitude=lon, ayanamsa="lahiri", max_depth=2
                        )
                    except Exception:
                        continue

                    md_lord = "Unknown"
                    ad_lord = "Unknown"
                    for md in dtree.mahadashas:
                        if md.contains(e_date):
                            md_lord = md.lord.capitalize()
                            for ad in md.sub_periods:
                                if ad.contains(e_date):
                                    ad_lord = ad.lord.capitalize()
                                    break
                            break

                    eval_res = karyesha_engine.evaluate_dasha_timing(
                        birth_datetime_utc=b_dt,
                        latitude=lat,
                        longitude=lon,
                        event_date=e_date,
                        md_lord=md_lord,
                        ad_lord=ad_lord,
                        domain=DomainEnum.MARRIAGE,
                        gender=gender,
                    )

                    if eval_res.is_karyesha_active:
                        active_karyesha_count += 1
                    if eval_res.gating_verdict == "HIGH":
                        high_confluence_count += 1
                    elif eval_res.gating_verdict == "REASONABLE":
                        reasonable_confluence_count += 1

                    if md_lord.lower() == "sun":
                        sun_md_total += 1
                        if eval_res.is_karyesha_active:
                            sun_md_active_karyesha_count += 1

                    evaluated_cases.append({
                        "name": row.get("name", ""),
                        "dob": str(b_dt.date()),
                        "marriage_date": str(e_date),
                        "md": md_lord,
                        "ad": ad_lord,
                        "ad_karyesha_score": eval_res.ad_karyesha_score,
                        "verdict": eval_res.gating_verdict,
                        "reasons": eval_res.explanation,
                    })
                    break

    n = len(evaluated_cases)
    hit_rate = (active_karyesha_count / n) * 100 if n > 0 else 0
    sun_hit_rate = (sun_md_active_karyesha_count / sun_md_total) * 100 if sun_md_total > 0 else 0

    print(f"=== KARYESHA ENGINE BENCHMARK RESULTS (n = {n}) ===")
    print(f"Total Marriage Events Evaluated:       {n}")
    print(f"Karyesha-Active Marriage Slices:       {active_karyesha_count} / {n} ({hit_rate:.1f}%)")
    print(f"  - High Confluence Verdicts:          {high_confluence_count} ({high_confluence_count/n:.1%})")
    print(f"  - Reasonable Confluence Verdicts:    {reasonable_confluence_count} ({reasonable_confluence_count/n:.1%})")
    print(f"Sun Mahadasha Karyesha Alignment:      {sun_md_active_karyesha_count} / {sun_md_total} ({sun_hit_rate:.1f}%)\n")

    print("Sample Individual Nativities & Karyesha Evidence:")
    print("| # | Subject | DOB | Marriage | MD | AD | AD Score | Verdict |")
    print("|---|---|---|---|---|---|---|---|")
    for i, c in enumerate(evaluated_cases[:10], start=1):
        print(f"| {i} | {c['name']} | {c['dob']} | {c['marriage_date']} | {c['md']} | {c['ad']} | {c['ad_karyesha_score']} | **{c['verdict']}** |")

if __name__ == "__main__":
    run_karyesha_benchmark(120)
