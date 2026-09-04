"""
Real Chart Validation — Raj (DOB: 30 June 1971, 04:57:40 AM, Vadodara, Gujarat)
==================================================================================
BLIND PROSPECTIVE VALIDATION TEST

Step 1: Run full consultation engine on chart
Step 2: Compare system output vs known life timeline
Step 3: Forward scan 2026-27
"""

from __future__ import annotations
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, date, timezone

sys.path.insert(0, str(Path.cwd()))

from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.arudha_engine import ArudhaEngine
from apps.api.services.bhrigu_bindu_engine import BhriguBinduEngine
from apps.api.services.sarvato_bhadra_engine import SarvatoBhadraEngine
from apps.api.services.sudarshana_chakra_engine import SudarshanaChakraEngine
from apps.api.services.phalita_core.decision_engine import PhalitaDecisionEngine

# ── Chart Data ────────────────────────────────────────────────────────────────
BIRTH_UTC  = datetime(1971, 6, 30, 4, 57, 40, tzinfo=timezone.utc)  # 04:57:40 AM IST ≈ -5:30 offset needed
# IST = UTC + 5:30, so 04:57:40 IST = 04:57:40 - 5:30 = 23:27:40 UTC (prev day)
# Let's be precise:
from datetime import timedelta
IST_OFFSET = timedelta(hours=5, minutes=30)
BIRTH_IST  = datetime(1971, 6, 30, 4, 57, 40)
BIRTH_UTC  = BIRTH_IST - IST_OFFSET  # Convert IST → UTC
BIRTH_UTC  = BIRTH_UTC.replace(tzinfo=timezone.utc)

LAT, LON = 22.3072, 73.1812   # Vadodara, Gujarat

# ── Known Life Events for Validation ─────────────────────────────────────────
KNOWN_EVENTS = [
    {"date": "1988-06-01", "event": "Education break in 12th std (approx 1988)", "category": "education"},
    {"date": "1994-06-01", "event": "Started BA Economics", "category": "education"},
    {"date": "1997-06-01", "event": "Completed BA, started MCA from IBM", "category": "education"},
    {"date": "2000-06-01", "event": "Completed MCA, got job as faculty", "category": "career"},
    {"date": "2002-04-01", "event": "Marriage", "category": "marriage"},
    {"date": "2002-05-01", "event": "Lost teaching job", "category": "career_loss"},
    {"date": "2003-02-01", "event": "Started IT career as web programmer", "category": "career"},
    {"date": "2003-05-01", "event": "Birth of son", "category": "child"},
    {"date": "2007-04-01", "event": "Shifted to Vadodara — new job Software Engineer", "category": "career"},
    {"date": "2008-03-01", "event": "Death of father", "category": "family_loss"},
    {"date": "2008-06-01", "event": "Shifted to Pune — Software Engineer", "category": "career"},
    {"date": "2011-12-01", "event": "Layoff — got new job as Project Manager", "category": "career"},
    {"date": "2013-07-01", "event": "New job as Project Manager", "category": "career"},
    {"date": "2013-01-01", "event": "Purchased first house", "category": "property"},
    {"date": "2014-05-01", "event": "Went to USA (15 days)", "category": "travel"},
    {"date": "2016-01-01", "event": "Purchased second house", "category": "property"},
    {"date": "2019-03-01", "event": "Lost job (5yr 9mo tenure) + Got new job same month", "category": "career"},
    {"date": "2020-10-01", "event": "Lost Senior PM job (1yr 8mo tenure)", "category": "career_loss"},
    {"date": "2021-03-01", "event": "New job (Mar 2021 - Feb 2023)", "category": "career"},
    {"date": "2023-02-01", "event": "End of 2yr 9mo corporate job", "category": "career_loss"},
    {"date": "2024-07-01", "event": "Joined as part-time teacher in school", "category": "career"},
    {"date": "2025-02-01", "event": "Joined sales role via networking", "category": "career"},
    {"date": "2026-01-01", "event": "Lost sales role", "category": "career_loss"},
    {"date": "2026-02-01", "event": "Lost part-time teaching job", "category": "career_loss"},
]

