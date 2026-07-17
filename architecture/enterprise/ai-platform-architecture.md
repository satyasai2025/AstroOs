---
title: Enterprise AI Platform Architecture
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise AI Platform Architecture

## 1. Problem Statement

Every document in this library to date has been a **horizontal, cross-cutting concern** — identity, lifecycle, capability mapping, runtime instances, configuration, flags, dependencies, version policy, errors, observability — applicable regardless of what a module or plugin actually *does*. This document is the first **vertical**: it addresses a specific class of capability (AI/LLM-backed functionality) that has needs the ten horizontal documents don't individually anticipate, while reusing every one of them rather than building a parallel, siloed stack.

AI-backed capabilities (the Capability Registry's own worked example, `cap.ai.summary`, anticipated this from the start) introduce concerns not covered by the horizontal library as it stands:

- **Model abstraction** — calling an underlying LLM provider directly, with no gateway, ties a capability's implementation to one vendor/model and makes failover or model-version migration a code change rather than an operational one.
- **Prompt/context versioning** — a prompt template or context-construction strategy is a versioned artifact whose "interface" (expected inputs, output contract) can change in backward-incompatible ways, but no existing document treats prompts as a first-class versioned thing.
- **Cost and usage governance** — LLM calls have a per-call cost (tokens, compute) that no other capability in this library incurs at meaningful scale; nothing in the horizontal library meters or budgets this.
- **Safety and output governance** — AI-generated output requires guardrails (content safety, PII handling, output validation) that have no analog among the deterministic, code-defined capabilities the horizontal documents were designed around.

**This document's central design commitment:** every one of these AI-specific needs is met by *reusing* an existing horizontal framework wherever one already fits, and a genuinely new component is introduced only for the residual gap (model gateway/routing, prompt/context versioning, cost governance, safety guardrails) that no horizontal document covers. This is "reuse before creating" applied at the vertical level, exactly as EDM, EVCS, EEHF, and EOA applied it at the horizontal level.

### Reuse map — what this document does NOT reinvent

| Need | Reused from | How |
|---|---|---|
| AI capability identity & discovery | [Capability Registry](capability-registry.md) (ADR-EAL-003) | AI capabilities are registered as ordinary modules or plugins and indexed under the `cap.ai.*` domain — the exact convention already illustrated by Appendix A's own example, `cap.ai.summary`. |
| AI model/runtime instance tracking | [Service Registry](service-registry.md) (ADR-EAL-004) | A deployed model-serving instance (self-hosted) or gateway instance registers with ESR like any other service instance; the canonical Capability → ECR → Module/Plugin → ESR chain (ADR-EAL-004) is unchanged. |
| Model parameters, prompts-as-config, per-environment/tenant overrides | [Configuration Framework](configuration-framework.md) (ADR-EAL-005) | Model name, temperature, token limits, and similar tunables are ECF configuration keys, layered Platform Default → Environment → Tenant → Instance exactly as ADR-EAL-005 specifies — no second config mechanism. |
| Gradual rollout of a new model/prompt version | [Feature Flag Framework](feature-flag-framework.md) (ADR-EAL-006) | Shifting traffic to a new model version or prompt variant is a targeted, percentage-rollout flag — reuses EFF's sticky bucketing and kill switch, not a new experimentation mechanism. |
| AI capability dependencies (e.g., a summarization capability depending on a retrieval/RAG module) | [Dependency Management](dependency-management.md) (ADR-EAL-007) | Declared via EDM's shared graph, including the cross-provider (module↔plugin) case EDM was built to support. |
| What counts as a breaking change to a prompt/output contract | [Version Compatibility Strategy](version-compatibility-strategy.md) (ADR-EAL-008) | The Prompt & Context Template Registry (§4, new) classifies template changes using EVCS's Breaking-Change Classification Rules rather than inventing a separate prompt-versioning policy. |
| Classifying an AI call failure (timeout, rate limit, upstream unavailable) | [Error Handling Framework](error-handling-framework.md) (ADR-EAL-009) | AI failures map into EEHF's existing, closed taxonomy (`timeout`, `dependency_unavailable`, `client_error`, `internal_error`) with new `err.ai.*` codes *within* those classes — **no new top-level taxonomy class is added**, respecting EEHF's explicit anti-taxonomy-sprawl guidance (EEHF §11). |
| Tracing an AI call across a multi-hop request | [Observability Architecture](observability-architecture.md) (ADR-EAL-010) | AI Gateway calls carry and propagate EEHF's correlation ID; no second tracing identifier. |

**Scope boundary:** this document does not modify any of the ten frozen documents listed above. Where it introduces genuinely new components (§4), those components are additive consumers of the existing frameworks, not replacements.

**Foundational principle (confirmed at approval): AI is an orchestration layer over deterministic engines, never a replacement for them.** Every AI-backed capability in this architecture calls into, summarizes, interprets, or coordinates the output of deterministic modules/plugins (the actual calculation engines registered via PLM/Module Registry) — it does not itself perform the deterministic computation those engines are responsible for. Where a capability's correctness depends on a deterministic result (a calculation, a lookup, a rule evaluation), that result must come from a deterministic provider; the AI layer's role is limited to orchestration, natural-language interpretation/summarization of deterministic output, and coordination across calls — never substituting a model's probabilistic output for a deterministic engine's result.

## 2. Goals

| Goal | Description |
|---|---|
| **Model-agnostic capability implementation** | An AI-backed capability's code depends on a gateway abstraction, not a specific vendor/model SDK directly, enabling failover and model migration without capability-level code changes. |
| **Versioned, governed prompts** | Prompt/context templates are versioned artifacts with an explicit breaking-change policy (via EVCS), not embedded string literals scattered through capability code. |
| **Cost visibility and control** | Every AI call's token/cost usage is metered, attributable to a specific capability and (where applicable) tenant, with budget/quota enforcement available. |
| **Consistent safety governance** | Output safety checks (content policy, PII handling) are applied consistently across all AI-backed capabilities via a shared guardrail layer, not implemented ad hoc per capability. |
| **Full reuse of the horizontal library** | Every applicable existing framework (Capability Registry, ESR, ECF, EFF, EDM, EVCS, EEHF, EOA) is used as-is; no parallel identity, config, flag, dependency, versioning, error, or tracing mechanism is introduced for AI capabilities specifically. |
| **AI as orchestration, never as a replacement for deterministic engines** | AI-backed capabilities orchestrate, interpret, and summarize the output of deterministic modules/plugins; they do not substitute model output for a deterministic engine's calculation. |

**Non-goals**: this document does not build a model-training or fine-tuning platform; it does not replace any horizontal framework; it does not mandate a specific LLM vendor or hosting model (self-hosted vs. API-based); it does not extend EEHF's fixed top-level error taxonomy (§1 reuse map explicitly avoids this); and it does not authorize using an AI model to perform a calculation, lookup, or rule evaluation that a deterministic engine is responsible for.

## 3. Architecture

```
   ┌───────────────────────────┐
   │   Capability Registry (ECR)  │  ← AI capabilities registered under
   │   cap.ai.* domain             │    cap.ai.summary, cap.ai.*, etc.
   └─────────────┬─────────────┘
                 │ resolves to
   ┌─────────────▼─────────────┐
   │   AI Capability Provider     │  ← a module or plugin implementing
   │   (module or plugin, per      │    one or more AI-backed capabilities
   │    ADR-EAL-001/002, unchanged)│
   └─────────────┬─────────────┘
                 │ calls
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Model Gateway / Router      │◄──────┤ Configuration Framework (ECF) │
   │   (new)                       │        │ model params, per env/tenant │
   └─────────────┬─────────────┘        └───────────────────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Prompt & Context Template   │◄──────┤ Version Compatibility        │
   │   Registry (new)              │        │ Strategy (EVCS) — breaking-   │
   │                                │        │ change classification         │
   └─────────────┬─────────────┘        └───────────────────────────┘
                 │
   ┌─────────────▼─────────────┐
   │   Safety & Guardrail Layer     │  ← new: content policy,
   │   (new)                       │    PII handling, output validation
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Cost & Usage Meter           │──────►│ Observability Architecture   │
   │   (new)                       │        │ (EOA) — metrics store         │
   └─────────────┬─────────────┘        └───────────────────────────┘
                 │
   ┌─────────────▼─────────────┐        ┌───────────────────────────┐
   │   Underlying LLM Provider(s)   │        │ Service Registry (ESR) —     │
   │   (self-hosted instance or      │◄──────┤ tracks live model-serving     │
   │    external API)               │        │ instances, if self-hosted     │
   └───────────────────────────┘        └───────────────────────────┘

   Errors at any stage classify into EEHF's existing taxonomy (err.ai.* codes
   within timeout / dependency_unavailable / client_error / internal_error);
   correlation ID (EEHF, traced via EOA) propagates through the entire chain.
```

## 4. Components

Only the following are genuinely new; everything else in the diagram is an existing, unmodified framework being consumed:

- **Model Gateway / Router** *(new)* — abstracts one or more underlying LLM providers behind a stable interface; handles provider/model selection, failover, and request/response normalization, so an AI Capability Provider's code never calls a vendor SDK directly.
- **Prompt & Context Template Registry** *(new)* — stores versioned prompt/context templates as first-class artifacts (not embedded string literals), each with a declared input/output contract; classifies changes to that contract using EVCS's Breaking-Change Classification Rules (EVCS, adopted voluntarily as that document's own precedent already anticipates) rather than an independent versioning scheme.
- **Safety & Guardrail Layer** *(new)* — applies content-policy checks, PII detection/redaction, and output validation consistently across all AI Capability Providers, rather than each implementing its own ad hoc checks.
- **Cost & Usage Meter** *(new)* — records token/compute cost per call, attributed to the originating capability (and tenant, where applicable per ECF's tenant layer), publishing aggregated usage into EOA's Metrics Store (EOA §4) via the Common Event Envelope, and supporting budget/quota enforcement.
- **AI Capability Provider** *(reused pattern, not new)* — an ordinary module or plugin (PLM/Module Registry, unchanged) that happens to implement an AI-backed capability; it is registered, versioned, and lifecycle-managed exactly like any other provider in this library.

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `invoke(capabilityId, input, context)` | AI Capability Provider → Model Gateway / Router | The capability's own code calls this, never a vendor SDK directly; the Gateway resolves provider/model selection (informed by ECF config and EFF rollout flags) internally. |
| `renderPrompt(templateId, templateVersion, variables)` | Model Gateway → Prompt & Context Template Registry | Resolves a versioned template with bound variables into the actual prompt/context sent to the model. |
| `checkOutput(rawOutput, policyProfile)` | Model Gateway → Safety & Guardrail Layer | Validates/redacts model output before it is returned to the calling capability. |
| `recordUsage(capabilityId, tenantId, tokenCounts, cost)` | Model Gateway → Cost & Usage Meter | Records per-call usage; the Meter aggregates and forwards to EOA's Metrics Store. |
| `classifyAIError(rawFailure)` | Model Gateway → (delegates to) EEHF's `classifyError()` | Maps a Gateway-level failure (rate limit, provider timeout, guardrail rejection) to an `err.ai.*` code within EEHF's existing, unmodified taxonomy — no new top-level class. |

## 6. Data Flow

1. A caller resolves an AI-backed capability via the standard chain already established by ADR-EAL-004: **Capability → ECR → Module/Plugin → ESR** (unchanged) — the AI Capability Provider is reached exactly as any other capability's provider would be.
2. The AI Capability Provider calls `invoke()` on the Model Gateway/Router, which reads model-selection parameters from ECF (layered per environment/tenant, ADR-EAL-005) and consults any active EFF rollout flag (ADR-EAL-006) governing which model/prompt variant is currently live.
3. The Gateway calls `renderPrompt()` against the Prompt & Context Template Registry, resolving the correct template version and its variable bindings.
4. The Gateway invokes the underlying LLM provider (a self-hosted instance tracked in ESR, or an external API) — the correlation ID from EEHF is propagated on this call, exactly as EEHF's standard requires (EEHF §4).
5. On response, `checkOutput()` applies the Safety & Guardrail Layer's checks before the result is returned to the calling capability.
6. `recordUsage()` logs token/cost data, which the Cost & Usage Meter aggregates and forwards into EOA's Metrics Store via the Common Event Envelope (EOA §4) — appearing alongside every other document's metrics in the same Unified Query Interface.
7. Any failure at any stage (rate limit, provider timeout, guardrail rejection, template resolution failure) is classified via EEHF's existing `classifyError()` into the appropriate existing class with a new `err.ai.*` code, and returned to the caller using EEHF's unmodified Error Response Contract (retryable/backoff hint included).

## 7. Design Patterns

- **Gateway/adapter pattern** — the Model Gateway/Router is the standard adapter pattern applied to LLM provider abstraction, the same conceptual move ESR already makes for arbitrary network service instances (ESR §7).
- **Versioned template as a first-class artifact** — treating prompts as versioned, governed artifacts (not embedded strings) mirrors how this library treats every other interface (module interfaces, plugin manifests, capability interfaces) as explicitly versioned rather than implicit.
- **Full reuse over parallel construction** — the single most important pattern in this document: every applicable horizontal framework is consumed as-is (§1's reuse map), and new components are scoped strictly to the residual gap, directly continuing the discipline established by EDM, EVCS, EEHF, and EOA.
- **Taxonomy extension via namespaced codes, not new classes** — `err.ai.*` codes are added *within* EEHF's existing classes, never as a new top-level class, respecting EEHF's own explicit guidance against taxonomy sprawl (EEHF §11).

## 8. Security Considerations

- **Prompt injection and output-based attacks** — the Safety & Guardrail Layer must treat model output as untrusted input to any downstream system (consistent with general input-validation discipline), particularly where output could influence further tool calls or be rendered back to end users.
- **PII handling in prompts and outputs** — both the Prompt & Context Template Registry's variable bindings and the Guardrail Layer's output checks must apply data-minimization principles consistent with this library's existing "no secrets/sensitive data in metadata" pattern (PLM §8, Module Registry §8, ECF §8), extended here to personal data in AI context windows.
- **Model/API credentials via ECF's secret-by-reference mechanism** — any API key or credential the Model Gateway needs to reach an external LLM provider is sourced through ECF's existing secrets-by-reference mechanism (ECF §4, §8) — never inline, and no new secrets-handling mechanism is introduced for AI specifically.
- **Cost data as a potential information-disclosure vector** — usage/cost data aggregated per tenant should be access-scoped consistently with EOA's "strictest-applicable-source-policy" principle (EOA §8), since cost patterns can reveal sensitive business information about usage volume.

## 9. Scalability

- **Model Gateway as a potential request-path bottleneck** — because every AI-backed capability call routes through it, the Gateway's own latency and availability characteristics matter more than most components in this library; it should be architected with the same request-path-latency discipline already established for ESR (§9) and EFF's evaluation cache (§9).
- **Template resolution should be cached, not re-fetched per call** — mirrors the materialized-view/caching discipline already used by ECR (§7) and EFF's local evaluation cache (§7): the Prompt & Context Template Registry's read path should not be a per-call round trip if avoidable.
- **Cost/usage aggregation is a high-cardinality metrics problem** — per-capability, per-tenant token/cost data can produce a large number of distinct metric series; the Cost & Usage Meter's aggregation strategy should anticipate this rather than assuming low-cardinality metrics as EOA's other, simpler use cases might.

## 10. Best Practices

- Never call an LLM vendor SDK directly from an AI Capability Provider's own code — always route through the Model Gateway, or model-migration and failover both become code changes instead of operational ones.
- Version every prompt/context template from its first release, and classify every change against EVCS's rules before shipping it, exactly as this library already expects for any other interface.
- Default to the strictest reasonable Safety & Guardrail policy profile and require an explicit, reviewed exception to relax it, rather than defaulting to permissive checks.
- Treat `err.ai.*` codes as extensions within EEHF's existing classes, never as a justification to add a new top-level taxonomy class — if an AI failure doesn't fit an existing class, that's a signal to reconsider the classification, not to expand the taxonomy.

## 11. Common Pitfalls

- **Reinventing configuration, flagging, or dependency mechanisms "because AI is special"** — the single most important pitfall this document is structured to avoid; none of the AI-specific needs identified in §1 actually require a new config, flag, or dependency system — ECF, EFF, and EDM already cover them.
- **Embedding prompts as string literals in capability code** — defeats the versioning and breaking-change-classification goals outright; prompts must go through the Template Registry to get any governance benefit at all.
- **Treating guardrail rejections as generic internal errors** — an output blocked by the Safety & Guardrail Layer is a distinct, classifiable condition (likely `client_error` or a dedicated `err.ai.guardrail_blocked` code) and should not be conflated with an unrelated system fault, which would make it harder for callers to distinguish "your input triggered a policy" from "something broke."
- **Ungoverned cost exposure** — allowing AI-backed capabilities to run without usage metering or budget enforcement risks unbounded cost exposure that no other capability type in this library carries at the same scale.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **Fully siloed AI platform, independent of the horizontal library** | Build AI-specific identity, config, flagging, dependency, versioning, and error handling from scratch. | Directly contradicts "reuse before creating"; every one of these needs is already met by an existing, frozen framework (§1's reuse map) — building parallel mechanisms would be the largest duplication finding in this library's history. |
| **No dedicated AI architecture; ad hoc per-feature implementation** | Let each AI-backed capability call vendor SDKs and manage prompts/costs independently. | Fails model-agnosticism, prompt governance, and cost-visibility goals outright; the status quo this document replaces. |
| **Vendor-SDK-owned integration (no Gateway abstraction)** | Call a single LLM vendor's SDK directly everywhere, accepting vendor lock-in. | Fails the model-agnostic capability goal; makes any future multi-model or failover strategy a capability-code-level change rather than a Gateway-level one. |
| **Extend EEHF's taxonomy with new AI-specific top-level error classes** | Add `ai_error` or similar as a new class rather than namespaced codes within existing classes. | Explicitly rejected per EEHF's own anti-sprawl guidance (EEHF §11); AI failures decompose cleanly into existing classes (timeout, dependency_unavailable, client_error, internal_error) without needing a new one. |

## 13. Migration Strategy

1. **Stand up the Model Gateway/Router first**, even before any AI capability is fully governed by the other new components, so that no future AI Capability Provider is ever written against a vendor SDK directly.
2. **Introduce the Prompt & Context Template Registry and migrate any existing embedded prompt strings into it**, applying EVCS classification to their version history retroactively where feasible.
3. **Wire the Safety & Guardrail Layer into the Gateway's response path** before enabling any new AI-backed capability, so guardrails are the default, not an opt-in retrofit.
4. **Enable the Cost & Usage Meter and establish initial budget/quota thresholds** before any AI-backed capability is exposed to production-scale traffic.
5. **Register each AI-backed capability through the existing Capability Registry under the `cap.ai.*` domain**, exactly as any other capability, and declare its dependencies via EDM where applicable (e.g., a summarization capability depending on a retrieval module).
6. **Use EFF for any model/prompt-version rollout** from the first migration onward, rather than a bespoke rollout mechanism specific to AI.

## 14. Success Criteria

- Zero AI Capability Provider code calls a vendor LLM SDK directly; all calls route through the Model Gateway.
- 100% of prompt/context templates in active use are versioned artifacts in the Template Registry, not embedded string literals.
- Every AI call's token/cost usage is recorded and queryable via EOA's Metrics Store, attributed to a specific capability.
- Zero AI-specific top-level error classes added to EEHF's taxonomy; all AI failures classify into existing classes with `err.ai.*` codes.
- At least one AI-backed capability's model/prompt version rollout is demonstrated end-to-end using EFF's existing rollout mechanism, with no bespoke rollout logic introduced.

## 15. Decision Matrix

| Criterion (weight) | Reuse horizontal library + thin new AI layer (recommended) | Fully siloed AI platform | Ad hoc per-feature implementation | Vendor-SDK-owned, no Gateway | Extend EEHF with new AI error classes |
|---|---|---|---|---|---|
| Reuse of existing frameworks / "reuse before creating" (High) | 5 | 1 | 2 | 3 | 3 |
| Model-agnostic capability implementation (High) | 5 | 4 | 1 | 1 | 5 |
| Prompt governance and versioning (High) | 5 | 4 | 1 | 3 | 5 |
| Cost visibility and control (High) | 5 | 4 | 1 | 3 | 5 |
| Respects EEHF's closed-taxonomy design (Medium) | 5 | 3 | 3 | 3 | 1 |
| Implementation/governance overhead (Medium, lower = better fit) | 3 | 1 | 4 | 4 | 3 |
| **Weighted outcome** | **Best overall fit** | Fails reuse principle | Fails nearly every goal | Fails model-agnosticism | Fails taxonomy discipline |

**Conclusion**: reusing the ten existing horizontal frameworks and introducing only the residual new components (Gateway, Template Registry, Guardrail Layer, Cost Meter) is recommended. It is the only option that meets the AI-specific goals without either duplicating the horizontal library or violating EEHF's explicit taxonomy discipline.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-011: Enterprise AI Platform Architecture as a Thin Vertical Layer Over the Existing Horizontal Library**

- **Status**: Accepted
- **Context**: AI-backed capabilities introduce needs (model abstraction, prompt versioning, cost governance, safety guardrails) not covered by the ten existing horizontal documents, but many apparent AI-specific needs (identity, config, flagging, dependencies, version policy, error classification, tracing) are already fully met by those documents.
- **Decision**: Introduce four new components — Model Gateway/Router, Prompt & Context Template Registry, Safety & Guardrail Layer, Cost & Usage Meter — scoped strictly to the residual gap, while requiring every AI-backed capability to be registered, configured, flagged, dependency-tracked, version-classified, error-classified, and traced using the existing Capability Registry, ESR, ECF, EFF, EDM, EVCS, EEHF, and EOA exactly as already frozen. **No modification to any of the ten prior documents.** AI error conditions extend EEHF's taxonomy only via namespaced `err.ai.*` codes within existing classes — no new top-level class. **Confirmed foundational principle: AI remains an orchestration layer over deterministic engines, never a replacement for deterministic engines** — the Model Gateway, Template Registry, Guardrail Layer, and Cost Meter all exist to govern AI's role in *calling, interpreting, and coordinating* deterministic modules/plugins, not to enable AI output to substitute for a deterministic calculation, lookup, or rule evaluation.
- **Rationale**: The Decision Matrix (§15) shows this is the only option that satisfies both the AI-specific goals and the "reuse before creating" principle this entire library is chartered around; a siloed AI platform would be the single largest duplication event in this library's history, and extending EEHF's taxonomy would violate that document's own explicit guidance. The orchestration-only principle is confirmed as a hard boundary: it protects the correctness guarantees of every deterministic engine registered under PLM/Module Registry from being silently replaced by probabilistic model output.
- **Consequences**:
  - *Positive*: AI capabilities gain model-agnosticism, prompt governance, cost visibility, and safety guardrails while remaining full first-class citizens of every existing horizontal framework; no parallel governance surface for operators to learn; deterministic engines' correctness guarantees remain fully intact and untouched by AI's introduction.
  - *Negative*: teams building AI-backed capabilities must integrate with four new components in addition to the ten existing ones, a real (if narrow) new integration surface; any future proposal to let AI perform a deterministic engine's role would require explicitly superseding this ADR, not a quiet scope creep.
  - *Neutral*: the Model Gateway's own request-path centrality makes its own availability and latency a first-order operational concern going forward.
- **Alternatives rejected**: fully siloed AI platform, ad hoc per-feature implementation, vendor-SDK-owned integration, extending EEHF's taxonomy — see §12 and §15.
- **Reversibility**: The four new components are additive and can be decommissioned without affecting the ten prior documents; however, any AI-backed capability actively depending on the Model Gateway for provider abstraction would need direct-SDK fallback code reinstated — a moderate, not low, reversal cost, comparable to reversing ESR adoption (ESR ADR-EAL-004) rather than EDM's low-cost case.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Gateway, Template Registry, Guardrail Layer, and Cost Meter are specified at architecture level, with explicit reuse mapping to all ten prior documents. |
| **Full reuse validation** | Confirmed | §1's reuse map traces every AI-specific need to either an existing framework or one of the four genuinely new components; no redundant mechanism identified. |
| **Respect for EEHF's closed taxonomy** | Confirmed | AI errors extend via namespaced codes within existing classes only; no new top-level class proposed. |
| **Technology-agnostic validation** | Ready | No binding to a specific LLM vendor, model architecture, or hosting approach (self-hosted vs. API-based). |
| **Security model maturity** | Ready for design review | Prompt-injection/output-trust, PII handling, and credential sourcing via ECF are addressed (§8); no formal threat model performed. |
| **Cost governance model** | Needs decision | Concrete budget/quota thresholds and enforcement actions (soft warning vs. hard block) are flagged for implementation planning, not fixed here. |
| **Orchestration-only boundary** | Confirmed at approval | AI remains an orchestration layer over deterministic engines, never a replacement for them (ADR-EAL-011). Any future proposal to change this requires a superseding ADR. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Retrieval-augmented generation (RAG) as a formalized pattern** — defining a standard shape for a retrieval-dependency-bearing AI capability, building on EDM's cross-provider dependency support (a summarization capability depending on a retrieval module) rather than a bespoke RAG-specific mechanism.
- **Agent/tool-use orchestration** — if AI capabilities evolve toward multi-step, tool-calling agents, a future document could define how tool invocations themselves resolve through the existing Capability Registry rather than a parallel tool-registration mechanism.
- **Automated evaluation harness** — a future capability for systematically evaluating prompt/model version changes before rollout, feeding into EFF's existing progressive-rollout mechanism rather than replacing it.
- **Cost-aware capability routing** — using the Cost & Usage Meter's data to inform Model Gateway routing decisions (e.g., preferring a cheaper model variant under budget pressure), analogous to the traffic-shaping future evolution already flagged for ESR (§18).

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-011.
