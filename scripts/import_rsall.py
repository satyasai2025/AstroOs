#!/usr/bin/env python3
"""
AstroOS — rsAll Research Dataset Importer
Parses and ingests the 4,688 specialized research cases from rsAll.
"""

import os
import re
import csv
import json
from datetime import datetime
from collections import Counter
from typing import Dict, List, Any

RS_DIR = r"C:\Users\rkmau\Downloads\rsAll\rsAll"
OUT_DIR = r"c:\Users\rkmau\Downloads\ReplitplusClaude\AstroOS\data\rsall"


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_event_line(line: str) -> Dict[str, Any]:
    cleaned = line.strip()
    cleaned = re.sub(r"\s*chart\s+Placidus\s+Equal_H\.?", "", cleaned, flags=re.IGNORECASE).strip()
    
    event_type = "Other"
    event_date = ""
    event_time = ""
    location = ""
    description = ""
    
    if ":" in cleaned:
        parts = cleaned.split(":", 1)
        event_type = parts[0].strip()
        rem = parts[1].strip()
    else:
        rem = cleaned

    m_date = re.search(
        r"(\d{1,2}\s+[A-Za-z]+\s+\d{4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4}|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b|\b\d{4}\b)",
        rem
    )
    if m_date:
        event_date = m_date.group(1).strip()
        after_date = rem[m_date.end():].strip()
        
        m_time = re.search(r"at\s+([0-9]{1,2}:[0-9]{2}(?::[0-9]{2})?\s*(?:AM|PM|am|pm)?)", after_date)
        if m_time:
            event_time = m_time.group(1).strip()
            after_date = after_date[m_time.end():].strip()
            
        m_loc = re.search(r"in\s+([^(]+)", after_date)
        if m_loc:
            location = m_loc.group(1).strip().rstrip(";").strip()
            after_date = after_date[m_loc.end():].strip()
            
        m_desc = re.search(r"\((.+)\)", after_date)
        if m_desc:
            description = m_desc.group(1).strip()
        else:
            description = after_date.strip(" ()")
    else:
        description = rem

    return {
        "event_type": event_type,
        "event_date": event_date,
        "event_time": event_time,
        "location": location,
        "description": description,
        "raw_text": line.strip()
    }


def parse_rs_file(filepath: str, filename: str) -> Dict[str, Any]:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        
    case_id = os.path.splitext(filename)[0]
    
    m_id = re.search(r"_(\d+)$", case_id)
    adb_id = int(m_id.group(1)) if m_id else None
    
    category = "General Research"
    if case_id.startswith("Research_"):
        cat_part = case_id.replace("Research_", "")
        cat_part = re.sub(r"_\d+$", "", cat_part)
        category = cat_part.replace("__", ": ").replace("_", " ").strip()
    elif "_" in case_id:
        category = case_id.split("_")[0]

    biography = ""
    if "START BIOGRAPHY" in content:
        bio_part = content.split("START BIOGRAPHY")[1]
        bio_part = bio_part.split("START")[0].strip()
        biography = clean_text(bio_part)
        
    source_notes = ""
    rodden_rating = "Unknown"
    if "START SOURCE NOTES" in content:
        sn_part = content.split("START SOURCE NOTES")[1]
        sn_part = sn_part.split("START")[0].strip()
        source_notes = clean_text(sn_part)
        
        if re.search(r"\b(AA|BC|BR in hand|birth certificate)\b", source_notes, re.I):
            rodden_rating = "AA"
        elif re.search(r"\b(A|from memory|quoted)\b", source_notes, re.I):
            rodden_rating = "A"
        elif re.search(r"\b(B|biography|autobiography)\b", source_notes, re.I):
            rodden_rating = "B"
        elif re.search(r"\b(C|caution|rectified)\b", source_notes, re.I):
            rodden_rating = "C"
        elif re.search(r"\b(DD|conflict|unverified)\b", source_notes, re.I):
            rodden_rating = "DD"

    keywords = []
    if "START CATEGORY KEYWORDS" in content:
        kw_part = content.split("START CATEGORY KEYWORDS")[1].strip()
        keywords = [k.strip() for k in kw_part.split("\n") if k.strip()]

    events = []
    if "START EVENTS" in content:
        ev_part = content.split("START EVENTS")[1].split("END EVENTS")[0].strip()
        for line in ev_part.split("\n"):
            line = line.strip()
            if line:
                events.append(parse_event_line(line))

    birth_date = ""
    birth_time = ""
    
    m_birth = re.search(
        r"\bborn\s+(?:on\s+)?(\d{1,2}\s+[A-Za-z]+\s+\d{4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}/\d{1,2}/\d{4}|\d{4}/\d{1,2}/\d{1,2})",
        biography,
        re.I
    )
    if m_birth:
        birth_date = m_birth.group(1).strip()
        
    m_btime = re.search(
        r"(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\s*(?:[A-Z]{3,4})?)",
        biography
    )
    if m_btime and m_birth:
        birth_time = m_btime.group(1).strip()

    return {
        "case_id": case_id,
        "filename": filename,
        "adb_id": adb_id,
        "category": category,
        "rodden_rating": rodden_rating,
        "biography": biography,
        "source_notes": source_notes,
        "keywords": keywords,
        "events": events,
        "total_events": len(events),
        "embedded_birth_date": birth_date,
        "embedded_birth_time": birth_time,
        "has_embedded_birth": bool(birth_date)
    }


