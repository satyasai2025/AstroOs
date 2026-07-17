---
title: Enterprise Notification Framework
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Notification Framework

## 1. Problem Statement

The [Event Bus](event-bus.md) (EEB, ADR-EAL-014) solved decoupled dispatch **between providers** — a subscriber is a module or plugin whose business logic executes in response to an event. It explicitly does not address a different, human-facing problem: **telling an actual person something, through a channel they've chosen (email, SMS, push, in-app), respecting their preferences (opt-in/opt-out, quiet hours, digest batching), and tracking whether the message was actually delivered.**

This is a genuinely distinct need from every prior document:

- EEB's subscribers are providers executing code; a notification's "subscriber" is a human recipient with communication preferences no provider has.
- No document models a **delivery channel** (email, SMS, push, in-app) as a pluggable adapter, or a **recipient's preference** (which channels, how often, when) as a first-class, queryable record.
- No document tracks **delivery outcome** (sent, delivered, bounced, opened) as distinct from EEHF's per-call error classification — a notification can be successfully "sent" by this system yet still bounce at the channel provider, a failure mode with no analog elsewhere in this library.

The Enterprise Notification Framework (ENF) defines templates, recipient preferences, channel adapters, and delivery tracking — and is, itself, simply an ordinary subscriber to the Event Bus for anything that triggers a notification, rather than inventing a second event-ingestion mechanism.

### Reuse map

| Need | Reused from | How |
|---|---|---|
| Being triggered by a system event (e.g., "research finding published," "plugin quarantined") | [Event Bus](event-bus.md) (ADR-EAL-014) | ENF's Trigger Mapping is an ordinary EEB subscriber — it calls `subscribe()` on relevant topics exactly like any other provider; no second event-ingestion path. |
| Notification template versioning and breaking-change classification | [Version Compatibility Strategy](version-compatibility-strategy.md) (ADR-EAL-008) | A template's variable contract is classified via EVCS before a revised version is considered compatible with existing trigger bindings. |
| Gradual rollout of a revised template or new channel | [Feature Flag Framework](feature-flag-framework.md) (ADR-EAL-006) | Shifting a subset of notifications to a new template/channel reuses EFF's rollout/kill-switch mechanism. |
| Channel provider credentials (email/SMS/push gateway API keys) | [Configuration Framework](configuration-framework.md) (ADR-EAL-005) | Sourced via ECF's secrets-by-reference mechanism, never inline. |
| Classifying a failed send attempt | [Error Handling Framework](error-handling-framework.md) (ADR-EAL-009) | Maps into EEHF's existing closed taxonomy with new `err.notification.*` codes — no new top-level class. |
| Optional AI-assisted notification wording | [AI Platform Architecture](ai-platform-architecture.md) (ADR-EAL-011) | Where a notification's body is phrased with AI assistance, that remains an ordinary AI-backed capability under the unchanged orchestration-only principle — AI may help word a message, but the decision of *whether*, *to whom*, and *through which channel* to send is always deterministic policy, never AI-decided. |
| Delivery outcome visibility for operators | [Observability Architecture](observability-architecture.md) (ADR-EAL-010) | The Delivery Ledger's entries may optionally be wrapped in EOA's Common Event Envelope and ingested for query, exactly as any other emitter's data. |

**Scope boundary:** this document does not modify any of the fourteen prior documents. New components are scoped strictly to templates, recipient preferences, channel adapters, and delivery tracking.

## 2. Goals

| Goal | Description |
|---|---|
| **Versioned, channel-aware templates** | A notification template's content and variable contract are versioned artifacts, classified via EVCS on change. |
| **Recipient preference as a first-class record** | Channel opt-in/out, quiet hours, and digest-frequency preferences are queryable and enforced before any send. |
| **Pluggable delivery channels** | Email, SMS, push, and in-app delivery are adapters behind a common interface, so adding a channel doesn't require touching trigger/template logic. |
| **Delivery outcome tracking** | Every notification's send attempt and (where the channel reports it) delivery/bounce/open status is recorded, distinct from EEHF's per-call error classification. |
| **Reuse of the Event Bus for triggering** | ENF never re-implements event ingestion; it is an ordinary EEB subscriber. |
| **AI limited to wording assistance, never to the send decision** | Consistent, unmodified application of ADR-EAL-011's orchestration-only principle to notification content. |

