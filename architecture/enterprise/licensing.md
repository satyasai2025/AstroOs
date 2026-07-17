---
title: Enterprise Licensing
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Licensing

## 1. Problem Statement

Two prior documents already gate access to a capability for different reasons, and it is essential this document adds a third gate without collapsing it into either:

- [Identity & Access](identity-and-access.md) (ADR-EAL-018) answers **"is this caller who they claim, and do they have permission?"** — a security/access-control question.
- The [Feature Flag Framework](feature-flag-framework.md) (ADR-EAL-006) answers **"should this request see this behavior right now, for engineering rollout/experimentation reasons?"** — a delivery/operations question, entirely unrelated to whether anyone has paid for anything.

Neither answers a third, genuinely distinct question: **has this tenant (or identity) been commercially granted access to this capability at all?** A capability can be fully authorized (Identity & Access says yes), fully rolled out (Feature Flags says the behavior is live for everyone), and still correctly denied — because the calling tenant's license doesn't cover it. Conflating this with either prior gate would corrupt both: it would make Identity & Access's permission model carry commercial/billing logic it was never designed for, and it would make Feature Flags — explicitly built for engineering rollout, not entitlement (Feature Flag Framework §1) — do double duty as a licensing mechanism, exactly the scope conflation that document's own boundary section warned against.

Enterprise Licensing (EL) defines the entitlement model — what a license/plan actually grants, in terms of existing Capability IDs — and a second, independent enforcement gate, `checkEntitlement()`, that composes with (never replaces) Identity & Access's `checkPermission()`.

### Reuse map

| Need | Reused from | How |
|---|---|---|
| What a license actually grants access to | [Capability Registry](capability-registry.md) (ADR-EAL-003) | An entitlement is expressed as a set of Capability IDs (or a capability domain prefix, e.g. `cap.ai.*`) a plan covers — not a new capability-naming scheme. |
| Who holds a license | [Multi Tenancy](multi-tenancy.md) (ADR-EAL-021) | A license is scoped to a Tenant (from the Tenant Registry) by default; seat-based licensing scopes to specific identities via Identity & Access's existing tenant-membership attribute. |
| The security/authorization gate this composes with | [Identity & Access](identity-and-access.md) (ADR-EAL-018) | `checkEntitlement()` is a second, independent check alongside the unchanged `checkPermission()` — both must pass; neither subsumes the other. |
| Entitlement-denied failure classification | [Error Handling Framework](error-handling-framework.md) (ADR-EAL-009) | Classifies via EEHF's existing `client_error` class with new `err.licensing.*` codes — no new top-level class. |
| Whether license grant/revoke should be a mandatory compliance record | [Audit Framework](audit-framework.md) (ADR-EAL-019) | This document *recommends* license grant/revoke as a future addition to the Mandatory Audit Event Catalog, via that document's own `designateMandatory()` governance process — it does not add it unilaterally. |
| License-tier parameters (seat counts, usage caps) | [Configuration Framework](configuration-framework.md) (ADR-EAL-005) | Layered exactly per ADR-EAL-005; licensing does not introduce a new configuration layer. |
| External-facing entitlement enforcement | [API Gateway](api-gateway.md) (ADR-EAL-020) | The Gateway's existing pipeline calls `checkEntitlement()` alongside `checkPermission()` for externally-exposed licensed routes — no separate external licensing mechanism. |

**Scope boundary:** this document does not modify any of the twenty-one prior documents, including Identity & Access's authorization model and the Feature Flag Framework's rollout mechanism — it adds a third, orthogonal gate that composes with, and never substitutes for, either.

**Confirmed canonical request evaluation order (at approval):**

```
Authentication → Authorization → Licensing → Feature Flags → Capability Execution
```

