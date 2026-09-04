"""
AstroOS — Mode C Holdout Split Validation (Chronological / Out-of-Time)
=======================================================================
Methodological Purpose:
Evaluates whether GATE-Mode-C (Tier 1 MDs: Sun, Rahu, Jupiter x Strict Karyesha)
maintains discriminatory signal when tested out-of-time on the second half of the cohort.

Design:
- Discovery / In-Sample Set: Events 1 to 60 + matched control slices.
- Holdout / Out-of-Time Test Set: Events 61 to 120 + matched control slices.
- Label: Mode C is strictly 'exploratory, cohort-internal'.
"""

import csv
import math
import sys
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Any, Tuple
from collections import defaultdict

REPO_ROOT = Path("c:/Users/rkmau/Downloads/ReplitplusClaude/AstroOS")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.karyesha_engine import KaryeshaEngine, DomainEnum
from apps.api.services.dataset_hygiene_v1 import parse_date_flex


def compute_contingency_stats(tp: int, fp: int, fn: int, tn: int) -> Dict[str, float]:
    total_pos = tp + fn
    total_neg = fp + tn
    total = total_pos + total_neg

    tpr = (tp / total_pos) * 100.0 if total_pos > 0 else 0.0
    fpr = (fp / total_neg) * 100.0 if total_neg > 0 else 0.0
    precision = (tp / (tp + fp)) * 100.0 if (tp + fp) > 0 else 0.0
    recall = tpr
    lift = (tpr / fpr) if fpr > 0 else 0.0
    f1 = (2 * (precision * recall) / (precision + recall)) if (precision + recall) > 0 else 0.0

    a, b, c, d = tp, fp, fn, tn
    denom = (a + b) * (c + d) * (a + c) * (b + d)
    if denom > 0:
        num = total * max(0.0, abs(a * d - b * c) - (total / 2.0)) ** 2
        chi2 = num / denom
    else:
        chi2 = 0.0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "total_pos": total_pos,
        "total_neg": total_neg,
        "tpr": tpr,
        "fpr": fpr,
        "precision": precision,
        "recall": recall,
        "lift": lift,
        "f1": f1,
        "chi2": chi2,
    }


