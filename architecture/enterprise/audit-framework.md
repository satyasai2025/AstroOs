---
title: Enterprise Audit Framework
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Audit Framework

## 1. Problem Statement

[Observability Architecture](observability-architecture.md) (EOA, ADR-EAL-010) already ingests events from any voluntarily-adopting emitter into a Log Store, with retention explicitly flagged as "needs decision" per source document (EOA §17). That is the right posture for *operational* observability — but it is the wrong posture for a specific, smaller class of events this library has already, repeatedly, called "audit": the Module Registry's ownership-transfer record (Module Registry §8), ECF's Change Audit Log (ECF §4, §8), and [Identity & Access](identity-and-access.md)'s permission grant/revoke history (Identity & Access §6, §8) are not optional operational telemetry — they are compliance-relevant records that must exist, must be tamper-evident, and must be retained for a defined minimum period regardless of whether any particular operator chooses to adopt EOA's voluntary envelope.

This document does not introduce a second event-ingestion mechanism (that would repeat the exact duplication this library has avoided since EDM). Instead, it does three things EOA's deliberately voluntary, general-purpose posture does not:

1. **Designates specific event categories as mandatory**, not optional — a closed catalog of what must always produce a compliance-grade record, rather than leaving adoption to each emitter's own choice (EOA's model).
2. **Guarantees tamper-evidence and a retention floor** stronger than EOA's general Log Store provides, with that floor enforced through Identity & Access's authorization model so it cannot be silently lowered via ordinary configuration.
3. **Provides a compliance-oriented query/export interface** — "every action by this identity," "every change to this resource, ever" — distinct from EOA's operational Unified Query Interface, which is designed for incident investigation, not audit/compliance response.

### Reuse map

| Need | Reused from | How |
|---|---|---|
| Event envelope and ingestion transport | [Observability Architecture](observability-architecture.md) (ADR-EAL-010) | Mandatory-class events use the same Common Event Envelope and Ingestion Gateway, routed to the Compliance Audit Log in addition to (not instead of) EOA's general Log Store — no second transport mechanism. |
| Which existing events are designated mandatory | [Identity & Access](identity-and-access.md) (ADR-EAL-018), [Module Registry](module-registry.md) (ADR-EAL-002), [Configuration Framework](configuration-framework.md) (ADR-EAL-005) | This document designates, rather than redefines, permission grant/revoke, ownership transfer, and configuration changes as mandatory-audit-class — the underlying events themselves are unchanged. |
| Correlation across an audited action's context | [Error Handling Framework](error-handling-framework.md) (ADR-EAL-009) | Reuses EEHF's unchanged correlation ID. |
| Retention-floor enforcement | [Identity & Access](identity-and-access.md) (ADR-EAL-018) | Lowering retention below the compliance-mandated floor requires a specific, named permission (`checkPermission()`), not ordinary configuration write access. |
| Retention/legal-hold parameters (above the floor) | [Configuration Framework](configuration-framework.md) (ADR-EAL-005) | Layered exactly per ADR-EAL-005 for anything at or above the mandatory floor. |
| Audit-pipeline failure classification | [Error Handling Framework](error-handling-framework.md) (ADR-EAL-009) | Classifies via EEHF's existing taxonomy with new `err.audit.*` codes. |
| Citing applicable security principles | [Security Architecture](security-architecture.md) (ADR-EAL-017) | Cites "Principle: Audit-Trail Integrity" directly rather than restating it. |

**Scope boundary:** this document does not modify any of the eighteen prior documents, including EOA's own voluntary-adoption model. It designates specific existing events as mandatory and adds a higher-guarantee store and compliance query interface alongside EOA's general one.

## 2. Goals

| Goal | Description |
|---|---|
| **A closed, named catalog of mandatory audit events** | Specific event categories (permission changes, ownership transfers, configuration changes, and others as designated) are compliance-mandatory, not left to voluntary adoption. |
| **Tamper-evidence stronger than general observability data** | The Compliance Audit Log is append-only and tamper-evident by construction, not merely by convention. |
| **An enforced retention floor** | A minimum retention period exists for mandatory-class records, and lowering it below that floor requires a specific, named permission — it cannot happen via ordinary configuration. |
| **A compliance-oriented query/export interface** | Distinct from EOA's operational Unified Query Interface, designed around "every action by this identity" and "every change to this resource" queries an auditor or compliance officer actually needs. |
| **No duplicate ingestion mechanism** | Reuses EOA's Common Event Envelope and Ingestion Gateway unchanged; this document adds a routing designation and a second, higher-guarantee store, not a second pipeline. |

