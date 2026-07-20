# AstroOS Phase III / v2.3.0 Roadmap

**Version:** v2.3.0 — Phase III  
**Codename:** "Lakshmi" (Expansion & Integration)  
**Date:** 2026-07-20 (revised per local-first audit)  
**Status:** PLANNING — scope amended  
**Predecessor:** v2.2.0 Phase II ("Arundhati") complete  
**Audit:** `PHASE_III_LOCAL_FIRST_AUDIT.md` — 2026-07-20

---

## Theme

**From Desktop to Multi-Device Personal Research Platform.** Phase III extends AstroOS beyond the browser into mobile apps, a local plugin architecture, advanced analytics, and internationalization — all while keeping the single-user local-first mandate. Real-time collaboration and hosted plugin marketplace are deferred; in their place, a local plugin directory and CLI toolchain give the researcher extensibility without cloud dependency.

---

## Operating Model (unchanged per ADR-EAL)

| Office | Owns | Does NOT own |
|--------|------|--------------|
| **Engineering (CEO-ENG)** | Backend, frontend, mobile apps, SDKs, API, DB, CI/CD, testing, performance, security, DevOps | Architecture decisions, astrology knowledge, benchmarks, research datasets |
| **Architecture (CAO)** | System architecture, ADRs, RFCs, module boundaries, dependency rules, plugin API design | Implementation |
| **Knowledge (CKO)** | Ontology, classical texts, catalogues, glossary, cross-references, conflicts, Knowledge Graph | Calculations |
| **Benchmark (CBO)** | Benchmark specs, gold-standard datasets, accuracy metrics, validation methodology | Algorithm implementation |
| **Research Data (CRDO)** | Research datasets, metadata, data standards, import pipelines, dataset quality/versioning | Benchmark rules, software implementation |

---

## Scope Amendment (2026-07-20)

Per the Phase III local-first audit (`PHASE_III_LOCAL_FIRST_AUDIT.md`):

| Original Item | Verdict | Replacement |
|---------------|---------|-------------|
| Plugin Marketplace (hosted registry, Stripe, dev portal) | ❌ FAIL — cloud infrastructure | Local plugin directory (`.plugin.json` manifests, `astroos plugin install <path>`, CLI from static files) |
| Real-Time Collaboration (OT/CRDT, chat, @mentions) | ❌ FAIL — inherently multi-user | **Deferred to Phase IV** |
| OAuth 2.0 flow | 🔄 Over-engineered for single-user | API keys as default; OAuth optional add-on |
| GDPR Compliance (consent management) | 🔄 Irrelevant for single-user | Re-scoped to "Research Data Privacy Tools" |
| Mobile push notifications (FCM/APNs) | 🔄 Conditional | Feature-flagged, optional; app works fully offline |
| Mobile sync target | 🔄 Conditional | Defaults to `localhost:8000`; user-configurable |
| Advanced Analytics | ✅ PASS — pure local computation | Proceed as-is |
| i18n & Localization | ✅ PASS — static content | Proceed as-is |

---

## Phase Breakdown

### Phase III.1 — Mobile Apps (React Native) (4-5 weeks)

**Goal:** Native iOS + Android apps with full offline-first capability. Users can cast charts, read reports, run research queries on mobile without internet connectivity.

**Engineering (CEO-ENG):**
- React Native app architecture (TypeScript, Expo or bare RN)
- Core features: birth chart generation, D1/D9 display, Dasha timeline, yoga detection, basic reports
- Offline-first SQLite sync with local PostgreSQL (bidirectional, defaults to `localhost:8000`)
- Push notification support **behind optional feature flag** (FCM/APNs — not required for core function)
- In-app purchase integration (optional monetization; no runtime dependency)
- iOS App Store + Google Play submission process

**Architecture (CAO):**
- ADR: Mobile sync protocol (last-write-wins vs manual merge — OT/CRDT explicitly deferred)
- ADR: Offline cache eviction strategy
- ADR: Push notification provider choice (FCM, APNs) — note: optional-only
- Design: Plugin swizzling for mobile (extend without modifying core)

**Quality (QA):**
- Mobile device lab (iOS + Android physical devices, various versions)
- **Primary path: app works fully offline** — zero connectivity test
- Offline/online transition testing with localhost sync target
- Push notification delivery tested only when feature flag enabled

---

### Phase III.2 — Plugin Architecture & Local Registry (3-4 weeks)

**Goal:** Extensible plugin system with sandboxed execution, CLI toolchain, and a local plugin directory — no hosted marketplace required.

**Engineering (CEO-ENG):**
- Plugin sandbox architecture (isolated CPU/memory/network limits per process)
- Plugin API surface: chart data, yoga detection, knowledge queries, report generation
- **Local plugin directory** — bundled `plugins/registry.json` manifest. Users discover plugins via CLI:
  - `astroos plugin list` — list available plugins from manifest
  - `astroos plugin install <name>` — download/clone from bundled URL
  - `astroos plugin uninstall <name>`, `astroos plugin enable/disable`
- CLI for plugin development: `astroos plugin scaffold`, `astroos plugin validate`, `astroos plugin package`
- No hosted marketplace, no Stripe payments, no developer portal (developer docs shipped with app)