**Non-goals**: ENF is not a marketing/campaign-management platform; it does not replace the Event Bus for provider-to-provider dispatch; and it does not let an AI-backed capability decide whether, to whom, or through which channel a notification is sent — those are deterministic policy decisions.

## 3. Architecture

```
   ┌───────────────────────────┐
   │   Event Bus (EEB)             │  ← ENF is an ordinary subscriber
   └─────────────┬─────────────┘
                 │ subscribe(topic) / dispatched event
   ┌─────────────▼─────────────┐
   │   Trigger Mapping             │  ← new: topic → template binding
   │   (new)                       │
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Notification Template       │◄──────┤ Version Compatibility        │
   │   Registry (new)              │        │ Strategy (EVCS)               │
   └─────────────┬─────────────┘        └───────────────────────────┘
                 │
   ┌─────────────▼─────────────┐
   │   Recipient Preference        │  ← new: channel opt-in/out,
   │   Registry (new)              │    quiet hours, digest frequency
   └─────────────┬─────────────┘
                 │ (preferences checked before send)
   ┌─────────────▼─────────────┐
   │   Delivery Channel Adapter     │  ← new: email/SMS/push/in-app
   │   Layer (new)                  │    behind a common interface
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Delivery Ledger (new)        │──────►│ Observability Architecture   │
   │                                │        │ (EOA) — optional ingestion    │
   └───────────────────────────┘        └───────────────────────────┘
```

## 4. Components

- **Trigger Mapping** *(new)* — binds an Event Bus topic to a notification template; on receiving a dispatched event (as an ordinary EEB subscriber), determines which template and which recipients apply.
- **Notification Template Registry** *(new)* — stores versioned, channel-aware templates (subject/body per channel, with a declared variable contract); changes are classified via EVCS before a revised template is considered compatible with existing trigger bindings.
- **Recipient Preference Registry** *(new)* — the queryable record of each recipient's channel opt-in/out status, quiet hours, and digest-frequency preference; consulted before every send.
- **Delivery Channel Adapter Layer** *(new)* — a common interface behind which email, SMS, push, and in-app delivery mechanisms are implemented as independent adapters; adding a new channel means adding an adapter, not touching trigger/template logic.
- **Delivery Ledger** *(new)* — records each notification's send attempt and, where the channel reports it, delivery/bounce/open status — a distinct concept from EEHF's per-call error classification, since a "successfully sent" notification can still fail to reach the recipient at the channel level.

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `bindTrigger(topicId, templateId, recipientResolution)` | Notification owner → Trigger Mapping | Declares that a topic's dispatched events should produce a notification using a given template, with a rule for resolving the actual recipient(s) from the event payload. |
| `defineTemplate(templateId, channelVariants, variableSchema)` | Template owner → Notification Template Registry | Declares a versioned, channel-aware template. |
| `setPreference(recipientId, channel, optIn, quietHours, digestFrequency)` | Recipient (or their own preference UI) → Recipient Preference Registry | Records a recipient's delivery preferences. |
| `send(recipientId, templateId, variables)` | Trigger Mapping → Delivery Channel Adapter Layer | Checks recipient preference, renders the appropriate channel variant, and dispatches through the matching adapter. |
| `recordDeliveryOutcome(notificationId, status)` | Delivery Channel Adapter (or channel provider callback) → Delivery Ledger | Records send/delivered/bounced/opened status as it becomes known. |

## 6. Data Flow

