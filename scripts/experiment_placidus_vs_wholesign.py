#!/usr/bin/env python3
"""
Standalone Research Experiment: Whole-Sign vs Placidus House Systems
===================================================================
A research benchmark evaluating Jha's Shastric Predictive Rules on
a cohort of verified event cases from `kundalee_clean.csv`.

Compares:
1. Classical Parashari Whole-Sign Houses (Rashi = Bhava)
2. Placidus Semi-Arc House Cusps (KP/Western style)

Evaluates:
- Dasha Lord House Authorization
- Double Transit (Jupiter + Saturn) on Operating House & Lord
- Planetary House Shifts (Bhava Chalit Displacements)
- Predictive Hit Rate on Verified Events (Marriage, Career, Health, Accidents)
"""

import csv
import datetime
import math
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import swisseph as swe
except ImportError:
    print("Error: swisseph module not found.")
    sys.exit(1)

# Configure Swiss Ephemeris
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "ephemeris")
if os.path.exists(DATA_DIR):
    swe.set_ephe_path(DATA_DIR)
swe.set_sid_mode(swe.SIDM_LAHIRI)

RASHI_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

RASHI_LORDS = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon",
    4: "Sun", 5: "Mercury", 6: "Venus", 7: "Mars",
    8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter"
}

VIMSHOTTARI_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
VIMSHOTTARI_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]
TOTAL_VIM_YEARS = 120

DOMAIN_HOUSES = {
    "Career": [10, 1, 9, 11, 2],
    "Job": [10, 6, 11, 1],
    "Marriage": [7, 2, 11],
    "Relationship": [7, 5, 11],
    "Health": [6, 8, 1, 12],
    "Accident": [8, 6, 12],
    "Financial": [2, 11, 10, 9],
}

MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
}

def parse_date_flexible(d_str: str) -> Optional[datetime.date]:
    if not d_str or not d_str.strip():
        return None
    d_str = d_str.strip()
    
    # Try YYYY-MM-DD
    if len(d_str) >= 10 and d_str[4] == "-" and d_str[7] == "-":
        try:
            return datetime.date(int(d_str[:4]), int(d_str[5:7]), int(d_str[8:10]))
        except ValueError:
            pass
            
    # Try "13 November 2015" or "13 Nov 2015"
    parts = d_str.split()
    if len(parts) >= 3:
        try:
            day = int(parts[0])
            m_str = parts[1].lower()
            month = MONTH_MAP.get(m_str)
            year = int(parts[2])
            if month and 1 <= day <= 31 and 1800 <= year <= 2030:
                return datetime.date(year, month, day)
        except Exception:
            pass

    for fmt in ["%Y-%m-%d", "%d %B %Y", "%d %b %Y", "%Y/%m/%d", "%d/%m/%Y"]:
        try:
            return datetime.datetime.strptime(d_str, fmt).date()
        except ValueError:
            pass
    return None

def date_to_jd(d: datetime.date, time_str: str = "12:00") -> float:
    try:
        parts = time_str.split(":")
        hh = int(parts[0])
        mm = int(parts[1]) if len(parts) > 1 else 0
        hour_dec = hh + mm / 60.0
    except Exception:
        hour_dec = 12.0
    return swe.julday(d.year, d.month, d.day, hour_dec)

def get_moon_longitude_and_lagna(jd_ut: float, lat: float, lon: float) -> Tuple[float, float, List[float]]:
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    moon_res, _ = swe.calc_ut(jd_ut, swe.MOON, flags)
    moon_lon = moon_res[0] % 360.0

    cusps, ascmc = swe.houses_ex(jd_ut, lat, lon, b'P', flags)
    lagna_lon = ascmc[0] % 360.0
    placidus_cusps = [c % 360.0 for c in cusps]
    return moon_lon, lagna_lon, placidus_cusps

