---
title: Enterprise Feature Flag Framework
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Feature Flag Framework

## 1. Problem Statement

The frozen [Enterprise Configuration Framework](configuration-framework.md) (ADR-EAL-005) governs how modules, plugins, and service instances are configured, resolved through a fixed layered precedence (Platform Default → Environment → Tenant → Instance). That model answers "what value does this provider/instance currently have for this key" — but it does not answer a related, functionally distinct question: **should this specific request, user, or account see this behavior right now**, independent of which instance happens to serve it.

Feature flagging has requirements that don't fit cleanly into ECF's layering model:

- **Request/user/tenant-level targeting** — a flag's value often needs to vary by attributes of the individual request (user segment, account cohort, percentage rollout bucket), not just by environment/tenant/instance layer.
- **High-frequency, low-latency evaluation** — a flag may be evaluated many times per second per instance (once per request), a very different access pattern from ECF's comparatively infrequent instance-level configuration resolution.
- **Progressive rollout semantics** — gradually shifting a percentage of traffic/users onto new behavior, then adjusting or reversing that percentage, is a first-class flag operation with no direct ECF analog.
- **A distinct maturity lifecycle** — a flag's own lifecycle (planned, being rolled out, fully rolled out, ready for cleanup) is conceptually close to, but not identical to, the Capability Lifecycle already defined in the Capability Registry (Appendix B), and is not something ECF's live-reconfigurable/restart-required classification captures.
- **Kill-switch semantics** — a flag is frequently used as an emergency off-switch for a specific behavior, which demands near-instant, request-path-suitable propagation distinct from ECF's live-reconfigurable delivery path (which is designed for instance-level settings, not per-request evaluation).

The Enterprise Feature Flag Framework (EFF) is the dedicated model for declaring, targeting, evaluating, and retiring feature flags — reusing ECF's secrets-and-layering discipline where it fits, but built as its own component rather than forced into ECF's shape.

### Relationship to the Enterprise Configuration Framework

This document's scope is deliberately distinct from, but designed to sit alongside, the frozen ECF (ADR-EAL-005):

| | **Feature Flag Framework (this document)** | **Configuration Framework (ECF, ADR-EAL-005)** |
|---|---|---|
| Answers | "Should this request/user see behavior X right now?" | "What is this provider/instance's current setting for key Y?" |
| Evaluation granularity | Per-request/per-user/per-cohort, evaluated in the request path | Per-provider/per-instance, resolved at startup or live-reload |
| Primary axis of variation | Targeting rules (segment, percentage, cohort) | Layer precedence (default/environment/tenant/instance) |
| Lifecycle | Flag-specific: Planned → Rolling Out → Fully Rolled Out → Cleanup-Pending → Retired (§6 below) | Key-level classification only: Live Reconfigurable / Restart Required |
| Typical operation | Gradual rollout, A/B assignment, kill switch | Set a value, resolve a value |

A flag's underlying **on/off state at the top level** may itself be sourced through ECF's layering (e.g., a flag can be globally disabled via an environment-layer override) — EFF does not duplicate secrets handling or environment/tenant layering where ECF's model already applies. But the per-request targeting/percentage evaluation that makes something a "feature flag" rather than a "configuration value" is EFF's distinct responsibility. This boundary is treated as authoritative for both documents, consistent with the non-merging precedent already established between the Module Registry and Plugin Registry (ADR-EAL-002).

## 2. Goals

| Goal | Description |
|---|---|
| **Declarative flag definitions** | Every flag has an explicit definition: identity, targeting rules, default/fallback value, and owner. |
| **Request-path-suitable evaluation** | Flag evaluation must be fast enough to run on every request without becoming a latency bottleneck. |
| **Deterministic, sticky targeting** | The same user/request consistently receives the same flag outcome for the duration of a rollout (no flip-flopping), unless the targeting rule itself changes. |
| **Progressive rollout control** | Percentage-based and cohort-based rollout can be adjusted (increased, decreased, halted) without a deploy. |
| **Kill-switch reliability** | Disabling a flag must propagate with very low latency and very high reliability — a kill switch that itself might not fire promptly defeats its purpose. |
| **Governed flag lifecycle** | Flags are not created and forgotten; each has a lifecycle that ends in either permanent configuration or code removal, preventing indefinite flag accumulation ("flag debt"). |
| **Reuse of existing primitives** | Where a flag's behavior is genuinely just a configuration value (no per-request targeting), it is expressed through ECF rather than duplicated in EFF. |