1. An event is dispatched on the Event Bus (per EEB, unchanged); the Trigger Mapping, subscribed like any other provider, receives it.
2. The Trigger Mapping resolves which template and which recipient(s) apply, based on its `bindTrigger()` declaration and the event's payload.
3. Before calling `send()`, the Recipient Preference Registry is consulted — a recipient who has opted out of the relevant channel, is within quiet hours, or is due for the next scheduled digest rather than an immediate send, does not receive an immediate message.
4. For an eligible recipient, `send()` renders the channel-appropriate template variant (with variables bound from the event payload) and dispatches through the matching Delivery Channel Adapter.
5. The adapter's own send attempt is recorded in the Delivery Ledger; where the underlying channel provider reports delivery/bounce/open status asynchronously, `recordDeliveryOutcome()` updates the ledger entry accordingly.
6. A failed send (channel provider error, invalid recipient address) is classified via EEHF's existing taxonomy with an `err.notification.*` code — distinct from a *bounce*, which is a channel-level outcome recorded in the Delivery Ledger, not an EEHF-classified call failure, since the `send()` call itself may have succeeded even though the message ultimately bounced.
7. Optionally, Delivery Ledger entries are wrapped in EOA's Common Event Envelope and ingested for operator query, exactly as any other emitter's output.

## 7. Design Patterns

- **Adapter pattern for delivery channels** — the Delivery Channel Adapter Layer is the standard adapter pattern, directly analogous to the Model Gateway's provider abstraction in the AI Platform Architecture (AI Platform §7) — channel-specific detail is isolated behind a common interface.
- **Preference-gated delivery** — checking recipient preference *before* attempting delivery, not after, avoiding wasted sends and respecting opt-out as an actual precondition rather than a post-hoc filter.
- **Delivery outcome as a distinct concept from call success** — recognizing that "the send API call succeeded" and "the message was actually delivered" are different facts, tracked separately in the Delivery Ledger rather than conflated into a single success/failure signal.
- **Ordinary subscriber, not a second ingestion path** — the Trigger Mapping's use of EEB's existing `subscribe()` continues the reuse discipline established since EDM: no new event-ingestion mechanism is built when an existing one already fits.

## 8. Security Considerations

- **Recipient contact information is sensitive** — the Recipient Preference Registry and any resolved recipient address/contact detail should be access-scoped consistently with this library's general data-minimization principle, and never logged in plaintext in the Delivery Ledger beyond what's operationally necessary.
- **Channel provider credentials via ECF's secrets-by-reference** — no new credential-handling mechanism; email/SMS/push gateway API keys are sourced exactly as any other secret in this library.
- **Preference changes should be self-service and audited** — a recipient changing their own opt-in/out status should be attributable and logged, consistent with the audit-trail discipline established for configuration changes (ECF §4, §8).
- **Template content should not leak sensitive event payload data unintentionally** — a template's variable contract (§4) should be deliberately scoped to what's appropriate for the recipient to see, not a raw dump of the triggering event's full payload.

## 9. Scalability

- **Delivery volume can spike with event volume** — because triggers are ordinary EEB subscribers, a burst of dispatched events (e.g., many plugins entering DEGRADED simultaneously) could generate a corresponding burst of notification sends; digest batching (a declared recipient preference, §4) is one mechanism, but the Adapter Layer itself should also be designed for burst tolerance rather than assuming steady-state volume.
- **Preference lookups are read-heavy relative to preference changes** — mirrors the read/write asymmetry established throughout this library (Module Registry §9, ECF §9); the Recipient Preference Registry's read path should be optimized independently of how often preferences actually change.
- **Delivery Ledger write volume scales with total notification volume, not just failures** — unlike EEHF's Error Signal Feed (failure-rate-scaled) or EOA's optional ingestion, every send — successful or not — produces a ledger entry, making this the highest-write-volume new component in this document.

## 10. Best Practices

- Always check recipient preference before attempting a send — never send-then-filter.
- Version every template from its first release and classify changes via EVCS before assuming a trigger binding still produces a compatible message.
- Keep the Delivery Ledger's distinction between "send attempted," "delivered," "bounced," and "opened" explicit — collapsing these into one status loses operationally important information.
- Scope a template's variable contract narrowly to what the recipient should actually see, not the triggering event's entire payload.

