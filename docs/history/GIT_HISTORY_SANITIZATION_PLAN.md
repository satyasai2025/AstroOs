# Git History Sanitization Plan — RSA Private Key Purge

> Planning only. **No command in this document has been executed.** This plan lays out what a full purge of the compromised RSA private key from git history would involve, the exact risks and blockers, and the recommended order — for approval before anything runs.
> Date: 2026-07-17

## 1. What's being purged, and why this is now lower-urgency (not zero-urgency)

`apps/api/security/keys/private.pem` (RS256 signing key for JWT auth) was committed in `638f65d` (2026-07-08) and removed from tracking — but not purged from history — in `029441a`. It remains fully recoverable from any clone via `git show 029441a^:apps/api/security/keys/private.pem`.

**The active-exposure risk was already closed**: the key was rotated this session (fresh 2048-bit keypair generated, old key no longer used for signing). What remains is a *retired* key sitting permanently in git history — a hygiene/compliance concern, not a live vulnerability. Anyone who already cloned this repo before rotation has had the old key regardless of whether history is ever purged; a purge only prevents *future* clones (or a future public release) from picking it up. This reframes the purge as important-but-not-urgent, which is worth weighing against its cost (below).

## 2. Exact scope of the exposure

| Fact | Value |
|---|---|
| File(s) | `apps/api/security/keys/private.pem`, `apps/api/security/keys/public.pem` (public key isn't sensitive by design, but was added in the same commit) |
| Introduced in | `638f65d` — "Fix horoscope calculations and improve testing stability" (a large, mixed commit — lots of unrelated real work in the same commit, not just the key) |
| Removed from tracking (not purged) in | `029441a` — "Stop tracking development RSA keys" |
| Other secrets ever tracked in history | **None found.** Searched all commits, all refs, for any other `*.pem`/`*.key` file — only these two. |
| Refs that contain `638f65d` | `main`, `replit-agent`, `claude/gallant-brattain-bee0a5`, `remotes/gitsafe-backup/main` — **all four** |
| Remotes | Only one: `gitsafe-backup` (`git://gitsafe:5418/backup.git`) — already has every commit through `029441a` pushed, including the compromised one |
| Tags | None exist — nothing extra to rewrite |

**Consequence of scope:** `main` only has 6 commits total, and the bad one is commit #2. Purging it means **5 of `main`'s 6 commits get new hashes** (everything from `638f65d` onward) — this isn't a surgical single-commit fix, it's a rewrite of nearly the entire repo history. `replit-agent` and `claude/gallant-brattain-bee0a5` are affected the same way.

## 3. Critical blocker: the working tree is not clean

**This is the top prerequisite, and it's not optional.** `git filter-repo` (see tool choice below) either operates on a fresh clone, or — if run in-place — refuses to proceed on a repo with staged/unstaged/untracked changes unless forced, because its normal workflow resets the working directory to match the rewritten history.

Right now this repo has **685 uncommitted `git status` entries** — the pre-existing large uncommitted body of work plus everything built this session (26 new router/schema files, `main.py` wiring, the review fixes). None of it is committed. Running any history rewrite against this working directory today would either be refused outright, or — if forced — would **destroy all of that uncommitted work**.

**This must be resolved first, and it's a separate decision from the purge itself:** either (a) commit the current state first (which itself is gated by the same report-first rule as this purge, and by the still-open [FOUNDATION_RELEASE_REVIEW.md](FOUNDATION_RELEASE_REVIEW.md) blockers), or (b) stash/back up the working tree changes somewhere safe before rewriting, then reapply them after. I'd recommend (a) once you're ready to commit — rewriting history on top of an already-clean, committed baseline is far safer than trying to rewrite around 685 pending changes.

## 4. Tool choice

`git filter-repo` — not `git filter-branch` (git's own docs call it unsafe/deprecated for this) and not BFG (Java dependency, coarser control). **Not currently installed** in this environment (`pip install git-filter-repo` required first — `pip` 25.2 / Python 3.13 already available, so this is a low-friction install).

## 5. Proposed steps (none executed)

### Phase A — safety net
1. Resolve the clean-working-tree blocker (§3) — your decision on commit-first vs. stash-first.
2. `pip install git-filter-repo`.
3. Create a full local mirror backup before touching anything: `git clone --mirror <this-repo> ../astroos-pre-purge-backup.git`. This is the actual undo button — keep it until the purge is verified end-to-end.

### Phase B — rewrite (performed on a mirror clone, not this working directory)
4. `git clone --mirror <this-repo> ../astroos-sanitize.git && cd ../astroos-sanitize.git`
5. `git filter-repo --path apps/api/security/keys/private.pem --path apps/api/security/keys/public.pem --invert-paths --force`
   — strips both files from every commit, across every branch, in one pass. Since `638f65d` contains substantial unrelated real work, it will **not** become an empty commit — only the two key blobs are removed from its tree.
6. Verify inside the mirror: `git log --all --oneline -- apps/api/security/keys/*.pem` returns nothing; `git show 029441a^:apps/api/security/keys/private.pem` (using the **old** hash, checked against the **pre-purge backup**) fails against the sanitized copy.
7. `git reflog expire --expire=now --all && git gc --prune=now --aggressive` inside the sanitized mirror, to actually drop the now-unreferenced blobs (23 reflog entries currently exist that would otherwise keep pinning them).

### Phase C — propagate
8. Force-push every rewritten ref to `gitsafe-backup`: `git push --force --all gitsafe-backup` (no tags exist, so nothing extra there). This is the only remote, so this is the only coordinated force-push needed — no second host/team to synchronize with beyond whoever else already has a clone.
9. Replace this working directory's history with the sanitized version — either re-clone fresh from the sanitized `gitsafe-backup`, or run the same `git filter-repo` command directly against this repo (only safe once §3 is resolved).
10. Explicitly decide the fate of `replit-agent` and `claude/gallant-brattain-bee0a5` before rewriting them reflexively — `replit-agent` in particular has an odd pattern of duplicate-message commits with different hashes alongside the real ones (likely a prior rebase/squash artifact from the Replit agent tool), worth a quick look to confirm it's still a branch worth keeping rather than mechanically preserving a stale line of history.

### Phase D — verify and close out
11. Confirm the old blob is unreachable in the sanitized repo: `git rev-list --objects --all | grep <old-private-key-blob-sha>` returns nothing.
12. Confirm `gitsafe-backup` reflects the new hashes.
13. Update [SECURITY_AUDIT_REPORT.md](SECURITY_AUDIT_REPORT.md) to record the purge date and method.
14. Retain the Phase A mirror backup for a defined period (e.g. 30 days) in case something downstream breaks, then delete it.

## 6. What this plan deliberately does NOT cover

- **`git gc`/LFS bloat cleanup** — already fully planned separately in [GIT_CLEANUP_PLAN.md](GIT_CLEANUP_PLAN.md); unrelated to the key and not bundled in here.
- **Anyone who already cloned this repo before the purge** keeps the old key in their local history regardless of what happens here — a purge protects future clones only, not past ones. Already-rotated key (§1) is what protects against *those* clones being useful to an attacker.
- **Committing the 685 pending changes** — a prerequisite (§3), but its own separate, larger decision (see [FOUNDATION_RELEASE_REVIEW.md](FOUNDATION_RELEASE_REVIEW.md)'s still-open blockers), not something this plan decides.

## 7. Recommended sequencing relative to everything else pending

Given §1's reframing (already-rotated key = no active exposure) and §3's blocker (would destroy 685 uncommitted changes if run today), I'd recommend **not** running this purge in isolation right now. It fits more naturally *after* a decision is made on committing the current baseline — at that point Phase A–D becomes a clean, low-drama operation instead of one that has to route around a large uncommitted working tree.

---

*Nothing in this document has been executed. Awaiting your decision on sequencing (§7) and on the working-tree prerequisite (§3) before any command runs.*
