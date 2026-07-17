---
title: Enterprise Multi Tenancy
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Multi Tenancy

## 1. Problem Statement

This is the first ENTERPRISE-phase document, and the audit that opens it finds the same pattern already seen with EDM, EVCS, ESA, and Identity & Access: a concept referenced everywhere, defined nowhere. **"Tenant" already appears as a load-bearing concept in multiple frozen documents:**

- [Configuration Framework](configuration-framework.md) (ECF, ADR-EAL-005) has "Tenant" as an explicit layer in its precedence hierarchy — Platform Default → Environment → **Tenant** → Instance — without ever defining what a tenant *is*, only that config can be scoped to one.
- The [AI Platform Architecture](ai-platform-architecture.md)'s Cost & Usage Meter attributes usage "to the originating capability (and tenant, where applicable per ECF's tenant layer)" (AI Platform §4) — again assuming, not defining, tenant identity.
- [Identity & Access](identity-and-access.md) defines Human and Provider identities but never states whether or how an identity relates to a tenant boundary.
- The [Audit Framework](audit-framework.md)'s compliance queries ("every action by identity X") have an obvious tenant-scoping dimension that document never addresses, since Multi Tenancy did not yet exist when it was written.

Enterprise Multi Tenancy (EMT) is the missing definition: what a tenant actually is, how identities relate to one, what isolation guarantee tenants get from each other, which capabilities are tenant-scoped versus platform-global, and how a tenant's lifecycle (onboarding through offboarding, including data deletion) works — completing what ECF's tenant layer, the AI Platform's cost attribution, and every other tenant-adjacent reference have assumed all along, without redefining any of them.

### Reuse map

| Need | Reused from | How |
|---|---|---|
| The configuration layer a tenant boundary already scopes | [Configuration Framework](configuration-framework.md) (ADR-EAL-005) | ECF's existing Tenant layer is unchanged; this document defines what the tenant identifier in that layer actually refers to. |
| Identity's relationship to a tenant | [Identity & Access](identity-and-access.md) (ADR-EAL-018) | A Human or Provider identity gains an optional tenant-membership attribute; **no fourth identity type is introduced** — tenant membership is an orthogonal scoping dimension on the existing identity types, not a new one. |
| Permission checks scoped to a tenant | [Identity & Access](identity-and-access.md) (ADR-EAL-018) | `checkPermission()` (unchanged) is called with the caller's tenant membership as part of the resource reference, rather than a new tenant-specific authorization mechanism. |
| Which capabilities are shared vs. tenant-scoped | [Module Registry](module-registry.md) (ADR-EAL-002) + [Capability Registry](capability-registry.md) (ADR-EAL-003) | This document classifies existing capabilities as platform-global or tenant-scoped; it does not redefine either registry's own model. |
| Tenant offboarding data-deletion vs. mandatory retention | [Audit Framework](audit-framework.md) (ADR-EAL-019) | Flagged as an explicit, unresolved tension (§16) rather than unilaterally decided — mandatory compliance retention and a tenant's data-deletion request can conflict, and this document defers the resolution policy rather than silently picking one. |
| Tenant-scoped rate limiting | [API Gateway](api-gateway.md) (ADR-EAL-020) | Reuses the Gateway's existing per-caller-class rate limiting, with tenant membership as one caller-class dimension — no second rate-limiting mechanism. |
| Tenant-scoped dependency declarations | [Dependency Management](dependency-management.md) (ADR-EAL-007) | A tenant-specific plugin instance's dependencies are ordinary EDM edges — no new dependency model for the tenant-scoped case. |

**Scope boundary:** this document does not modify any of the twenty prior documents. It defines what "tenant" means everywhere it was already referenced, and adds the lifecycle/isolation concerns none of them owned.

## 2. Goals