**Non-goals**: this document does not replace EOA's general-purpose, voluntary observability model (that remains fully in effect for anything not designated mandatory); it does not define new authorization mechanics beyond citing Identity & Access; and it does not itself perform compliance certification against any specific external regulatory regime — it provides the mechanism a compliance program would use.

## 3. Architecture

```
   ┌───────────────────────────┐
   │   Any emitter across the       │  ← unchanged: PLM, Module Registry,
   │   library (unchanged)          │    ECF, Identity & Access, etc.
   └─────────────┬─────────────┘
                 │ (same Common Event Envelope, EOA §4, unchanged)
   ┌─────────────▼─────────────┐
   │   Ingestion Gateway (EOA,       │  ← unchanged component
   │   unchanged)                    │
   └──────┬──────────────┬──────┘
          │              │
          │ (voluntary)   │ (mandatory-class events, per the
          │               │  Mandatory Audit Event Catalog)
┌─────────▼──────┐  ┌──────▼──────────────────┐
│ EOA's general    │  │   Compliance Audit Log      │  ← new: append-only,
│ Log/Metrics/     │  │   (new)                      │    tamper-evident,
│ Trace Store       │  │                              │    retention-floor-
│ (unchanged)       │  │                              │    enforced
└─────────────────┘  └──────────────┬───────────────┘
                                    │
                      ┌─────────────▼─────────────┐
                      │   Compliance Query/Export      │  ← new: auditor/
                      │   Interface (new)               │    compliance-officer-
                      │                                  │    oriented queries
                      └───────────────────────────┘
```

## 4. Components

- **Mandatory Audit Event Catalog** *(new)* — a closed, named list of event categories designated as compliance-mandatory (initially: permission grant/revoke from Identity & Access; ownership transfer from the Module Registry; configuration changes from ECF; others may be added only via a governance decision, not ad hoc). Each entry references the source document's own existing event — it does not redefine what that event is.
- **Compliance Audit Log** *(new)* — a distinct, append-only, tamper-evident store (e.g., cryptographically chained or write-once) separate from EOA's general Log Store, receiving mandatory-class events routed by the (unchanged) Ingestion Gateway.
- **Retention Floor Enforcement** *(new)* — a governance rule, not a new mechanism: attempting to configure retention below the compliance-mandated minimum requires a specific, named permission checked via Identity & Access's `checkPermission()`, rather than being reachable through ordinary ECF configuration write access.
- **Compliance Query/Export Interface** *(new)* — a query surface oriented around compliance/audit use cases ("every action attributed to identity X," "every change to resource Y across its full retained history," bulk export for an external auditor) — distinct from EOA's Unified Query Interface, which is oriented around incident correlation and time-window investigation.

## 5. Interfaces

| Interface | Direction | Purpose |
|---|---|---|
| `designateMandatory(eventCategory, sourceDocumentRef)` | Governance decision → Mandatory Audit Event Catalog | Adds a new event category to the mandatory catalog; itself a deliberate, auditable governance action, not an incidental one. |
| `routeToComplianceLog(envelope)` | Ingestion Gateway (unchanged) → Compliance Audit Log | Internal routing: a mandatory-class event is written to the tamper-evident store in addition to, or instead of, EOA's general Log Store per its own retention policy. |
| `setRetention(eventCategory, period)` | Operator → Configuration Framework (unchanged), gated by Retention Floor Enforcement | Sets retention at or above the compliance floor; an attempt below the floor requires the specific named permission from §4. |
| `queryByIdentity(identityRef, timeRange)` / `queryByResource(resourceRef, timeRange)` | Compliance officer/auditor → Compliance Query/Export Interface | The primary compliance-response queries — "what did this identity do" / "what happened to this resource" — over the full retained history. |
| `exportForAudit(query, format)` | Compliance officer → Compliance Query/Export Interface | Produces an exportable record set for an external auditor, distinct from EOA's operational query output. |

## 6. Data Flow

