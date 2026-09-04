"""
Raj Chart — Classical 2026-27 Forward Prediction
Uses HoroscopeEngine for transit chart computation
"""
from __future__ import annotations
import sys
from pathlib import Path
from datetime import datetime, date, timezone, timedelta

sys.path.insert(0, str(Path.cwd()))

from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.arudha_engine import ArudhaEngine
from apps.api.services.bhrigu_bindu_engine import BhriguBinduEngine
from apps.api.services.phalita_core.classical_filter_engine import ClassicalFilterEngine

BIRTH_IST = datetime(1971, 6, 30, 4, 57, 40)
IST_OFFSET = timedelta(hours=5, minutes=30)
BIRTH_UTC  = (BIRTH_IST - IST_OFFSET).replace(tzinfo=timezone.utc)
LAT, LON   = 22.3072, 73.1812

RASHI_NUM = {
    "aries":1,"taurus":2,"gemini":3,"cancer":4,"leo":5,"virgo":6,
    "libra":7,"scorpio":8,"sagittarius":9,"capricorn":10,"aquarius":11,"pisces":12
}

def house_from_lagna(lagna_rashi: str, planet_rashi: str) -> int:
    l = RASHI_NUM.get(lagna_rashi.lower(), 1)
    p = RASHI_NUM.get(planet_rashi.lower(), 1)
    return ((p - l) % 12) + 1

