"""
AstroOS — GATE-v0.1 Qualitative Gating Benchmark
=================================================
Pre-registered deterministic gating test on frozen COHORT-v1.3 (n=120 marriages, 514 control slices).

Gating Rules Evaluated:
1. Gate 1 (Desha-Kaala): Age 18.0 <= Age <= 65.0
2. Gate 2 (MD Screen):
   - Mode A (All MDs): Permissive, full cohort recall.
   - Mode B (Tier 1+2 MDs): Sun, Rahu, Jupiter, Moon, Mars, Venus (Saturn, Mercury, Ketu rejected).
   - Mode C (Tier 1 Only): Sun, Rahu, Jupiter only.
3. Gate 3 (Strict Karyesha): AD Lord is D1 7th Lord (v1) OR Sambandha with 7th Lord (v4) OR D9 7th House (v6).
   - Variant: Strict D1-only (v1 OR v4).
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


def run_gate_benchmark(target_n: int = 120):
    wrapper = EphemerisWrapper(ephemeris_path=str(REPO_ROOT / "data/ephemeris"))
    dasha_engine = DashaEngine(wrapper)
    karyesha_engine = KaryeshaEngine(wrapper)

    pristine_csv_path = REPO_ROOT / "data/shastric_rules/kundalee_pristine_full.csv"

    TIER_1_MDS = {"sun", "rahu", "jupiter"}
    TIER_2_MDS = {"moon", "mars", "venus"}
    EXCLUDED_MDS = {"saturn", "mercury", "ketu"}

    pos_records: List[Dict[str, Any]] = []
    neg_records: List[Dict[str, Any]] = []

    md_distribution_pos = defaultdict(int)
    md_distribution_neg = defaultdict(int)

    event_total = 0
    control_total = 0

    with pristine_csv_path.open("r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if event_total >= target_n:
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
                    md_lord = target_md.lord.lower()
                    ad_lord = target_ad.lord.lower()
                    ad_prof = profiles.get(ad_lord)

                    md_distribution_pos[md_lord] += 1

                    pos_rec = {
                        "subject_id": row.get("id", f"subj_{event_total}"),
                        "age": age_years,
                        "md_lord": md_lord,
                        "ad_lord": ad_lord,
                        "v1_7th_lord": ad_prof.is_primary_bhavesha if ad_prof else False,
                        "v4_sambandha": ad_prof.is_lord_sambandha if ad_prof else False,
                        "v6_d9_7th": ad_prof.is_d9_karyesha if ad_prof else False,
                        "v5_dk": ad_prof.is_chara_karaka if ad_prof else False,
                        "v7_naisargika": ad_prof.is_naisargika_karaka if ad_prof else False,
                    }
                    pos_records.append(pos_rec)

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

                        control_total += 1
                        ctrl_prof = profiles.get(ctrl_ad_lord)
                        md_distribution_neg[ctrl_md_lord] += 1

                        neg_rec = {
                            "subject_id": row.get("id", f"subj_{event_total}"),
                            "age": ctrl_age,
                            "md_lord": ctrl_md_lord,
                            "ad_lord": ctrl_ad_lord,
                            "v1_7th_lord": ctrl_prof.is_primary_bhavesha if ctrl_prof else False,
                            "v4_sambandha": ctrl_prof.is_lord_sambandha if ctrl_prof else False,
                            "v6_d9_7th": ctrl_prof.is_d9_karyesha if ctrl_prof else False,
                            "v5_dk": ctrl_prof.is_chara_karaka if ctrl_prof else False,
                            "v7_naisargika": ctrl_prof.is_naisargika_karaka if ctrl_prof else False,
                        }
                        neg_records.append(neg_rec)

                    break

    print("=" * 80)
    print(f"ASTROOS GATE-v0.1 BENCHMARK RESULTS (N_pos = {len(pos_records)}, N_neg = {len(neg_records)}, Total = {len(pos_records) + len(neg_records)})")
    print("=" * 80)

    print("\n### 1. MD DISTRIBUTION & RECALL-LOSS AUDIT TABLE (TRANSPARENCY REPORT)")
    print("| MD Planet | MD Tier | Marriage Hits (Pos) | % of Cohort | Control Hits (Neg) | % of Controls | MD Lift | Recall Loss if Gated Out |")
    print("|---|---|---|---|---|---|---|---|")

    all_md_planets = ["sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury", "ketu", "venus"]
    for p in all_md_planets:
        p_hits = md_distribution_pos[p]
        n_hits = md_distribution_neg[p]
        p_pct = (p_hits / event_total) * 100.0 if event_total > 0 else 0.0
        n_pct = (n_hits / control_total) * 100.0 if control_total > 0 else 0.0
        p_lift = (p_pct / n_pct) if n_pct > 0 else 0.0

        if p in TIER_1_MDS:
            tier_str = "Tier 1 (High)"
        elif p in TIER_2_MDS:
            tier_str = "Tier 2 (Neutral)"
        else:
            tier_str = "Tier 3 (Low/Exclude)"

        loss_str = f"-{p_hits} marriages (-{p_pct:.1f}%)" if p in EXCLUDED_MDS else "Retained"
        print(f"| **{p.capitalize()}** | {tier_str} | {p_hits}/{event_total} | {p_pct:.1f}% | {n_hits}/{control_total} | {n_pct:.1f}% | **{p_lift:.2f}x** | {loss_str} |")

    gating_configurations = [
        {
            "name": "GATE-0: Strict Karyesha Alone (No MD Gate, v1+v4+v6)",
            "md_allowed": set(all_md_planets),
            "karyesha_check": lambda r: r["v1_7th_lord"] or r["v4_sambandha"] or r["v6_d9_7th"],
            "desc": "Baseline Gate: Any MD + (D1 7th Lord OR Sambandha OR D9 7th)",
        },
        {
            "name": "GATE-0b: Strict D1 Karyesha Alone (No MD Gate, v1+v4 only)",
            "md_allowed": set(all_md_planets),
            "karyesha_check": lambda r: r["v1_7th_lord"] or r["v4_sambandha"],
            "desc": "Baseline Gate: Any MD + (D1 7th Lord OR Sambandha)",
        },
        {
            "name": "GATE-Mode-A: Strict Karyesha (v1+v4+v6) + All MDs",
            "md_allowed": set(all_md_planets),
            "karyesha_check": lambda r: r["v1_7th_lord"] or r["v4_sambandha"] or r["v6_d9_7th"],
            "desc": "Mode A: All MDs + (v1 or v4 or v6)",
        },
        {
            "name": "GATE-Mode-B: Strict Karyesha (v1+v4+v6) x Tier 1+2 MDs",
            "md_allowed": TIER_1_MDS.union(TIER_2_MDS),
            "karyesha_check": lambda r: r["v1_7th_lord"] or r["v4_sambandha"] or r["v6_d9_7th"],
            "desc": "Mode B: Excludes Saturn, Mercury, Ketu MDs",
        },
        {
            "name": "GATE-Mode-B-D1: Strict D1 (v1+v4) x Tier 1+2 MDs",
            "md_allowed": TIER_1_MDS.union(TIER_2_MDS),
            "karyesha_check": lambda r: r["v1_7th_lord"] or r["v4_sambandha"],
            "desc": "Mode B-D1: Excludes Saturn, Mercury, Ketu MDs + D1 strict only",
        },
        {
            "name": "GATE-Mode-C: Strict Karyesha (v1+v4+v6) x Tier 1 Only (Sun, Rahu, Jup)",
            "md_allowed": TIER_1_MDS,
            "karyesha_check": lambda r: r["v1_7th_lord"] or r["v4_sambandha"] or r["v6_d9_7th"],
            "desc": "Mode C: Sun, Rahu, Jupiter MDs only",
        },
        {
            "name": "GATE-Mode-C-D1: Strict D1 (v1+v4) x Tier 1 Only (Sun, Rahu, Jup)",
            "md_allowed": TIER_1_MDS,
            "karyesha_check": lambda r: r["v1_7th_lord"] or r["v4_sambandha"],
            "desc": "Mode C-D1: Sun, Rahu, Jupiter MDs only + D1 strict only",
        },
    ]

    print("\n### 2. GATE-v0.1 PERFORMANCE BENCHMARK MATRIX")
    print("| Model Name | TP | FP | FN | TN | Full Cohort Recall (TPR) | FPR | Precision (PPV) | Lift | F1 Score | Chi2 (p-val) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")

    for cfg in gating_configurations:
        tp, fp, fn, tn = 0, 0, 0, 0

        for r in pos_records:
            age_ok = 18.0 <= r["age"] <= 65.0
            md_ok = r["md_lord"] in cfg["md_allowed"]
            karyesha_ok = cfg["karyesha_check"](r)

            if age_ok and md_ok and karyesha_ok:
                tp += 1
            else:
                fn += 1

        for r in neg_records:
            age_ok = 18.0 <= r["age"] <= 65.0
            md_ok = r["md_lord"] in cfg["md_allowed"]
            karyesha_ok = cfg["karyesha_check"](r)

            if age_ok and md_ok and karyesha_ok:
                fp += 1
            else:
                tn += 1

        stats = compute_contingency_stats(tp, fp, fn, tn)
        chi2_val = stats["chi2"]
        if chi2_val >= 10.83:
            p_str = f"chi2={chi2_val:.2f} (p<0.001)"
        elif chi2_val >= 6.63:
            p_str = f"chi2={chi2_val:.2f} (p<0.01)"
        elif chi2_val >= 3.84:
            p_str = f"chi2={chi2_val:.2f} (p<0.05)"
        else:
            p_str = f"chi2={chi2_val:.2f} (p>0.05)"

        print(
            f"| **{cfg['name']}** | {tp} | {fp} | {fn} | {tn} | "
            f"**{stats['recall']:.1f}%** ({tp}/{event_total}) | {stats['fpr']:.1f}% ({fp}/{control_total}) | "
            f"**{stats['precision']:.1f}%** | **{stats['lift']:.2f}x** | {stats['f1']:.2f} | {p_str} |"
        )

    print("\n### 3. METHODOLOGICAL AUDIT & TAKEAWAYS")
    print(f"- Base Rate of Marriage in sample: {event_total} / {event_total + control_total} = {(event_total/(event_total+control_total))*100:.1f}%")
    print("- All figures calculated strictly on the frozen within-subject cohort.")


if __name__ == "__main__":
    run_gate_benchmark(120)
