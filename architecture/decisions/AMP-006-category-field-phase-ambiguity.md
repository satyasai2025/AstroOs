---
id: AMP-006
title: "Category: enterprise" frontmatter field does not distinguish the four ROADMAP.md phases
status: CLOSED — ACCEPTED (Option B applied; Option A rejected) — 2026-07-19
severity: Low
source: Architecture Library Validation Audit (2026-07-15)
target_documents:
  - All 34 files under enterprise/*.md (frontmatter `category` field)
  - STATUS.md (Category column)
---

# AMP-006: Ambiguous "Category" Field Across the Library

## Finding

Every one of the 34 documents' frontmatter carries `category: enterprise`, and STATUS.md's "Category" column reproduces this verbatim — regardless of whether the document is actually a FOUNDATION, PLATFORM, ENTERPRISE, or FUTURE phase item per ROADMAP.md. For example, Plugin Lifecycle Management (a FOUNDATION-phase document) and Digital Twin (a FUTURE-phase document) both show "Category: enterprise." This conflates "part of the Enterprise Architecture Library" (the library's name) with "the ENTERPRISE phase" (one of its four quarters), and could mislead a reader who trusts STATUS.md's Category column instead of cross-referencing ROADMAP.md.

## Proposed Correction (Recommendation Only — Not Applied)

Two independent, non-exclusive options for governance to choose from:

- **Option A:** Add a distinct `phase:` frontmatter field (`foundation` / `platform` / `enterprise` / `future`) to each of the 34 documents, leaving `category: enterprise` as-is (denoting library membership). This is additive and would not require reinterpreting existing content.
- **Option B:** Add a "Phase" column to STATUS.md's Completed (Frozen) table, populated from ROADMAP.md, so the phase is visible without relying on the ambiguous Category field.

Since STATUS.md is a tracking file (not a frozen ADR document), Option B can proceed as routine maintenance. Option A touches all 34 frozen documents' frontmatter and would require a governance decision on whether a frontmatter-only addition needs a superseding ADR per document, or can be treated as non-substantive metadata maintenance — this AMP surfaces that question rather than deciding it.

## Impact

- **Frozen documents affected if Option A is chosen:** All 34 — frontmatter-only change, no body content affected.
- **Frozen documents affected if Option B is chosen:** None — STATUS.md only.
- **Reversibility:** Fully reversible either way; purely additive metadata.

## Resolution (Architecture Office, 2026-07-19)

**ACCEPTED — Option B. Option A REJECTED. CLOSED.**

Rationale: Option B (a "Phase" column in STATUS.md's Completed table, populated from ROADMAP.md) fully resolves the reader-facing ambiguity and is routine maintenance on a tracking file — applied. Option A (frontmatter edits to all 34 frozen documents) is rejected: even metadata-only touches to frozen enterprise documents create churn with no benefit beyond what Option B already provides, and those documents are outside the active local-first v2.1.0 scope. STATUS.md has been updated with the Phase column (FOUNDATION/PLATFORM/ENTERPRISE/FUTURE). No frozen document was modified.
