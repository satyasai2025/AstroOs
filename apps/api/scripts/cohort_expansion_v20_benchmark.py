"""
AstroOS — COHORT-v2.0 Replication Benchmark Suite
=================================================
Evaluates n = 400 verified marriage events (Events 121 to 520, AA/A Rodden-rated)
along with 1,600 symmetric within-subject negative controls (Offsets: [-6, -3, +3, +6] years).
Total Evaluated Windows: N = 2,000.

Pre-Registered Replication Hypotheses:
1. E1: Mahadasha (MD) Distribution Replication (Chi2, p-val, FDR).
2. E2: Strict D1 Karyesha (v1 + v4) Replication.
3. E3: D9 Navamsha 7th House (v6) Replication.
4. E4: GATE-Mode-C Replication on N=2,000 unseen sample.
"""

import csv
import math
import sys
from pathlib import Path
from datetime import datetime, date, timezone
from typing import List, Dict, Any, Tuple
from collections import defaultdict, Counter

REPO_ROOT = Path("c:/Users/rkmau/Downloads/ReplitplusClaude/AstroOS")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.karyesha_engine import KaryeshaEngine, DomainEnum, RASHI_LORDS
from apps.api.services.dataset_hygiene_v1 import parse_date_flex


def safe_year_offset(d: date, offset: int) -> date:
    try:
        return d.replace(year=d.year + offset)
    except ValueError:
        return d.replace(year=d.year + offset, day=28)


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


