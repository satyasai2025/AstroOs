---
title: Enterprise Integration Framework
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Integration Framework

## 1. Problem Statement

Two frozen documents have already named an external system this library never defined how to actually reach: [Licensing](licensing.md) and [Marketplace](marketplace.md) both call out an "external payment step" as explicitly out of scope (Licensing §2, Marketplace §2) — assumed to exist, never given a mechanism. Separately, the [Notification Framework](notification-framework.md)'s Delivery Channel Adapter Layer (ENF §4) already implements one specific instance of "calling an external system" (email/SMS/push providers) without this library ever generalizing that pattern for reuse elsewhere.

The Enterprise Integration Framework (EIF) is that generalization: a pattern for **outbound calls to external third-party systems** and **inbound webhook receipt from them** — reusing every applicable mechanism already established, and explicitly recognizing (not redefining) ENF's existing adapter layer as one instance of the same pattern.

This is the mirror image of two already-frozen documents, and the distinction matters:

- The [API Gateway](api-gateway.md) (ADR-EAL-020) is the platform's single point for **external callers reaching in**. EIF is the platform's pattern for **the platform reaching out** — an inbound webhook from an external system is still received through the unchanged Gateway (as just another route), but EIF defines the connector/verification pattern for what happens once it arrives.
- The [SDK](sdk.md) (ADR-EAL-024) is a convenience wrapper for **external developers calling into this platform**. EIF is for **this platform calling into external systems** — the opposite direction, with different concerns (credential management for outbound calls, circuit-breaking against an external system's own reliability).

### Reuse map

| Need | Reused from | How |
|---|---|---|
| Inbound webhook receipt | [API Gateway](api-gateway.md) (ADR-EAL-020) | A webhook endpoint is an ordinary external route through the Gateway's unchanged pipeline — no second inbound path. |
| External system's own identity when it calls in (a webhook sender) | [Identity & Access](identity-and-access.md) (ADR-EAL-018) | An external system resolves to an existing Provider Identity, exactly as any other external caller (API Gateway §1) — no new identity type for "external system." |
| Outbound credential storage | [Configuration Framework](configuration-framework.md) (ADR-EAL-005) | Credentials for reaching an external system are sourced via ECF's existing secrets-by-reference mechanism, never inline. |
| An external call made from within a multi-step process | [Workflow Engine](workflow-engine.md) (ADR-EAL-013) | An outbound call (e.g., the payment step Licensing and Marketplace both deferred) is an ordinary workflow step; a webhook confirming completion resumes a paused instance via the Engine's unchanged `resumeInstance()` — no new orchestration logic. |
| Translating a received webhook into an internal signal | [Event Bus](event-bus.md) (ADR-EAL-014) | A verified webhook is translated into an ordinary published event for internal subscribers — no second pub/sub mechanism. |
| Outbound call failure classification | [Error Handling Framework](error-handling-framework.md) (ADR-EAL-009) | Classifies via EEHF's existing taxonomy with new `err.integration.*` codes. |
| Circuit-breaking against an unreliable external system | *Pattern* validated by [Plugin Lifecycle Management](plugin-lifecycle-management.md) (PLM §7), not PLM's own component | EIF introduces its own circuit breaker for outbound calls, applying the same validated pattern — PLM's Failure Handler is scoped to plugin lifecycle health, a different concern, so its component is not reused directly, only the pattern it already proved out. |
| The existing notification-channel adapter instance | [Notification Framework](notification-framework.md)'s Delivery Channel Adapter Layer (ENF §4) | Explicitly recognized as an already-frozen, unmodified instance of the same outbound-connector pattern this document generalizes — not redefined, not migrated, just acknowledged as a sibling. |

**Scope boundary:** this document does not modify any of the twenty-four prior documents, including the API Gateway's inbound-only scope, the SDK's inbound-convenience scope, ENF's existing adapter layer, or the Workflow Engine's exclusive orchestration role.

## 2. Goals

| Goal | Description |
|---|---|
| **A named pattern for outbound external calls** | Credential sourcing, circuit-breaking, and error classification for calling an external system are defined once, generally, rather than reinvented per integration (as payment, and potentially others, would otherwise require). |
| **Webhook receipt through the existing Gateway, not a second inbound path** | Inbound callbacks from external systems arrive as ordinary Gateway routes. |
| **External systems as ordinary Provider Identities** | No new identity type for "third-party system." |
| **Recognizes, does not redefine, ENF's existing adapter layer** | The Notification Framework's channel adapters remain exactly as frozen; this document generalizes the pattern for future use, without touching that instance. |
| **Fills the payment-step gap Licensing and Marketplace both deferred** | Gives those documents' "external payment step" a concrete, reusable connector pattern to plug into — without this document defining payment processing itself. |

**Non-goals**: EIF does not define payment processing, or any other specific external integration's business logic; it does not modify the API Gateway's inbound scope, the SDK's outbound-convenience scope, or ENF's existing adapter implementation; and it does not become a second orchestrator — external calls remain ordinary steps within whatever mechanism invokes them (a workflow step, a direct capability call).

## 3. Architecture

```
   OUTBOUND                                    INBOUND
   ┌───────────────────────────┐        ┌───────────────────────────┐
   │   Caller (a Workflow Engine    │        │   External system              │
   │   step, or any capability)     │        │   (webhook sender)              │
   └─────────────┬─────────────┘        └─────────────┬─────────────┘
                 │                                    │ external request
   ┌─────────────▼─────────────┐        ┌─────────────▼─────────────┐
   │   Outbound Connector           │        │   API Gateway (unchanged)      │
   │   Registry (new)               │        │   — webhook is an ordinary      │
   └─────────────┬─────────────┘        │     external route              │
                 │                       └─────────────┬─────────────┘
   ┌─────────────▼─────────────┐                       │
   │   Outbound Circuit Breaker     │        ┌─────────────▼─────────────┐
   │   (new — pattern from PLM §7,  │        │   Webhook Verification          │
   │    not PLM's own component)    │        │   (new)                        │
   └─────────────┬─────────────┘        └─────────────┬─────────────┘
                 │                                    │
   ┌─────────────▼─────────────┐        ┌─────────────▼─────────────┐
   │   External third-party system  │        │   Event Bus (unchanged)        │
   │                                 │        │   — translated into an          │
   │                                 │        │     ordinary published event     │
   └───────────────────────────┘        └───────────────────────────┘
```

## 4. Components

- **Outbound Connector Registry** *(new)* — records each external system integration's identity, endpoint, and credential reference (via ECF's unchanged secrets-by-reference mechanism); the concrete, reusable answer to "how does a workflow step (or any caller) actually reach the payment processor Licensing/Marketplace deferred."
- **Outbound Circuit Breaker** *(new, applying a validated pattern, not a reused component)* — protects against a failing or slow external system using the same circuit-breaking discipline PLM's Failure Handler already validated (PLM §7) for a different concern (plugin health); this document introduces its own instance scoped to outbound-call reliability specifically.
- **Webhook Verification** *(new)* — verifies an inbound webhook's authenticity (e.g., signature check against the sending external system's registered credential) before any further processing — the external sender resolves to an ordinary Provider Identity (Identity & Access, unchanged), not a new identity type.
- **(Recognized, not owned) Delivery Channel Adapter Layer** — the Notification Framework's existing, frozen component (ENF §4); this document explicitly acknowledges it as a sibling instance of the same pattern rather than absorbing or redefining it.

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `registerConnector(connectorId, endpoint, credentialRef)` | Integration owner → Outbound Connector Registry | Declares an external system integration. |
| `callExternal(connectorId, payload)` | Any caller (typically a Workflow Engine step) → Outbound Circuit Breaker → external system | Makes an outbound call, protected by the circuit breaker, with failures classified via EEHF. |
| `receiveWebhook(connectorId, rawPayload, signature)` | API Gateway (unchanged route) → Webhook Verification | Verifies an inbound callback's authenticity against the connector's registered credential. |
| `publishFromWebhook(envelope)` | Webhook Verification → Event Bus (unchanged `publish()`) | Translates a verified webhook into an ordinary internal event. |

