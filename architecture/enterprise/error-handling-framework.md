---
title: Enterprise Error Handling Framework
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Error Handling Framework

## 1. Problem Statement

Two frozen documents already reason about *failure* at their own respective granularity:

- [Enterprise Plugin Lifecycle Management](plugin-lifecycle-management.md) (ADR-EAL-001) tracks plugin-level health via its Health & Telemetry Monitor and Failure Handler/Circuit Breaker (PLM §4, §10), deciding whether a *plugin as a whole* should move to DEGRADED or QUARANTINED.
- [Enterprise Service Registry](service-registry.md) (ADR-EAL-004) tracks instance-level liveness via its Health Check Aggregator (ESR §4), deciding whether a *specific running instance* is healthy enough to receive traffic.

Neither document addresses a finer-grained, and arguably more foundational, question: **when an individual call or request fails, what did it actually fail with, how is that communicated consistently to the caller, and how does a caller decide whether to retry?** Without a shared answer, the same problems this library has repeatedly worked to eliminate elsewhere reappear at the level of individual errors:

- **Inconsistent error shapes** — each module/plugin/service returns errors in its own ad hoc format, forcing every caller to write provider-specific error-handling code.
- **No shared error taxonomy** — "this failed because the caller sent bad input" and "this failed because a downstream dependency was unavailable" are different situations requiring different caller behavior (don't retry vs. retry with backoff), but without a shared classification, callers can't reliably distinguish them.
- **No correlation across a request's path** — a request that traverses multiple modules/plugins/service instances (per ESR's own layering) has no standard way to correlate a failure back to where it originated, complicating diagnosis.
- **No standard retry guidance** — callers must guess whether a given failure is safe to retry, and with what backoff, rather than being told.
- **Weak signal into existing health mechanisms** — PLM's Health & Telemetry Monitor and ESR's Health Check Aggregator both need *some* signal to decide DEGRADED/QUARANTINED or healthy/unhealthy status, but neither document specifies where that signal comes from at the level of individual failed calls.

The Enterprise Error Handling Framework (EEHF) defines a shared error taxonomy, a globally namespaced error code scheme, a correlation-ID propagation standard, and a structured error-response contract — consumed by callers directly, and feeding (as an input signal only) into PLM's and ESR's existing health mechanisms without altering either.

### Relationship to PLM's Failure Handler and ESR's Health Check Aggregator

This document's scope is deliberately narrower than, and feeds into rather than replaces, the failure-handling mechanisms already frozen elsewhere:

| | **Error Handling Framework (this document)** | **PLM Failure Handler/Circuit Breaker** | **ESR Health Check Aggregator** |
|---|---|---|---|
| Answers | "What exactly went wrong on this call, and should the caller retry?" | "Is this plugin's overall behavior degraded enough to quarantine it?" | "Is this specific running instance currently healthy?" |
| Granularity | Per call/request | Per plugin (aggregate across calls/instances) | Per instance (aggregate across calls to that instance) |
| Primary output | A structured error response (code, correlation ID, retryable hint) | A lifecycle state transition (ACTIVE → DEGRADED → QUARANTINED) | A healthy/unhealthy instance-set membership change |
| Relationship | Individual classified errors are an **input signal** to both of the other two — repeated errors of a given class from a plugin or instance are exactly the kind of evidence those mechanisms already consume | Consumes error-rate signals (already anticipated generically in PLM §10) | Consumes error-rate signals (already anticipated generically in ESR §4) |

EEHF does not perform circuit-breaking, quarantine, or instance-health determination itself — those remain owned exactly as frozen by PLM and ESR respectively. EEHF standardizes what a failure *is* and how it's *reported*; PLM and ESR remain the owners of what happens *in response* at their respective levels. **This document does not modify either frozen document.**

## 2. Goals

