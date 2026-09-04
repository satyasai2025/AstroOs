"""
AstroOS — Ashtakavarga Bindu & Kakshya Transit Gating Benchmark
===============================================================
Evaluates whether Ashtakavarga SAV (Sarvashtakavarga) and BAV (Bhinnashtakavarga)
Bindu thresholds and Kakshya transit rules narrow the 44% FPR on Gochara across 634 windows.
"""

import csv
import math
import sys
from pathlib import Path
from datetime import datetime, date, timezone
from typing import List, Dict, Any, Tuple, Set

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.karyesha_engine import KaryeshaEngine, DomainEnum, RASHI_LORDS, RASHI_NAMES
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.ashtakavarga.bhinnashtakavarga_calculator import BhinnashtakavargaCalculator
from apps.api.services.dataset_hygiene_v1 import parse_date_flex
from packages.shared.ashtakavarga_bindu_table import BINDU_TABLE, CONTRIBUTORS, TARGET_PLANETS
from packages.shared.enums import Rashi, Graha

# 8 Kakshya Lords in strict classical order (0 to 7)
KAKSHYA_LORDS = ["saturn", "jupiter", "mars", "sun", "venus", "mercury", "moon", "lagna"]
DEGREES_PER_KAKSHYA = 30.0 / 8.0  # 3.75° = 3°45'

RASHI_LIST = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
]


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


def get_transit_aspect_houses(planet: str, current_house: int) -> Set[int]:
    p = planet.lower()
    def offset_house(base: int, step: int) -> int:
        return (base - 1 + step) % 12 + 1
    aspects = {current_house, offset_house(current_house, 6)}
    if p in ("jupiter", "guru"):
        aspects.add(offset_house(current_house, 4))
        aspects.add(offset_house(current_house, 8))
    elif p in ("saturn", "shani"):
        aspects.add(offset_house(current_house, 2))
        aspects.add(offset_house(current_house, 9))
    return aspects


def is_kakshya_donated(target_planet: str, transiting_rashi: str, kakshya_lord: str, contributor_rashis: Dict[str, str]) -> bool:
    """
    Checks if kakshya_lord donated a bindu in transiting_rashi for target_planet.
    """
    if target_planet not in BINDU_TABLE:
        return False
    target_table = BINDU_TABLE[target_planet]
    if kakshya_lord not in target_table or kakshya_lord not in contributor_rashis:
        return False
    contrib_rashi = contributor_rashis[kakshya_lord]
    offset = (RASHI_LIST.index(transiting_rashi) - RASHI_LIST.index(contrib_rashi)) % 12 + 1
    return offset in target_table[kakshya_lord]


