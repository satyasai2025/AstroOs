# AstroOS — Alpha Release Readiness Report

> Scope: (1) closure of governance finding `GD-RDO-001`, (2) a from-source-of-truth readiness assessment for `v1.0.0-alpha`, superseding `FOUNDATION_RELEASE_REVIEW.md`'s 2026-07-16 verdict.
> Method: direct repository inspection — `git log`/`git tag`/`git ls-tree`/`git status`, grep across `apps/` and `tests/` for dataset consumers, direct reads of all Research Data Office governance docs, direct reads of the already-tagged commit's own included documents. The roadmap's claims were treated as a hypothesis to verify, not a source of truth, per instruction.
> Date: 2026-07-17
> **No commits, tags, or pushes were made in the course of this review or its remediation.** One data deletion was executed (below), with explicit confirmation.

---

## 1. Executive Summary

**`GD-RDO-001` is RESOLVED, at an expanded scope.** The fabricated RS-EVENT `v1.0.0` dataset tree has been deleted, and so have three derivative datasets discovered during closure — RS-HEALTH, RS-WEALTH, and RS-SPIRITUAL v0.1.0, all filtered exports of the same fabricated data.

**A bigger finding surfaced during this investigation: `v1.0.0-alpha` is not a future decision — it already exists, and it is not clean.** The repository owner tagged it directly (`git tag`, commit `d98fd01`, 2026-07-17 19:44) before this investigation began. Verification of what that tag actually contains found two things, one reassuring and one not:
- The original fabricated `ASTRO-RS-EVENT-v1.0.0` tree was never committed — the tag is unaffected by that specific file.
- **However, the three derivative datasets (RS-HEALTH/WEALTH/SPIRITUAL v0.1.0) — built from that same fabricated data — were already `git add`-ed and are present in the tagged commit.** The already-published `v1.0.0-alpha` tag contains fabricated, falsely-`verified`-labeled data right now. Deleting the files from the working tree today stages a removal for the *next* commit; it does not and cannot retroactively clean the already-created `d98fd01` commit object or the tag pointing at it — that would require a history rewrite, which was neither requested nor performed.

**Phase B may still start — this is a data/release-hygiene defect, not a code defect, and nothing about it blocks writing new Phase B code.** But it does mean the existing `v1.0.0-alpha` tag should not be treated as a clean, trustworthy baseline as-is. See §5.

---

## 2. GD-RDO-001 Closure (summary — full record in `research-data/governance/GD-RDO-001_RS_EVENT_DATA_INTEGRITY.md`)

