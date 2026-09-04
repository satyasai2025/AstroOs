import sys
from pathlib import Path
sys.path.insert(0, ".")
from datetime import datetime, timezone, date
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.dasha_engine import DashaEngine

wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
de = DashaEngine(wrapper)

birth_dt = datetime(1971, 6, 29, 23, 27, 40, tzinfo=timezone.utc)
tree = de.compute_vimshottari(birth_dt, 22.3072, 73.1812, max_depth=4)

print("="*80)
print("ASTROOS VIMSHOTTARI TREE: JUPITER MD -> MARS AD (ALL 9 PRATYANTARDASHAS)")
print("="*80)

for md in tree.mahadashas:
    if md.lord.lower() == "jupiter":
        print(f"JUPITER MD: {md.start_date} to {md.end_date}")
        for ad in md.sub_periods:
            if ad.lord.lower() == "mars":
                print(f"  MARS AD: {ad.start_date} to {ad.end_date} ({ad.duration_days} days)")
                for pd in ad.sub_periods:
                    print(f"    {pd.lord.upper():7} PD: {pd.start_date} to {pd.end_date} ({pd.duration_days} days)")
                    if pd.lord.lower() in ("mars", "jupiter"):
                        print(f"      Sookshma-antardashas in {pd.lord.upper()} PD:")
                        for sd in pd.sub_periods:
                            print(f"        {sd.lord.upper():7} SD: {sd.start_date} to {sd.end_date} ({sd.duration_days} days)")
