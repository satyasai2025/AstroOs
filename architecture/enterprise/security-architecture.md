---
title: Enterprise Security Architecture
status: FROZEN
version: 1.0
owner: Chief Solutions Architect
category: enterprise
---

# Enterprise Security Architecture

## 1. Problem Statement

**Audit finding across all sixteen prior documents:** every one of them has its own §8 Security Considerations section, and every one of them independently restates a handful of the same underlying principles — least privilege, secrets-by-reference, fail-closed validation, audit-trail integrity, data minimization — in slightly different words, scoped to that document's own components. And every single one of their §17 Readiness Assessments contains some variant of "no formal threat model performed." Sixteen documents, sixteen ad hoc restatements of the same principles, and zero instances of an actual, structured threat-modeling exercise having been run against any of them.

This is the same category of gap the Version Compatibility Strategy (EVCS, ADR-EAL-008) closed for versioning semantics: not a duplicated *component*, but a duplicated, unwritten-down-in-one-place *policy*. The Enterprise Security Architecture (ESA) is this document's analog to EVCS — a **written reference**, consolidating the security principles already scattered across sixteen documents' §8 sections into one catalog, and establishing a single, reusable threat-modeling methodology that can (as future, separately-scoped work) be applied to any of them.

**What this document explicitly is not:**

- It does not define authentication or authorization mechanisms (who a caller is, how they prove it, what roles/permissions mean) — that is the next roadmap item, **Identity & Access**, and this document defers to it entirely rather than partially overlapping.
- It does not run the sixteen (or any) outstanding threat-model exercises itself — it establishes the methodology; execution against any specific document is separately-scoped future work (§18).
- It does not modify any of the sixteen prior documents' own §8 content — each remains valid and in effect exactly as frozen; this document is a cross-reference catalog, not a replacement.

### What this document consolidates (not reuses — restates once, precisely)

| Principle, as it already appears (scattered) | Where it currently lives |
|---|---|
| Least-privilege capability/access grants | PLM §8 (capability declarations), Module Registry §8 |
| Secrets never inline, only by reference/handle | PLM §8, Module Registry §8, ECF §4/§8, EEHF §8, EFF §8, EWE §8, EEB §8, ENF §8, Scheduling §8 |
| Fail-closed / deny-by-default on ambiguous validation | PLM §7 (Compatibility Checker), Module Registry §7 |
| Data minimization / no sensitive detail in shared metadata | EEHF §8 (error messages), EOA §8, ENF §8 (recipient data) |
| Audit-trail integrity (append-only, tamper-evident) | ECF §8 (Change Audit Log), Module Registry §8 (ownership transfer) |
| Strictest-applicable-source-policy for aggregated/derived data | EOA §8, ESR §8 (network address exposure), Scheduling §8 |
| Privilege parity — a decoupled/derived mechanism grants no more access than a direct caller would have | EWE §8 (workflow steps), Scheduling §8 (schedule targets), EDM §8 |

**Scope boundary:** this document does not modify any of the sixteen prior documents. It restates their already-established principles once, precisely, as a referenceable catalog, and adds the one genuinely new artifact none of them individually needed: a reusable threat-modeling methodology.

## 2. Goals