**Architecture (CAO):**
- ADR: Plugin security model (sandbox CPU/memory limits, network access, data isolation)
- ADR: Plugin signing and verification
- Design: Hit-and-run plugin API (plugins call core engines; core calls plugins)

**Knowledge (CKO):**
- Plugin taxonomy: which astrology categories do plugins cover? (yoga detection, report themes, data import)
- Plugin markup/review for accuracy

---

### Phase III.3 — *(vacant — Real-Time Collaboration Deferred to Phase IV)*

Real-Time Collaboration is **deferred** per `PHASE_III_LOCAL_FIRST_AUDIT.md` recommendation. OT/CRDT sync, chat, @mentions, and presence indicators are inherently multi-user features with no application in the single-user local-first platform. Revisit in Phase IV if multi-tenant scope is approved.

---

### Phase III.4 — Advanced Analytics & Benchmarking Tools (3-4 weeks)

**Goal:** Power-user analytics suite. Cohort analysis, correlation studies, statistical significance testing, custom query builder, visualizable data exports — all running on local data.

**Engineering (CEO-ENG):**
- Query builder UI (drag-and-drop variables, filters, aggregations)
- Statistical analysis engine (Pearson correlation, chi-squared, t-tests, Bayes factors)
- Cohort segmentation (group births by criteria, compare outcomes)
- Visualization library (interactive scatter plots, heatmaps, time series)
- Report automation (scheduled output to local filesystem)

**Benchmark (CBO):**
- Validate statistical methods against known datasets
- Guard against p-hacking, multiple comparison problems

**Knowledge (CKO):**
- Document statistical methods in astrological context
- Guidance: spurious correlation warnings

**Research Data (CRDO):**
- Curate open research datasets for statistical testing
- Anonymization best practices for research publishing

---

### Phase III.5 — Internationalization & Localization (2-3 weeks)

**Goal:** Global readiness. UI translations, cultural adaptations, locale-specific defaults.

**Engineering (CEO-ENG):**
- i18n infrastructure: message extraction, translation memory (local file-based)
- RTL support (Arabic, Hebrew)
- Locale-specific defaults (date formats, house systems, ayanamsa preferences)

**Knowledge (CKO):**
- Cultural adaptation guidelines
- Terminology normalization across Jyotish schools
- Glossary translations: English → Spanish, Hindi, French, German, Arabic

**Quality (QA):**
- Native speaker reviews of translations
- Functional testing with RTL locales

---

### Phase III.6 — Developer API Exposure (2 weeks)

**Goal:** Developers can build on AstroOS via a documented REST API, SDKs, API key authentication (OAuth optional), and webhooks.

**Engineering (CEO-ENG):**
- Public API documentation (OpenAPI 3.0 spec, ReDoc/ Swagger UI shipped locally)
- **API key authentication as default** — simple key-based auth for single-user/local development
- **OAuth 2.0 as optional** — feature-flagged for users who expose their instance publicly
- API key management panel (web UI)
- Rate limiting (generous local-first defaults; opt-in tightening)
- Webhook system (on event X, POST to URL Y; documented for local testing via ngrok/tunnel)
- Developer playground (local Swagger UI — no hosted service)

**Architecture (CAO):**
- ADR: API authentication model (API keys primary, OAuth 2.0 optional add-on)
- ADR: Rate limiting algorithm (token bucket, sliding window — disabled by default)
- ADR: Backward compatibility policy (deprecation timeline)

---

## Success Criteria (M3 Definition — Amended 2026-07-20)

1. **Mobile apps published** — iOS + Android apps downloadable, generate chart fully offline
2. **Plugin API stable** — 2+ sample plugins installable via CLI, sandbox execution verified
3. **Advanced analytics core** — correlated birth-death sample dataset with significance p<0.05
4. **i18n coverage** — 5 languages localized (ES, HI, FR, DE, AR), RTL layout correct
5. **API key system operational** — key management UI works, webhooks testable with local tunnel, developer docs complete

*(Original criteria for marketplace downloads, 10+ concurrent collaborators, OAuth, and 10+ external developers removed per local-first mandate.)*

---

## Out of Scope (Local-First Mandate)

Per `CLAUDE_START_HERE.md` and Phase III audit:
- Hosted plugin marketplace / Stripe payments / developer portal
- Real-time collaboration (OT/CRDT, chat, @mentions) — deferred to Phase IV
- OAuth 2.0 as default authentication — API keys are the default; OAuth optional
- Multi-tenancy / SaaS hosting
- Blockchain/crypto integrations
- VR/AR visualization
- Any feature that requires a cloud service to function

---

## Dependency Graph

```
1 (AMP Gov) → 6 (iOS) → 7 (Android) → 8 (Store) → 9 (Plugin Design) → 10 (Local Registry) → 11 (Plugin CLI)
               ↘ 19 (QA Mobile)        ↘ 20 (Sandbox Security)
                                                                          14 (Query Builder) → 15 (Stats Engine)
                                                                                                   16 (i18n Infra) → 17 (Localization)
                                                                                                                      18 (API & Keys)
                                                                                                                      21 (Privacy Tools)
                                                                                                                      22 (Release v2.3.0)
```

---

*Last updated: 2026-07-20 — scope amended per local-first audit. See `PHASE_III_LOCAL_FIRST_AUDIT.md` for full rationale.*