| Question | Answer |
|---|---|
| Was it resolved, needing code changes, or an accepted limitation? | Required a data change (not a code change) — now executed, at an expanded scope (see below). Not accepted as a limitation: the false claims named real, identifiable historical figures, which isn't a risk worth carrying into any future state. |
| What was the fix? | Deleted `research-data/research/event/ASTRO-RS-EVENT-v1.0.0/` (CSV, metadata.json, 2 generator scripts), **plus, discovered during closure and deleted under the same decision:** `research-data/research/health/ASTRO-RS-HEALTH-v0.1.0/`, `.../wealth/ASTRO-RS-WEALTH-v0.1.0/`, `.../spiritual/ASTRO-RS-SPIRITUAL-v0.1.0/` — three category-filtered derivatives built directly from the fabricated file (each row's `_dataset_id` reads `ASTRO-RS-EVENT-v1.0.0`; the wealth file alone had 44 rows with the same unfilled `{source}`-style placeholders naming Lincoln, Newton, and Hawking). All disposed of per explicit confirmation from the repository owner among three options (delete / relabel-as-synthetic / quarantine). |
| Why delete rather than relabel as synthetic (the path used successfully for `ASTRO-SY-RANDOM-v1.0.0`)? | `SY-RANDOM` never names real people — it's genuinely synthetic subjects. These files invented specific false claims *about* real, named individuals (Lincoln, Newton, Hawking, and a fabricated, historically-contradicted 1942 Berlin relocation for JFK). Relabeling the provenance tier doesn't fix that; the false claims are the problem, not just the label. |
| Any code/test impact from deleting them? | None for any of the 4 deleted trees. Grepped `apps/` and `tests/` for `RS-EVENT`/`RS_EVENT`/`RS-HEALTH`/`RS-WEALTH`/`RS-SPIRITUAL` (and underscore variants) — zero real hits (one false-positive substring match in a test function name for RS-EVENT, verified by inspection). No engine, router, or test consumes any of this data. |
| Any git/release impact? | **Mixed.** The original `ASTRO-RS-EVENT-v1.0.0` tree was untracked (`??`) from discovery to deletion — never staged, never committed, confirmed absent from `d98fd01`. **The three derivative datasets were already tracked and confirmed present in `d98fd01`** via `git ls-tree -r d98fd01 --name-only` — meaning the tagged `v1.0.0-alpha` release does contain fabricated data. See §3 and §5. |
| Was the original "licensing gap" framing (`FOUNDATION_RELEASE_REVIEW.md` §7 item 2) ever accurate? | No — re-investigation (done in an earlier pass this session, reconfirmed here) found the actual problem was data fabrication, not licensing. `FOUNDATION_RELEASE_REVIEW.md` has been given a dated addendum rather than rewritten, to preserve the historical record. |
| Any process-integrity follow-up? | Yes, recorded in `research-data/STATUS.md`'s M4 gate section: the fabricated file's 1,098-record count matches that milestone's "≥1,000 events" gate almost exactly, suggesting it was generated specifically to *appear* to satisfy that gate — and its filtered derivatives were then committed as if they were legitimate v0.1.0 candidacy datasets, contradicting `STATUS.md`'s own "NOT STARTED" tracking for those three. The gate's wording (a bare count + self-reported status) is flagged as satisfiable by exactly this shortcut and worth tightening before RS-EVENT is scaled for real. |
| Governance docs updated | `GD-RDO-001_RS_EVENT_DATA_INTEGRITY.md` (status → RESOLVED, §6–7 Closure + scope expansion), `research-data/STATUS.md` (Open Governance Decisions table, Key Metrics counts, RS-HEALTH/WEALTH/SPIRITUAL rows, M4 process-integrity note), `research-data/INDEX.md` (RS-EVENT/RS-HEALTH/RS-WEALTH/RS-SPIRITUAL rows, GD-RDO-001 row), `ASTROOS_V2_ROADMAP.md`, `ASTROOS_V2_STATUS.md`, `ASTROOS_V2_RELEASE_PLAN.md`, `ASTROOS_V2_INDEX.md`, `FOUNDATION_RELEASE_REVIEW.md` (addendum). |

---

## 3. The `v1.0.0-alpha` Tag — What It Actually Is

```
tag:      v1.0.0-alpha  "AstroOS Platform Alpha"
commit:   d98fd018055b633cdb7256b329a834b3e8e892b5
author:   satyasai2025 <satyasai21@gmail.com>
date:     2026-07-17 19:42:21 +0530 (commit) / 19:44:10 +0530 (tag)
message:  chore(release): prepare v1.0.0-alpha
          - Rotate compromised RSA keys
          - Stage governance and audit docs
          - Deduplicate RS-COHORT dataset
          - Update ROADMAP and README to v1.0.0-alpha
          - Ensure final test pass
```

This was created directly by the repository owner via `git tag`/`git commit`, outside of and not requested through this Claude Code session — confirmed by author identity and by the fact no `git tag`, `git commit`, or `git push` was ever run in this conversation (standing constraint, honored throughout).

### 3.1 What's in it

650 files, 290,199 insertions — the bulk of the repository's pre-existing engine/knowledge/benchmark/research-data content, the RSA key rotation, the RS-COHORT deduplication, and a `PLATFORM_ALPHA_COMPLETION_REPORT.md` claiming "✅ PLATFORM ALPHA COMPLETE" based on an end-to-end test pass against a then-current build of the frontend/backend.

### 3.2 What's *not* in it — verified directly, not assumed

`git status` against `d98fd01` shows the following as **untracked (`??`)** — never committed:

- `apps/api/services/workflow_orchestrator.py`, `apps/api/routers/workflow.py`, `apps/api/schemas/workflow.py` — the Unified Analysis Pipeline itself
- `apps/api/domain/geocoding.py`, `apps/api/services/geocoding_service.py`, `apps/api/routers/geocoding.py`, `apps/api/schemas/geocoding.py` — the birth-place search/timezone-resolution feature
- `apps/web/src/app/dashboard/`, `apps/web/src/components/workflow/` — the entire analysis-pipeline frontend (forms, 10 result panels, birth-place search UI)
- `apps/web/src/lib/workflow.ts`, `apps/web/src/lib/geocoding.ts`
- `research-data/governance/GD-RDO-001_RS_EVENT_DATA_INTEGRITY.md` and this report itself

This is corroborated by the tagged commit's own `PLATFORM_ALPHA_COMPLETION_REPORT.md`, which lists as a known limitation: *"No geographic autocomplete — Birth form requires manual lat/lng entry — a geocoding router exists but is not wired to the frontend form."* That was true when that report was written; it is no longer true — the geocoding UI was subsequently built, wired, and browser-verified end-to-end in this session — but the tag was cut on the older state regardless.

**The tagged commit also contains, unmodified, `FOUNDATION_RELEASE_REVIEW.md` with its own final verdict reading "NOT READY FOR FOUNDATION RELEASE."** Two of that review's four blocking items were fixed by the same commit (RSA key, RS-COHORT dedup) but the document's verdict text was never updated to say so before tagging — see the addendum added to that document today.

### 3.3 Is any of this a *defect* in the tagged release?

No functional or security defect — everything committed compiles and the RSA key was safely rotated first. **But there is a real data-integrity defect: `d98fd01`/`v1.0.0-alpha` contains three fabricated, falsely-`verified`-labeled datasets** (`research-data/research/{health,wealth,spiritual}/ASTRO-RS-{HEALTH,WEALTH,SPIRITUAL}-v0.1.0/`), confirmed via direct `git ls-tree` inspection of the tagged commit (§2, §3.2). This was not caught before tagging because `research-data/STATUS.md` itself — the document that should have flagged it — incorrectly listed all three as "NOT STARTED" at the time, unaware they'd already been generated and committed the day before.

Beyond that specific defect, the tag is also simply an *earlier and less complete* snapshot than what "AstroOS Platform Alpha" is now defined to mean (`ASTROOS_V2_ROADMAP.md` Phase A, all 4 objectives) and than what its own completion report and this repository's naming imply.

---

## 4. Release Blocker Checklist

| Item | Status | Evidence |
|---|---|---|
| RSA private key compromise | ✅ Resolved | Rotated in `029441a`; included in tagged commit |
| RS-COHORT dataset duplication | ✅ Resolved | Deduplicated per `d98fd01` commit message |
| RS-EVENT data fabrication, original file (`GD-RDO-001`) | ✅ Resolved | Deleted 2026-07-17; never in any commit, tagged or otherwise |
| RS-EVENT data fabrication, 3 derivative datasets (`GD-RDO-001` §7) | ⚠️ **Deleted from working tree, but still present in the already-published `v1.0.0-alpha` tag** | `git ls-tree -r d98fd01` confirms `RS-HEALTH`/`RS-WEALTH`/`RS-SPIRITUAL` v0.1.0 (fabricated) are part of that commit; a history rewrite would be needed to remove them from the tag itself, which was not performed |
| Frontend integration (Phase A objective 2) | ✅ Complete, **not yet committed** | Built, browser-verified end-to-end this session; sits uncommitted |
| Auth/RBAC (Phase A objective 4) | ✅ Complete, **not yet committed** | Router-level gating verified via OpenAPI schema + live requests |
| Knowledge/Rule/Report Engine connection incl. Research Data correlation (Phase A objective 3 / M1 criteria 8–9) | ✅ Complete, **not yet committed** | Live-verified this session (see `CHANGELOG_V2.md` "M1 milestone completed to 9/10 criteria") |
| `FOUNDATION_RELEASE_REVIEW.md`'s stale "NOT READY" verdict sitting inside the tagged commit | ✅ Addressed | Dated addendum added 2026-07-17 (historical text preserved, not rewritten) |

**No open item blocks Phase B *implementation* from starting** — the one open item (fabricated data inside the already-tagged commit) is a release/data-hygiene defect the repository owner needs to decide how to handle (§5), not something that stops writing new code. It should not, however, be read as "no remaining release blockers" in the unqualified sense — the existing tag itself is not clean.

---

## 5. Recommendation

**Do not force-move `v1.0.0-alpha` to a different commit, and do not attempt a history rewrite to scrub the fabricated files out of `d98fd01`, without a separate, explicit decision from the repository owner.** Both are legitimate options in general, but both are destructive/hard-to-reverse operations (tag force-move, `git filter-repo`-style rewrite) that this report is flagging as *available*, not recommending unilaterally — especially since it's unverified from this environment whether `d98fd01` has already been pushed to the `gitsafe-backup` remote (`git ls-remote gitsafe-backup` could not resolve the host here; the owner should check directly with network access).

**Recommended next step:**
1. **Check whether `gitsafe-backup` (or anywhere else) already has `d98fd01`.** This determines urgency — if it's only ever existed locally, the fabricated data hasn't left this machine yet.
2. **Commit the current working tree** (frontend integration, geocoding, RBAC, M1 closure, and this GD-RDO-001 resolution — including the now-staged deletions of the three fabricated derivative datasets) as a new commit on top of `d98fd01`. This produces a commit whose *tree* is clean of the fabricated data, even though the fabricated data remains reachable from the `v1.0.0-alpha` tag one commit back in history.
3. **Cut a new tag on that clean commit** — `v1.0.0-alpha.1` or `v2.0.0-alpha.1` (per `ASTROOS_V2_RELEASE_PLAN.md`'s own proposed Phase A naming) — and treat *that* tag, not `v1.0.0-alpha`, as the one to point people at going forward.
4. **Separately decide** whether `v1.0.0-alpha` itself needs deleting/retracting as a git ref (`git tag -d` locally, plus coordination with anyone who already has it) given it contains fabricated data — this is a judgment call about how much it matters that an old, superseded tag remains reachable in history, and is intentionally left to the owner rather than decided here.

None of steps 1–4 are something this session will execute without separate, explicit confirmation, per the standing instruction to report-then-stop before any commit/tag/history operation on this repository.

**Phase B (Research Engine) may begin now regardless.** The fabricated-data defect lives in already-published git history, not in the working tree or in any code path — it doesn't block writing new Phase B code, per this repository's own established precedent (`ASTROOS_V2_RELEASE_PLAN.md`, "nothing about writing v2 code requires the tag to exist first"). It does mean whoever next looks at `v1.0.0-alpha` as a reference point should be told what §3 and §4 found.

---

*This report reflects direct repository inspection on 2026-07-17. It should be re-verified against `git log`/`git tag` if read significantly later, since it describes a moment-in-time git state that a future commit or tag will change.*