**Non-goals**: EFF is not a general experimentation/analytics platform (it may emit assignment events *to* one, but does not itself compute statistical significance or run experiment analysis); it does not replace ECF for provider/instance-level settings that have no per-request targeting dimension; and it does not alter module/plugin/capability/instance identity owned by the four registries.

## 3. Architecture

```
   ┌───────────────────────────┐
   │   Configuration Framework    │  ← a flag's global on/off can be
   │   (ECF, ADR-EAL-005)          │    sourced via ECF layering
   └─────────────┬─────────────┘
                 │ (optional) global toggle layer
                 │
   ┌─────────────▼─────────────┐
   │   Flag Definition Registry   │  ← identity, targeting rules,
   │                               │    default/fallback, owner
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐
   │   Targeting & Rollout        │  ← percentage buckets, cohort
   │   Rule Engine                │    rules, sticky assignment
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐
   │   Evaluation Cache /          │  ← low-latency, request-path
   │   Local SDK Snapshot          │    evaluation surface
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐
   │   Assignment Event Emitter   │  ← optional: feeds external
   │                               │    experimentation/analytics
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐
   │   Flag Lifecycle Tracker     │  ← Planned → Rolling Out →
   │                               │    Fully Rolled Out → Cleanup
   └───────────────────────────┘
```

EFF sits beside ECF (not on top of or beneath it): a flag definition may reference an ECF-managed configuration value as its global kill-switch layer, but EFF owns targeting, rollout percentage, and per-request evaluation outright.

## 4. Components

- **Flag Definition Registry** — the declarative store of flag identity, targeting rule set, default/fallback value, and owning team; analogous in role to the Module Registry's catalog (Module Registry §4) but scoped to flags rather than modules.
- **Targeting & Rollout Rule Engine** — evaluates a flag's targeting rules (percentage bucket, cohort membership, explicit allow/deny lists) against a given request/user context to produce a deterministic outcome.
- **Evaluation Cache / Local SDK Snapshot** — a low-latency, request-path-local evaluation surface (e.g., an in-process cache refreshed periodically or via push) so that evaluating a flag on every request does not require a network round trip per evaluation.
- **Assignment Event Emitter** — optionally publishes "this user/request saw this flag outcome" events for consumption by an external experimentation/analytics system; EFF does not itself compute experiment results.
- **Flag Lifecycle Tracker** — governs a flag's progression from creation to retirement (§6), preventing indefinite accumulation of stale flags in the codebase.

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `defineFlag(flagId, targetingRules, defaultValue, owner)` | Flag owner → Flag Definition Registry | Declares a new flag; analogous to `registerModule()` (Module Registry §5) but for flags. |
| `evaluate(flagId, requestContext)` | Consuming code (request path) → Evaluation Cache | The primary, high-frequency call: returns the flag's outcome for a given request/user context, evaluated locally against the cached snapshot wherever possible. |
| `updateRollout(flagId, percentage or cohortRule)` | Flag owner/operator → Targeting & Rollout Rule Engine | Adjusts rollout percentage or targeting rule without a deploy. |
| `killSwitch(flagId)` | Operator → Targeting & Rollout Rule Engine | A dedicated, high-priority path to force a flag to its safe/disabled outcome immediately, bypassing normal rollout-percentage propagation latency. |
| `promoteLifecycleStage(flagId, stage)` | Flag owner/governance → Flag Lifecycle Tracker | Advances a flag through its lifecycle (§6); a required, explicit governance action, never implicit. |
| `emitAssignment(flagId, requestContext, outcome)` | Evaluation Cache → Assignment Event Emitter | Fires (where enabled) an assignment event for external experimentation/analytics consumption. |

## 6. Flag Lifecycle