Every gated capability invocation evaluates in exactly this order: Identity & Access's `authenticate()` resolves the caller; its `checkPermission()` authorizes them; this document's `checkEntitlement()` confirms commercial licensing; the Feature Flag Framework's `evaluate()` determines whether the (now authenticated, authorized, and licensed) behavior is currently rolled out; only then does the request reach actual capability execution. A failure at any stage short-circuits the pipeline — a request denied at Authorization never reaches Licensing, and a request denied at Licensing never reaches Feature Flags. This ordering is itself now a confirmed, citable architectural fact, not an implementation detail left to each integrator's discretion.

**Reconfirmed at this approval, restating prior ADRs without altering them:**
- **Identity & Access (ADR-EAL-018)** is the authoritative source for authentication, authorization, and identity; no other document — including this one — implements its own identity or permission model. This document's Entitlement Registry tracks *what* is licensed, never *who* the caller is; that remains entirely Identity & Access's domain.
- **API Gateway (ADR-EAL-020)** is the single external entry point and remains strictly a translation and enforcement layer — it does not contain business logic and is not an orchestration engine. Where the Gateway enforces this document's `checkEntitlement()` for external routes (API Gateway §1 reuse map), it does so as one more stage in the evaluation order above, not as custom Gateway-side logic.
- **Multi Tenancy (ADR-EAL-021)**: Tenant is a platform construct — an attribute Identity & Access's existing identity types carry — never a new identity type. This document's licenses are scoped to that same Tenant construct, introducing no second notion of tenancy.

## 2. Goals

| Goal | Description |
|---|---|
| **Entitlements expressed in terms of existing Capability IDs** | A license/plan grants access to a defined set of capabilities, referenced by their existing identity — no parallel capability-naming scheme. |
| **A second, independent enforcement gate** | `checkEntitlement()` is distinct from and composes with `checkPermission()`; a capability invocation must pass both. |
| **Clean boundary from Feature Flags** | Licensing never uses, and is never used by, EFF's rollout mechanism — commercial entitlement and engineering rollout remain entirely separate concerns, even though both can "block" a capability. |
| **A governed license lifecycle** | Trial, Active, Grace Period, Suspended, and Terminated are explicit states, not ad hoc account flags. |
| **Recommend, not mandate, audit inclusion** | License grant/revoke is proposed as a future Mandatory Audit Event Catalog candidate, respecting the Audit Framework's own closed-catalog governance discipline. |

