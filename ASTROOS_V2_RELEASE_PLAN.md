# AstroOS v2.0 Release Plan

> Versioning, tagging, and deployment strategy for v2. Planning only — no tag or release has been created.
> Date: 2026-07-17

## Versioning scheme

Each phase deliverable in `ASTROOS_V2_ROADMAP.md` is tracked as its own alpha/beta milestone rather than one big-bang v2.0.0 release:

| Phase | Deliverable | Proposed tag |
|---|---|---|
| A | AstroOS Platform Alpha | `v2.0.0-alpha.1` |
| B | AstroOS Research Platform | `v2.0.0-alpha.2` |
| C | Benchmark reports operational | `v2.0.0-alpha.3` |
| D | Knowledge Intelligence live | `v2.0.0-beta.1` |
| E | AI Layer live | `v2.0.0-beta.2` |
| F | Reports (PDF/JSON/API export) | `v2.0.0-beta.3` |
| G | SDK complete | `v2.0.0-rc.1` |
| H | Production-ready | `v2.0.0` |

This scheme is a proposal, not yet approved — record any change to it here rather than silently deviating.

## Baseline dependency

This plan originally assumed a `v1.0.0-foundation` tag would exist as the point v2 branches from, gated on resolving the items `FOUNDATION_RELEASE_REVIEW.md` flagged (compromised RSA key, RS-COHORT duplicate, the RS-EVENT data-integrity finding `GD-RDO-001`). **That specific tag name was never cut — the repository owner instead tagged `v1.0.0-alpha` directly** (commit `d98fd01`, 2026-07-17), addressing the RSA-key and RS-COHORT items but predating this session's `GD-RDO-001` investigation and closure (now resolved — see `research-data/governance/GD-RDO-001_RS_EVENT_DATA_INTEGRITY.md`) and predating Phase A's completion (Workflow Orchestrator, frontend, geocoding, RBAC, M1 closure — all built after that tag, still uncommitted).

**Consequence:** the already-tagged `v1.0.0-alpha` is a real but incomplete snapshot — it doesn't contain the deliverable its own name refers to. v2 (this document's own scope) has continued being built directly on top of the uncommitted working tree regardless, same as before the tag existed. See `ALPHA_RELEASE_READINESS_REPORT.md` (2026-07-17) for the full assessment and recommendation on what to do about the tag/working-tree gap before Phase B begins.

This is tracked as an open decision, not a blocker for continued implementation — see `ASTROOS_V2_ROADMAP.md`'s "Open dependency" section.

## Deployment strategy (Phase H, not yet started)

Placeholder pending Phase H work: Docker packaging, monitoring/logging, backup strategy, deployment pipeline, and the release pipeline itself all remain to be designed. Filling this in prematurely would duplicate Architecture's ownership of infrastructure decisions — this section stays a placeholder until Phase H begins.

## Change log discipline

Every tagged release (starting with `v2.0.0-alpha.1`, whenever it's cut) gets an entry in `CHANGELOG_V2.md`. Untagged in-progress work is still logged there dated by day, per that document's own convention, so the changelog doesn't have gaps between releases.

---

*Last updated: 2026-07-17*
