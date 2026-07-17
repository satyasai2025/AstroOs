---
title: Enterprise Identity & Access
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Identity & Access

## 1. Problem Statement

**Audit finding across the library:** nearly every one of the seventeen prior documents refers to an authenticated identity, an authorized caller, an owner, or a permission check — and not one of them defines what that identity actually *is*, how it is *verified*, or how a permission decision is actually *made*. A sample of load-bearing references left unresolved until now:

- PLM's Capability/Security Gate "mediates access to host resources" and enforces capability grants "with an approval step" (PLM §4, §8) — but never defines what a plugin's own verifiable identity is, or who/what is doing the approving.
- The Module Registry requires that "only a module's recorded owner... may submit updates" (Module Registry §8) — but never defines how an owner proves they are the owner.
- ECF requires "different authorization requirements per layer" for configuration writes (ECF §8) — without a permission model to check against.
- The Event Bus requires the Broker to "attribute a published event to an authenticated provider identity" (Event Bus §8) — without defining how that authentication actually happens.
- Scheduling requires `pauseSchedule()`/`resumeSchedule()` to be "authorized distinctly from routine schedule definition" (Scheduling §8) — again assuming, not defining, an authorization mechanism.
- [Enterprise Security Architecture](security-architecture.md) (ESA, ADR-EAL-017) explicitly named this exact gap and deferred it here rather than partially addressing it (ESA §1, §12).

The Enterprise Identity & Access document (EIA) is the mechanism all of these already-written requirements were implicitly assuming: a shared identity model (what kinds of callers exist), an authentication mechanism (how each proves itself), and an authorization model (how a permission decision actually gets made) — that every prior document's access-control language now resolves to, without any of them needing to be rewritten.

### Reuse map

| Need | Reused from | How |
|---|---|---|
| Naming the recurring principles this document must satisfy | [Security Architecture](security-architecture.md) (ADR-EAL-017) | Cites the Security Principles Catalog directly (least-privilege, secrets-by-reference, fail-closed, audit-trail integrity) rather than restating them. |
| Provider identity anchor for modules/plugins | [Module Registry](module-registry.md) (ADR-EAL-002) + [Plugin Lifecycle Management](plugin-lifecycle-management.md) (ADR-EAL-001) | A Provider Identity in this document *is* the module ID or plugin ID already assigned by those registries — EIA does not mint a second identity for the same provider. |
| Integrity/signature verification anchor | [Plugin Lifecycle Management](plugin-lifecycle-management.md) §8 | PLM's existing artifact signature/checksum requirement is the basis for a provider's credential material; this document does not redefine PLM's integrity verification, it completes what identity that verification is *for*. |
| Credential storage (API keys, signing keys) | [Configuration Framework](configuration-framework.md) (ADR-EAL-005) | Sourced via ECF's existing secrets-by-reference mechanism, never inline. |
| Auth-failure classification | [Error Handling Framework](error-handling-framework.md) (ADR-EAL-009) | An authentication or authorization failure classifies into EEHF's existing `client_error` class with new `err.identity.*` codes — no new top-level class. |
| Auth/permission event audit trail | [Observability Architecture](observability-architecture.md) (ADR-EAL-010) | Authentication and permission-grant events are wrapped in EOA's Common Event Envelope for query, exactly as any other emitter's output. |
| Gradual rollout of a new authentication mechanism or permission model change | [Feature Flag Framework](feature-flag-framework.md) (ADR-EAL-006) | Migrating a subset of callers to a revised auth mechanism reuses EFF's rollout/kill-switch mechanism. |
| Permission-model versioning | [Version Compatibility Strategy](version-compatibility-strategy.md) (ADR-EAL-008) | A change to what a role/permission means is classified via EVCS before being considered a compatible evolution. |

**Scope boundary:** this document does not modify any of the seventeen prior documents. It defines the identity/authentication/authorization mechanism every one of their existing access-control references already assumed, without redefining any of those documents' own requirements.

## 2. Goals

