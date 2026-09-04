"""
AstroOS — CSV to JSONL Benchmark Synchronizer
============================================
Converts human-curated CSV event files (e.g. data/benchmark/events.death.csv)
into the production data/benchmark/events.jsonl format.
"""

import csv
import json
import sys
from pathlib import Path

DATA_BENCH = Path("data/benchmark")

def sync_csv_to_events_jsonl(csv_filename: str = "events.death.csv"):
    csv_path = DATA_BENCH / csv_filename
    jsonl_path = DATA_BENCH / "events.jsonl"
    
    if not csv_path.exists():
        print(f"Error: {csv_path} does not exist.")
        return

    # Read existing events to preserve other domains
    existing_events = []
    if jsonl_path.exists():
        with jsonl_path.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    existing_events.append(json.loads(line))

    # Existing keys
    existing_keys = {(ev["case_id"], ev["event_type"], ev["date"]) for ev in existing_events}
    new_count = 0

    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["case_id"].strip()
            etype = row["event_type"].strip()
            edate = row["date"].strip()
            prec = row["precision"].strip()
            source = row["source"].strip()
            verified = row.get("verified", "true").lower() in ("true", "1", "yes")

            if not cid or not etype or not edate:
                continue

            key = (cid, etype, edate)
            ev_obj = {
                "case_id": cid,
                "event_type": etype,
                "date": edate,
                "precision": prec,
                "source": source,
                "source_url": row.get("source_url", "").strip(),
                "verified_by": row.get("verified_by", "Curator").strip(),
                "notes": row.get("notes", "").strip(),
                "verified": verified,
            }

            if key not in existing_keys:
                existing_events.append(ev_obj)
                existing_keys.add(key)
                new_count += 1

    # Write back
    with jsonl_path.open("w", encoding="utf-8") as f:
        for ev in existing_events:
            f.write(json.dumps(ev) + "\n")

    print(f"Successfully synced {new_count} new events from {csv_filename} into {jsonl_path} (Total: {len(existing_events)}).")

if __name__ == "__main__":
    fn = sys.argv[1] if len(sys.argv) > 1 else "events.death.csv"
    sync_csv_to_events_jsonl(fn)
