# Git Cleanup Plan

> Inspection only. None of the commands below (`git reflog expire`, `git gc`, `git lfs prune`) have been executed. This document lays out what each would do, the exact space reclaimed, the risk, and the recommended order — for your approval before anything runs.
> Date: 2026-07-16

## Current state

```
.git/                816 MB total
├── objects/         415.22 MiB (501 loose objects, 0 packed)
├── lfs/objects/      399 MB   (2 objects)
├── logs/ hooks/ etc.  ~2 MB
```

Only 5 commits exist on `main`. A `.git` this size for a 5-commit repo is entirely explained by two incidents, both traced below.

## Root cause

Commit `ff1e23e` ("Remove unnecessary large uploaded files from the project library", 2026-07-09) deleted two files from the working tree: `Vedic-Astro-Research.zip` (214 MB) and `zipFile.zip` (203 MB). Both were tracked via Git LFS (`.gitattributes` still has `filter=lfs` rules for both, byte-for-byte). Removing them from the tree did **not** remove their content from `.git` — that content lives on in two places:

1. **Two dangling loose blobs in `.git/objects`** (215,802,738 and 214,180,207 bytes on disk, ≈410 MiB combined) — these are pre-LFS full copies of the same two files. `git log --all --find-object=<hash>` returns **zero commits** for either blob across every branch, tag, and ref in the repo. They are provably unreachable — nothing points to them.
2. **The LFS cache** (`.git/lfs/objects`, 399 MB, exactly 2 files matching the same two zips) — these *are* still referenced. `git ls-tree` on commits `86d8ff1`, `638f65d`, `78de3f0`, and `b80eb15` (i.e., every commit on `main` before `ff1e23e`, plus their equivalents on the `replit-agent` branch) shows the LFS pointer files for both zips still present in those trees.

## What each command would actually do

### `git gc --prune=now`
Reclaims **≈415 MiB** — the confirmed-unreachable loose objects in `.git/objects` (item 1 above), plus a small amount of routine loose-object overhead. Standard `git gc` (no flags) would **not** touch these yet, because git's default 2-week grace period (`gc.pruneExpire`) protects loose objects younger than 2 weeks regardless of reachability, and these are ~8 days old. `--prune=now` overrides that grace period.

- **Impact assessment:** Low risk. Verified via `git fsck --unreachable` and `git log --all --find-object=<hash>` that both blobs are unreferenced by every commit, branch, and tag currently in the repo (including `replit-agent`). Removing them cannot orphan any reachable history.
- **Trade-off:** `--prune=now` skips the 2-week safety buffer that normally guards against a concurrent git operation writing a loose object mid-gc. For a single-developer local repo with no other git process running, this is negligible.

### `git reflog expire --expire=now --all`
Reclaims **0 bytes** directly, on its own. Checked: every reflog entry (`HEAD@{0}`–`{4}` on `main`, `replit-agent@{0}`–`{3}`) points to a commit that is *also* a normal reachable ancestor of a current branch tip — there are no amended-away or reset-away commits hiding in the reflog. Expiring it doesn't unlock any additional space beyond what `git gc --prune=now` already reclaims on its own.
- **Impact assessment:** Effectively a no-op for space, included only because it's the conventional pairing with `git gc --prune=now` and because you explicitly asked it be inspected. Running it removes your ability to `git reflog` your way back to a pre-cleanup `HEAD` if something *else* goes wrong during the same session — minor convenience loss, not a data-loss risk given the finding above.

### `git lfs prune`
Reclaims **0 bytes right now**. Verified directly:
```
$ git lfs prune --dry-run --verbose
2 local objects, 3 retained, done.
```
Both cached LFS objects are still "retained" — they're referenced by commits within LFS's default recency/retention window across two branches (`main`'s pre-`ff1e23e` history and `replit-agent`'s equivalent commits). LFS prune will not remove an object that's still referenced by reachable, recent history, regardless of whether the *current* tree still contains the file.
- **To actually reclaim this 399 MB**, the LFS pointer entries for `Vedic-Astro-Research.zip` and `zipFile.zip` would need to be purged from every commit that still contains them (`86d8ff1`, `638f65d`, `78de3f0`, `b80eb15`, and their `replit-agent` equivalents) via history rewrite (`git filter-repo`). That is a materially bigger, more disruptive operation — it changes every downstream commit hash, requires a coordinated force-push to the `gitsafe-backup` remote, and requires reconciling the `replit-agent` branch. **Not included in this plan** — flagging as a separate decision for you to make later, not bundling it with routine cleanup.

## Rollback considerations

- **The two dangling blobs (415 MiB) are safe to lose permanently.** They were never reachable from any commit; there is no "rollback" concept for objects nothing points to. Their content (the two zip files) is separately preserved in the LFS cache and in the tree history of 4 earlier commits anyway, so nothing is uniquely lost.
- **Remote backup exists.** `git remote -v` shows `gitsafe-backup` (git://gitsafe:5418, LFS endpoint http://gitsafe:5419), and the reflog confirms every commit on `main` has already been pushed there ("update by push" for `ff1e23e`, `b80eb15`, `78de3f0`, `638f65d`). Local `gc`/`reflog expire` do not touch that remote — it remains a full recovery point regardless of what's run locally.
- **`replit-agent` branch is untouched by this plan.** It has its own separate (but content-equivalent) commit history and is not affected by pruning `main`'s local objects.
- Once `git gc --prune=now` runs, the two dangling blobs are unrecoverable from this local repo (short of re-extracting them from the LFS cache or the remote, since their content is identical to what's LFS-cached). This is intentional — that's the entire point of the cleanup.

## Recommended execution order (pending your approval — nothing below has been run)

1. `git reflog expire --expire=now --all` — optional but conventional; confirmed no-op for space, negligible convenience trade-off.
2. `git gc --prune=now` — reclaims ≈415 MiB. This is the actual win.
3. **Do not run `git lfs prune` yet** — it will reclaim nothing today and isn't worth invoking until/unless you decide to pursue the larger history-rewrite to purge the LFS-tracked zips entirely.

## Expected result

| | Before | After steps 1–2 |
|---|---|---|
| `.git/objects` | 415.22 MiB | ≈5 MiB |
| `.git/lfs/objects` | 399 MB | 399 MB (unchanged) |
| **Total `.git`** | **816 MB** | **≈406 MB** |

Let me know if you'd like me to run steps 1–2, or if you'd rather batch this with a decision on the history rewrite for the LFS objects.
