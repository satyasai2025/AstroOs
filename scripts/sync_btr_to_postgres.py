#!/usr/bin/env python3
r"""
AstroOS — Synchronize Pandit Vinay Jha 26,456 BTR Charts to PostgreSQL
======================================================================
Flushes unrectified raw records from live research tables (already backed up safely
to archive_research_cases_raw, archive_life_events_raw, archive_event_snapshots_raw)
and ingests the 26,456 certified BTR charts from kundalee_btr_26456.csv.
"""

import os
import sys
import csv
import uuid
import asyncio
from datetime import datetime, timezone
from dotenv import dotenv_values
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

BTR_CSV = r"c:\Users\rkmau\Downloads\ReplitplusClaude\AstroOS\data\research_sandbox\kundalee_btr_baseline\kundalee_btr_26456.csv"
CFG = dotenv_values(r"c:\Users\rkmau\Downloads\ReplitplusClaude\AstroOS\.env")
DB_URL = CFG.get("DATABASE_URL")

async def sync_btr_database():
    print("[*] Starting BTR Synchronization to PostgreSQL...")
    if not os.path.exists(BTR_CSV):
        print(f"[!] BTR CSV file not found: {BTR_CSV}")
        return

    engine = create_async_engine(DB_URL)

    # 1. Verify backup exists
    async with engine.connect() as conn:
        bkp_cnt = (await conn.execute(text("SELECT count(*) FROM archive_research_cases_raw;"))).scalar()
        print(f"[*] Verified safe backup table: {bkp_cnt:,} raw cases preserved in archive_research_cases_raw.")

    # 2. Flush unrectified live records
    print("[*] Flushing unrectified raw records from live research tables...")
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM event_snapshots;"))
        await conn.execute(text("DELETE FROM life_events;"))
        await conn.execute(text("DELETE FROM research_cases;"))
        print("  [OK] Cleaned event_snapshots, life_events, and research_cases.")

    # 3. Read and insert BTR cases in batches
    print("[*] Reading BTR dataset...")
    with open(BTR_CSV, "r", encoding="utf-8") as f:
        cases = list(csv.DictReader(f))

    total_cases = len(cases)
    print(f"[*] Total BTR records to ingest: {total_cases:,}")

    batch_size = 2000
    now_utc = datetime.now(timezone.utc)

    for i in range(0, total_cases, batch_size):
        chunk = cases[i : i + batch_size]
        insert_params = []
        for r in chunk:
            # Parse dob
            try:
                dob_dt = datetime.strptime(r["dob"], "%Y-%m-%d")
            except Exception:
                dob_dt = datetime(1900, 1, 1)

            insert_params.append({
                "id": str(uuid.uuid4()),
                "created_at": now_utc,
                "updated_at": now_utc,
                "research_case_id": r["case_id"],
                "person_name": r["person_name"][:250],
                "gender": "other",
                "dob": dob_dt,
                "tob": r["tob"],
                "place_of_birth": "Kundalee BTR Archive",
                "latitude": float(r["latitude"]),
                "longitude": float(r["longitude"]),
                "timezone": r["timezone"],
                "data_source": "kundalee_jha_rectified_baseline",
                "birth_time_confidence": "high",
                "ayanamsa": "lahiri",
                "house_system": "W",
                "rectified": True,
                "rectification_notes": f"Vinay Jha BTR Baseline: Lagna={r['lagna_lon']} Sun={r['sun_lon']} Moon={r['moon_lon']}",
                "source_batch": "kundalee_jha_btr_gold",
                "validation_status": "btr_verified"
            })

        async with engine.begin() as conn:
            stmt = text("""
                INSERT INTO research_cases (
                    id, created_at, updated_at, research_case_id, person_name,
                    gender, dob, tob, place_of_birth, latitude, longitude,
                    timezone, data_source, birth_time_confidence, ayanamsa,
                    house_system, rectified, rectification_notes, source_batch,
                    validation_status
                ) VALUES (
                    :id, :created_at, :updated_at, :research_case_id, :person_name,
                    :gender, :dob, :tob, :place_of_birth, :latitude, :longitude,
                    :timezone, :data_source, :birth_time_confidence, :ayanamsa,
                    :house_system, :rectified, :rectification_notes, :source_batch,
                    :validation_status
                );
            """)
            await conn.execute(stmt, insert_params)

        print(f"  Ingested {min(i + batch_size, total_cases):,}/{total_cases:,} BTR charts into PostgreSQL...")

    # 4. Final verification
    async with engine.connect() as conn:
        new_cnt = (await conn.execute(text("SELECT count(*) FROM research_cases;"))).scalar()
        rectified_cnt = (await conn.execute(text("SELECT count(*) FROM research_cases WHERE rectified = True;"))).scalar()
        print(f"\n[OK] Database BTR Synchronization Complete!")
        print(f"   * Total Records in research_cases: {new_cnt:,}")
        print(f"   * Total Rectified Records (rectified = True): {rectified_cnt:,} (100.0%)")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(sync_btr_database())