1. An event occurs in any of the eighteen prior documents' own, unmodified emission logic (a permission grant in Identity & Access, an ownership transfer in the Module Registry, a configuration change in ECF).
2. The event is wrapped in EOA's unchanged Common Event Envelope and submitted to the unchanged Ingestion Gateway, exactly as any other emitted event in this library.
3. The Ingestion Gateway checks the event's category against the Mandatory Audit Event Catalog; if designated mandatory, the event is additionally routed to the Compliance Audit Log (alongside, not instead of, its optional routing to EOA's general Log Store, if that source has also adopted EOA voluntarily).
4. The Compliance Audit Log persists the record append-only and tamper-evident, subject to its enforced retention floor.
5. A compliance officer or auditor uses the Compliance Query/Export Interface — distinct from EOA's own Unified Query Interface — to answer "what did this identity do" or "what happened to this resource," and to produce an export for external audit purposes.
6. Any attempt to set retention below the compliance floor is checked via Identity & Access's `checkPermission()` for the specific named permission required; an unauthorized attempt is denied (fail-closed, per the Security Principles Catalog) and classified via EEHF with an `err.audit.*` code.

## 7. Design Patterns

- **Mandatory subset of a voluntary system, not a parallel system** — the Compliance Audit Log is fed by the exact same Ingestion Gateway and envelope EOA already defined; this document adds a designation and a second, stricter store, rather than building a second ingestion mechanism, directly continuing the reuse discipline established since EDM.
- **Governance-gated floor, not just a configuration default** — the retention floor is enforced through Identity & Access's authorization model specifically because a compliance guarantee that can be silently lowered via ordinary configuration access is not actually a guarantee; this is a deliberate escalation beyond ECF's normal per-layer write governance (ECF §8) for this one, compliance-critical parameter.
- **Distinct query surface for a distinct consumer** — EOA's Unified Query Interface is built for an operator investigating an incident; the Compliance Query/Export Interface is built for an auditor reconstructing history — different access patterns, different consumers, kept as separate interfaces over the same underlying tamper-evident data rather than forcing one interface to serve both audiences.

## 8. Security Considerations

*(Consistent with the Security Architecture's citation discipline.)*

- **Principle: Audit-Trail Integrity** (ESA catalog) is this document's central concern — the Compliance Audit Log's append-only, tamper-evident construction is the direct implementation of that principle for the specific event categories designated mandatory.
- **Principle: Least-Privilege** (ESA catalog) applies to the Retention Floor Enforcement permission — it should be granted to as narrow a set of identities as operationally possible, given its direct compliance implications.
- **Principle: Fail-Closed Validation** (ESA catalog) applies to any retention-floor-lowering attempt without the required permission — denied by default, not permitted pending review.
- **The Compliance Audit Log itself is a high-value target** — because it is the authoritative record for compliance response, write access (beyond the automated Ingestion Gateway routing) should not exist at all under normal operation; there is no legitimate direct-write path for a human or provider.

## 9. Scalability

- **Mandatory-class event volume is a small, curated subset of total library event volume** — because the Mandatory Audit Event Catalog is deliberately closed and named (§4), the Compliance Audit Log's write volume is bounded and predictable, unlike EOA's general Log Store, which scales with however many emitters voluntarily adopt it.
- **Retention-driven storage growth is a known, planned cost** — because retention has an enforced floor rather than an arbitrary per-source default, storage growth for the Compliance Audit Log is a predictable function of mandatory-event rate and the floor period, not a variable one.
- **Compliance queries are infrequent but must not be latency-sensitive in the way EOA's operational queries are** — an auditor's "every action by this identity over three years" query can tolerate materially higher latency than an operator's incident-investigation query, simplifying the Compliance Query/Export Interface's performance requirements relative to EOA's Unified Query Interface.

## 10. Best Practices

- Keep the Mandatory Audit Event Catalog closed and change it only through a deliberate governance decision (`designateMandatory()`), never by informal convention.
- Never provide a direct human or provider write path into the Compliance Audit Log — it must only ever be populated through the unchanged Ingestion Gateway's automated routing.
- Grant the retention-floor-lowering permission as narrowly as possible, and audit its use with the same rigor as the records it protects.
- Keep the Compliance Query/Export Interface's access scoped to compliance/audit roles specifically, distinct from EOA's broader operational query access.

## 11. Common Pitfalls

- **Building a second event-ingestion mechanism instead of routing through EOA's existing Ingestion Gateway** — repeats the exact duplication this library has consistently avoided since EDM; mandatory-class events must flow through the same pipe as everything else, only routed differently.
- **Treating the compliance retention floor as an ordinary configuration default** — if it can be lowered through normal ECF write access rather than a specifically-gated permission, it is not actually a floor, undermining the entire purpose of this document.
- **Letting the Mandatory Audit Event Catalog grow informally** — an uncurated, ever-expanding "mandatory" list defeats its own purpose by becoming indistinguishable from EOA's general voluntary adoption.
- **Serving compliance queries from EOA's operational Unified Query Interface instead of a distinct Compliance Query/Export Interface** — conflates two different consumers' needs and risks either under-serving auditors or over-exposing operational tooling to compliance-sensitive access patterns.

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **Rely entirely on EOA's voluntary adoption for compliance-relevant events** | Treat permission changes, ownership transfers, and configuration changes as just another optional EOA source. | Fails the compliance goal outright — a voluntary, un-retained, non-tamper-evident record is not an adequate basis for audit/compliance response; the exact gap this document exists to close. |
| **Build a second, dedicated ingestion mechanism for compliance events** | A parallel pipeline separate from EOA's Ingestion Gateway. | Directly repeats the duplication problem this library has avoided since EDM; EOA's envelope and gateway already work and require no redesign to support a second downstream store. |
| **Enforce retention floor via ordinary ECF configuration governance only** | Rely on ECF's existing per-layer write governance (ECF §8) rather than a specifically-gated Identity & Access permission. | ECF's per-layer governance is designed for routine configuration, not a compliance-critical, hard-to-reverse guarantee; a specifically-named, narrowly-granted permission provides a meaningfully stronger guarantee against silent weakening. |
| **Serve compliance queries from EOA's Unified Query Interface** | Avoid building a second query interface. | Conflates two different consumer needs (operational incident investigation vs. compliance/audit response) with different access-scoping and query-shape requirements, the same distinction-preservation discipline used throughout this library (e.g., EEHF vs. PLM's health mechanism, EEB vs. EOA). |