| Goal | Description |
|---|---|
| **A precise definition of tenant identity** | A tenant is a named, registered organizational/data boundary — not an implicit string passed around by convention. |
| **Identity-to-tenant membership, without a new identity type** | Human/Provider identities gain an optional tenant-membership attribute; System Identity remains platform-global by definition. |
| **An explicit isolation guarantee** | A stated boundary for what tenants can and cannot see of each other's data/configuration/usage, consistent with least-privilege (ESA catalog). |
| **A classification of platform-global vs. tenant-scoped capabilities** | Every capability is either shared across all tenants or scoped to one, stated explicitly rather than left ambiguous. |
| **A governed tenant lifecycle** | Onboarding, active operation, suspension, and offboarding (including data deletion) are defined stages, not ad hoc operations. |
| **Full reuse of Foundation/Platform mechanisms for everything except tenant definition itself** | No parallel config, identity, permission, or rate-limiting mechanism specific to tenancy. |

**Non-goals**: EMT does not redefine ECF's tenant layer mechanics, Identity & Access's identity types, or the Module/Capability Registries' own models; it does not resolve the retention-vs-deletion tension it identifies (§16) — that is named as an open governance question; and it does not mandate a specific physical data-isolation technology (single database with row-level tenancy vs. per-tenant database, etc.) — that remains an implementation-phase decision within the isolation guarantee this document states.

## 3. Architecture

```
   ┌───────────────────────────┐
   │   Tenant Registry              │  ← new: tenant identity + lifecycle
   │   (new)                        │
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Identity Tenant Membership   │◄──────┤ Identity & Access             │
   │   (new — an attribute on         │        │ (Human/Provider identity,     │
   │    existing identity types)      │        │  unchanged)                    │
   └─────────────┬─────────────┘        └───────────────────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Capability Tenancy           │◄──────┤ Module Registry /             │
   │   Classification (new)          │        │ Capability Registry           │
   │                                 │        │ (unchanged)                    │
   └─────────────┬─────────────┘        └───────────────────────────┘
                 │
   ┌─────────────▼─────────────┐
   │   Isolation Guarantee           │  ← new: stated boundary,
   │   Statement (new)               │    referenced by ECF's Tenant
   │                                 │    layer, EAG rate limiting, etc.
   └───────────────────────────┘
```

## 4. Components

- **Tenant Registry** *(new)* — the authoritative record of tenant identity (a stable Tenant ID) and lifecycle state (Onboarding, Active, Suspended, Offboarding, Deleted). This is the identifier ECF's existing Tenant configuration layer, the AI Platform's Cost Meter, and any future tenant-scoped reference now resolve to.
- **Identity Tenant Membership** *(new, but an attribute, not a new identity type)* — extends Identity & Access's existing Human and Provider identity types with an optional tenant-membership field; System Identity is, by definition, platform-global and never tenant-scoped.
- **Capability Tenancy Classification** *(new)* — a declared attribute (platform-global or tenant-scoped) on each module/plugin capability, referencing the existing Module Registry/Capability Registry identity — this document classifies, it does not re-register capabilities.
- **Isolation Guarantee Statement** *(new)* — a precise, stated boundary for what a tenant's own identities can and cannot access outside their own tenant (data, configuration, usage/cost visibility), which ECF's Tenant layer, the API Gateway's rate limiting, and the Audit Framework's compliance queries can all reference as the boundary they respectively enforce or report against.

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `registerTenant(tenantId, metadata)` | Governance action → Tenant Registry | Onboards a new tenant. |
| `setTenantLifecycleState(tenantId, state)` | Governance action → Tenant Registry | Advances a tenant through Onboarding → Active → Suspended → Offboarding → Deleted. |
| `assignTenantMembership(identityRef, tenantId)` | Governance action → Identity & Access (extended attribute) | Associates a Human or Provider identity with a tenant. |
| `classifyCapabilityTenancy(capabilityId, scope)` | Capability owner → Capability Tenancy Classification | Declares a capability as platform-global or tenant-scoped. |
| `getTenantState(tenantId)` | Operator/tooling → Tenant Registry | Read-only query of a tenant's current lifecycle state. |

## 6. Data Flow

