---
title: Enterprise Marketplace
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Marketplace

## 1. Problem Statement

[Licensing](licensing.md) (ADR-EAL-022) defines what a license grants and how it's enforced, but deliberately does not define how a customer *discovers* something to license or *initiates* the acquisition (Licensing §2 non-goals: "does not define pricing, billing... or payment processing"). [Plugin Lifecycle Management](plugin-lifecycle-management.md) (PLM, ADR-EAL-001) defines how a plugin is registered and activated, but not how a third-party publisher's plugin becomes customer-discoverable in the first place, distinct from the platform's own first-party modules.

Enterprise Marketplace (EMP) is the customer-facing discovery and acquisition layer sitting on top of both: a catalog of listings (referencing existing Module/Plugin IDs, never re-registering them), a publisher onboarding path (extending Identity & Access's existing Provider identity, never a new identity type), and a purchase fulfillment flow that — because acquisition is naturally a multi-step, potentially long-running, compensable process — is itself an ordinary Workflow Engine definition, not a bespoke mechanism.

### Reuse map

| Need | Reused from | How |
|---|---|---|
| What is being listed (a plugin, module capability, or plan) | [Module Registry](module-registry.md) (ADR-EAL-002) / [Plugin Lifecycle Management](plugin-lifecycle-management.md) (ADR-EAL-001) / [Licensing](licensing.md) (ADR-EAL-022) | A listing references an already-registered (or concurrently-registering) module/plugin ID and a Licensing plan ID — the Marketplace does not re-register capabilities or re-define plans. |
| Publisher identity | [Identity & Access](identity-and-access.md) (ADR-EAL-018) | A third-party publisher is an existing Provider Identity with a "publisher" attribute, mirroring exactly how Multi Tenancy added a tenant-membership attribute rather than a new identity type (Multi Tenancy §7). |
| Plugin submission | [Plugin Lifecycle Management](plugin-lifecycle-management.md) (ADR-EAL-001) | A publisher's plugin is registered through PLM's existing, unchanged registration flow; the Marketplace Listing is a customer-facing wrapper around an already-valid registration, not a second submission path. |
| Purchaser/tenant identity | [Multi Tenancy](multi-tenancy.md) (ADR-EAL-021) | A purchase is made on behalf of a Tenant (the typical case) or a specific identity for seat-based plans, exactly as Licensing already scopes entitlements. |
| Entitlement grant on successful purchase | [Licensing](licensing.md) (ADR-EAL-022) | A completed purchase calls the unchanged `grantLicense()` — the Marketplace never implements its own entitlement mechanism. |
| Purchase fulfillment as a multi-step, compensable process | [Workflow Engine](workflow-engine.md) (ADR-EAL-013) | Purchase fulfillment (validate → external payment step → grant license → trigger plugin activation → notify) is an ordinary workflow definition, with compensation (e.g., revoke a just-granted license) for a failure partway through — not a bespoke fulfillment engine. |
| External-facing purchase request | [API Gateway](api-gateway.md) (ADR-EAL-020) | A purchase request is an external call through the Gateway's unchanged pipeline (Authentication → Authorization → Licensing → Feature Flags → Capability Execution, ADR-EAL-022) — the purchase capability itself is authorized like any other; the *target* license doesn't exist yet, which is exactly why fulfillment, not pre-check, is what grants it. |
| Promotional/trial listing rollout | [Feature Flag Framework](feature-flag-framework.md) (ADR-EAL-006) | Featuring a listing or offering a time-limited trial reuses EFF's rollout/kill-switch mechanism — no separate promotional system. |
| Purchase notification | [Event Bus](event-bus.md) (ADR-EAL-014) + [Notification Framework](notification-framework.md) (ADR-EAL-015) | A completed purchase publishes an event; ENF's existing Trigger Mapping (an ordinary EEB subscriber) binds a confirmation notification to it — no new notification mechanism. |
| Purchase-failure classification | [Error Handling Framework](error-handling-framework.md) (ADR-EAL-009) | Classifies via EEHF's existing taxonomy with new `err.marketplace.*` codes. |

**Scope boundary:** this document does not modify any of the twenty-two prior documents. It does not process payment itself — consistent with Licensing's own explicit non-goal (Licensing §2) — payment processing remains an external, out-of-scope concern this document's fulfillment workflow calls out to but does not define.

## 2. Goals

| Goal | Description |
|---|---|
| **A customer-facing catalog referencing existing identities** | Listings point to existing Module/Plugin IDs and Licensing plan IDs — no parallel catalog identity scheme. |
| **Publisher onboarding without a new identity type** | Third-party publishers are Provider Identities with a publisher attribute, reusing Identity & Access unchanged. |
| **Purchase as an ordinary, compensable workflow** | Fulfillment is a Workflow Engine definition with declared compensation, not a bespoke transactional mechanism. |
| **No new entitlement mechanism** | A successful purchase calls Licensing's unchanged `grantLicense()` — the Marketplace is a purchase *initiator*, never a second entitlement authority. |
| **Payment processing explicitly out of scope** | Consistent with Licensing's own boundary, this document defines where a payment step fits in the fulfillment workflow without defining payment processing itself. |

**Non-goals**: EMP does not process payments or handle payment credentials (an external system's responsibility, referenced but not defined here); it does not redefine PLM's plugin registration, Licensing's entitlement model, or the Workflow Engine's orchestration mechanics; and it does not introduce a new identity type for publishers or purchasers.

## 3. Architecture

```
   ┌───────────────────────────┐
   │   Marketplace Listing          │  ← new: catalog entries referencing
   │   Registry (new)               │    existing Module/Plugin + Plan IDs
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Publisher Onboarding          │◄──────┤ Identity & Access             │
   │   (new — publisher attribute      │        │ (Provider Identity, unchanged) │
   │    on existing Provider Identity) │        └───────────────────────────┘
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Purchase Fulfillment          │──────►│ Workflow Engine               │
   │   Workflow (new definition,      │        │ (startWorkflow(), unchanged)  │
   │    not a new engine)             │        └───────────────────────────┘
   └─────────────┬─────────────┘
                 │ on success
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Licensing (unchanged)         │◄──────┤ grantLicense()                │
   └─────────────┬─────────────┘        └───────────────────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Event Bus (unchanged)         │──────►│ Notification Framework        │
   │   publish("purchase.completed")  │        │ (ordinary subscriber,          │
   │                                 │        │  unchanged)                    │
   └───────────────────────────┘        └───────────────────────────┘
```

## 4. Components

- **Marketplace Listing Registry** *(new)* — customer-facing catalog entries, each referencing an existing Module/Plugin ID and a Licensing plan ID, plus presentation metadata (description, category) that neither the Module Registry nor the Capability Registry was designed to carry.
- **Publisher Onboarding** *(new attribute, not a new component category)* — a "publisher" attribute on an existing Provider Identity (Identity & Access, unchanged), letting a third-party publisher submit plugins through PLM's existing registration flow and manage their own listings.
- **Purchase Fulfillment Workflow** *(new workflow definition, reusing the unchanged Workflow Engine)* — the multi-step acquisition sequence: validate the purchase request → invoke an external payment step (out of scope) → call `grantLicense()` → trigger the purchased plugin's activation for the purchasing tenant (via PLM's unchanged activation flow) → publish a completion event.
- **Review/Rating Store** *(new — no existing reuse candidate)* — customer reviews and ratings attached to a listing; the one genuinely new data store this document introduces without an analog elsewhere in the library.

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `createListing(listingId, moduleOrPluginId, planId, metadata)` | Publisher → Marketplace Listing Registry | Publishes a catalog entry referencing an already-registered (or concurrently-submitted) module/plugin and a Licensing plan. |
| `onboardPublisher(identityRef)` | Governance/self-service action → Identity & Access (attribute extension) | Marks an existing Provider Identity as a publisher. |
| `initiatePurchase(listingId, purchaserTenantRef)` | Purchaser (via API Gateway, unchanged pipeline) → Purchase Fulfillment Workflow | Starts the fulfillment workflow (`startWorkflow()`, EWE unchanged) for a given listing. |
| `submitReview(listingId, purchaserIdentityRef, rating, text)` | Purchaser → Review/Rating Store | Records a review, scoped to a purchaser who holds (or held) an active license for that listing. |

## 6. Data Flow

1. A publisher (an existing Provider Identity with the publisher attribute) submits a plugin through PLM's unchanged registration flow, then calls `createListing()` to make it customer-discoverable, referencing the plugin's own ID and a Licensing plan.
2. A prospective purchaser, authenticated and authorized through the API Gateway's unchanged pipeline, calls `initiatePurchase()`, which starts the Purchase Fulfillment Workflow (`startWorkflow()`, EWE unchanged) — note that the *purchase capability itself* is authorized like any other capability invocation; the license being purchased does not yet exist, which is precisely why fulfillment (not a pre-check) is what grants it.
3. The workflow's steps execute in sequence: validation, an external payment step (out of scope for this document), `grantLicense()` on payment success, and a trigger for the purchased plugin's tenant-scoped activation via PLM's unchanged flow.
4. Any step failure triggers the Workflow Engine's unchanged compensation mechanism — e.g., if plugin activation fails after a license was already granted, a compensating action can revoke that grant, keeping the tenant's entitlement state consistent with what was actually fulfilled.
5. On successful completion, the workflow publishes a `purchase.completed` event on the unchanged Event Bus; the Notification Framework's existing Trigger Mapping (an ordinary subscriber) sends a purchase confirmation, with no Marketplace-specific notification logic.
6. A purchaser who holds or held an active license for a listing may `submitReview()`, recorded in the Review/Rating Store.

## 7. Design Patterns

- **Catalog referencing existing identity, never re-registering** — mirrors the Capability Registry's own discipline (Capability Registry §1) of resolving rather than duplicating identity, applied here to what's being sold rather than what's being discovered internally.
- **Purchase as an ordinary workflow, not a bespoke transaction engine** — directly reuses the Workflow Engine's saga-style compensation (Workflow Engine §7) for exactly the kind of multi-step, partially-reversible process it was built for, rather than inventing a parallel fulfillment mechanism.
- **Attribute extension over new identity type** — continues the exact discipline established by Multi Tenancy (tenant membership as an attribute) and reapplied here for "publisher" — a role/attribute on an existing identity, never a fourth kind of caller.
- **Explicit non-goal boundary for payment** — mirrors Licensing's own explicit exclusion of billing/payment processing (Licensing §2); this document is consistent with, not an exception to, that established boundary.

## 8. Security Considerations

*(Citing the Security Principles Catalog directly, per ESA's discipline.)*

- **Principle: Least-Privilege** (ESA catalog) applies to publisher access — a publisher identity should be scoped to managing its own listings, not others'.
- **Principle: Fail-Closed Validation** (ESA catalog) applies to the Purchase Fulfillment Workflow — an ambiguous or failed validation step must halt fulfillment (per the Workflow Engine's own failure-behavior model, EWE §4), never proceed optimistically.
- **No payment credential ever enters this document's own components** — the payment step is explicitly external and out of scope (§2); the Purchase Fulfillment Workflow orchestrates *that a payment step occurs*, never handles payment data itself, consistent with the "no secrets inline" discipline applied throughout this library.
- **Review authenticity** — `submitReview()` should verify the reviewer actually holds or held an active license for the listing (via Licensing's unchanged Entitlement Registry query), preventing unverified reviews.

## 9. Scalability

- **Listing browsing is read-heavy; purchases are comparatively rare** — the now-familiar read/write asymmetry established throughout this library (Module Registry §9, Capability Registry §9); the Listing Registry's read path should be optimized independently of purchase-write volume.
- **Purchase Fulfillment Workflow instances scale per the Workflow Engine's own existing model** — no new scaling concern beyond what EWE already addresses (Workflow Engine §9), since fulfillment is an ordinary workflow, not a new execution engine.
- **Review/Rating Store is the one net-new storage growth vector** — unlike every other component in this document, it has no reuse candidate and should be capacity-planned on its own terms (review volume relative to purchase volume).

## 10. Best Practices

- Always reference an existing Module/Plugin ID and Licensing plan ID when creating a listing — never let a listing describe something not already validly registered/defined elsewhere.
- Declare compensation for every fulfillment step with a real side effect (license grant, plugin activation), consistent with the Workflow Engine's own best practice (EWE §10).
- Treat the payment step as a black box the workflow calls out to and awaits, never as logic this document's own components implement.
- Verify review authenticity against Licensing's entitlement history before accepting a review.

## 11. Common Pitfalls

- **Building a second plugin-registration path "for marketplace publishers"** — repeats exactly the duplication this library has avoided since EDM; publishers use PLM's existing, unchanged registration flow.
- **Implementing payment processing directly** — violates the explicit non-goal shared with Licensing (§2); payment must remain an external, out-of-scope call the fulfillment workflow awaits.
- **Granting a license before fulfillment actually completes** — risks an entitled-but-not-delivered state; `grantLicense()` should occur at the correct point in the workflow sequence (post-payment-confirmation), not eagerly.
- **Treating a publisher as a new identity type instead of an attribute** — repeats the identity-fragmentation mistake Identity & Access and Multi Tenancy have each avoided.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **A bespoke purchase/fulfillment transaction engine** | Build dedicated transactional logic for purchases instead of reusing the Workflow Engine. | Directly duplicates a capability (multi-step, compensable orchestration) the Workflow Engine already provides; purchase fulfillment is a textbook saga, not a reason for new orchestration infrastructure. |
| **A second plugin submission path for marketplace publishers** | Let marketplace publishers register plugins through a dedicated Marketplace-specific flow. | Fragments plugin registration between first-party and third-party sources for no structural reason; PLM's registration flow already handles this identity-agnostically. |
| **A new "Publisher" identity type** | Model publishers as a fourth kind of caller alongside Human/Provider/System. | Repeats the exact fragmentation Identity & Access and Multi Tenancy were each built to prevent; publisher is a role/attribute on an existing Provider Identity. |
| **Process payment directly within this document's scope** | Define payment processing as part of the Marketplace architecture. | Payment processing is a distinct commerce/compliance domain (PCI-scope, external processor integration) explicitly excluded by Licensing's own precedent (Licensing §2); keeping it external and out of scope avoids conflating architecture with a regulated third-party integration concern. |

## 13. Migration Strategy

1. **Stand up the Marketplace Listing Registry, Publisher Onboarding attribute, and Review/Rating Store** as new, independently-operable components.
2. **Define the Purchase Fulfillment Workflow as an ordinary Workflow Engine definition**, validating it end-to-end (including a deliberately-triggered mid-fulfillment failure, to confirm compensation works) before any real purchase flows through it.
3. **Onboard a small number of listings referencing already-registered, stable plugins first**, before opening publisher self-service onboarding broadly.
4. **Wire the external payment step as a genuinely external call** from day one — never a placeholder implemented internally "temporarily," which risks becoming an unintentional permanent scope violation.
5. **Bind a purchase-confirmation notification via the Notification Framework's existing Trigger Mapping** once the fulfillment workflow reliably publishes its completion event.

## 14. Success Criteria

- Every listing references an already-registered Module/Plugin ID and an existing Licensing plan ID — zero listings for unregistered or undefined targets.
- Zero new identity types introduced for publishers or purchasers.
- A deliberately-failed mid-fulfillment step is demonstrated triggering correct compensation (e.g., license revocation) via the unchanged Workflow Engine mechanism.
- Zero payment-credential handling within any component this document defines.
- At least one purchase is traceable end-to-end — listing view, purchase initiation, fulfillment, license grant, activation, and confirmation notification — via a single correlation ID.

## 15. Decision Matrix

| Criterion (weight) | Listing registry + attribute-based publisher + Workflow-Engine-based fulfillment (recommended) | Bespoke transaction engine | Second plugin submission path | New Publisher identity type | Payment processing in-scope |
|---|---|---|---|---|---|
| Reuse of Workflow Engine for fulfillment (High) | 5 | 1 | 4 | 4 | 3 |
| Reuse of PLM's registration flow (High) | 5 | 4 | 1 | 3 | 4 |
| Avoids identity fragmentation (High) | 5 | 4 | 4 | 1 | 4 |
| Consistent with Licensing's payment non-goal (High) | 5 | 3 | 4 | 4 | 1 |
| Compensable, auditable fulfillment (Medium) | 5 | 2 | 3 | 3 | 3 |
| Implementation/governance overhead (Medium, lower = better fit) | 3 | 2 | 3 | 3 | 2 |
| **Weighted outcome** | **Best overall fit** | Fails reuse principle | Fails reuse principle | Fails identity-reuse goal | Fails scope boundary |

**Conclusion**: a Listing Registry referencing existing identities, publisher-as-attribute, and Workflow-Engine-based fulfillment is recommended. It is the only option that fully reuses PLM, Licensing, the Workflow Engine, and Identity & Access without duplicating any of their responsibilities, while respecting the payment-processing boundary Licensing already established.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-023: Enterprise Marketplace as a Listing/Publisher Layer with Workflow-Engine-Based Fulfillment**

- **Status**: Accepted
- **Context**: Licensing defines entitlement but not discovery/acquisition; PLM defines plugin registration but not customer-facing listing; nothing in the library addresses how a customer discovers and acquires a licensed capability.
- **Decision**: Introduce a Marketplace Listing Registry (referencing existing Module/Plugin and Licensing plan IDs), a publisher attribute on Identity & Access's existing Provider Identity, a Purchase Fulfillment Workflow expressed as an ordinary Workflow Engine definition (with declared compensation), and a Review/Rating Store. **Confirmed at approval: Marketplace reuses existing platform capabilities throughout; the Workflow Engine remains the only orchestration mechanism** — no second, Marketplace-specific orchestrator is introduced, now or in any future extension, without superseding this ADR. **Payment processing remains outside the Marketplace boundary** entirely, consistent with Licensing's own established boundary. **No modification to any of the twenty-two prior documents.**
- **Rationale**: The Decision Matrix (§15) shows this is the only option that fully reuses PLM, Licensing, the Workflow Engine, and Identity & Access for their respective, already-established responsibilities, introducing new components only for the genuinely new concerns (customer-facing catalog, publisher role, reviews).
- **Consequences**:
  - *Positive*: purchases get durable, compensable fulfillment for free from the Workflow Engine; publishers and purchasers use existing identity/tenancy models unchanged; payment processing stays cleanly out of this architecture's scope, consistent with Licensing's precedent.
  - *Negative*: introduces a fourth new component category (Listing Registry, publisher attribute, Fulfillment Workflow definition, Review Store); an external payment integration is a real dependency this document does not itself resolve.
  - *Neutral*: publisher payout mechanics are entirely out of scope, mirroring the payment-processing exclusion.
- **Alternatives rejected**: bespoke transaction engine, second plugin submission path, new Publisher identity type, in-scope payment processing — see §12 and §15.
- **Reversibility**: Fully reversible — the Listing Registry, publisher attribute, and Review Store can be decommissioned without affecting PLM, Licensing, or the Workflow Engine; any in-flight fulfillment workflows would need individual resolution.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Listing Registry, publisher attribute, Fulfillment Workflow, and Review Store are specified at architecture level. |
| **Full reuse validation** | Confirmed | §1's reuse map traces every non-catalog/review-specific need to an existing Foundation/Platform/Enterprise mechanism. |
| **Consistency with Licensing's payment boundary** | Confirmed | Payment processing remains explicitly external, mirroring Licensing §2's own non-goal. |
| **Compensation correctness** | Needs validation | The specific compensating actions for each fulfillment step (e.g., license revocation on late-stage failure) are specified conceptually; concrete implementation validation is future work. |
| **Technology-agnostic validation** | Ready | No binding to a specific payment processor or e-commerce platform. |
| **Reuse and orchestration boundary** | Confirmed at approval | Reuses existing platform capabilities throughout; Workflow Engine is the only orchestration mechanism; payment processing stays outside the Marketplace boundary. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Publisher payout/revenue-share mechanics** — a future, separately-scoped document or extension addressing how publisher revenue share is calculated and disbursed, kept as external to this architecture as payment processing itself.
- **Marketplace analytics** — surfacing listing performance (views, conversion, ratings trends) via EOA's existing Unified Query Interface rather than a Marketplace-specific analytics store.
- **Bundle/multi-listing purchases** — extending the Purchase Fulfillment Workflow to handle a single transaction spanning multiple listings, as a workflow-definition refinement rather than a new mechanism.
- **Trial-to-paid conversion flows** — building on EFF's existing rollout mechanism (already reused for promotional/trial listings, §1) to formalize automatic or prompted conversion from a trial license to a paid one.

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-023.
