---
title: Enterprise Configuration Framework
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Configuration Framework

## 1. Problem Statement

The four frozen registries in this library — [Plugin Lifecycle Management](plugin-lifecycle-management.md) (ADR-EAL-001), [Module Registry](module-registry.md) (ADR-EAL-002), [Capability Registry](capability-registry.md) (ADR-EAL-003), and [Service Registry](service-registry.md) (ADR-EAL-004) — together answer *what exists, who provides it, how to find it, and where it's running*. None of them addresses a related but distinct concern: **how a module, plugin, or running service instance is configured** — its tunable settings, feature flags, environment-specific values, and the secrets it needs indirect access to.

Without a governed configuration model, the same problems this library exists to prevent elsewhere tend to reappear in configuration specifically:

- **Ad hoc, per-provider configuration mechanisms** — each module or plugin invents its own config-loading approach (files, environment variables, hardcoded defaults), with no consistency across the platform.
- **No layered override model** — a value that should differ by environment (dev/staging/prod), by tenant, or by individual service instance has no defined precedence order, leading to "which value actually won" confusion.
- **Secrets handled inconsistently** — some providers inline secrets in config files or environment variables directly, repeating the exact anti-pattern PLM (§8) and the Module Registry (§8) already explicitly forbid for manifests.
- **No validation before delivery** — malformed configuration is often only discovered at provider startup (or worse, at first use), rather than being caught before it reaches a running instance.
- **No safe propagation path** — changing a configuration value often requires a redeploy or restart, undermining the zero/low-downtime goals already established for plugin activation (PLM §2) and instance elasticity (ESR §2).

The Enterprise Configuration Framework (ECF) is the governed model for declaring, layering, validating, and delivering configuration to modules, plugins, and their running service instances — consistently, across the whole platform, referencing existing identities rather than duplicating them.

## 2. Goals

| Goal | Description |
|---|---|
| **Declarative configuration schema** | Every module or plugin declares its configuration surface (keys, types, defaults, required vs. optional) as part of its existing manifest/descriptor — no separate, uncoordinated declaration mechanism. |
| **Deterministic layered resolution** | A well-defined precedence order (e.g., platform default → environment → tenant → instance override) resolves to exactly one effective value per key, with no ambiguity about which layer won. |
| **Secrets by indirection only** | Configuration values that are secrets are never stored or transmitted inline; they are referenced by handle to a secret store, consistent with the existing manifest-hygiene rule (PLM §8, Module Registry §8). |
| **Validate before delivery** | Configuration is validated against its declared schema before it reaches a running instance, not discovered as a runtime failure. |
| **Live reconfiguration where safe** | Configuration changes can propagate to running instances without a restart wherever the change is safe to apply live; changes that aren't safe are explicitly marked as restart-required rather than silently attempted live. |
| **Auditability** | Every configuration change (what changed, at which layer, by whom, when) is recorded, mirroring the transition-logging discipline established in PLM (§4) and the Module Registry (§8). |
| **Identity-referencing, not identity-owning** | Configuration is always attached to an existing module ID, plugin ID, or (where instance-specific) a Service Registry instance — ECF never invents its own parallel identity scheme. |

**Non-goals**: ECF is not a secrets vault itself (it references one); it does not perform capability discovery (ECR's job) or instance health tracking (ESR's job); and it does not replace environment-level infrastructure configuration (networking, deployment topology) that sits below the application layer.

## 3. Architecture

```
   ┌───────────────────────────┐        ┌───────────────────────────┐
   │   Module Registry           │        │   Plugin Registry (PLM)     │
   │   (declares config schema    │        │   (declares config schema    │
   │    as part of descriptor)    │        │    as part of manifest)      │
   └─────────────┬─────────────┘        └─────────────┬─────────────┘
                 │ schema reference                     │ schema reference
                 └────────────────┬────────────────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │   Configuration Schema        │  ← validates declared
                    │   Registry                    │    config schemas
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │   Layered Resolution Engine   │  ← default → env →
                    │                                │    tenant → instance
                    └─────────────┬──────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                        │
┌─────────▼────────┐   ┌──────────▼─────────┐   ┌──────────▼─────────┐
│ Secret Reference   │   │ Validation Gate     │   │ Change Audit Log    │
│ Resolver           │   │                     │   │                     │
└─────────┬────────┘   └──────────┬─────────┘   └──────────┬─────────┘
          │                       │                        │
          └───────────────────────┼────────────────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │   Delivery Channel            │  ← push (live reload) or
                    │                                │    pull-at-startup, per
                    │                                │    declared safety class
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │   Running Instance             │  ← identified via
                    │   (referenced via ESR)          │    Service Registry (ESR)
                    └───────────────────────────┘
```