1. A tenant is onboarded via `registerTenant()`, receiving a stable Tenant ID and entering the Onboarding lifecycle state.
2. Human or Provider identities are associated with that tenant via `assignTenantMembership()` — an attribute on Identity & Access's existing identity types, not a new type.
3. Every capability in the Module Registry/Capability Registry is declared platform-global or tenant-scoped via `classifyCapabilityTenancy()`; a tenant-scoped capability's instance-level configuration and dependencies (EDM edges, ECF's Tenant layer) resolve to that tenant's own scope.
4. At runtime, `checkPermission()` (Identity & Access, unchanged) is called with the caller's tenant membership included in the resource reference, so a permission check can distinguish "authorized for this tenant's data" from "authorized platform-wide."
5. The API Gateway's existing rate limiting (unchanged) may use tenant membership as one caller-class dimension, without a second rate-limiting mechanism.
6. On offboarding, the tenant moves through a defined sequence (§7) that must reconcile any data-deletion request against the Audit Framework's mandatory retention floor for any compliance-designated records already captured for that tenant — an explicit, unresolved tension named in §16 rather than silently decided here.

## 7. Design Patterns

- **Tenant as an orthogonal scoping attribute, not a fourth identity type** — directly continues Identity & Access's own discipline (Identity & Access §7) of anchoring to existing concepts rather than fragmenting identity; tenant membership is metadata on an identity, not a new kind of caller.
- **Classification over redefinition** — capabilities are classified (global vs. tenant-scoped) using their existing Module Registry/Capability Registry identity, mirroring the Audit Framework's own "designate, don't redefine" approach to the Mandatory Audit Event Catalog (Audit Framework §7).
- **Named, unresolved tension surfaced explicitly rather than silently decided** — the retention-vs-deletion conflict (§16) follows the same discipline as EDM's deferred PLM/Module Registry migration question (EDM §16) and EVCS's deferred conformance question: name the open governance decision, do not quietly resolve it by omission.

## 8. Security Considerations

