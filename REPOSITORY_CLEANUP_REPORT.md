# Repository Cleanup Report

> Date: 2026-07-16
> Companion documents: [SECURITY_AUDIT_REPORT.md](SECURITY_AUDIT_REPORT.md), [GIT_CLEANUP_PLAN.md](GIT_CLEANUP_PLAN.md)

## Files deleted

14 files (13 individual files + 1 directory of 20 files) were removed from the working tree. All were confirmed obsolete backups, Replit-platform leftovers, confirmed stray artifacts, or obsolete implementation scratch before deletion.

| Category | Path | Reason |
|---|---|---|
| Obsolete backup | `apps/api/main.py.bak` | 1 commit behind `main.py` (missing events router registration) |
| Obsolete backup | `apps/api/repositories/event_repository.py.bak` | Byte-identical duplicate of the live file |
| Obsolete backup | `tests/conftest.py.bak` | Older version with leftover debug `print("[TR] ...")` tracing already cleaned from `conftest.py` |
| Replit | `.replit` | Replit platform config, no longer applicable |
| Replit | `replit.md` | Replit platform README variant, superseded by [README.md](README.md) |
| Replit | `replit.nix` | Replit Nix environment config |
| Confirmed stray | `dir` | Empty 0-byte file, artifact of a mistyped shell redirect |
| Confirmed stray | `desktop.ini` | Windows Explorer metadata pointing at a zip file no longer in the repo |
| Confirmed stray | `project_tree.txt` | 224 KB stale directory-listing dump, unreferenced anywhere |
| Obsolete implementation scratch | `a.py` | One-off local Postgres password-brute-force setup script |
| Obsolete implementation scratch | `try_chart.py` | Debug script; also contained a hardcoded JWT (see Security Audit §3 — confirmed never tracked by git) |
| Obsolete implementation scratch | `module14_phase3_architecture_md_addendum.md` | "Add this snippet" scratch note; described changes already merged into `event_repository.py` / `dependencies.py` |
| Obsolete implementation scratch | `module14_phase3_dependencies_snippet.py` | Same — snippet already applied |
| Obsolete implementation scratch | `AI_CONTEXT delete it once project is built/` (20 files) | Folder's own name was an explicit instruction to delete once the project is built; content (CLAUDE.md, architecture.md, module design-audit notes 13–27) is now superseded by `architecture/` and `docs/` |

**Git impact:** `.replit`, `replit.md`, and `replit.nix` were tracked in git (added in the initial commit, before `.gitignore` excluded them) — they now show as deletions (`D`) in `git status` and will be finalized on your next commit. All other 11 items were untracked working-tree files; their removal is immediate and not reflected in git history.

## `.env.example` change

See [SECURITY_AUDIT_REPORT.md §1](SECURITY_AUDIT_REPORT.md) — the hardcoded dev database password was replaced with a `<db-password>` placeholder. `.env` itself was not modified.

## Items reviewed but intentionally NOT touched

| Item | Why left alone |
|---|---|
| `apps/api/security/keys/{private,public}.pem` | Explicitly out of scope for deletion/rotation per your instructions — see full findings in [SECURITY_AUDIT_REPORT.md §2](SECURITY_AUDIT_REPORT.md) |
| `.git` bloat (dangling blobs + LFS cache) | Inspected only, nothing executed — see [GIT_CLEANUP_PLAN.md](GIT_CLEANUP_PLAN.md) |
| Root `ENGINEERING_*.md` vs `architecture/*.md` duplicate doc sets | Not part of this deletion pass; still flagged as diverging duplicates worth consolidating in a future pass |
| `__pycache__`, `.pytest_cache`, `node_modules` | Regenerable local cache dirs, already gitignored; left in place since they cost nothing to keep and regenerate automatically |
| Empty scaffold dirs (`architecture/{adr,future,handbook,research,rfc}`, `sdks/python/astroos/{api,models}`) | Look like intentional placeholders for planned work, not debris — flagged, not removed |
| `docker-compose.yml` plaintext dev password | Common low-risk pattern for local compose files; flagged as informational only, not changed |
| `datasets/rs/cohort/.../*.csv` (5.6 MB), `data/ephemeris/*.se1` (~2 MB) | Legitimate application/research assets, not junk — noted in the Git Cleanup Plan as candidates for LFS if committing them |

## Verification

```
$ git status --porcelain=v1 -uall | grep -E "main.py.bak|event_repository.py.bak|conftest.py.bak|replit.md|\.replit|replit.nix|^\?\? dir$|desktop.ini|project_tree.txt|^\?\? a.py$|try_chart.py|module14_phase3|AI_CONTEXT"
 D .replit
 D replit.md
 D replit.nix
```
Confirms all 14 targeted items are gone; the 3 previously-tracked Replit files show as pending deletions awaiting your next commit.

## Outstanding follow-ups (not yet approved for action)

1. Rotate the committed RSA private key and decide whether to purge it from git history — [SECURITY_AUDIT_REPORT.md §2](SECURITY_AUDIT_REPORT.md).
2. Run the two-step git object cleanup (`git reflog expire` + `git gc --prune=now`) to reclaim ≈415 MiB — [GIT_CLEANUP_PLAN.md](GIT_CLEANUP_PLAN.md).
3. Decide whether to pursue the larger history rewrite needed to reclaim the 399 MB LFS cache.
4. Consolidate the diverging `ENGINEERING_*.md` / `architecture/*.md` document pairs into a single source of truth.
5. Commit the pending `.replit`/`replit.md`/`replit.nix` deletions (and the `.env.example` fix) once you've reviewed this report.