## 13. Migration Strategy

1. **Publish the initial Mandatory Audit Event Catalog** with the three events already named in this document (permission grant/revoke, ownership transfer, configuration change), each referencing its existing, unmodified source event.
2. **Stand up the Compliance Audit Log and wire the existing, unchanged Ingestion Gateway to route mandatory-class events into it** — no change to any of the eighteen prior documents' own emission logic.
3. **Establish the retention floor and gate its lowering via a specific Identity & Access permission** before any mandatory-class event flows into production.
4. **Build the Compliance Query/Export Interface and validate it against at least one realistic compliance scenario** (e.g., "reconstruct every permission change for identity X over the past year") before general availability.
5. **Add further event categories to the Mandatory Audit Event Catalog only through a deliberate governance decision**, never informally.

## 14. Success Criteria

- 100% of events in the Mandatory Audit Event Catalog are captured in the Compliance Audit Log, append-only and tamper-evident.
- Zero instances of retention being lowered below the compliance floor without the specifically-gated permission.
- A compliance query ("every action by identity X," "every change to resource Y") is answerable end-to-end via the Compliance Query/Export Interface, distinct from and without relying on EOA's operational interface.
- Zero direct write paths into the Compliance Audit Log other than the unchanged Ingestion Gateway's automated routing.
- Zero new event-ingestion mechanisms introduced — confirmed reuse of EOA's existing Common Event Envelope and Ingestion Gateway.

## 15. Decision Matrix

| Criterion (weight) | Mandatory catalog + tamper-evident store + gated retention floor, reusing EOA's ingestion (recommended) | Rely entirely on EOA's voluntary model | Second, dedicated ingestion mechanism | Retention floor via ordinary ECF governance only | Serve compliance queries from EOA's interface |
|---|---|---|---|---|---|
| Compliance-adequate guarantee (mandatory, tamper-evident, retained) (High) | 5 | 1 | 4 | 3 | 4 |
| Reuse of existing ingestion mechanism (High) | 5 | 5 | 1 | 5 | 5 |
| Retention floor cannot be silently weakened (High) | 5 | 1 | 4 | 2 | 4 |
| Distinct, appropriately-scoped compliance query access (Medium) | 5 | 2 | 4 | 4 | 1 |
| Implementation/governance overhead (Medium, lower = better fit) | 3 | 5 | 2 | 4 | 4 |
| **Weighted outcome** | **Best overall fit** | Fails compliance goal | Fails reuse principle | Weaker retention guarantee | Fails query-separation goal |

