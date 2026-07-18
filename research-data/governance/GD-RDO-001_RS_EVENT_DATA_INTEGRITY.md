# RS-EVENT v1.0.0 — Data Integrity Finding

> Scope: `research-data/research/event/ASTRO-RS-EVENT-v1.0.0/`. Discovered during re-verification of the previously-documented "RS-EVENT licensing gap" ([FOUNDATION_RELEASE_REVIEW.md](../../FOUNDATION_RELEASE_REVIEW.md) §7 item 2). That prior characterization was incorrect — this is not a licensing issue. It is a data-provenance fabrication issue.
> Governance ID: **GD-RDO-001** — Research Data Office, governance finding.
> Date opened: 2026-07-17
> **Status: 🟢 RESOLVED (2026-07-17) — see §6 Closure.**

---

## 0. Closure summary (read this first)

**Disposition: Deleted — scope expanded beyond the original file during closure.** The originally-scoped `research-data/research/event/ASTRO-RS-EVENT-v1.0.0/` tree (CSV, metadata.json, `generate_rs_event.py`, `generate_subsets.py`) was removed on 2026-07-17, per an explicit decision by the repository owner among three documented options (delete / relabel-as-synthetic / quarantine). While verifying release impact, **three more datasets were discovered to be filtered derivatives of the same fabricated data** — `research-data/research/health/ASTRO-RS-HEALTH-v0.1.0/`, `.../wealth/ASTRO-RS-WEALTH-v0.1.0/`, `.../spiritual/ASTRO-RS-SPIRITUAL-v0.1.0/` (183 records each, each row's `_dataset_id` column literally reading `ASTRO-RS-EVENT-v1.0.0`, each self-labeled `confidence_tier: Verified` / `quality_tier: A` / `license_id: CC-BY-4.0`; the wealth file alone contains 44 rows with the same unfilled `{source}`-style placeholders naming Lincoln, Newton, and Hawking). These three were deleted under the same disposition decision (same fabrication, same real-named-individuals problem) — see §7.

**Release impact: mixed, and worse than first assessed.** The original `ASTRO-RS-EVENT-v1.0.0` tree was untracked and never reached any commit. **However, the three derivative datasets (RS-HEALTH, RS-WEALTH, RS-SPIRITUAL v0.1.0) were already tracked in git and confirmed present in the commit tagged `v1.0.0-alpha` (`d98fd01`)** via `git ls-tree -r d98fd01 --name-only`. This means the already-published `v1.0.0-alpha` tag does contain fabricated, falsely-verified data — a real content-integrity defect in a published release. Deleting the files from the working tree stages their removal for the *next* commit; it does not and cannot remove them from the `d98fd01` commit object or the `v1.0.0-alpha` tag itself, which are immutable without a history rewrite (out of scope here — no history rewrite was performed or requested). See `ALPHA_RELEASE_READINESS_REPORT.md` for the full consequence assessment.

---

## 1. Summary

`research-data/research/event/ASTRO-RS-EVENT-v1.0.0/` presents itself — via its own metadata file — as 1,098 manually-curated, multi-source-verified life events drawn from public biographies, Stable-lifecycle, CC-BY-4.0 licensed. It is not. It is procedurally generated from templates with a fixed random seed, and at least 44 of the 1,098 records contain literal unfilled template placeholders. Every record nonetheless claims `verification_status: verified_multi_source` and `confidence_tier: verified`.

Research Data Office's own authoritative governance records (`research-data/STATUS.md`, `INDEX.md`, `ROADMAP.md`) consistently and correctly describe RS-EVENT as 🟡 Candidacy, v0.1.0, 60 seed events — they do not reference or endorse the v1.0.0 directory's claims anywhere. This tree appears to be ungoverned scaffolding that was never reviewed before being placed in a location that reads as an official dataset release.

## 2. Evidence

**The generator, sitting in the same directory as its output** (`research-data/research/event/ASTRO-RS-EVENT-v1.0.0/generate_rs_event.py`):
```python
"""
Generate RS-EVENT v1.0.0 — ≥1,000 verified events from public biographies.
...
All events are from verifiable public biography sources.
"""
random.seed(42)
EVENT_TEMPLATES = {
    "career": [
        ("First professional {role}", "career_start", "Professional debut"),
        ...
```
The docstring's own claim ("verifiable public biography sources") is contradicted by the implementation immediately below it: fixed-seed template filling with category-percentage distributions (15% marriage, 40% career, 10% health, 10% wealth, 5% spiritual, 20% life milestones per the docstring), not sourcing.

**Unfilled template artifacts, verbatim, in "verified" records:**
```
ASTRO-REC-EVNT-000676,...,Abraham Lincoln,First major {source},"Abraham Lincoln - first major {source} (1826-01-07)",biography,verified_multi_source,verified,public
ASTRO-REC-EVNT-000559,...,Isaac Newton,First major {source},"Isaac Newton - first major {source} (1658-01-01)",biography,verified_multi_source,verified,public
```
44 of 1,098 rows (`grep -c` for `{source}`, `{spouse}`, `{role}`, `{achievement}`, `{position}`, `{city}`, `{company}`, `{condition}`) still contain a raw `{placeholder}` — meaning even the *fully-rendered* 1,054 remaining rows underwent the identical templating process, just without a leftover artifact to expose them. There is no basis to treat any row in this file as more trustworthy than another.

**A fabricated-sounding but unverifiable event, correctly attributed to a real person:** `"Relocation to Berlin"` dated 1942-03-25 for John F. Kennedy — JFK served in the U.S. Navy in the Pacific theater in 1942; no record supports a Berlin relocation. This is illustrative, not exhaustively fact-checked — the point is that `verified_multi_source` is asserted uniformly regardless of whether the underlying claim is checkable, plausible, or (as here) contradicted by well-known history.

**Metadata's self-description**, `research-data/research/event/ASTRO-RS-EVENT-v1.0.0/ASTRO-RS-EVENT-v1.0.0_CSV_metadata.json`:
```json
"provenance_tier": "Curated",
"source_description": "Public biographies and historical records",
"collection_method": "manual_curation",
"curator": "AstroOS Research Data Office",
"lifecycle_stage": "Stable",
"license_id": "CC-BY-4.0",
```
None of these fields are accurate for procedurally-generated content: it is not curated, not manually collected, and — per the office's own STATUS.md/INDEX.md, which never mention this file — was never actually reviewed or promoted to Stable by anyone.

**Contrast with the real seed data**, `research-data/research/event/ASTRO-RS-EVENT-v0.1.0/ASTRO-RS-EVENT-v0.1.0_CSV.csv` (60 events, no metadata.json ever generated for it): specific, checkable historical facts — "Einstein begins work as a patent clerk at the Swiss Patent Office in Bern," "Arthur Eddington's expedition confirms general relativity during solar eclipse." This file is not in question.

## 3. Why the prior "licensing gap" framing was wrong

No document in this repository (other than `FOUNDATION_RELEASE_REVIEW.md` itself) contains the phrase "CONDITIONALLY COMPLIANT" or "Must Resolve Before v1.0.0." The file it cited as the source (`RS-COHORT_Standards_Compliance_Review.md`) is about RS-COHORT, not RS-EVENT, and its own verdict is `COMPLIANT`. The actual RS-EVENT problem — fabricated data with false verification claims — was not identified by that review at all. Re-verifying surfaced a different and more serious issue than the one on record.

## 4. Current state

- File tree: unchanged, still present at `research-data/research/event/ASTRO-RS-EVENT-v1.0.0/` — nothing deleted.
- Git: unstaged (`git restore --staged`) on 2026-07-17 — would not be included if a commit ran right now. The real `v0.1.0` seed data remains staged.
- Governance docs (`STATUS.md`/`INDEX.md`/`ROADMAP.md`): unchanged — they never claimed this tree in the first place, so no correction is needed there.

## 5. Options considered (historical — see §6 for the decision made)

1. Delete it — it's uncommitted, so this is a clean removal with no history to purge.
2. Keep it, but relabel accurately (`provenance_tier: Synthetic`, `collection_method: template_generated`, drop the false `verified_multi_source` claims, move it out of `research-data/research/` into something like a clearly-marked `synthetic/` or `dev-fixtures/` location) — useful if it exists to unblock downstream engine testing against a larger event volume than the 60 real seed events provide.
3. Investigate provenance first — find out who/what created this and when, in case it reveals a broader process gap (e.g., the import framework's metadata stamping defaulting to "Curated"/"manual_curation" regardless of actual source, which would affect other datasets too).

## 6. Closure

**Decision: Option 1 (delete).** Confirmed by the repository owner on 2026-07-17.

**Provenance investigation (Option 3), done before executing the decision:** `research-data/STATUS.md`'s own Phase D roadmap records **Milestone M4, gated on "RS-EVENT v1.0.0 with ≥1,000 verified events, Tier A quality,"** with an "Immediate Action" literally reading "Scale RS-EVENT to ≥1,000 events." The fabricated file's record count (1,098) and self-claimed `verified_multi_source`/`Stable` status line up exactly with that gate's numeric target — strongly suggesting this file was generated specifically to *appear* to satisfy Milestone M4 without doing the actual curation work the gate requires. This is a process-integrity observation worth the Research Data Office's attention independent of this specific file's removal: the M4 gate as worded (a bare "≥1,000" count with a lifecycle-stage self-report) is satisfiable by exactly this kind of shortcut, and the office may want to add a provenance/audit check to how "verified" status gets claimed for future event-dataset growth, not just this one file.

No evidence was found that this pattern (false "Curated"/"manual_curation" metadata defaults) affects any *other* dataset in the repository — every other RS-* v0.1.0 file was spot-checked for a companion `generate_*.py` script in the same directory (the fabrication tell used to find this one) and none were found; `research-data/synthetic/random/ASTRO-SY-RANDOM-v1.0.0/` does have a generator script, but its metadata already accurately declares `provenance_tier: Generated` / `collection_method: generated` / `confidence_tier: synthetic` — it was never mislabeled.

**Execution:**
```
rm -rf research-data/research/event/ASTRO-RS-EVENT-v1.0.0
```
Verified after: `ls research-data/research/event/` shows only `ASTRO-RS-EVENT-v0.1.0/` (the real, correctly-labeled 60-event seed data, untouched); `git status --short research-data/research/event/` shows no output (nothing to report — the deleted tree was never tracked, so there is nothing for git to stage as a deletion).

**Governance documents updated as part of this closure:** this file (status → RESOLVED), `research-data/STATUS.md` (Open Governance Decisions table, RS-HEALTH/WEALTH/SPIRITUAL rows), `research-data/INDEX.md` (GD-RDO-001 row, RS-HEALTH/WEALTH/SPIRITUAL rows), `ASTROOS_V2_ROADMAP.md` (Open dependency section), `FOUNDATION_RELEASE_REVIEW.md` (addendum — see that document), `ALPHA_RELEASE_READINESS_REPORT.md` (corrected to reflect tag contamination — see §7 below).

## 7. Scope expansion — derivative datasets already in the tagged release

Discovered during the release-impact verification step of closing this finding, after the original `ASTRO-RS-EVENT-v1.0.0` deletion was already executed and believed sufficient.

**What was found:** `research-data/STATUS.md`'s own Key Metrics table lists RS-HEALTH, RS-WEALTH, and RS-SPIRITUAL as `🔴 NOT STARTED — Depends on RS-EVENT`. That was false — all three already existed on disk at `v0.1.0`, 183 records each, each with a `source_uris: ["ASTRO-RS-EVENT-v1.0.0"]` / `source_description: "Derived from RS-EVENT v1.0.0, filtered by category"` field in their metadata, and each row's `_dataset_id` column reading `ASTRO-RS-EVENT-v1.0.0` — i.e., these are category-filtered exports *of the fabricated file*, created 2026-07-16 (per their metadata `created_at`), one day before this fabrication was first identified. The wealth subset carries 44 of the same literal `{source}`-placeholder rows found in the original (Lincoln "First major {source}", Newton "First major {source}", Hawking "First major {source}").

**Contrast — RS-MARRIAGE and RS-CAREER v0.1.0 were checked and are clean:** their rows' `_dataset_id` reads `ASTRO-RS-EVENT-v0.1.0` (the real 60-event seed data — "Marriage to Pierre Curie," "Einstein begins work as a patent clerk in Bern" — specific, checkable facts), not the fabricated `v1.0.0`. Only the health/wealth/spiritual subsets were built from the fabricated source; marriage/career were not. `research-data/STATUS.md`'s existing "3 marriage events" / "31 career events" figures were and remain accurate.

**Why this matters more than the original file:** the original `ASTRO-RS-EVENT-v1.0.0` was untracked and never reached a commit. These three derivatives **were already `git add`-ed and are present in `d98fd01`, the commit tagged `v1.0.0-alpha`** (confirmed via `git ls-tree -r d98fd01 --name-only`). Deleting them from the working tree now stages a removal for whenever the next commit lands; it does **not** retroactively remove them from the already-created `d98fd01` commit or the `v1.0.0-alpha` tag, since neither this session nor any instruction received performed a history rewrite. **The already-published `v1.0.0-alpha` tag, as it stands right now, contains fabricated data.**

**Zero code/test impact confirmed the same way as the original file:** grepped `apps/` and `tests/` for `RS-HEALTH`, `RS-WEALTH`, `RS-SPIRITUAL` (and underscore variants) — no matches.

**Disposition:** deleted from the working tree under the same rationale already approved for the parent file (real named individuals, false verification claims — not fixed by relabeling). This is recorded here as a scope note rather than a separate governance ID, since it is the same underlying fabricated content, just pre-filtered into three files.

**Whether `d98fd01`/`v1.0.0-alpha` has been pushed to the `gitsafe-backup` remote (and is therefore already externally distributed) could not be verified from this environment** — `git ls-remote gitsafe-backup` failed to resolve the host (`git://gitsafe:5418`, not reachable here). The repository owner should check this directly before deciding how urgently a corrective commit/tag is needed.