ECF references module/plugin identity from the Module Registry and PLM, and (for instance-specific overrides or live delivery) references running-instance identity from ESR — it introduces no competing identity scheme of its own.

## 4. Components

- **Configuration Schema Registry** — stores the declared configuration schema for each module/plugin (keys, types, defaults, required/optional, safety class per key — live-reconfigurable vs. restart-required), sourced from the same manifest/descriptor each provider already submits to its home registry (Module Registry or PLM).
- **Layered Resolution Engine** — computes the single effective value for each configuration key by applying a fixed precedence order across layers (§6), never leaving more than one value "active" for a given key at a time.
- **Secret Reference Resolver** — resolves a secret-handle reference in a configuration value to its actual value at the point of delivery, without that value ever being persisted in the Configuration Schema Registry or Layered Resolution Engine's own storage.
- **Validation Gate** — checks a fully-resolved configuration set against its declared schema before it is delivered to any instance, rejecting invalid configurations with a specific diagnostic rather than delivering and failing at the instance.
- **Change Audit Log** — append-only record of every configuration change: key, old value reference, new value reference (never the raw secret value), layer, actor, and timestamp.
- **Delivery Channel** — the mechanism that actually gets resolved, validated configuration to a running instance: a live-push path for keys marked safely reconfigurable, and a pull-at-startup path for keys marked restart-required.

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `declareSchema(providerId, schema)` | Module/plugin manifest (via Module Registry or PLM) → Configuration Schema Registry | Registers the configuration surface for a provider; piggybacks on each provider's existing manifest submission rather than introducing a separate declaration step. |
| `setConfigValue(providerId, key, value, layer)` | Operator/policy → Layered Resolution Engine | Sets a value at a specific layer (environment, tenant, or instance); never bypasses the precedence model. |
| `resolveConfig(providerId, [instanceId])` | Running instance (via ESR identity) or tooling → Layered Resolution Engine | Returns the fully-resolved, validated effective configuration for a provider, optionally scoped to a specific live instance. |
| `getEffectiveValue(providerId, key)` | Consumer/tooling → Layered Resolution Engine | Read-only lookup of a single key's currently effective value and which layer it resolved from (for debugging "which layer won"). |
| `applyLiveChange(providerId, key, value)` | Operator/policy → Delivery Channel | Triggers live propagation for a key marked safely reconfigurable; rejected for restart-required keys with a diagnostic pointing to the safety class. |

## 6. Data Flow

1. A module owner or plugin author declares a configuration schema as part of their existing manifest submission (Module Registry §6 / PLM §5), including, per key: type, default value, required/optional, and safety class (live-reconfigurable or restart-required).
2. The Configuration Schema Registry validates the schema itself (well-formed, no duplicate keys, secret-typed keys reference a secret handle rather than an inline value).
3. An operator or policy sets values at one or more layers via `setConfigValue()` — platform default, environment override, tenant override, or (referencing ESR) a specific instance override.
4. When a value is requested (`resolveConfig()`), the Layered Resolution Engine applies the fixed precedence order (§7) to compute exactly one effective value per key, resolving any secret-handle reference via the Secret Reference Resolver only at this final step — never earlier, and never persisting the resolved secret value.
5. The Validation Gate checks the fully-resolved set against the declared schema before delivery; a failure blocks delivery to that instance and is logged, rather than delivering a partially invalid configuration.
6. The Delivery Channel pushes safely-reconfigurable changes live to already-running instances (identified via ESR) and makes restart-required changes available for pickup at the instance's next startup.
7. Every change at every layer is recorded in the Change Audit Log, mirroring the transition-logging discipline already established for lifecycle events in PLM (§6) and the Module Registry (§8).

## 7. Design Patterns