def run_holdout_validation():
    wrapper = EphemerisWrapper(ephemeris_path=str(REPO_ROOT / "data/ephemeris"))
    dasha_engine = DashaEngine(wrapper)
    karyesha_engine = KaryeshaEngine(wrapper)

    pristine_csv_path = REPO_ROOT / "data/shastric_rules/kundalee_pristine_full.csv"

    TIER_1_MDS = {"sun", "rahu", "jupiter"}

    pos_discovery: List[Dict[str, Any]] = []
    neg_discovery: List[Dict[str, Any]] = []

    pos_holdout: List[Dict[str, Any]] = []
    neg_holdout: List[Dict[str, Any]] = []

    event_total = 0

    with pristine_csv_path.open("r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if event_total >= 120:
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
                        lagna_idx, planets_info, karakas = karyesha_engine.extract_chart_positions(b_dt, lat, lon)
                        profiles = karyesha_engine.analyze_domain_karyeshas(
                            lagna_idx, planets_info, karakas, domain=DomainEnum.MARRIAGE, gender=gender
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

                    event_total += 1
                    is_discovery = (event_total <= 60)

                    md_lord = target_md.lord.lower()
                    ad_lord = target_ad.lord.lower()
                    ad_prof = profiles.get(ad_lord)

                    pos_rec = {
                        "event_idx": event_total,
                        "age": age_years,
                        "md_lord": md_lord,
                        "ad_lord": ad_lord,
                        "v1_7th_lord": ad_prof.is_primary_bhavesha if ad_prof else False,
                        "v4_sambandha": ad_prof.is_lord_sambandha if ad_prof else False,
                        "v6_d9_7th": ad_prof.is_d9_karyesha if ad_prof else False,
                    }

                    if is_discovery:
                        pos_discovery.append(pos_rec)
                    else:
                        pos_holdout.append(pos_rec)

                    # Controls
                    offsets_years = [-7, -4, 3, 6, 9]
                    for offset in offsets_years:
                        ctrl_date = e_date.replace(year=e_date.year + offset)
                        ctrl_age = (ctrl_date - b_dt.date()).days / 365.25
                        if ctrl_age < 18.0 or ctrl_age > 65.0:
                            continue

                        ctrl_md_lord = None
                        ctrl_ad_lord = None
                        for md in dtree.mahadashas:
                            if md.contains(ctrl_date):
                                ctrl_md_lord = md.lord.lower()
                                for ad in md.sub_periods:
                                    if ad.contains(ctrl_date):
                                        ctrl_ad_lord = ad.lord.lower()
                                        break
                                break

                        if not ctrl_md_lord or not ctrl_ad_lord:
                            continue

                        ctrl_prof = profiles.get(ctrl_ad_lord)
                        neg_rec = {
                            "event_idx": event_total,
                            "age": ctrl_age,
                            "md_lord": ctrl_md_lord,
                            "ad_lord": ctrl_ad_lord,
                            "v1_7th_lord": ctrl_prof.is_primary_bhavesha if ctrl_prof else False,
                            "v4_sambandha": ctrl_prof.is_lord_sambandha if ctrl_prof else False,
                            "v6_d9_7th": ctrl_prof.is_d9_karyesha if ctrl_prof else False,
                        }

                        if is_discovery:
                            neg_discovery.append(neg_rec)
                        else:
                            neg_holdout.append(neg_rec)

                    break

    print("=" * 80)
    print("MODE C HOLDOUT VALIDATION (CHRONOLOGICAL / OUT-OF-TIME SPLIT)")
    print("Label: Mode C = exploratory, cohort-internal")
    print(f"Discovery Set: {len(pos_discovery)} marriages, {len(neg_discovery)} controls (Total = {len(pos_discovery) + len(neg_discovery)})")
    print(f"Holdout Set:   {len(pos_holdout)} marriages, {len(neg_holdout)} controls (Total = {len(pos_holdout) + len(neg_holdout)})")
    print("=" * 80)

    def evaluate_set(name: str, pos_list: List[Dict], neg_list: List[Dict]):
        tp, fp, fn, tn = 0, 0, 0, 0
        for r in pos_list:
            age_ok = 18.0 <= r["age"] <= 65.0
            md_ok = r["md_lord"] in TIER_1_MDS
            karyesha_ok = r["v1_7th_lord"] or r["v4_sambandha"] or r["v6_d9_7th"]
            if age_ok and md_ok and karyesha_ok:
                tp += 1
            else:
                fn += 1

        for r in neg_list:
            age_ok = 18.0 <= r["age"] <= 65.0
            md_ok = r["md_lord"] in TIER_1_MDS
            karyesha_ok = r["v1_7th_lord"] or r["v4_sambandha"] or r["v6_d9_7th"]
            if age_ok and md_ok and karyesha_ok:
                fp += 1
            else:
                tn += 1

        stats = compute_contingency_stats(tp, fp, fn, tn)
        return stats

    stats_disc = evaluate_set("Discovery (1-60)", pos_discovery, neg_discovery)
    stats_hold = evaluate_set("Holdout (61-120)", pos_holdout, neg_holdout)

    print("\n### RESULTS TABLE: DISCOVERY VS OUT-OF-TIME HOLDOUT")
    print("| Split Partition | Total Pos | Total Neg | TP | FP | FN | TN | Recall (TPR) | FPR | Precision | Lift | Chi2 (p-val) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")

    for label, st in [("Discovery (Events 1-60)", stats_disc), ("Holdout (Events 61-120)", stats_hold)]:
        chi2_val = st["chi2"]
        if chi2_val >= 6.63:
            p_str = f"chi2={chi2_val:.2f} (p<0.01)"
        elif chi2_val >= 3.84:
            p_str = f"chi2={chi2_val:.2f} (p<0.05)"
        else:
            p_str = f"chi2={chi2_val:.2f} (p>0.05)"

        print(
            f"| **{label}** | {st['total_pos']} | {st['total_neg']} | {st['tp']} | {st['fp']} | {st['fn']} | {st['tn']} | "
            f"**{st['recall']:.1f}%** | {st['fpr']:.1f}% | **{st['precision']:.1f}%** | **{st['lift']:.2f}x** | {p_str} |"
        )


if __name__ == "__main__":
    run_holdout_validation()