def run_import():
    print("Starting AstroOS rsAll Import Pipeline...")
    print(f"Source Directory: {RS_DIR}")
    
    os.makedirs(OUT_DIR, exist_ok=True)
    
    all_files = [f for f in os.listdir(RS_DIR) if f.endswith(".txt")]
    print(f"Found {len(all_files)} files in rsAll dataset.\n")
    
    parsed_cases = []
    category_counts = Counter()
    event_type_counts = Counter()
    total_events = 0
    cases_with_events = 0
    cases_with_birth = 0
    
    for i, fname in enumerate(all_files, 1):
        fpath = os.path.join(RS_DIR, fname)
        rec = parse_rs_file(fpath, fname)
        parsed_cases.append(rec)
        
        category_counts[rec["category"]] += 1
        if rec["total_events"] > 0:
            cases_with_events += 1
            total_events += rec["total_events"]
            for ev in rec["events"]:
                event_type_counts[ev["event_type"]] += 1
                
        if rec["has_embedded_birth"]:
            cases_with_birth += 1
            
        if i % 1000 == 0 or i == len(all_files):
            print(f"  Parsed {i}/{len(all_files)} files... (Cases with events: {cases_with_events}, Total events: {total_events})")

    json_path = os.path.join(OUT_DIR, "rsall_catalog_full.json")
    print(f"\nWriting full JSON catalog to {json_path}...")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(parsed_cases, f, indent=2, ensure_ascii=False)

    csv_events_path = os.path.join(OUT_DIR, "rsall_events_database.csv")
    print(f"Writing flat events database to {csv_events_path}...")
    with open(csv_events_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "case_id", "adb_id", "category", "rodden_rating", "embedded_birth_date",
            "event_index", "event_type", "event_date", "event_time", "location", "description"
        ])
        for rec in parsed_cases:
            for idx, ev in enumerate(rec["events"], 1):
                writer.writerow([
                    rec["case_id"],
                    rec["adb_id"] or "",
                    rec["category"],
                    rec["rodden_rating"],
                    rec["embedded_birth_date"],
                    idx,
                    ev["event_type"],
                    ev["event_date"],
                    ev["event_time"],
                    ev["location"],
                    ev["description"]
                ])

    audit_path = os.path.join(OUT_DIR, "rsall_import_audit.json")
    audit_data = {
        "source_directory": RS_DIR,
        "total_files_processed": len(all_files),
        "cases_with_structured_events": cases_with_events,
        "total_events_extracted": total_events,
        "cases_with_embedded_birth_data": cases_with_birth,
        "top_categories": dict(category_counts.most_common(25)),
        "top_event_types": dict(event_type_counts.most_common(20)),
        "import_timestamp": datetime.now().isoformat()
    }
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)

    print("\nImport Complete!")
    print(f"   Total Files Processed: {len(all_files):,}")
    print(f"   Cases with Verified Events: {cases_with_events:,}")
    print(f"   Total Real-Life Events Ingested: {total_events:,}")
    print(f"   Output Directory: {OUT_DIR}")


if __name__ == "__main__":
    run_import()
