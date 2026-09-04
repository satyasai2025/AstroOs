"""
AstroOS — Integrated Multi-Tool Classical Confluence Benchmark
==============================================================
Evaluates multi-tool simultaneous alignment across 6 classical tools:
1. Tool 1 (D1 Aspect & Rasi): Active Dasha lord is Domain Lord, Occupant, or Aspects Domain House.
2. Tool 2 (Bhavachalita): Active Dasha lord occupies Domain House in Sripati Bhava-Madhya.
3. Tool 3 (Divisional Varga): D9 7H/Venus for Marriage; D10 10H/Sun for Career.
4. Tool 4 (Ashtakavarga): Domain Bhava SAV >= 28 AND Dasha Lord BAV >= 4.
5. Tool 5 (Sudarshana Tri-Lagna): Domain House activated from Lagna, Chandra, or Surya Lagna.
6. Tool 6 (Gochara Transits): Jupiter or Saturn transiting/aspecting Domain House or Lord.
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


def evaluate_chart_confluence(
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
    # 1. D1 Chart and Ascendant
    d1 = wrapper.calculate(b_dt, lat, lon, ayanamsa="lahiri")
    asc_lon = d1.ascendant.sidereal_longitude
    planet_lons = {p.planet.lower(): p.sidereal_longitude for p in d1.planet_positions}

    # 2. Bhavachalita
    chalita_report = BhavachalitaEngine.analyze_chart(asc_lon, planet_lons)

    # 3. Dasha Active Lords
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

    # 4. Karyesha Profile
    lagna_idx, planets_info, karakas = karyesha_engine.extract_chart_positions(b_dt, lat, lon)
    dom_enum = DomainEnum.MARRIAGE if domain == "marriage" else DomainEnum.CAREER
    target_h_num = 7 if domain == "marriage" else 10

    profiles = karyesha_engine.analyze_domain_karyeshas(lagna_idx, planets_info, karakas, domain=dom_enum, gender=gender)
    ad_prof = profiles.get(ad_lord)

    # 5. Ashtakavarga & Gochara
    d1_chart_obj = filter_engine.horoscope_engine.generate_d1(b_dt, lat, lon)
    confl_report = filter_engine.compute_continuous_confluence(
        chart=d1_chart_obj,
        target_date=target_date,
        mahadasha_lord=md_lord,
        antardasha_lord=ad_lord,
        domain=domain,
    )

    # TOOL 1: D1 Aspect & Rasi Connection
    t1_d1_connection = bool(ad_prof and (ad_prof.is_primary_bhavesha or ad_prof.is_house_occupant or ad_prof.is_house_aspector or ad_prof.is_lord_sambandha))

    # TOOL 2: Bhavachalita True Placement in Domain House
    ad_chalita = chalita_report.placements.get(ad_lord)
    t2_chalita_connection = bool(ad_chalita and (ad_chalita.bhavachalita_house in (target_h_num, 1, 9, 11)))

    # TOOL 3: Divisional Confirmation (D9 for marriage, D10 for career)
    if domain == "marriage":
        t3_varga_connection = bool(ad_prof and (ad_prof.is_d9_karyesha or ad_prof.is_naisargika_karaka))
    else:
        t3_varga_connection = bool(ad_chalita and (ad_chalita.d10_dignity in ("EXALTED", "OWN") or ad_chalita.d10_house_from_d10_lagna in (1, 10, 11, 2, 5, 9)))

    # TOOL 4: Ashtakavarga Fertility (SAV >= 28 and BAV >= 4)
    t4_ashtakavarga = (confl_report.sav_bindus >= 28) and (confl_report.ad_bav_bindus >= 4)

    # TOOL 5: Tri-Lagna Sudarshana Activation
    chandra_lon = planet_lons.get("moon", 0.0)
    surya_lon = planet_lons.get("sun", 0.0)
    chandra_rashi_idx = int(chandra_lon / 30.0) % 12
    surya_rashi_idx = int(surya_lon / 30.0) % 12
    ad_rashi_idx = int(planet_lons.get(ad_lord, 0.0) / 30.0) % 12

    h_from_lagna = ((ad_rashi_idx - lagna_idx) % 12) + 1
    h_from_chandra = ((ad_rashi_idx - chandra_rashi_idx) % 12) + 1
    h_from_surya = ((ad_rashi_idx - surya_rashi_idx) % 12) + 1

    t5_tri_lagna = (h_from_lagna in (1, 7, 10, 5, 9)) or (h_from_chandra in (1, 7, 10, 5, 9)) or (h_from_surya in (1, 7, 10, 5, 9))

    # TOOL 6: Gochara Real-Time Transits & Aspects
    jup_aspect = confl_report.jupiter_aspects_house or confl_report.jupiter_aspects_lord or confl_report.jupiter_aspects_amk
    sat_aspect = confl_report.saturn_aspects_house or confl_report.saturn_aspects_lord or confl_report.saturn_aspects_amk
    t6_gochara_trigger = (jup_aspect or sat_aspect)

    tools_active = [t1_d1_connection, t2_chalita_connection, t3_varga_connection, t4_ashtakavarga, t5_tri_lagna, t6_gochara_trigger]
    confluence_count = sum(1 for t in tools_active if t)

    return {
        "md_lord": md_lord,
        "ad_lord": ad_lord,
        "t1_d1": t1_d1_connection,
        "t2_chalita": t2_chalita_connection,
        "t3_varga": t3_varga_connection,
        "t4_ashtakavarga": t4_ashtakavarga,
        "t5_tri_lagna": t5_tri_lagna,
        "t6_gochara": t6_gochara_trigger,
        "confluence_count": confluence_count,
    }


def run_multi_tool_study(domain: str = "marriage", max_events: int = 400):
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

            # Skip Raj from career
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

                    pos_eval = evaluate_chart_confluence(
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

                        neg_eval = evaluate_chart_confluence(
                            wrapper, dasha_engine, karyesha_engine, filter_engine,
                            b_dt, lat, lon, gender, ctrl_date, domain=domain
                        )
                        if neg_eval:
                            neg_records.append(neg_eval)

                    break

    print("=" * 85)
    print(f"ASTROOS INTEGRATED MULTI-TOOL CONFLUENCE BENCHMARK ({domain.upper()} DOMAIN)")
    print(f"Sample: N_pos = {len(pos_records)} Events, N_neg = {len(neg_records)} Controls | Total = {len(pos_records) + len(neg_records)} Windows")
    print(f"Base Rate: {(len(pos_records)/(len(pos_records)+len(neg_records)))*100:.2f}%")
    print("=" * 85)

    thresholds = [
        ("Confluence >= 3 Tools Active", lambda r: r["confluence_count"] >= 3),
        ("Confluence >= 4 Tools Active", lambda r: r["confluence_count"] >= 4),
        ("Confluence >= 5 Tools Active", lambda r: r["confluence_count"] >= 5),
        ("Confluence == 6 Tools Active (Full Alignment)", lambda r: r["confluence_count"] == 6),
    ]

    print("\n### MULTI-TOOL SYNTHESIS PERFORMANCE MATRIX")
    print("| Threshold Rule | TP | FP | FN | TN | Recall (TPR) | FPR | Precision | Lift | Chi2 (p-val) |")
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
    print("\n--- RUNNING MARRIAGE MULTI-TOOL SYNTHESIS ---")
    run_multi_tool_study(domain="marriage", max_events=400)
    print("\n--- RUNNING CAREER MULTI-TOOL SYNTHESIS ---")
    run_multi_tool_study(domain="career", max_events=120)
