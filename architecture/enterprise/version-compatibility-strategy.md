---
title: Enterprise Version Compatibility Strategy
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Version Compatibility Strategy

## 1. Problem Statement

**Audit finding, consistent with the pattern identified in [Enterprise Dependency Management](dependency-management.md) (ADR-EAL-007):** two frozen documents already implement version-compatibility logic independently, without a shared, explicit policy defining what the underlying semantics actually mean:

- [Enterprise Plugin Lifecycle Management](plugin-lifecycle-management.md) (ADR-EAL-001) specifies a **Compatibility Checker** (PLM §4) that validates a plugin's declared host-version range against the current host API version (PLM §9), including a notion of "breaking-change signaling" and a "deprecation window" (PLM §9) — but neither term is given a precise, cross-library definition.
- [Enterprise Dependency Management](dependency-management.md) (ADR-EAL-007) specifies a **Version-Range Validator** (EDM §4) that checks whether a declared dependency's version-range constraint is satisfiable against a target's current version — using, by its own admission (EDM §18), "simple semver-range checking" with no further-specified policy.

Both components answer variations of the same underlying question — *is version A compatible with version B, and if not, was the incompatibility introduced in a governed, predictable way* — but each was specified with its own implicit assumptions about semver semantics, what counts as a breaking change, and how long a deprecation window should last. Unlike the EDM finding (duplicate *graph logic*), this is a duplication of *policy/semantics* with no shared, written contract — a subtler but equally real instance of the "reuse before creating" gap, and one that will only compound as more documents in this library (the Module Registry's interface versioning, the Capability Registry's Stable-maturity promotion criteria, ECF's config schema versioning) each make their own implicit versioning assumptions.

The Enterprise Version Compatibility Strategy (EVCS) defines the single, canonical versioning policy — semver interpretation, breaking-change classification, deprecation window standard, and a compatibility-declaration format — that any component in this library can conform to, so "compatible" means the same thing everywhere it's checked.

**Scope boundary, respecting the "no redesign of approved modules" constraint:** this document does **not** modify PLM's Compatibility Checker or EDM's Version-Range Validator as specified in their frozen documents. It defines the policy those components already *implicitly* approximate, and — mirroring the precedent set in EDM (ADR-EAL-007) — leaves the question of whether/how to update either component to explicitly conform to this written policy as an **open question, deferred to a future ADR** against ADR-EAL-001 and/or ADR-EAL-007 respectively, not decided by this document.

## 2. Goals

| Goal | Description |
|---|---|
| **One definition of "compatible"** | A single, precise policy for semver interpretation and range satisfiability, referenceable by any component instead of each assuming its own. |
| **Breaking-change classification standard** | A clear, consistent rule for what constitutes a breaking (major), additive (minor), or fix-level (patch) change, applicable uniformly to host APIs, module interfaces, plugin contracts, and capability interfaces. |
| **Deprecation window standard** | A defined minimum notice period and signaling mechanism between announcing a breaking change and enforcing it, applicable wherever "deprecation" is already referenced in this library (PLM §9, Module Registry §6/§10, Capability Registry Appendix B). |
| **Compatibility declaration format** | A single, reusable format for expressing a version-range constraint and a compatibility result, so PLM's Compatibility Checker and EDM's Version-Range Validator (and any future component) can express the same concept identically. |
| **Non-disruption of frozen decisions** | Adoption does not require, and does not itself perform, any change to PLM (ADR-EAL-001) or EDM (ADR-EAL-007) as currently specified. |

**Non-goals**: EVCS does not itself check any actual version pair (that remains PLM's and EDM's respective runtime responsibility); it does not decide whether PLM or EDM must adopt it (an explicit open question, §16); it does not define deployment/release cadence policy, only compatibility semantics.

## 3. Architecture

```
   ┌───────────────────────────────────────────────────────────┐
   │        Enterprise Version Compatibility Strategy             │
   │        (policy/contract specification — no runtime          │
   │         component of its own beyond the artifacts below)     │
   │                                                                │
   │   ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
   │   │ Semver            │  │ Breaking-Change   │  │ Deprecation   │ │
   │   │ Interpretation      │  │ Classification    │  │ Window        │ │
   │   │ Rules               │  │ Rules              │  │ Standard      │ │
   │   └─────────────────┘  └─────────────────┘  └──────────────┘ │
   │   ┌─────────────────────────────────────────────────────────┐ │
   │   │  Compatibility Declaration Format (shared schema)          │ │
   │   └─────────────────────────────────────────────────────────┘ │
   └──────────────────────────────┬────────────────────────────────┘
                                  │ referenced/conformed to (optionally,
                                  │ per §1 scope boundary — not enforced
                                  │ on already-frozen components)
          ┌───────────────────────┼───────────────────────┐
          │                       │                        │
┌─────────▼────────┐   ┌──────────▼─────────┐   ┌──────────▼─────────┐
│ PLM Compatibility  │   │ EDM Version-Range    │   │ Future components   │
│ Checker (existing,  │   │ Validator (existing,  │   │ (Module Registry     │
│ unchanged)          │   │ unchanged)            │   │ interfaces, Capability│
│                     │   │                       │   │ Registry maturity,   │
│                     │   │                       │   │ ECF schema versions) │
└───────────────────┘   └───────────────────┘   └───────────────────┘
```

EVCS is deliberately drawn as a **policy specification**, not a new runtime service — unlike EDM (a shared *component*), this document's output is a written contract that other components can choose to conform to, which is why it introduces no new runtime interfaces of its own beyond the declaration format.

## 4. Components

Because EVCS is a policy specification rather than a runtime engine, its "components" are the artifacts that make up the policy itself, not services:

- **Semver Interpretation Rules** — the precise definition of MAJOR.MINOR.PATCH semantics adopted across this library: what a version number means, how ranges (`>=`, `<`, caret/tilde-style ranges) are interpreted, and how pre-release/build metadata (if used) affects comparison.
- **Breaking-Change Classification Rules** — a concrete rubric for classifying a given change to a host API, module interface, plugin contract, or capability interface as MAJOR (breaking), MINOR (additive, backward-compatible), or PATCH (fix, no interface change) — the missing definition that both PLM §9 ("breaking-change signaling") and the general notion of "interface versioning" (Module Registry §10) currently reference without specifying.
- **Deprecation Window Standard** — a minimum notice period and required signaling behavior (a compatibility check must surface a warning-level result, not just eventually fail) between when a breaking change is announced and when it is enforced, generalizing the "deprecation window" already named but not quantified in PLM §9.
- **Compatibility Declaration Format** — a shared schema for expressing (a) a version-range constraint and (b) a compatibility check result (compatible / compatible-with-deprecation-warning / incompatible, plus a specific diagnostic), so that PLM's Compatibility Checker and EDM's Version-Range Validator, if they choose to conform, produce results that are format-equivalent even if their invocation contexts differ.

## 5. Interfaces

EVCS's "interfaces" are conformance points rather than runtime APIs, since it defines policy, not a callable service:

| Conformance Point | Consumer | Purpose |
|---|---|---|
| Compatibility Declaration Format schema | PLM's Compatibility Checker (optionally, if conformance is later approved) | Express plugin↔host version-range constraints and results in the shared format. |
| Compatibility Declaration Format schema | EDM's Version-Range Validator (optionally, if conformance is later approved) | Express dependency-edge version-range constraints and results in the shared format. |
| Breaking-Change Classification Rules | Any document/team versioning a host API, module interface, plugin contract, or capability interface | A shared rubric for deciding "is this change MAJOR/MINOR/PATCH," reducing inconsistent, ad hoc judgment calls. |
| Deprecation Window Standard | Module Registry's deprecation workflow (§6, §10), Capability Registry's Deprecated stage (Appendix B), PLM's deprecation signaling (§9) | A common minimum notice period and warning-signal behavior, referenceable wherever any of those documents already handle deprecation. |

## 6. Data Flow

Because EVCS defines policy rather than runtime behavior, its "data flow" describes how the policy is authored and referenced, not a request-time sequence:

1. This document establishes the Semver Interpretation Rules, Breaking-Change Classification Rules, Deprecation Window Standard, and Compatibility Declaration Format as the canonical reference.
2. Any team introducing a new versioned interface (host API, module interface, plugin manifest contract, capability interface) classifies changes against the Breaking-Change Classification Rules (§4) when deciding whether to bump MAJOR/MINOR/PATCH.
3. Where a deprecation is being announced (Module Registry §6/§10, Capability Registry Appendix B, PLM §9), the announcing party applies the Deprecation Window Standard's minimum notice period and signaling requirement.
4. Where a component performs an actual compatibility check at runtime (PLM's Compatibility Checker, EDM's Version-Range Validator), it may — per the deferred conformance decision in §16 — express its constraint and result using the Compatibility Declaration Format, without requiring any change to how the check itself is computed internally.
5. No data flows *into* EVCS from either existing component under this decision; adoption is unidirectional and voluntary until/unless a future conformance ADR is approved.

## 7. Design Patterns

- **Policy-as-specification, not policy-as-code** — this document intentionally stops short of "policy-as-code" (a future evolution already flagged for the Module Registry, §18, and ECF, §18); it establishes the human-readable, referenceable rules first, leaving automated enforcement as a later, separate evolution.
- **Shared contract format, independent enforcement points** — directly analogous to how the Capability Registry (§1) resolves a capability to a provider without owning the provider's data; here, EVCS defines a shared *format* for expressing compatibility without owning or replacing the *checking logic* that already exists in PLM and EDM.
- **Additive, non-redesigning policy introduction** — mirrors the precedent set by EDM (ADR-EAL-007): a new, referenceable capability is introduced without mandating any change to already-frozen documents, with conformance explicitly deferred to a future, separately-approved decision.

## 8. Security Considerations

- **Breaking-change misclassification as a security-relevant risk** — an interface change incorrectly classified as MINOR when it is actually breaking (e.g., silently narrowing an accepted input range in a way that changes security-relevant validation behavior) could cause a consuming component to accept a version it should have rejected; the Breaking-Change Classification Rules (§4) should explicitly call out security-relevant behavior changes as a MAJOR-classification trigger, not just wire-format changes.
- **Deprecation window as a security patch consideration** — a security-motivated breaking change (e.g., closing a vulnerability that requires an interface change) may warrant a shortened or waived deprecation window; the Deprecation Window Standard (§4) should explicitly allow for an expedited path for security-driven breaking changes, rather than mandating the full standard notice period unconditionally.
- **No secrets in compatibility declarations** — consistent with every manifest/schema pattern elsewhere in this library, the Compatibility Declaration Format carries only version/range/result metadata, never credential material.

## 9. Scalability

- As a policy specification rather than a runtime service, EVCS itself has no request-path performance profile. Its practical scalability concern is **organizational, not computational**: the Breaking-Change Classification Rules and Deprecation Window Standard must be simple enough to apply consistently across a growing number of versioned interfaces (host API, module interfaces, plugin contracts, capability interfaces) without requiring case-by-case reinterpretation each time — a rubric that only works for one interface type today would fail this goal as the library grows.
- If a future conformance decision (§16) leads PLM's Compatibility Checker or EDM's Version-Range Validator to adopt the shared Compatibility Declaration Format, the scalability characteristics of *that* work remain governed by each component's own frozen document (PLM §9, EDM §9) — EVCS does not alter their performance profile.

## 10. Best Practices

- Apply the Breaking-Change Classification Rules at the moment a change is authored, not retroactively — classification is easiest and most accurate when done by the person making the change, with full context.
- Treat "shortened deprecation window for a security fix" as an explicit, logged exception to the standard, never a silent default — the standard window remains the default precisely so exceptions stand out as exceptions.
- When introducing a new versioned interface anywhere in this library going forward, reference EVCS's rules explicitly in that document rather than re-deriving an implicit versioning policy, per the same discovery-search discipline already established by the Module Registry (§10) and reinforced by EDM (§11).

## 11. Common Pitfalls

- **Treating this document as retroactively redefining PLM's or EDM's already-frozen behavior** — the single most important pitfall to avoid, mirroring the equivalent caution in EDM (§11); EVCS documents policy for voluntary future conformance, it does not silently reinterpret existing frozen specifications.
- **Ad hoc, per-team breaking-change judgment calls** — without a shared rubric, "is this breaking" tends to be decided inconsistently across teams/interfaces, which is precisely the fragmentation this document exists to prevent.
- **Treating the deprecation window as a suggestion rather than a floor** — a deprecation window that can be silently skipped under schedule pressure provides no real guarantee to consumers, undermining the entire point of having a standard.
- **Over-engineering into policy-as-code prematurely** — attempting to build automated enforcement (§7) before the written policy itself has been validated in practice risks encoding an unproven or incomplete rubric into automation.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **Leave versioning policy implicit, as today** | Accept that PLM's Compatibility Checker and EDM's Version-Range Validator each carry their own unwritten assumptions. | Directly contradicts "reuse before creating"; leaves the classification/deprecation-window ambiguity unresolved and likely to worsen as more versioned interfaces are added. |
| **Immediately mandate conformance in PLM and EDM** | Require both existing components to be updated to explicitly reference EVCS's format now. | Violates the "no redesign of approved modules" charter boundary without a separate approval for each; this document instead defers that decision explicitly (§16), consistent with the EDM precedent. |
| **Build EVCS as a runtime policy-enforcement engine (policy-as-code) immediately** | Skip the written-policy stage and go straight to automated, code-enforced compatibility policy. | Premature: a policy should be validated in written, human-reviewable form first (§7, §11) before being encoded into automated enforcement; also a larger scope commitment than this document's mandate, though noted as valid future evolution (§18). |
| **Fold this policy directly into EDM's document as an addendum** | Extend the already-frozen EDM document with a compatibility-policy appendix rather than a new document. | Would itself require reopening a frozen, approved document without a dedicated ADR for that specific change, and would conflate a graph/dependency capability (EDM's actual scope) with a versioning-semantics policy (a different concern) — the same scope-distortion risk avoided elsewhere in this library (e.g., keeping ESR separate from ECR, Service Registry §12). |