def run_ashtakavarga_benchmark(target_n: int = 120):
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    dasha_engine = DashaEngine(wrapper)
    karyesha_engine = KaryeshaEngine(wrapper)
    av_calculator = BhinnashtakavargaCalculator()

    pristine_csv_path = Path("data/shastric_rules/kundalee_pristine_full.csv")

    event_total = 0
    control_total = 0

    models = [
        "baseline_double_transit",
        "sav_7h_ge_28",
        "sav_7h_ge_30",
        "jup_bav_ge_4",
        "sat_bav_ge_4",
        "both_bav_ge_4",
        "jup_kakshya_positive",
        "sat_kakshya_positive",
        "double_transit_and_kakshya_active",
        "dasha_double_transit_and_kakshya",
    ]
    model_stats = {m: {"pos": 0, "neg": 0} for m in models}

    pos_composite_scores = []
    neg_composite_scores = []

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
                        natal_ephem = wrapper.calculate(b_dt, lat, lon, ayanamsa="lahiri")
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
                    seventh_rashi_name = RASHI_LIST[seventh_rashi_idx]
                    seventh_lord_name = RASHI_LORDS[seventh_rashi_idx]
                    seventh_lord_d1_house = planets_info[seventh_lord_name].house_num_d1 if seventh_lord_name in planets_info else 7

                    # Natal Ashtakavarga Computation
                    contributor_rashis = {p.planet.lower(): p.rashi for p in natal_ephem.planet_positions if p.planet.lower() in CONTRIBUTORS}
                    contributor_rashis["lagna"] = natal_ephem.ascendant.rashi

                    bav_results = av_calculator.calculate_all(contributor_rashis)
                    bav_by_planet = {b.target_planet: b for b in bav_results}

                    # Sum to Sarvashtakavarga (SAV)
                    sav_bindus: Dict[str, int] = {r: 0 for r in RASHI_LIST}
                    for b in bav_results:
                        for idx, r_name in enumerate(RASHI_LIST):
                            sav_bindus[r_name] += b.bindus_by_rashi[idx]

                    sav_7th_house = sav_bindus[seventh_rashi_name]

                    # Dasha AD
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

                    ad_lord = target_ad.lord.lower()
                    ad_prof = profiles.get(ad_lord)
                    dasha_karyesha = (ad_prof.chart_specific_score >= 1.5) if ad_prof else False

                    # Event Date Gochara
                    e_dt_utc = datetime(e_date.year, e_date.month, e_date.day, 12, 0, 0, tzinfo=timezone.utc)
                    try:
                        transit_ephem = wrapper.calculate(e_dt_utc, lat, lon, ayanamsa="lahiri")
                    except Exception:
                        continue

                    trans_jup = None
                    trans_sat = None
                    for p in transit_ephem.planet_positions:
                        if p.planet.lower() == "jupiter":
                            trans_jup = p
                        elif p.planet.lower() == "saturn":
                            trans_sat = p

                    if not trans_jup or not trans_sat:
                        continue

                    event_total += 1

                    j_rashi_idx = int(trans_jup.sidereal_longitude / 30.0) % 12
                    j_rashi_name = RASHI_LIST[j_rashi_idx]
                    j_deg = trans_jup.sidereal_longitude % 30.0
                    j_kakshya_idx = int(j_deg / DEGREES_PER_KAKSHYA)
                    j_kakshya_lord = KAKSHYA_LORDS[j_kakshya_idx]

                    s_rashi_idx = int(trans_sat.sidereal_longitude / 30.0) % 12
                    s_rashi_name = RASHI_LIST[s_rashi_idx]
                    s_deg = trans_sat.sidereal_longitude % 30.0
                    s_kakshya_idx = int(s_deg / DEGREES_PER_KAKSHYA)
                    s_kakshya_lord = KAKSHYA_LORDS[s_kakshya_idx]

                    j_house = (j_rashi_idx - lagna_idx) % 12 + 1
                    s_house = (s_rashi_idx - lagna_idx) % 12 + 1

                    j_aspects = get_transit_aspect_houses("jupiter", j_house)
                    s_aspects = get_transit_aspect_houses("saturn", s_house)

                    j_hits_any = (1 in j_aspects) or (7 in j_aspects) or (seventh_lord_d1_house in j_aspects)
                    s_hits_any = (1 in s_aspects) or (7 in s_aspects) or (seventh_lord_d1_house in s_aspects)
                    base_double = j_hits_any and s_hits_any

                    j_bav = bav_by_planet["jupiter"].bindus_in_rashi(j_rashi_name) if "jupiter" in bav_by_planet else 0
                    s_bav = bav_by_planet["saturn"].bindus_in_rashi(s_rashi_name) if "saturn" in bav_by_planet else 0

                    j_kakshya_donated = is_kakshya_donated("jupiter", j_rashi_name, j_kakshya_lord, contributor_rashis)
                    s_kakshya_donated = is_kakshya_donated("saturn", s_rashi_name, s_kakshya_lord, contributor_rashis)

                    if base_double:
                        model_stats["baseline_double_transit"]["pos"] += 1
                    if sav_7th_house >= 28:
                        model_stats["sav_7h_ge_28"]["pos"] += 1
                    if sav_7th_house >= 30:
                        model_stats["sav_7h_ge_30"]["pos"] += 1
                    if j_bav >= 4:
                        model_stats["jup_bav_ge_4"]["pos"] += 1
                    if s_bav >= 4:
                        model_stats["sat_bav_ge_4"]["pos"] += 1
                    if j_bav >= 4 and s_bav >= 4:
                        model_stats["both_bav_ge_4"]["pos"] += 1
                    if j_kakshya_donated:
                        model_stats["jup_kakshya_positive"]["pos"] += 1
                    if s_kakshya_donated:
                        model_stats["sat_kakshya_positive"]["pos"] += 1
                    if base_double and (j_kakshya_donated or s_kakshya_donated):
                        model_stats["double_transit_and_kakshya_active"]["pos"] += 1
                    if dasha_karyesha and base_double and (j_kakshya_donated or s_kakshya_donated):
                        model_stats["dasha_double_transit_and_kakshya"]["pos"] += 1

                    pos_score = (1.0 if base_double else 0) + (1.0 if j_kakshya_donated else 0) + (1.0 if s_kakshya_donated else 0) + (0.5 if sav_7th_house >= 28 else 0)
                    pos_composite_scores.append(pos_score)

                    # Control Slices (5 per subject)
                    offsets_years = [-7, -4, 3, 6, 9]
                    for offset in offsets_years:
                        ctrl_date = e_date.replace(year=e_date.year + offset)
                        ctrl_age = (ctrl_date - b_dt.date()).days / 365.25
                        if ctrl_age < 18.0 or ctrl_age > 65.0:
                            continue

                        ctrl_dt_utc = datetime(ctrl_date.year, ctrl_date.month, ctrl_date.day, 12, 0, 0, tzinfo=timezone.utc)
                        try:
                            c_transit_ephem = wrapper.calculate(ctrl_dt_utc, lat, lon, ayanamsa="lahiri")
                        except Exception:
                            continue

                        c_trans_jup = None
                        c_trans_sat = None
                        for p in c_transit_ephem.planet_positions:
                            if p.planet.lower() == "jupiter":
                                c_trans_jup = p
                            elif p.planet.lower() == "saturn":
                                c_trans_sat = p

                        if not c_trans_jup or not c_trans_sat:
                            continue

                        control_total += 1

                        c_ad_lord = None
                        for md in dtree.mahadashas:
                            if md.contains(ctrl_date):
                                for ad in md.sub_periods:
                                    if ad.contains(ctrl_date):
                                        c_ad_lord = ad.lord.lower()
                                        break
                                break

                        c_ad_prof = profiles.get(c_ad_lord) if c_ad_lord else None
                        c_dasha_karyesha = (c_ad_prof.chart_specific_score >= 1.5) if c_ad_prof else False

                        cj_rashi_idx = int(c_trans_jup.sidereal_longitude / 30.0) % 12
                        cj_rashi_name = RASHI_LIST[cj_rashi_idx]
                        cj_deg = c_trans_jup.sidereal_longitude % 30.0
                        cj_kakshya_idx = int(cj_deg / DEGREES_PER_KAKSHYA)
                        cj_kakshya_lord = KAKSHYA_LORDS[cj_kakshya_idx]

                        cs_rashi_idx = int(c_trans_sat.sidereal_longitude / 30.0) % 12
                        cs_rashi_name = RASHI_LIST[cs_rashi_idx]
                        cs_deg = c_trans_sat.sidereal_longitude % 30.0
                        cs_kakshya_idx = int(cs_deg / DEGREES_PER_KAKSHYA)
                        cs_kakshya_lord = KAKSHYA_LORDS[cs_kakshya_idx]

                        cj_house = (cj_rashi_idx - lagna_idx) % 12 + 1
                        cs_house = (cs_rashi_idx - lagna_idx) % 12 + 1

                        cj_aspects = get_transit_aspect_houses("jupiter", cj_house)
                        cs_aspects = get_transit_aspect_houses("saturn", cs_house)

                        cj_hits_any = (1 in cj_aspects) or (7 in cj_aspects) or (seventh_lord_d1_house in cj_aspects)
                        cs_hits_any = (1 in cs_aspects) or (7 in cs_aspects) or (seventh_lord_d1_house in cs_aspects)
                        c_base_double = cj_hits_any and cs_hits_any

                        cj_bav = bav_by_planet["jupiter"].bindus_in_rashi(cj_rashi_name) if "jupiter" in bav_by_planet else 0
                        cs_bav = bav_by_planet["saturn"].bindus_in_rashi(cs_rashi_name) if "saturn" in bav_by_planet else 0

                        cj_kakshya_donated = is_kakshya_donated("jupiter", cj_rashi_name, cj_kakshya_lord, contributor_rashis)
                        cs_kakshya_donated = is_kakshya_donated("saturn", cs_rashi_name, cs_kakshya_lord, contributor_rashis)

                        if c_base_double:
                            model_stats["baseline_double_transit"]["neg"] += 1
                        if sav_7th_house >= 28:
                            model_stats["sav_7h_ge_28"]["neg"] += 1
                        if sav_7th_house >= 30:
                            model_stats["sav_7h_ge_30"]["neg"] += 1
                        if cj_bav >= 4:
                            model_stats["jup_bav_ge_4"]["neg"] += 1
                        if cs_bav >= 4:
                            model_stats["sat_bav_ge_4"]["neg"] += 1
                        if cj_bav >= 4 and cs_bav >= 4:
                            model_stats["both_bav_ge_4"]["neg"] += 1
                        if cj_kakshya_donated:
                            model_stats["jup_kakshya_positive"]["neg"] += 1
                        if cs_kakshya_donated:
                            model_stats["sat_kakshya_positive"]["neg"] += 1
                        if c_base_double and (cj_kakshya_donated or cs_kakshya_donated):
                            model_stats["double_transit_and_kakshya_active"]["neg"] += 1
                        if c_dasha_karyesha and c_base_double and (cj_kakshya_donated or cs_kakshya_donated):
                            model_stats["dasha_double_transit_and_kakshya"]["neg"] += 1

                        c_score = (1.0 if c_base_double else 0) + (1.0 if cj_kakshya_donated else 0) + (1.0 if cs_kakshya_donated else 0) + (0.5 if sav_7th_house >= 28 else 0)
                        neg_composite_scores.append(c_score)

                    break

    print("=== ASHTAKAVARGA & KAKSHYA TRANSIT BENCHMARK (634 WINDOWS) ===")
    print(f"Total Marriage Windows (Positives): {event_total}")
    print(f"Total Control Windows (Negatives):  {control_total}\n")

    descriptions = {
        "baseline_double_transit": "Baseline Double Transit (Rashi level alone)",
        "sav_7h_ge_28": "7th House SAV >= 28 Bindus",
        "sav_7h_ge_30": "7th House SAV >= 30 Bindus (High Strength)",
        "jup_bav_ge_4": "Jupiter Transit Sign BAV >= 4 Bindus",
        "sat_bav_ge_4": "Saturn Transit Sign BAV >= 4 Bindus",
        "both_bav_ge_4": "Both Jupiter & Saturn Transit Sign BAV >= 4",
        "jup_kakshya_positive": "Jupiter in Active Donated Kakshya (1 Bindu)",
        "sat_kakshya_positive": "Saturn in Active Donated Kakshya (1 Bindu)",
        "double_transit_and_kakshya_active": "Double Transit + Active Kakshya (Jup or Sat)",
        "dasha_double_transit_and_kakshya": "Multi-Layer (Dasha + Double Transit + Kakshya)",
    }

    print("| Model / Gating Rule | Description | TPR (Positives) | FPR (Controls) | Lift (TPR/FPR) |")
    print("|---|---|---|---|---|")
    for m in models:
        p = model_stats[m]["pos"]
        n = model_stats[m]["neg"]
        tpr = (p / event_total) * 100 if event_total > 0 else 0
        fpr = (n / control_total) * 100 if control_total > 0 else 0
        lift = tpr / fpr if fpr > 0 else 0
        desc = descriptions[m]
        print(f"| `{m}` | {desc} | {p}/{event_total} ({tpr:.1f}%) | {n}/{control_total} ({fpr:.1f}%) | **{lift:.2f}x** |")

    auc = compute_roc_auc(pos_composite_scores, neg_composite_scores)
    print(f"\nAshtakavarga + Kakshya Composite ROC-AUC: **{auc:.4f}**")


if __name__ == "__main__":
    run_ashtakavarga_benchmark(120)
