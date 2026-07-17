---
title: Enterprise Event Bus
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Event Bus

## 1. Problem Statement

This library already contains a great deal of "event" vocabulary — PLM's lifecycle events, the Module Registry's registration/ownership events, ESR's health signals, ECF's change audit log, EFF's assignment events, EEHF's error signals, and EOA's Common Event Envelope that unifies all of them for storage and query. It is essential to be precise about what the Enterprise Event Bus (EEB) is *not*, before defining what it is:

- **[Observability Architecture](observability-architecture.md)** (EOA, ADR-EAL-010) is a **read/query-oriented** sink: existing emitters optionally wrap their output in the Common Event Envelope so an *operator* can later query it. Nothing in EOA causes a *subscriber's business logic* to run in response to an event — it is a destination for investigation, not a dispatch mechanism.
- **[Workflow Engine](workflow-engine.md)** (EWE, ADR-EAL-013) explicitly rejected choreography (event-driven, no central engine) as its internal step-sequencing model (Workflow Engine §12), in favor of a central orchestrator with durable state — a deliberate, considered choice for *within one workflow instance's* control flow.

Neither covers a genuine, distinct need: **a decoupled publish/subscribe mechanism where publishing an event actually causes one or more independent subscribers' business logic to execute**, without the publisher knowing or caring who is listening. This is the classic integration-decoupling problem — e.g., "when a research finding is Published, notify any interested module" or "when a plugin enters QUARANTINED, notify an external on-call system" — and it is a fundamentally different consumption pattern from both EOA (query-after-the-fact) and EWE (centrally-orchestrated control flow).

The Enterprise Event Bus defines topics as versioned event schemas, a publish/subscribe broker with defined delivery guarantees, and a subscriber registry — reusing EOA's envelope format, EVCS's versioning discipline, and every other applicable Foundation/Platform mechanism, rather than duplicating them.

### Reuse map