## 13. Migration Strategy

1. **Publish the Semver Interpretation Rules, Breaking-Change Classification Rules, Deprecation Window Standard, and Compatibility Declaration Format** as this document's frozen artifacts — no runtime change required to adopt step 1.
2. **Apply the Breaking-Change Classification Rules and Deprecation Window Standard prospectively** to any new versioned interface introduced in future Enterprise Architecture Library documents, per the discovery-search discipline in §10.
3. **Reference EVCS's rules when any existing document's deprecation workflow is actually exercised** (e.g., the next time the Module Registry's deprecation workflow or the Capability Registry's Deprecated stage is invoked in practice), as a non-invasive way to start applying the standard without modifying either frozen document's specification.
4. **Separately propose, if desired, a conformance ADR against ADR-EAL-001 (PLM)** to have its Compatibility Checker explicitly adopt the Compatibility Declaration Format — a distinct, future decision, not a consequence of this document.
5. **Separately propose, if desired, a conformance ADR against ADR-EAL-007 (EDM)** to have its Version-Range Validator explicitly adopt the same format — likewise a distinct, future decision.
6. **Only after such conformance ADRs (if any) are approved** would PLM's or EDM's compatibility-result representation actually change; this document does not assume that outcome.

## 14. Success Criteria

- Every future Enterprise Architecture Library document that introduces a versioned interface references the Breaking-Change Classification Rules and Deprecation Window Standard explicitly, rather than each re-deriving its own implicit policy.
- No new versioning-policy logic is specified in a future document without first checking EVCS (mirroring the discovery-search success metric already defined for the Module Registry, §14, and EDM, §14).
- Zero unauthorized modifications to PLM's or EDM's frozen specifications as a side effect of this document's adoption.
- If a future conformance ADR is approved for either PLM or EDM, the resulting behavior is equivalent to (not a regression from) each document's originally frozen compatibility semantics.

