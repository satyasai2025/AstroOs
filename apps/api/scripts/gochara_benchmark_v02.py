"""
AstroOS — GOCHARA-RULES-v0.2 Benchmark Suite
=============================================
Pre-registered Gochara transit testing on frozen COHORT-v1.3 (N_pos=120, N_neg=514, Total=634).

Pre-Registered Triggers:
1. G1: Rahu or Ketu in 1st House, 7th House, or natal 7th Lord's house.
2. G2: Rahu-Ketu axis aligned with Lagna-7th axis (Rahu in 1st & Ketu in 7th, or vice-versa).
3. G3 (Narrowed): Transit Jupiter in 7th House (or 7L house) AND Transit Rahu in 1st House (Lagna).
4. Composite Triggers with GATE-Mode-C (exploratory, cohort-internal):
   - G4: Mode C + G1
   - G5: Mode C + G2
   - G6: Mode C + G3
"""

import csv
import math
import sys
from pathlib import Path
from datetime import datetime, date, timezone
from typing import List, Dict, Any, Tuple, Set

REPO_ROOT = Path("c:/Users/rkmau/Downloads/ReplitplusClaude/AstroOS")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.karyesha_engine import KaryeshaEngine, DomainEnum, RASHI_LORDS
from apps.api.services.dataset_hygiene_v1 import parse_date_flex


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


