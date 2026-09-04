"""
AstroOS — COHORT-v3.0 Tripartite Replication Benchmark Suite
============================================================
Evaluates n = 400 verified marriage events (Events 521 to 920, AA/A Rodden-rated)
along with symmetric within-subject negative controls (Offsets: [-6, -3, +3, +6] years).
Total Evaluated Sample: N ≈ 2,000 Windows.

Pre-Registered Invariants:
1. Zero Data Leakage: Skip first 520 events (Events 1-120: Cohort 1; Events 121-520: Cohort 2).
2. Confirmatory Single Hypothesis: Goodness-of-fit Chi2 across 9 planetary Mahadashas.
3. All 9 planets reported verbatim (Empirical Lift vs Controls + Theoretical Lift vs Years/120).
"""

import csv
import math
import sys
from pathlib import Path
from datetime import datetime, date, timezone
from typing import List, Dict, Any, Tuple
from collections import defaultdict

REPO_ROOT = Path("c:/Users/rkmau/Downloads/ReplitplusClaude/AstroOS")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.karyesha_engine import KaryeshaEngine, DomainEnum
from apps.api.services.dataset_hygiene_v1 import parse_date_flex


def safe_year_offset(d: date, offset: int) -> date:
    try:
        return d.replace(year=d.year + offset)
    except ValueError:
        return d.replace(year=d.year + offset, day=28)


def run_v30_benchmark(skip_n: int = 520, target_n: int = 400):
    wrapper = EphemerisWrapper(ephemeris_path=str(REPO_ROOT / "data/ephemeris"))
    dasha_engine = DashaEngine(wrapper)
    karyesha_engine = KaryeshaEngine(wrapper)

    pristine_csv_path = REPO_ROOT / "data/shastric_rules/kundalee_pristine_full.csv"

    pos_records: List[Dict[str, Any]] = []
    neg_records: List[Dict[str, Any]] = []

    md_distribution_pos = defaultdict(int)
    md_distribution_neg = defaultdict(int)

    seen_event_count = 0
    collected_pos_count = 0

    with pristine_csv_path.open("r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if collected_pos_count >= target_n:
                break

            gender = row.get("gender", "Male")
            rodden = row.get("rodden_rating", "").strip()
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
                ev_type = row.get(f"event_{ev_num}_type", "").lower()
                ev_date_str = row.get(f"event_{ev_num}_date", "")

                if "marriage" in ev_type and ev_date_str:
                    e_date = parse_date_flex(ev_date_str)
                    if not e_date:
                        continue

                    age_years = (e_date - b_dt.date()).days / 365.25
                    if age_years < 18.0 or age_years > 65.0:
                        continue

                    seen_event_count += 1
                    # INVARIANT 1: Skip first 520 events (Cohorts 1 & 2)
                    if seen_event_count <= skip_n:
                        continue

                    try:
                        dtree = dasha_engine.compute_vimshottari(
                            birth_datetime_utc=b_dt, latitude=lat, longitude=lon, ayanamsa="lahiri", max_depth=2
                        )
                    except Exception:
                        continue

                    target_md = None
                    for md in dtree.mahadashas:
                        if md.contains(e_date):
                            target_md = md
                            break

                    if not target_md:
                        continue

                    collected_pos_count += 1
                    md_lord = target_md.lord.lower()
                    md_distribution_pos[md_lord] += 1

                    pos_records.append({
                        "subject_id": row.get("name", f"subj_{collected_pos_count}"),
                        "age": age_years,
                        "md_lord": md_lord,
                    })

                    # INVARIANT 2: Symmetric Control Offsets [-6, -3, +3, +6]
                    offsets_years = [-6, -3, 3, 6]
                    for offset in offsets_years:
                        ctrl_date = safe_year_offset(e_date, offset)
                        ctrl_age = (ctrl_date - b_dt.date()).days / 365.25
                        if ctrl_age < 18.0 or ctrl_age > 65.0:
                            continue

                        ctrl_md_lord = None
                        for md in dtree.mahadashas:
                            if md.contains(ctrl_date):
                                ctrl_md_lord = md.lord.lower()
                                break

                        if not ctrl_md_lord:
                            continue

                        md_distribution_neg[ctrl_md_lord] += 1
                        neg_records.append({
                            "subject_id": row.get("name", f"subj_{collected_pos_count}"),
                            "age": ctrl_age,
                            "md_lord": ctrl_md_lord,
                        })

                    break

    print("=" * 85)
    print(f"ASTROOS COHORT-v3.0 TRIPARTITE REPLICATION BENCHMARK (Events 521 to 920)")
    print(f"Sample: N_pos = {len(pos_records)} Marriages, N_neg = {len(neg_records)} Controls | Total = {len(pos_records) + len(neg_records)} Windows")
    print(f"Base Rate: {(len(pos_records)/(len(pos_records)+len(neg_records)))*100:.2f}% | Zero Leakage: Events 1-520 Skipped")
    print("=" * 85)

    print("\n### MAHADASHA (MD) DISTRIBUTION REPLICATION (COHORT 3 VERBATIM)")
    print("| MD Planet | Positive Hits (n=400) | % Pos | Control Hits (n=1447) | % Neg | Empirical Lift | Theoretical Lift (Years/120) |")
    print("|---|---|---|---|---|---|---|")

    DASHA_YEARS = {"sun": 6, "moon": 10, "mars": 7, "rahu": 18, "jupiter": 16, "saturn": 19, "mercury": 17, "ketu": 7, "venus": 20}
    all_planets = ["sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury", "ketu", "venus"]

    chi2_theoretical = 0.0
    for p in all_planets:
        p_hits = md_distribution_pos[p]
        n_hits = md_distribution_neg[p]
        p_pct = (p_hits / len(pos_records)) * 100.0 if pos_records else 0.0
        n_pct = (n_hits / len(neg_records)) * 100.0 if neg_records else 0.0
        emp_lift = (p_pct / n_pct) if n_pct > 0 else 0.0

        theo_pct = (DASHA_YEARS[p] / 120.0) * 100.0
        theo_lift = (p_pct / theo_pct) if theo_pct > 0 else 0.0

        expected_count = len(pos_records) * (DASHA_YEARS[p] / 120.0)
        chi2_theoretical += ((p_hits - expected_count) ** 2) / expected_count

        print(f"| **{p.capitalize()}** | {p_hits}/{len(pos_records)} | {p_pct:.1f}% | {n_hits}/{len(neg_records)} | {n_pct:.1f}% | **{emp_lift:.2f}x** | **{theo_lift:.2f}x** |")

    print(f"\nGoodness-of-Fit vs Theoretical Vimshottari: Chi2 = {chi2_theoretical:.2f} (df=8, critical at p=0.05 is 15.51, at p=0.01 is 20.09)")
    if chi2_theoretical >= 20.09:
        print("CONFIRMATORY OUTCOME: p < 0.01 (Statistically Significant across 3rd Independent Cohort)")
    elif chi2_theoretical >= 15.51:
        print("CONFIRMATORY OUTCOME: p < 0.05 (Statistically Significant across 3rd Independent Cohort)")
    else:
        print("CONFIRMATORY OUTCOME: p >= 0.05 (Non-Significant on 3rd Independent Cohort)")


if __name__ == "__main__":
    run_v30_benchmark(skip_n=520, target_n=400)