Distinct from both PLM's plugin activation state machine and the Capability Registry's capability maturity lifecycle (Capability Registry, Appendix B), a feature flag progresses through a lifecycle oriented around rollout progress and eventual flag removal, since an indefinitely-lived flag accumulates complexity ("flag debt") that this framework is explicitly designed to prevent:

```
 PLANNED
    │
    ▼
 ROLLING OUT
    │
    ▼
 FULLY ROLLED OUT
    │
    ▼
 CLEANUP-PENDING
    │
    ▼
 RETIRED
```

- **PLANNED** — the flag is defined (targeting rules, default/fallback) but not yet evaluated against real traffic; a reservation/declaration stage, mirroring the Capability Registry's PROPOSED stage in spirit.
- **ROLLING OUT** — the flag is live and its rollout percentage/cohort targeting is actively being adjusted; the normal, expected operating state for a flag under progressive rollout.
- **FULLY ROLLED OUT** — targeting resolves to the "on" outcome for effectively all traffic; the flag is still evaluated (so a kill switch remains available) but is no longer being actively tuned.
- **CLEANUP-PENDING** — a governance signal that the flag has served its purpose (fully rolled out and stable for an agreed period) and the underlying code should now be simplified to remove the flag check entirely; this stage exists specifically to counter flag debt (§11) by making cleanup a tracked, visible obligation rather than an informal afterthought.
- **RETIRED** — the flag definition is removed from the Flag Definition Registry once the corresponding code cleanup has shipped; as with the Capability Registry's REMOVED stage (Capability Registry, Appendix B), a retired flag ID is never reused for a different flag.

**Governance notes:**

- Advancing to CLEANUP-PENDING should be a tracked, queryable state — ideally surfaced to owning teams on a recurring basis — precisely because the failure mode this lifecycle exists to prevent is flags that quietly stay in FULLY ROLLED OUT (or worse, ROLLING OUT) forever.
- A flag never skips PLANNED → ROLLING OUT; evaluation against real traffic before a deliberate rollout decision would undermine the sticky/deterministic targeting goal (§2).
- Reverting a flag (rolling back after issues at any stage) is a normal operation, not a lifecycle violation — the lifecycle tracks forward progress toward retirement, not a one-way ratchet on rollout percentage itself.

## 7. Design Patterns

- **Client-side (SDK) evaluation cache** — mirrors best practice in mature feature-flag systems: push flag definitions/targeting rules to a local cache near the request path, evaluate locally, and only call back to a central service for infrequent definition/rule updates — this is what makes the request-path-suitable goal (§2) achievable at scale.
- **Sticky/deterministic bucketing** — percentage rollout is implemented via a deterministic hash of a stable identifier (user ID, account ID) rather than random assignment per request, so a given user's outcome doesn't flip between requests during a partial rollout.
- **Kill switch as a distinct, higher-priority path** — rather than treating "disable" as just another rollout-percentage update, a dedicated kill-switch interface (§5) is prioritized for lower latency and higher reliability, since its use case is inherently time-sensitive (incident response).
- **Governed lifecycle to counter entropy** — directly reuses the governed-deprecation discipline already established in the Module Registry (§10, §13) and the Capability Registry (Appendix B), applied to the specific failure mode of accumulating stale flags.

## 8. Security Considerations

- **Targeting rules must not leak sensitive segmentation logic to clients** — where evaluation happens client-side (browser, mobile), targeting rules that reference sensitive attributes (internal risk scores, account tiers tied to pricing) should be evaluated server-side or via an intermediary, not shipped as raw rules to an untrusted client.
- **Kill-switch authorization** — because `killSwitch()` is a high-impact, immediate-effect operation, it should have clear, auditable authorization (who can invoke it) distinct from routine `updateRollout()` permissions, similar in spirit to the elevated write-governance already established for platform-default-layer changes in ECF (ECF §8).
- **Assignment event data minimization** — `emitAssignment()` events sent to external experimentation/analytics systems should avoid carrying more request-context detail than the receiving system actually needs, consistent with general data-minimization practice.
- **No secrets in targeting rules** — as with every manifest/schema pattern elsewhere in this library (PLM §8, Module Registry §8, ECF §8), targeting rules are metadata/logic, never a place to embed credentials or secret material.