## 15. Decision Matrix

| Criterion (weight) | Written policy specification, additive/voluntary conformance (recommended) | Leave policy implicit (status quo) | Immediately mandate conformance in PLM/EDM | Build policy-as-code engine immediately | Fold into EDM as an addendum |
|---|---|---|---|---|---|
| Closes the policy-duplication finding (High) | 5 | 1 | 5 | 5 | 4 |
| Respects "no redesign of approved modules" (High) | 5 | 5 | 1 | 3 | 2 |
| Applicable across all versioned interfaces in the library (Medium) | 5 | 1 | 3 | 4 | 3 |
| Maturity/validation before automation (Medium) | 5 | 3 | 3 | 1 | 3 |
| Implementation/governance overhead (Medium, lower = better fit) | 4 | 5 | 2 | 1 | 3 |
| **Weighted outcome** | **Best overall fit** | Fails core principle | Fails charter boundary | Premature automation | Scope conflation with EDM |

**Conclusion**: a written, voluntarily-adoptable policy specification is recommended, consistent with the precedent set for EDM. It closes the policy-duplication finding and gives every future document a shared reference, without requiring or implying any change to PLM's or EDM's already-frozen specifications.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-008: Enterprise Version Compatibility Strategy as a Written Policy Specification, Adopted Voluntarily**

