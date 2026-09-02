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

dates_to_check = [
    (date(2016, 8, 15), "Property Finalized / Seen (Aug 2016)"),
    (date(2016, 12, 15), "Property Agreement (Dec 2016)"),
    (date(2021, 6, 15), "Griha Pravesha / Shifted to Own Home (June 2021)"),
]

for d, ev in dates_to_check:
    print(f"\n" + "="*80)
    print(f"MILESTONE: {ev} [{d}]")
    print("="*80)
    
    # Dasha
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
    
    print(f"Vimshottari Dasha Hierarchy:")
    print(f"  MD: {cur_md.lord.upper()} ({cur_md.start_date} to {cur_md.end_date})")
    print(f"  AD: {cur_ad.lord.upper()} ({cur_ad.start_date} to {cur_ad.end_date})")
    if cur_pd:
        print(f"  PD: {cur_pd.lord.upper()} ({cur_pd.start_date} to {cur_pd.end_date})")
    if cur_sd:
        print(f"  SD: {cur_sd.lord.upper()} ({cur_sd.start_date} to {cur_sd.end_date})")
    
    # Transit
    dt_target = datetime(d.year, d.month, d.day, 12, 0, tzinfo=timezone.utc)
    transit = he.generate_d1(dt_target, 22.3072, 73.1812)
    rep = pe.evaluate(natal, transit, cur_md.lord, cur_ad.lord)
    print(f"\n3-Kundali Gochara: {rep.transit_auspicious_count}A / {rep.transit_inauspicious_count}I -> {rep.transit_net_polarity} (Polarity: {rep.final_polarity})")
    for r in rep.tri_lagna_planet_results:
        if r.planet in ("jupiter", "saturn", "mars", "venus"):
            print(f"  {r.planet.upper():7}: LK=H{r.house_from_lagna:2} ({r.lagna_polarity[:3]}) | SK=H{r.house_from_sun:2} ({r.sun_polarity[:3]}) | CK=H{r.house_from_moon:2} ({r.moon_polarity[:3]}) -> {r.composite_polarity}")

    # SCD
    scd_rep = scd.compute_scd(natal, birth_dt, d)
    print(f"\nSudarshana Chakra Dasha (SCD):")
    print(f"  Native Age: {scd_rep.native_age_years:.2f} yrs | Annual House: House {scd_rep.annual_house_offset} | Monthly House: House {scd_rep.monthly_house_offset} | Score: {scd_rep.composite_scd_score:+.2f}")