| Goal | Description |
|---|---|
| **One identity model for every caller type** | Provider Identity (modules/plugins), Human Identity (end users, operators), and System Identity (internal components like the Broker or Timer/Trigger Engine acting autonomously) are each precisely defined, not implicitly assumed per document. |
| **A concrete authentication mechanism per identity type** | How each identity type proves itself — building on PLM's existing signature/integrity model for providers, credential-based verification for humans, and a service-identity mechanism for internal system components. |
| **A concrete authorization model** | Roles/permissions that every prior document's access-control requirement (Module Registry ownership, ECF layer-write governance, EEB publisher verification, Scheduling pause/resume, etc.) can be checked against by name. |
| **Completes, never replaces, existing enforcement points** | PLM's Security Gate, the Module Registry's ownership check, and every other document's own access-control logic remain exactly as specified — this document supplies the identity/permission substrate they check against. |
| **Full reuse of Foundation/Platform mechanisms for everything except identity/auth itself** | No parallel secrets, error-classification, versioning, or audit mechanism specific to identity. |

**Non-goals**: EIA does not replace or redesign PLM's Capability/Security Gate, the Module Registry's ownership model, or any other document's own access-control point — it defines what those checks resolve against. It does not mandate a specific vendor SSO/OAuth implementation (the mechanism is architecture-level, not a product choice). It does not redefine the Security Principles Catalog (ESA's role, cited not restated).

## 3. Architecture

```
   ┌───────────────────────────┐
   │   Identity Model               │  ← new: Provider / Human / System
   │   (new)                        │    identity types, precisely defined
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Authentication Mechanism      │◄──────┤ Module Registry / PLM          │
   │   (new)                        │        │ (provider ID + integrity        │
   │                                 │        │  verification, unchanged)       │
   └─────────────┬─────────────┘        └───────────────────────────┘
                 │ verified identity
   ┌─────────────▼─────────────┐
   │   Authorization Model /        │  ← new: roles/permissions that
   │   Permission Grant Registry    │    every prior document's access-
   │   (new)                        │    control requirement checks against
   └─────────────┬─────────────┘
                 │ permission decision
   ┌─────────────▼─────────────┐
   │   Existing enforcement points   │  ← PLM's Security Gate, Module
   │   in all 17 prior documents     │    Registry's ownership check, ECF's
   │   (unchanged — now backed by     │    layer governance, EEB publisher
   │    a real identity/permission    │    verification, Scheduling pause/
   │    substrate instead of an      │    resume authorization, etc.
   │    assumed one)                 │
   └───────────────────────────┘
```

## 4. Components

