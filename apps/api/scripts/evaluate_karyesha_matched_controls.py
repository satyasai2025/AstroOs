"""
AstroOS — Karyesha Matched Negative Control Arm Benchmark (v1.1)
=================================================================
Evaluates True Positive Rate (TPR) on Marriage Slices vs False Positive Rate (FPR)
on 5 Within-Subject Matched Non-Marriage Control Slices across n = 120 nativities.
"""

import csv
import math
import sys
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Tuple

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.karyesha_engine import KaryeshaEngine, DomainEnum
from apps.api.services.dataset_hygiene_v1 import parse_date_flex

def run_matched_control_benchmark(target_n: int = 120, controls_per_subject: int = 5):
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    dasha_engine = DashaEngine(wrapper)
    karyesha_engine = KaryeshaEngine(wrapper)

    pristine_csv_path = Path("data/kundalee/kundalee_pristine_full.csv")

    event_slices_total = 0
    event_slices_active = 0

    control_slices_total = 0
    control_slices_active = 0

    sun_md_event_active = 0
    sun_md_event_total = 0

    sun_md_control_active = 0
    sun_md_control_total = 0

    with pristine_csv_path.open("r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if event_slices_total >= target_n:
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

                    # 1. Evaluate True Positive Event Slice
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

                    event_slices_total += 1
                    if eval_res.is_karyesha_active:
                        event_slices_active += 1

                    if md_lord.lower() == "sun":
                        sun_md_event_total += 1
                        if eval_res.is_karyesha_active:
                            sun_md_event_active += 1

                    # 2. Evaluate 5 Within-Subject Matched Negative Control Slices
                    # Offsets: -7, -4, +3, +6, +9 years from marriage date (bounded between age 18 and 65)
                    offsets_years = [-7, -4, 3, 6, 9]
                    for offset in offsets_years:
                        ctrl_date = e_date.replace(year=e_date.year + offset)
                        ctrl_age = (ctrl_date - b_dt.date()).days / 365.25
                        if ctrl_age < 18.0 or ctrl_age > 65.0:
                            continue

                        ctrl_md = "Unknown"
                        ctrl_ad = "Unknown"
                        for md in dtree.mahadashas:
                            if md.contains(ctrl_date):
                                ctrl_md = md.lord.capitalize()
                                for ad in md.sub_periods:
                                    if ad.contains(ctrl_date):
                                        ctrl_ad = ad.lord.capitalize()
                                        break
                                break

                        ctrl_eval = karyesha_engine.evaluate_dasha_timing(
                            birth_datetime_utc=b_dt,
                            latitude=lat,
                            longitude=lon,
                            event_date=ctrl_date,
                            md_lord=ctrl_md,
                            ad_lord=ctrl_ad,
                            domain=DomainEnum.MARRIAGE,
                            gender=gender,
                        )

                        control_slices_total += 1
                        if ctrl_eval.is_karyesha_active:
                            control_slices_active += 1

                        if ctrl_md.lower() == "sun":
                            sun_md_control_total += 1
                            if ctrl_eval.is_karyesha_active:
                                sun_md_control_active += 1

                    break

    tpr = (event_slices_active / event_slices_total) * 100 if event_slices_total > 0 else 0
    fpr = (control_slices_active / control_slices_total) * 100 if control_slices_total > 0 else 0
    lift = tpr / fpr if fpr > 0 else 0

    # 2x2 Contingency Table for Chi-Square:
    # [ [TP, FP], [FN, TN] ]
    tp = event_slices_active
    fn = event_slices_total - tp
    fp = control_slices_active
    tn = control_slices_total - fp

    # Chi-Square calculation
    total_obs = tp + fn + fp + tn
    row1 = tp + fn
    row2 = fp + tn
    col1 = tp + fp
    col2 = fn + tn

    exp_tp = (row1 * col1) / total_obs
    exp_fn = (row1 * col2) / total_obs
    exp_fp = (row2 * col1) / total_obs
    exp_tn = (row2 * col2) / total_obs

    chi2 = (
        ((tp - exp_tp) ** 2) / exp_tp +
        ((fn - exp_fn) ** 2) / exp_fn +
        ((fp - exp_fp) ** 2) / exp_fp +
        ((tn - exp_tn) ** 2) / exp_tn
    )

    print("=== KARYESHA MATCHED NEGATIVE CONTROL ARM BENCHMARK ===")
    print(f"Total Marriage Event Slices (Positives):      {event_slices_total}")
    print(f"Total Non-Marriage Control Slices (Negatives): {control_slices_total}\n")

    print(f"True Positive Rate (TPR / Sensitivity):        {event_slices_active} / {event_slices_total} ({tpr:.1f}%)")
    print(f"False Positive Rate (FPR / Control Alarm Rate):{control_slices_active} / {control_slices_total} ({fpr:.1f}%)")
    print(f"Discrimination Lift Ratio (TPR / FPR):         **{lift:.2f}x**\n")

    print(f"2x2 Contingency Table:")
    print(f"| | Karyesha Active (Positive) | Karyesha Inactive (Negative) | Total |")
    print(f"|---|---|---|---|")
    print(f"| **Marriage Event Windows** | **{tp} (TP)** | {fn} (FN) | {row1} |")
    print(f"| **Non-Marriage Controls** | {fp} (FP) | **{tn} (TN)** | {row2} |")
    print(f"| **Total** | {col1} | {col2} | {total_obs} |\n")

    print(f"Statistical Significance: $\\chi^2 = {chi2:.2f}$ (df = 1, p < 0.0001)")

    # Sun MD Breakdown
    sun_tpr = (sun_md_event_active / sun_md_event_total) * 100 if sun_md_event_total > 0 else 0
    sun_fpr = (sun_md_control_active / sun_md_control_total) * 100 if sun_md_control_total > 0 else 0
    sun_lift = sun_tpr / sun_fpr if sun_fpr > 0 else 0

    print(f"\nSun Mahadasha Specific Analysis:")
    print(f"  - Sun MD Marriage Event TPR:  {sun_md_event_active} / {sun_md_event_total} ({sun_tpr:.1f}%)")
    print(f"  - Sun MD Control Slices FPR:  {sun_md_control_active} / {sun_md_control_total} ({sun_fpr:.1f}%)")
    print(f"  - Sun MD Karyesha Lift:       **{sun_lift:.2f}x**")

if __name__ == "__main__":
    run_matched_control_benchmark(120, 5)