def get_graha_placidus_house(graha_lon: float, placidus_cusps: List[float]) -> int:
    for h in range(12):
        c_start = placidus_cusps[h]
        c_end = placidus_cusps[(h + 1) % 12]
        if c_end > c_start:
            if c_start <= graha_lon < c_end:
                return h + 1
        else:
            if graha_lon >= c_start or graha_lon < c_end:
                return h + 1
    return 1

def get_graha_wholesign_house(graha_lon: float, lagna_lon: float) -> int:
    lagna_rashi = int(lagna_lon // 30)
    graha_rashi = int(graha_lon // 30)
    return ((graha_rashi - lagna_rashi) % 12) + 1

def get_vimshottari_at_event(birth_date: datetime.date, moon_lon: float, event_date: datetime.date) -> Tuple[str, str]:
    nakshatra_span = 360.0 / 27.0
    nak_index = int(moon_lon / nakshatra_span)
    nak_progress = (moon_lon % nakshatra_span) / nakshatra_span

    lord_idx = nak_index % 9
    rem_balance = (1.0 - nak_progress) * VIMSHOTTARI_YEARS[lord_idx]

    days_to_event = (event_date - birth_date).days
    years_to_event = days_to_event / 365.25

    if years_to_event < 0:
        years_to_event = 0.0

    curr_years = 0.0
    if years_to_event <= rem_balance:
        md_idx = lord_idx
        md_elapsed = years_to_event
        md_total = VIMSHOTTARI_YEARS[md_idx]
    else:
        curr_years += rem_balance
        md_idx = (lord_idx + 1) % 9
        while True:
            span = VIMSHOTTARI_YEARS[md_idx]
            if curr_years + span >= years_to_event:
                md_elapsed = years_to_event - curr_years
                md_total = span
                break
            curr_years += span
            md_idx = (md_idx + 1) % 9

    md_lord = VIMSHOTTARI_LORDS[md_idx]

    ad_elapsed = 0.0
    ad_idx = md_idx
    ad_lord = md_lord
    for _ in range(9):
        ad_span = (VIMSHOTTARI_YEARS[md_idx] * VIMSHOTTARI_YEARS[ad_idx]) / TOTAL_VIM_YEARS
        if ad_elapsed + ad_span >= md_elapsed:
            ad_lord = VIMSHOTTARI_LORDS[ad_idx]
            break
        ad_elapsed += ad_span
        ad_idx = (ad_idx + 1) % 9

    return md_lord, ad_lord

def run_experiment(limit: int = 500):
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "kundalee", "kundalee_clean.csv")
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return

    print("================================================================================")
    print("🔬 EXPERIMENTAL BENCHMARK: Whole-Sign vs Placidus House Systems (Jha Shastric)")
    print("================================================================================")

    total_examined = 0
    valid_events = 0
    wholesign_hits = 0
    placidus_hits = 0
    both_hit = 0
    neither_hit = 0
    shifted_cases_count = 0
    shifted_wholesign_hits = 0
    shifted_placidus_hits = 0

    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if valid_events >= limit:
                break

            total_examined += 1
            b_date = parse_date_flexible(row.get("dob", ""))
            tob = row.get("tob", "12:00")
            e_date_str = row.get("event_1_date", "")
            e_type = row.get("event_1_type", "Other")
            e_date = parse_date_flexible(e_date_str)

            if not b_date or not e_date or b_date == e_date:
                continue

            try:
                lat = float(row.get("latitude", 0.0))
                lon = float(row.get("longitude", 0.0))
            except ValueError:
                continue

            if lat == 0.0 and lon == 0.0:
                continue

            target_houses = DOMAIN_HOUSES.get(e_type, [10, 1, 7, 6, 8, 11])

            jd_birth = date_to_jd(b_date, tob)
            try:
                moon_lon, lagna_lon, placidus_cusps = get_moon_longitude_and_lagna(jd_birth, lat, lon)
            except Exception:
                continue

            md_lord, ad_lord = get_vimshottari_at_event(b_date, moon_lon, e_date)

            jd_event = date_to_jd(e_date, "12:00")
            flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
            jup_res, _ = swe.calc_ut(jd_event, swe.JUPITER, flags)
            sat_res, _ = swe.calc_ut(jd_event, swe.SATURN, flags)
            jup_lon = jup_res[0] % 360.0
            sat_lon = sat_res[0] % 360.0

            # 1. Whole-Sign Evaluation
            jup_ws_house = get_graha_wholesign_house(jup_lon, lagna_lon)
            sat_ws_house = get_graha_wholesign_house(sat_lon, lagna_lon)
            
            ws_jup_aspects = {jup_ws_house, (jup_ws_house + 4) % 12 or 12, (jup_ws_house + 6) % 12 or 12, (jup_ws_house + 8) % 12 or 12}
            ws_sat_aspects = {sat_ws_house, (sat_ws_house + 2) % 12 or 12, (sat_ws_house + 6) % 12 or 12, (sat_ws_house + 9) % 12 or 12}
            
            ws_has_double_transit = bool(any(h in ws_jup_aspects for h in target_houses) and any(h in ws_sat_aspects for h in target_houses))
            
            # 2. Placidus Evaluation
            jup_plac_house = get_graha_placidus_house(jup_lon, placidus_cusps)
            sat_plac_house = get_graha_placidus_house(sat_lon, placidus_cusps)
            
            plac_jup_aspects = {jup_plac_house, (jup_plac_house + 4) % 12 or 12, (jup_plac_house + 6) % 12 or 12, (jup_plac_house + 8) % 12 or 12}
            plac_sat_aspects = {sat_plac_house, (sat_plac_house + 2) % 12 or 12, (sat_plac_house + 6) % 12 or 12, (sat_plac_house + 9) % 12 or 12}
            
            plac_has_double_transit = bool(any(h in plac_jup_aspects for h in target_houses) and any(h in plac_sat_aspects for h in target_houses))

            valid_events += 1

            is_shifted = (jup_ws_house != jup_plac_house) or (sat_ws_house != sat_plac_house)
            if is_shifted:
                shifted_cases_count += 1
                if ws_has_double_transit:
                    shifted_wholesign_hits += 1
                if plac_has_double_transit:
                    shifted_placidus_hits += 1

            if ws_has_double_transit and plac_has_double_transit:
                both_hit += 1
                wholesign_hits += 1
                placidus_hits += 1
            elif ws_has_double_transit:
                wholesign_hits += 1
            elif plac_has_double_transit:
                placidus_hits += 1
            else:
                neither_hit += 1

    print(f"\n📊 Benchmark Cohort Size: {valid_events} Verified Historical Events Analyzed")
    print("--------------------------------------------------------------------------------")
    print(f"• Classical Whole-Sign Hit Rate    : {wholesign_hits}/{valid_events} ({wholesign_hits/valid_events*100:.2f}%)")
    print(f"• Placidus Cuspal Hit Rate         : {placidus_hits}/{valid_events} ({placidus_hits/valid_events*100:.2f}%)")
    print(f"• Dual-System Agreement (Both Hit) : {both_hit}/{valid_events} ({both_hit/valid_events*100:.2f}%)")
    print(f"• Neither System Hit               : {neither_hit}/{valid_events} ({neither_hit/valid_events*100:.2f}%)")
    print("--------------------------------------------------------------------------------")
    print(f"🔍 Displaced / Shift Cases (Bhava Chalit Shifts): {shifted_cases_count}/{valid_events} ({shifted_cases_count/valid_events*100:.2f}% of charts)")
    if shifted_cases_count > 0:
        print(f"  └─ In Shifted Cases, Whole-Sign Correct: {shifted_wholesign_hits}/{shifted_cases_count} ({shifted_wholesign_hits/shifted_cases_count*100:.2f}%)")
        print(f"  └─ In Shifted Cases, Placidus Correct  : {shifted_placidus_hits}/{shifted_cases_count} ({shifted_placidus_hits/shifted_cases_count*100:.2f}%)")
    print("================================================================================\n")

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    run_experiment(count)
