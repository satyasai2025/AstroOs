"""
AstroOS — STUDY-MARRIAGE-DASHA-LORD-FREQ-v0.2 (Large Cohort Expansion)
========================================================================
Executes pre-registered marriage dasha frequency study across n >= 100 verified
human charts from kundalee_pristine_full.csv using Swiss Ephemeris + DashaEngine.

Hypotheses Tested:
1. H1: Venus and Jupiter show statistically significant positive lift in AD (Bonferroni alpha = 0.0055).
2. H2: Sun MD marriages exist and exhibit the Abboud Pattern (AD Karyesha activation).
3. H3: AD distribution shows higher chi-square divergence from chance than MD.
"""

import csv
import json
import math
import sys
from pathlib import Path
from datetime import datetime, date
from collections import Counter
from typing import List, Dict, Any, Tuple

# Bootstrap repo root to sys.path
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.dataset_hygiene_v1 import parse_date_flex

def chi_square_goodness_of_fit(observed: Dict[str, int], expected: Dict[str, float]) -> Tuple[float, int]:
    stat = 0.0
    k = len(expected)
    for p, exp in expected.items():
        obs = observed.get(p, 0)
        if exp > 0:
            stat += ((obs - exp) ** 2) / exp
    return stat, k - 1

def run_v02_study(target_n: int = 150):
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    dasha_engine = DashaEngine(wrapper)

    pristine_csv_path = Path("data/shastric_rules/kundalee_pristine_full.csv")
    if not pristine_csv_path.exists():
        print(f"Error: missing {pristine_csv_path}")
        return

    marriage_records: List[Dict[str, Any]] = []

    with pristine_csv_path.open("r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if len(marriage_records) >= target_n:
                break

            gender = row.get("gender", "")
            if gender not in ("Male", "Female", "M", "F"):
                continue

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

            # Check events for Marriage
            for ev_num in (1, 2, 3):
                ev_type = row.get(f"event_{ev_num}_type", "")
                ev_date_str = row.get(f"event_{ev_num}_date", "")
                if ev_type.lower() == "marriage" and ev_date_str:
                    e_date = parse_date_flex(ev_date_str)
                    if not e_date:
                        continue

                    # Calculate age at marriage
                    age_years = (e_date - b_dt.date()).days / 365.25
                    if age_years < 15.0 or age_years > 75.0:
                        continue

                    # Compute Dasha
                    try:
                        dasha_tree = dasha_engine.compute_vimshottari(
                            birth_datetime_utc=b_dt,
                            latitude=lat,
                            longitude=lon,
                            ayanamsa="lahiri",
                            max_depth=2
                        )
                    except Exception:
                        continue

                    md_lord = "Unknown"
                    ad_lord = "Unknown"

                    for md in dasha_tree.mahadashas:
                        if md.contains(e_date):
                            md_lord = md.lord.capitalize()
                            for ad in md.sub_periods:
                                if ad.contains(e_date):
                                    ad_lord = ad.lord.capitalize()
                                    break
                            break

                    marriage_records.append({
                        "name": row.get("name", ""),
                        "gender": gender,
                        "dob": str(b_dt.date()),
                        "marriage_date": str(e_date),
                        "age_years": round(age_years, 1),
                        "md_lord": md_lord,
                        "ad_lord": ad_lord,
                        "rodden": rodden,
                    })
                    break  # One marriage event per subject for independence

    n = len(marriage_records)
    print(f"=== STUDY-MARRIAGE-DASHA-LORD-FREQ-v0.2 (COHORT SIZE: n = {n}) ===")

    dasha_weights = {
        "Venus": 20/120, "Jupiter": 16/120, "Saturn": 19/120, "Rahu": 18/120,
        "Mercury": 17/120, "Moon": 10/120, "Mars": 7/120, "Ketu": 7/120, "Sun": 6/120
    }

    md_counts = Counter(r["md_lord"] for r in marriage_records)
    ad_counts = Counter(r["ad_lord"] for r in marriage_records)

    expected_md = {p: n * wt for p, wt in dasha_weights.items()}
    expected_ad = {p: n * wt for p, wt in dasha_weights.items()}

    chi2_md, df_md = chi_square_goodness_of_fit(md_counts, expected_md)
    chi2_ad, df_ad = chi_square_goodness_of_fit(ad_counts, expected_ad)

    print("\n### 1. Mahadasha (MD) Distribution vs Chance Expectation")
    print(f"| Planet | Duration | Chance % | Expected (n={n}) | Observed | Diff | Lift Ratio |")
    print("|---|---|---|---|---|---|---|")
    for p, wt in sorted(dasha_weights.items(), key=lambda x: -x[1]):
        exp = expected_md[p]
        obs = md_counts.get(p, 0)
        diff = obs - exp
        lift = obs / exp if exp > 0 else 0
        print(f"| **{p}** | {int(wt*120)}y | {wt:.1%} | {exp:.2f} | **{obs}** | {diff:+.2f} | {lift:.2f}x |")
    print(f"\n*MD Chi-Square Stat:* $\\chi^2 = {chi2_md:.2f}$ (df = {df_md})")

    print("\n### 2. Antardasha (AD) Distribution vs Chance Expectation")
    print(f"| Planet | Duration | Chance % | Expected (n={n}) | Observed | Diff | Lift Ratio |")
    print("|---|---|---|---|---|---|---|")
    for p, wt in sorted(dasha_weights.items(), key=lambda x: -x[1]):
        exp = expected_ad[p]
        obs = ad_counts.get(p, 0)
        diff = obs - exp
        lift = obs / exp if exp > 0 else 0
        print(f"| **{p}** | {int(wt*120)}y | {wt:.1%} | {exp:.2f} | **{obs}** | {diff:+.2f} | {lift:.2f}x |")
    print(f"\n*AD Chi-Square Stat:* $\\chi^2 = {chi2_ad:.2f}$ (df = {df_ad})")

    # Abboud Pattern Check (Sun MD cases and their AD lords)
    sun_md_cases = [r for r in marriage_records if r["md_lord"] == "Sun"]
    print(f"\n### 3. Sun Mahadasha Marriage Cases (n = {len(sun_md_cases)} out of {n})")
    print("| Subject | DOB | Marriage Date | Age | MD Lord | AD Lord |")
    print("|---|---|---|---|---|---|")
    for r in sun_md_cases:
        print(f"| {r['name']} | {r['dob']} | {r['marriage_date']} | {r['age_years']} | **{r['md_lord']}** | **{r['ad_lord']}** |")

if __name__ == "__main__":
    from typing import Tuple
    run_v02_study(target_n=120)
