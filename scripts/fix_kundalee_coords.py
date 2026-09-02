#!/usr/bin/env python3
"""Fix the 2,509 WRONG-coordinate Kundalee cases.

Source of truth: data/kundalee/kundalee_data_audit.csv (rows coord_status=WRONG),
whose correct_lat/correct_lon were re-parsed from the raw place string
(dense DMS: 43w0613 = 43deg 06' 13" W).

For every matched DB row (source_batch=kundaleestore_v2):
  1. latitude/longitude  <- corrected values
  2. old event_snapshots (computed from the wrong coords) are DELETED
     and fresh snapshots are recomputed with SnapshotComputer.

Run:  python scripts/fix_kundalee_coords.py --dry
      python scripts/fix_kundalee_coords.py --limit 5
      python scripts/fix_kundalee_coords.py
"""
import argparse, asyncio, csv, json, re, sys, time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(REPO_ROOT))

from apps.api.dependencies import _async_session_factory
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.import_service import (
    SnapshotComputer, _case_model_to_domain, _NOON,
)
from apps.api.models.research_case import ResearchCaseModel, EventSnapshotModel
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

AUDIT_CSV = REPO_ROOT / "data" / "kundalee" / "kundalee_data_audit.csv"


def norm_key(name, dob, tob):
    n = (name or "").strip().lower()[:200]
    d = dob.strftime("%Y-%m-%d") if hasattr(dob, "strftime") else str(dob or "")[:10]
    m = re.match(r"\s*(\d{1,2}):(\d{2})", str(tob or ""))
    t = f"{int(m.group(1)):02d}:{m.group(2)}" if m else str(tob or "").strip()[:5]
    return (n, d, t)