- **Layered/hierarchical configuration (precedence chain)** — the standard pattern for resolving "most specific override wins": Platform Default → Environment → Tenant → Instance, with each layer only present in the resolution when actually set, and the Resolution Engine deterministic about precedence order.
- **Schema-first validation** — the same fail-fast discipline used elsewhere in this library (PLM's Compatibility Checker, Module Registry's schema validation) applied to configuration: validate before delivery, not after failure.
- **Secrets-by-reference (indirection)** — directly reuses the manifest-hygiene principle already established twice in this library (PLM §8, Module Registry §8): a secret is never inline, only a handle resolved at the point of use.
- **Safety-classed change propagation** — explicitly distinguishing "safe to apply live" from "requires restart" per configuration key, rather than treating all configuration as uniformly hot-reloadable (which risks unsafe live application) or uniformly restart-required (which reintroduces the downtime problem PLM and ESR both aim to avoid).
- **Append-only audit trail** — mirrors the event-sourcing pattern already used for PLM's lifecycle history (PLM §7), applied here to configuration change history.

## 8. Security Considerations

- **Secrets never persisted or logged in resolved form** — the Secret Reference Resolver resolves a handle to its actual value only at delivery time, and the Change Audit Log records the handle/reference, never the resolved secret value, consistent with the "secrets never inline" rule established in PLM (§8) and Module Registry (§8).
- **Write-access governance per layer** — setting a platform-default value is a materially more sensitive operation than setting an instance-level override; `setConfigValue()` must enforce different authorization requirements per layer, not a single flat permission.
- **Validation as a security boundary, not just a correctness one** — a malformed or malicious configuration value (e.g., one that would disable a security control) should be caught by the Validation Gate's schema check before delivery, meaning the schema itself must be able to express security-relevant constraints (e.g., "this flag cannot be set to false in production environment layer").
- **Audit trail integrity** — the Change Audit Log must be tamper-evident (append-only, ideally cryptographically chained or in a write-once store), since it is the primary forensic record for "who changed this security-relevant setting and when."

## 9. Scalability

- **Read-heavy resolution path** — `resolveConfig()` and `getEffectiveValue()` will be called far more often (every instance startup, every live-reload) than `setConfigValue()`; the Layered Resolution Engine's read path should be cached/optimized independently of its write path, mirroring the read/write split noted for the Module Registry (§9) and Capability Registry (§9).
- **Precomputed effective configuration per instance** — rather than recomputing the full layered resolution on every request, the effective configuration for a given provider/instance combination can be materialized and invalidated only when a relevant layer changes, similar to the Capability Registry's materialized-view approach (Capability Registry §7).
- **Live delivery fan-out** — the Delivery Channel's live-push path must scale with instance count (via ESR's instance directory) rather than requiring a linear per-instance push loop that doesn't parallelize.
- **Audit log growth** — as an append-only, potentially high-volume log (especially with frequent tenant/instance-level changes), the Change Audit Log needs a retention/archival strategy distinct from the low-volume ADR/design-document history elsewhere in this library.

## 10. Best Practices

- Always declare configuration schema as part of the existing module/plugin manifest — never introduce a second, uncoordinated place where a provider's configuration surface is described.
- Mark every configuration key's safety class (live-reconfigurable vs. restart-required) explicitly at declaration time; do not default to assuming a key is safe to hot-reload without the provider having stated so.
- Resolve secret handles only at the final delivery step, immediately before use, never earlier in the pipeline and never into a persisted or logged form.
- Keep the precedence order fixed and platform-wide (Default → Environment → Tenant → Instance) rather than allowing per-provider custom precedence rules, which would reintroduce the "which value actually won" ambiguity this framework exists to eliminate.
- Treat validation failures as delivery-blocking, not warnings — an instance should never receive a configuration set that fails its own declared schema.

## 11. Common Pitfalls