def run():
    wrapper  = EphemerisWrapper(ephemeris_path="data/ephemeris")
    horo     = HoroscopeEngine(wrapper)
    filter_e = ClassicalFilterEngine("data/ephemeris")
    bb_eng   = BhriguBinduEngine("data/ephemeris")

    # Natal chart
    natal    = horo.generate_d1(BIRTH_UTC, LAT, LON)
    arudha   = ArudhaEngine().compute(natal)
    natal_pm = {p.planet.lower(): p for p in natal.planets}
    lagna_rashi = natal.ascendant.rashi.lower()

    print("=" * 78)
    print("  RAJ — CLASSICAL 2026-27 DEEP FORWARD READING")
    print(f"  Lagna: TAURUS 29.79 | Saturn-Saturn MD (2024-06 to 2027-06)")
    print("=" * 78)

    print(f"\n  Natal Key Positions (for transit overlay reference):")
    print(f"  Lagna / H1 : TAURUS  | 10H (karma) : AQUARIUS")
    print(f"  A10 Pada   : TAURUS  | AL (image)  : AQUARIUS")
    print(f"  BB         : TAURUS 14.28 (Rohini) — H1 (self/reinvention)")
    print(f"  Natal Sat  : TAURUS H1 | Natal Jup  : SCORPIO H7 (R)")
    print(f"  Natal Rahu : CAPRICORN H9 | Natal Mars : CAPRICORN H9 (Exalted)")

    quarters = [
        ("Jan 2026", datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)),
        ("Apr 2026", datetime(2026, 4, 15, 0, 0, tzinfo=timezone.utc)),
        ("Jul 2026", datetime(2026, 7, 15, 0, 0, tzinfo=timezone.utc)),
        ("Oct 2026", datetime(2026, 10, 15, 0, 0, tzinfo=timezone.utc)),
        ("Jan 2027", datetime(2027, 1, 15, 0, 0, tzinfo=timezone.utc)),
        ("Apr 2027", datetime(2027, 4, 15, 0, 0, tzinfo=timezone.utc)),
    ]

    print("\n" + "=" * 78)
    print("  TRANSIT MAP — Quarter by Quarter")
    print("=" * 78)

    results = []

    for label, dt in quarters:
        transit = horo.generate_d1(dt, LAT, LON)
        tp = {p.planet.lower(): p for p in transit.planets}

        jup_t  = tp.get("jupiter")
        sat_t  = tp.get("saturn")
        rahu_t = tp.get("rahu")
        ketu_t = tp.get("ketu")
        mars_t = tp.get("mars")

        jup_h  = house_from_lagna(lagna_rashi, jup_t.rashi) if jup_t else "?"
        sat_h  = house_from_lagna(lagna_rashi, sat_t.rashi) if sat_t else "?"
        rahu_h = house_from_lagna(lagna_rashi, rahu_t.rashi) if rahu_t else "?"
        mars_h = house_from_lagna(lagna_rashi, mars_t.rashi) if mars_t else "?"

        # Jupiter aspects: 5th, 7th, 9th from itself
        jup_aspects = [(jup_h+4-1)%12+1, (jup_h+6-1)%12+1, (jup_h+8-1)%12+1] if jup_t else []
        # Saturn aspects: 3rd, 7th, 10th from itself
        sat_aspects = [(sat_h+2-1)%12+1, (sat_h+6-1)%12+1, (sat_h+9-1)%12+1] if sat_t else []

        jup_on_10 = 10 in jup_aspects or jup_h == 10
        sat_on_10 = 10 in sat_aspects or sat_h == 10
        jup_on_1  = 1 in jup_aspects or jup_h == 1
        sat_on_1  = 1 in sat_aspects or sat_h == 1
        jup_on_7  = 7 in jup_aspects or jup_h == 7
        rahu_on_1 = rahu_h == 1

        # BB check
        bb_rep = bb_eng.evaluate_transit(natal, target_date=date(dt.year, dt.month, dt.day))
        bb_active = bb_rep.activation_status != "INACTIVE"

        confl = filter_e.compute_continuous_confluence(
            chart=natal,
            target_date=date(dt.year, dt.month, dt.day),
            mahadasha_lord="saturn",
            antardasha_lord="saturn",
            domain="career",
        )

        print(f"\n  [{label}]")
        print(f"    Jupiter  : {jup_t.rashi.upper():12} H{jup_h:2}  aspects -> {jup_aspects}")
        print(f"    Saturn   : {sat_t.rashi.upper():12} H{sat_h:2}  aspects -> {sat_aspects}")
        print(f"    Rahu     : {rahu_t.rashi.upper():12} H{rahu_h:2}")
        print(f"    Mars     : {mars_t.rashi.upper():12} H{mars_h:2}")
        print(f"    Jup->H10 : {jup_on_10}  | Sat->H10: {sat_on_10}  | SAV 10H: {confl.sav_bindus}")
        print(f"    Jup->H1  : {jup_on_1}  | Sat->H1 : {sat_on_1}")
        print(f"    BB Active: {bb_active} ({bb_rep.activation_status})")

        # Synthesize signal
        signals = []
        if jup_on_10 and sat_on_10:
            signals.append("DOUBLE TRANSIT H10 = Strong career activation")
        if jup_h == 11 or jup_on_1:
            signals.append("Jupiter -> H11/H1 = Income expansion + new opportunity")
        if jup_h == 7:
            signals.append("Jupiter H7 = Partnership/collaboration opportunity")
        if sat_h == 1 or sat_on_1:
            signals.append("Saturn on Lagna = Pressure, hard work, discipline required")
        if rahu_h == 1:
            signals.append("Rahu H1 = Identity shift, unconventional path, new direction")
        if rahu_h == 10:
            signals.append("Rahu H10 = Ambition spike, unusual career opportunity")
        if bb_active:
            signals.append(f"BB ACTIVATED = Destiny trigger active ({bb_rep.activation_status})")
        if mars_h == 10:
            signals.append("Mars H10 = Energy/action in career, possible conflict")

        results.append((label, signals, jup_h, sat_h, rahu_h, jup_on_10, sat_on_10))

        if signals:
            print(f"    SIGNALS:")
            for s in signals:
                print(f"      >> {s}")
        else:
            print(f"    SIGNALS: Routine period — no major activation")

    print("\n" + "=" * 78)
    print("  CLASSICAL SYNTHESIS — Raj ke 2026-27 ke liye Predictions")
    print("=" * 78)
    print("""
  SATURN-SATURN MAHADASHA (2024-Jun to 2027-Jun) — Taurus Lagna

  Classical Rule: Jab Mahadasha lord aur Antardasha lord ek hi graha ho,
  tab us graha ki natal position, transit position aur natural significations
  — teeno milkar ek intense, concentrated period banate hain.

  Natal Saturn Taurus H1 mein hai:
  - Saturn = Lagna lord (Taurus mein H1) — very strong vargottama-type
  - Saturn-Saturn = khud apne aap ko face karna
  - Theme: Hard discipline, delayed rewards, identity restructuring

  KEY CLASSICAL INDICATORS FOR 2026:
  ─────────────────────────────────
  1. Sade-Sati / Shani ki position check karo (Taurus Lagna)
     Shani agar Aries/Taurus/Gemini mein ho = intense pressure on Lagna
     Shani agar Cancer/Leo/Virgo mein ho = relatively stable

  2. Jupiter transit is most important positive factor:
     Jupiter H10 ya H11 transit = income, recognition, new opportunity
     Jupiter H6/H8/H12 transit = obstacles

  3. Rahu H1 ya H10 = unconventional career opportunity — IT training,
     online education, freelance etc. — Rahu naturally represents these

  HONEST CLASSICAL PREDICTION for 2026-27:
  ─────────────────────────────────────────
  >> Saturn-Saturn is NOT naturally a "peak career" dasha for Taurus Lagna
     Saturn rules H9 (fortune) and H10 (career) — so it IS a career dasha
     BUT Saturn being in H1 natally = results come with hard work and delay

  >> The period STRONGLY suggests:
     - A shift from instability to a more structured/stable role
     - Teaching, training, technical writing — Saturn + Mercury themes
     - IT training/education domain (Mercury in H2 + Saturn in H1)
     - Financial tightness continues but foundation-building begins

  >> What to WATCH for as validation markers:
     - Any stable role (even part-time) that lasts more than 1 year = system correct
     - Financial improvement after mid-2026 = Jupiter transit confirmation
     - A role in education/training/IT domain = chart signature match
""")

if __name__ == "__main__":
    run()