**Non-goals**: EL does not define pricing, billing, or payment processing (those are business/commerce-layer concerns outside this architecture's scope); it does not redefine Identity & Access's permission model or the Feature Flag Framework's rollout mechanism; and it does not itself designate license events as mandatory-audit-class — that remains the Audit Framework's own governance decision.

## 3. Architecture

```
   ┌───────────────────────────┐
   │   License/Entitlement Model    │  ← new: plans/tiers, each granting
   │   (new)                        │    a set of existing Capability IDs
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Entitlement Registry (new)    │◄──────┤ Multi Tenancy                │
   │                                 │        │ (Tenant Registry, unchanged)  │
   └─────────────┬─────────────┘        └───────────────────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Entitlement Enforcement       │◄──────┤ Identity & Access             │
   │   (new — checkEntitlement(),     │        │ (checkPermission(), unchanged)│
   │    composes with, does not        │        │ — both gates must pass        │
   │    replace, checkPermission())     │        └───────────────────────────┘
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐
   │   License Lifecycle             │  ← new: Trial → Active →
   │   Tracker (new)                 │    Grace Period → Suspended →
   │                                 │    Terminated
   └───────────────────────────┘

   Explicitly NOT connected: the Feature Flag Framework's rollout
   mechanism — entitlement and rollout remain independent gates.
```

## 4. Components

- **License/Entitlement Model** *(new)* — defines a plan/tier as a named set of Capability IDs (or domain prefixes) it grants, plus any quantitative limits (seat count, usage cap) associated with that plan.
- **Entitlement Registry** *(new)* — records which Tenant (or, for seat-based plans, which specific identity within a tenant) holds which license, and its current lifecycle state.
- **Entitlement Enforcement** *(new)* — the `checkEntitlement()` gate, checked independently of and alongside Identity & Access's unchanged `checkPermission()`; a capability invocation proceeds only if both gates pass.
- **License Lifecycle Tracker** *(new)* — governs a license's progression: Trial → Active → Grace Period (e.g., after a renewal lapse) → Suspended → Terminated, a distinct lifecycle from the Tenant's own lifecycle (Multi Tenancy §6) and from any capability's maturity lifecycle (Capability Registry, Appendix B).

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `definePlan(planId, grantedCapabilityIds, limits)` | Plan owner → License/Entitlement Model | Declares a named plan and what it grants. |
| `grantLicense(tenantOrIdentityRef, planId)` | Governance/commercial action → Entitlement Registry | Grants a license, entering the Trial or Active lifecycle state. |
| `checkEntitlement(identityOrTenantRef, capabilityId)` | Any capability invocation path (e.g., the standard chain, or the API Gateway) → Entitlement Enforcement | Answers "is this caller's tenant/identity entitled to this capability" — independent of, and checked alongside, `checkPermission()`. |
| `setLicenseLifecycleState(licenseRef, state)` | Governance/commercial action → License Lifecycle Tracker | Advances or changes a license's lifecycle state. |
| `getEntitlements(tenantOrIdentityRef)` | Operator/tooling → Entitlement Registry | Read-only query of what a tenant/identity is currently entitled to. |

## 6. Data Flow

1. A plan is defined via `definePlan()`, naming the Capability IDs (or domain prefixes) it grants and any quantitative limits.
2. A license is granted via `grantLicense()`, associating a Tenant (typical case, per Multi Tenancy) or a specific identity (seat-based case) with a plan, entering the License Lifecycle Tracker's Trial or Active state.
3. When a capability is invoked — through the standard chain or via the API Gateway — the confirmed canonical order applies: Identity & Access's `authenticate()`, then its `checkPermission()`, then this document's `checkEntitlement()`, then the Feature Flag Framework's `evaluate()`, then capability execution. Each stage short-circuits the pipeline on failure — a caller can be fully authorized and still denied for lack of entitlement, but never reaches the Licensing stage at all without first passing Authentication and Authorization.
4. A failed entitlement check classifies via EEHF's existing taxonomy with an `err.licensing.*` code, distinct from a permission-denied `err.identity.*` code (Identity & Access §6) — callers can distinguish "not authorized" from "not entitled."
5. The License Lifecycle Tracker governs transitions — e.g., a lapsed renewal moves a license from Active to Grace Period (where `checkEntitlement()` may still pass, per the plan's grace-period policy) and eventually to Suspended (where it does not).
6. License grant, revoke, and lifecycle-state-change events are candidates this document recommends for the Audit Framework's Mandatory Audit Event Catalog — a recommendation for that document's own governance process (`designateMandatory()`, Audit Framework §5), not an automatic inclusion.

## 7. Design Patterns

- **A third, independent gate, not a merged one** — directly continuing this library's discipline of keeping orthogonal concerns separate even when they superficially resemble each other (EFF vs. ECF, EEB vs. EOA, Scheduling vs. the Workflow Engine); entitlement, authorization, and rollout are three different reasons a capability might be blocked, each with its own gate.
- **Entitlement expressed against existing identity, never a new capability-naming scheme** — mirrors the Capability Registry's own discipline of resolving rather than re-minting identity (Capability Registry §1).
- **A named lifecycle, joining an established family** — License Lifecycle (Trial → Active → Grace Period → Suspended → Terminated) follows the same pattern as PLM's activation lifecycle, the Feature Flag's rollout lifecycle, the Capability Registry's maturity lifecycle, and the Research Platform's findings lifecycle — each named, distinct, and answering a different question about a different kind of thing.
- **Recommend into another document's governance process, don't reach into it** — proposing (not forcing) an addition to the Audit Framework's Mandatory Audit Event Catalog respects that document's own closed-catalog discipline (Audit Framework §11) rather than treating it as automatically extensible from outside.

## 8. Security Considerations

*(Citing the Security Principles Catalog directly, per ESA's discipline.)*

- **Principle: Fail-Closed Validation** (ESA catalog) applies to `checkEntitlement()` exactly as it does to `checkPermission()` — an ambiguous or unresolvable entitlement check denies access, never defaults to allow.
- **Principle: Least-Privilege** (ESA catalog) applies to plan design — a plan should grant only the Capability IDs it's actually meant to cover, not a broad default.
- **Entitlement state is commercially sensitive** — the Entitlement Registry's data (what a tenant has or hasn't licensed) has business-sensitivity implications distinct from, but analogous to, the access-scoping already applied to cost/usage data in the AI Platform's Cost & Usage Meter (AI Platform §8).
- **License Lifecycle transitions (especially Suspended/Terminated) are high-impact** — should be gated by a specific, narrowly-granted Identity & Access permission, consistent with how Multi Tenancy gates its own lifecycle transitions (Multi Tenancy §8).

## 9. Scalability

- **`checkEntitlement()` sits on the same request path as `checkPermission()`** — it must meet the same request-path latency expectations (Identity & Access §9), likely via a similarly cached verified-entitlement model with explicit invalidation on license change.
- **Entitlement Registry is read-heavy relative to grant/revoke frequency** — the now-familiar read/write asymmetry established throughout this library.
- **Plan definitions change far less often than entitlement checks occur** — the License/Entitlement Model's own read path (resolving what a plan grants) is a natural caching candidate, similar to EFF's evaluation cache for flag definitions (Feature Flag Framework §9).

## 10. Best Practices

- Always express a plan's grants in terms of existing Capability IDs — never introduce a second identifier scheme for "licensed things."
- Check `checkEntitlement()` and `checkPermission()` independently and require both to pass — never let one substitute for the other, even as an implementation shortcut.
- Keep Feature Flag rollout and license entitlement decisions completely separate in code and in operational reasoning — a capability can be flag-enabled but unlicensed for a tenant, or licensed but not yet flag-rolled-out; these are independent facts.
- Propose, rather than assume, license events' inclusion in the Mandatory Audit Event Catalog — respect the Audit Framework's own governance process for that decision.

## 11. Common Pitfalls

- **Using Feature Flags to enforce licensing** — the single most tempting and most damaging conflation this document exists to prevent; a flag rollout percentage is not a commercial entitlement boundary, and using one for the other breaks the moment a flag reaches 100% rollout while a tenant's license still doesn't cover the capability.
- **Folding entitlement checks into Identity & Access's permission model** — would force a security/authorization system to carry commercial logic it wasn't designed for, and would make "why was this denied" ambiguous between a security reason and a billing reason.
- **Treating the Entitlement Registry's grant/revoke history as automatically mandatory-audit-class** — bypasses the Audit Framework's own deliberate governance process for catalog additions (Audit Framework §11); this document recommends, it does not decide.
- **Defaulting new plans to broad capability grants "to be safe for the customer"** — inverts least-privilege and risks entitlement creep that's difficult to walk back once customers expect the broader access.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **Reuse Feature Flags for licensing** | Gate licensed capabilities using EFF's existing targeting/rollout mechanism instead of a new entitlement gate. | Directly conflates two conceptually different questions (commercial entitlement vs. engineering rollout) that EFF's own boundary section (EFF §1) was explicit about keeping separate from ECF; doing the same conflation here with licensing would repeat that exact mistake in a new direction. |
| **Fold entitlement into Identity & Access's permission model** | Model a license as just another permission grant. | Would force a security/authorization system to carry commercial/billing semantics, and would make an entitlement-denied response indistinguishable from an authorization-denied one without additional structure — the two-gate model keeps both concerns, and their respective diagnostics, cleanly separated. |
| **No licensing model; enforce entitlement ad hoc per capability** | Let each capability implement its own commercial-access check. | Fails consistency and auditability outright; the exact fragmentation problem this library has repeatedly closed (e.g., the original motivation for the Module Registry, EDM, and EVCS). |
| **Automatically designate all license events as mandatory audit records** | Have this document unilaterally add itself to the Audit Framework's catalog. | Bypasses that document's own explicit, deliberate governance process for catalog changes (Audit Framework §11, §13); this document instead recommends the addition as a future, separately-approved decision (§18). |

## 13. Migration Strategy

1. **Define the License/Entitlement Model and initial plans**, expressed entirely in terms of existing Capability IDs.
2. **Stand up the Entitlement Registry and License Lifecycle Tracker**, granting licenses for existing tenants under their current commercial arrangements.
3. **Wire `checkEntitlement()` alongside `checkPermission()` for one capability first**, validating that both gates compose correctly (denial from either blocks the call) before wiring the remainder.
4. **Propose license grant/revoke for the Mandatory Audit Event Catalog** through the Audit Framework's own governance process, rather than assuming inclusion.
5. **Incrementally wire remaining licensed capabilities**, prioritizing the highest-commercial-risk ones first.

## 14. Success Criteria

- Every plan's grants are expressed as existing Capability IDs; zero new capability-identification schemes introduced.
- 100% of licensed capability invocations require both `checkEntitlement()` and `checkPermission()` to pass independently.
- Zero instances of Feature Flags being used as a licensing enforcement mechanism, or vice versa.
- License grant/revoke is formally proposed to the Audit Framework's governance process; the outcome (accepted or deferred) is recorded regardless of which way it goes.
- An entitlement-denied response is distinguishable from a permission-denied response via distinct EEHF-classified codes (`err.licensing.*` vs. `err.identity.*`).

## 15. Decision Matrix

| Criterion (weight) | Independent entitlement gate, composing with checkPermission() (recommended) | Reuse Feature Flags for licensing | Fold into Identity & Access | No licensing model, ad hoc per capability | Auto-designate license events as mandatory audit |
|---|---|---|---|---|---|
| Clean boundary from Feature Flags (High) | 5 | 1 | 4 | 4 | 4 |
| Clean boundary from Identity & Access (High) | 5 | 4 | 1 | 4 | 4 |
| Distinguishable entitlement-vs-permission diagnostics (High) | 5 | 2 | 1 | 2 | 4 |
| Respects Audit Framework's own governance process (Medium) | 5 | 4 | 4 | 4 | 1 |
| Consistency/auditability of entitlement decisions (Medium) | 5 | 2 | 3 | 1 | 4 |
| Implementation/governance overhead (Medium, lower = better fit) | 3 | 4 | 3 | 5 | 3 |
| **Weighted outcome** | **Best overall fit** | Fails EFF-boundary goal | Fails IA-boundary goal | Fails consistency goal | Bypasses Audit Framework governance |

**Conclusion**: an independent `checkEntitlement()` gate — composing with, never replacing, Identity & Access's `checkPermission()`, and kept entirely separate from Feature Flags' rollout mechanism — is recommended. It is the only option that preserves all three documents' distinct boundaries while giving licensing a real, auditable enforcement point.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-022: Enterprise Licensing as an Independent Entitlement Gate, Composing With Identity & Access and Distinct From Feature Flags**

- **Status**: Accepted
- **Context**: No prior document defines commercial entitlement; Identity & Access answers authorization, and the Feature Flag Framework answers engineering rollout — neither answers, nor should be conflated with, "has this tenant been commercially granted access to this capability."
- **Decision**: Introduce a License/Entitlement Model (plans expressed as existing Capability IDs), an Entitlement Registry (scoped via Multi Tenancy's Tenant Registry or Identity & Access's identity types for seat-based plans), an independent `checkEntitlement()` gate composing with the unchanged `checkPermission()`, and a License Lifecycle Tracker. Entitlement-denied failures classify via EEHF with new `err.licensing.*` codes. License grant/revoke is *recommended*, not automatically designated, for the Audit Framework's Mandatory Audit Event Catalog. **Confirmed canonical request evaluation order: Authentication → Authorization → Licensing → Feature Flags → Capability Execution**, with each stage short-circuiting on failure. **No modification to any of the twenty-one prior documents.**
- **Rationale**: The Decision Matrix (§15) shows this is the only option preserving the Feature Flag Framework's and Identity & Access's own established boundaries while giving commercial entitlement a real, distinct, auditable enforcement point — reusing Capability IDs, Tenant scoping, EEHF classification, and the Audit Framework's governance process rather than duplicating or conflating any of them.
- **Consequences**:
  - *Positive*: entitlement, authorization, and rollout remain three cleanly separated concerns with three distinct diagnostics; plans are expressed in terms of existing, stable Capability IDs; the Audit Framework's own governance discipline is respected rather than bypassed; the confirmed evaluation order gives every future integration a single, unambiguous pipeline sequence rather than each caller composing the gates in its own order.
  - *Negative*: capability invocation paths must now check three independent gates (authZ, licensing, flags) in a fixed sequence instead of one, a real (if narrow) integration cost.
  - *Neutral*: pricing, billing, and payment processing remain explicitly out of scope — this document defines the entitlement/enforcement architecture only.
- **Alternatives rejected**: reusing Feature Flags, folding into Identity & Access, no licensing model, auto-designating audit inclusion — see §12 and §15.
- **Reversibility**: Fully reversible — the new components can be decommissioned without affecting Identity & Access, the Feature Flag Framework, or any other prior document; capabilities would simply become universally accessible to any authorized caller if entitlement enforcement were removed.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | License/Entitlement Model, Entitlement Registry, Entitlement Enforcement, and License Lifecycle Tracker are specified at architecture level. |
| **Boundary with Feature Flags** | Confirmed explicit | §1, §7, §11 directly address why entitlement and rollout remain separate gates. |
| **Boundary with Identity & Access** | Confirmed explicit | `checkEntitlement()` composes with, never replaces, `checkPermission()`. |
| **Respect for Audit Framework's governance** | Confirmed | License audit inclusion is a recommendation (§18), not a unilateral designation. |
| **Technology-agnostic validation** | Ready | No binding to a specific billing/commerce platform. |
| **Pricing/billing scope** | Explicitly out of scope | Named as a non-goal (§2); this document defines entitlement architecture, not commerce. |
| **Canonical evaluation order** | Confirmed at approval | Authentication → Authorization → Licensing → Feature Flags → Capability Execution, short-circuiting on failure at any stage. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Propose license grant/revoke to the Audit Framework's Mandatory Audit Event Catalog** — a concrete, near-term follow-up through that document's own `designateMandatory()` governance process (Audit Framework §5, §13), not assumed here.
- **Usage-based entitlement limits** — extending beyond simple capability-grant lists toward quantitative usage caps (e.g., call volume, integrating with the AI Platform's Cost & Usage Meter for AI-backed capabilities specifically), as a refinement of the License/Entitlement Model.
- **Grace-period and dunning policy detail** — formalizing the specific behavior during the Grace Period lifecycle state (e.g., degraded vs. full access) as implementation-phase detail building on the stated lifecycle.
- **Marketplace integration** — a future connection to a not-yet-drafted Marketplace document (per ROADMAP.md's ENTERPRISE phase), where a customer-facing plan-selection/purchase flow could originate a `grantLicense()` call, without this document needing to anticipate that flow's own design.

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-022.
