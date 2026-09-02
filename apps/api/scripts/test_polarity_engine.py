"""
Test: Classical Polarity Engine on Raj's chart
Taurus Lagna | Saturn-Saturn MD | Various transit dates
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(Path.cwd()))

from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.phalita_core.polarity_engine import ClassicalPolarityEngine

BIRTH_UTC = datetime(1971, 6, 29, 23, 27, 40, tzinfo=timezone.utc)
LAT, LON  = 22.3072, 73.1812

wrapper  = EphemerisWrapper("data/ephemeris")
horo     = HoroscopeEngine(wrapper)
engine   = ClassicalPolarityEngine()

natal = horo.generate_d1(BIRTH_UTC, LAT, LON)

print("=" * 70)
print("  CLASSICAL POLARITY ENGINE TEST — RAJ CHART (Taurus Lagna)")
print("=" * 70)
print(f"\n  Natal Moon: {[p for p in natal.planets if p.planet.lower()=='moon'][0].rashi.upper()}")
print(f"  Lagna: {natal.ascendant.rashi.upper()}")

# Test historical events with known polarity
test_cases = [
    # (date_str, MD, AD, known_event, expected_polarity)
    ("2002-04-15", "rahu",    "venus",   "Marriage (AUSPICIOUS)",  "should be AUSPICIOUS"),
    ("2002-05-01", "rahu",    "venus",   "Lost teaching job (CHALLENGING)", "same window as marriage"),
    ("2008-03-01", "rahu",    "mars",    "Father death (CHALLENGING)", "should be CHALLENGING"),
    ("2013-07-01", "jupiter", "mercury", "New PM job (AUSPICIOUS)", "should be AUSPICIOUS"),
    ("2019-03-01", "jupiter", "sun",     "Lost job + new job same month (MIXED)", "should be MIXED"),
    ("2026-01-01", "saturn",  "saturn",  "Lost sales role (CHALLENGING)", "should be CHALLENGING"),
    ("2027-01-01", "saturn",  "saturn",  "Forward scan 2027 (??)", "unknown — our prediction"),
]

print("\n" + "-" * 70)
print(f"  {'Date':<12} {'MD-AD':<20} {'Dasha Pol':<14} {'Transit Pol':<14} {'FINAL'}")
print("-" * 70)

for date_str, md, ad, event, expectation in test_cases:
    dt = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    transit = horo.generate_d1(dt, LAT, LON)
    report  = engine.evaluate(natal, transit, md, ad)

    print(f"\n  [{date_str}] {event}")
    print(f"  MD: {md.upper()} ({report.md_category}) | AD: {ad.upper()} ({report.ad_category})")
    print(f"  Dasha polarity: {report.dasha_polarity}")
    sc_type = "Amavasya (SK+CK)" if report.is_amavasya_sc else "Sudarshana (LK+SK+CK)"
    print(f"  Gochara [{sc_type}]:")
    for r in report.tri_lagna_planet_results:
        icon = "+" if r.composite_polarity == "AUSPICIOUS" else "-" if r.composite_polarity == "INAUSPICIOUS" else "~"
        print(f"    [{icon}] {r.planet.upper():7} | LK: H{r.house_from_lagna:2} ({r.lagna_polarity[:3]}) | SK: H{r.house_from_sun:2} ({r.sun_polarity[:3]}) | CK: H{r.house_from_moon:2} ({r.moon_polarity[:3]}) -> {r.composite_polarity}")
    print(f"  Transit Net: {report.transit_auspicious_count}A / {report.transit_inauspicious_count}I -> {report.transit_net_polarity}")
    print(f"  FINAL: >>> {report.final_polarity} <<<")
    print(f"  {report.final_polarity_logic}")
    print(f"  Expected: {expectation}")