- **Status**: Accepted
- **Context**: Audit of the frozen library (§1) found that PLM's Compatibility Checker (ADR-EAL-001) and EDM's Version-Range Validator (ADR-EAL-007) each implement version-compatibility logic with their own implicit assumptions about semver interpretation, breaking-change classification, and deprecation windows — an unwritten-policy duplication in the same spirit as the graph-logic duplication that motivated EDM.
- **Decision**: Publish a canonical, written Version Compatibility Strategy — Semver Interpretation Rules, Breaking-Change Classification Rules, a Deprecation Window Standard, and a Compatibility Declaration Format — as a referenceable **policy specification, not a runtime component**. **This decision does not modify PLM's or EDM's existing internal compatibility-checking logic.** Future conformance by PLM and/or EDM to this format remains entirely **optional** and requires its own separate, future ADR against ADR-EAL-001 and/or ADR-EAL-007 respectively — not decided, implied, or scheduled by this ADR.
- **Rationale**: The Decision Matrix (§15) shows this is the only option that closes the policy-duplication finding while fully respecting the charter's "no redesign of approved modules" boundary; automated enforcement (policy-as-code) is deliberately deferred as future evolution (§18) rather than attempted before the written policy itself is validated.
- **Consequences**:
  - *Positive*: gives every current and future versioned interface in this library a single, precise reference for what "compatible" and "breaking" mean; establishes a deprecation-window floor applicable wherever deprecation is already referenced (Module Registry, Capability Registry, PLM); fully respects existing frozen decisions.
  - *Negative*: until/unless a conformance ADR is approved for either PLM or EDM, their actual compatibility-result formats remain whatever was originally frozen, so full library-wide format consistency is not immediate.
  - *Neutral*: adoption is voluntary and prospective — no existing consumer of PLM or EDM is affected by this decision.