| Need | Reused from | How |
|---|---|---|
| Event envelope shape (timestamp, source identity, event type, correlation ID, payload) | [Observability Architecture](observability-architecture.md) (ADR-EAL-010) | EEB dispatches events using the **same Common Event Envelope**, rather than inventing a second wrapper format — a subscriber and EOA's Telemetry Pipeline can both receive the identical envelope shape for different purposes (dispatch vs. query). |
| Correlation across a dispatched event's downstream effects | [Error Handling Framework](error-handling-framework.md) (ADR-EAL-009) | The envelope's correlation ID (EEHF's, unchanged) propagates from publisher to every subscriber's own resulting work. |
| Topic/event schema versioning and breaking-change classification | [Version Compatibility Strategy](version-compatibility-strategy.md) (ADR-EAL-008) | A topic's payload schema changes are classified via EVCS before subscribers are expected to handle a new version. |
| Gradual migration of subscribers to a new topic schema version | [Feature Flag Framework](feature-flag-framework.md) (ADR-EAL-006) | Rolling a topic's consumers over to a new schema version in stages reuses EFF's rollout/kill-switch mechanism. |
| Subscriber worker instance tracking | [Service Registry](service-registry.md) (ADR-EAL-004) | A subscriber's running consumer instance registers with ESR like any other service instance. |
| Delivery failure classification | [Error Handling Framework](error-handling-framework.md) (ADR-EAL-009) | Undeliverable/failed dispatch attempts classify into EEHF's existing taxonomy with new `err.eventbus.*` codes — no new top-level class. |
| Subscriber-side configuration (retry policy, batch size) | [Configuration Framework](configuration-framework.md) (ADR-EAL-005) | Layered exactly per ADR-EAL-005; no separate subscriber-config mechanism. |
| A subscriber's declared reliance on a topic existing | [Dependency Management](dependency-management.md) (ADR-EAL-007) | Optionally expressed as an EDM dependency edge (subscriber provider → topic), enabling impact analysis ("what breaks if this topic is removed") via EDM's existing `getDependents()`. |

**Scope boundary:** this document does not modify any of the thirteen prior documents. It introduces new components strictly for topic definition, decoupled dispatch, and subscription management.

## 2. Goals

| Goal | Description |
|---|---|
| **Decoupled publish/subscribe** | A publisher emits an event without knowing which, or how many, subscribers exist; subscribers register interest in a topic independently of the publisher's own deployment. |
| **Versioned topic schemas** | A topic's event payload shape is a versioned artifact, classified via EVCS on change, not an implicit, undocumented contract. |
| **Defined delivery guarantees** | Every topic states its delivery semantics (at-least-once, ordering within a partition key, or best-effort) explicitly, so subscribers can build correct handling logic. |
| **Reuse of the Common Event Envelope** | Dispatched events use the exact same envelope shape EOA already defined — no second, competing event-wrapper format in this library. |
| **Clear boundary from EOA and the Workflow Engine** | The Bus is for decoupled, subscriber-triggered business logic; it is not a query/investigation sink (EOA's role) and not a replacement for the Workflow Engine's intentionally-centralized internal step orchestration. |
| **Failed-delivery visibility** | Undeliverable events are classified (EEHF) and held in a dead-letter path rather than silently dropped. |

**Non-goals**: EEB is not a second observability/query system (EOA remains the query surface for historical event investigation); it is not a workflow orchestrator (EWE remains the model for centrally-sequenced, stateful multi-step execution); and it does not grant a subscriber any elevated access to a publisher's own data beyond what the published event payload contains.

## 3. Architecture

```
   ┌───────────────────────────┐
   │   Publisher (any module,     │  ← publishes using the same Common
   │   plugin, or Foundation/     │    Event Envelope EOA already defined
   │   Platform emitter)          │
   └─────────────┬─────────────┘
                 │ publish(topic, envelope)
   ┌─────────────▼─────────────┐
   │   Topic & Schema Registry     │  ← new: versioned topic definitions,
   │   (new)                       │    classified via EVCS on change
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐
   │   Publish/Subscribe Broker    │  ← new: delivers to all current
   │   (new)                       │    subscribers per topic's delivery
   └─────────────┬─────────────┘    guarantee
                 │
   ┌─────────────▼─────────────┐
   │   Subscriber Registry         │  ← new: who is subscribed to what,
   │   (new)                       │    tracked via ESR for live instances
   └─────────────┬─────────────┘
                 │
       ┌─────────┴─────────┐
       │                     │
┌──────▼───────┐   ┌─────────▼────────┐
│ Subscriber A    │   │ Dead-Letter Path   │  ← failed deliveries, classified
│ (independent     │   │ (new)               │    via EEHF, held for inspection
│  business logic) │   │                     │
└───────────────┘   └───────────────────┘

   EOA's Telemetry Pipeline may separately ingest the same envelope for
   query/investigation purposes — a read-only consumer alongside any
   business-logic subscriber, not a special case.
```

## 4. Components

- **Topic & Schema Registry** *(new)* — stores each topic's identity, versioned payload schema, and declared delivery guarantee (at-least-once, ordered-by-key, or best-effort). Schema changes are classified via EVCS before a new version is considered compatible with existing subscribers.
- **Publish/Subscribe Broker** *(new)* — accepts a `publish()` call carrying a Common-Event-Envelope-wrapped payload and dispatches it to every current subscriber of that topic, honoring the topic's declared delivery guarantee.
- **Subscriber Registry** *(new)* — tracks which providers (modules/plugins) are subscribed to which topics, and — for a subscriber's own live consumer instance — defers to ESR for instance/health tracking rather than duplicating it.
- **Dead-Letter Path** *(new)* — holds events that could not be delivered after the topic's defined retry policy is exhausted, classified via EEHF's existing taxonomy with `err.eventbus.*` codes, for later inspection or manual replay rather than silent loss.

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `defineTopic(topicId, schema, deliveryGuarantee)` | Topic owner → Topic & Schema Registry | Declares a new, versioned topic. |
| `publish(topicId, envelope)` | Any publisher → Publish/Subscribe Broker | Emits an event; the publisher has no knowledge of, or dependency on, current subscriber count. |
| `subscribe(topicId, subscriberProviderId)` | Subscriber (module/plugin) → Subscriber Registry | Registers interest in a topic; delivery to this subscriber begins on the next dispatch. |
| `unsubscribe(topicId, subscriberProviderId)` | Subscriber → Subscriber Registry | Removes a subscription; no further deliveries. |
| `inspectDeadLetter(topicId, timeRange)` / `replay(eventId)` | Operator → Dead-Letter Path | Inspects and, where appropriate, manually replays a failed delivery after resolving the underlying cause. |

## 6. Data Flow

1. A topic owner calls `defineTopic()`, declaring its schema and delivery guarantee; schema changes on an existing topic are classified via EVCS before being considered a compatible evolution.
2. A subscriber calls `subscribe()`, registering its provider identity against the topic; its own running consumer instance is tracked via ESR exactly as any other service instance.
3. A publisher — which may be an ordinary module/plugin, or one of the Foundation/Platform documents' own existing emitters (PLM lifecycle events, the Research Platform's finding-published transition, etc.) choosing to also publish to the Bus — calls `publish()` with a Common-Event-Envelope-wrapped payload.
4. The Publish/Subscribe Broker dispatches the event to every current subscriber per the topic's declared delivery guarantee, propagating the envelope's correlation ID unchanged.
5. A subscriber's own business logic executes in response — this is the defining characteristic distinguishing EEB from EOA, where no comparable subscriber-side execution occurs.
6. A delivery that fails after the topic's retry policy is exhausted is classified via EEHF and routed to the Dead-Letter Path rather than dropped, available for operator inspection and (after remediation) `replay()`.
7. Independently, and without any special-casing, EOA's Telemetry Pipeline may also ingest the same envelope for query/investigation purposes — the Bus does not need to know or coordinate with EOA's ingestion; both are simply consumers of the same envelope-shaped event, for different purposes (dispatch vs. query).

## 7. Design Patterns

- **Publish/subscribe (pub/sub) messaging** — the standard decoupling pattern: publishers and subscribers depend only on a shared topic contract, never on each other directly.
- **Dead-letter queue** — undeliverable messages are held, not dropped, mirroring the same "don't silently lose the signal" discipline already applied to EEHF's classified errors and PLM's rejection diagnostics.
- **Shared envelope, divergent consumption** — reusing EOA's Common Event Envelope for a genuinely different purpose (subscriber dispatch vs. operator query) is the clearest instance yet in this library of the "one artifact, multiple non-conflicting consumers" pattern already seen with EDM's dependency graph and EEHF's correlation ID.
- **Explicit rejection of choreography for internal orchestration, explicit adoption of it for cross-boundary decoupling** — directly resolves the tension the Workflow Engine document raised: choreography is the right pattern *between* independently-owned providers reacting to a shared topic, and the wrong pattern *within* one workflow instance's own step sequencing (Workflow Engine §12) — this document and EWE are consistent, not contradictory, because they answer different questions.

## 8. Security Considerations

- **Subscription is not automatically broad read access** — subscribing to a topic grants visibility only into that topic's declared payload schema, not into the publisher's other internal data; topic schemas should be designed with this exposure boundary in mind from `defineTopic()` onward.
- **Publisher identity should be verifiable** — the Broker should be able to attribute a published event to an authenticated provider identity, preventing an unauthorized source from publishing fabricated events onto a topic other subscribers trust.
- **Dead-letter inspection access should match the topic's own sensitivity** — consistent with EOA's strictest-applicable-source-policy principle (EOA §8), the Dead-Letter Path's access control should be at least as strict as the originating topic's.
- **No secrets in topic payloads** — consistent with the manifest-hygiene pattern repeated throughout this library, event payloads carry only the data legitimately needed by subscribers, never credentials.

## 9. Scalability

- **Publish volume can be high; the Broker must not become a publish-time bottleneck** — `publish()` should be effectively fire-and-forget from the publisher's perspective, mirroring EOA's own non-blocking-ingestion discipline (EOA §9, §10) — a slow or unavailable Broker must never block a publisher's own core operation.
- **Subscriber count per topic is independent of publish volume** — a topic with many subscribers multiplies delivery fan-out, not publish cost; the Broker's dispatch tier should scale independently of the publish-intake tier.
- **Dead-letter volume should be a small fraction of total traffic** — as with EEHF's Error Signal Feed (EEHF §9), the Dead-Letter Path should be capacity-planned against expected failure rate, not total topic volume.

## 10. Best Practices

- Design a topic's schema for the narrowest payload that serves subscribers' actual needs — broader payloads mean broader implicit access, per §8.
- Declare a topic's delivery guarantee explicitly and choose it deliberately (at-least-once with idempotent subscriber handling is usually safer to build against than assuming exactly-once).
- Treat `publish()` as fire-and-forget from the publisher's perspective; never let publisher availability become coupled to Broker or subscriber availability.
- Reuse EOA's Common Event Envelope without modification for anything published on the Bus — a second envelope format would fragment the one consistency win EOA already established.

## 11. Common Pitfalls

- **Using the Event Bus as a second observability sink** — if operators start querying the Bus directly for historical investigation instead of using EOA's Unified Query Interface, the two systems' purposes blur; EOA remains the query surface, the Bus remains the dispatch surface.
- **Using the Event Bus for internal workflow step sequencing** — reintroduces the exact choreography-vs-orchestration tension the Workflow Engine document already resolved in favor of central orchestration for that specific, in-instance concern (Workflow Engine §12); the Bus is for cross-boundary decoupling between independently-owned providers, not for one workflow's own internal control flow.
- **Silently dropping undeliverable events instead of dead-lettering them** — defeats the failed-delivery-visibility goal and can hide a broken subscriber for an extended period.
- **Publishers blocking on subscriber processing** — violates the fire-and-forget discipline (§9, §10) and couples the publisher's own availability to every subscriber's.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **Extend EOA's Telemetry Pipeline into a pub/sub bus** | Add subscriber-dispatch capability directly to EOA's Ingestion Gateway. | Would conflate EOA's deliberately read/query-only scope (EOA §2 non-goals) with an active dispatch mechanism, the exact scope distortion this library has repeatedly avoided (e.g., keeping ESR separate from ECR). |
| **Use the Workflow Engine's step model for cross-provider notification** | Model "notify subscribers" as workflow steps instead of a separate bus. | Conflates centrally-orchestrated, single-instance step sequencing (EWE's actual scope) with decoupled, multi-subscriber, publisher-agnostic dispatch — a different problem with a different natural solution shape. |
| **No event bus; direct point-to-point calls between providers** | Providers call each other directly when one needs to notify another. | Reintroduces tight coupling between providers that this document exists to remove; scales poorly as the number of interested parties grows, since every new subscriber requires a publisher-side code change. |
| **Exactly-once delivery as the only supported guarantee** | Mandate the strongest possible delivery semantic for every topic. | Exactly-once delivery is materially more complex and costly to guarantee correctly across arbitrary subscribers; at-least-once with idempotent subscriber handling is the more broadly achievable default, with stronger guarantees available per-topic where genuinely justified. |

