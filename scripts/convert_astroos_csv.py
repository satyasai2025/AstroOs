#!/usr/bin/env python3
"""
AstroOS — Public Biographical CSV -> Research Case Import JSON converter

Converts a publicly-available astrological biography dataset (collected
by the AstroOS team; column shape: fname,lname,gender,place,country,day,
month,year,hour,min,jdUt,calType,lat,lng,rr,evnList,event_name,catList,
category_name) into batched JSON payloads AstroOS's Case Import actually
accepts (POST /api/v1/research/cases/import — schemas/research_case.py's
ResearchCaseBatchImportSchema, capped at 1000 cases per request).

Filtering (per explicit user decision): rows with calType='j' (Julian
calendar) and rows with unknown/malformed hour or min (genuine dirty
source data, e.g. hour="unknown, 12") are DROPPED, not guessed at. Drop
counts are reported, never silently swallowed.

Two real bugs this script deliberately avoids for the KEPT rows:
1. Reconstructing the birth date from day/month/year assuming Gregorian
   would be WRONG for calType='j' rows — moot now since those are
   dropped, but jdUt (already-resolved absolute UT Julian Day) is still
   used as the source of truth for date/time, converted via Swiss
   Ephemeris (swe.revjul), rather than trusting day/month/year directly.
2. Since jdUt gives a trustworthy exact UTC instant, `timezone` is set to
   "UTC" and `dob`/`tob` are the already-UTC values — avoiding a second,
   redundant, error-prone local-time round-trip through an assumed
   historical IANA zone.

Event taxonomy: `event_name` entries map to AstroOS's fixed EventType
enum where unambiguous, else "Other". `category_name` entries are a
SEPARATE, independent list in the source format (not 1:1 with events) —
each becomes its own life_event with type="Other" and a real
`category_path` (open, auto-creating tree — see
apps/api/services/event_category_service.py), rather than guessing a
wrong event<->category pairing. No data is discarded.

Usage:
    python scripts/convert_astroos_csv.py <input.csv> <output_prefix> [--limit N] [--batch-size 1000] [--only-relationship]

--only-relationship keeps ONLY marriage/relationship data per person —
event_name entries under the source's own "Relationship / ..." prefix and
category_name entries under "Family & Relations / Relationship / ..." —
dropping every other event/category, and dropping entirely any person who
has no relationship/marriage data at all (rather than fabricating a
placeholder event for them).

Writes <output_prefix>_batch_001.json, _batch_002.json, ... (one file per
<=1000-case batch) plus a summary printed to stdout.
"""

from __future__ import annotations

import csv
import json
import sys

import swisseph as swe

_DEFAULT_BATCH_SIZE = 1000

# Source event-name substring -> AstroOS EventType enum value.
# Only unambiguous matches; anything else falls through to "Other".
_EVENT_TYPE_MAP: list[tuple[str, str]] = [
    ("Relationship / Marriage", "Marriage"),
    ("Death of Mate", "Death of Spouse"),
    ("Death of Mother", "Death of Parent"),
    ("Death of Father", "Death of Parent"),
    ("Work / Gain social status", "Promotion"),
]


def _map_event_type(event_name: str) -> str:
    for needle, event_type in _EVENT_TYPE_MAP:
        if needle in event_name:
            return event_type
    return "Other"


def _jd_ut_to_datetime_parts(jd_ut: float) -> tuple[int, int, int, float]:
    """jdUt -> (year, month, day, ut_hour_decimal) in the proleptic
    Gregorian calendar, via Swiss Ephemeris — matches AstroOS's own
    ephemeris_wrapper.py convention (Gregorian throughout)."""
    year, month, day, ut_hour = swe.revjul(jd_ut, swe.GREG_CAL)
    return year, month, day, ut_hour


def _split_multi(value: str) -> list[str]:
    return [v.strip() for v in value.split(";") if v.strip()]


def _is_dirty_time(row: dict[str, str]) -> bool:
    try:
        int(row["hour"])
        int(row["min"])
        return False
    except (ValueError, TypeError, KeyError):
        return True


def _is_julian(row: dict[str, str]) -> bool:
    return row.get("calType", "").strip().lower() == "j"


def _is_bad_coordinate(row: dict[str, str]) -> bool:
    """Genuine dirty source data — e.g. lat=150.1833 for Whittingehame,
    Scotland (real lat ~55.87) — not a parsing bug, dropped like the
    Julian/dirty-time rows rather than clamped or guessed at."""
    try:
        lat = float(row["lat"])
        lng = float(row["lng"])
        return not (-90.0 <= lat <= 90.0) or not (-180.0 <= lng <= 180.0)
    except (ValueError, TypeError, KeyError):
        return True


def _is_relationship_event(event_name: str) -> bool:
    """Matches the source's own "Relationship / ..." event_name prefix
    (Marriage, Divorce dates, Begin/End significant relationship, etc.)."""
    return event_name.strip().startswith("Relationship / ")


def _is_relationship_category(category_name: str) -> bool:
    """Matches the source's own "Family & Relations / Relationship / ..."
    category_name prefix (Marriage - Very happy, Number of Divorces,
    Mate - Noted, etc.)."""
    return category_name.strip().startswith("Family & Relations / Relationship / ")


