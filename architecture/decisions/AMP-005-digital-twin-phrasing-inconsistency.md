---
id: AMP-005
title: Digital Twin mixes cardinal and ordinal phrasing for the same confirmation count
status: CLOSED — REJECTED (cosmetic; no superseding ADR warranted) — 2026-07-19
severity: Low (Informational)
source: Architecture Library Validation Audit (2026-07-15)
target_documents:
  - enterprise/digital-twin.md (ADR-EAL-030)
---

# AMP-005: Digital Twin Cardinal/Ordinal Phrasing Inconsistency

## Finding

Digital Twin §12 (Alternatives Considered) reads "after five consecutive confirmations" (cardinal, no ordinal suffix), while §2, §7 (twice), and §14 of the same document describe the identical fact as "the sixth consecutive confirmation" (ordinal). The underlying numbers are arithmetically consistent (five prior documents plus Digital Twin itself equals the sixth) — this is a phrasing-style inconsistency, not a numeric error.

## Proposed Correction (Recommendation Only — Not Applied)

Reword §12's "after five consecutive confirmations" to "after the fifth consecutive confirmation" (or equivalent ordinal phrasing) for internal stylistic consistency. Purely cosmetic; no architectural content changes. Digital Twin is frozen — a correction requires a new ADR superseding ADR-EAL-030, per governance mode.

## Impact

- **Frozen documents affected:** Digital Twin (ADR-EAL-030) — a superseding ADR would be required to touch it.
- **Reversibility:** Trivial; wording polish only.

## Resolution (Architecture Office, 2026-07-19)

**REJECTED. CLOSED.**

Rationale: The AMP itself notes the numbers are arithmetically consistent — this is style-only, not even an error. Digital Twin (ADR-EAL-030) is a frozen FUTURE-phase document outside local-first v2.1.0 scope. A superseding ADR for wording polish is not justified under any circumstances, let alone for an out-of-scope document. No further action; no frozen document was modified.
