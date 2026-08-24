#!/usr/bin/env python3
"""
AstroOS — Astro-Databank CSV -> Research Case Import JSON converter

Converts the Astro-Databank-style export format (fname,lname,gender,place,
country,day,month,year,hour,min,jdUt,calType,lat,lng,rr,evnList,event_name,
catList,category_name) into the JSON payload AstroOS's Case Import actually
accepts (POST /api/v1/research/cases/import — schemas/research_case.py's
ResearchCaseBatchImportSchema).

Two real bugs this script deliberately avoids:
1. Reconstructing the birth date from day/month/year assuming Gregorian
   would be WRONG for calType='j' (Julian calendar) rows, common for dates
   before the Oct 1582 Gregorian reform. Since the source already provides
   jdUt (an absolute, calendar-independent Julian Day already resolved to
   UT), this script converts FROM jdUt back to a proleptic Gregorian
   calendar date/time via Swiss Ephemeris (swe.revjul) instead of trusting
   the source's own day/month/year columns — sidesteps the calendar
   question entirely, and gives us a UTC instant we can trust directly.
2. Since we now have a trustworthy exact UTC instant from jdUt, `tob` is
   populated for display but `timezone` is set to "UTC" and `dob`/`tob`
   are the ALREADY-UTC values — avoiding a second, redundant, error-prone
   local-time round-trip through an assumed historical IANA zone.

Event taxonomy mapping: Astro-Databank's free-text event names do not
match AstroOS's fixed 22-value EventType enum. Only names with an
unambiguous match are mapped (Marriage, Death of Spouse via "Death of
Mate", Death of Parent via "Death of Mother"/"Death of Father"); every
other event (including the subject's own death, for which AstroOS's
enum has no dedicated category) maps to type="Other" with the FULL
original event/category text preserved in `category`, `tags`, and
`description` — no data is discarded, just not force-fit into the wrong
bucket.

Usage:
    python scripts/convert_astrodatabank_csv.py <input.csv> <output.json> [--limit N]
"""

from __future__ import annotations

import csv
import json
import sys

import swisseph as swe

# Astro-Databank event-name substring -> AstroOS EventType enum value.
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
    ephemeris_wrapper.py convention (Gregorian throughout, calendar flag
    SE_GREG_CAL) regardless of what calendar the source date was recorded
    in."""
    year, month, day, ut_hour = swe.revjul(jd_ut, swe.GREG_CAL)
    return year, month, day, ut_hour


def _split_multi(value: str) -> list[str]:
    return [v.strip() for v in value.split(";") if v.strip()]


def convert_row(row: dict[str, str]) -> dict:
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
    # category_name entries don't align 1:1 with event_name entries (they're
    # independent lists per the source format) — attach the FULL category
    # list to every event so no information is lost, rather than guessing
    # a wrong 1:1 pairing.
    full_category_text = "; ".join(category_names)

    life_events = []
    if not event_names:
        event_names = ["Unspecified event (source had no event_name)"]
    for evt in event_names:
        life_events.append({
            "type": _map_event_type(evt),
            "event_date": dob,  # source only gives ONE date (the jdUt) shared by all listed events for this person
            "category": full_category_text[:100] if full_category_text else "Other",
            "verified": row.get("rr", "").strip().upper() in ("AA", "A"),
            "source": "Astro-Databank import",
            "description": evt,
            "tags": category_names,
        })

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
            "timezone": "UTC",  # dob/tob above are already the UTC instant (see module docstring point 2)
            "source": "Astro-Databank import",
        },
        "ayanamsa": "lahiri",
        "house_system": "P",
        "life_events": life_events,
        "source_batch": "astrodatabank-import",
    }


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    with open(input_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader if r.get("fname", "").strip()]

    if limit:
        rows = rows[:limit]

    cases = [convert_row(r) for r in rows]
    payload = {"cases": cases, "generate_ids": True}

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"Converted {len(cases)} case(s) -> {output_path}")
    unmapped = sum(1 for c in cases for e in c["life_events"] if e["type"] == "Other")
    total_events = sum(len(c["life_events"]) for c in cases)
    print(f"Event types: {total_events - unmapped}/{total_events} mapped to a specific EventType, {unmapped} mapped to 'Other' (full text preserved in description/tags).")


if __name__ == "__main__":
    main()