def run():
    print("=" * 90)
    print("  RAJ CHART — REAL BLIND LIFE-EVENT VALIDATION + FORWARD SCAN 2026-27")
    print(f"  DOB: 30 Jun 1971, 04:57:40 AM IST | Vadodara, Gujarat")
    print(f"  Birth UTC: {BIRTH_UTC}")
    print("=" * 90)

    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    horo    = HoroscopeEngine(wrapper)
    chart   = horo.generate_d1(BIRTH_UTC, LAT, LON)

    # ── 1. Basic Chart Info ──────────────────────────────────────────────────
    print("\n[A] BASIC CHART INFO")
    print(f"  Lagna (Ascendant)  : {chart.ascendant.rashi}")
    print(f"  Lagna Degree       : {chart.ascendant.rashi_degree:.2f}°")
    planet_map = {p.planet.lower(): p for p in chart.planets}
    for planet in ["sun","moon","mars","mercury","jupiter","venus","saturn","rahu","ketu"]:
        p = planet_map.get(planet)
        if p:
            retro = " (R)" if p.is_retrograde else ""
            print(f"  {planet.upper():10}: {p.rashi:12} {p.rashi_degree:6.2f}° H{p.house_number}{retro}")

    # ── 2. Arudha Padas ───────────────────────────────────────────────────────
    arudha_engine = ArudhaEngine()
    arudha = arudha_engine.compute(chart)
    print(f"\n[B] ARUDHA PADAS")
    print(f"  AL  (Arudha Lagna / Public Image)  : {arudha.arudha_lagna.rashi} (H{arudha.arudha_lagna.house_number})")
    print(f"  UL  (Upapada Lagna / Marriage)      : {arudha.upapada_lagna.rashi} (H{arudha.upapada_lagna.house_number})")
    print(f"  A10 (Rajya Pada / Career Authority) : {arudha.by_house(10).rashi} (H{arudha.by_house(10).house_number})")
    print(f"  A7  (Spouse Pada)                   : {arudha.by_house(7).rashi} (H{arudha.by_house(7).house_number})")

    # ── 3. Sudarshana Chakra ─────────────────────────────────────────────────
    sc_engine = SudarshanaChakraEngine()
    sc = sc_engine.evaluate_chart(chart, BIRTH_UTC,
         datetime(2026, 8, 28, tzinfo=timezone.utc))
    print(f"\n[C] SUDARSHANA CHAKRA (Tri-Lagna)")
    print(f"  Lagna Kundali (LK)  : {sc.lagna_rashi}")
    print(f"  Chandra Kundali (CK): {sc.moon_rashi}")
    print(f"  Surya Kundali (SK)  : {sc.sun_rashi}")
    print(f"  Tri-Harmony Score   : {sc.tri_fold_harmony_score}")
    print(f"  Active SCD House    : H{sc.current_scd.active_house_from_lagna} — {sc.current_scd.primary_theme}")

    # ── 4. Bhrigu Bindu ──────────────────────────────────────────────────────
    bb_engine = BhriguBinduEngine(ephemeris_path="data/ephemeris")
    bb = bb_engine.evaluate_transit(chart, target_date=date(2026, 8, 28))
    print(f"\n[D] BHRIGU BINDU (Destiny Trigger Point)")
    print(f"  BB Rashi / Degree   : {bb.bb_rashi} {bb.bb_rashi_degree:.2f}°")
    print(f"  BB Nakshatra        : {bb.bb_nakshatra} Pada {bb.bb_nakshatra_pada}")
    print(f"  House from Lagna    : H{bb.bb_house_from_lagna}")
    print(f"  Current Status      : {bb.activation_status}")
    print(f"  Destiny Impact Score: {bb.destiny_impact_score}")

    # ── 5. Vimshottari Dasha Timeline ────────────────────────────────────────
    dasha_engine = DashaEngine(wrapper)
    dasha_tree = dasha_engine.compute_vimshottari(BIRTH_UTC, LAT, LON)
    print(f"\n[E] VIMSHOTTARI DASHA PERIODS")
    for md in dasha_tree.mahadashas:
        md_start = md.start_date
        md_end   = md.end_date
        if md_end.year < 1985:
            continue
        if md_start.year > 2030:
            break
        print(f"\n  == {md.lord.upper()} Mahadasha: {md_start} -> {md_end} ==")
        for ad in md.sub_periods:
            ad_start = ad.start_date
            ad_end   = ad.end_date
            if ad_start.year > 2030:
                break
            print(f"      {md.lord.upper()}-{ad.lord.upper():8} : {ad_start} -> {ad_end}")

    # ── 6. Life-Event Validation Scan ────────────────────────────────────────
    decision_engine = PhalitaDecisionEngine(ephemeris_path="data/ephemeris")

    print("\n" + "=" * 90)
    print("  [F] LIFE-EVENT VALIDATION — System Tier vs Known Events")
    print("=" * 90)
    print(f"  {'Event Date':12} {'Known Event':52} {'Dasha Window':20} {'Tier':22}")
    print("-" * 90)

    timeline_1985_2026 = decision_engine.scan_life_timeline(
        birth_datetime=BIRTH_UTC, latitude=LAT, longitude=LON,
        native_name="Raj", scan_start_year=1985, scan_end_year=2026,
        domain="career",
    )

    for ev in KNOWN_EVENTS:
        ev_date = date.fromisoformat(ev["date"])
        matched = None
        for w in timeline_1985_2026.windows:
            ws = w.window_start if isinstance(w.window_start, date) else w.window_start.date()
            we = w.window_end   if isinstance(w.window_end,   date) else w.window_end.date()
            if ws <= ev_date <= we:
                matched = w
                break
        if matched:
            dasha_str = f"{matched.mahadasha_lord}-{matched.antardasha_lord}"
            tier = matched.decision_tier
        else:
            dasha_str = "OUT_OF_SCAN"
            tier = "—"

        tier_icon = {"PRATYAKSHA_PHALA": "[HIGH]", "SUSHUPTA_BEEJA": "[MID]", "ALPA_PHALA": "[LOW]", "SAMANYA_KAL": "[NORM]"}.get(tier, "[?]")
        print(f"  {ev['date']:12} {ev['event'][:52]:52} {dasha_str:20} {tier_icon:6} {tier}")

    # ── 7. Forward Scan 2026-27 ──────────────────────────────────────────────
    print("\n" + "=" * 90)
    print("  [G] FORWARD SCAN 2026-2027 — System Predictions")
    print("=" * 90)

    forward = decision_engine.scan_life_timeline(
        birth_datetime=BIRTH_UTC, latitude=LAT, longitude=LON,
        native_name="Raj", scan_start_year=2026, scan_end_year=2028,
        domain="career",
    )

    for w in forward.windows:
        tier_icon = {"PRATYAKSHA_PHALA": "[HIGH]", "SUSHUPTA_BEEJA": "[MID]", "ALPA_PHALA": "[LOW]", "SAMANYA_KAL": "[NORM]"}.get(w.decision_tier, "[?]")
        ws = w.window_start if isinstance(w.window_start, date) else w.window_start.date()
        we = w.window_end   if isinstance(w.window_end,   date) else w.window_end.date()
        print(f"\n  {tier_icon} [{ws} -> {we}]")
        print(f"     Dasha   : {w.mahadasha_lord}-{w.antardasha_lord}")
        print(f"     Tier    : {w.decision_tier} | Confidence: {w.confidence_level}")
        print(f"     SAV 10H : {w.sav_10th_bindus} bindus | Double Transit: {w.double_transit}")
        print(f"     D10 Dignity: {w.d10_dignity_summary}")
        print(f"     Bhava Sandhi: {w.bhavachalita_note}")
        print(f"     Explanation [HI]: {w.explanation_hi}")
        print(f"     Explanation [EN]: {w.explanation_en}")

    print("\n[OK] Validation + Forward Scan Complete.")

if __name__ == "__main__":
    run()