def run_v20_benchmark(skip_n: int = 120, target_n: int = 400):
    wrapper = EphemerisWrapper(ephemeris_path=str(REPO_ROOT / "data/ephemeris"))
    dasha_engine = DashaEngine(wrapper)
    karyesha_engine = KaryeshaEngine(wrapper)

    pristine_csv_path = REPO_ROOT / "data/shastric_rules/kundalee_pristine_full.csv"

    TIER_1_MDS = {"sun", "rahu", "jupiter"}

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
                    # INVARIANT 1: Skip first 120 events (COHORT-v1.3 Discovery Set)
                    if seen_event_count <= skip_n:
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

                    collected_pos_count += 1
                    md_lord = target_md.lord.lower()
                    ad_lord = target_ad.lord.lower()
                    ad_prof = profiles.get(ad_lord)

                    md_distribution_pos[md_lord] += 1

                    pos_rec = {
                        "subject_id": row.get("name", f"subj_{collected_pos_count}"),
                        "age": age_years,
                        "md_lord": md_lord,
                        "ad_lord": ad_lord,
                        "v1_7th_lord": ad_prof.is_primary_bhavesha if ad_prof else False,
                        "v2_occupant": ad_prof.is_house_occupant if ad_prof else False,
                        "v3_aspect": ad_prof.is_house_aspector if ad_prof else False,
                        "v4_sambandha": ad_prof.is_lord_sambandha if ad_prof else False,
                        "v5_dk": ad_prof.is_chara_karaka if ad_prof else False,
                        "v6_d9_7th": ad_prof.is_d9_karyesha if ad_prof else False,
                        "v7_naisargika": ad_prof.is_naisargika_karaka if ad_prof else False,
                        "strict_v1_v4": (ad_prof.is_primary_bhavesha or ad_prof.is_lord_sambandha) if ad_prof else False,
                    }
                    pos_records.append(pos_rec)

                    # INVARIANT 4: Symmetric Control Offsets [-6, -3, +3, +6]
                    offsets_years = [-6, -3, 3, 6]
                    for offset in offsets_years:
                        ctrl_date = safe_year_offset(e_date, offset)
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
                        md_distribution_neg[ctrl_md_lord] += 1

                        neg_rec = {
                            "subject_id": row.get("name", f"subj_{collected_pos_count}"),
                            "age": ctrl_age,
                            "md_lord": ctrl_md_lord,
                            "ad_lord": ctrl_ad_lord,
                            "v1_7th_lord": ctrl_prof.is_primary_bhavesha if ctrl_prof else False,
                            "v2_occupant": ctrl_prof.is_house_occupant if ctrl_prof else False,
                            "v3_aspect": ctrl_prof.is_house_aspector if ctrl_prof else False,
                            "v4_sambandha": ctrl_prof.is_lord_sambandha if ctrl_prof else False,
                            "v5_dk": ctrl_prof.is_chara_karaka if ctrl_prof else False,
                            "v6_d9_7th": ctrl_prof.is_d9_karyesha if ctrl_prof else False,
                            "v7_naisargika": ctrl_prof.is_naisargika_karaka if ctrl_prof else False,
                            "strict_v1_v4": (ctrl_prof.is_primary_bhavesha or ctrl_prof.is_lord_sambandha) if ctrl_prof else False,
                        }
                        neg_records.append(neg_rec)

                    break

    print("=" * 85)
    print(f"ASTROOS COHORT-v2.0 EXPANSION BENCHMARK RESULTS")
    print(f"Sample: N_pos = {len(pos_records)} Marriages, N_neg = {len(neg_records)} Symmetric Controls | Total = {len(pos_records) + len(neg_records)} Windows")
    print(f"Base Rate: {(len(pos_records)/(len(pos_records)+len(neg_records)))*100:.2f}% | Zero Leakage: Events 1-120 Skipped")
    print("=" * 85)

    # 1. Mahadasha Distribution (Replication Test E1)
    print("\n### 1. HYPOTHESIS E1: MAHADASHA (MD) DISTRIBUTION REPLICATION TABLE")
    print("| MD Planet | Positive Hits (n=400) | % Pos | Control Hits (n=1569) | % Neg | Empirical Lift | Theoretical Lift (Years/120) |")
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

    print(f"\nGoodness-of-Fit vs Theoretical Vimshottari: Chi2 = {chi2_theoretical:.2f} (df=8, critical at p=0.05 is 15.51, at p=0.001 is 26.12)")

    # 2. Per-Vector Replication Table (E2 & E3)
    print("\n### 2. HYPOTHESES E2 & E3: KARYESHA VECTOR ABLATION REPLICATION MATRIX")
    print("| Vector ID | Vector Rule Description | TPR (Recall) | FPR | Precision | Lift | Chi2 (p-val) |")
    print("|---|---|---|---|---|---|---|")

    vector_defs = [
        ("v1_7th_lord", "Primary D1 7th Lord (v1)", lambda r: r["v1_7th_lord"]),
        ("v2_occupant", "D1 7th House Occupant (v2)", lambda r: r["v2_occupant"]),
        ("v3_aspect", "D1 7th House Drishti (v3)", lambda r: r["v3_aspect"]),
        ("v4_sambandha", "7th Lord Sambandha (v4)", lambda r: r["v4_sambandha"]),
        ("v5_dk", "Chara Dara Karaka (DK, v5)", lambda r: r["v5_dk"]),
        ("v6_d9_7th", "D9 Navamsha 7th House (v6)", lambda r: r["v6_d9_7th"]),
        ("v7_naisargika", "Naisargika Karaka Booster (v7)", lambda r: r["v7_naisargika"]),
        ("strict_v1_v4", "Strict D1 Karyesha (v1 OR v4)", lambda r: r["strict_v1_v4"]),
    ]

    for v_id, desc, check_fn in vector_defs:
        tp, fp, fn, tn = 0, 0, 0, 0
        for r in pos_records:
            if check_fn(r):
                tp += 1
            else:
                fn += 1
        for r in neg_records:
            if check_fn(r):
                fp += 1
            else:
                tn += 1

        st = compute_contingency_stats(tp, fp, fn, tn)
        chi2_val = st["chi2"]
        if chi2_val >= 6.63:
            p_str = f"chi2={chi2_val:.2f} (p<0.01)"
        elif chi2_val >= 3.84:
            p_str = f"chi2={chi2_val:.2f} (p<0.05)"
        else:
            p_str = f"chi2={chi2_val:.2f} (p>0.05)"

        print(
            f"| **`{v_id}`** | {desc} | {st['tpr']:.1f}% ({st['tp']}/{len(pos_records)}) | "
            f"{st['fpr']:.1f}% ({st['fp']}/{len(neg_records)}) | **{st['precision']:.1f}%** | **{st['lift']:.2f}x** | {p_str} |"
        )

    # 3. GATE-Mode-C Replication on N=2,000 (E4)
    print("\n### 3. HYPOTHESIS E4: GATE-MODE-C REPLICATION ON N=2,000 WINDOWS")
    print("| Model Name | TP | FP | FN | TN | Full Cohort Recall (TPR) | FPR | Precision | Lift | F1 Score | Chi2 (p-val) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")

    gate_check = lambda r: (r["md_lord"] in TIER_1_MDS) and (r["v1_7th_lord"] or r["v4_sambandha"] or r["v6_d9_7th"])
    tp, fp, fn, tn = 0, 0, 0, 0
    for r in pos_records:
        if gate_check(r):
            tp += 1
        else:
            fn += 1
    for r in neg_records:
        if gate_check(r):
            fp += 1
        else:
            tn += 1

    st = compute_contingency_stats(tp, fp, fn, tn)
    chi2_val = st["chi2"]
    if chi2_val >= 10.83:
        p_str = f"chi2={chi2_val:.2f} (p<0.001)"
    elif chi2_val >= 6.63:
        p_str = f"chi2={chi2_val:.2f} (p<0.01)"
    elif chi2_val >= 3.84:
        p_str = f"chi2={chi2_val:.2f} (p<0.05)"
    else:
        p_str = f"chi2={chi2_val:.2f} (p>0.05)"

    print(
        f"| **GATE-Mode-C (N=2,000)** | {st['tp']} | {st['fp']} | {st['fn']} | {st['tn']} | "
        f"**{st['recall']:.1f}%** ({st['tp']}/{len(pos_records)}) | {st['fpr']:.1f}% ({st['fp']}/{len(neg_records)}) | "
        f"**{st['precision']:.1f}%** | **{st['lift']:.2f}x** | {st['f1']:.2f} | {p_str} |"
    )


if __name__ == "__main__":
    run_v20_benchmark(skip_n=120, target_n=400)
