---
title: Enterprise SDK
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise SDK

## 1. Problem Statement

[API Gateway](api-gateway.md) (ADR-EAL-020) is "the single external entry point" and "remains a translation and enforcement layer" that "must not contain business logic or become an orchestration engine" — a principle just reconfirmed at ADR-EAL-022's approval. Every external caller — including a Marketplace publisher's integration, an internal team building against the platform, or a partner system — currently has to construct raw requests against the Gateway's versioned route contracts by hand: attaching credentials correctly, handling classified errors and retry hints, propagating a correlation ID, and tracking which Gateway route-contract version they're coding against.

The Enterprise SDK (ESDK) is a thin, generated/maintained client library that wraps exactly that — and nothing more. It is deliberately **not** a second gateway, **not** a second authentication mechanism, and — reinforcing the principle just confirmed with Marketplace (ADR-EAL-023) — **not** a second orchestration mechanism. Every one of those temptations is named explicitly in this document precisely because a client library sits in a natural position to accumulate exactly that kind of scope creep over time.

### Reuse map

| Need | Reused from | How |
|---|---|---|
| The only entry point the SDK ever calls | [API Gateway](api-gateway.md) (ADR-EAL-020) | Every SDK method is a thin wrapper around one Gateway route; the SDK never bypasses the Gateway or implements a second call path. |
| What a call actually requires and returns | [API Gateway](api-gateway.md)'s API Route Registry (ADR-EAL-020) | SDK methods are generated from (or kept in lockstep with) the Gateway's own versioned route contracts — no separate contract definition. |
| SDK version compatibility with the Gateway's route contracts | [Version Compatibility Strategy](version-compatibility-strategy.md) (ADR-EAL-008) | A breaking change to a route contract (classified via EVCS) requires a corresponding major SDK version — the SDK's own versioning follows EVCS's rules, not an independent scheme. |
| Credential handling | [Identity & Access](identity-and-access.md) (ADR-EAL-018) | The SDK provides a convenience helper for attaching a credential to a request; it never authenticates or authorizes anything itself — that remains entirely the Gateway's (and, behind it, Identity & Access's) responsibility. |
| Error surfacing and retry guidance | [Error Handling Framework](error-handling-framework.md) (ADR-EAL-009) | The SDK surfaces EEHF's classified errors and retryable/backoff hints directly to the calling developer — no SDK-specific error format. |
| Multi-step business processes | [Workflow Engine](workflow-engine.md) (ADR-EAL-013) | The SDK performs single-call retries per EEHF's hint; any multi-step, compensable process remains entirely server-side, orchestrated by the unchanged Workflow Engine — the SDK never implements client-side orchestration logic. |
| Request tracing | [Observability Architecture](observability-architecture.md) (ADR-EAL-010) + [Error Handling Framework](error-handling-framework.md) (ADR-EAL-009) | The SDK generates (or accepts a caller-supplied) request ID and propagates it as EEHF's correlation ID, exactly as the Gateway already expects to receive it (API Gateway §10). |

**Scope boundary:** this document does not modify any of the twenty-three prior documents, including the API Gateway's own translation/enforcement scope and the Workflow Engine's exclusive orchestration role (just reconfirmed, ADR-EAL-023). The SDK is a client, never a second instance of either.

## 2. Goals

| Goal | Description |
|---|---|
| **A thin wrapper, generated from the Gateway's contracts** | SDK methods correspond directly to API Route Registry entries; no independently-defined SDK contract. |
| **No second authentication mechanism** | The SDK helps attach credentials; it never verifies them — verification remains entirely server-side. |
| **No second orchestration mechanism** | The SDK performs single-call retries only; multi-step processes remain the Workflow Engine's exclusive responsibility, per the principle just reconfirmed with Marketplace. |
| **Consistent error surface for developers** | EEHF's classified errors and retry hints are surfaced as-is, not translated into a parallel SDK-specific error taxonomy. |
| **Versioned in lockstep with the Gateway's contracts** | SDK version compatibility follows EVCS's breaking-change classification of the underlying route contracts. |

