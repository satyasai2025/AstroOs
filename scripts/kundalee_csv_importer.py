#!/usr/bin/env python3
"""KundaleeStore CSV Import - fast version with in-memory dedup."""
import asyncio, csv, re, sys, time
from datetime import datetime
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(REPO_ROOT))

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.dependencies import _async_session_factory
from apps.api.schemas.research_case import (
    ResearchCaseBatchImportSchema, EventType, BirthTimeConfidence, SourceConfidence, Severity,
)
from apps.api.services.import_service import ResearchCaseImportService, SnapshotComputer

DATE_FORMATS = [
    "%Y-%m-%d", "%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y",
    "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y", "%Y.%m.%d",
    "%d %B, %Y", "%d %b, %Y", "%B %d %Y", "%b %d %Y",
    "%d-%B-%Y", "%d-%b-%Y", "%Y %B %d",
]
VALID_EVENT_TYPES = {e.value for e in EventType}
VALID_BTC = {e.value for e in BirthTimeConfidence}
VALID_CONFIDENCE = {e.value for e in SourceConfidence}
VALID_SEVERITY = {e.value for e in Severity}

def parse_date(s):
    if not s or not s.strip():
        return None
    s = s.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    m = re.match(r"^(\d{1,2})\s+at\s+(\d{4})$", s)
    if m:
        try:
            return datetime(int(m.group(2)), int(m.group(1)), 1).date()
        except ValueError:
            pass
    return None

def parse_bool(val):
    if not val or not val.strip():
        return False
    return val.strip().lower() in ("true", "1", "yes", "t", "y")

def safe_float(val):
    try:
        return float(val) if val.strip() else None
    except (ValueError, TypeError):
        return None

def fix_lat_lon(lat, lon):
    if lat is None and lon is None:
        return 0.0, 0.0
    if lat is None:
        return 0.0, lon or 0.0
    if lon is None:
        return lat, 0.0
    if abs(lat) > 90 and abs(lon) <= 90:
        return lon, lat
    if abs(lat) > 90 and abs(lon) > 90:
        return 0.0, 0.0
    return max(-90, min(90, lat)), max(-180, min(180, lon))

def map_event_type(csv_type):
    if csv_type in VALID_EVENT_TYPES:
        return csv_type
    aliases = {"Death Parent": "Death of Parent", "Death Spouse": "Death of Spouse"}
    return aliases.get(csv_type, "Other")

def map_btc(val):
    val = val.strip().lower() if val else ""
    return val if val in VALID_BTC else "medium"

def map_confidence(val):
    val = val.strip().lower() if val else ""
    return val if val in VALID_CONFIDENCE else "medium"

def map_severity(val):
    val = val.strip() if val else ""
    if val:
        val = val[0].upper() + val[1:].lower()
    return val if val in VALID_SEVERITY else "Moderate"

def row_to_payload(row):
    life_events = []
    for ev in [1, 2, 3]:
        ev_type = row.get(f"event_{ev}_type", "").strip()
        ev_date = row.get(f"event_{ev}_date", "").strip()
        if ev_type and ev_date:
            parsed = parse_date(ev_date)
            if parsed is None:
                continue
            life_events.append({
                "type": map_event_type(ev_type),
                "event_date": parsed.isoformat(),
                "severity": map_severity(row.get(f"event_{ev}_severity", "")),
                "verified": parse_bool(row.get(f"event_{ev}_verified", "")),
                "confidence": map_confidence(row.get(f"event_{ev}_confidence", "")),
                "source": "KundaleeStore",
                "description": row.get(f"event_{ev}_description", "").strip() or "",
            })
    if not life_events:
        return None
    lat, lon = fix_lat_lon(
        safe_float(row.get("latitude", "")),
        safe_float(row.get("longitude", "")),
    )
    return {
        "person": {
            "name": row["name"].strip()[:200],
            "gender": row.get("gender", "").strip() or "Other",
            "dob": row["dob"].strip(),
            "tob": row.get("tob", "").strip() or None,
            "place": row.get("place", "").strip() or "Unknown",
            "latitude": lat,
            "longitude": lon,
            "timezone": row.get("timezone", "").strip() or "UTC",
            "source": row.get("source", "").strip() or "KundaleeStore",
            "birth_time_confidence": map_btc(row.get("birth_time_confidence", "")),
        },
        "ayanamsa": row.get("ayanamsa", "lahiri").strip() or "lahiri",
        "house_system": row.get("house_system", "P").strip() or "P",
        "divisional_charts": ["D1"],
        "life_events": life_events,
        "research_notes": row.get("research_notes", "").strip() or "",
        "source_batch": row.get("source_batch", "kundaleestore_v2").strip() or "kundaleestore_v2",
    }

def make_dedup_key(row):
    """(name, dob, tob) tuple for duplicate detection."""
    return (
        row["name"].strip()[:200].lower(),
        row["dob"].strip(),
        row.get("tob", "").strip(),
    )