def load_fixes(status="WRONG"):
    fixes = {}
    with open(AUDIT_CSV, "r", encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r["coord_status"] != status:
                continue
            try:
                lat, lon = float(r["correct_lat"]), float(r["correct_lon"])
            except (ValueError, TypeError):
                continue
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                continue
            fixes[norm_key(r["name"], r["dob"], r["tob"])] = (lat, lon)
    return fixes



async def run(dry: bool, limit, status: str = "WRONG"):
    fixes = load_fixes(status)
    print(f"Fixes loaded from audit CSV ({status}): {len(fixes):,}")

    wrapper = EphemerisWrapper(ephemeris_path=str(REPO_ROOT / "data" / "ephemeris"))
    computer = SnapshotComputer(wrapper)

    async with _async_session_factory() as session:
        # Phase 1: lightweight key scan (columns only — full models are ~4 GB)
        result = await session.execute(
            select(ResearchCaseModel.id, ResearchCaseModel.person_name,
                   ResearchCaseModel.dob, ResearchCaseModel.tob)
            .where(ResearchCaseModel.source_batch == "kundaleestore_v2",
                   ResearchCaseModel.deleted_at.is_(None))
        )
        key_to_id = {}
        for rid, name, dob, tob in result.all():
            key_to_id.setdefault(norm_key(name, dob, tob), []).append(rid)
        print(f"Kundalee keys in DB: {len(key_to_id):,}")

        matched_ids, dup = [], 0
        for key, (lat, lon) in fixes.items():
            hits = key_to_id.get(key)
            if not hits:
                continue
            if len(hits) > 1:
                dup += 1
            matched_ids.append((hits[0], lat, lon))
        print(f"Matched to DB ids: {len(matched_ids):,} (dup-key hits: {dup})")
        unmatched = len(fixes) - len(matched_ids)
        if unmatched:
            print(f"Unmatched fix keys: {unmatched:,}")

        if limit:
            matched_ids = matched_ids[:limit]
        if dry:
            id_latlon = dict((i, (la, lo)) for i, la, lo in matched_ids[:8])
            result = await session.execute(
                select(ResearchCaseModel).where(ResearchCaseModel.id.in_(id_latlon))
            )
            for m in result.scalars().all():
                la, lo = id_latlon[m.id]
                print(f"  {m.research_case_id} | {m.person_name[:35]:35s} "
                      f"({m.latitude:.4f}, {m.longitude:.4f}) -> ({la:.4f}, {lo:.4f})")
            print(f"DRY RUN - {len(matched_ids)} rows would be fixed.")
            return

        # Phase 2: fetch id -> (case_id, name) mapping as plain rows (no ORM
        # instances held, so nothing can expire mid-loop)
        ids = [i for i, _, _ in matched_ids]
        rows = (await session.execute(
            select(ResearchCaseModel.id,
                   ResearchCaseModel.research_case_id,
                   ResearchCaseModel.person_name)
            .where(ResearchCaseModel.id.in_(ids))
        )).all()
        info = {r[0]: (r[1], r[2]) for r in rows}
        prepared = [
            {"id": i, "case_id": str(info[i][0]),
             "name": (info[i][1] or "")[:30], "lat": la, "lon": lo}
            for i, la, lo in matched_ids if i in info
        ]
        print(f"Models loaded: {len(prepared):,}")
        await apply_fixes(computer, prepared)


async def apply_fixes(computer, prepared):
    """Per-item fresh session: a failed case can never poison the next one,
    and every domain object is built AFTER the coords are corrected."""
    fixed = snap_ok = snap_err = 0
    errors = []
    t0 = time.perf_counter()
    for i, item in enumerate(prepared, 1):
        try:
            async with _async_session_factory() as session:
                m = (await session.execute(
                    select(ResearchCaseModel)
                    .where(ResearchCaseModel.id == item["id"])
                    .options(selectinload(ResearchCaseModel.life_events))
                )).scalars().first()
                if m is None:
                    snap_err += 1
                    errors.append(f"{item['case_id']} {item['name']}: row vanished")
                    continue
                if m.life_events:
                    await session.execute(
                        delete(EventSnapshotModel).where(
                            EventSnapshotModel.life_event_id.in_(
                                [e.id for e in m.life_events]))
                    )
                m.latitude, m.longitude = item["lat"], item["lon"]
                await session.flush()
                domain_case = _case_model_to_domain(m)  # built AFTER coord fix
                per_event = await asyncio.to_thread(computer.compute_case, domain_case)
                for (_ev, snapshots), ev_model in zip(per_event, m.life_events):
                    for snap in snapshots:
                        session.add(EventSnapshotModel(
                            life_event_id=ev_model.id,
                            snapshot_date=datetime.combine(snap.snapshot_date, _NOON),
                            snapshot_version=snap.snapshot_version,
                            mahadasha=snap.current_dasha.mahadasha if snap.current_dasha else None,
                            antardasha=snap.current_dasha.antardasha if snap.current_dasha else None,
                            pratyantar=snap.current_dasha.pratyantar if snap.current_dasha else None,
                            transit_features=json.dumps(snap.transits),
                            shadbala_values=json.dumps(snap.shadbala),
                            active_yogas=json.dumps(snap.active_yogas),
                            varga_activations=json.dumps(snap.varga_activations),
                            nakshatra_activations=json.dumps(snap.nakshatra_activations),
                            house_lord_statuses=json.dumps(snap.house_lord_statuses),
                            facts_json=json.dumps(
                                [{"key": f.key, "value": f.value, "source": f.source}
                                 for f in snap.facts]) if snap.facts else None,
                        ))
                        snap_ok += 1
                await session.commit()
            fixed += 1
        except Exception as exc:  # noqa: BLE001
            snap_err += 1
            errors.append(f"{item['case_id']} {item['name']}: {exc}")
            continue
        if i % 100 == 0:
            print(f"  {i:,}/{len(prepared):,} fixed | snaps {snap_ok:,} | "
                  f"err {snap_err} | {time.perf_counter() - t0:.0f}s", flush=True)

    print(f"\nDONE in {time.perf_counter() - t0:.0f}s")
    print(f"  Coordinates fixed:  {fixed:,}")
    print(f"  Snapshots rebuilt:  {snap_ok:,}")
    print(f"  Case errors:        {snap_err}")
    for e in errors[:15]:
        print("   !", e)
    if errors:
        err_log = REPO_ROOT / "data" / "kundalee" / "coord_fix_errors.txt"
        err_log.write_text("\n".join(errors), encoding="utf-8")
        print(f"  Full error list -> {err_log}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--status", default="WRONG",
                    help="audit CSV coord_status bucket to fix (WRONG / ZEROED)")
    args = ap.parse_args()
    asyncio.run(run(args.dry, args.limit, args.status))

