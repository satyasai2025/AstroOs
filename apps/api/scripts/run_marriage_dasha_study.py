"""
AstroOS — STUDY-MARRIAGE-DASHA-LORD-FREQ-v0.1 Execution Runner
==============================================================
Evaluates Mahadasha (MD) and Antardasha (AD) lord distributions at marriage dates
using the verified Swiss Ephemeris and Vimshottari Dasha Engine.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, date
from collections import Counter

# Add repository root to sys.path
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.dasha_engine import DashaEngine

def run_study():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    dasha_engine = DashaEngine(wrapper)

    pristine_json_path = Path("data/shastric_rules/kundalee_events_pristine_100kb.json")
    data = json.loads(pristine_json_path.read_text(encoding="utf-8"))

    marriage_records = []

    for subject in data:
        b_dt_str = subject["birth_dt_utc"]
        b_dt = datetime.fromisoformat(b_dt_str)
        lat = float(subject["lat"])
        lon = float(subject["lon"])
        
        for ev in subject.get("events", []):
            if ev.get("type") == "Marriage":
                ev_date_str = ev.get("date")
                try:
                    ev_date = date.fromisoformat(ev_date_str)
                except ValueError:
                    continue
                    
                # Compute Dasha Tree
                try:
                    dasha_tree = dasha_engine.compute_vimshottari(
                        birth_datetime_utc=b_dt,
                        latitude=lat,
                        longitude=lon,
                        ayanamsa="lahiri",
                        max_depth=2
                    )
                except Exception as e:
                    print(f"Error computing dasha for {subject['name']}: {e}")
                    continue
                    
                md_lord = "Unknown"
                ad_lord = "Unknown"
                
                for md in dasha_tree.mahadashas:
                    if md.contains(ev_date):
                        md_lord = md.lord.capitalize()
                        for ad in md.sub_periods:
                            if ad.contains(ev_date):
                                ad_lord = ad.lord.capitalize()
                                break
                        break
                        
                marriage_records.append({
                    "name": subject["name"],
                    "dob": subject["dob"],
                    "tob": subject["tob"],
                    "marriage_date": str(ev_date),
                    "age_years": ev.get("age_years", 0),
                    "md_lord": md_lord,
                    "ad_lord": ad_lord,
                    "source": subject.get("source", "")
                })

    print(f"=== STUDY-MARRIAGE-DASHA-LORD-FREQ-v0.1 RESULTS ===")
    print(f"Total Pre-Registered Marriage Events Analyzed: {len(marriage_records)}\n")

    print("| # | Subject | DOB | Marriage Date | Age | MD Lord | AD Lord |")
    print("|---|---|---|---|---|---|---|")
    for idx, r in enumerate(marriage_records, start=1):
        print(f"| {idx} | {r['name']} | {r['dob']} | {r['marriage_date']} | {r['age_years']} | **{r['md_lord']}** | **{r['ad_lord']}** |")

    md_counts = Counter(r["md_lord"] for r in marriage_records)
    ad_counts = Counter(r["ad_lord"] for r in marriage_records)

    dasha_weights = {
        "Venus": 20/120, "Jupiter": 16/120, "Mercury": 17/120, "Saturn": 19/120,
        "Rahu": 18/120, "Ketu": 7/120, "Sun": 6/120, "Moon": 10/120, "Mars": 7/120
    }

    n = len(marriage_records)
    print("\n### 1. Mahadasha (MD) Distribution vs Chance")
    print(f"| Planet | Duration | Chance % | Expected (n={n}) | Observed | Diff | Lift |")
    print("|---|---|---|---|---|---|---|")
    for p, wt in sorted(dasha_weights.items(), key=lambda x: -x[1]):
        exp = n * wt
        obs = md_counts.get(p, 0)
        diff = obs - exp
        lift = obs / exp if exp > 0 else 0
        print(f"| **{p}** | {int(wt*120)}y | {wt:.1%} | {exp:.2f} | **{obs}** | {diff:+.2f} | {lift:.2f}x |")

    print("\n### 2. Antardasha (AD) Distribution vs Chance")
    print(f"| Planet | Duration | Chance % | Expected (n={n}) | Observed | Diff | Lift |")
    print("|---|---|---|---|---|---|---|")
    for p, wt in sorted(dasha_weights.items(), key=lambda x: -x[1]):
        exp = n * wt
        obs = ad_counts.get(p, 0)
        diff = obs - exp
        lift = obs / exp if exp > 0 else 0
        print(f"| **{p}** | {int(wt*120)}y | {wt:.1%} | {exp:.2f} | **{obs}** | {diff:+.2f} | {lift:.2f}x |")

if __name__ == "__main__":
    run_study()
