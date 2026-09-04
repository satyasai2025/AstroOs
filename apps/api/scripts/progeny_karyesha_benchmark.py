"""
AstroOS — Childbirth & Progeny Multi-Tool Empirical Benchmark Suite
===================================================================
Evaluates all available verified Childbirth events (AA/A Rodden-rated)
along with symmetric within-subject negative controls (Offsets: [-6, -3, +3, +6] years).

Pre-Registered Classical Tools for Progeny (सन्तति विचार):
- Backbone: Active Vimshottari Dasha (MD -> AD).
- Tool 1 (D1 5th House): Dasha Lord rules 5H, occupies 5H, or aspects 5H / 5L.
- Tool 2 (Bhavachalita 5H): Dasha Lord occupies 5th Bhava-Madhya (or 1H, 9H, 11H).
- Tool 3 (D7 Saptamsha): Dasha Lord is D7 5th Lord or in D7 5th House / D7 Lagna.
- Tool 4 (Karaka Dasha): Active Dasha is Jupiter (Naisargika Putrakaraka) OR Jaimini PK (5th Karaka).
- Tool 5 (Ashtakavarga 5H): 5th House SAV >= 28 AND AD Lord BAV >= 4.
- Tool 6 (Sudarshana Tri-Lagna 5H): 5th House triggered from Lagna, Chandra, or Surya Lagna.
- Tool 7 (Gochara Double Transit): Jupiter or Saturn transiting/aspecting 5th House or 5th Lord.
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


def compute_d7_rashi_index(lon_deg: float) -> int:
    sign_idx = int(lon_deg / 30.0) % 12
    part_idx = int((lon_deg % 30.0) / (30.0 / 7.0))
    if part_idx > 6:
        part_idx = 6

    if sign_idx % 2 == 0:  # Odd sign (0=Aries, 2=Gemini...)
        return (sign_idx + part_idx) % 12
    else:  # Even sign (1=Taurus, 3=Cancer...)
        return (sign_idx + 6 + part_idx) % 12


def evaluate_progeny_confluence(
    wrapper: EphemerisWrapper,
    dasha_engine: DashaEngine,
    karyesha_engine: KaryeshaEngine,
    filter_engine: ClassicalFilterEngine,
    b_dt: datetime,
    lat: float,
    lon: float,
    gender: str,
    target_date: date,
) -> Dict[str, Any]:
    # 1. D1 Chart and Ascendant
    d1 = wrapper.calculate(b_dt, lat, lon, ayanamsa="lahiri")
    asc_lon = d1.ascendant.sidereal_longitude
    lagna_rashi_idx = int(asc_lon / 30.0) % 12
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

    # 4. 5th House and Karakas
    fifth_rashi_idx = (lagna_rashi_idx + 4) % 12
    fifth_lord = RASHI_LORDS[fifth_rashi_idx]
    karakas = karyesha_engine.calculate_chara_karakas(planet_lons)
    pk_planet = getattr(karakas, "pitri_karaka", "jupiter").lower()

    # Tool 1: D1 5th House Connection
    ad_d1_house = ((int(planet_lons.get(ad_lord, 0.0) / 30.0) % 12 - lagna_rashi_idx) % 12) + 1
    fifth_lord_house = ((int(planet_lons.get(fifth_lord, 0.0) / 30.0) % 12 - lagna_rashi_idx) % 12) + 1
    aspected_by_ad = karyesha_engine.get_parashari_aspect_houses(ad_lord, ad_d1_house)

    t1_d1_5h = (
        (ad_lord == fifth_lord) or
        (ad_d1_house == 5) or
        (5 in aspected_by_ad) or
        (ad_d1_house == fifth_lord_house) or
        (fifth_lord_house in aspected_by_ad)
    )

    # Tool 2: Bhavachalita 5th House
    ad_chalita = chalita_report.placements.get(ad_lord)
    t2_chalita_5h = bool(ad_chalita and (ad_chalita.bhavachalita_house in (5, 1, 9, 11)))

    # Tool 3: D7 Saptamsha
    d7_lagna_rashi = compute_d7_rashi_index(asc_lon)
    d7_fifth_rashi = (d7_lagna_rashi + 4) % 12
    d7_fifth_lord = RASHI_LORDS[d7_fifth_rashi]
    ad_d7_rashi = compute_d7_rashi_index(planet_lons.get(ad_lord, 0.0))
    ad_d7_house = ((ad_d7_rashi - d7_lagna_rashi) % 12) + 1

    t3_d7_saptamsha = (
        (ad_lord == d7_fifth_lord) or
        (ad_d7_house in (5, 1, 9)) or
        (ad_d7_rashi == d7_fifth_rashi)
    )

    # Tool 4: Karaka Dasha (Jupiter Naisargika or Jaimini PK)
    t4_karaka = (ad_lord in ("jupiter", "guru", pk_planet)) or (md_lord in ("jupiter", "guru", pk_planet))

    # Tool 5: Ashtakavarga 5H Fertility (SAV >= 28 on 5H, BAV >= 4 for AD lord)
    d1_chart_obj = filter_engine.horoscope_engine.generate_d1(b_dt, lat, lon)
    sav_res = filter_engine.ashtakavarga_engine.compute_sarvashtakavarga(d1_chart_obj)
    sav_5h = sav_res.bindus_from_lagna(d1_chart_obj.ascendant.rashi.lower(), 5)
    bhav_list = filter_engine.ashtakavarga_engine.compute_bhinnashtakavarga(d1_chart_obj)
    bav_map = {b.target_planet.lower(): b for b in bhav_list}
    ad_rashi_name = d1_chart_obj.planets[0].rashi.lower()
    for p in d1_chart_obj.planets:
        if p.planet.lower() == ad_lord:
            ad_rashi_name = p.rashi.lower()
            break
    ad_bav = bav_map[ad_lord].bindus_in_rashi(ad_rashi_name) if ad_lord in bav_map else 4
    t5_ashtakavarga = (sav_5h >= 28) and (ad_bav >= 4)

    # Tool 6: Sudarshana Tri-Lagna 5H Activation
    chandra_lon = planet_lons.get("moon", 0.0)
    surya_lon = planet_lons.get("sun", 0.0)
    chandra_rashi_idx = int(chandra_lon / 30.0) % 12
    surya_rashi_idx = int(surya_lon / 30.0) % 12
    ad_rashi_idx = int(planet_lons.get(ad_lord, 0.0) / 30.0) % 12

    h_from_lagna = ((ad_rashi_idx - lagna_rashi_idx) % 12) + 1
    h_from_chandra = ((ad_rashi_idx - chandra_rashi_idx) % 12) + 1
    h_from_surya = ((ad_rashi_idx - surya_rashi_idx) % 12) + 1
    t6_tri_lagna = (h_from_lagna in (5, 1, 9)) or (h_from_chandra in (5, 1, 9)) or (h_from_surya in (5, 1, 9))

    # Tool 7: Gochara Real-Time Transits (Jupiter/Saturn aspecting 5H or 5L)
    confl_report = filter_engine.compute_continuous_confluence(
        chart=d1_chart_obj, target_date=target_date, mahadasha_lord=md_lord, antardasha_lord=ad_lord, domain="progeny"
    )
    jup_aspect = confl_report.jupiter_aspects_house or confl_report.jupiter_aspects_lord or confl_report.jupiter_aspects_amk
    sat_aspect = confl_report.saturn_aspects_house or confl_report.saturn_aspects_lord or confl_report.saturn_aspects_amk
    t7_gochara = (jup_aspect or sat_aspect)

    tools = [t1_d1_5h, t2_chalita_5h, t3_d7_saptamsha, t4_karaka, t5_ashtakavarga, t6_tri_lagna, t7_gochara]
    confluence_count = sum(1 for t in tools if t)

    return {
        "md_lord": md_lord,
        "ad_lord": ad_lord,
        "t1_d1_5h": t1_d1_5h,
        "t2_chalita_5h": t2_chalita_5h,
        "t3_d7_saptamsha": t3_d7_saptamsha,
        "t4_karaka": t4_karaka,
        "t5_ashtakavarga": t5_ashtakavarga,
        "t6_tri_lagna": t6_tri_lagna,
        "t7_gochara": t7_gochara,
        "confluence_count": confluence_count,
    }


def run_progeny_benchmark(target_n: int = 748):
    wrapper = EphemerisWrapper(ephemeris_path=str(REPO_ROOT / "data/ephemeris"))
    dasha_engine = DashaEngine(wrapper)
    karyesha_engine = KaryeshaEngine(wrapper)
    filter_engine = ClassicalFilterEngine(ephemeris_path=str(REPO_ROOT / "data/ephemeris"))

    pristine_csv_path = REPO_ROOT / "data/shastric_rules/kundalee_pristine_full.csv"

    pos_records: List[Dict[str, Any]] = []
    neg_records: List[Dict[str, Any]] = []

    md_distribution_pos = defaultdict(int)
    md_distribution_neg = defaultdict(int)

    collected_events = 0

    with pristine_csv_path.open("r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if collected_events >= target_n:
                break

            gender = row.get("gender", "Female")
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

                if "child birth" in ev_type and ev_date_str:
                    e_date = parse_date_flex(ev_date_str)
                    if not e_date:
                        continue

                    age_years = (e_date - b_dt.date()).days / 365.25
                    if age_years < 16.0 or age_years > 55.0:
                        continue

                    pos_eval = evaluate_progeny_confluence(
                        wrapper, dasha_engine, karyesha_engine, filter_engine,
                        b_dt, lat, lon, gender, e_date
                    )
                    if not pos_eval:
                        continue

                    collected_events += 1
                    pos_records.append(pos_eval)
                    md_distribution_pos[pos_eval["md_lord"]] += 1

                    # Symmetric Controls [-6, -3, +3, +6]
                    for offset in [-6, -3, 3, 6]:
                        ctrl_date = safe_year_offset(e_date, offset)
                        ctrl_age = (ctrl_date - b_dt.date()).days / 365.25
                        if ctrl_age < 16.0 or ctrl_age > 55.0:
                            continue

                        neg_eval = evaluate_progeny_confluence(
                            wrapper, dasha_engine, karyesha_engine, filter_engine,
                            b_dt, lat, lon, gender, ctrl_date
                        )
                        if neg_eval:
                            neg_records.append(neg_eval)
                            md_distribution_neg[neg_eval["md_lord"]] += 1

                    break

    print("=" * 85)
    print(f"ASTROOS CHILDBIRTH & PROGENY EMPIRICAL BENCHMARK (N_pos = {len(pos_records)}, N_neg = {len(neg_records)})")
    print(f"Total Evaluated Sample: {len(pos_records) + len(neg_records)} Windows | Base Rate: {(len(pos_records)/(len(pos_records)+len(neg_records)))*100:.2f}%")
    print("=" * 85)

    # 1. Mahadasha Distribution
    print("\n### 1. HYPOTHESIS P1: MAHADASHA (MD) DISTRIBUTION IN CHILDBIRTH")
    print("| MD Planet | Positive Hits (n={}) | % Pos | Control Hits (n={}) | % Neg | Empirical Lift | Theoretical Lift (Years/120) |".format(len(pos_records), len(neg_records)))
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

    # 2. Individual Classical Tools Contingency Matrix
    print("\n### 2. INDIVIDUAL PROGENY TOOLS CONTINGENCY MATRIX (P2 - P6)")
    print("| Tool ID | Classical Mechanism Description | TPR (Recall) | FPR | Precision | Lift | Chi2 (p-val) |")
    print("|---|---|---|---|---|---|---|")

    single_tools = [
        ("P2_d1_5h", "Tool 1: D1 5th Lord, 5th Occupant, or 5H Drishti in Dasha", lambda r: r["t1_d1_5h"]),
        ("P3_chalita_5h", "Tool 2: Bhavachalita 5th House (Bhava-Madhya 5H/1H/9H/11H)", lambda r: r["t2_chalita_5h"]),
        ("P4_d7_saptamsha", "Tool 3: D7 Saptamsha 5th Lord or D7 5th House / Lagna", lambda r: r["t3_d7_saptamsha"]),
        ("P5_karaka_dasha", "Tool 4: Jupiter (Putrakaraka) OR Jaimini PK active in Dasha", lambda r: r["t4_karaka"]),
        ("P6_ashtakavarga", "Tool 5: 5th House SAV >= 28 AND AD Lord BAV >= 4", lambda r: r["t5_ashtakavarga"]),
        ("P7_tri_lagna", "Tool 6: Sudarshana Tri-Lagna 5H Activation (L/C/S)", lambda r: r["t6_tri_lagna"]),
        ("P8_gochara_double", "Tool 7: Gochara Jupiter / Saturn Real Transit Trigger on 5H", lambda r: r["t7_gochara"]),
    ]

    for t_id, desc, check_fn in single_tools:
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
            f"| **`{t_id}`** | {desc} | **{st['tpr']:.1f}%** ({st['tp']}/{len(pos_records)}) | "
            f"{st['fpr']:.1f}% ({st['fp']}/{len(neg_records)}) | **{st['precision']:.1f}%** | **{st['lift']:.2f}x** | {p_str} |"
        )

    # 3. Multi-Tool Synthesis Confluence
    print("\n### 3. HYPOTHESIS P7: PROGENY MULTI-TOOL CONFLUENCE PERFORMANCE MATRIX")
    print("| Confluence Level | TP | FP | FN | TN | Recall (TPR) | FPR | Precision | Lift | Chi2 (p-val) |")
    print("|---|---|---|---|---|---|---|---|---|---|")

    confl_thresholds = [
        ("Confluence >= 3 Tools Active", lambda r: r["confluence_count"] >= 3),
        ("Confluence >= 4 Tools Active", lambda r: r["confluence_count"] >= 4),
        ("Confluence >= 5 Tools Active", lambda r: r["confluence_count"] >= 5),
        ("Confluence >= 6 Tools Active", lambda r: r["confluence_count"] >= 6),
        ("Confluence == 7 Tools (All 7 Aligned)", lambda r: r["confluence_count"] == 7),
    ]

    for c_name, check_fn in confl_thresholds:
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
            f"| **{c_name}** | {st['tp']} | {st['fp']} | {st['fn']} | {st['tn']} | "
            f"**{st['tpr']:.1f}%** ({st['tp']}/{len(pos_records)}) | {st['fpr']:.1f}% ({st['fp']}/{len(neg_records)}) | "
            f"**{st['precision']:.1f}%** | **{st['lift']:.2f}x** | {p_str} |"
        )


if __name__ == "__main__":
    run_progeny_benchmark(748)
