import sys
from pathlib import Path
sys.path.insert(0, ".")
from datetime import datetime, timezone, date
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.phalita_core.polarity_engine import ClassicalPolarityEngine
from apps.api.services.sudarshana_chakra_dasha_engine import SudarshanaChakraDashaEngine
from apps.api.services.divisional_engine import compute_varga_sign
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine

wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
he = HoroscopeEngine(wrapper)
de = DashaEngine(wrapper)
pe = ClassicalPolarityEngine()
scd = SudarshanaChakraDashaEngine()
av = AshtakavargaEngine()

birth_dt = datetime(1971, 6, 29, 23, 27, 40, tzinfo=timezone.utc)
natal = he.generate_d1(birth_dt, 22.3072, 73.1812)
dasha_tree = de.compute_vimshottari(birth_dt, 22.3072, 73.1812, max_depth=3)

# SAV Bindus
sav_table = av.compute_sarvashtakavarga(natal)
h4_bindus = sav_table.bindus_from_lagna(natal.ascendant.rashi, 4)
h12_bindus = sav_table.bindus_from_lagna(natal.ascendant.rashi, 12)
h3_bindus = sav_table.bindus_from_lagna(natal.ascendant.rashi, 3)
h9_bindus = sav_table.bindus_from_lagna(natal.ascendant.rashi, 9)

print(f"--- NATAL PROPERTY & RELOCATION SIGNATURES (TAURUS LAGNA) ---")
print(f"4th House (Property/Home): Leo (Lord Sun in Gemini H2) | SAV Bindus = {h4_bindus}")
print(f"12th House (Foreign/Distant Relocation): Aries (Lord Mars in Cap H9) | SAV Bindus = {h12_bindus}")
print(f"3rd House (Short Shift): Cancer (Lord Moon in Virgo H5) | SAV Bindus = {h3_bindus}")
print(f"9th House (Long Travel/Relocation): Capricorn (Lord Saturn in Taurus H1) | SAV Bindus = {h9_bindus}")

# D4 Chaturthamsha (Property & Net Fortune)
d4_lagna = compute_varga_sign("D4", natal.ascendant.sidereal_longitude)[0]
print(f"D4 Lagna: {d4_lagna}")
for p in natal.planets:
    d4_r, d4_d = compute_varga_sign("D4", p.sidereal_longitude)
    if p.planet in ("sun", "mars", "venus", "jupiter", "saturn", "rahu", "ketu"):
        print(f"  {p.planet:7} D1: H{p.house_number:2} ({p.rashi}) -> D4: {d4_r:10} {d4_d:5.2f}°")

# Scan Life Windows for Property and Relocation
print("\n" + "="*80)
print("PROMINENT HISTORICAL & PROSPECTIVE PROPERTY / RELOCATION WINDOWS")
print("="*80)

# We check Antardasha periods
for md in dasha_tree.mahadashas:
    for ad in md.sub_periods:
        # Check mid date
        mid_days = (ad.end_date - ad.start_date).days // 2
        mid_d = ad.start_date + (ad.end_date - ad.start_date) / 2
        if isinstance(mid_d, datetime):
            mid_date = mid_d.date()
        else:
            mid_date = ad.start_date
        
        # Check if Dasha involves 4H, Mars, Venus, Sun (Property) or 3H/9H/12H/Rahu (Relocation)
        p_lords = [md.lord.lower(), ad.lord.lower()]
        
        # SCD
        scd_rep = scd.compute_scd(natal, birth_dt, mid_date)
        
        # Check triggers
        is_prop_dasha = bool(set(p_lords) & {"sun", "mars", "venus", "jupiter", "saturn"})
        is_relo_dasha = bool(set(p_lords) & {"rahu", "mars", "moon", "jupiter", "saturn"})
        
        scd_house = scd_rep.annual_house_offset
        
        is_property_highlight = (scd_house in (4, 9, 11, 1, 2)) and ("venus" in p_lords or "mars" in p_lords or "sun" in p_lords or "saturn" in p_lords)
        is_relocation_highlight = (scd_house in (3, 4, 8, 9, 12)) and ("rahu" in p_lords or "mars" in p_lords or "moon" in p_lords or "saturn" in p_lords)
        
        if ad.start_date.year >= 1995 and ad.start_date.year <= 2030:
            reasons = []
            if is_property_highlight and ("venus" in p_lords or "mars" in p_lords):
                reasons.append("PROPERTY / ASSET PURCHASE (4H/Venus/Mars/SCD alignment)")
            if is_relocation_highlight:
                reasons.append(f"RELOCATION / RESIDENCE CHANGE (SCD H{scd_house} + {md.lord.upper()}-{ad.lord.upper()})")
            
            if reasons:
                print(f"\nWindow: [{ad.start_date} to {ad.end_date}] — MD: {md.lord.upper()} | AD: {ad.lord.upper()}")
                print(f"  SCD Annual House: House {scd_house} (Age ~{scd_rep.native_age_years:.1f} yrs)")
                for r in reasons:
                    print(f"  -> {r}")
