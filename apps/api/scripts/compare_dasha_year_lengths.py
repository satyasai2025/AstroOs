import sys
from pathlib import Path
sys.path.insert(0, ".")
from datetime import datetime, timezone, date, timedelta
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from packages.shared.constants import VIMSHOTTARI_DASHA_YEARS, VIMSHOTTARI_SEQUENCE, VIMSHOTTARI_TOTAL_YEARS

# Let's compare:
# 1. Solar Year: 365.2422 days (Jagannatha Hora default)
# 2. Savana Year: 360.0000 days (360 solar days - often cited in classical texts)
# 3. Chaandra Year: 354.3670 days (360 tithis - Vinay Ji's canonical proposal)

birth_dt = datetime(1971, 6, 29, 23, 27, 40, tzinfo=timezone.utc)
birth_date = birth_dt.date()

# Moon longitude in Virgo: 155.60° (approx)
wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
from apps.api.services.horoscope_engine import HoroscopeEngine
he = HoroscopeEngine(wrapper)
natal = he.generate_d1(birth_dt, 22.3072, 73.1812)
moon = next(p for p in natal.planets if p.planet == "moon")
moon_lon = moon.sidereal_longitude

# Moon is in Uttara Phalguni (Sun's nakshatra, nakshatra index 11)
deg_in_nak = moon_lon % (360.0 / 27.0)
frac = deg_in_nak / (360.0 / 27.0)

print(f"Moon Sidereal Longitude: {moon_lon:.4f}° ({moon.rashi} {moon.rashi_degree:.2f}°)")
print(f"Nakshatra: {moon.nakshatra} | Fraction Elapsed: {frac:.4f}")

def compute_dasha_dates(days_per_year: float, mode_name: str):
    print(f"\n--- {mode_name.upper()} (Year = {days_per_year:.4f} days) ---")
    first_lord = "sun"
    first_years = VIMSHOTTARI_DASHA_YEARS["sun"] # 6 years
    balance_years = (1.0 - frac) * first_years
    elapsed_days = frac * first_years * days_per_year
    first_start = birth_date - timedelta(days=round(elapsed_days))
    
    seq = VIMSHOTTARI_SEQUENCE
    start_idx = seq.index(first_lord)
    
    cur_start = first_start
    for i in range(len(seq)):
        lord = seq[(start_idx + i) % len(seq)]
        y = VIMSHOTTARI_DASHA_YEARS[lord]
        duration_days = y * days_per_year
        cur_end = cur_start + timedelta(days=round(duration_days))
        
        # Check Jupiter and Saturn MDs
        if lord in ("jupiter", "saturn", "sun", "moon", "mars", "rahu"):
            print(f"  {lord.upper():7} MD: {cur_start} to {cur_end} ({y} yrs, {round(duration_days)} days)")
        cur_start = cur_end

compute_dasha_dates(365.2422, "1. Solar Year (Jagannatha Hora / Modern Standard)")
compute_dasha_dates(360.0000, "2. Savana Year (360 Civil Days)")
compute_dasha_dates(354.3670, "3. Chaandra Year (360 Tithis - Vinay Ji Canonical)")