**Conclusion**: a closed Mandatory Audit Event Catalog feeding a tamper-evident Compliance Audit Log — reusing EOA's existing ingestion mechanism and gating the retention floor through Identity & Access — is recommended. It is the only option delivering a genuine compliance guarantee without duplicating ingestion infrastructure.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-019: Enterprise Audit Framework as a Mandatory, Tamper-Evident Subset Layered on Observability's Existing Ingestion**

- **Status**: Accepted
- **Context**: EOA's voluntary, general-purpose observability model is correct for operational telemetry but inadequate for compliance-relevant events already named across the library (Identity & Access's permission changes, the Module Registry's ownership transfers, ECF's configuration changes), which require mandatory capture, tamper-evidence, and a retention floor that cannot be silently weakened.
- **Decision**: Designate a closed Mandatory Audit Event Catalog, feed it through EOA's existing, unchanged Ingestion Gateway into a new, distinct Compliance Audit Log (append-only, tamper-evident), enforce a retention floor gated by a specific Identity & Access permission, and provide a distinct Compliance Query/Export Interface separate from EOA's operational one. **No modification to any of the eighteen prior documents**, including EOA's own voluntary-adoption model, which remains fully in effect for everything not designated mandatory.
- **Rationale**: The Decision Matrix (§15) shows this is the only option providing a genuine compliance guarantee (mandatory, tamper-evident, retention-floor-protected) while fully reusing EOA's existing ingestion mechanism rather than duplicating it, and while keeping compliance query access appropriately separated from operational query access.
- **Consequences**:
  - *Positive*: compliance-relevant history now has a genuine guarantee instead of depending on voluntary adoption; the retention floor is protected by a specific permission rather than ordinary configuration access; auditors get a query interface shaped for their actual use case.
  - *Negative*: introduces a fourth new component (Catalog, Compliance Audit Log, Retention Floor Enforcement, Compliance Query/Export Interface) that must be operated with particular care given its compliance role.
  - *Neutral*: EOA's general Log Store continues operating exactly as before for anything not designated mandatory — this document changes nothing about that voluntary model.
- **Alternatives rejected**: rely entirely on EOA's voluntary model, a second ingestion mechanism, retention floor via ordinary ECF governance, serving compliance queries from EOA's interface — see §12 and §15.
- **Reversibility**: Moderate reversal cost — the Compliance Audit Log and its retained history would need a defined disposition policy if this document were ever superseded, since compliance records generally cannot simply be discarded; less reversible than EDM's low-cost case, comparable to reversing PLM or ESR adoption.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Mandatory Audit Event Catalog, Compliance Audit Log, Retention Floor Enforcement, and Compliance Query/Export Interface are specified at architecture level. |
| **Reuse of EOA's ingestion mechanism** | Confirmed | No second event-ingestion pipeline; routes through the unchanged Ingestion Gateway. |
| **Retention floor protection** | Confirmed by design | Gated via a specific Identity & Access permission, not ordinary ECF configuration access. |
| **Distinct query interface from EOA** | Confirmed | Compliance Query/Export Interface is explicitly separate from EOA's Unified Query Interface. |
| **Technology-agnostic validation** | Ready | No binding to a specific tamper-evident storage technology (e.g., a specific WORM or hash-chaining implementation). |
| **Threat-model application** | Recommended as a priority candidate | Alongside Identity & Access, a natural early candidate for ESA's Threat Modeling Methodology given its compliance role. |
| **Specific compliance regime mapping** | Not performed | This document provides the mechanism; mapping it to any specific external regulatory requirement (e.g., a named compliance framework) is separately-scoped future work. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Mapping to specific external compliance regimes** — a future, separately-scoped exercise to confirm this mechanism satisfies a named regulatory framework's specific requirements, rather than a general compliance-adequacy claim.
- **Legal-hold override of retention** — extending the Retention Floor Enforcement model to support an explicit, permissioned legal-hold state that suspends normal retention expiry for specific records.
- **Cryptographic external anchoring** — periodically anchoring the Compliance Audit Log's tamper-evidence chain to an external, independently-verifiable record, strengthening the tamper-evidence guarantee beyond internal construction alone.
- **Expanding the Mandatory Audit Event Catalog** — as future documents introduce new compliance-relevant events, each addition should go through the same deliberate `designateMandatory()` governance decision rather than informal expansion.

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-019.
