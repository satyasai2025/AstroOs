"""
AstroOS — Karyesha Diagnostic Suite: ROC-AUC, Vector Ablation & Within-MD Granularity
=====================================================================================
1. Continuous Score Distribution & ROC-AUC calculation (Marriage vs Control Slices).
2. Isolated Vector Ablation (TPR, FPR, Lift for each individual vector + Strict-Only).
3. Within-Mahadasha AD Slice Discrimination (Marriage AD vs Other 8 ADs in same MD).
"""

import csv
import math
import sys
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Any, Tuple

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.karyesha_engine import KaryeshaEngine, DomainEnum
from apps.api.services.dataset_hygiene_v1 import parse_date_flex


def compute_roc_auc(pos_scores: List[float], neg_scores: List[float]) -> float:
    """
    Computes ROC-AUC via Mann-Whitney U statistic:
    AUC = P(Score_pos > Score_neg) + 0.5 * P(Score_pos == Score_neg)
    """
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


def run_diagnostic_suite(target_n: int = 120):
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    dasha_engine = DashaEngine(wrapper)
    karyesha_engine = KaryeshaEngine(wrapper)

    pristine_csv_path = Path("data/kundalee/kundalee_pristine_full.csv")

    marriage_scores: List[float] = []
    control_scores: List[float] = []

    # Vector tracking: dict of vector_name -> {'event_hits': int, 'control_hits': int}
    vectors = [
        "v1_7th_lord",
        "v2_7th_occupant",
        "v3_7th_aspect",
        "v4_7th_lord_sambandha",
        "v5_dara_karaka_dk",
        "v6_d9_7th_house",
        "v7_naisargika_booster",
        "strict_only_v1_or_v4",
    ]
    vector_stats = {v: {"pos_hits": 0, "neg_hits": 0} for v in vectors}

    # Within-MD tracking
    within_md_marriage_ranks: List[int] = []  # Rank of marriage AD score among 9 ADs (1 = highest)
    within_md_top1_count = 0
    within_md_top3_count = 0
    within_md_total = 0

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

                    # Find Marriage MD and AD
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
                    ad_lord = target_ad.lord.lower()
                    ad_prof = profiles.get(ad_lord)
                    marriage_scores.append(ad_prof.karyesha_score if ad_prof else 0.0)

                    # Vector tracking for marriage AD
                    if ad_prof:
                        if ad_prof.is_primary_bhavesha:
                            vector_stats["v1_7th_lord"]["pos_hits"] += 1
                        if ad_prof.is_house_occupant:
                            vector_stats["v2_7th_occupant"]["pos_hits"] += 1
                        if ad_prof.is_house_aspector:
                            vector_stats["v3_7th_aspect"]["pos_hits"] += 1
                        if ad_prof.is_lord_sambandha:
                            vector_stats["v4_7th_lord_sambandha"]["pos_hits"] += 1
                        if ad_prof.is_chara_karaka:
                            vector_stats["v5_dara_karaka_dk"]["pos_hits"] += 1
                        if ad_prof.is_d9_karyesha:
                            vector_stats["v6_d9_7th_house"]["pos_hits"] += 1
                        if ad_prof.is_naisargika_karaka:
                            vector_stats["v7_naisargika_booster"]["pos_hits"] += 1
                        if ad_prof.is_primary_bhavesha or ad_prof.is_lord_sambandha:
                            vector_stats["strict_only_v1_or_v4"]["pos_hits"] += 1

                    # Within-MD analysis: compare target_ad score against all 9 ADs in target_md
                    all_ad_scores = []
                    for ad in target_md.sub_periods:
                        p_prof = profiles.get(ad.lord.lower())
                        score = p_prof.karyesha_score if p_prof else 0.0
                        all_ad_scores.append((score, ad.lord.lower()))

                    all_ad_scores.sort(key=lambda x: x[0], reverse=True)
                    # Find rank of target_ad
                    for rank, (score, p_name) in enumerate(all_ad_scores, start=1):
                        if p_name == ad_lord:
                            within_md_marriage_ranks.append(rank)
                            if rank == 1:
                                within_md_top1_count += 1
                            if rank <= 3:
                                within_md_top3_count += 1
                            break
                    within_md_total += 1

                    # Control Slices: 5 within-subject non-marriage slices
                    offsets_years = [-7, -4, 3, 6, 9]
                    for offset in offsets_years:
                        ctrl_date = e_date.replace(year=e_date.year + offset)
                        ctrl_age = (ctrl_date - b_dt.date()).days / 365.25
                        if ctrl_age < 18.0 or ctrl_age > 65.0:
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

                        control_total += 1
                        ctrl_prof = profiles.get(ctrl_ad_lord)
                        control_scores.append(ctrl_prof.karyesha_score if ctrl_prof else 0.0)

                        if ctrl_prof:
                            if ctrl_prof.is_primary_bhavesha:
                                vector_stats["v1_7th_lord"]["neg_hits"] += 1
                            if ctrl_prof.is_house_occupant:
                                vector_stats["v2_7th_occupant"]["neg_hits"] += 1
                            if ctrl_prof.is_house_aspector:
                                vector_stats["v3_7th_aspect"]["neg_hits"] += 1
                            if ctrl_prof.is_lord_sambandha:
                                vector_stats["v4_7th_lord_sambandha"]["neg_hits"] += 1
                            if ctrl_prof.is_chara_karaka:
                                vector_stats["v5_dara_karaka_dk"]["neg_hits"] += 1
                            if ctrl_prof.is_d9_karyesha:
                                vector_stats["v6_d9_7th_house"]["neg_hits"] += 1
                            if ctrl_prof.is_naisargika_karaka:
                                vector_stats["v7_naisargika_booster"]["neg_hits"] += 1
                            if ctrl_prof.is_primary_bhavesha or ctrl_prof.is_lord_sambandha:
                                vector_stats["strict_only_v1_or_v4"]["neg_hits"] += 1

                    break

    # 1. Distribution Metrics & ROC-AUC
    mean_pos = sum(marriage_scores) / len(marriage_scores) if marriage_scores else 0
    mean_neg = sum(control_scores) / len(control_scores) if control_scores else 0
    auc = compute_roc_auc(marriage_scores, control_scores)

    print("=== 1. CONTINUOUS SCORE DISTRIBUTION & ROC-AUC ===")
    print(f"Total Marriage Slices (Positives): {event_total}")
    print(f"Total Control Slices (Negatives):  {control_total}")
    print(f"Marriage AD Score Mean:            {mean_pos:.2f}")
    print(f"Control AD Score Mean:             {mean_neg:.2f}")
    print(f"Delta (Pos - Neg):                 {mean_pos - mean_neg:+.2f}")
    print(f"ROC-AUC:                           **{auc:.4f}**\n")

    # 2. Per-Vector Ablation Table
    print("=== 2. PER-VECTOR ISOLATED ABLATION ANALYSIS ===")
    print("| Vector | Vector Rule | TPR (n=120) | FPR (n=514) | Lift (TPR/FPR) |")
    print("|---|---|---|---|---|")
    vector_descriptions = {
        "v1_7th_lord": "Primary D1 7th Lord",
        "v2_7th_occupant": "D1 7th House Occupant",
        "v3_7th_aspect": "D1 7th House Drishti",
        "v4_7th_lord_sambandha": "Sambandha with 7th Lord",
        "v5_dara_karaka_dk": "Chara Dara Karaka (DK)",
        "v6_d9_7th_house": "D9 Navamsha 7th Occupant",
        "v7_naisargika_booster": "Naisargika Venus/Jupiter",
        "strict_only_v1_or_v4": "**Strict-Only (7th Lord OR Sambandha)**",
    }

    for v, desc in vector_descriptions.items():
        pos_h = vector_stats[v]["pos_hits"]
        neg_h = vector_stats[v]["neg_hits"]
        tpr = (pos_h / event_total) * 100 if event_total > 0 else 0
        fpr = (neg_h / control_total) * 100 if control_total > 0 else 0
        lift = tpr / fpr if fpr > 0 else 0
        print(f"| `{v}` | {desc} | {pos_h}/{event_total} ({tpr:.1f}%) | {neg_h}/{control_total} ({fpr:.1f}%) | **{lift:.2f}x** |")

    # 3. Within-MD Slice Analysis
    print("\n=== 3. WITHIN-MAHADASHA AD RANK ANALYSIS ===")
    print(f"Total Evaluated Mahadashas:            {within_md_total}")
    print(f"Marriage AD Ranked #1 Highest Score:   {within_md_top1_count} / {within_md_total} ({within_md_top1_count/within_md_total:.1%}) [Expected: 11.1%]")
    print(f"Marriage AD in Top 3 Highest Scores:   {within_md_top3_count} / {within_md_total} ({within_md_top3_count/within_md_total:.1%}) [Expected: 33.3%]")
    mean_rank = sum(within_md_marriage_ranks) / len(within_md_marriage_ranks) if within_md_marriage_ranks else 0
    print(f"Average Rank of Marriage AD (1-9):    {mean_rank:.2f} (Expected random: 5.00)")


if __name__ == "__main__":
    run_diagnostic_suite(120)