def run_gochara_v02_benchmark(target_n: int = 120):
    wrapper = EphemerisWrapper(ephemeris_path=str(REPO_ROOT / "data/ephemeris"))
    dasha_engine = DashaEngine(wrapper)
    karyesha_engine = KaryeshaEngine(wrapper)

    pristine_csv_path = REPO_ROOT / "data/shastric_rules/kundalee_pristine_full.csv"

    TIER_1_MDS = {"sun", "rahu", "jupiter"}

    triggers = [
        "G1_rahu_ketu_7h_1h_7l",
        "G2_rahu_ketu_1_7_axis",
        "G3_jup7h_rahu1h_synergy",
        "G4_mode_c_AND_G1",
        "G5_mode_c_AND_G2",
        "G6_mode_c_AND_G3",
    ]
    trigger_counts = {t: {"tp": 0, "fp": 0, "fn": 0, "tn": 0} for t in triggers}

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

                    seventh_rashi_idx = (lagna_idx + 6) % 12
                    seventh_lord_name = RASHI_LORDS[seventh_rashi_idx]
                    seventh_lord_d1_house = planets_info[seventh_lord_name].house_num_d1 if seventh_lord_name in planets_info else 7

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

                    # Positive Marriage Window
                    event_total += 1
                    md_lord = target_md.lord.lower()
                    ad_lord = target_ad.lord.lower()
                    ad_prof = profiles.get(ad_lord)

                    mode_c_pass = (
                        (18.0 <= age_years <= 65.0) and
                        (md_lord in TIER_1_MDS) and
                        (ad_prof and (ad_prof.is_primary_bhavesha or ad_prof.is_lord_sambandha or ad_prof.is_d9_karyesha))
                    )

                    # Date-wise Transit at noon UTC
                    e_dt_utc = datetime(e_date.year, e_date.month, e_date.day, 12, 0, 0, tzinfo=timezone.utc)
                    try:
                        transit_ephem = wrapper.calculate(e_dt_utc, lat, lon, ayanamsa="lahiri")
                    except Exception:
                        continue

                    t_jup_lon = None
                    t_rahu_lon = None
                    t_ketu_lon = None
                    for p in transit_ephem.planet_positions:
                        pn = p.planet.lower()
                        if pn == "jupiter":
                            t_jup_lon = p.sidereal_longitude
                        elif pn in ("rahu", "mean_node", "true_node"):
                            t_rahu_lon = p.sidereal_longitude
                        elif pn == "ketu":
                            t_ketu_lon = p.sidereal_longitude

                    if t_rahu_lon is None:
                        continue
                    if t_ketu_lon is None:
                        t_ketu_lon = (t_rahu_lon + 180.0) % 360.0

                    # Transit house relative to Natal Lagna
                    rahu_house = ((int(t_rahu_lon / 30.0) - lagna_idx) % 12) + 1
                    ketu_house = ((int(t_ketu_lon / 30.0) - lagna_idx) % 12) + 1
                    jup_house = (((int(t_jup_lon / 30.0) - lagna_idx) % 12) + 1) if t_jup_lon is not None else 0

                    g1_hit = (rahu_house in (1, 7, seventh_lord_d1_house)) or (ketu_house in (1, 7, seventh_lord_d1_house))
                    g2_hit = (rahu_house == 1 and ketu_house == 7) or (rahu_house == 7 and ketu_house == 1)
                    g3_hit = (jup_house in (7, seventh_lord_d1_house)) and (rahu_house == 1)

                    # Update Positive hits
                    for t_name, is_hit in [
                        ("G1_rahu_ketu_7h_1h_7l", g1_hit),
                        ("G2_rahu_ketu_1_7_axis", g2_hit),
                        ("G3_jup7h_rahu1h_synergy", g3_hit),
                        ("G4_mode_c_AND_G1", mode_c_pass and g1_hit),
                        ("G5_mode_c_AND_G2", mode_c_pass and g2_hit),
                        ("G6_mode_c_AND_G3", mode_c_pass and g3_hit),
                    ]:
                        if is_hit:
                            trigger_counts[t_name]["tp"] += 1
                        else:
                            trigger_counts[t_name]["fn"] += 1

                    # Within-subject Controls
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
                        ctrl_mode_c_pass = (
                            (18.0 <= ctrl_age <= 65.0) and
                            (ctrl_md_lord in TIER_1_MDS) and
                            (ctrl_prof and (ctrl_prof.is_primary_bhavesha or ctrl_prof.is_lord_sambandha or ctrl_prof.is_d9_karyesha))
                        )

                        # Transit at control date
                        ctrl_dt_utc = datetime(ctrl_date.year, ctrl_date.month, ctrl_date.day, 12, 0, 0, tzinfo=timezone.utc)
                        try:
                            c_transit_ephem = wrapper.calculate(ctrl_dt_utc, lat, lon, ayanamsa="lahiri")
                        except Exception:
                            continue

                        c_jup_lon = None
                        c_rahu_lon = None
                        c_ketu_lon = None
                        for p in c_transit_ephem.planet_positions:
                            pn = p.planet.lower()
                            if pn == "jupiter":
                                c_jup_lon = p.sidereal_longitude
                            elif pn in ("rahu", "mean_node", "true_node"):
                                c_rahu_lon = p.sidereal_longitude
                            elif pn == "ketu":
                                c_ketu_lon = p.sidereal_longitude

                        if c_rahu_lon is None:
                            continue
                        if c_ketu_lon is None:
                            c_ketu_lon = (c_rahu_lon + 180.0) % 360.0

                        c_rahu_house = ((int(c_rahu_lon / 30.0) - lagna_idx) % 12) + 1
                        c_ketu_house = ((int(c_ketu_lon / 30.0) - lagna_idx) % 12) + 1
                        c_jup_house = (((int(c_jup_lon / 30.0) - lagna_idx) % 12) + 1) if c_jup_lon is not None else 0

                        c_g1_hit = (c_rahu_house in (1, 7, seventh_lord_d1_house)) or (c_ketu_house in (1, 7, seventh_lord_d1_house))
                        c_g2_hit = (c_rahu_house == 1 and c_ketu_house == 7) or (c_rahu_house == 7 and c_ketu_house == 1)
                        c_g3_hit = (c_jup_house in (7, seventh_lord_d1_house)) and (c_rahu_house == 1)

                        for t_name, is_hit in [
                            ("G1_rahu_ketu_7h_1h_7l", c_g1_hit),
                            ("G2_rahu_ketu_1_7_axis", c_g2_hit),
                            ("G3_jup7h_rahu1h_synergy", c_g3_hit),
                            ("G4_mode_c_AND_G1", ctrl_mode_c_pass and c_g1_hit),
                            ("G5_mode_c_AND_G2", ctrl_mode_c_pass and c_g2_hit),
                            ("G6_mode_c_AND_G3", ctrl_mode_c_pass and c_g3_hit),
                        ]:
                            if is_hit:
                                trigger_counts[t_name]["fp"] += 1
                            else:
                                trigger_counts[t_name]["tn"] += 1

                    break

    print("=" * 80)
    print("ASTROOS GOCHARA-RULES-v0.2 BENCHMARK RESULTS")
    print(f"Sample: N_pos = {event_total}, N_neg = {control_total}, Total = {event_total + control_total}")
    print("=" * 80)

    trigger_descriptions = {
        "G1_rahu_ketu_7h_1h_7l": "Rahu/Ketu in 7H, Lagna, or 7th Lord House",
        "G2_rahu_ketu_1_7_axis": "Rahu-Ketu Exact Lagna-7H Axis (1H/7H)",
        "G3_jup7h_rahu1h_synergy": "Narrowed: Guru in 7H/7L AND Rahu in Lagna",
        "G4_mode_c_AND_G1": "Composite: Mode C (Exploratory) AND G1",
        "G5_mode_c_AND_G2": "Composite: Mode C (Exploratory) AND G2",
        "G6_mode_c_AND_G3": "Composite: Mode C (Exploratory) AND G3",
    }

    print("\n### GOCHARA-RULES-v0.2 PERFORMANCE MATRIX")
    print("| Trigger ID | Description | TP | FP | FN | TN | Recall (TPR) | FPR | Precision (PPV) | Lift | Chi2 (p-val) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")

    for t_name, desc in trigger_descriptions.items():
        st_counts = trigger_counts[t_name]
        stats = compute_contingency_stats(st_counts["tp"], st_counts["fp"], st_counts["fn"], st_counts["tn"])
        chi2_val = stats["chi2"]
        if chi2_val >= 6.63:
            p_str = f"chi2={chi2_val:.2f} (p<0.01)"
        elif chi2_val >= 3.84:
            p_str = f"chi2={chi2_val:.2f} (p<0.05)"
        else:
            p_str = f"chi2={chi2_val:.2f} (p>0.05)"

        print(
            f"| **`{t_name}`** | {desc} | {stats['tp']} | {stats['fp']} | {stats['fn']} | {stats['tn']} | "
            f"**{stats['recall']:.1f}%** ({stats['tp']}/{event_total}) | {stats['fpr']:.1f}% ({stats['fp']}/{control_total}) | "
            f"**{stats['precision']:.1f}%** | **{stats['lift']:.2f}x** | {p_str} |"
        )


if __name__ == "__main__":
    run_gochara_v02_benchmark(120)
