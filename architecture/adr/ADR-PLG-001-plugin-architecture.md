# ADR-PLG-001: Plugin Architecture — Local Sandbox with File-Based Manifest Registry

**Status:** Accepted
**Date:** 2026-07-20
**Owner:** Architecture (CAO)
**Phase:** III.2 — Plugin Architecture & Local Registry

## Context

Phase III requires an extensible plugin system that allows users to add custom calculators, report themes, and data sources. The local-first mandate prohibits a hosted marketplace, Stripe payments, or a cloud developer portal (per `PHASE_III_LOCAL_FIRST_AUDIT.md`).

## Decision

Adopt a **local-first plugin architecture** with sandboxed execution and a file-based manifest registry:

1. **Plugin discovery** — A bundled `plugins/registry.json` ships with the app, listing available plugins by name, version, description, and download URL (GitHub release tarball). No hosted registry server.
2. **Installation** — `astroos plugin install <name>` downloads the plugin from its URL in `registry.json` and extracts it to `~/.astroos/plugins/<name>/`. The CLI verifies the plugin's `plugin.json` manifest against a JSON Schema.
3. **Sandbox** — Plugins run in a subprocess with CPU/memory limits (via `resource` module on POSIX, or `subprocess` with ulimit on Linux). Network access is blocked by default; opt-in via plugin manifest.
4. **API surface** — Plugins receive a read-only snapshot of chart data via stdin (JSON). They return results via stdout (JSON). No direct filesystem or network access inside the sandbox.
5. **No hosted marketplace** — Plugin distribution is decentralized: authors publish tarballs on GitHub/GitLab; users add URLs to their local `registry.json` or install from a local path.

## Alternatives considered

- **Hosted marketplace with Stripe payments** — rejected: requires cloud infrastructure, payment processing, developer portal. Violates local-first mandate.
- **npm-based plugin system** — rejected: installs Node.js packages with full filesystem access. Sandbox boundary unclear.
- **Python import hooks** — rejected: in-process execution of untrusted code. No isolation.

## Consequences

- Plugin discovery is manual (add URL to registry.json) or CLI-based from bundled list.
- No automatic updates — users run `plugin update` to refresh.
- Sandboxed execution prevents malicious plugins from accessing the filesystem or network.
- The system is fully offline-capable: plugins ship with the app or are downloaded once.

---
*Author: Architecture Office, 2026-07-20*
