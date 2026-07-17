---
id: AMP-005
title: Digital Twin mixes cardinal and ordinal phrasing for the same confirmation count
status: Proposed — Awaiting Approval
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

## Status

Awaiting approval. No frozen document has been modified by this AMP.
