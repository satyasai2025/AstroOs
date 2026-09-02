"""
AstroOS — Career Domain (Job Change / Awards / Promotion) Benchmark (v1.0)
==========================================================================
Evaluates Mahadasha distribution, Amatya Karaka (AmK), and 10th House Karyesha
timing across n = 120 verified Career events vs 5 within-subject control slices.
"""

import csv
import math
import sys
from pathlib import Path
from datetime import datetime, date, timezone
from typing import List, Dict, Any, Tuple
from collections import Counter

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.karyesha_engine import KaryeshaEngine, DomainEnum, RASHI_LORDS
from apps.api.services.dataset_hygiene_v1 import parse_date_flex


DASHA_YEARS = {
    "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17, "Ketu": 7
}
TOTAL_YEARS = 120.0
DASHA_PROBABILITIES = {k: v / TOTAL_YEARS for k, v in DASHA_YEARS.items()}


def compute_roc_auc(pos_scores: List[float], neg_scores: List[float]) -> float:
    n_pos = len(pos_scores)
    n_neg = len(neg_scores)
    if n_pos == 0 or n_neg == 0:
        return 0.5
    wins = 0.0
    for p in pos_scores:
        for n in neg_scores:
            if p > n:
                wins += 1.0
            elif p == n:
                wins += 0.5
    return wins / (n_pos * n_neg)


