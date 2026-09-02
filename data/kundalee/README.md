# KundaleeStore — AstroOS Import Package

## Source
- **Raw data:** `KundaleeStore_Full/KundaleeStore/Included/celebrities/*.txt` (71,489 birth chart files)
- **Original source:** AstroDatabank / KundaleeStore

## Converted Data

| File | Description | Size |
|------|-------------|------|
| `kundalee_export.csv` | Flat CSV — 66,732 cases, 34 columns | 23 MB |
| `batches/` | 72 JSON batch folders (AstroOS schema) | ~72 MB |

### Batches
```
batches/
  kundalee_batch_0001/cases_0001.json   (920 cases)
  kundalee_batch_0002/cases_0002.json   (924 cases)
  ...
  kundalee_batch_0072/cases_0072.json   (469 cases)
```
Each batch ≤ 1000 cases (AstroOS max). Total: **66,732 valid cases**.

## JSON Format — ResearchCaseBatchImportSchema
```json
{
  "cases": [
    {
      "person": {
        "name": "Ali, Muhammad",
        "gender": "Male",
        "dob": "1942-01-17",
        "tob": "18:35",
        "place": "Louisville, Kentucky, 38n15,  85w46",
        "latitude": 38.25,
        "longitude": -85.766666,
        "timezone": "America/Chicago",
        "source": "BC/BR in hand",
        "birth_time_confidence": "high"
      },
      "ayanamsa": "lahiri",
      "house_system": "P",
      "divisional_charts": ["D1"],
      "life_events": [
        {
          "type": "Other",
          "event_date": "25 February 1964",
          "severity": "Moderate",
          "verified": true,
          "confidence": "medium",
          "source": "KundaleeStore",
          "description": "Work : Prize ..."
        }
      ],
      "source_batch": "kundaleestore_v2"
    }
  ],
  "generate_ids": false
}
```

## CSV Columns (34)
`case_id`, `name`, `gender`, `dob`, `tob`, `place`, `latitude`, `longitude`, `timezone`, `source`, `birth_time_confidence`, `ayanamsa`, `house_system`, `event_1_type`, `event_1_date`, `event_1_severity`, `event_1_verified`, `event_1_confidence`, `event_1_description`, `event_2_type`, `event_2_date`, `event_2_severity`, `event_2_verified`, `event_2_confidence`, `event_2_description`, `event_3_type`, `event_3_date`, `event_3_severity`, `event_3_verified`, `event_3_confidence`, `event_3_description`, `total_events`, `research_notes`, `source_batch`

## Converter Scripts

**Location:** `scripts/kundalee_converter.py` and `scripts/kundalee_to_csv.py`

Re-run conversion anytime:
```cmd
python scripts/kundalee_converter.py        # JSON batches
python scripts/kundalee_to_csv.py            # CSV export
```

## Import into AstroOS
1. Start AstroOS → Research → Import Cases
2. Upload `batches/kundalee_batch_XXXX/cases_XXXX.json` sequentially (1–72)
3. Filter by `source_batch: "kundaleestore_v2"` to identify Kundalee data

## Failed / Skipped Export — `kundalee_failed_949.csv`

949 CSV entries never reached the DB (verified by full key-diff against all 60,160 `research_cases`).
Exported with per-row `status`, `reason_category` and `reason` columns:

| Status | Count | Reason |
|--------|-------|--------|
| `SNAPSHOT_ERROR` (`POLAR_LATITUDE_PLACIDUS`) | 948 | Birth latitude is beyond the polar circle (|lat| 66.57°–89.98°). The **Placidus (P) house system is mathematically undefined at polar latitudes**, so Swiss Ephemeris fails with `swisseph.houses: error` and the case-level import rolls back. Several of these rows also carry questionable source coordinates (e.g. a São Paulo event recorded at the North Pole). **Fix options:** verify/correct lat-lon in source, or compute these cases with a polar-safe house system (W = whole-sign, E = equal). |
| `NO_VALID_EVENTS` (`NO_EVENTS`) | 1 | Philippson, Julius (1894-04-08): no parseable event type+date combination, so the clean-data filter skipped it by design. |

Re-generate anytime: `python scratch/export_failed_cases.py` (replays the importer's exact dedup
filter and re-attempts snapshot computation to capture live error messages).

## Data Quality
- **Valid cases:** 66,732 / 71,489 (93.3%)
- **Skipped:** 4,757 (no parseable DOB — ancient figures, ambiguous dates)
- **Birth time confidence:** `high` (AA/A ratings), `medium` (B/C), `low` (X/XX/DD)
- **Timezone:** Converted to IANA format (e.g., `America/Chicago`)

## Data-Quality Audit & Coordinate Fix (2026-08-29)

Full audit of all 59,871 imported rows (`scratch/audit_kundalee_data.py` →
`kundalee_data_audit.csv`, one row per problem, with stored-vs-correct values):

| Issue | Rows | Mechanism |
|-------|------|-----------|
| `WRONG` coordinates | 2,509 | Dense DMS misparse: `43w0613` means 43°06′13″W, parser read 613 arc-minutes (some rows also lat/lon swapped) |
| `ZEROED` coordinates | 231 | Parse failure fell back to lat=0, lon=0 |
| `TZ_MISMATCH` | 14,948 | UTC fallback for unmapped abbreviations (`BZT`, `AMT`, `LMT`, `-05`…) and pre-1911 France LMT vs `MET h1e` |
| `RAW_MISSING_OR_UNPARSED` | 14,776 | Meridian notation `m4e53` (= +0:19:32) not parsed by audit regex |

Raw owner data was correct (e.g. `timezone: BZT h3w` = −3) — inconsistencies were
introduced by the automated converter's notation handling.

**Coordinate fix applied (2026-08-29):** `python scripts/fix_kundalee_coords.py`
- 2,487/2,509 `WRONG` rows fixed in DB (22 belong to other import batches)
- Old snapshots (computed from wrong coords) deleted; 2,935 fresh snapshots
  recomputed via `SnapshotComputer` — 0 errors
- Post-fix integrity: 0 duplicate snapshots, 0 events without snapshot, 0 orphans
- Backup before fix: `D:\AstroOS_Backups\astroos_db_pre_coordfix_20260829_215551.dump`

**Still open:** timezone issues (~20k rows incl. France-LMT),
949 polar-latitude cases (948 + Lyngstad, see Failed/Skipped section above).

### ZEROED coordinate fix (2026-08-29, after WRONG fix)

- **228 rows fixed** (`--status ZEROED`): stored (0,0) → correct dense-DMS
  coords, 245 snapshots rebuilt (~5s), 0 unexpected errors.
- **Special case — Alaska 2014 earthquake:** raw `182w3040` crosses the
  antimeridian → stored as **177.4889E** (audit CSV patched; audit script now
  wraps |lon| > 180).
- **Left at (0,0) by design:** `Lyngstad, Anni-Frid` (RC-1945-198) — corrected
  coords = 68.33N (above Arctic Circle) so Placidus is undefined; her old
  snapshots remain intact pending the polar-house fix (polar bucket now 949).
- Post-fix integrity: 0 events without snapshot, 0 duplicate snapshots,
  73,317 snapshots, 60,160 cases.
- Script: `python scripts/fix_kundalee_coords.py --status ZEROED [--dry] [--limit N]`