| Goal | Description |
|---|---|
| **Shared error taxonomy** | A small, fixed set of error classes (e.g., validation/client error, not-found, dependency-unavailable, timeout, internal/system error) applicable regardless of which module, plugin, or service produced the error. |
| **Globally namespaced error codes** | Every distinguishable error condition has a stable, globally unique code, following a naming convention consistent with this library's existing identifier schemes (Capability IDs, §3 Appendix A of the Capability Registry). |
| **Structured, consistent error response contract** | Every error, regardless of source, is expressible in one common shape: code, class, human-readable message, correlation ID, and a retryable/backoff hint. |
| **Correlation-ID propagation** | A single correlation ID follows a request across module/plugin/service boundaries, so a failure can be traced back to its origin regardless of how many providers were involved (consistent with ESR's multi-instance routing model). |
| **Actionable retry guidance** | Every error explicitly states whether the caller should retry, and if so, with what backoff strategy — removing guesswork from caller-side error handling. |
| **Signal, not control, into existing health mechanisms** | Classified error data is available as an input to PLM's Health & Telemetry Monitor and ESR's Health Check Aggregator, without EEHF making or overriding either's DEGRADED/QUARANTINED or healthy/unhealthy decisions. |

**Non-goals**: EEHF does not perform circuit-breaking, quarantine, or instance-health determination (owned by PLM and ESR respectively); it is not a logging/observability platform itself (it defines a contract that a logging/tracing system would consume); and it does not alter module/plugin/capability/instance identity owned by the other registries.

## 3. Architecture

```
   ┌───────────────────────────┐
   │   Calling code / consumer    │
   └─────────────┬─────────────┘
                 │ request (carries correlation ID)
   ┌─────────────▼─────────────┐
   │   Module / Plugin / Service   │  ← on failure, classifies and
   │   Instance (any provider)     │    returns a structured error
   └─────────────┬─────────────┘
                 │ structured error response
   ┌─────────────▼─────────────┐
   │   Error Taxonomy &            │  ← the shared classification +
   │   Code Namespace              │    code scheme this document defines
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐
   │   Error Response Contract     │  ← code, class, message,
   │   (shared schema)             │    correlation ID, retry hint
   └─────────────┬─────────────┘
                 │
          ┌───────┴────────┐
          │                 │
┌─────────▼────────┐  ┌─────▼──────────────┐
│ Calling code        │  │ Error Signal Feed     │  ← aggregated error-rate
│ (retry per hint)    │  │ (to PLM Health Monitor │    signal, consumed by
│                     │  │  and ESR Health Check   │    frozen mechanisms as-is
│                     │  │  Aggregator, as input   │
│                     │  │  only — no control back)│
└───────────────────┘  └───────────────────┘
```

EEHF sits *before* PLM's and ESR's own health mechanisms in the data flow — it standardizes and classifies; those two frozen systems remain the sole owners of what decision, if any, follows from a pattern of classified errors.

## 4. Components

- **Error Taxonomy** — the fixed set of top-level error classes: `client_error` (caller's fault — bad input, unauthorized), `not_found` (a referenced identity, per this library's own identity schemes — module ID, plugin ID, Capability ID — does not resolve), `dependency_unavailable` (a declared dependency, per EDM's model, could not be reached), `timeout`, `capability_incompatible` (a resolved capability failed a version-compatibility check per EVCS's classification, §"Breaking-Change Classification Rules"), and `internal_error` (unclassified system fault). This taxonomy is intentionally small and closed — new classes require a deliberate addition, not ad hoc proliferation.
- **Error Code Namespace** — a globally unique code per distinguishable error condition, following the convention `err.<domain>.<condition>` (e.g., `err.chart.invalid_input`, `err.rule.dependency_unavailable`), directly mirroring the Capability ID naming convention already established (Capability Registry, Appendix A) for consistency across the library's identifier schemes.
- **Error Response Contract** — the shared schema every provider returns on failure: `{ code, class, message, correlationId, retryable, retryAfterHint }`.
- **Correlation-ID Propagation Standard** — the rule that a correlation ID is generated at the origin of a request and passed through every subsequent module/plugin/service-instance call it triggers, so a failure anywhere in the chain can be traced to the originating request.
- **Error Signal Feed** — an optional, additive stream of classified error occurrences (by provider identity and error class) that PLM's Health & Telemetry Monitor and ESR's Health Check Aggregator may consume as one input among others they already anticipate (PLM §10, ESR §4) — EEHF publishes the signal; it does not decide what either frozen mechanism does with it.

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `classifyError(rawError)` | Provider's own error-handling code → Error Taxonomy | Maps an internal fault to one of the fixed taxonomy classes and an `err.<domain>.<condition>` code. |
| `buildErrorResponse(code, class, correlationId, context)` | Provider → Error Response Contract | Produces the structured response shape returned to the caller. |
| `propagateCorrelationId(incomingId or newId)` | Any provider handling a request → Correlation-ID Propagation Standard | Ensures the same correlation ID is threaded through to any downstream calls the provider itself makes. |
| `emitErrorSignal(providerId, providerType, errorCode, timestamp)` | Provider (optionally) → Error Signal Feed | Publishes a classified error occurrence for consumption by PLM's Health & Telemetry Monitor or ESR's Health Check Aggregator — read-only from those systems' perspective, exactly as EDM's and EVCS's outputs are consumed voluntarily rather than imposed. |

## 6. Data Flow

1. A request enters the system carrying a correlation ID (generated at origin if not already present).
2. If a module, plugin, or service instance encounters a fault while handling that request, it calls `classifyError()` to map the fault to a taxonomy class and a globally namespaced error code.
3. `buildErrorResponse()` constructs the structured response, including the correlation ID that was propagated in on the incoming request.
4. The response is returned to the caller, which reads the `retryable`/`retryAfterHint` fields to decide whether and how to retry — no guesswork required.
5. If the provider itself made downstream calls (e.g., to another module, plugin, or a resolved capability's provider, per the Capability Registry → Service Registry chain), the same correlation ID is propagated to those calls per §4's standard, so a multi-hop failure remains traceable to one origin.
6. Optionally, the provider calls `emitErrorSignal()`, publishing the classified occurrence; PLM's Health & Telemetry Monitor and ESR's Health Check Aggregator may (per their own already-frozen, unmodified logic) treat a pattern of such signals as one input toward a DEGRADED/QUARANTINED or healthy/unhealthy determination — EEHF has no visibility into, and does not control, what either does with that input.

## 7. Design Patterns

- **Shared error taxonomy / problem-details style contract** — a small, closed classification plus a consistent response shape, the same discipline this library already applies to identity (Capability IDs) and compatibility (EVCS), now applied to failures.
- **Correlation ID propagation** — the standard distributed-tracing pattern for tying a multi-hop failure back to one originating request, essential precisely because ESR's own model (Service Registry §1) already establishes that a single logical request may traverse multiple independently-scaled instances.
- **Signal producer, not controller** — mirrors the additive, non-invasive integration pattern already used by EDM (feeding dependency structure without altering PLM/Module Registry) and by EVCS (a policy referenced voluntarily): EEHF produces a signal that existing frozen mechanisms may consume, without embedding itself into their decision logic.
- **Fixed, closed taxonomy over open-ended free-form errors** — deliberately constrains the error classes to a small, well-understood set rather than allowing arbitrary new top-level classes, keeping caller-side handling logic tractable regardless of how many providers exist.

## 8. Security Considerations

- **Error messages must not leak sensitive internals** — the human-readable `message` field in the Error Response Contract should be safe for the calling context to see; sensitive diagnostic detail (stack traces, internal identifiers not meant for external exposure) belongs in server-side logs correlated by the correlation ID, not in the response itself.
- **Correlation IDs are not authentication or authorization tokens** — a correlation ID must not be usable to bypass access controls or reveal information about a request beyond what the caller is already authorized to see; it identifies a request for tracing purposes only.
- **Error signal feed access scoping** — consistent with the general principle already applied to health-relevant data in ESR (§8, network-address exposure) and PLM (§8, least-privilege), the Error Signal Feed should be readable only by the health mechanisms authorized to consume it, not broadly exposed.
- **No secrets in error codes, messages, or context** — consistent with the manifest-hygiene rule already established repeatedly in this library (PLM §8, Module Registry §8, ECF §8), error responses never carry credential material.

## 9. Scalability

- **Highest call-volume surface in this library** — error classification and response construction happen (when they happen at all) on the normal request path, at a volume comparable to or exceeding EFF's per-request flag evaluation (Feature Flag Framework §9); the taxonomy and response-building logic must be lightweight enough not to add meaningful latency even on the failure path.
- **Error Signal Feed volume scales with failure rate, not total traffic** — under normal operation this is a small fraction of total request volume; the feed's design should not assume it needs to handle full request-volume throughput, only failure-rate throughput, which is a materially different (and usually much lower) capacity planning target.
- **Correlation ID propagation adds negligible overhead** — passing an existing identifier through call headers/context is computationally trivial; the design cost is discipline (every provider must actually propagate it), not runtime performance.

## 10. Best Practices

- Always classify an error into one of the fixed taxonomy classes before returning it — never let a raw, unclassified internal exception escape to a caller.
- Populate `retryable`/`retryAfterHint` deliberately and conservatively — marking a genuinely non-idempotent-unsafe operation as retryable is worse than being conservative and marking a safely-retryable one as non-retryable.
- Propagate the correlation ID on every downstream call a provider makes, with no exceptions — a single un-propagated hop breaks traceability for the entire chain beyond that point.
- Treat `emitErrorSignal()` as optional but recommended — a provider that never emits error signals loses no functionality itself, but denies PLM's and ESR's existing health mechanisms a potentially valuable input signal they already anticipate consuming.
- Keep the error code namespace's domain segment consistent with the Capability ID domain it relates to (e.g., `err.chart.*` alongside `cap.chart.*`), making the two schemes easy to cross-reference.

## 11. Common Pitfalls

- **Ad hoc, per-provider error formats reappearing despite this framework** — the framework only helps if actually adopted; a provider that continues returning unstructured errors reintroduces exactly the fragmentation problem in §1 for its own callers.
- **Treating EEHF as a circuit-breaking or quarantine mechanism** — the single most important boundary to preserve (§1's relationship table); EEHF classifies and reports, it does not decide to quarantine a plugin or mark an instance unhealthy — those decisions remain exactly where PLM and ESR already placed them.
- **Correlation ID regeneration mid-chain** — a provider that generates a *new* correlation ID instead of propagating the incoming one silently breaks traceability, often invisibly until an incident makes the gap obvious.
- **Taxonomy sprawl** — allowing every team to add its own top-level error class defeats the purpose of a *shared*, closed taxonomy; new conditions should map into the existing classes via a specific `err.<domain>.<condition>` code, not a new class.
- **Leaking sensitive detail through error messages** — see §8; a common and easy mistake when error messages are constructed by simply stringifying an internal exception.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **No shared error framework (status quo)** | Each provider defines its own error format and retry semantics. | This is precisely the fragmented state described in §1; fails every goal in §2. |
| **Fold error handling into PLM's Failure Handler** | Extend PLM's existing Failure Handler/Circuit Breaker to also define the per-call error contract. | PLM's mechanism is scoped to plugin-level aggregate health and lifecycle transitions (PLM §4, §10), not per-call error taxonomy; modules (which aren't governed by PLM at all) would be left uncovered, and PLM's frozen scope would be distorted by a per-call concern it wasn't designed for — the same design-integrity issue already avoided when ESR was kept separate from ECR (Service Registry §12) and EFF was kept separate from ECF (Feature Flag Framework §12). |
| **Fold error handling into the Service Registry's Health Check Aggregator** | Extend ESR to also define the per-call error contract, since it already tracks instance health. | ESR's Health Check Aggregator is scoped to instance-level liveness aggregation, not per-call error classification or correlation-ID propagation across a multi-provider chain; conflating the two would mix a request-path concern into what is otherwise a comparatively low-frequency health-polling component (ESR §9). |
| **Open-ended, free-form error classification (no fixed taxonomy)** | Let each provider define its own error classes freely, with only the response shape standardized. | Fails the shared-taxonomy goal outright — callers still can't write generic "retry on dependency_unavailable, don't retry on client_error" logic if the class names themselves aren't shared and fixed. |

## 13. Migration Strategy

1. **Publish the Error Taxonomy, Error Code Namespace convention, Error Response Contract, and Correlation-ID Propagation Standard** as this document's frozen artifacts.
2. **Adopt the framework for any newly-built module, plugin, or service integration first**, requiring conformance from day one rather than retrofitting.
3. **Retrofit existing providers incrementally**, prioritized by which providers are most often implicated in cross-provider call chains (where correlation-ID propagation delivers the most immediate diagnostic value).
4. **Enable `emitErrorSignal()` publication for retrofitted providers** once their error classification is in place, giving PLM's and ESR's existing health mechanisms an additional, voluntary input signal without any change to either frozen document.
5. **Decommission any legacy, provider-specific error format** once callers have migrated to expect the shared Error Response Contract, on a per-provider basis rather than a single platform-wide cutover.

## 14. Success Criteria

- 100% of newly-built providers return errors conforming to the shared Error Response Contract from initial release.
- A representative sample of multi-hop request failures can be traced end-to-end via a single correlation ID, across at least one module→plugin (or plugin→module) call chain.
- Zero instances of a caller being unable to determine retry safety because `retryable`/`retryAfterHint` were missing or ambiguous, for any conforming provider.
- Measurable adoption of `emitErrorSignal()` by providers already integrated with PLM's Health & Telemetry Monitor or ESR's Health Check Aggregator, without any modification to either frozen mechanism's own logic.
- No new, unclassified top-level error class introduced outside the fixed taxonomy without a deliberate, reviewed addition to this document.

## 15. Decision Matrix

| Criterion (weight) | Dedicated Error Handling Framework, additive signal into PLM/ESR (recommended) | No shared framework | Fold into PLM's Failure Handler | Fold into ESR's Health Check Aggregator | Open-ended, unfixed taxonomy |
|---|---|---|---|---|---|
| Shared taxonomy / consistent contract (High) | 5 | 1 | 3 | 3 | 2 |
| Correlation across multi-hop chains (High) | 5 | 1 | 2 | 2 | 3 |
| Respects PLM/ESR design integrity (High) | 5 | 5 | 1 | 1 | 4 |
| Actionable retry guidance (Medium) | 5 | 1 | 2 | 2 | 2 |
| Coverage of both modules and plugins (Medium) | 5 | 3 | 2 | 3 | 4 |
| Implementation/governance overhead (Medium, lower = better fit) | 3 | 5 | 3 | 3 | 4 |
| **Weighted outcome** | **Best overall fit** | Fails core goals | Fails design integrity | Fails design integrity | Fails consistency goal |

**Conclusion**: a dedicated Error Handling Framework, feeding classified error signals into PLM's and ESR's existing health mechanisms as an optional input without altering either, is recommended. It is the only option that achieves a consistent, shared error contract without distorting the already-accepted scope of PLM or ESR.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-009: Enterprise Error Handling Framework as a Shared, Non-Invasive Error Contract**

- **Status**: Accepted
- **Context**: No document in this library defines a shared error taxonomy, error code namespace, correlation-ID propagation standard, or structured error-response contract at the level of an individual failed call — a gap distinct from PLM's plugin-level health mechanism (ADR-EAL-001) and ESR's instance-level health mechanism (ADR-EAL-004), both of which need *some* input signal that neither document specifies the source of.
- **Decision**: Adopt a shared Error Taxonomy, `err.<domain>.<condition>` code namespace (consistent with the Capability ID convention, Capability Registry Appendix A), a structured Error Response Contract, and a Correlation-ID Propagation Standard, retained as a **shared policy and taxonomy**. An optional Error Signal Feed publishes classified error occurrences for voluntary consumption by PLM's Health & Telemetry Monitor and ESR's Health Check Aggregator. **This decision does not modify either frozen document** — PLM and ESR may consume EEHF's signals but retain full, exclusive ownership of health and recovery decisions (DEGRADED/QUARANTINED transitions, healthy/unhealthy instance determination); EEHF is a producer of an optional input signal only, never a controller of either mechanism's decisions.
- **Rationale**: The Decision Matrix (§15) shows that folding this capability into either PLM's or ESR's existing mechanism would distort their already-accepted, narrower scope (plugin lifecycle health and instance liveness respectively), the same design-integrity concern already honored when ESR was kept separate from ECR and EFF was kept separate from ECF. A dedicated, narrowly-scoped, purely additive framework achieves the consistency goals without that risk.
- **Consequences**:
  - *Positive*: consistent error handling and retry logic for callers across all providers; correlation IDs make multi-hop failures traceable, consistent with ESR's own multi-instance routing model; PLM and ESR gain an additional, optional signal source without any change to their frozen specifications.
  - *Negative*: introduces a framework that, like EDM and EVCS before it, requires voluntary adoption to deliver value — a provider that doesn't conform gains nothing and remains a gap in consistency until retrofitted.
  - *Neutral*: `emitErrorSignal()` adoption is optional; PLM's and ESR's health-determination logic is unaffected whether or not any given provider emits signals.
- **Alternatives rejected**: no shared framework, folding into PLM, folding into ESR, open-ended taxonomy — see §12 and §15.
- **Reversibility**: Fully reversible — EEHF can be decommissioned without impact to PLM or ESR, since neither depends on it under this decision; providers would simply revert to unclassified, ad hoc error formats.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Taxonomy, code namespace, response contract, and correlation-ID standard are specified at architecture level. |
| **Respect for PLM/ESR design integrity** | Confirmed by design | §1's relationship table and ADR-EAL-009 explicitly scope EEHF as a signal producer only, not a controller, consistent with the additive precedent set by EDM and EVCS. |
| **Consistency with existing identifier schemes** | Confirmed | Error code namespace convention (`err.<domain>.<condition>`) mirrors the Capability ID convention (Capability Registry, Appendix A) for cross-reference ease. |
| **Technology-agnostic validation** | Ready | No binding to a specific tracing system, logging platform, or transport. |
| **Security model maturity** | Ready for design review | Message-content sensitivity and error-signal-feed access scoping are addressed (§8); no formal threat model performed. |
| **Ownership boundary with PLM/ESR** | Confirmed at approval | PLM and ESR may consume EEHF's signals but retain exclusive ownership of health and recovery decisions (ADR-EAL-009). |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Distributed tracing integration** — formalizing the Correlation-ID Propagation Standard into a full distributed-tracing contract (spans, parent/child relationships), building on the correlation-ID foundation established here.
- **Automated error-signal-driven health tuning** — a future, separately-approved enhancement to PLM's or ESR's health mechanisms could make more sophisticated use of the Error Signal Feed than simple rate thresholds — but any such change would itself require its own future ADR against ADR-EAL-001 or ADR-EAL-004, consistent with the non-invasive precedent set here.
- **Error-class-aware retry libraries** — providing shared, reusable caller-side retry/backoff logic keyed off the fixed taxonomy, reducing the chance of inconsistent retry behavior even among conforming callers.
- **Capability-maturity-aware error tolerance** — using the Capability Registry's maturity lifecycle (Appendix B) to set different alerting thresholds for errors from EXPERIMENTAL versus STABLE capabilities, echoing the maturity-aware ideas already flagged as future evolution for ECF (§18) and EFF (§18).

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-009.
