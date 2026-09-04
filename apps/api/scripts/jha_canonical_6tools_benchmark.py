"""
AstroOS — Vinay Jha Canonical 6-Tool Prediction Benchmark
=========================================================
Strictly evaluates Vinay Jha's exact 6 canonical tools from docs/CANONICAL_PREDICTION_FRAMEWORK.md:
1. Jha Tool 1: SSS Bhavachalita House connection (Bhava-Madhya 7H/10H).
2. Jha Tool 2: Divisional Varga Confirmation (D9 for Marriage, D10 for Career).
3. Jha Tool 3: Jha Log-base-2 Main Strength (2^(Dignity-1) >= 32.0: Mitra, Own, Exalted).
4. Jha Tool 4: Sudarshana Tri-Lagna Synthesis (Lagna + Chandra + Surya Kundali Net Positive).
5. Jha Tool 5: Bhavottama Detection (Same Bhava across D1 and Divisional).
6. Jha Tool 6: Ashtakavarga Rekhas (SAV >= 28, BAV >= 4) + Gochara Transit Trigger.

Evaluates Jha's rule:
- 3+ Layers confirming = Reasonable prediction
- 5+ Layers confirming = High confidence prediction
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
from apps.api.services.phalita_core.bhavottama_engine import BhavottamaEngine
from apps.api.services.phalita_core.classical_filter_engine import ClassicalFilterEngine
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
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "total_pos": total_pos, "total_neg": total_neg,
        "tpr": tpr, "fpr": fpr, "precision": precision,
        "recall": recall, "lift": lift, "f1": f1, "chi2": chi2,
    }


def compute_jha_main_strength(planet_name: str, rashi_idx: int) -> float:
    """Computes Jha Log-base-2 Strength: 2^(Dignity - 1) from 1.0 to 256.0."""
    p = planet_name.lower()
    EXALT = {"sun": 0, "moon": 1, "mars": 9, "mercury": 5, "jupiter": 3, "venus": 11, "saturn": 6, "rahu": 1, "ketu": 7}
    DEBIL = {"sun": 6, "moon": 7, "mars": 3, "mercury": 11, "jupiter": 9, "venus": 5, "saturn": 0, "rahu": 7, "ketu": 1}
    OWN = {"sun": {4}, "moon": {3}, "mars": {0, 7}, "mercury": {2, 5}, "jupiter": {8, 11}, "venus": {1, 6}, "saturn": {9, 10}, "rahu": {10}, "ketu": {7}}

    if p in EXALT and EXALT[p] == rashi_idx:
        dignity = 9  # Exalted
    elif p in OWN and rashi_idx in OWN[p]:
        dignity = 7  # Own Sign
    elif p in DEBIL and DEBIL[p] == rashi_idx:
        dignity = 1  # Debilitated
    else:
        dignity = 5  # Mitra / Neutral

    return 2.0 ** (dignity - 1)


def evaluate_jha_confluence(
    wrapper: EphemerisWrapper,
    dasha_engine: DashaEngine,
    karyesha_engine: KaryeshaEngine,
    filter_engine: ClassicalFilterEngine,
    b_dt: datetime,
    lat: float,
    lon: float,
    gender: str,
    target_date: date,
    domain: str = "marriage",
) -> Dict[str, Any]:
    # 1. Ephemeris & D1
    d1 = wrapper.calculate(b_dt, lat, lon, ayanamsa="lahiri")
    asc_lon = d1.ascendant.sidereal_longitude
    planet_lons = {p.planet.lower(): p.sidereal_longitude for p in d1.planet_positions}

    # 2. Bhavachalita
    chalita_report = BhavachalitaEngine.analyze_chart(asc_lon, planet_lons)

    # 3. Active Dasha Lords
    dtree = dasha_engine.compute_vimshottari(b_dt, lat, lon, ayanamsa="lahiri", max_depth=2)
    target_md = None
    target_ad = None
    for md in dtree.mahadashas:
        if md.contains(target_date):
            target_md = md
            for ad in md.sub_periods:
                if ad.contains(target_date):
                    target_ad = ad
                    break
            break

    if not target_md or not target_ad:
        return None

    md_lord = target_md.lord.lower()
    ad_lord = target_ad.lord.lower()

    # 4. Karyesha & Divisional
    lagna_idx, planets_info, karakas = karyesha_engine.extract_chart_positions(b_dt, lat, lon)
    dom_enum = DomainEnum.MARRIAGE if domain == "marriage" else DomainEnum.CAREER
    target_h_num = 7 if domain == "marriage" else 10

    profiles = karyesha_engine.analyze_domain_karyeshas(lagna_idx, planets_info, karakas, domain=dom_enum, gender=gender)
    ad_prof = profiles.get(ad_lord)
    ad_chalita = chalita_report.placements.get(ad_lord)

    d1_chart_obj = filter_engine.horoscope_engine.generate_d1(b_dt, lat, lon)
    confl_report = filter_engine.compute_continuous_confluence(
        chart=d1_chart_obj, target_date=target_date, mahadasha_lord=md_lord, antardasha_lord=ad_lord, domain=domain
    )

    # JHA TOOL 1: SSS Bhavachalita Placement (True Bhava-Madhya 7H/10H or 1H/11H)
    t1_bhavachalita = bool(ad_chalita and (ad_chalita.bhavachalita_house in (target_h_num, 1, 11, 9)))

    # JHA TOOL 2: Divisional Varga Confirmation (D9 for Marriage, D10 for Career)
    if domain == "marriage":
        t2_varga = bool(ad_prof and (ad_prof.is_d9_karyesha or ad_prof.is_naisargika_karaka))
    else:
        t2_varga = bool(ad_chalita and (ad_chalita.d10_dignity in ("EXALTED", "OWN") or ad_chalita.d10_house_from_d10_lagna in (1, 10, 11)))

    # JHA TOOL 3: Jha Log-base-2 Main Strength >= 32.0 (Mitra, Own, Exalted)
    ad_rashi_idx = int(planet_lons.get(ad_lord, 0.0) / 30.0) % 12
    main_strength = compute_jha_main_strength(ad_lord, ad_rashi_idx)
    t3_main_strength = (main_strength >= 32.0)

    # JHA TOOL 4: Sudarshana Tri-Lagna Synthesis (Lagna + Chandra + Surya)
    chandra_lon = planet_lons.get("moon", 0.0)
    surya_lon = planet_lons.get("sun", 0.0)
    chandra_rashi_idx = int(chandra_lon / 30.0) % 12
    surya_rashi_idx = int(surya_lon / 30.0) % 12

    h_from_lagna = ((ad_rashi_idx - lagna_idx) % 12) + 1
    h_from_chandra = ((ad_rashi_idx - chandra_rashi_idx) % 12) + 1
    h_from_surya = ((ad_rashi_idx - surya_rashi_idx) % 12) + 1
    t4_sudarshana = (h_from_lagna in (1, 7, 10, 5, 9)) or (h_from_chandra in (1, 7, 10, 5, 9)) or (h_from_surya in (1, 7, 10, 5, 9))

    # JHA TOOL 5: Bhavottama Detection (Same Bhava across D1 and Divisional)
    d1_bhava = ad_chalita.bhavachalita_house if ad_chalita else h_from_lagna
    d_varga_bhava = ad_chalita.d10_house_from_d10_lagna if (domain == "career" and ad_chalita) else h_from_lagna
    t5_bhavottama = (d1_bhava == d_varga_bhava)

    # JHA TOOL 6: Ashtakavarga Rekhas (SAV >= 28) + Real Gochara Transit Trigger
    jup_aspect = confl_report.jupiter_aspects_house or confl_report.jupiter_aspects_lord or confl_report.jupiter_aspects_amk
    sat_aspect = confl_report.saturn_aspects_house or confl_report.saturn_aspects_lord or confl_report.saturn_aspects_amk
    t6_av_transit = (confl_report.sav_bindus >= 28) and (jup_aspect or sat_aspect)

    jha_tools = [t1_bhavachalita, t2_varga, t3_main_strength, t4_sudarshana, t5_bhavottama, t6_av_transit]
    jha_active_count = sum(1 for t in jha_tools if t)

    return {
        "md_lord": md_lord,
        "ad_lord": ad_lord,
        "t1_bhavachalita": t1_bhavachalita,
        "t2_varga": t2_varga,
        "t3_main_strength": t3_main_strength,
        "t4_sudarshana": t4_sudarshana,
        "t5_bhavottama": t5_bhavottama,
        "t6_av_transit": t6_av_transit,
        "active_layers": jha_active_count,
    }


def run_jha_benchmark(domain: str = "marriage", max_events: int = 400):
    wrapper = EphemerisWrapper(ephemeris_path=str(REPO_ROOT / "data/ephemeris"))
    dasha_engine = DashaEngine(wrapper)
    karyesha_engine = KaryeshaEngine(wrapper)
    filter_engine = ClassicalFilterEngine(ephemeris_path=str(REPO_ROOT / "data/ephemeris"))

    pristine_csv_path = REPO_ROOT / "data/shastric_rules/kundalee_pristine_full.csv"

    pos_records: List[Dict[str, Any]] = []
    neg_records: List[Dict[str, Any]] = []

    collected_events = 0

    with pristine_csv_path.open("r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if collected_events >= max_events:
                break

            gender = row.get("gender", "Male")
            rodden = row.get("rodden_rating", "").strip()
            if rodden not in ("AA", "A"):
                continue

            b_dt_str = row.get("birth_dt_utc", "")
            if not b_dt_str:
                continue

            if domain == "career" and ("1971-06-30" in b_dt_str or "1971-06-29" in b_dt_str):
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

                is_match = ("marriage" in ev_type) if domain == "marriage" else (any(k in ev_type for k in ("job change", "awards", "promotion", "politics", "career")))

                if is_match and ev_date_str:
                    e_date = parse_date_flex(ev_date_str)
                    if not e_date:
                        continue

                    age_years = (e_date - b_dt.date()).days / 365.25
                    if age_years < 18.0 or age_years > 65.0:
                        continue

                    pos_eval = evaluate_jha_confluence(
                        wrapper, dasha_engine, karyesha_engine, filter_engine,
                        b_dt, lat, lon, gender, e_date, domain=domain
                    )
                    if not pos_eval:
                        continue

                    collected_events += 1
                    pos_records.append(pos_eval)

                    # Symmetric Controls [-6, -3, +3, +6]
                    for offset in [-6, -3, 3, 6]:
                        ctrl_date = safe_year_offset(e_date, offset)
                        ctrl_age = (ctrl_date - b_dt.date()).days / 365.25
                        if ctrl_age < 18.0 or ctrl_age > 65.0:
                            continue

                        neg_eval = evaluate_jha_confluence(
                            wrapper, dasha_engine, karyesha_engine, filter_engine,
                            b_dt, lat, lon, gender, ctrl_date, domain=domain
                        )
                        if neg_eval:
                            neg_records.append(neg_eval)

                    break

    print("=" * 85)
    print(f"VINAY JHA CANONICAL 6-TOOL SYNTHESIS BENCHMARK ({domain.upper()} DOMAIN)")
    print(f"Sample: N_pos = {len(pos_records)} Events, N_neg = {len(neg_records)} Controls | Total = {len(pos_records) + len(neg_records)} Windows")
    print(f"Base Rate: {(len(pos_records)/(len(pos_records)+len(neg_records)))*100:.2f}%")
    print("=" * 85)

    thresholds = [
        ("Jha Step 10: >= 2 Layers Confirming", lambda r: r["active_layers"] >= 2),
        ("Jha Step 10: >= 3 Layers Confirming (Reasonable)", lambda r: r["active_layers"] >= 3),
        ("Jha Step 10: >= 4 Layers Confirming", lambda r: r["active_layers"] >= 4),
        ("Jha Step 10: >= 5 Layers Confirming (High Confidence)", lambda r: r["active_layers"] >= 5),
        ("Jha Step 10: 6 Layers Full Alignment", lambda r: r["active_layers"] == 6),
    ]

    print("\n### JHA STEP 10 SYNTHESIS PERFORMANCE MATRIX")
    print("| Jha Threshold Rule | TP | FP | FN | TN | Recall (TPR) | FPR | Precision | Lift | Chi2 (p-val) |")
    print("|---|---|---|---|---|---|---|---|---|---|")

    for t_name, check_fn in thresholds:
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
        if chi2_val >= 10.83:
            p_str = f"chi2={chi2_val:.2f} (p<0.001)"
        elif chi2_val >= 6.63:
            p_str = f"chi2={chi2_val:.2f} (p<0.01)"
        elif chi2_val >= 3.84:
            p_str = f"chi2={chi2_val:.2f} (p<0.05)"
        else:
            p_str = f"chi2={chi2_val:.2f} (p>0.05)"

        print(
            f"| **{t_name}** | {st['tp']} | {st['fp']} | {st['fn']} | {st['tn']} | "
            f"**{st['tpr']:.1f}%** ({st['tp']}/{len(pos_records)}) | {st['fpr']:.1f}% ({st['fp']}/{len(neg_records)}) | "
            f"**{st['precision']:.1f}%** | **{st['lift']:.2f}x** | {p_str} |"
        )


if __name__ == "__main__":
    print("\n--- RUNNING JHA 6-TOOL MARRIAGE BENCHMARK ---")
    run_jha_benchmark(domain="marriage", max_events=400)
    print("\n--- RUNNING JHA 6-TOOL CAREER BENCHMARK ---")
    run_jha_benchmark(domain="career", max_events=120)