- **Alternatives rejected**: leave policy implicit, immediately mandate conformance, build policy-as-code immediately, fold into EDM — see §12 and §15.
- **Reversibility**: Fully reversible — as a written specification with no runtime dependency from any existing component under this decision, EVCS can be revised or withdrawn without impact to PLM or EDM.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Semver rules, breaking-change classification, deprecation window standard, and declaration format are specified. |
| **Respect for "no redesign of approved modules"** | Confirmed by design | §1 scope boundary and ADR-EAL-008 explicitly defer any conformance change to PLM/EDM to a separate, future approval, mirroring the EDM precedent. |
| **Applicability validation** | Ready for review | Rules are written generically enough to apply to host APIs, module interfaces, plugin contracts, and capability interfaces without modification. |
| **Open decision requiring your explicit input** | **Confirmed left open, at your direction** | Future conformance by PLM and/or EDM remains optional and requires its own separate ADR. No conformance is scheduled or implied. |
| **Security model maturity** | Ready for design review | Breaking-change security-relevance and expedited-deprecation-for-security-fixes are addressed (§8); no formal threat model performed. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Policy-as-code enforcement** — automating the Breaking-Change Classification Rules and Compatibility Declaration Format checks, once the written policy has been validated in practice, echoing the policy-as-code future evolution already flagged for the Module Registry (§18) and ECF (§18).
- **Conformance ADRs for PLM and/or EDM (explicitly deferred, not committed)** — should you choose to pursue it, each scoped as its own future ADR per §13/§16.
- **Extension to ECF and the Feature Flag Framework** — ECF's config schema versioning and EFF's flag-definition versioning could, in the future, reference the same Breaking-Change Classification Rules rather than each developing an independent notion of what constitutes a breaking configuration or flag-definition change.
- **Capability Registry maturity criteria integration** — using the Breaking-Change Classification Rules to formally define what disqualifies a capability from remaining STABLE (Capability Registry, Appendix B) versus requiring a new major version / new Capability ID.

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-008.
