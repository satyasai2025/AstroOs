---
title: Enterprise API Gateway
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise API Gateway

## 1. Problem Statement

This is the final PLATFORM-phase document, and it closes a gap every prior document has quietly assumed away: **something external to the platform is making the first call.** Every mechanism built so far — the Capability → ECR → Module/Plugin → ESR chain, the Workflow Engine, the Event Bus, Scheduling — describes what happens *inside* the platform once a call is already underway. None of them address the actual edge: an external HTTP (or other wire-protocol) request arriving from outside, in an external shape, from a caller who has not yet been resolved to one of Identity & Access's own identity types.

The Enterprise API Gateway (EAG) is that edge: it authenticates the external caller (resolving them to an existing Identity & Access identity type — never a fourth, gateway-specific one), validates and translates an external request into the standard internal invocation chain, applies rate limiting, and translates the response — including error responses — back into the external wire format. It is deliberately *not* a second service-discovery layer, a second authentication mechanism, or a second error-response contract.

### Reuse map

| Need | Reused from | How |
|---|---|---|
| Resolving and invoking the target capability once a request is validated | [Capability Registry](capability-registry.md) (ADR-EAL-003) + [Service Registry](service-registry.md) (ADR-EAL-004) | The Gateway is the first hop; after authentication and validation, it invokes the unchanged Capability → ECR → Module/Plugin → ESR chain exactly like any other caller. |
| Authenticating the external caller | [Identity & Access](identity-and-access.md) (ADR-EAL-018) | An external caller resolves to an existing identity type — a Human Identity (external end user) or a Provider Identity (an external partner/integration system) — never a new, Gateway-specific identity type. |
| Authorizing the resolved caller against the requested route | [Identity & Access](identity-and-access.md) (ADR-EAL-018) | The Gateway calls the unchanged `checkPermission()` before invoking the target capability. |
| Error response shape, including for external callers | [Error Handling Framework](error-handling-framework.md) (ADR-EAL-009) | Internal errors (classified via EEHF's existing taxonomy) are translated to the external wire format, but the underlying code/class/retryable-hint structure is unchanged — no second error contract invented for "external" errors. |
| API route/contract versioning and breaking-change classification | [Version Compatibility Strategy](version-compatibility-strategy.md) (ADR-EAL-008) | An external route's request/response contract is a versioned artifact, classified via EVCS exactly as a module interface or workflow definition would be. |
| Gradual rollout of a new API route/version | [Feature Flag Framework](feature-flag-framework.md) (ADR-EAL-006) | Shifting external traffic to a new route version reuses EFF's rollout/kill-switch mechanism. |
| Rate-limit threshold configuration | [Configuration Framework](configuration-framework.md) (ADR-EAL-005) | Per-route, per-caller-class limits are layered exactly per ADR-EAL-005. |
| Tracing an external request through the internal chain | [Observability Architecture](observability-architecture.md) (ADR-EAL-010) + [Error Handling Framework](error-handling-framework.md) (ADR-EAL-009) | The Gateway honors an external caller's own request ID where supplied, or generates one, and propagates it as EEHF's correlation ID unchanged through the entire internal chain. |
| Mandatory audit of external authentication/authorization events | [Audit Framework](audit-framework.md) (ADR-EAL-019) | Where an external authentication or authorization event matches a category in the Mandatory Audit Event Catalog, it is captured exactly as any other such event — no separate audit mechanism for external traffic. |

**Scope boundary:** this document does not modify any of the nineteen prior documents. It introduces new components strictly for external route definition, request/response translation, and rate limiting.

## 2. Goals

| Goal | Description |
|---|---|
| **A single, versioned external contract per route** | Every externally-exposed route has a versioned request/response schema, classified via EVCS on change. |
| **No new identity type** | External callers resolve to an existing Identity & Access identity type (Human or Provider); the Gateway never introduces a fourth. |
| **No new error contract** | External error responses are translations of EEHF's existing classified errors, not an independently-invented external error shape. |
| **Defined rate limiting** | Every route has an explicit rate-limit policy, configured via ECF, with an emergency kill-switch via EFF. |
| **The Gateway is the only external ingress point** | No capability is reachable from outside the platform except through the Gateway's authenticated, validated, rate-limited path. |
| **Full reuse of internal invocation, identity, error, versioning, and tracing mechanisms** | No parallel mechanism specific to "external" traffic beyond translation itself. |

**Non-goals**: EAG is not a second service-discovery or health-tracking layer (ESR's role, unchanged); it does not define a new authentication mechanism (Identity & Access's role, unchanged); and it does not replace EEHF's error taxonomy — it translates it.

## 3. Architecture

```
   ┌───────────────────────────┐
   │   External caller               │  ← HTTP/API request, external
   │   (human end user or external    │    wire format
   │    partner/integration system)   │
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   API Route Registry (new)     │◄──────┤ Version Compatibility        │
   │                                 │        │ Strategy (EVCS)               │
   └─────────────┬─────────────┘        └───────────────────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Authentication/Authorization  │◄──────┤ Identity & Access             │
   │   Enforcement (new, calls        │        │ (authenticate / checkPermission,│
   │    unchanged EIA interfaces)     │        │  unchanged)                    │
   └─────────────┬─────────────┘        └───────────────────────────┘
                 │
   ┌─────────────▼─────────────┐
   │   Request Validator (new)       │  ← schema check against the
   │                                 │    route's versioned contract
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐
   │   Rate Limiter (new)            │  ← per-route/per-caller-class
   │                                 │    throttling
   └─────────────┬─────────────┘
                 │ (validated, authenticated, within limits)
   ┌─────────────▼─────────────┐
   │   Capability Registry → ESR      │  ← unchanged standard chain
   │   chain (unchanged)              │
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Response Translator (new)     │◄──────┤ Error Handling Framework     │
   │                                 │        │ (EEHF) — classified errors    │
   └───────────────────────────┘        │  translated to external format│
                                        └───────────────────────────┘
```

## 4. Components

- **API Route Registry** *(new)* — stores each externally-exposed route's versioned request/response contract and its mapped target Capability ID. Contract changes are classified via EVCS before a revision is considered compatible with existing external callers.
- **Authentication/Authorization Enforcement** *(new, but calls unchanged interfaces)* — resolves an external caller's credential to an existing Identity & Access identity type via `authenticate()`, then calls `checkPermission()` for the requested route — introducing no new identity type or permission model, only the translation from an external credential format (e.g., an API key or bearer token) into the call Identity & Access already expects.
- **Request Validator** *(new)* — checks an inbound request against the route's currently-active versioned schema (from the API Route Registry) before it reaches the internal chain, rejecting malformed requests with a translated EEHF-classified error.
- **Rate Limiter** *(new)* — enforces a per-route, per-caller-class throttling policy (configured via ECF), with an emergency kill-switch for a specific route reusing EFF's mechanism.
- **Response Translator** *(new)* — maps a capability's successful result, or an EEHF-classified error response, into the route's external wire format — a pure translation layer, never an independent source of error semantics.

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `defineRoute(routeId, contractSchema, targetCapabilityId)` | Route owner → API Route Registry | Declares a new, versioned external route, mapped to an internal Capability ID. |
| `handleExternalRequest(routeId, rawRequest)` | External caller → Gateway (composed pipeline) | The single entry point: authenticate → authorize → validate → rate-limit → invoke → translate response. |
| `authenticate(credential)` / `checkPermission(identity, permission, resourceRef)` | Gateway → Identity & Access (unchanged) | Resolves the external caller and authorizes the requested route — no Gateway-specific auth logic. |
| `setRateLimit(routeId, callerClass, threshold)` | Operator → Configuration Framework (unchanged) | Sets a route's rate-limit threshold, layered per ADR-EAL-005. |

## 6. Data Flow

1. An external caller sends a request to a defined route; the Gateway's Authentication/Authorization Enforcement calls Identity & Access's unchanged `authenticate()`, resolving the caller to an existing Human or Provider identity — never a new type.
2. `checkPermission()` (unchanged) confirms the resolved identity is authorized for the requested route.
3. The Request Validator checks the request against the route's currently-active contract version (from the API Route Registry); a mismatch is rejected with a translated EEHF-classified error before ever reaching the internal chain.
4. The Rate Limiter checks the caller against the route's configured threshold (ECF); an exceeded limit is rejected with a translated, classified error and, where configured, a retry-after hint consistent with EEHF's existing retryable-hint model.
5. The validated, authorized, within-limit request is translated into a call against the route's target Capability ID, invoked through the entirely unchanged Capability Registry → ECR → Module/Plugin → ESR chain — propagating a correlation ID (the external caller's own request ID if supplied, or freshly generated) as EEHF's standard correlation ID.
6. The Response Translator maps the capability's result — success or an EEHF-classified error — into the route's external wire format and returns it.
7. Where an authentication or authorization event at this edge matches a category in the Audit Framework's Mandatory Audit Event Catalog, it is captured exactly as it would be for any internal equivalent — no separate external-audit mechanism.