async def load_existing_keys():
    """Load all existing (name, dob, tob) keys into a set for O(1) dedup."""
    from apps.api.models.research_case import ResearchCaseModel
    from sqlalchemy import select
    existing = set()
    async with _async_session_factory() as session:
        result = await session.execute(
            select(ResearchCaseModel.person_name, ResearchCaseModel.dob, ResearchCaseModel.tob)
            .where(ResearchCaseModel.deleted_at.is_(None))
        )
        for row in result.all():
            key = (str(row.person_name or "").lower(), (row.dob.strftime("%Y-%m-%d") if hasattr(row.dob, "strftime") else str(row.dob or "")[:10]), str(row.tob or ""))
            existing.add(key)
    return existing

async def run(csv_path, dry_run):
    print(f"\n{'='*60}")
    print(f"KundaleeStore CSV Import (fast)")
    print(f"CSV: {csv_path}")
    print(f"Mode: {'DRY' if dry_run else 'LIVE'}")
    print(f"{'='*60}")

    # Load existing keys into memory
    print("Loading existing records for dedup...")
    existing_keys = await load_existing_keys()
    print(f"Existing records in DB: {len(existing_keys):,}\n")

    # Stream CSV and build filtered payloads
    print("Streaming CSV, filtering duplicates...")
    all_payloads = []
    skipped = 0
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            key = make_dedup_key(row)
            if key in existing_keys:
                skipped += 1
                continue
            payload = row_to_payload(row)
            if payload is None:
                skipped += 1
                continue
            existing_keys.add(key)  # dedup within CSV too
            all_payloads.append(payload)
    print(f"Filtered: {len(all_payloads):,} new | {skipped:,} skipped (dup+no-event)\n")

    if dry_run:
        print("Sample (first 3):")
        for p in all_payloads[:3]:
            print(f"  {p['person']['name']} | {p['person']['dob']} | Events: {len(p['life_events'])}")
        print(f"\nDRY RUN - {len(all_payloads)} rows would be imported.\n")
        return

    if not all_payloads:
        print("No new rows to import."); return

    BATCH = 1000
    batches = [all_payloads[i:i+BATCH] for i in range(0, len(all_payloads), BATCH)]
    print(f"Batches: {len(batches)}\n")
    print(f"{'Batch':>5}  {'Status':>8}  {'Cases':>6}  {'OK':>5}  {'Snaps':>6}  {'Errs':>5}  {'Time':>7}")
    print(f"{'-'*60}")

    wrapper = EphemerisWrapper(ephemeris_path=str(REPO_ROOT / "data" / "ephemeris"))
    computer = SnapshotComputer(wrapper)

    total_cases = total_ok = total_snaps = total_errs = 0

    for bn, batch_payloads in enumerate(batches, 1):
        t0 = time.perf_counter()
        try:
            schema = ResearchCaseBatchImportSchema(cases=batch_payloads, generate_ids=True)
            domain_cases = [c.to_domain() for c in schema.cases]
        except Exception as e:
            elapsed = time.perf_counter() - t0
            print(f"  {bn:04d}  VALID_ERR  {str(e)[:80]}  {elapsed:.1f}s")
            continue

        try:
            async with _async_session_factory() as session:
                svc = ResearchCaseImportService(session, computer)
                results = await svc.import_cases(domain_cases, update_existing=False)
                await session.commit()

            ok = sum(1 for r in results if not r.errors)
            snaps = sum(r.total_snapshots_created for r in results)
            errs = sum(len(r.errors) for r in results)
            elapsed = time.perf_counter() - t0
            icon = "OK" if errs == 0 else "PARTIAL"
            print(f"  {bn:04d}  {icon:>8}  {len(domain_cases):>6}  {ok:>5}  {snaps:>6}  {errs:>5}  {elapsed:>6.1f}s")
            total_cases += len(domain_cases)
            total_ok += ok
            total_snaps += snaps
            total_errs += errs
        except Exception as e:
            elapsed = time.perf_counter() - t0
            print(f"  {bn:04d}  ERROR       {str(e)[:80]}  {elapsed:.1f}s")

    print(f"{'-'*60}")
    print(f"\nSUMMARY: {total_cases:,} cases | {total_ok:,} OK | {total_snaps:,} snaps | {total_errs:,} errors\n")

    try:
        from apps.api.models.research_case import ResearchCaseModel, LifeEventModel
        from sqlalchemy import select, func
        async with _async_session_factory() as session:
            rc = await session.scalar(select(func.count()).select_from(ResearchCaseModel))
            le = await session.scalar(select(func.count()).select_from(LifeEventModel))
            q = select(ResearchCaseModel.source_batch, func.count().label("cnt")).group_by(ResearchCaseModel.source_batch).order_by(func.count().desc())
            rows = (await session.execute(q)).all()
        print(f"DB: {rc:,} research_cases | {le:,} life_events")
        for r in rows:
            print(f"  {(r.source_batch or '(null)'):<45} {r.cnt:>8,}")
    except Exception as e:
        print(f"\nDB verification error (non-fatal): {e}")
    print()

if __name__ == "__main__":
    dry_run = "--dry" in sys.argv or "--dry-run" in sys.argv
    csv_file = REPO_ROOT / "data" / "kundalee" / "kundalee_clean.csv"
    if not csv_file.exists():
        print(f"CSV not found: {csv_file}"); sys.exit(1)
    try:
        asyncio.run(run(csv_file, dry_run))
    finally:
        sys.exit(0)