*(Citing the Security Principles Catalog directly, per ESA's discipline.)*

- **Principle: Least-Privilege** (ESA catalog) is the direct basis for the Isolation Guarantee Statement — a tenant's identities should have no visibility into another tenant's data, configuration, or usage by default.
- **Cross-tenant capability sharing must be an explicit, reviewed classification, not a default** — a capability should be classified tenant-scoped unless there is a deliberate reason for it to be platform-global, consistent with fail-closed/least-privilege defaults elsewhere in this library.
- **Tenant offboarding data-deletion requests intersect with the Audit Framework's retention floor** (§16) — this is a security-and-compliance-relevant tension, not merely an operational one, since mishandling it risks either a compliance violation (deleting mandatory-retained records) or a data-protection violation (retaining data a tenant is entitled to have deleted) depending on which is resolved incorrectly.
- **Tenant Registry write access is itself a high-privilege operation** — onboarding, suspending, or deleting a tenant should be gated by a specific, narrowly-granted permission via Identity & Access, not general administrative access.

## 9. Scalability

- **Tenant count and identity-membership lookups are the dominant read pattern** — mirrors the read/write asymmetry established throughout this library; `checkPermission()` calls now include a tenant-scoping dimension on every request, so this lookup must be as cheap as Identity & Access's own permission check (Identity & Access §9).
- **Tenant-scoped capability instances scale independently per tenant** — a tenant-scoped plugin's own instance count (tracked via ESR, unchanged) scales with that tenant's load, not with total tenant count.
- **Isolation guarantee should not itself dictate a single physical scaling model** — the Isolation Guarantee Statement (§4) describes a logical boundary; whether it's implemented via shared infrastructure with row-level isolation or per-tenant physical isolation is an implementation-phase decision that can vary by tenant tier without changing this document's architecture.

## 10. Best Practices

- Classify every capability's tenancy scope explicitly at registration time — never leave it implicit or assumed.
- Default new capabilities to tenant-scoped unless there's a deliberate, reviewed reason to make them platform-global.
- Gate Tenant Registry lifecycle transitions (especially offboarding/deletion) behind a specific, narrowly-granted Identity & Access permission.
- Resolve the retention-vs-deletion tension (§16) explicitly and in writing before any tenant offboarding involving compliance-designated records actually occurs — never improvise it case by case.

## 11. Common Pitfalls

- **Treating "tenant" as an implicit string threaded through ECF's config layer with no actual registry behind it** — the exact gap this document exists to close; without a Tenant Registry, "tenant" remains a convention, not an enforceable boundary.
- **Introducing a fourth identity type for "tenant" instead of a membership attribute** — repeats the identity-fragmentation mistake Identity & Access was built to prevent.
- **Defaulting new capabilities to platform-global "for simplicity"** — inverts the least-privilege default and risks unintentional cross-tenant data exposure.
- **Silently choosing either full retention or full deletion on tenant offboarding without surfacing the tension to governance** — the single most consequential pitfall in this document; either choice made unilaterally risks a real compliance or data-protection failure.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **Leave "tenant" as an implicit convention (status quo)** | Continue letting ECF's Tenant layer and the AI Platform's cost attribution reference tenant IDs with no registry or lifecycle behind them. | Fails the core definitional goal outright — this is precisely the unresolved gap identified in §1. |
| **A fourth, tenant-specific identity type** | Model a tenant itself as a new kind of identity alongside Human/Provider/System. | Repeats the exact fragmentation Identity & Access was built to prevent (Identity & Access §11); tenant membership is better modeled as an attribute of an identity than a new identity kind. |
| **Physical, per-tenant infrastructure isolation mandated architecture-wide** | Require every tenant to have fully separate infrastructure regardless of tier or need. | Over-constrains implementation choices this document doesn't need to make; the Isolation Guarantee Statement defines the logical boundary, leaving physical implementation (shared vs. dedicated infrastructure) as an implementation-phase, possibly tier-dependent, decision. |
| **Resolve the retention-vs-deletion tension unilaterally in this document** | Pick either "compliance retention always wins" or "deletion request always wins" as a fixed rule. | Both defaults carry real risk depending on jurisdiction and specific compliance regime; this document instead surfaces the tension explicitly (§16) as a governance decision requiring deliberate resolution, consistent with how EDM and EVCS handled comparably consequential open questions. |

## 13. Migration Strategy

1. **Stand up the Tenant Registry** and register existing tenants (if any operate today under an implicit convention) with stable Tenant IDs.
2. **Extend Identity & Access's identity types with the tenant-membership attribute**, assigning existing identities to their appropriate tenant.
3. **Classify every existing capability as platform-global or tenant-scoped**, defaulting to tenant-scoped where unclear, per the least-privilege best practice (§10).
4. **Wire `checkPermission()` calls to include tenant membership in the resource reference incrementally**, starting with the highest-risk cross-tenant-exposure capabilities first.
5. **Resolve the retention-vs-deletion governance question (§16) before the first tenant offboarding involving any Audit-Framework-mandatory record occurs** — not simply before this document is used at all.

## 14. Success Criteria

- Every tenant has a stable Tenant ID in the Tenant Registry; zero tenant references remain purely implicit/conventional.
- Every capability has an explicit tenancy classification (platform-global or tenant-scoped); zero capabilities left unclassified.
- Zero new identity types introduced — tenant membership is confirmed as an attribute on Identity & Access's existing types.
- The retention-vs-deletion tension (§16) has a documented, governance-approved resolution policy before any tenant offboarding exercises it in practice.
- At least one tenant-scoped permission check is demonstrated end-to-end via `checkPermission()` with tenant membership included in the resource reference.

## 15. Decision Matrix

| Criterion (weight) | Tenant Registry + membership attribute + capability classification (recommended) | Leave implicit | Fourth identity type for tenant | Mandate physical isolation architecture-wide | Unilaterally resolve retention-vs-deletion here |
|---|---|---|---|---|---|
| Closes the "tenant is undefined" finding (High) | 5 | 1 | 4 | 4 | 4 |
| Avoids identity fragmentation (High) | 5 | 3 | 1 | 4 | 4 |
| Explicit isolation guarantee (High) | 5 | 1 | 3 | 5 | 3 |
| Flexibility of implementation (physical isolation choice) (Medium) | 4 | 3 | 3 | 1 | 4 |
| Governance-appropriate handling of retention-vs-deletion (Medium) | 5 | 2 | 3 | 3 | 2 |
| Implementation/governance overhead (Medium, lower = better fit) | 3 | 5 | 2 | 2 | 4 |
| **Weighted outcome** | **Best overall fit** | Fails core definitional goal | Fails identity-reuse goal | Over-constrains implementation | Risks premature, possibly wrong governance call |

**Conclusion**: a Tenant Registry with identity-membership as an attribute (not a new identity type) and explicit per-capability tenancy classification is recommended, with the retention-vs-deletion tension surfaced rather than resolved unilaterally.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-021: Enterprise Multi Tenancy as a Registry, Identity Attribute, and Capability Classification — with Retention-vs-Deletion Explicitly Unresolved**

- **Status**: Accepted
- **Context**: "Tenant" is already a load-bearing concept in ECF's configuration hierarchy and referenced across multiple subsequent documents, but no document defines tenant identity, isolation guarantees, or lifecycle.
- **Decision**: Introduce a Tenant Registry (identity + lifecycle), extend Identity & Access's Human/Provider identity types with an optional tenant-membership attribute (no new identity type), and require every capability to be explicitly classified platform-global or tenant-scoped. **This decision does not modify any of the twenty prior documents.** A specific, consequential open question is surfaced rather than resolved: **when a tenant is offboarded and requests data deletion, but some of that tenant's records are captured under the Audit Framework's mandatory retention floor (ADR-EAL-019), which requirement takes precedence?** This document does not decide that question; it names it as requiring a deliberate, separately-approved governance decision (likely jurisdiction- and record-type-dependent) before any real offboarding exercises it.
- **Rationale**: The Decision Matrix (§15) shows this is the only option that defines tenant identity without fragmenting identity or over-constraining implementation, while correctly declining to silently resolve a governance question whose wrong answer carries real compliance or data-protection risk.
- **Consequences**:
  - *Positive*: "tenant" now has a precise, registry-backed definition; every capability's tenancy scope is explicit rather than assumed; the isolation guarantee gives ECF's Tenant layer, the API Gateway's rate limiting, and the Audit Framework's compliance queries a real boundary to reference.
  - *Negative*: the retention-vs-deletion question remains genuinely open and must be resolved by separate governance decision before certain offboarding scenarios can safely proceed — this document creates that obligation rather than discharging it.
  - *Neutral*: physical data-isolation architecture (shared infrastructure vs. per-tenant) is left as an implementation-phase, potentially tier-dependent choice.
- **Alternatives rejected**: leave implicit, a fourth identity type, mandated physical isolation, unilaterally resolving retention-vs-deletion — see §12 and §15.
- **Reversibility**: Moderate — the Tenant Registry and classification could be decommissioned, but any tenant-scoped data/configuration already keyed by Tenant ID would need remediation; the identity-membership attribute is low-cost to remove given it does not alter Identity & Access's own identity types.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Tenant Registry, identity-membership attribute, and capability classification are specified at architecture level. |
| **Avoids identity fragmentation** | Confirmed | Tenant membership is an attribute on existing Identity & Access types, not a new identity kind. |
| **Isolation guarantee precision** | Ready for review | Stated as a logical boundary; physical implementation deliberately left open. |
| **Retention-vs-deletion governance decision** | **Explicitly unresolved — requires your decision before affected offboarding occurs** | Named in §16 as an open question, not defaulted either direction. |
| **Technology-agnostic validation** | Ready | No binding to a specific database multi-tenancy pattern. |
| **Threat-model application** | Recommended as a priority candidate | Given cross-tenant isolation's direct security implications, alongside Identity & Access, the Audit Framework, and the API Gateway (ESA §18). |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Resolve the retention-vs-deletion governance question** — the highest-priority follow-up, likely requiring input on applicable jurisdiction(s) and specific compliance regime(s), before broad tenant offboarding is exercised in production.
- **Tenant tiering** — a future refinement distinguishing tenant tiers (e.g., differing isolation strength, rate-limit thresholds, or SLA) building on the Tenant Registry's lifecycle state rather than a new mechanism.
- **Cross-tenant capability request workflows** — if a tenant-scoped capability's data ever needs to be deliberately, temporarily shared with another tenant (e.g., a support/debugging scenario), a future formalized workflow (via the Workflow Engine) could govern that exception rather than an ad hoc classification change.
- **Apply ESA's Threat Modeling Methodology to this document** — given direct cross-tenant isolation implications, alongside Identity & Access, the Audit Framework, and the API Gateway.

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-021. The retention-vs-deletion tension named in §16 remains an open governance question, not resolved by this freeze.
