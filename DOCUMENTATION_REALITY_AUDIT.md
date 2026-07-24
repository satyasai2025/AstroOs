# AstroOS Documentation & Reality Audit

**Date:** 2026-07-22
**Scope:** Verify that top-level docs and status reports match what's actually in the codebase. Follow-up to the workstream proposed in `ASTROOS_PHASE_IV_V2_4_ROADMAP.md`.
**Method:** Direct inspection of source, git history, and test files — not a re-run of the full suite (pytest isn't installed in this sandbox).

## Summary

The specific stale-doc claim that motivated this audit doesn't hold up on closer inspection, and the other high-profile claims checked (the AMP-009/010 fix, the "2,114 tests" figure) are real. The genuine issues found are different: repo-root document sprawl (78 status/roadmap/report files), a handful of junk files from broken shell commands, and a currently-held git index lock that suggests another process may be writing to this repo at the same time.

## 1. Shadbala/Drekkana Bala claim — not actually stale

The prior session flagged `docs/architecture.md` as claiming Drekkana Bala and Saptavargaja Bala "aren't built" while the code has them. On inspection, `docs/architecture.md` is written as a phase-by-phase build log, not a single point-in-time status page. The line that reads "Drekkana Bala (not yet attempted)" is at the Module 9 Phase 2 checkpoint (~line 876), describing state as of that milestone — it's accurate for that point in the log.

The log's final Shadbala entry (~line 1209-1211) says `not_yet_implemented_components()` lists exactly one remaining item, `kala_bala.varsha_masa_lord`. I checked `apps/api/services/shadbala_engine.py` directly: `implemented_components()` lists 15 items including `sthana_bala.drekkana_bala` and `sthana_bala.saptavargaja_bala`, and `not_yet_implemented_components()` returns only `["kala_bala.varsha_masa_lord"]`. Doc and code agree at the current state. The doc's summary table even points at the code as the source of truth (`ShadbalaEngine().implemented_components()` directly) rather than hardcoding a number — a good pattern.

**Verdict:** not a real discrepancy. The earlier finding read an intermediate checkpoint in the log as if it were the current-state claim.

## 2. AMP-009/010 fix — confirmed real

`git log` shows `cdb102d fix(amp): resolve AMP-009/010 — PDF/CSV report endpoints and missing templates`, already merged into the branch history. Not just a status-doc claim — it's an actual commit.

## 3. "2,114 tests across 143 test files" — plausible, not exactly verified

`ASTROOS_V2_STATUS.md` claims 2,114 tests across 143 files. Pytest isn't available in this sandbox, so I couldn't collect the exact count, but static inspection is consistent with the claim: 1,653 raw `def test_...` function definitions across 122 files in `tests/`, before counting `async def test_` variants or parametrized cases (each parametrized case counts as a separate collected test in pytest, which easily accounts for the gap to 2,114). Files outside `tests/` weren't checked.

**Recommendation:** run `pytest --collect-only -q | tail -1` in the real dev environment to get an exact number next time this figure is cited, rather than carrying it forward from memory.

## 4. Repo-root document sprawl

78 markdown/txt files sit at the repo root — roadmaps, completion reports, governance audits, and status files, many for phases that are long since closed (`M2_MILESTONE_COMPLETE.md`, `PHASE_H_COMPLETION_REPORT.md`, `Phase_F_G_Governance_Audit_Report.md` and `Phase_F_G_H_Governance_Audit_Report.md` side by side, etc.). This isn't a correctness bug, but it's the actual mechanism behind stale-doc risk: with this many overlapping status documents, it's easy for one to drift from the code and hard for a reader (or an agent) to know which one is authoritative. `README.md` and `VERSION` do agree with each other and with the latest release (v2.3.0 "Lakshmi"), so the canonical entry points are fine — the risk is in the graveyard of superseded reports sitting alongside them at the same directory level.

**Recommendation:** move closed-phase reports into a `docs/history/` or `archive/` folder, keeping only the current roadmap, README, and CHANGELOG at root.

## 5. Junk files from broken shell commands

Six zero-byte, untracked files sit at repo root: `alembic`, `docker`, `echo`, `env.py`, `location`, `uvicorn`, plus `nul` (which contains literal error text: `dir: cannot access '/s'`, `dir: cannot access '/b'`). These look like leftovers from a Windows-style command (`dir /s /b > nul`) run in a POSIX shell, where `/s` and `/b` got treated as separate arguments and `nul` became a real file instead of the Windows null device. Harmless but untracked clutter (`git status` shows them as `??`).

**Recommendation:** delete these seven files; add `nul` to `.gitignore` as a guard against recurrence if commands like this get run again from a Windows-originated script.

## 6. Concurrent process warning

`git status` and `git diff --stat` both failed on first attempt with `unable to unlink '.git/index.lock': Operation not permitted`, and a plain `git status` took long enough to time out once. This means another process (very possibly the other Claude session referenced in `ASTROOS_PHASE_IV_V2_4_ROADMAP.md`, or a local git client) may be holding a lock on this repo concurrently. This audit was read-only throughout, but it's worth flagging so two agents don't clobber each other's commits.

## 7. Not checked

For scope/time reasons this pass did not: run the full test suite, verify claims in every one of the 78 root-level docs, check `docs/architecture.md` sections beyond the Shadbala module, or verify the SBOM/third-party dataset audit contents.

---
*This report itself follows the repo's existing convention of a standalone root-level `.md` audit file — consider it a candidate for the archive folder proposed in §4 once its findings are actioned.*