## 9. Scalability

- **Evaluation is the dominant workload by a wide margin** — `evaluate()` may be called on every request across the platform, several orders of magnitude more frequently than `updateRollout()` or `defineFlag()`; the entire architecture (§3) is built around making that specific call cheap (local cache) rather than optimizing the rarely-called write paths.
- **Definition/rule propagation latency vs. evaluation latency are different budgets** — propagating an `updateRollout()` change to all evaluation caches can tolerate more latency (seconds) than the `evaluate()` call itself (which must be sub-millisecond-class to avoid becoming a request-path bottleneck), except for the kill-switch path, which needs both low propagation and low evaluation latency.
- **Assignment event volume can dwarf configuration change volume** — if assignment-event emission is enabled at full request volume, the Assignment Event Emitter's throughput requirements may exceed anything else in this library; sampling should be a supported option rather than assuming full-volume emission is always desired.
- **Flag count growth is bounded by the lifecycle, not just capacity** — the Flag Lifecycle (§6) is itself a scalability control: without governed retirement, the number of live flags (and thus targeting rules to evaluate) grows unboundedly.

## 10. Best Practices

- Default to expressing anything without a genuine per-request targeting dimension as an ECF configuration value, not an EFF flag — reserve flags for cases that actually need targeting, rollout percentage, or a kill switch.
- Always define a safe fallback/default value for every flag, used when evaluation cannot reach a fresh definition (cache miss, network partition) — a flag should fail toward its safest behavior, not throw or block the request.
- Treat `killSwitch()` as a distinct, well-tested operational path, not merely "set rollout to 0%" — its latency and reliability guarantees should be verified independently of normal rollout-percentage propagation.
- Make CLEANUP-PENDING visible and actionable (e.g., a recurring report of flags in that state) rather than a passive label nobody looks at — the lifecycle only counters flag debt if it's actually acted upon.
- Use deterministic, sticky bucketing keyed on a stable identifier for any percentage rollout — never re-randomize assignment per request.

## 11. Common Pitfalls

- **Flag debt** — flags left indefinitely in ROLLING OUT or FULLY ROLLED OUT with no path to CLEANUP-PENDING/RETIRED, accumulating branching complexity in code long after the rollout decision has effectively been made; the single most common failure mode in feature-flag systems generally, which is why §6's lifecycle exists as a first-class concern rather than an afterthought.
- **Non-sticky (random-per-request) targeting** — causes a user to see inconsistent behavior across requests during a partial rollout, which is confusing at best and can produce data-integrity issues (e.g., mixed-version behavior within a single user session) at worst.
- **Conflating a flag's global kill-switch with its targeting rules** — treating "fully off" as just another targeting-rule permutation rather than a distinct, prioritized kill-switch path can mean an incident-response disable is subject to the same propagation latency as routine rollout tuning, when it needs to be faster and more reliable.
- **Duplicating ECF's layering inside EFF** — reimplementing environment/tenant precedence logic within the flag system rather than sourcing a flag's global toggle through ECF where no per-request targeting is actually needed, which fragments configuration logic across two systems unnecessarily.
- **Shipping sensitive targeting logic to untrusted clients** — see §8; a common mistake when evaluation is naively implemented purely client-side without considering what the targeting rules themselves reveal.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **Fold feature flags into the Configuration Framework** | Model flags purely as ECF configuration keys with no separate targeting/rollout engine. | ECF's layering (environment/tenant/instance) has no native concept of per-request/per-user targeting or percentage rollout with sticky bucketing; forcing this into ECF would either leave those capabilities unbuilt or bolt them onto a system explicitly scoped (ECF §2 non-goals) to avoid them — the same design-integrity concern that kept the Module and Plugin Registries separate (ADR-EAL-002). |
| **No dedicated framework; ad hoc if/else flags in code** | Flags implemented as scattered conditional branches with hardcoded or environment-variable-driven toggles. | Fails nearly every goal in §2 — no targeting, no progressive rollout control, no governed lifecycle, no kill-switch reliability guarantee; the status quo this document replaces. |
| **Full experimentation platform as the primary model** | Adopt a full A/B-testing/experimentation platform as the flag system, with EFF's scope absorbed into it. | Conflates flagging (a delivery/operations concern) with experimentation analysis (a statistical/product-analytics concern); this document instead treats experimentation platforms as an optional downstream consumer of assignment events (§4), keeping EFF's own scope narrower and reusable even for teams with no experimentation platform. |
| **Central-only evaluation (no local cache/SDK)** | Every `evaluate()` call is a network round trip to a central flag service. | Fails the request-path-suitable evaluation goal outright at any meaningful request volume; latency and availability would make EFF itself a request-path dependency and single point of failure, the opposite of the intended design. |

