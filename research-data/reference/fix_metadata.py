import json, os

BASE = "C:/Users/rkmau/.claude/projects/c--Users-rkmau--claude/datasets/rf"

# Path, correct_type_code
fixes = [
    ("nakshatras/ASTRO-RF-NAK-v1.0.0/ASTRO-RF-NAKSHATRAS-v1.0.0_CSV_metadata.json", "NAK"),
    ("padas/ASTRO-RF-PADA-v1.0.0/ASTRO-RF-PADAS-v1.0.0_CSV_metadata.json", "PADA"),
    ("planets/ASTRO-RF-PLANET-v1.0.0/ASTRO-RF-PLANETS-v1.0.0_CSV_metadata.json", "PLANET"),
    ("houses/ASTRO-RF-HOUSE-v1.0.0/ASTRO-RF-HOUSES-v1.0.0_CSV_metadata.json", "HOUSE"),
    ("ephemeris/ASTRO-RF-EPHEM-v1.0.0/ASTRO-RF-EPHEMERIS-v1.0.0_CSV_metadata.json", "EPHEM"),
    ("ayanamsa/ASTRO-RF-AYAN-v1.0.0/ASTRO-RF-AYANAMSA-v1.0.0_CSV_metadata.json", "AYAN"),
    ("timezone/ASTRO-RF-TZ-v1.0.0/ASTRO-RF-TIMEZONE-v1.0.0_CSV_metadata.json", "TZ"),
]

for relpath, correct_code in fixes:
    old_path = os.path.join(BASE, relpath)
    if not os.path.exists(old_path):
        print(f"NOT FOUND: {old_path}")
        continue

    with open(old_path) as f:
        meta = json.load(f)

    correct_id = f"ASTRO-RF-{correct_code}-v1.0.0"
    meta["dataset_id"] = correct_id
    meta["dataset_version"] = correct_id
    meta["type_code"] = correct_code
    meta["type"] = correct_code

    dir_part = os.path.dirname(old_path)
    new_filename = f"{correct_id}_CSV_metadata.json"
    new_path = os.path.join(dir_part, new_filename)

    with open(new_path, "w") as f:
        json.dump(meta, f, indent=2)

    os.remove(old_path)
    print(f"FIXED: {old_path} -> {new_path}")

print("\nAll metadata corrected.")
