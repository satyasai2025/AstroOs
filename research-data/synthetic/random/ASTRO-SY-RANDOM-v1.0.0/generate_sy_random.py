"""Generate SY-RANDOM v1.0.0 — 100K random birth records.
Seeded RNG for reproducibility. Geographic distribution approximates global population.
Output: CSV with raw birth data (no computed astrology)."""

import hashlib, json, os, csv

SEED = 42
RNG = __import__('random').Random(SEED)

# Geographic distribution: region -> (weight, countries, lat_range, lng_range)
REGIONS = [
    ("asia", 0.60, ["IN","CN","JP","KR","ID","TH","VN","PH","MY","PK","BD","IR"],
     [(5,40), (60,150)]),
    ("africa", 0.17, ["NG","ZA","KE","EG","GH","MA","ET","TZ"],
     [(-35,37), (-20,55)]),
    ("europe", 0.10, ["GB","DE","FR","IT","ES","NL","SE","PL","GR","PT"],
     [(35,70), (-10,40)]),
    ("north_america", 0.08, ["US","CA","MX"],
     [(15,70), (-130,-60)]),
    ("south_america", 0.045, ["BR","AR","CO","CL","PE","EC"],
     [(-55,12), (-80,-35)]),
    ("oceania", 0.005, ["AU","NZ"],
     [(-45,-10), (110,180)])
]

# Ensure weights sum to 1.0
total_w = sum(r[1] for r in REGIONS)
REGIONS = [(r[0], r[1]/total_w, r[2], r[3]) for r in REGIONS]

def random_birth():
    """Generate a random birth record."""
    # Pick region by weight
    r = RNG.random()
    cum = 0
    for region_name, weight, countries, (lat_range, lng_range) in REGIONS:
        cum += weight
        if r <= cum:
            break

    # Birth date: uniform 1900-2020
    year = RNG.randint(1900, 2020)
    month = RNG.randint(1, 12)
    max_day = [0,31,29,31,30,31,30,31,31,30,31,30,31][month]
    if month == 2 and year % 4 != 0:
        max_day = 28
    day = RNG.randint(1, max_day)

    # Birth time: uniform 24h
    hour = RNG.randint(0, 23)
    minute = RNG.randint(0, 59)
    second = RNG.randint(0, 59)

    # Location: within region bounds
    lat = round(RNG.uniform(lat_range[0], lat_range[1]), 4)
    lng = round(RNG.uniform(lng_range[0], lng_range[1]), 4)
    country = RNG.choice(countries)

    # Timezone: rough estimate from longitude
    tz_offset = round(lng / 15) * 60  # minutes

    birth_date = f"{year:04d}-{month:02d}-{day:02d}"
    birth_time = f"{hour:02d}:{minute:02d}:{second:02d}"

    return {
        "birth_date": birth_date,
        "birth_time": birth_time,
        "birth_year": year,
        "birth_month": month,
        "birth_dow": (year + year//4 - year//100 + year//400 + (13*month+8)//5 + day) % 7,
        "birth_hour": hour + minute/60.0,
        "latitude": lat,
        "longitude": lng,
        "country_code": country,
        "timezone_offset_minutes": tz_offset,
        "region": region_name
    }

# Generate
N = 100000
records = [random_birth() for _ in range(N)]

# Write CSV
BASE = "C:/Users/rkmau/.claude/projects/c--Users-rkmau--claude/datasets/sy/random/ASTRO-SY-RANDOM-v1.0.0"
path = os.path.join(BASE, "ASTRO-SY-RANDOM-v1.0.0_CSV.csv")

fieldnames = ["_record_id","_dataset_id","_record_type","_version","_is_deleted",
              "birth_date","birth_time","birth_year","birth_month","birth_dow","birth_hour",
              "latitude","longitude","country_code","timezone_offset_minutes","region",
              "confidence_tier","privacy_tier"]

with open(path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for i, rec in enumerate(records):
        row = {
            "_record_id": f"ASTRO-REC-RANDOM-{i+1:06d}",
            "_dataset_id": "ASTRO-SY-RANDOM-v1.0.0",
            "_record_type": "synthetic",
            "_version": 1,
            "_is_deleted": "false",
            **rec,
            "confidence_tier": "synthetic",
            "privacy_tier": "public"
        }
        writer.writerow(row)

checksum = hashlib.sha256()
with open(path, "rb") as f:
    checksum.update(f.read())

print(f"SY-RANDOM generated: {N} records")
print(f"File: {path}")
print(f"Size: {os.path.getsize(path)} bytes")
print(f"SHA256: {checksum.hexdigest()}")

# Verify distribution
from collections import Counter
regions = Counter(r["region"] for r in records)
print("\nGeographic distribution:")
for reg, count in sorted(regions.items()):
    pct = count/N*100
    print(f"  {reg}: {count} ({pct:.1f}%)")

# Year range
years = [r["birth_year"] for r in records]
print(f"\nYear range: {min(years)}-{max(years)}")
print(f"Hour range: {min(r['birth_hour'] for r in records):.1f}-{max(r['birth_hour'] for r in records):.1f}")