**Non-goals**: the SDK does not implement authentication/authorization logic, business logic, or orchestration; it does not define new API contracts (it consumes the Gateway's existing ones); and it does not replace direct Gateway access for callers who prefer not to use it — the Gateway remains fully usable without the SDK.

## 3. Architecture

```
   ┌───────────────────────────┐
   │   Developer / integrator       │
   └─────────────┬─────────────┘
                 │ SDK method call
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   SDK Client Library (new)      │◄──────┤ API Route Registry            │
   │                                 │        │ (API Gateway, unchanged)       │
   └─────────────┬─────────────┘        └───────────────────────────┘
                 │
   ┌─────────────▼─────────────┐
   │   Credential Attachment         │  ← new: convenience only,
   │   Helper (new)                  │    not a security boundary
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐
   │   Single-Call Retry Helper      │  ← new: retries per EEHF's
   │   (new)                        │    hint; never multi-step logic
   └─────────────┬─────────────┘
                 │ HTTP/wire call
   ┌─────────────▼─────────────┐
   │   API Gateway (unchanged)       │  ← the only entry point;
   │                                 │    Auth → AuthZ → Licensing →
   │                                 │    Flags → Execution (ADR-EAL-022)
   └───────────────────────────┘
```

## 4. Components

- **SDK Client Library** *(new)* — the generated/maintained per-language wrapper; each method corresponds to exactly one API Route Registry entry, versioned to match.
- **Credential Attachment Helper** *(new, convenience only)* — attaches a caller-supplied credential to outgoing requests in the format the Gateway expects; performs no verification itself — a lost or invalid credential simply results in the Gateway's own unchanged Authentication stage rejecting the call.
- **Single-Call Retry Helper** *(new, deliberately narrow)* — retries an individual failed call according to EEHF's `retryable`/`retryAfterHint` fields; explicitly does not sequence multiple calls, maintain cross-call state, or perform compensation — any of which would constitute the client-side orchestration this document's scope boundary forbids.

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| SDK method (one per Route Registry entry, e.g. `client.<domain>.<action>(input)`) | Developer → SDK Client Library | Thin wrapper around a single Gateway route call. |
| `attachCredential(request, credential)` | SDK Client Library (internal) → Credential Attachment Helper | Formats and attaches a credential; performs no verification. |
| `retryIfEligible(response)` | SDK Client Library (internal) → Single-Call Retry Helper | Applies EEHF's retryable/backoff hint to a single failed call only. |

## 6. Data Flow

1. A developer calls an SDK method corresponding to one API Route Registry entry.
2. The Credential Attachment Helper formats the developer-supplied credential onto the outgoing request — no verification occurs client-side.
3. The SDK Client Library generates (or accepts a caller-supplied) request ID, propagated as EEHF's correlation ID.
4. The call reaches the API Gateway's unchanged pipeline (Authentication → Authorization → Licensing → Feature Flags → Capability Execution, per ADR-EAL-022) — the SDK has no visibility into, and implements none of, these stages; it only sees the eventual response.
5. On a classified, retryable error, the Single-Call Retry Helper retries that one call per EEHF's hint; it never chains additional calls or maintains state across multiple requests.
6. On success or a non-retryable classified error, the SDK returns the result (or the EEHF-classified error, unmodified in shape) directly to the developer.

## 7. Design Patterns

- **Thin client, not a second server-side layer** — the SDK's entire value proposition is convenience over an unmodified Gateway; any logic that would require the SDK to make an authorization, entitlement, or business decision belongs server-side, not in the client.
- **Contract-generated, not independently authored** — SDK methods are generated from (or kept strictly synchronized with) the Gateway's own API Route Registry, the same "reference, don't re-define" discipline used throughout this library (e.g., the Capability Registry referencing rather than owning provider identity, Capability Registry §1).
- **Narrow retry scope as a deliberate boundary** — retrying a single call is categorically different from orchestrating a multi-step process; keeping the Single-Call Retry Helper deliberately narrow is what prevents the SDK from organically growing into a second orchestrator, the exact risk the Marketplace document's reconfirmed principle (ADR-EAL-023) was aimed at foreclosing.

## 8. Security Considerations

*(Citing the Security Principles Catalog directly, per ESA's discipline.)*

- **The SDK is not a trust boundary** — per Identity & Access's model, all real authentication/authorization enforcement happens at the Gateway (and, behind it, via Identity & Access's `authenticate()`/`checkPermission()`); the SDK's credential-attachment convenience must never be mistaken for, or documented as, a security control in its own right.
- **Principle: Secrets-by-Reference** (ESA catalog) applies to how a developer supplies credentials to the SDK — the SDK should accept a reference/handle to stored credential material where the calling environment supports it, rather than encouraging inline hardcoded credentials in application code.
- **No credential material is logged by the SDK** — consistent with the manifest/error-message hygiene discipline applied throughout this library (EEHF §8).

## 9. Scalability

Not a meaningful architectural concern for the SDK itself — it runs within each calling application's own process and inherits whatever load characteristics that application has. The only relevant consideration is that the Single-Call Retry Helper's backoff behavior (per EEHF's hint) must not, in aggregate across many SDK-using clients, produce a retry storm against the Gateway during an incident — a client-side responsibility to honor the server-provided backoff hint faithfully, not to retry more aggressively than instructed.

## 10. Best Practices

- Generate SDK methods directly from the API Route Registry's contract definitions wherever feasible, minimizing drift between the two.
- Bump the SDK's major version whenever a route contract undergoes an EVCS-classified breaking change — never let SDK versioning drift independently of the contracts it wraps.
- Keep the Single-Call Retry Helper's scope to exactly one call — any temptation to add "just one more step" of client-side sequencing should be redirected to a server-side Workflow Engine definition instead.
- Document clearly, in the SDK's own materials, that it is not a security boundary — real enforcement always happens at the Gateway.

## 11. Common Pitfalls

- **The SDK growing into a client-side orchestrator** — the single most important pitfall this document exists to prevent, given the confirmed, permanent principle that the Workflow Engine is the only orchestration mechanism in this library (ADR-EAL-023); any multi-call sequencing logic in the SDK is a violation of that principle regardless of how small it starts.
- **Treating the SDK's credential attachment as a security control** — risks a false sense of client-side security when the actual enforcement is, and must remain, entirely server-side.
- **SDK version drift from the Gateway's route contracts** — an SDK that doesn't track EVCS-classified breaking changes will silently produce requests the Gateway rejects, or worse, requests that are accepted but misinterpreted.
- **Inventing an SDK-specific error format** — discards the classified-error/retry-hint structure EEHF already provides, forcing developers to learn a second error vocabulary for no reason.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **No official SDK; developers construct raw requests** | Leave every integrator to build their own client against the Gateway's contracts. | Fails the developer-convenience goal outright and invites inconsistent, ad hoc client-side handling of credentials, retries, and errors across every integration. |
| **SDK with built-in multi-step orchestration/workflow logic** | Let the SDK sequence multiple calls, retry across steps, and manage compensation client-side. | Directly violates the just-confirmed, permanent principle that the Workflow Engine is the sole orchestration mechanism (ADR-EAL-023); any such logic belongs server-side. |
| **SDK with its own authentication/token-management logic that verifies credentials client-side** | Have the SDK perform local credential validation before sending a request. | Would create a second, client-side authentication mechanism that could drift from Identity & Access's authoritative model; verification must remain exclusively server-side. |
| **A second, SDK-specific error/response format** | Translate Gateway responses into a bespoke SDK error model. | Discards EEHF's already-established, consistent error classification and retry-hint structure for no benefit, forcing developers to learn a redundant vocabulary. |

## 13. Migration Strategy

1. **Generate the SDK Client Library directly from the API Gateway's existing API Route Registry**, starting with a small set of stable, already-versioned routes.
2. **Implement the Credential Attachment Helper and Single-Call Retry Helper as thin, narrowly-scoped components**, resisting any early feature request to add multi-call convenience logic.
3. **Establish the SDK-version-to-route-contract-version mapping** before general release, so a breaking Gateway change has an unambiguous corresponding SDK version bump.
4. **Document the SDK's non-goals explicitly** (no client-side auth verification, no client-side orchestration) in its own developer-facing materials, not just this architecture document.

## 14. Success Criteria

- Every SDK method corresponds to exactly one API Route Registry entry; zero SDK-specific endpoints.
- SDK major-version bumps align 1:1 with EVCS-classified breaking changes to the underlying route contracts.
- Zero multi-call orchestration, sequencing, or compensation logic present in the SDK codebase.
- Zero client-side credential verification logic present in the SDK codebase.
- Developer-facing error handling code can rely on EEHF's classified error shape without any SDK-specific translation.

## 15. Decision Matrix

| Criterion (weight) | Thin, contract-generated SDK with narrow retry scope (recommended) | No official SDK | SDK with built-in orchestration | SDK with client-side auth verification | SDK-specific error format |
|---|---|---|---|---|---|
| Developer convenience (High) | 5 | 1 | 5 | 4 | 3 |
| Preserves Workflow-Engine-only orchestration principle (High) | 5 | 5 | 1 | 5 | 5 |
| Preserves Identity & Access as sole auth authority (High) | 5 | 5 | 4 | 1 | 4 |
| Consistent error/retry experience (Medium) | 5 | 2 | 4 | 4 | 2 |
| Version-drift risk (Medium, lower = better fit) | 4 | 5 | 2 | 2 | 3 |
| **Weighted outcome** | **Best overall fit** | Fails convenience goal | Fails orchestration-boundary goal | Fails auth-boundary goal | Fails error-reuse goal |

**Conclusion**: a thin, contract-generated SDK with a deliberately narrow single-call retry scope is recommended. It is the only option that delivers real developer convenience while fully preserving the Workflow Engine's exclusive orchestration role and Identity & Access's exclusive authentication/authorization authority.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-024: Enterprise SDK as a Thin, Contract-Generated Client — No Second Gateway, Auth Mechanism, or Orchestrator**

- **Status**: Accepted
- **Context**: Every external integrator currently constructs raw requests against the API Gateway's contracts by hand; a client library would help, but sits in a natural position to accumulate scope (auth logic, orchestration logic, a parallel error format) that would violate several already-confirmed principles in this library.
- **Decision**: Introduce an SDK Client Library generated from the Gateway's existing API Route Registry, a Credential Attachment Helper (convenience only, not a security boundary), and a Single-Call Retry Helper (single-call retry per EEHF's hint only — no multi-step logic). SDK versioning follows EVCS's breaking-change classification of the underlying route contracts. **This decision does not modify any of the twenty-three prior documents**, and explicitly reaffirms that the API Gateway remains the only entry point, Identity & Access remains the sole authentication/authorization authority, and the Workflow Engine remains the only orchestration mechanism.
- **Rationale**: The Decision Matrix (§15) shows this is the only option delivering developer convenience without violating any of the three boundary principles (single gateway, single auth authority, single orchestrator) this library has established and, in Marketplace's case, just explicitly reconfirmed.
- **Consequences**:
  - *Positive*: developers get consistent, convenient access to the platform without any duplicated security or orchestration surface; SDK versioning has an unambiguous, EVCS-driven update trigger.
  - *Negative*: SDK maintenance must track Gateway contract changes closely to avoid drift; feature requests for client-side convenience will need ongoing discipline to avoid violating the orchestration/auth boundaries.
  - *Neutral*: the Gateway remains fully usable without the SDK — it is a convenience layer, not a required integration path.
- **Alternatives rejected**: no official SDK, built-in client-side orchestration, client-side auth verification, a second error format — see §12 and §15.
- **Reversibility**: Fully reversible — the SDK can be deprecated or withdrawn without affecting the Gateway, Identity & Access, or the Workflow Engine; integrators would revert to constructing raw requests.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Client Library, Credential Attachment Helper, and Retry Helper are specified at architecture level. |
| **Preserves single-gateway, single-auth, single-orchestrator principles** | Confirmed | Explicitly reaffirmed in the ADR without altering any of the three source documents. |
| **Contract-generation validation** | Ready for review | Depends on the API Route Registry's contracts being sufficiently structured to generate from; an implementation-phase concern. |
| **Technology-agnostic validation** | Ready | No binding to a specific programming language or SDK-generation toolchain. |
| **Security model maturity** | Ready for design review | The "not a trust boundary" clarification (§8) is the key discipline to carry into developer-facing documentation. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Multi-language SDK parity tracking** — if the SDK is offered in multiple languages, a future mechanism to verify all language variants stay in sync with the same route-contract version.
- **SDK usage telemetry via EOA** — SDK-side call metrics (opt-in) could be ingested into EOA's Telemetry Pipeline using the Common Event Envelope, exactly as any other emitter, if visibility into SDK-originated traffic patterns becomes valuable.
- **Typed workflow-result helpers (still not orchestration)** — a future convenience for polling a Workflow Engine instance's state (via its existing read-only `getInstanceState()`) could be added to the SDK, since polling an existing read interface is not orchestration — but initiating or sequencing workflow steps from the SDK would remain out of bounds.

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-024.