def convert_row(row: dict[str, str], *, only_relationship: bool = False) -> dict:
    fname = row["fname"].strip()
    lname = row["lname"].strip()
    name = f"{fname} {lname}".strip()

    gender_map = {"m": "Male", "f": "Female"}
    gender = gender_map.get(row["gender"].strip().lower(), "Other")

    jd_ut = float(row["jdUt"])
    year, month, day, ut_hour = _jd_ut_to_datetime_parts(jd_ut)
    hh = int(ut_hour)
    mm = int(round((ut_hour - hh) * 60))
    if mm == 60:
        mm = 0
        hh += 1
    dob = f"{year:04d}-{month:02d}-{day:02d}"
    tob = f"{hh:02d}:{mm:02d}"

    lat = float(row["lat"])
    lng = float(row["lng"])

    event_names = _split_multi(row.get("event_name", ""))
    category_names = _split_multi(row.get("category_name", ""))
    if only_relationship:
        event_names = [e for e in event_names if _is_relationship_event(e)]
        category_names = [c for c in category_names if _is_relationship_category(c)]
    verified = row.get("rr", "").strip().upper() in ("AA", "A")

    life_events = []

    # Real dated events (from event_name) — no category_path guessed, since
    # category_name is an independent list in this source format, not
    # paired 1:1 with individual events.
    for evt in event_names:
        life_events.append({
            "type": _map_event_type(evt),
            "event_date": dob,  # source gives one date (jdUt) shared by all listed events for this person
            "category": "Other",
            "verified": verified,
            "source": "AstroOS public dataset import",
            "description": evt,
        })

    # Biographical/notability category tags (from category_name) — each
    # becomes its own life_event carrying a real category_path into the
    # open category tree, rather than truncating/collapsing them.
    for cat in category_names:
        path = [p.strip() for p in cat.split(" / ") if p.strip()]
        if not path:
            continue
        life_events.append({
            "type": "Other",
            "event_date": dob,
            "category": cat[:100],
            "category_path": path,
            "verified": verified,
            "source": "AstroOS public dataset import (category tag)",
            "description": cat,
        })

    if not life_events and only_relationship:
        # No marriage/relationship data for this person at all — drop them
        # rather than fabricating a placeholder event, since the whole
        # point of --only-relationship is a person actually has that data.
        return None

    if not life_events:
        life_events = [{
            "type": "Other",
            "event_date": dob,
            "category": "Other",
            "verified": verified,
            "source": "AstroOS public dataset import",
            "description": "Unspecified (source had no event_name or category_name)",
        }]

    return {
        "person": {
            "name": name,
            "gender": gender,
            "dob": dob,
            "tob": tob,
            "place": row["place"].strip(),
            "country": row["country"].strip() or None,
            "latitude": round(lat, 6),
            "longitude": round(lng, 6),
            "timezone": "UTC",  # dob/tob above are already the UTC instant (see module docstring)
            "source": "AstroOS public dataset import",
        },
        "ayanamsa": "lahiri",
        "house_system": "P",
        "life_events": life_events,
        "source_batch": "astroos-public-dataset-import-relationship-only" if only_relationship else "astroos-public-dataset-import",
    }


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    input_path = sys.argv[1]
    output_prefix = sys.argv[2]
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    batch_size = _DEFAULT_BATCH_SIZE
    if "--batch-size" in sys.argv:
        batch_size = int(sys.argv[sys.argv.index("--batch-size") + 1])
    only_relationship = "--only-relationship" in sys.argv

    with open(input_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        all_rows = [r for r in reader if r.get("fname", "").strip()]

    total = len(all_rows)
    julian_dropped = sum(1 for r in all_rows if _is_julian(r))
    dirty_time_dropped = sum(1 for r in all_rows if _is_dirty_time(r))
    bad_coord_dropped = sum(1 for r in all_rows if _is_bad_coordinate(r))
    rows = [
        r for r in all_rows
        if not _is_julian(r) and not _is_dirty_time(r) and not _is_bad_coordinate(r)
    ]
    dropped = total - len(rows)

    print(f"Total source rows: {total}")
    print(f"Dropped (Julian calType): {julian_dropped}")
    print(f"Dropped (unknown/malformed hour or min): {dirty_time_dropped}")
    print(f"Dropped (lat/lng out of valid range): {bad_coord_dropped}")
    print(f"Total dropped (union): {dropped}")
    print(f"Remaining clean rows: {len(rows)}")

    if limit:
        rows = rows[:limit]
        print(f"--limit applied: converting only {len(rows)} row(s)")

    converted = [convert_row(r, only_relationship=only_relationship) for r in rows]
    cases = [c for c in converted if c is not None]
    if only_relationship:
        no_relationship_data = len(converted) - len(cases)
        print(f"--only-relationship applied: dropped {no_relationship_data} person(s) with no relationship/marriage data")

    num_batches = (len(cases) + batch_size - 1) // batch_size if cases else 0
    for i in range(num_batches):
        batch = cases[i * batch_size : (i + 1) * batch_size]
        payload = {"cases": batch, "generate_ids": True}
        out_path = f"{output_prefix}_batch_{i + 1:03d}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"Wrote {len(batch)} case(s) -> {out_path}")

    total_events = sum(len(c["life_events"]) for c in cases)
    with_category_path = sum(
        1 for c in cases for e in c["life_events"] if "category_path" in e
    )
    print(f"Total life_events emitted: {total_events} ({with_category_path} carry a real category_path).")


if __name__ == "__main__":
    main()