| Goal | Description |
|---|---|
| **One Security Principles Catalog** | The principles in §1's table are stated once, precisely, with a stable name each, so future documents can cite "Principle: Secrets-by-Reference" instead of re-deriving it. |
| **A reusable threat-modeling methodology** | A structured method (asset/threat/control categories mapped to this library's own component types — registries, engines, gateways, brokers, stores) that can be applied consistently to any current or future document. |
| **A defense-in-depth layering model** | An explicit map of which architectural layer each existing security control operates at, showing how they compose rather than leaving that composition implicit. |
| **Explicit deferral to Identity & Access** | Authentication/authorization mechanism design is named as out of scope here and owned by the next roadmap item, with no partial overlap. |
| **Non-disruption of the sixteen prior documents** | Adoption requires no change to any of their §8 sections; this is a reference, not a mandate to rewrite. |

**Non-goals**: ESA does not define authentication/authorization (Identity & Access's role); it does not perform any specific threat-model exercise itself (future, separately-scoped work); it does not introduce a new runtime security-enforcement component (no new gateway, no new access-control engine — this is a policy/reference document, following EVCS's precedent, not a component like PLM's Security Gate or the AI Platform's Guardrail Layer).

## 3. Architecture

Like EVCS, ESA is a **policy/reference specification**, not a runtime component:

```
   ┌───────────────────────────────────────────────────────────┐
   │        Enterprise Security Architecture                      │
   │        (reference catalog — no runtime component of its own) │
   │                                                                │
   │   ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
   │   │ Security           │  │ Threat Modeling     │  │ Defense-in-   │ │
   │   │ Principles Catalog  │  │ Methodology         │  │ Depth Layering │ │
   │   │ (§1 table,          │  │ (asset/threat/       │  │ Model          │ │
   │   │  consolidated)      │  │  control categories) │  │                │ │
   │   └─────────────────┘  └─────────────────┘  └──────────────┘ │
   └──────────────────────────────┬────────────────────────────────┘
                                  │ referenced/cited voluntarily —
                                  │ not enforced retroactively on
                                  │ already-frozen §8 sections
          ┌───────────────────────┼───────────────────────┐
          │                       │                        │
┌─────────▼────────┐   ┌──────────▼─────────┐   ┌──────────▼─────────┐
│ Sixteen prior       │   │ Identity & Access     │   │ Future documents'    │
│ documents' existing  │   │ (next roadmap item —  │   │ own §8 sections       │
│ §8 sections           │   │ authN/authZ mechanism, │   │ (may cite this        │
│ (unchanged)           │   │ not overlapping here)  │   │  catalog directly)    │
└───────────────────┘   └───────────────────┘   └───────────────────┘
```

## 4. Components

Because ESA is a reference specification, its "components" are catalog artifacts, not services:

- **Security Principles Catalog** — the table in §1, restated as a stable, named reference (e.g., "Principle: Secrets-by-Reference," "Principle: Fail-Closed Validation") that any document — past (by citation, not rewrite) or future (by direct application) — can point to.
- **Threat Modeling Methodology** — a structured method for identifying assets, threats, and controls, organized around the *component archetypes* already established in this library (registry, engine/broker, gateway/adapter, durable store, policy specification), so applying it to any current or future document follows the same repeatable shape.
- **Defense-in-Depth Layering Model** — an explicit map (§7) of which layer each existing control operates at (declaration-time validation, runtime enforcement, audit/detection, recovery), making the composition of controls across this library's sixteen documents visible as a system, not sixteen disconnected lists.

## 5. Interfaces

ESA's "interfaces" are citation points, consistent with its nature as a policy specification (mirroring EVCS §5):

| Conformance Point | Consumer | Purpose |
|---|---|---|
| Security Principles Catalog entries | Any future document's §8 | Cite a named principle instead of re-deriving it from first principles. |
| Threat Modeling Methodology | Any team running a threat-model exercise against a current or future document | A shared, repeatable structure — not a mandate on when to run one. |
| Defense-in-Depth Layering Model | Design reviewers | A reference for evaluating whether a new document's security section addresses the layer(s) it actually operates at. |

## 6. Data Flow

As a reference specification, ESA's "data flow" describes how the catalog is authored and consulted, not a request-time sequence:

1. This document establishes the Security Principles Catalog, Threat Modeling Methodology, and Defense-in-Depth Layering Model as the canonical reference.
2. Any future Enterprise Architecture Library document's §8 Security Considerations may cite a named principle from the catalog directly, rather than restating it — reducing the sixteen-times-restated pattern identified in §1 going forward.
3. Where a threat-model exercise is separately chartered (future work, §18) against any current or future document, it applies the Threat Modeling Methodology's structure.
4. No data flows *from* ESA into any of the sixteen prior documents under this decision — citation is voluntary and forward-looking, exactly as EVCS's conformance model was voluntary for PLM and EDM (EVCS §16).

## 7. Design Patterns

- **Policy-as-specification, not policy-as-code** — directly follows EVCS's precedent (EVCS §7): establish the human-readable, referenceable catalog first; automated enforcement, if ever pursued, is future evolution (§18), not attempted here.
- **Defense-in-depth, made explicit rather than implicit** — the Layering Model doesn't add new controls; it makes visible that this library already has controls at multiple layers (PLM's declaration-time capability grants, ECF's secrets-by-reference, EEHF's fail-closed classification, EOA's audit trail) that compose into a defense-in-depth posture no single document was positioned to describe.
- **Consolidation without redesign** — mirrors EDM's and EVCS's shared discipline: a cross-cutting gap is closed by a new, additive reference/capability, never by reopening an already-frozen document.

## 8. Security Considerations

(This section, unusually for this library, is about the document's own handling of security content rather than a system's.) The catalog itself must not become a single point of stale information: if a future document supersedes a cited principle (e.g., a future ADR revises the secrets-by-reference model), this catalog must be updated to reflect that, or citations elsewhere would silently reference an outdated statement. This document's own Readiness Assessment (§17) flags this as an ongoing maintenance responsibility, not a one-time artifact.

## 9. Scalability

Not applicable in the runtime sense — as a reference specification, ESA has no request path, no throughput, and no capacity planning concern. Its only "scaling" dimension is organizational: the catalog must remain a small, curated set of named principles rather than growing into an unmanageably long, uncurated list, or it stops being faster to cite than to restate.

## 10. Best Practices

- Cite a named principle from the catalog in any future document's §8 rather than restating it in different words — this is the entire practical value of consolidation.
- Treat "no formal threat model performed" (as flagged in every one of the sixteen prior documents' Readiness Assessments) as a tracked, visible backlog item once the methodology exists, rather than a permanently accepted gap.
- Keep this document's own catalog current if any cited principle is later revised by a superseding ADR elsewhere in the library.

## 11. Common Pitfalls

- **Treating this document as retroactively rewriting any of the sixteen prior §8 sections** — the single most important pitfall to avoid, mirroring the equivalent caution already established for EDM (§11) and EVCS (§11); this is a citation catalog, not a silent redefinition.
- **Conflating this document's scope with Identity & Access** — this document deliberately does not define authentication/authorization; a reader looking for "how do we verify who's calling" should look to the next roadmap item, not here.
- **Letting the catalog grow unmanageably** — see §9; a catalog with fifty entries is no faster to consult than restating each principle individually, defeating its own purpose.
- **Assuming the Threat Modeling Methodology's existence means threat models have been run** — the methodology is necessary but not sufficient; actually applying it to each of the sixteen (or any future) documents remains separately-scoped, unstarted work (§18).

## 12. Alternatives Considered

| Alternative | Description | Why not chosen as primary model |
|---|---|---|
| **Leave security principles scattered across each document's own §8** | Accept the sixteen-times-restated pattern as-is. | Fails "reuse before creating" in the same way EVCS's unwritten versioning policy did; makes it harder to verify consistency across documents and to onboard reviewers to a single reference. |
| **Immediately retrofit all sixteen prior documents to cite the new catalog** | Edit every existing §8 section to reference ESA instead of its own prose. | Violates "no redesign of approved modules" without a separate approval per document; this document instead makes citation available prospectively, consistent with the EDM/EVCS precedent. |
| **Build ESA as a runtime policy-enforcement/threat-detection system immediately** | Skip the written catalog and build automated security scanning/enforcement. | Premature in the same way policy-as-code was judged premature for EVCS (EVCS §12); a validated, human-reviewed catalog should precede automation, and is noted as future evolution (§18) rather than in scope now. |
| **Fold Identity & Access design into this document** | Define authentication/authorization here rather than as a separate roadmap item. | The roadmap already sequences Identity & Access as its own item; conflating the two would produce an oversized document mixing a reference catalog with a concrete mechanism design, and would preempt the roadmap's own sequencing without approval to reorder it. |

## 13. Migration Strategy

1. **Publish the Security Principles Catalog, Threat Modeling Methodology, and Defense-in-Depth Layering Model** as this document's frozen artifacts — no change required to any of the sixteen prior documents to adopt step 1.
2. **Cite catalog entries in every future document's §8** from this point forward, per the discovery-search discipline already established elsewhere in this library (Module Registry §10, EDM §11).
3. **Track "threat model not yet performed" as a visible backlog** across the sixteen existing documents, without committing to when (or whether) each will be exercised — that remains separately-scoped future work.
4. **Apply the Defense-in-Depth Layering Model during future design reviews** to check whether a new document's security section addresses the layer(s) relevant to its own components.

## 14. Success Criteria

- Every catalog entry has a stable name and precise statement, citable without ambiguity.
- At least one future Enterprise Architecture Library document's §8 cites a named catalog principle instead of restating it from scratch.
- Zero modifications made to any of the sixteen prior documents' own content as a side effect of this document's publication.
- The Defense-in-Depth Layering Model correctly maps at least one existing control from each of the sixteen prior documents to a layer, demonstrating the model's completeness against the library as it currently stands.
- No overlap identified between this document's content and the (separately drafted) Identity & Access document once both exist.

## 15. Decision Matrix

| Criterion (weight) | Written catalog + methodology, no runtime component (recommended) | Leave scattered across each document | Immediately retrofit all sixteen documents | Build automated enforcement/detection now | Fold Identity & Access in here |
|---|---|---|---|---|---|
| Closes the scattered-principle finding (High) | 5 | 1 | 5 | 5 | 4 |
| Respects "no redesign of approved modules" (High) | 5 | 5 | 1 | 3 | 4 |
| Clean boundary from Identity & Access (High) | 5 | 4 | 4 | 3 | 1 |
| Provides a reusable threat-model structure (Medium) | 5 | 1 | 3 | 4 | 3 |
| Maturity/validation before automation (Medium) | 5 | 3 | 3 | 1 | 3 |
| Implementation/governance overhead (Medium, lower = better fit) | 4 | 5 | 2 | 1 | 3 |
| **Weighted outcome** | **Best overall fit** | Fails consolidation goal | Fails charter boundary | Premature automation | Fails roadmap-sequencing/scope boundary |

**Conclusion**: a written Security Principles Catalog, Threat Modeling Methodology, and Defense-in-Depth Layering Model — with no runtime component and no retroactive rewriting of the sixteen prior documents — is recommended, directly following the precedent already validated by EVCS.

## 16. Architecture Decision Record (ADR)

**ADR-EAL-017: Enterprise Security Architecture as a Consolidated Reference Catalog, Not a Runtime Component**

- **Status**: Accepted
- **Context**: Audit of the library (§1) found the same security principles independently restated across all sixteen prior documents' §8 sections, and a universal, unaddressed "no formal threat model performed" gap in every one of their Readiness Assessments.
- **Decision**: Publish a Security Principles Catalog, Threat Modeling Methodology, and Defense-in-Depth Layering Model as a referenceable specification. **This decision does not modify any of the sixteen prior documents.** Authentication/authorization mechanism design is explicitly deferred to the next roadmap item, Identity & Access, with no overlap. Actually running a threat-model exercise against any specific document remains separately-scoped future work.
- **Rationale**: The Decision Matrix (§15) shows this is the only option that closes the consolidation gap while respecting the "no redesign of approved modules" boundary and the roadmap's own sequencing of Identity & Access as a distinct, subsequent item.
- **Consequences**:
  - *Positive*: future documents can cite one precise, named principle instead of restating it; a repeatable threat-modeling structure now exists, ready for future application; the composition of existing controls across sixteen documents is now visible as a defense-in-depth system rather than sixteen disconnected lists.
  - *Negative*: the sixteen existing documents' §8 sections remain, by design, unchanged and thus not yet citing the new catalog — full consistency is prospective, not immediate.
  - *Neutral*: no threat-model exercise is actually performed by this document; the gap it responds to (§1) remains open until separately chartered work executes the methodology.
- **Alternatives rejected**: leave scattered, immediately retrofit all sixteen, build automated enforcement now, fold Identity & Access in here — see §12 and §15.
- **Reversibility**: Fully reversible — as a pure reference specification with no runtime dependency from any existing document, this catalog can be revised or withdrawn without impact to any of the sixteen prior documents.

## 17. Readiness Assessment

| Dimension | Assessment | Notes |
|---|---|---|
| **Conceptual completeness** | Ready for review | Principles Catalog, Threat Modeling Methodology, and Layering Model are specified. |
| **Respect for "no redesign of approved modules"** | Confirmed by design | No change to any of the sixteen prior documents; citation is prospective and voluntary, mirroring EVCS's precedent. |
| **Boundary with Identity & Access** | Confirmed explicit | §1 and §12 explicitly name authentication/authorization as out of scope, owned entirely by the next roadmap item. |
| **Catalog completeness against current library** | Confirmed for the seven principles identified in §1's table | Should be revisited if a future document surfaces a genuinely new cross-cutting principle not yet catalogued. |
| **Threat-model methodology validation** | Not yet exercised | The methodology is specified but has not been run against any document; first application is recommended as near-term future work (§18), not assumed complete here. |
| **Overall readiness for Implementation phase** | **Architecture-complete; not implementation-ready** | Per operating policy, this document is a frozen architecture artifact only. Implementation planning is explicitly out of scope until separately chartered. |

## 18. Future Evolution

- **Run the Threat Modeling Methodology against each of the sixteen prior documents**, prioritized by which handle the most sensitive data or highest-privilege operations (a natural first candidate: PLM's capability-grant model, given its direct privilege implications).
- **Policy-as-code enforcement of catalog principles** — e.g., automated checks that a new document's manifest/schema doesn't inline a secret, once the written catalog has been validated in practice, echoing the policy-as-code future evolution already flagged for the Module Registry (§18), ECF (§18), and EVCS (§18).
- **Joint review with Identity & Access once drafted** — confirming no boundary drift has occurred between the two documents as Identity & Access's own design solidifies.
- **Formal supply-chain/artifact-integrity consolidation** — PLM already covers plugin signing/checksums (PLM §8); a future extension could generalize this into the catalog as its own named principle if additional documents introduce comparable integrity-verification needs.

---

**Document status**: FROZEN as of this revision. No further changes without a new ADR superseding ADR-EAL-017.
