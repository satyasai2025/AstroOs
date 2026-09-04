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

wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
he = HoroscopeEngine(wrapper)
de = DashaEngine(wrapper)
pe = ClassicalPolarityEngine()
scd = SudarshanaChakraDashaEngine()

birth_dt = datetime(1971, 6, 29, 23, 27, 40, tzinfo=timezone.utc)
natal = he.generate_d1(birth_dt, 22.3072, 73.1812)
dasha_tree = de.compute_vimshottari(birth_dt, 22.3072, 73.1812, max_depth=4)

print("--- NATAL PLANETS & D12 (DWADASHAMSHA - PARENTS) ---")
d12_lagna = compute_varga_sign("D12", natal.ascendant.sidereal_longitude)[0]
print(f"Lagna: {natal.ascendant.rashi} {natal.ascendant.rashi_degree:.2f}° | D12 Lagna: {d12_lagna}")

for p in natal.planets:
    d12_rashi, d12_deg = compute_varga_sign("D12", p.sidereal_longitude)
    print(f"  {p.planet:8}: {p.rashi:11} {p.rashi_degree:5.2f}° | H{p.house_number:2} | D12: {d12_rashi:11} {d12_deg:5.2f}°")

dates_to_check = [
    (date(2008, 2, 14), "Father Bed-ridden / Hospitalized (Feb 2008)"),
    (date(2008, 3, 8), "Father Death (8 March 2008)"),
    (date(2025, 11, 10), "Mother Bed-ridden (10 Nov 2025)"),
    (date(2025, 12, 25), "Mother Death (25 Dec 2025)"),
]

for d, ev in dates_to_check:
    print(f"\n" + "="*80)
    print(f"EVENT: {ev} [{d}]")
    print("="*80)
    
    # 1. Active Dasha Hierarchy
    cur_md, cur_ad, cur_pd, cur_sd = None, None, None, None
    for md in dasha_tree.mahadashas:
        if md.start_date <= d < md.end_date:
            cur_md = md
            for ad in md.sub_periods:
                if ad.start_date <= d < ad.end_date:
                    cur_ad = ad
                    for pd in ad.sub_periods:
                        if pd.start_date <= d < pd.end_date:
                            cur_pd = pd
                            for sd in pd.sub_periods:
                                if sd.start_date <= d < sd.end_date:
                                    cur_sd = sd
    
    md_str = cur_md.lord.upper() if cur_md else "N/A"
    ad_str = cur_ad.lord.upper() if cur_ad else "N/A"
    pd_str = cur_pd.lord.upper() if cur_pd else "N/A"
    sd_str = cur_sd.lord.upper() if cur_sd else "N/A"
    print(f"Vimshottari Dasha Hierarchy:")
    print(f"  Mahadasha (MD)     : {md_str} ({cur_md.start_date} to {cur_md.end_date})")
    print(f"  Antardasha (AD)    : {ad_str} ({cur_ad.start_date} to {cur_ad.end_date})")
    if cur_pd:
        print(f"  Pratyantardasha (PD): {pd_str} ({cur_pd.start_date} to {cur_pd.end_date})")
    if cur_sd:
        print(f"  Sookshma Dasha (SD) : {sd_str} ({cur_sd.start_date} to {cur_sd.end_date})")
    
    # 2. 3-Kundali Gochara
    dt_target = datetime(d.year, d.month, d.day, 12, 0, tzinfo=timezone.utc)
    transit = he.generate_d1(dt_target, 22.3072, 73.1812)
    rep = pe.evaluate(natal, transit, cur_md.lord, cur_ad.lord)
    print(f"\n3-Kundali Gochara (LK=Taurus, SK=Gemini, CK=Virgo):")
    print(f"  Net Transit Vote: {rep.transit_auspicious_count}A / {rep.transit_inauspicious_count}I -> {rep.transit_net_polarity}")
    print(f"  Combined Polarity: {rep.final_polarity}")
    print(f"  Logic: {rep.final_polarity_logic}")
    for r in rep.tri_lagna_planet_results:
        icon = "+" if r.composite_polarity == "AUSPICIOUS" else "-" if r.composite_polarity == "INAUSPICIOUS" else "~"
        print(f"    [{icon}] {r.planet.upper():7}: LK=H{r.house_from_lagna:2} ({r.lagna_polarity[:3]}) | SK=H{r.house_from_sun:2} ({r.sun_polarity[:3]}) | CK=H{r.house_from_moon:2} ({r.moon_polarity[:3]}) -> {r.composite_polarity}")

    # 3. Sudarshana Chakra Dasha (SCD)
    scd_rep = scd.compute_scd(natal, birth_dt, d)
    print(f"\nSudarshana Chakra Dasha (SCD):")
    print(f"  Native Age: {scd_rep.native_age_years:.2f} years (Cycle {scd_rep.scd_cycle_number})")
    print(f"  Active Annual House : House {scd_rep.annual_house_offset} (LK={scd_rep.lk_annual.active_lord}, SK={scd_rep.sk_annual.active_lord}, CK={scd_rep.ck_annual.active_lord})")
    print(f"  Active Monthly House: House {scd_rep.monthly_house_offset}")
    print(f"  Composite SCD Score : {scd_rep.composite_scd_score:+.2f}")
