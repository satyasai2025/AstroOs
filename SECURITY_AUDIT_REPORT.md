# AstroOS Security Audit Report

> Scope: `.env` / `.env.example` secret hygiene, `apps/api/security/keys/*.pem` provenance, and one credential found during the repository cleanup pass.
> Date: 2026-07-16
> No keys were rotated, regenerated, or deleted as part of this audit.

---

## 1. `.env` / `.env.example`

**Finding:** `.env` and `.env.example` were byte-identical. Every value in both files was inspected line by line.

| Variable | Value | Assessment |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://astroos:astroos_dev_password@localhost:5432/astroos` | The password matches `POSTGRES_PASSWORD: astroos_dev_password` in [docker-compose.yml](docker-compose.yml:20) — a local-only default for the dev Postgres container. Not a third-party or production credential, but it had no business being hardcoded in a *template* file. |
| `REDIS_URL` | `redis://localhost:6379/0` | Local, no auth token. Not sensitive. |
| `JWT_PRIVATE_KEY_PATH` / `JWT_PUBLIC_KEY_PATH` | File paths, not key material | Not sensitive (see §2 for the actual key files). |
| Everything else (`APP_NAME`, `DEBUG`, pool sizes, `BCRYPT_ROUNDS`, `ALLOWED_ORIGINS`, `EPHEMERIS_*`, etc.) | Plain config | Not sensitive. |

No API keys, cloud credentials, or third-party tokens were present in either file.

**Action taken:** [.env.example](.env.example) line 20 changed from the literal dev password to a placeholder:

```diff
- DATABASE_URL=postgresql+asyncpg://astroos:astroos_dev_password@localhost:5432/astroos
+ DATABASE_URL=postgresql+asyncpg://astroos:<db-password>@localhost:5432/astroos
```

A comment was added directing the developer to set `<db-password>` to match their `docker-compose.yml` / local Postgres instance, and not to reuse it across environments. All variable names were preserved exactly — no keys added, removed, or renamed. `.env` itself was left untouched (it's your real local config and is already gitignored).

**Not changed, informational only:** `docker-compose.yml` still contains `POSTGRES_PASSWORD: astroos_dev_password` in plaintext. This is a common, low-risk pattern for local dev compose files, but flagging it here since you asked for a full secrets pass — say the word if you'd also like that parameterized via a `.env`-backed variable.

---

## 2. `apps/api/security/keys/private.pem` / `public.pem`

**Determination: development-only key material by design and origin, but it was accidentally committed to git history.**

Evidence:

- **Generated locally, by design.** [apps/api/security/generate_keys.py](apps/api/security/generate_keys.py) generates a fresh 2048-bit RSA key pair (PKCS8, no passphrase) purely for local RS256 JWT signing. Its own docstring says: *"Keys are written to `apps/api/security/keys/` which is gitignored. In production, mount these keys as secrets ... do not bake them into container images."* This is unambiguous dev-tooling intent, not production key material.
- **No production/external signature.** No CA metadata, no reference to any secrets manager, no production deployment config anywhere in the repo points at this specific file as a production artifact.
- **Currently gitignored going forward** — [.gitignore](.gitignore) line 16 excludes `apps/api/security/keys/*.pem`.
- **But it was committed once, and never removed.** `git log --follow` shows exactly one commit touching these files:
  ```
  638f65d 2026-07-08  Fix horoscope calculations and improve testing stability
  ```
  That commit added `private.pem` (27 lines) and `public.pem` (9 lines) to the tree. No later commit removes or updates them in git — the `.gitignore` rule only stops *new* changes from being tracked, it does not retroactively remove already-tracked files. `git status` currently shows both files as **modified** (not untracked), confirming they are still tracked.
- **The working-tree copy is not the committed copy.** `git diff --stat` shows 32 lines changed in each file versus what's in git — meaning the key pair was regenerated locally at some point *after* 638f65d, but that regeneration was never committed. The private key sitting in your git history right now (and already pushed to the `gitsafe-backup` remote — see the Git Cleanup Plan) is an **older, still-recoverable key**, different from the one currently on disk.

**Risk:** Since this is an RS256 signing key for auth tokens (the same mechanism used to mint the bearer token found in the now-deleted `try_chart.py`), anyone with read access to this repository's git history — including the `gitsafe-backup` remote — can extract the committed private key and forge valid JWTs against any deployment still trusting that key.

**Recommendation (not executed — requires your approval):**
1. Treat the committed key as compromised. Rotate it (`python apps/api/security/generate_keys.py`) and commit the new **public** key only if you ever intend to track it — the private key should stay gitignored and untracked from this point forward.
2. If this repository will ever be made public, shared beyond its current owners, or handed to a new environment, the old private key needs to be purged from git history (not just the working tree) via `git filter-repo` or BFG Repo-Cleaner — this rewrites history and requires a coordinated force-push to `gitsafe-backup` and reconciliation with the `replit-agent` branch. This is a separate, larger operation from anything in the Git Cleanup Plan and should only be scheduled once you're ready for that disruption.
3. No key material has been rotated, deleted, or modified by this audit — steps 1 and 2 are pending your explicit go-ahead.

---

## 3. Credential found and removed during file cleanup

[try_chart.py](try_chart.py) (deleted as part of this cleanup pass, see [REPOSITORY_CLEANUP_REPORT.md](REPOSITORY_CLEANUP_REPORT.md)) contained a hardcoded JWT bearer token in plaintext, posted to `localhost:8000`. Checked `git ls-files` before deleting: **this file was never tracked by git** — it only ever existed in the working tree, so no git-history exposure occurred. The file itself is now gone; no further action needed on this item specifically, though its existence is a reminder to avoid pasting live tokens into scratch scripts even locally.

---

## Summary

| Item | Severity | Status |
|---|---|---|
| `.env.example` hardcoded dev DB password | Low | ✅ Fixed — placeholder substituted |
| `.env` real secrets | — | ✅ None found |
| Committed RSA private key (git history) | **High** | ⚠️ Identified, not remediated — awaiting your approval to rotate / purge history |
| JWT token in `try_chart.py` | Medium (mitigated) | ✅ File deleted; confirmed never entered git history |
| `docker-compose.yml` plaintext dev password | Informational | Not changed — flagged only |
