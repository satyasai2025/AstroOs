#!/usr/bin/env python3
"""Export KundaleeStore JSON batches to CSV for spreadsheet analysis."""
import os, csv, json, re

BATCH_DIR = r"C:\Users\rkmau\Downloads\KundaleeStore_Full\KundaleeStore_Full\KundaleeStore\Imported\cases"
OUT_CSV   = r"C:\Users\rkmau\Downloads\KundaleeStore_Full\KundaleeStore_Full\KundaleeStore\Imported\kundalee_export.csv"

HEADERS = [
    "case_id", "name", "gender", "dob", "tob",
    "place", "latitude", "longitude", "timezone",
    "source", "birth_time_confidence",
    "ayanamsa", "house_system",
    "event_1_type", "event_1_date", "event_1_severity",
    "event_1_verified", "event_1_confidence", "event_1_description",
    "event_2_type", "event_2_date", "event_2_severity",
    "event_2_verified", "event_2_confidence", "event_2_description",
    "event_3_type", "event_3_date", "event_3_severity",
    "event_3_verified", "event_3_confidence", "event_3_description",
    "total_events",
    "research_notes", "source_batch",
]

def clean(val):
    if val is None: return ""
    s = str(val).strip().replace("\r", " ").replace("\n", " | ")
    return s

def flatten_case(case, idx):
    p = case.get("person", {})
    evs = case.get("life_events", [])
    row = {
        "case_id":                 f"KUND_{idx:06d}",
        "name":                    clean(p.get("name")),
        "gender":                 clean(p.get("gender")),
        "dob":                    clean(p.get("dob")),
        "tob":                    clean(p.get("tob")),
        "place":                  clean(p.get("place")),
        "latitude":               p.get("latitude"),
        "longitude":              p.get("longitude"),
        "timezone":               clean(p.get("timezone")),
        "source":                 clean(p.get("source")),
        "birth_time_confidence":  clean(p.get("birth_time_confidence")),
        "ayanamsa":               clean(case.get("ayanamsa")),
        "house_system":           clean(case.get("house_system")),
        "total_events":           len(evs),
        "research_notes":         clean(case.get("research_notes")),
        "source_batch":           clean(case.get("source_batch")),
    }
    for i, ev in enumerate(evs[:3]):
        prefix = f"event_{i+1}_"
        row[prefix+"type"]       = clean(ev.get("type"))
        row[prefix+"date"]      = clean(ev.get("event_date"))
        row[prefix+"severity"]  = clean(ev.get("severity"))
        row[prefix+"verified"]  = ev.get("verified", False)
        row[prefix+"confidence"]= clean(ev.get("confidence"))
        row[prefix+"description"]= clean(ev.get("description"))
    return row

def main():
    batches = sorted(d for d in os.listdir(BATCH_DIR)
                    if os.path.isdir(os.path.join(BATCH_DIR, d)))
    print(f"Found {len(batches)} batch folders")

    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as fout:
        writer = csv.DictWriter(fout, fieldnames=HEADERS, extrasaction="ignore")
        writer.writeheader()

        total = 0
        for bi, batch in enumerate(batches, 1):
            json_dir = os.path.join(BATCH_DIR, batch)
            json_files = sorted(f for f in os.listdir(json_dir) if f.endswith(".json"))
            for jf in json_files:
                with open(os.path.join(json_dir, jf), encoding="utf-8") as fin:
                    data = json.load(fin)
                for case in data.get("cases", []):
                    row = flatten_case(case, total + 1)
                    writer.writerow(row)
                    total += 1
            print(f"  Batch {bi}/{len(batches)} ({batch}): written {total} total cases")

    print(f"\nDone! {total} cases written to:\n  {OUT_CSV}")

if __name__ == "__main__":
    main()