## 7. Design Patterns

- **Gateway as translation, not as a second mechanism** — the entire document is structured around one discipline: the Gateway translates external shapes (credentials, request formats, error formats) into forms the rest of the library already understands, rather than re-implementing authentication, error classification, or service discovery for "external" traffic specifically.
- **Contract-first external routes** — an external route's request/response schema is a versioned artifact from its first release, mirroring the Workflow Engine's and Notification Framework's own template/definition versioning discipline (EWE §7, ENF §7).
- **Full reuse over parallel construction** — continuing the discipline established since EDM: every internal mechanism (identity, error, versioning, rollout, tracing) is reused unchanged; only the external-facing translation layer is new.

## 8. Security Considerations

*(Citing the Security Principles Catalog directly, per ESA's discipline.)*

- **Principle: Fail-Closed Validation** (ESA catalog) applies to every stage of the Gateway's pipeline — an unauthenticated, unauthorized, malformed, or rate-limit-exceeded request is rejected, never passed through by default.
- **Principle: Least-Privilege** (ESA catalog) applies to what permission an external caller's resolved identity is actually granted — an external partner integration should be authorized only for the specific routes it needs, not broad internal access.
- **The Gateway is the platform's primary externally-reachable attack surface** — as the sole external ingress point (§2 goal), its own availability and correctness are more security-critical than most components in this library; this is a direct consequence of deliberately consolidating all external access through one point rather than exposing capabilities individually.
- **No capability should be reachable from outside the platform except through the Gateway** — any direct external path bypassing authentication/validation/rate-limiting would undermine every control this document establishes.

## 9. Scalability

- **The Gateway sits squarely on the external request path** — its own latency and availability requirements are the most stringent in this library, comparable to or exceeding ESR's and EFF's own request-path disciplines (ESR §9, EFF §9), since every single external request passes through it.
- **Rate limiting must itself be cheap to evaluate** — a rate-limiter check slower than the request it's gating would defeat its own purpose; this mirrors EFF's local evaluation-cache discipline (EFF §7, §9) applied to throttling decisions instead of flag evaluation.
- **Route/contract lookups should be cached, not re-fetched per request** — mirrors the materialized-view/caching discipline used by ECR (§7) and EFF's evaluation cache (§7).

## 10. Best Practices

- Never let a capability be reachable from outside the platform through any path other than the Gateway's authenticated, validated, rate-limited pipeline.
- Version every external route's contract from its first release and classify changes via EVCS before assuming external callers remain compatible.
- Translate, never reinvent — authentication, error classification, and service discovery all belong to existing mechanisms; the Gateway's own logic should be limited to translation and the genuinely new concerns (route definition, rate limiting).
- Honor an external caller's own supplied request/correlation ID where present, rather than discarding it in favor of an internally-generated one, to preserve end-to-end traceability for callers who already track their own request IDs.

## 11. Common Pitfalls

- **Inventing a fourth identity type for external callers** — directly undermines Identity & Access's consolidation goal (Identity & Access §11); an external caller must resolve to an existing Human or Provider identity, with credential *format* translation being the Gateway's only new responsibility.
- **Inventing a second error-response format "for external consumers"** — defeats the purpose of EEHF's shared contract; the Gateway's Response Translator maps EEHF's existing classified errors to a wire format, it does not define new error semantics.
- **Allowing any capability to be reached from outside the platform without going through the Gateway** — reopens exactly the uncontrolled external attack surface this document exists to close.
- **Rate limiting configured so loosely it provides no real protection, or so strictly it blocks legitimate traffic** — both failure modes stem from treating rate-limit thresholds as an afterthought rather than a deliberately configured, per-route decision.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **Expose capabilities directly, with no consolidated gateway** | Let individual modules/plugins each handle their own external exposure. | Fails the single-ingress-point goal outright, multiplying the external attack surface and the number of places authentication/validation/rate-limiting must be independently (and inconsistently) implemented. |
| **A Gateway-specific identity/credential system, separate from Identity & Access** | Build a dedicated external-caller identity model rather than resolving to Identity & Access's existing types. | Directly repeats the identity-fragmentation problem Identity & Access was built to prevent (Identity & Access §11); external callers are still either people or systems, which the existing Human/Provider types already cover. |
| **A Gateway-specific error format for external responses** | Define a new error contract for external consumers instead of translating EEHF's existing one. | Fragments error semantics between internal and external callers for no structural reason; a translation layer over EEHF's existing classified errors serves the same purpose without duplicating taxonomy. |
| **No rate limiting; rely on downstream capacity alone** | Skip explicit throttling at the edge. | Leaves the platform's internal capacity as the only defense against traffic spikes or abuse, when a much cheaper, edge-level control (rate limiting) can prevent load from reaching internal systems at all. |

## 13. Migration Strategy

1. **Stand up the API Route Registry, Authentication/Authorization Enforcement, Request Validator, Rate Limiter, and Response Translator** as new, independently-operable components.
2. **Define the first external route targeting an existing, already-registered Capability ID**, validating the full authenticate → authorize → validate → rate-limit → invoke → translate pipeline before exposing additional routes.
3. **Require every new external route to resolve callers through Identity & Access's existing identity types from day one** — no interim Gateway-specific credential scheme, even temporarily.
4. **Establish rate-limit thresholds per route before any route is exposed to production external traffic.**
5. **Consolidate any pre-existing direct external exposure paths into the Gateway incrementally**, prioritizing the highest-risk or highest-traffic capabilities first.

## 14. Success Criteria

- 100% of externally-reachable capabilities are reachable only through the Gateway's pipeline — zero direct external exposure paths.
- Every external caller resolves to an existing Identity & Access identity type; zero Gateway-specific identity types introduced.
- Every external error response is a translation of an EEHF-classified error; zero independently-invented external error codes outside that taxonomy.
- Every external route has an explicit, configured rate-limit threshold.
- At least one external request is traceable end-to-end via a single correlation ID through EOA's Unified Query Interface, from Gateway entry through the internal chain.

## 15. Decision Matrix

| Criterion (weight) | Consolidated Gateway, full reuse of internal mechanisms (recommended) | No consolidated gateway | Gateway-specific identity system | Gateway-specific error format | No rate limiting |
|---|---|---|---|---|---|
| Single external ingress point (High) | 5 | 1 | 4 | 4 | 4 |
| Reuse of Identity & Access (High) | 5 | 3 | 1 | 4 | 4 |
| Reuse of EEHF's error contract (High) | 5 | 3 | 4 | 1 | 4 |
| Defined rate-limit protection (Medium) | 5 | 2 | 4 | 4 | 1 |
| Implementation/governance overhead (Medium, lower = better fit) | 3 | 4 | 2 | 3 | 4 |
| **Weighted outcome** | **Best overall fit** | Fails ingress-consolidation goal | Fails identity-reuse goal | Fails error-reuse goal | Fails rate-limit goal |

**Conclusion**: a consolidated API Gateway that resolves external callers to Identity & Access's existing identity types, translates (never reinvents) EEHF's error contract, and enforces explicit per-route rate limits is recommended. It is the only option closing the external-ingress gap while fully preserving the reuse discipline this library has maintained since EDM.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-020: Enterprise API Gateway as a Single External Ingress Point, Translating Into Existing Internal Mechanisms**

- **Status**: Accepted
- **Context**: No prior document addresses external ingress — every mechanism built so far assumes a call is already underway inside the platform; this document closes that gap as the final Platform-phase item.
- **Decision**: Introduce an API Route Registry, Authentication/Authorization Enforcement (calling Identity & Access's unchanged interfaces), Request Validator, Rate Limiter, and Response Translator (mapping EEHF's unchanged classified errors to external wire formats). External callers resolve to existing Human or Provider identity types — no new identity type. Route contracts version via EVCS; rollout reuses EFF; rate-limit configuration reuses ECF; tracing reuses EEHF's correlation ID; mandatory audit events reuse the Audit Framework's existing catalog. **No modification to any of the nineteen prior documents.**
- **Rationale**: The Decision Matrix (§15) shows this is the only option that consolidates external access into a single, controlled ingress point while fully reusing the identity, error, versioning, rollout, configuration, tracing, and audit mechanisms already established — avoiding both an uncontrolled external attack surface and a duplicated set of external-specific mechanisms.
- **Consequences**:
  - *Positive*: external access is consolidated, authenticated, validated, and rate-limited through one point; every internal mechanism this library has built is reused without modification; external error responses remain semantically consistent with internal ones.
  - *Negative*: introduces a fifth new Platform-phase component set, and — as the platform's primary external attack surface — carries a higher security/availability bar than most components in this library.
  - *Neutral*: any pre-existing direct external exposure paths must be migrated into the Gateway incrementally (§13), not necessarily all at once.
- **Alternatives rejected**: no consolidated gateway, a Gateway-specific identity system, a Gateway-specific error format, no rate limiting — see §12 and §15.
- **Reversibility**: Moderate reversal cost — external callers and any published API documentation would need to be repointed if the Gateway were decommissioned; the internal mechanisms it reuses are entirely unaffected either way.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Route Registry, Auth Enforcement, Request Validator, Rate Limiter, and Response Translator are specified at architecture level. |
| **Full reuse validation** | Confirmed | §1's reuse map traces every non-translation-specific need to an existing Foundation/Platform mechanism; no new identity type or error format introduced. |
| **Single-ingress-point guarantee** | Needs operational enforcement | The architecture assumes no direct external path bypasses the Gateway; verifying this holds in practice is an implementation/deployment-topology concern, not fixed by this document alone. |
| **Technology-agnostic validation** | Ready | No binding to a specific API gateway product, protocol (REST/GraphQL/gRPC), or rate-limiting algorithm. |
| **Security model maturity** | Ready for design review | Fail-closed and least-privilege principles are cited (§8); this document, as the platform's primary external attack surface, is a strong candidate for early application of ESA's Threat Modeling Methodology alongside Identity & Access and the Audit Framework. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Apply ESA's Threat Modeling Methodology to this document as a priority candidate** — given its role as the platform's primary external attack surface, alongside Identity & Access and the Audit Framework (ESA §18, Identity & Access §18).
- **API documentation/contract publishing** — a future extension to auto-publish the API Route Registry's versioned contracts as external-facing documentation, building on the existing EVCS-classified version history rather than a separate documentation pipeline.
- **Per-caller adaptive rate limiting** — extending beyond static per-route thresholds toward behavior-aware throttling, informed by EEHF's error-signal patterns for a given caller.
- **GraphQL/multi-protocol route support** — extending the Request Validator/Response Translator pair to additional wire protocols beyond a single initial format, without changing the underlying authenticate → authorize → validate → rate-limit → invoke → translate pipeline.

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-020.