- **Treating all configuration as uniformly hot-reloadable** — applying a live change to a key that actually requires a restart to take effect safely (e.g., a value read only once at process boot) can leave a running instance in an inconsistent state; the safety-class declaration (§7) exists specifically to prevent this.
- **Letting secrets leak into the Change Audit Log or resolution cache "for debugging convenience"** — the single most damaging violation of the secrets-by-reference pattern; audit and cache layers must be built assuming they will eventually be read by someone without secret-access privileges.
- **No environment-layer isolation** — allowing a value set in a lower-privilege environment (e.g., staging) to unintentionally affect production resolution due to a shared or misconfigured layer boundary.
- **Schema drift between the manifest and the running instance's actual expectations** — if a provider's code expects a configuration key that was never declared in its schema, validation cannot catch a missing/malformed value for it; schema completeness is the provider owner's responsibility, not something ECF can infer.
- **Building this as a fifth identity-owning registry** — ECF must reference existing module/plugin/instance identities (Module Registry, PLM, ESR) rather than inventing its own parallel notion of "provider," which would fragment identity across the library exactly as ADR-EAL-002 and ADR-EAL-003 were designed to prevent.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **Per-provider ad hoc configuration (status quo)** | Each module/plugin manages its own configuration loading independently. | This is precisely the fragmented, inconsistent state described in §1; fails every goal in §2. |
| **Flat key-value store with no layering** | A single global config store, last-write-wins, no environment/tenant/instance precedence. | Fails the deterministic layered resolution goal; "which value actually won" ambiguity reappears immediately at any meaningful deployment complexity (multiple environments/tenants). |
| **Configuration folded into the Module/Plugin manifests themselves (no separate framework)** | Treat configuration purely as static manifest fields with no resolution engine, secret indirection, or live-delivery mechanism. | Manifests already declare the *schema* (§6) — this document reuses that — but manifests are static, versioned artifacts (Module Registry §1, PLM §5) unsuited to holding frequently-changing environment/tenant/instance values or mediating live secret resolution; conflating the two would force manifest updates for routine configuration changes. |
| **Restart-required for all configuration changes** | Simplify by never supporting live reconfiguration; every change requires redeploy/restart. | Directly undermines the zero/low-downtime goals already established for PLM (§2) and ESR (§2); simpler to build but reintroduces an availability cost this library has otherwise worked to eliminate. |

## 13. Migration Strategy

1. **Introduce the Configuration Schema Registry and require new schema declarations** for any newly-registered module/plugin, without yet requiring existing providers to migrate.
2. **Backfill schemas for existing providers** on a best-effort basis, capturing their real current configuration surface (including identifying any inline secrets that need conversion to secret-handle references as a priority remediation).
3. **Stand up the Layered Resolution Engine and Validation Gate in observe-only mode** for backfilled providers, surfacing discrepancies between assumed and actual configuration before enforcing validation.
4. **Enable validation enforcement and layered resolution for new providers first**, then migrate existing providers incrementally, prioritizing any identified inline-secret remediation.
5. **Enable live-delivery for keys explicitly marked safely reconfigurable**, leaving all unmarked/legacy keys on the restart-required path by default until a provider owner explicitly reclassifies them.
6. **Decommission any legacy ad hoc configuration mechanism** once all providers are migrated and the observe-only discrepancies from step 3 are resolved.

## 14. Success Criteria

- 100% of registered modules/plugins have a declared configuration schema with every key classified as live-reconfigurable or restart-required.
- Zero configuration values delivered to a running instance that fail their own declared schema (Validation Gate has zero bypass incidents).
- Zero secrets found inline in any configuration layer or in the Change Audit Log (periodic audit sweep confirms only handle references are stored).
- Live-reconfigurable changes propagate to all affected running instances within an agreed SLA, with restart-required changes correctly deferred rather than misapplied live.
- 100% of configuration changes at every layer are represented in the Change Audit Log with actor and timestamp populated.

## 15. Decision Matrix

| Criterion (weight) | Layered framework with schema-first validation + secrets-by-reference (recommended) | Ad hoc per-provider config | Flat key-value, no layering | Config folded into manifests only | Restart-required for all changes |
|---|---|---|---|---|---|
| Declarative schema (High) | 5 | 1 | 2 | 4 | 4 |
| Deterministic layered resolution (High) | 5 | 1 | 1 | 2 | 4 |
| Secrets handling (High) | 5 | 1 | 2 | 2 | 3 |
| Validate-before-delivery (High) | 5 | 1 | 2 | 3 | 4 |
| Live reconfiguration support (Medium) | 4 | 2 | 3 | 1 | 1 |
| Auditability (Medium) | 5 | 1 | 2 | 3 | 4 |
| Implementation complexity (Medium, lower = better fit) | 3 | 5 | 4 | 4 | 4 |
| **Weighted outcome** | **Best overall fit** | Fails nearly every goal | Fails layering goal | Fails live-delivery + resolution goals | Fails availability goal |

