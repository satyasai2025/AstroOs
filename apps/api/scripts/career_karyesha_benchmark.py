"""
AstroOS — Career Domain Empirical Benchmark (D10 Dignity, Bhava-Sandhi & Karyesha)
==================================================================================
Pre-Registered Hypotheses:
- C1: D10 Debilitation of Period Lord (MD or AD) in Career Event vs Controls.
- C2: Bhava-Sandhi Displacement (BHAVA-SANDHI-RULES-v0.1: Asc_deg <= 2.0° or >= 28.0°) of 10L / Period Lord.
- C3: D10 Dussthana (6H / 8H / 12H from D10 Lagna) placement of Period Lord.
- C4: D10 Exalted / Own Sign placement of Period Lord.
- C5: 10th Lord OR Amatya Karaka (AmK) active in Dasha (Primary Career Karyesha).

Methodological Invariants:
1. Raj is 100% EXCLUDED from this calibration cohort.
2. Symmetric within-subject control offsets: [-6, -3, +3, +6] years.
3. AA / A Rodden-rated pristine records only.
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
from apps.api.services.karyesha_engine import KaryeshaEngine, DomainEnum, RASHI_LORDS
from apps.api.services.bhavachalita_engine import BhavachalitaEngine
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


def run_career_benchmark(target_n: int = 120):
    wrapper = EphemerisWrapper(ephemeris_path=str(REPO_ROOT / "data/ephemeris"))
    dasha_engine = DashaEngine(wrapper)
    karyesha_engine = KaryeshaEngine(wrapper)

    pristine_csv_path = REPO_ROOT / "data/shastric_rules/kundalee_pristine_full.csv"

    # Career event keywords in dataset
    career_types = {"job change", "awards", "promotion", "politics", "career"}

    pos_records: List[Dict[str, Any]] = []
    neg_records: List[Dict[str, Any]] = []

    event_total = 0
    control_total = 0

    with pristine_csv_path.open("r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if event_total >= target_n:
                break

            # STRICT INVARIANT 1: EXCLUDE RAJ COMPLETELY (Zero Leakage)
            b_dt_str = row.get("birth_dt_utc", "")
            if "1971-06-30" in b_dt_str or "1971-06-29" in b_dt_str:
                lat_str = row.get("latitude", "")
                if "22.3" in lat_str:
                    continue

            gender = row.get("gender", "Male")
            rodden = row.get("rodden_rating", "")
            if rodden not in ("AA", "A"):
                continue

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

                is_career_event = any(ct in ev_type for ct in career_types)
                if is_career_event and ev_date_str:
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
                        planet_lons = {p_name: p.sidereal_lon for p_name, p in planets_info.items()}
                        d1 = wrapper.calculate(b_dt, lat, lon, ayanamsa="lahiri")
                        asc_lon = d1.ascendant.sidereal_longitude
                        chalita_report = BhavachalitaEngine.analyze_chart(asc_lon, planet_lons)
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

                    tenth_rashi_idx = (lagna_idx + 9) % 12
                    tenth_lord = RASHI_LORDS[tenth_rashi_idx]
                    amk_planet = karakas.amatya_karaka.lower()

                    ad_chalita = chalita_report.placements.get(ad_lord)
                    tenth_chalita = chalita_report.placements.get(tenth_lord)

                    pos_rec = {
                        "subject_id": row.get("name", f"subj_{event_total}"),
                        "event_type": ev_type,
                        "age": age_years,
                        "md_lord": md_lord,
                        "ad_lord": ad_lord,
                        "c1_d10_debilitated": (ad_chalita.d10_dignity == "DEBILITATED") if ad_chalita else False,
                        "c2_bhava_sandhi": chalita_report.is_bhava_sandhi and ((ad_chalita and ad_chalita.is_displaced) or (tenth_chalita and tenth_chalita.is_displaced)),
                        "c3_d10_dussthana": (ad_chalita.d10_house_from_d10_lagna in (6, 8, 12)) if ad_chalita else False,
                        "c4_d10_strong": (ad_chalita.d10_dignity in ("EXALTED", "OWN") or (ad_chalita and ad_chalita.d10_house_from_d10_lagna in (1, 2, 4, 7, 10, 11))) if ad_chalita else False,
                        "c5_10L_or_AmK_active": (ad_lord in (tenth_lord, amk_planet)) or (md_lord in (tenth_lord, amk_planet)),
                    }
                    pos_records.append(pos_rec)

                    # STRICT INVARIANT 2: Symmetric Control Offsets [-6, -3, +3, +6]
                    offsets_years = [-6, -3, 3, 6]
                    for offset in offsets_years:
                        ctrl_date = e_date.replace(year=e_date.year + offset)
                        ctrl_age = (ctrl_date - b_dt.date()).days / 365.25
                        if ctrl_age < 18.0 or ctrl_age > 75.0:
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
                        c_ad_chalita = chalita_report.placements.get(ctrl_ad_lord)

                        neg_rec = {
                            "subject_id": row.get("name", f"subj_{event_total}"),
                            "age": ctrl_age,
                            "md_lord": ctrl_md_lord,
                            "ad_lord": ctrl_ad_lord,
                            "c1_d10_debilitated": (c_ad_chalita.d10_dignity == "DEBILITATED") if c_ad_chalita else False,
                            "c2_bhava_sandhi": chalita_report.is_bhava_sandhi and ((c_ad_chalita and c_ad_chalita.is_displaced) or (tenth_chalita and tenth_chalita.is_displaced)),
                            "c3_d10_dussthana": (c_ad_chalita.d10_house_from_d10_lagna in (6, 8, 12)) if c_ad_chalita else False,
                            "c4_d10_strong": (c_ad_chalita.d10_dignity in ("EXALTED", "OWN") or (c_ad_chalita and c_ad_chalita.d10_house_from_d10_lagna in (1, 2, 4, 7, 10, 11))) if c_ad_chalita else False,
                            "c5_10L_or_AmK_active": (ctrl_ad_lord in (tenth_lord, amk_planet)) or (ctrl_md_lord in (tenth_lord, amk_planet)),
                        }
                        neg_records.append(neg_rec)

                    break

    print("=" * 85)
    print(f"ASTROOS CAREER-COHORT EMPIRICAL BENCHMARK (N_pos = {len(pos_records)}, N_neg = {len(neg_records)}, Total = {len(pos_records) + len(neg_records)})")
    print("Methodological Note: Raj is 100% EXCLUDED from this calibration cohort.")
    print("Symmetric Control Offsets: [-6, -3, +3, +6] years.")
    print("=" * 85)

    hypotheses = [
        ("C1_d10_debilitation", "Hypothesis C1: Period Lord Debilitated in D10", lambda r: r["c1_d10_debilitated"]),
        ("C2_bhava_sandhi_displacement", "Hypothesis C2: Bhava-Sandhi (<=2° or >=28°) Displaced Lord", lambda r: r["c2_bhava_sandhi"]),
        ("C3_d10_dussthana", "Hypothesis C3: Period Lord in D10 Dussthana (6H/8H/12H)", lambda r: r["c3_d10_dussthana"]),
        ("C4_d10_kendra_or_exalted", "Hypothesis C4: Period Lord Strong in D10 (Exalted/Own/Kendra/2H)", lambda r: r["c4_d10_strong"]),
        ("C5_10L_or_AmK_active", "Hypothesis C5: 10th Lord OR Amatya Karaka (AmK) in Dasha", lambda r: r["c5_10L_or_AmK_active"]),
    ]

    print("\n### CAREER HYPOTHESIS CONTINGENCY MATRIX & EMPIRICAL LIFTS")
    print("| Hypothesis ID | Rule Description | TP | FP | FN | TN | TPR (Recall) | FPR | Precision | Lift | Chi2 (p-val) | Status Verdict |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")

    for h_id, desc, check_fn in hypotheses:
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

        lift_val = st["lift"]
        if lift_val > 1.30 and (chi2_val >= 3.84):
            status_verdict = "**CONFIRMED TRIGGER**"
        elif lift_val <= 1.10 or chi2_val < 3.84:
            status_verdict = "**DESCRIPTIVE ONLY (NO TRIGGER)**"
        else:
            status_verdict = "MARGINAL / UNCONFIRMED"

        print(
            f"| **`{h_id}`** | {desc} | {st['tp']} | {st['fp']} | {st['fn']} | {st['tn']} | "
            f"**{st['tpr']:.1f}%** ({st['tp']}/{len(pos_records)}) | {st['fpr']:.1f}% ({st['fp']}/{len(neg_records)}) | "
            f"**{st['precision']:.1f}%** | **{st['lift']:.2f}x** | {p_str} | {status_verdict} |"
        )


if __name__ == "__main__":
    run_career_benchmark(120)