## 13. Migration Strategy

1. **Stand up the Topic & Schema Registry, Publish/Subscribe Broker, Subscriber Registry, and Dead-Letter Path** as new, independently-operable components.
2. **Define the first topic using the existing Common Event Envelope** with no schema deviation, validating that reuse holds before any topic-specific customization is considered.
3. **Onboard a small number of publisher/subscriber pairs first** (e.g., the Research Platform's finding-published transition notifying one interested subscriber) before broader adoption.
4. **Establish dead-letter monitoring and a replay runbook** before any topic is considered production-critical.
5. **Use EFF for any topic schema migration** requiring a staged subscriber cutover, rather than a hard cutover for all subscribers simultaneously.

## 14. Success Criteria

- 100% of published events use the unmodified Common Event Envelope — no second envelope format introduced.
- Every topic has a declared, documented delivery guarantee that subscriber implementations can rely on.
- Zero events silently dropped on delivery failure — all failed deliveries reach the Dead-Letter Path with a classified `err.eventbus.*` code.
- At least one cross-provider publish/subscribe relationship (e.g., Research Platform → an interested subscriber) is demonstrated end-to-end without the publisher requiring any code change to add a second subscriber later.
- Zero instances of the Event Bus being used for a workflow instance's own internal step sequencing.

## 15. Decision Matrix

| Criterion (weight) | Dedicated pub/sub bus reusing EOA's envelope (recommended) | Extend EOA into a bus | Use Workflow Engine for cross-provider notification | Direct point-to-point calls | Exactly-once only |
|---|---|---|---|---|---|
| Decoupled publish/subscribe (High) | 5 | 3 | 2 | 1 | 5 |
| Clean boundary from EOA (High) | 5 | 1 | 4 | 4 | 4 |
| Clean boundary from Workflow Engine (High) | 5 | 4 | 1 | 4 | 4 |
| Reuse of existing envelope format (High) | 5 | 5 | 3 | 2 | 4 |
| Failed-delivery visibility (Medium) | 5 | 3 | 3 | 2 | 4 |
| Achievable delivery-guarantee complexity (Medium, lower = better fit) | 4 | 3 | 3 | 4 | 1 |
| **Weighted outcome** | **Best overall fit** | Fails EOA-boundary goal | Fails Workflow Engine-boundary goal | Fails decoupling goal | Overly complex default |

**Conclusion**: a dedicated publish/subscribe bus, reusing EOA's Common Event Envelope and defaulting to at-least-once delivery with idempotent-subscriber expectations, is recommended. It is the only option that achieves genuine decoupling while keeping clean, explicit boundaries from both EOA and the Workflow Engine.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-014: Enterprise Event Bus as a Decoupled Pub/Sub Layer, Distinct from Observability and Workflow Orchestration**

- **Status**: Accepted
- **Context**: No prior document provides genuine decoupled publish/subscribe dispatch — EOA is a read/query sink and the Workflow Engine deliberately centralizes its own internal step orchestration; both boundaries must be preserved explicitly to avoid scope confusion.
- **Decision**: Introduce a Topic & Schema Registry, Publish/Subscribe Broker, Subscriber Registry, and Dead-Letter Path. Dispatched events reuse EOA's Common Event Envelope unchanged; topic schema versioning reuses EVCS; delivery failures classify into EEHF's existing taxonomy via new `err.eventbus.*` codes; subscriber consumer instances are tracked via ESR. **No modification to any of the thirteen prior documents**, including no change to EOA's read-only scope or the Workflow Engine's orchestration model.
- **Rationale**: The Decision Matrix (§15) shows this is the only option achieving genuine decoupling while preserving both the EOA and Workflow Engine boundaries; extending either existing system would repeat a scope-distortion pattern this library has consistently avoided.
- **Consequences**:
  - *Positive*: providers can be notified of relevant events without publisher-side awareness of subscriber count or identity; failed deliveries remain visible rather than silently lost; the shared envelope format keeps this library's one-envelope discipline intact.
  - *Negative*: introduces a fourth new Platform-phase component set; teams must understand the (now three-way) distinction between EOA (query), EWE (orchestration), and EEB (decoupled dispatch).
  - *Neutral*: at-least-once is the default delivery guarantee; stronger guarantees are available per-topic but not mandated.
- **Alternatives rejected**: extending EOA, using the Workflow Engine for cross-provider notification, direct point-to-point calls, exactly-once-only — see §12 and §15.
- **Reversibility**: Fully reversible — publishers and subscribers could revert to direct point-to-point calls if the Bus were decommissioned, at the cost of reintroducing the coupling this document removes.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Topic/Schema Registry, Broker, Subscriber Registry, and Dead-Letter Path are specified at architecture level. |
| **Boundary with EOA** | Confirmed explicit | §1, §7, §11 all address the query-vs-dispatch distinction directly; both consume the same envelope for different purposes. |
| **Boundary with Workflow Engine** | Confirmed explicit | §7, §11, §12 directly resolve the choreography-vs-orchestration question raised (and answered differently, for a different scope) in the Workflow Engine document. |
| **Technology-agnostic validation** | Ready | No binding to a specific message broker technology. |
| **Security model maturity** | Ready for design review | Subscription-scope and publisher-identity verification are addressed (§8); no formal threat model performed. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Schema registry validation at publish time** — rejecting a `publish()` call whose payload doesn't conform to the topic's declared schema, rather than relying solely on subscriber-side validation.
- **Topic-level access policy integration** — a future, more granular authorization model for subscription approval, beyond the basic identity-verification model described here.
- **Ordered, partitioned delivery as a first-class topic option** — formalizing partition-key-based ordering guarantees for topics that need them, building on the delivery-guarantee declaration already in the Topic & Schema Registry.
- **EDM-integrated impact analysis for topic removal** — fully wiring the optional subscriber→topic EDM dependency edge (§1 reuse map) into a standard pre-removal check, rather than leaving it as an optional declaration.

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-014.