**Conclusion**: the layered configuration framework with schema-first validation and secrets-by-reference is recommended. As with the prior documents in this library, its main cost is implementation complexity relative to the simpler alternatives, each of which fails at least one **High**-weighted goal outright.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-005: Layered Enterprise Configuration Framework with Schema-First Validation and Secrets-by-Reference**

- **Status**: Accepted
- **Context**: Modules, plugins, and their running service instances all require configuration, but no document in this library addresses how configuration is declared, layered, validated, or safely delivered — a gap left open by ADR-EAL-001 through ADR-EAL-004, which cover identity, lifecycle, capability mapping, and runtime instances respectively but not configuration.
- **Decision**: Adopt a layered configuration model with precedence **Platform Default → Environment → Tenant → Instance** (retained exactly as designed), with configuration schema declared as part of each provider's existing manifest, secrets resolved only by reference/handle at delivery time (never inline, never persisted or logged in resolved form), and every configuration key explicitly classified as **Live Reconfigurable** or **Restart Required** — no key may be left unclassified. Configuration references but does not redefine module/plugin identity (Module Registry, PLM) or instance identity (ESR).
- **Rationale**: This is the only evaluated option that satisfies deterministic layered resolution, schema-first validation, and secrets-by-reference simultaneously (Decision Matrix, §15), while reusing identity and manifest patterns already established elsewhere in this library rather than introducing a competing scheme.
- **Consequences**:
  - *Positive*: consistent, auditable configuration management across all providers; secrets hygiene consistent with PLM/Module Registry precedent; live reconfiguration preserves the zero/low-downtime goals already established elsewhere in this library.
  - *Negative*: adds a fifth operational component; requires all providers to eventually declare a configuration schema and classify each key's safety class, a migration effort tracked in §13.
  - *Neutral*: providers must think explicitly about which configuration keys are safe to change live versus which require a restart — a new authoring discipline, not merely a new store.
- **Alternatives rejected**: ad hoc per-provider configuration, flat unlayered store, manifest-only configuration, restart-required-for-everything — see §12 and §15.
- **Reversibility**: Reversible with moderate cost — providers could fall back to ad hoc configuration if this framework were decommissioned, but any live-reconfiguration behavior already relied upon by operators would need to be replaced by redeploy-based change processes, similar in reversal cost to PLM (PLM §13) rather than to ECR's low-cost reversibility.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Schema declaration, layered resolution, secrets handling, and delivery model are specified at architecture level. |
| **Consistency with ADR-EAL-001 through 004** | Confirmed | References but does not redefine module/plugin/instance identity owned by the four prior registries. |
| **Technology-agnostic validation** | Ready | No binding to a specific config store, secrets vault, or delivery transport. |
| **Security model maturity** | Ready for design review | Secrets-by-reference and per-layer write governance are defined (§8); no formal threat model performed yet. |
| **Live-reconfiguration safety model** | Needs decision | The safety-classification mechanism (live-reconfigurable vs. restart-required) is specified conceptually; concrete criteria for classifying a given key are an implementation-phase activity. |
| **Dependency on prior documents** | Depends on Module Registry, PLM, and ESR remaining stable | References their identity/manifest patterns; a future superseding ADR to any of those three would require a corresponding review here. |
| **Hierarchy, secrets, and key classification** | Confirmed at approval | Platform Default → Environment → Tenant → Instance retained; secrets remain reference/handle-only; every key classified Live Reconfigurable or Restart Required (ADR-EAL-005). |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Policy-as-code validation rules** — extending the Validation Gate beyond type/shape schema checks toward declarative policy rules (e.g., "this flag must be false in production"), echoing the policy-as-code future evolution already flagged for the Module Registry (§18).
- **Capability-maturity-aware configuration defaults** — using the Capability Registry's maturity lifecycle (Appendix B) to drive different default configuration postures for EXPERIMENTAL vs. STABLE capabilities (e.g., more verbose logging defaults for experimental capabilities).
- **Configuration drift detection** — periodically comparing an instance's actually-observed configuration (self-reported) against the Resolution Engine's computed effective value, surfacing drift before it causes a support incident.
- **Progressive/canary configuration rollout** — applying a live configuration change to a subset of instances first (via ESR's instance directory) before full propagation, mirroring the progressive-activation pattern already flagged as future evolution in PLM (§18) and ESR (§18).

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-005.