def run_career_benchmark(target_n: int = 120):
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    dasha_engine = DashaEngine(wrapper)
    karyesha_engine = KaryeshaEngine(wrapper)

    pristine_csv_path = Path("data/kundalee/kundalee_pristine_full.csv")

    career_events = []
    control_slices = []

    pos_scores = []
    neg_scores = []

    md_counts = Counter()
    ad_counts = Counter()

    amk_pos_hits = 0
    amk_neg_hits = 0
    tenth_lord_pos_hits = 0
    tenth_lord_neg_hits = 0

    career_types = {"job change", "awards", "promotion", "politics", "career"}

    with pristine_csv_path.open("r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if len(career_events) >= target_n:
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
                ev_type = row.get(f"event_{ev_num}_type", "").strip().lower()
                ev_date_str = row.get(f"event_{ev_num}_date", "")
                if ev_type in career_types and ev_date_str:
                    e_date = parse_date_flex(ev_date_str)
                    if not e_date:
                        continue

                    age_years = (e_date - b_dt.date()).days / 365.25
                    if age_years < 18.0 or age_years > 75.0:
                        continue

                    try:
                        dtree = dasha_engine.compute_vimshottari(
                            birth_datetime_utc=b_dt, latitude=lat, longitude=lon, ayanamsa="lahiri", max_depth=2
                        )
                        lagna_idx, planets_info, karakas = karyesha_engine.extract_chart_positions(b_dt, lat, lon)
                        profiles = karyesha_engine.analyze_domain_karyeshas(
                            lagna_idx, planets_info, karakas, domain=DomainEnum.CAREER, gender=gender
                        )
                    except Exception:
                        continue

                    target_md = None
                    target_ad = None
                    for md in dtree.mahadashas:
                        if md.contains(e_date):
                            target_md = md
                            for ad in md.sub_periods:
                                if ad.contains(e_date):
                                    target_ad = ad
                                    break
                            break

                    if not target_md or not target_ad:
                        continue

                    md_lord = target_md.lord.capitalize()
                    ad_lord = target_ad.lord.capitalize()

                    md_counts[md_lord] += 1
                    ad_counts[ad_lord] += 1

                    ad_clean = ad_lord.lower()
                    ad_prof = profiles.get(ad_clean)

                    if ad_prof:
                        if ad_prof.is_chara_karaka:  # AmK
                            amk_pos_hits += 1
                        if ad_prof.is_primary_bhavesha:  # 10th Lord
                            tenth_lord_pos_hits += 1

                    score = ad_prof.karyesha_score if ad_prof else 0.0
                    pos_scores.append(score)

                    career_events.append({
                        "name": row.get("name", ""),
                        "event": ev_type,
                        "dob": str(b_dt.date()),
                        "date": str(e_date),
                        "md": md_lord,
                        "ad": ad_lord,
                        "score": score,
                    })

                    # 5 Matched Negative Control Slices
                    offsets_years = [-7, -4, 3, 6, 9]
                    for offset in offsets_years:
                        ctrl_date = e_date.replace(year=e_date.year + offset)
                        ctrl_age = (ctrl_date - b_dt.date()).days / 365.25
                        if ctrl_age < 18.0 or ctrl_age > 75.0:
                            continue

                        ctrl_ad_lord = None
                        for md in dtree.mahadashas:
                            if md.contains(ctrl_date):
                                for ad in md.sub_periods:
                                    if ad.contains(ctrl_date):
                                        ctrl_ad_lord = ad.lord.lower()
                                        break
                                break

                        if not ctrl_ad_lord:
                            continue

                        ctrl_prof = profiles.get(ctrl_ad_lord)
                        c_score = ctrl_prof.karyesha_score if ctrl_prof else 0.0
                        neg_scores.append(c_score)

                        if ctrl_prof:
                            if ctrl_prof.is_chara_karaka:
                                amk_neg_hits += 1
                            if ctrl_prof.is_primary_bhavesha:
                                tenth_lord_neg_hits += 1

                        control_slices.append(c_score)

                    break

    n_pos = len(career_events)
    n_neg = len(control_slices)

    print(f"=== CAREER DOMAIN TIMING BENCHMARK (n = {n_pos} Events, n = {n_neg} Controls) ===")

    # 1. Mahadasha Distribution
    chi2_stat = 0.0
    print("\n### 1. Mahadasha (MD) Distribution vs Chance Expectation")
    print("| Planet | Duration | Chance % | Expected (n=120) | Observed | Diff | Lift Ratio |")
    print("|---|---|---|---|---|---|---|")
    for planet in ["Venus", "Saturn", "Rahu", "Mercury", "Jupiter", "Moon", "Mars", "Ketu", "Sun"]:
        prob = DASHA_PROBABILITIES[planet]
        exp = n_pos * prob
        obs = md_counts[planet]
        diff = obs - exp
        lift = obs / exp if exp > 0 else 0
        chi2_stat += ((obs - exp) ** 2) / exp
        print(f"| **{planet}** | {DASHA_YEARS[planet]}y | {prob*100:.1f}% | {exp:.2f} | **{obs}** | {diff:+.2f} | **{lift:.2f}x** |")

    print(f"\n*MD Chi-Square Stat:* $\\chi^2 = {chi2_stat:.2f}$ (df = 8)")

    # 2. Vector Isolation for Career
    tpr_amk = (amk_pos_hits / n_pos) * 100 if n_pos > 0 else 0
    fpr_amk = (amk_neg_hits / n_neg) * 100 if n_neg > 0 else 0
    lift_amk = tpr_amk / fpr_amk if fpr_amk > 0 else 0

    tpr_10th = (tenth_lord_pos_hits / n_pos) * 100 if n_pos > 0 else 0
    fpr_10th = (tenth_lord_neg_hits / n_neg) * 100 if n_neg > 0 else 0
    lift_10th = tpr_10th / fpr_10th if fpr_10th > 0 else 0

    print("\n### 2. Isolated Vector Performance (Career)")
    print(f"- **Amatya Karaka (AmK - 2nd highest degree planet):**")
    print(f"  - TPR (Career Event in AmK AD): {amk_pos_hits}/{n_pos} ({tpr_amk:.1f}%)")
    print(f"  - FPR (Control Slice in AmK AD): {amk_neg_hits}/{n_neg} ({fpr_amk:.1f}%)")
    print(f"  - AmK Lift: **{lift_amk:.2f}x**")

    print(f"\n- **Primary 10th House Lord (Dashamesha):**")
    print(f"  - TPR (Career Event in 10th Lord AD): {tenth_lord_pos_hits}/{n_pos} ({tpr_10th:.1f}%)")
    print(f"  - FPR (Control Slice in 10th Lord AD): {tenth_lord_neg_hits}/{n_neg} ({fpr_10th:.1f}%)")
    print(f"  - 10th Lord Lift: **{lift_10th:.2f}x**")

    # 3. Continuous Score Distribution & ROC-AUC
    mean_pos = sum(pos_scores) / len(pos_scores) if pos_scores else 0
    mean_neg = sum(neg_scores) / len(neg_scores) if neg_scores else 0
    auc = compute_roc_auc(pos_scores, neg_scores)

    print(f"\n### 3. Discrimination & ROC-AUC")
    print(f"- Career Event AD Score Mean: {mean_pos:.2f}")
    print(f"- Control Slice AD Score Mean: {mean_neg:.2f}")
    print(f"- Delta: {mean_pos - mean_neg:+.2f}")
    print(f"- Career Karyesha ROC-AUC: **{auc:.4f}**")


if __name__ == "__main__":
    run_career_benchmark(120)
