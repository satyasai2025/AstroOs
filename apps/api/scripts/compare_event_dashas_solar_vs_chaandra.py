import sys
from pathlib import Path
sys.path.insert(0, ".")
from datetime import datetime, timezone, date, timedelta
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from packages.shared.constants import VIMSHOTTARI_DASHA_YEARS, VIMSHOTTARI_SEQUENCE, VIMSHOTTARI_TOTAL_YEARS

birth_dt = datetime(1971, 6, 29, 23, 27, 40, tzinfo=timezone.utc)
birth_date = birth_dt.date()

# Moon in Uttara Phalguni, fraction elapsed ~0.6699
moon_lon = 155.5984
deg_in_nak = moon_lon % (360.0 / 27.0)
frac = deg_in_nak / (360.0 / 27.0)

def get_dasha_at_date(target_date: date, days_per_year: float):
    first_lord = "sun"
    first_years = VIMSHOTTARI_DASHA_YEARS["sun"]
    elapsed_days = frac * first_years * days_per_year
    first_start = birth_date - timedelta(days=round(elapsed_days))
    
    seq = VIMSHOTTARI_SEQUENCE
    start_idx = seq.index(first_lord)
    
    cur_start = first_start
    for i in range(len(seq)):
        md_lord = seq[(start_idx + i) % len(seq)]
        md_years = VIMSHOTTARI_DASHA_YEARS[md_lord]
        md_days = md_years * days_per_year
        md_end = cur_start + timedelta(days=round(md_days))
        
        if cur_start <= target_date < md_end:
            # Found MD. Now find AD
            ad_start = cur_start
            ad_start_idx = seq.index(md_lord)
            for j in range(len(seq)):
                ad_lord = seq[(ad_start_idx + j) % len(seq)]
                ad_years = VIMSHOTTARI_DASHA_YEARS[ad_lord]
                ad_days = md_days * (ad_years / VIMSHOTTARI_TOTAL_YEARS)
                ad_end = ad_start + timedelta(days=round(ad_days))
                
                if ad_start <= target_date < ad_end:
                    # Found AD. Now find PD
                    pd_start = ad_start
                    pd_start_idx = seq.index(ad_lord)
                    for k in range(len(seq)):
                        pd_lord = seq[(pd_start_idx + k) % len(seq)]
                        pd_years = VIMSHOTTARI_DASHA_YEARS[pd_lord]
                        pd_days = ad_days * (pd_years / VIMSHOTTARI_TOTAL_YEARS)
                        pd_end = pd_start + timedelta(days=round(pd_days))
                        
                        if pd_start <= target_date < pd_end:
                            return md_lord, ad_lord, pd_lord, cur_start, md_end, ad_start, ad_end, pd_start, pd_end
                        pd_start = pd_end
                ad_start = ad_end
        cur_start = md_end
    return "N/A", "N/A", "N/A", None, None, None, None, None, None

events = [
    (date(2016, 8, 15), "Property Finalized (Aug 2016)"),
    (date(2016, 12, 15), "Property Agreement (Dec 2016)"),
    (date(2021, 6, 15), "Shifted to Own Home (June 2021)"),
    (date(2008, 3, 8), "Father's Demise (March 2008)"),
    (date(2025, 12, 25), "Mother's Demise (Dec 2025)"),
]

print("="*90)
print("SIDE-BY-SIDE COMPARISON: SOLAR (JH) vs CHAANDRA (VINAY JI CANONICAL)")
print("="*90)

for d, ev_name in events:
    print(f"\n>>> EVENT: {ev_name.upper()} [{d}]")
    
    # 1. Solar (JH standard: 365.2422)
    md_s, ad_s, pd_s, ms_s, me_s, as_s, ae_s, ps_s, pe_s = get_dasha_at_date(d, 365.2422)
    print(f"  A. SOLAR (Jagannatha Hora / 365.24 days):")
    print(f"     MD-AD-PD: {md_s.upper()} - {ad_s.upper()} - {pd_s.upper()}")
    print(f"     AD Window: {ad_s.upper()} from {as_s} to {ae_s}")
    
    # 2. Chaandra (Vinay Ji 360-Tithi: 354.3670)
    md_c, ad_c, pd_c, ms_c, me_c, as_c, ae_c, ps_c, pe_c = get_dasha_at_date(d, 354.3670)
    print(f"  B. CHAANDRA (Vinay Ji 360-Tithis / 354.37 days):")
    print(f"     MD-AD-PD: {md_c.upper()} - {ad_c.upper()} - {pd_c.upper()}")
    print(f"     AD Window: {ad_c.upper()} from {as_c} to {ae_c}")