## 13. Migration Strategy

1. **Stand up the Flag Definition Registry and Targeting & Rollout Rule Engine** independently of any existing ad hoc flagging mechanism (environment variables, hardcoded conditionals).
2. **Introduce the local Evaluation Cache/SDK pattern for new flags first**, validating request-path latency characteristics before migrating existing ad hoc flags.
3. **Inventory existing ad hoc flags and classify each** as either a genuine EFF candidate (needs targeting/rollout) or an ECF candidate (a plain configuration value with no per-request targeting need) — not everything currently called a "flag" necessarily belongs in EFF.
4. **Migrate genuine flag candidates into EFF**, starting each in PLANNED and progressing deliberately through the lifecycle (§6), rather than bulk-importing them directly into ROLLING OUT.
5. **Establish the CLEANUP-PENDING reporting mechanism** before or alongside the first wave of migrations, so flag debt does not begin accumulating again immediately after migration.
6. **Decommission the legacy ad hoc flagging mechanism** once all genuine flag candidates are migrated and the remaining, reclassified configuration-only values are handled via ECF instead.

## 14. Success Criteria

- 100% of flags have a declared definition (targeting rules, default/fallback, owner) in the Flag Definition Registry — no undeclared, code-only flags remain.
- `evaluate()` latency stays within the request-path-suitable target defined during implementation planning, verified under representative load.
- Kill-switch propagation (from `killSwitch()` invocation to effective disablement across all evaluation caches) meets an agreed, tested SLA distinct from and faster than routine rollout-percentage propagation.
- Zero user-visible inconsistency incidents traced to non-sticky/non-deterministic targeting during a partial rollout.
- No flag remains in FULLY ROLLED OUT beyond an agreed grace period without either advancing to CLEANUP-PENDING or an explicit, recorded exception.
- 100% of flag lifecycle transitions are recorded with actor and timestamp, mirroring the auditability discipline established elsewhere in this library.

## 15. Decision Matrix

| Criterion (weight) | Dedicated flag framework beside ECF (recommended) | Fold into Configuration Framework | Ad hoc code-level flags | Full experimentation platform as primary model | Central-only evaluation (no local cache) |
|---|---|---|---|---|---|
| Request-path-suitable evaluation (High) | 5 | 2 | 3 | 3 | 1 |
| Deterministic sticky targeting (High) | 5 | 1 | 1 | 4 | 4 |
| Progressive rollout control (High) | 5 | 1 | 1 | 4 | 4 |
| Kill-switch reliability (High) | 5 | 2 | 2 | 3 | 2 |
| Governed lifecycle / anti flag-debt (Medium) | 5 | 2 | 1 | 3 | 3 |
| Design integrity (does not distort ECF) (Medium) | 5 | 1 | 5 | 4 | 4 |
| Reuse of existing primitives (Medium) | 4 | 5 | 2 | 2 | 3 |
| **Weighted outcome** | **Best overall fit** | Fails targeting/rollout goals | Fails nearly every goal | Over-scoped, conflates concerns | Fails latency goal |

**Conclusion**: a dedicated feature-flag framework, built beside (not inside) ECF and reusing its layering only for genuinely non-targeted global toggles, is recommended. It is the only option that satisfies request-path evaluation, sticky targeting, and progressive rollout simultaneously without distorting the already-accepted ECF design (ADR-EAL-005).

## 16. Architecture Decision Record (ADR)