## 11. Common Pitfalls

- **Letting an AI-backed capability decide whether or to whom to send a notification** — directly violates ADR-EAL-011's orchestration-only principle; AI assistance is limited to wording a template's content, never the send decision itself.
- **Treating a successful `send()` call as proof of delivery** — conflates call success with delivery outcome, the exact distinction §6/§7 are structured to preserve; a channel-level bounce must still be recorded even though the API call succeeded.
- **Sending immediately regardless of quiet-hours/digest preference** — undermines the recipient-preference goal and risks recipient frustration/opt-out entirely.
- **Building a second event-ingestion mechanism instead of subscribing to the Event Bus** — repeats the exact duplication this library has consistently avoided since EDM; the Trigger Mapping must be an ordinary EEB subscriber, not a parallel listener.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **Have each provider send notifications directly** | Every module/plugin that wants to notify a human implements its own email/SMS logic. | Fails template consistency, recipient-preference enforcement, and delivery tracking outright; the status quo this document replaces. |
| **Build a second, ENF-specific event listener instead of subscribing to the Event Bus** | ENF ingests events through its own dedicated mechanism rather than EEB's `subscribe()`. | Directly duplicates EEB's already-solved decoupled-dispatch capability, the exact "reuse before creating" violation this library is structured to avoid. |
| **Skip recipient preference; send every triggered notification immediately** | No opt-out, quiet hours, or digest batching. | Fails the recipient-preference goal outright and risks recipient harm/opt-out at the channel-provider level (e.g., spam complaints), a real operational risk. |
| **Let AI generate and send notifications autonomously** | An AI-backed capability decides content and triggers delivery without a deterministic policy gate. | Directly violates the confirmed ADR-EAL-011 principle; also removes the auditable, deterministic policy trail this document's Trigger Mapping and Recipient Preference checks are designed to provide. |

## 13. Migration Strategy