## 6. Data Flow

1. **Outbound**: a caller (typically a Workflow Engine step, e.g., Marketplace's deferred payment step) calls `callExternal()` against a registered connector; the Outbound Circuit Breaker protects the call, and a classified failure (via EEHF, `err.integration.*`) is returned on trouble, exactly like any other classified error in this library.
2. **Inbound**: an external system sends a webhook to a route already exposed through the unchanged API Gateway pipeline; Webhook Verification checks its signature against the connector's registered credential before any further processing occurs.
3. A verified webhook is translated into an ordinary event via the unchanged Event Bus `publish()` — for example, resuming a paused Purchase Fulfillment Workflow instance (Marketplace §6) via the Workflow Engine's own unchanged `resumeInstance()`, triggered by a subscriber to that published event, not by any new orchestration logic in this document.
4. An unverified webhook is rejected at the Webhook Verification stage with a classified `err.integration.*` error — it never reaches internal event publication.

## 7. Design Patterns

- **Generalizing a validated pattern, not migrating an existing instance** — ENF's Delivery Channel Adapter Layer remains exactly as frozen; this document names the pattern it already represents so future integrations (starting with the payment connector Licensing/Marketplace deferred) don't have to reinvent it, mirroring how EDM generalized dependency-graph logic without touching PLM's or the Module Registry's own components (EDM §1, §7).
- **Circuit breaker, reapplied not reused** — explicitly borrows the pattern PLM's Failure Handler validated (PLM §7) for a different scope, rather than either redefining PLM's component or building an unrelated mechanism from scratch.
- **Webhooks as ordinary Gateway routes, not a second ingress** — continues the API Gateway's own discipline (API Gateway §7) that nothing reaches the platform from outside except through its unchanged pipeline.
- **External calls as ordinary steps, orchestration untouched** — an outbound call from within a workflow is exactly one more step per the Workflow Engine's existing model; this document adds no sequencing logic of its own, keeping the Workflow Engine the library's sole orchestrator (reconfirmed, ADR-EAL-023).

## 8. Security Considerations

*(Citing the Security Principles Catalog directly, per ESA's discipline.)*

- **Principle: Secrets-by-Reference** (ESA catalog) applies directly to the Outbound Connector Registry's credential references — sourced via ECF, never inline.
- **Principle: Fail-Closed Validation** (ESA catalog) applies to Webhook Verification — an unverifiable signature rejects the webhook outright, never processes it "just in case."
- **An external system's webhook-sending identity must be verified, not merely trusted by network origin** — the specific reason Webhook Verification exists as a distinct stage rather than assuming any request reaching the registered route is legitimate.
- **Outbound credentials are as sensitive as any other in this library** — no exception to the manifest/credential hygiene discipline applied throughout (PLM §8, ECF §8) for external-facing credentials specifically.

## 9. Scalability

- **Outbound call volume and reliability characteristics vary per external system** — the Outbound Circuit Breaker's thresholds should be configurable per connector (via ECF), not a single global setting, since different external systems have different latency/reliability profiles.
- **Webhook receipt inherits the API Gateway's own scalability model** — no new inbound scaling concern beyond what the Gateway already addresses (API Gateway §9).
- **Connector Registry is read-heavy, low-write** — the now-familiar asymmetry established throughout this library; connector definitions change rarely relative to call volume.

## 10. Best Practices

- Register every external integration as a named connector before any code calls out to it directly — never hardcode an external endpoint/credential inline.
- Configure circuit-breaker thresholds per connector, reflecting that external system's actual reliability characteristics.
- Always verify a webhook's signature before translating it into an internal event — never process an unverified payload "provisionally."
- When Licensing's or Marketplace's payment step is actually implemented, register it as an ordinary connector here rather than building bespoke payment-calling logic inside either of those documents' own components.

## 11. Common Pitfalls

- **Building a second inbound path for webhooks instead of routing through the API Gateway** — repeats exactly the ingress-fragmentation risk the Gateway's own document was built to prevent (API Gateway §11).
- **Treating ENF's Delivery Channel Adapter Layer as something this document redefines or migrates** — the single most important boundary to preserve; it remains exactly as frozen, only recognized as a sibling pattern instance.
- **Processing an unverified webhook "to be safe" rather than rejecting it** — violates fail-closed validation and is the most likely path to a spoofed external event being treated as legitimate.
- **Letting an outbound call's retry/circuit-breaker logic creep into multi-step orchestration** — an outbound call and its circuit breaker remain a single step's concern; sequencing multiple external calls together remains the Workflow Engine's exclusive domain.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **Build a bespoke payment connector directly inside Licensing or Marketplace** | Each document that needs an external call implements its own. | Repeats the exact per-document duplication this library has avoided since EDM; a general outbound-connector pattern serves both today and any future external integration need. |
| **Migrate ENF's Delivery Channel Adapter Layer into this document** | Absorb the existing adapter layer as part of EIF. | Violates "no redesign of approved modules"; ENF's component is frozen and correctly scoped to its own document — this document recognizes the pattern without touching the instance. |
| **A second inbound ingress path specifically for webhooks** | Build a dedicated webhook-receiving endpoint separate from the API Gateway. | Fragments external ingress exactly as the Gateway's own document was built to prevent; a webhook is simply another external route. |
| **Reuse PLM's Failure Handler/Circuit Breaker component directly for outbound calls** | Route outbound-call failure handling through PLM's existing mechanism. | PLM's component is scoped to plugin lifecycle health (ACTIVE/DEGRADED/QUARANTINED), a different concern from outbound-call reliability; reusing the *pattern* without redefining or overloading PLM's actual component preserves both documents' scope integrity. |

## 13. Migration Strategy

1. **Stand up the Outbound Connector Registry, Outbound Circuit Breaker, and Webhook Verification** as new, independently-operable components.
2. **Register the payment connector Licensing and Marketplace both deferred** as the first concrete Outbound Connector Registry entry, validating the pattern against a real, already-named need.
3. **Route the payment processor's webhook (payment confirmation) through the API Gateway as an ordinary route**, verified via Webhook Verification, and translated into an event that resumes the relevant paused Workflow Engine instance.
4. **Recognize, without modifying, ENF's existing adapter layer** as a parallel, already-operating instance of this pattern — no migration action required.
5. **Register further external integrations incrementally** as they're identified, each as an ordinary connector.

## 14. Success Criteria

- The payment connector Licensing and Marketplace both deferred is registered and demonstrably callable from an ordinary Workflow Engine step.
- Zero webhook endpoints exist outside the API Gateway's unchanged pipeline.
- Every external system resolves to an existing Provider Identity — zero new identity types introduced.
- Zero modification to ENF's Delivery Channel Adapter Layer, PLM's Failure Handler, or any other prior document's own component.
- An unverified webhook is demonstrably rejected before reaching internal event publication.

## 15. Decision Matrix

| Criterion (weight) | General outbound-connector pattern, webhooks via unchanged Gateway (recommended) | Bespoke per-document payment connector | Migrate ENF's adapter layer in | Second webhook-specific ingress | Reuse PLM's circuit breaker component directly |
|---|---|---|---|---|---|
| Closes the payment-step gap generally (High) | 5 | 3 | 3 | 3 | 3 |
| Respects "no redesign of approved modules" (ENF, PLM) (High) | 5 | 5 | 1 | 5 | 2 |
| Single inbound ingress point preserved (High) | 5 | 5 | 5 | 1 | 5 |
| Reusable for future external integrations (Medium) | 5 | 1 | 3 | 3 | 3 |
| Implementation/governance overhead (Medium, lower = better fit) | 3 | 4 | 2 | 3 | 3 |
| **Weighted outcome** | **Best overall fit** | Fails reuse/generality goal | Fails charter boundary | Fails single-ingress goal | Fails scope-integrity goal |

**Conclusion**: a general outbound-connector pattern, with webhooks received through the unchanged API Gateway and a purpose-built (pattern-reused, component-distinct) circuit breaker, is recommended. It closes the payment-step gap generally, without touching ENF's or PLM's already-frozen components or the Gateway's single-ingress model.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-025: Enterprise Integration Framework as a General Outbound-Connector Pattern, With Webhooks Received Through the Unchanged API Gateway**

- **Status**: Accepted
- **Context**: Licensing and Marketplace both named an "external payment step" as explicitly out of scope without a defined mechanism; ENF's Delivery Channel Adapter Layer already implements one instance of "calling an external system" without this library generalizing that pattern.
- **Decision**: Introduce an Outbound Connector Registry, an Outbound Circuit Breaker (applying, not reusing, PLM's already-validated circuit-breaker pattern), and Webhook Verification for inbound callbacks received as ordinary API Gateway routes. External systems resolve to existing Provider Identities. ENF's Delivery Channel Adapter Layer is explicitly recognized as an existing instance of this pattern, not migrated or redefined. **No modification to any of the twenty-four prior documents.**
- **Rationale**: The Decision Matrix (§15) shows this is the only option that closes the payment-step gap generally, for future integrations as well, while fully respecting the "no redesign of approved modules" boundary for both ENF's adapter layer and PLM's circuit-breaker component, and preserving the API Gateway's single-ingress-point model.
- **Consequences**:
  - *Positive*: Licensing's and Marketplace's deferred payment steps now have a concrete, reusable connector pattern; future external integrations don't require per-document bespoke connector logic; ENF's and PLM's existing components remain untouched.
  - *Negative*: introduces a third new component set (Registry, Circuit Breaker, Webhook Verification) alongside an implicit expectation that ENF's adapter layer and this framework will look similar without being formally unified.
  - *Neutral*: payment processing itself remains entirely undefined by this document — it defines the connector pattern, not the specific integration's business logic.
- **Alternatives rejected**: bespoke per-document connectors, migrating ENF's adapter layer, a second webhook ingress, reusing PLM's circuit breaker directly — see §12 and §15.
- **Reversibility**: Fully reversible — the new components can be decommissioned without affecting the API Gateway, ENF, PLM, or the Workflow Engine; any registered connector would need individual reimplementation if EIF were removed.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Connector Registry, Circuit Breaker, and Webhook Verification are specified at architecture level. |
| **Respect for ENF's and PLM's frozen components** | Confirmed | Pattern recognized/reapplied, not migrated or redefined. |
| **Single-ingress-point preservation** | Confirmed | Webhooks are ordinary API Gateway routes. |
| **Fills the Licensing/Marketplace payment-step gap** | Confirmed as a pattern, not as a payment implementation | The connector mechanism is ready; the actual payment processor integration remains future, separately-scoped work. |
| **Technology-agnostic validation** | Ready | No binding to a specific payment processor or external system. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Register the actual payment connector** for Licensing's and Marketplace's deferred payment steps — the concrete next action this document enables but does not itself perform.
- **Formal recognition of ENF's adapter layer as a conforming instance** — a future, lightweight documentation exercise (not a redesign) explicitly cross-referencing the two without altering either.
- **Outbound rate limiting** — extending the Outbound Circuit Breaker with rate-limiting for external systems with their own usage quotas, building on ECF's existing configuration model.
- **Connector health surfaced via Observability** — publishing connector-level health/circuit-breaker-state signals into EOA's Metrics Store, exactly as any other emitter, for operator visibility.

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-025.