- **Identity Model** *(new)* — precisely defines three caller types: **Provider Identity** (a module or plugin, anchored to the ID already assigned by the Module Registry or PLM — not a second identity), **Human Identity** (an end user or operator, verified via credential-based authentication), and **System Identity** (an internal component, such as the Event Bus's Broker or the Timer/Trigger Engine, acting on its own authority rather than on behalf of a specific human or provider).
- **Authentication Mechanism** *(new)* — how each identity type proves itself: a Provider Identity's authentication builds directly on PLM's existing artifact signature/integrity verification (PLM §8) rather than introducing a second credential scheme for the same provider; a Human Identity authenticates via verifiable credentials; a System Identity authenticates via a service-level credential scoped to its specific internal role.
- **Authorization Model / Permission Grant Registry** *(new)* — the roles/permissions substrate that every prior document's already-stated access-control requirement checks against: e.g., "module owner" (Module Registry §8), "per-layer config writer" (ECF §8), "schedule pause/resume operator" (Scheduling §8), "recipient preference change" (Notification Framework §8) are each expressed as a named permission here, resolved against a verified identity from the Authentication Mechanism.

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `authenticate(credential)` | Any caller → Authentication Mechanism | Verifies a presented credential and returns a verified identity (Provider/Human/System), or a classified failure. |
| `checkPermission(identity, permission, resourceRef)` | Any existing enforcement point (PLM's Security Gate, Module Registry's ownership check, etc.) → Authorization Model | Answers "may this verified identity perform this named permission against this resource" — the call every prior document's access-control requirement now has a concrete mechanism to make. |
| `grantPermission(identity, permission, resourceRef, grantedBy)` | Governance action → Permission Grant Registry | Records a permission grant, attributable and auditable. |
| `revokePermission(identity, permission, resourceRef)` | Governance action → Permission Grant Registry | Removes a previously granted permission. |

## 6. Data Flow

1. A caller (provider, human, or system component) presents a credential; `authenticate()` verifies it against the Authentication Mechanism appropriate to that identity type — for a Provider Identity, this includes checking the artifact signature/integrity already required by PLM (PLM §8), not a separate check.
2. On successful authentication, a verified identity is established for the remainder of the call/session.
3. When any existing enforcement point elsewhere in this library needs to answer an access-control question it already stated but didn't mechanize — the Module Registry's ownership check, ECF's per-layer write governance, PLM's Security Gate's capability-grant approval, EEB's publisher verification, ENF's preference-change attribution, Scheduling's pause/resume authorization — it calls `checkPermission()` against the verified identity and the specific named permission that document already required.
4. A failed authentication or authorization attempt classifies via EEHF's existing `client_error` class with a new `err.identity.*` code.
5. Every authentication event and permission grant/revoke is wrapped in EOA's Common Event Envelope for audit-trail query, consistent with the audit-integrity principle cited from the Security Principles Catalog (ESA).

## 7. Design Patterns

- **Identity as an anchor, not a second registry** — a Provider Identity is the Module Registry's or PLM's existing ID, not a new identifier; this mirrors the Capability Registry's own discipline of referencing rather than re-minting identity (Capability Registry §1).
- **Authentication/authorization as a substrate every existing enforcement point calls into** — rather than replacing PLM's Security Gate, the Module Registry's ownership check, or any other document's own access-control logic, this document supplies the concrete mechanism those already-specified checks resolve against, the same "complete, don't replace" discipline used when EVCS supplied policy for PLM's and EDM's already-existing compatibility checkers (EVCS §1).
- **Named, citable permissions** — mirrors the Security Principles Catalog's own citation discipline (ESA §4): a permission like "module owner" or "schedule pause/resume operator" is named once here and referenced by the document that originally required it, rather than each document inventing its own ad hoc notion of "authorized."

## 8. Security Considerations

*(Consistent with ESA's citation discipline — this section names the applicable catalog principles rather than restating them.)*

- **Principle: Least-Privilege** (ESA catalog) applies directly to the Authorization Model's permission grants — a granted permission should be the narrowest one satisfying the actual need, consistent with PLM's own least-privilege capability-grant model (PLM §2, §8).
- **Principle: Secrets-by-Reference** (ESA catalog) applies to all credential material used in the Authentication Mechanism — sourced via ECF, never inline.
- **Principle: Fail-Closed Validation** (ESA catalog) applies to `checkPermission()` — an ambiguous or unresolvable permission check must deny, not default-allow.
- **Principle: Audit-Trail Integrity** (ESA catalog) applies to the Permission Grant Registry's grant/revoke history — append-only, attributable, tamper-evident.
- **Provider Identity must not be spoofable independent of PLM's existing integrity check** — building authentication on top of PLM's already-required artifact signature (rather than a separate, weaker provider-credential scheme) is a deliberate reuse of an already-verified integrity anchor, not just a convenience.

## 9. Scalability

- **`authenticate()` and `checkPermission()` sit on or near the request path for many prior documents' own operations** (a capability invocation, a config write, a schedule pause) — both must meet request-path latency expectations comparable to ESR's and EFF's own evaluation-cache disciplines (ESR §9, EFF §9), likely via a cached verified-identity/permission-decision model rather than a full check on every call.
- **Permission Grant Registry is read-heavy relative to grant/revoke frequency** — the now-familiar read/write asymmetry established throughout this library (Module Registry §9, Capability Registry §9, ECF §9).
- **Authentication mechanism scaling depends on identity type** — Provider Identity authentication piggybacks on PLM's existing artifact-verification cadence (infrequent, at registration/activation); Human Identity authentication is comparatively higher-frequency and should be architected accordingly.

## 10. Best Practices

- Anchor every Provider Identity to its existing Module Registry/PLM ID — never mint a second identifier for the same provider.
- Name every permission precisely and reuse the exact name a prior document already used when describing its own access-control requirement (e.g., "module owner," not a rephrased equivalent).
- Cache verified identity/permission decisions where the request-path latency goals of the calling document (e.g., ESR, EFF) require it, with an explicit invalidation path on revoke.
- Treat any authentication/authorization mechanism change as requiring EVCS classification before assuming existing callers remain compatible.

## 11. Common Pitfalls

- **Treating this document as redefining PLM's Security Gate or the Module Registry's ownership check** — the single most important pitfall to avoid; this document supplies the identity/permission substrate those existing, unmodified enforcement points check against, exactly as EVCS supplied policy without redefining PLM's or EDM's own compatibility-checking components (EVCS §11).
- **Minting a second identifier for a provider already known to the Module Registry or PLM** — fragments identity exactly as this library has consistently avoided since the Capability Registry's own identity-reuse discipline (Capability Registry §1).
- **Defaulting to allow on an ambiguous permission check** — violates the fail-closed principle cited from the Security Principles Catalog (§8).
- **Building a separate provider-credential scheme instead of reusing PLM's existing artifact signature** — duplicates an already-solved integrity-verification problem.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **Leave identity/auth implicit, as it has been across all seventeen prior documents** | Continue assuming "authenticated" and "authorized" without a defined mechanism. | This is precisely the unresolved gap identified in §1 and explicitly deferred by ESA (ADR-EAL-017); every prior document's access-control language remains unmechanized without this document. |
| **Redefine PLM's Security Gate or the Module Registry's ownership check directly** | Rewrite those documents' existing enforcement points instead of supplying a shared substrate. | Violates "no redesign of approved modules"; this document instead completes what those already-frozen checks resolve against, without touching their specifications. |
| **A separate identity scheme per document (each document defines its own auth)** | Let each of the seventeen documents independently define how its own "authorized caller" is verified. | Repeats the exact duplicated-principle problem ESA was built to consolidate (ESA §1), at an even more foundational layer; a single shared identity/permission substrate is directly analogous to why EDM consolidated two independent dependency graphs. |
| **Mint a new identity for providers instead of anchoring to Module Registry/PLM IDs** | Give modules/plugins a second, EIA-specific identifier. | Fragments identity unnecessarily; the Capability Registry, EDM, and every other document already reference module/plugin IDs directly — a second identifier would require translation everywhere those IDs are already used. |

## 13. Migration Strategy

1. **Define the Identity Model and anchor Provider Identity to existing Module Registry/PLM IDs** — no new identifier introduced.
2. **Stand up the Authentication Mechanism, building Provider Identity verification directly on PLM's existing artifact-signature requirement** rather than a new credential scheme.
3. **Stand up the Authorization Model / Permission Grant Registry, naming permissions using the exact language each prior document already used** (module owner, per-layer config writer, schedule pause/resume operator, etc.).
4. **Wire one existing enforcement point first** (e.g., the Module Registry's ownership check) to call `checkPermission()` against the new substrate, validating the integration before wiring the remaining sixteen documents' access-control points.
5. **Incrementally wire the remaining documents' enforcement points**, each independently, since none require simultaneous cutover.

## 14. Success Criteria

- Every named permission referenced implicitly across the seventeen prior documents (module owner, per-layer config writer, publisher identity, schedule pause/resume operator, recipient preference change, etc.) has a corresponding, precisely-named entry in the Authorization Model.
- Zero new provider identifiers introduced — 100% of Provider Identities resolve to an existing Module Registry or PLM ID.
- `checkPermission()` defaults to deny on any ambiguous or unresolvable check, verified by test.
- Zero modifications to any of the seventeen prior documents' own specifications as a result of this document's adoption.
- At least one existing enforcement point (e.g., Module Registry ownership transfer) is demonstrated calling `checkPermission()` against the new substrate end-to-end.

## 15. Decision Matrix

| Criterion (weight) | Shared identity/authZ substrate, completes existing enforcement points (recommended) | Leave implicit (status quo) | Redefine existing enforcement points directly | Per-document independent auth schemes | Mint a new provider identifier |
|---|---|---|---|---|---|
| Closes the "no defined identity/auth mechanism" finding (High) | 5 | 1 | 4 | 3 | 4 |
| Respects "no redesign of approved modules" (High) | 5 | 5 | 1 | 4 | 3 |
| Consistency across all seventeen prior documents (High) | 5 | 1 | 3 | 1 | 3 |
| Reuse of PLM's existing integrity verification (Medium) | 5 | 3 | 3 | 2 | 1 |
| Avoids identity fragmentation (Medium) | 5 | 4 | 4 | 2 | 1 |
| Implementation/governance overhead (Medium, lower = better fit) | 3 | 5 | 2 | 3 | 3 |
| **Weighted outcome** | **Best overall fit** | Fails core goal | Fails charter boundary | Fails consistency goal | Fails identity-reuse goal |

**Conclusion**: a shared identity model, authentication mechanism, and authorization substrate that every prior document's already-stated access-control requirement can check against — without redefining any of those requirements or their enforcement points — is recommended.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-018: Enterprise Identity & Access as a Shared Authentication/Authorization Substrate Completing Existing Enforcement Points**

- **Status**: Accepted
- **Context**: Seventeen prior documents each reference an authenticated identity, authorized caller, or permission check without any of them defining the actual mechanism; ESA (ADR-EAL-017) explicitly named and deferred this gap.
- **Decision**: Define an Identity Model (Provider/Human/System), an Authentication Mechanism (Provider Identity built on PLM's existing signature verification; credential-based for Human; service-credential for System), and an Authorization Model / Permission Grant Registry naming every permission already implicitly required across the prior seventeen documents. **This decision does not modify PLM's Security Gate, the Module Registry's ownership check, or any other prior document's own enforcement logic** — it supplies the substrate those checks resolve against.
- **Rationale**: The Decision Matrix (§15) shows this is the only option closing the identity/auth gap while fully respecting "no redesign of approved modules" and avoiding identity fragmentation, by anchoring Provider Identity to already-existing Module Registry/PLM IDs rather than minting a new one.
- **Consequences**:
  - *Positive*: every prior document's previously-unmechanized access-control language now has a concrete, consistent, citable mechanism; PLM's existing integrity verification is reused rather than duplicated; permission names are consistent across the library instead of each document inventing its own.
  - *Negative*: seventeen existing enforcement points must each be incrementally wired to call into the new substrate — a real, if independently-schedulable, integration effort.
  - *Neutral*: this document does not itself mandate a specific vendor SSO/OAuth product — that remains an implementation-phase decision within the architecture defined here.
- **Alternatives rejected**: leave implicit, redefine existing enforcement points, per-document independent schemes, mint a new provider identifier — see §12 and §15.
- **Reversibility**: Moderate reversal cost — once enforcement points are wired to `checkPermission()`, reverting would require restoring each document's prior ad hoc (undefined) behavior; comparable in cost profile to reversing ESR or PLM adoption rather than to EDM's low-cost case, given how many prior documents' access-control language now depends on this substrate.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Identity Model, Authentication Mechanism, and Authorization Model are specified at architecture level. |
| **Fills the gap ESA deferred** | Confirmed | Directly addresses the authentication/authorization mechanism ESA (§1, §12) explicitly named and deferred. |
| **Respect for "no redesign of approved modules"** | Confirmed by design | No prior document's enforcement logic is modified; this substrate is called into, not substituted for, existing checks. |
| **Provider identity anchoring** | Confirmed | No new provider identifier; anchors to existing Module Registry/PLM IDs. |
| **Technology-agnostic validation** | Ready | No binding to a specific SSO/OAuth vendor or credential storage technology. |
| **Threat-model application** | Recommended as first candidate | Per ESA §18's future evolution, this document — given its direct privilege implications — is a natural first candidate for the Threat Modeling Methodology's initial application. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Apply ESA's Threat Modeling Methodology to this document first** — given its direct privilege implications, a natural priority candidate over the other sixteen (ESA §18).
- **Fine-grained, attribute-based authorization (ABAC)** — extending beyond named role-style permissions toward attribute-based rules, if the coarse-grained model proves insufficient for a future document's needs.
- **Federated/external identity provider integration** — a future extension for Human Identity authentication to integrate with an external identity provider, without changing the Provider/System Identity model.
- **Incremental wiring completion tracking** — a visible backlog (mirroring ESA's own "threat model not yet performed" tracking, ESA §13) of which of the seventeen prior documents' enforcement points have actually been wired to call `checkPermission()`, since §13's migration strategy is deliberately incremental rather than a single cutover.

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-018.