1. **Stand up the Trigger Mapping, Notification Template Registry, Recipient Preference Registry, Delivery Channel Adapter Layer, and Delivery Ledger** as new, independently-operable components.
2. **Implement one delivery channel adapter first** (e.g., email), validating the full trigger → template → preference → send → ledger path before adding additional channels.
3. **Bind the first trigger to an existing Event Bus topic** already in production use (e.g., the Research Platform's finding-published transition, if it publishes to EEB) rather than inventing a new topic solely for this migration.
4. **Require preference-registry consultation from the first send onward** — never launch with an unconditional-send path that preference-gating is retrofitted onto later.
5. **Add additional channel adapters incrementally**, each validated independently against the same Adapter Layer interface.

## 14. Success Criteria

- 100% of notification triggers are ordinary Event Bus subscriptions — zero parallel event-ingestion mechanisms.
- Every send checks recipient preference before dispatch; zero sends bypass an opted-out or quiet-hours-restricted preference.
- Delivery Ledger entries distinguish send-attempted from delivered/bounced/opened for every channel that reports such status.
- Zero AI-backed capability observed making a send/recipient/channel decision; AI involvement, where present, is limited to content wording.
- Zero new top-level EEHF error classes introduced; all send failures classify into existing classes with `err.notification.*` codes.

## 15. Decision Matrix

| Criterion (weight) | Dedicated ENF as an EEB subscriber, full reuse (recommended) | Each provider sends directly | Second, ENF-specific event listener | No recipient preference gating | AI decides send/content/recipient |
|---|---|---|---|---|---|
| Template consistency and versioning (High) | 5 | 1 | 4 | 4 | 3 |
| Recipient preference enforcement (High) | 5 | 1 | 4 | 1 | 3 |
| Reuse of Event Bus for triggering (High) | 5 | 2 | 1 | 5 | 4 |
| Delivery outcome tracking (Medium) | 5 | 1 | 3 | 3 | 2 |
| Respects ADR-EAL-011 orchestration-only principle (High) | 5 | 5 | 5 | 5 | 1 |
| Implementation/governance overhead (Medium, lower = better fit) | 3 | 4 | 3 | 4 | 3 |
| **Weighted outcome** | **Best overall fit** | Fails consistency/preference goals | Fails reuse principle | Fails preference goal | Fails ADR-EAL-011 |

**Conclusion**: a dedicated Notification Framework, subscribing to the Event Bus like any other provider and enforcing recipient preference before every send, is recommended. It is the only option meeting the template, preference, delivery-tracking, and reuse goals simultaneously while fully preserving the AI orchestration-only principle.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-015: Enterprise Notification Framework as an Event-Bus-Subscribing, Preference-Gated Delivery Layer**

- **Status**: Accepted
- **Context**: No prior document addresses human-facing notification delivery — channel adapters, recipient preference, and delivery outcome tracking are all needs distinct from the Event Bus's provider-to-provider decoupled dispatch.
- **Decision**: Introduce a Trigger Mapping (an ordinary EEB subscriber), Notification Template Registry, Recipient Preference Registry, Delivery Channel Adapter Layer, and Delivery Ledger. Templates version via EVCS; rollout reuses EFF; channel credentials source via ECF; send failures classify via EEHF's existing taxonomy with new `err.notification.*` codes; optional AI-assisted content wording remains bound by ADR-EAL-011's orchestration-only principle, never deciding whether/to whom/through which channel to send. **No modification to any of the fourteen prior documents.**
- **Rationale**: The Decision Matrix (§15) shows this is the only option meeting template consistency, preference enforcement, delivery tracking, and full reuse of the Event Bus simultaneously, while keeping the AI orchestration-only principle intact for notification content.
- **Consequences**:
  - *Positive*: recipients get consistent, preference-respecting notifications across channels; delivery outcomes are tracked distinctly from call-level success; the Event Bus's decoupled-dispatch investment is directly reused rather than duplicated.
  - *Negative*: introduces five new components; each new delivery channel requires its own adapter implementation.
  - *Neutral*: AI-assisted content wording is optional and, where used, strictly bounded to phrasing — never the send decision.
- **Alternatives rejected**: direct per-provider sending, a second event-ingestion mechanism, no preference gating, AI-decided sends — see §12 and §15.
- **Reversibility**: Fully reversible — the new components can be decommissioned without affecting the Event Bus or any other prior document; providers would revert to direct, ungoverned notification logic if ENF were removed.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Trigger Mapping, Template Registry, Preference Registry, Adapter Layer, and Delivery Ledger are specified at architecture level. |
| **Reuse of the Event Bus** | Confirmed | Trigger Mapping is an ordinary EEB subscriber; no parallel ingestion mechanism introduced. |
| **Preservation of ADR-EAL-011's orchestration-only principle** | Confirmed | AI involvement, where used, is limited to content wording via the unchanged AI Platform mechanism; no AI write-path into the send decision. |
| **Technology-agnostic validation** | Ready | No binding to a specific email/SMS/push provider. |
| **Security model maturity** | Ready for design review | Recipient data sensitivity and credential sourcing are addressed (§8); no formal threat model performed. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Digest aggregation logic** — formalizing how multiple triggered notifications for the same recipient within a digest window are batched into a single message, building on the declared digest-frequency preference rather than ad hoc batching.
- **Channel provider webhook standardization** — a common contract for ingesting asynchronous delivery-status callbacks (bounce, open) across different channel providers' own webhook formats.
- **Preference-center self-service UI integration** — a formal interface contract for a recipient-facing preference management surface, building on `setPreference()` rather than a bespoke settings mechanism.
- **Cross-reference with the Research Platform's Findings Repository** — notifying interested recipients when a finding reaches PUBLISHED, as a concrete example trigger binding, once both documents' owners agree on the specific topic/template pairing.

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-015.