**ADR-EAL-006: Enterprise Feature Flag Framework as a Dedicated Component Beside the Configuration Framework**

- **Status**: Accepted
- **Context**: ECF (ADR-EAL-005) governs layered configuration resolution for providers and instances but has no concept of per-request/per-user targeting, progressive rollout, or a flag-specific lifecycle — capabilities feature flagging requires that would distort ECF's scope if bolted on.
- **Decision**: Introduce a dedicated Enterprise Feature Flag Framework with its own Flag Definition Registry, Targeting & Rollout Rule Engine, local Evaluation Cache/SDK, optional Assignment Event Emitter, and a distinct Flag Lifecycle (Planned → Rolling Out → Fully Rolled Out → Cleanup-Pending → Retired). A flag's global kill-switch layer may source from ECF where no per-request targeting is needed, but EFF is not folded into ECF.
- **Rationale**: The Decision Matrix (§15) shows folding flags into ECF fails the targeting, rollout, and kill-switch goals that motivate a separate flag system in the first place, while a fully separate experimentation platform over-scopes the problem by conflating flag delivery with statistical analysis. A dedicated, narrowly-scoped framework satisfies all high-weighted goals without compromising ECF's already-accepted design.
- **Consequences**:
  - *Positive*: request-path evaluation performance is achievable via local caching without burdening ECF's design; progressive rollout and kill-switch operations get dedicated, appropriately-prioritized paths; the governed lifecycle directly targets flag debt as a named, tracked problem.
  - *Negative*: introduces a sixth operational component to the library; teams must learn to classify "is this an ECF value or an EFF flag" correctly (§13 step 3), which requires judgment rather than a purely mechanical rule.
  - *Neutral*: assignment-event emission is optional and does not itself constitute an experimentation platform — teams wanting statistical experiment analysis must still adopt or build one downstream.
- **Alternatives rejected**: folding into ECF, ad hoc code-level flags, full experimentation platform as primary model, central-only evaluation — see §12 and §15.
- **Reversibility**: Reversible in principle (flags without genuine targeting needs could be migrated back into ECF via a superseding ADR), but flags actively mid-rollout at the time of reversal would need individual handling; moderate reversal cost, comparable to ECF's own reversibility profile (ECF ADR-EAL-005) rather than to ECR's low-cost case.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Definition, targeting/rollout, evaluation caching, and lifecycle are specified at architecture level. |
| **Boundary with ECF** | Ready for review, flagged for joint sign-off | §1's relationship table and ADR-EAL-006 define the boundary explicitly; recommend review alongside the frozen ECF document before this document freezes, consistent with how the Module/Plugin Registry boundary was handled (ADR-EAL-002). |
| **Technology-agnostic validation** | Ready | No binding to a specific flag-evaluation SDK, caching technology, or transport. |
| **Security model maturity** | Ready for design review | Client-side targeting exposure and kill-switch authorization are identified (§8); no formal threat model performed yet. |
| **Latency/propagation model** | Needs decision | Concrete SLA targets for evaluation latency and kill-switch propagation (§9, §14) are flagged for implementation planning, not fixed here. |
| **Dependency on prior documents** | Depends on ECF and the Capability Registry remaining stable | References ECF's layering for global toggles and takes lifecycle-design inspiration from the Capability Registry's maturity model; a future superseding ADR to either would warrant review here. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Automated CLEANUP-PENDING enforcement** — tooling that flags a stale flag for removal automatically once it has been FULLY ROLLED OUT beyond a defined threshold, rather than relying solely on manual governance review.
- **Capability-Registry-aware flags** — linking a flag's rollout to a capability's maturity stage (Capability Registry, Appendix B), e.g., automatically gating a flag's rollout ceiling while its underlying capability remains EXPERIMENTAL.
- **Server-side targeting evaluation as a security hardening step** — moving all targeting-rule evaluation server-side by default (§8), with client-side evaluation reserved for pre-vetted, non-sensitive rule sets only.
- **Native experimentation integration** — a formal, first-class integration contract for the optional Assignment Event Emitter output, rather than treating experimentation-platform integration as purely a downstream consumer's concern.

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-006.
