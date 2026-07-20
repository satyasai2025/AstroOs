# AstroOS Phase III / v2.3.0 Roadmap

**Version:** v2.3.0 — Phase III  
**Codename:** "Lakshmi" (Expansion & Integration)  
**Date:** 2026-07-19  
**Status:** PLANNING  
**Predecessor:** v2.2.0 Phase II ("Arundhati") complete  
**Author:** `[rtk:astroos-governance]`

---

## Theme

**From Enterprise Platform to Multi-Channel Ecosystem.** Phase III extends AstroOS beyond desktop/browser into mobile apps, plugin architecture, real-time collaboration, and advanced analytics marketplace. Users get native mobile experiences, developers can build/share plugins, and teams can collaborate on research projects in real-time.

---

## Operating Model (unchanged)

| Office | Owns | Does NOT own |
|---|---|---|
| **Engineering (CEO-ENG)** | Backend, frontend, mobile apps, SDKs, API, DB, CI/CD, testing, performance, security, DevOps | Architecture decisions, astrology knowledge, benchmarks, research datasets |
| **Architecture (CAO)** | System architecture, ADRs, RFCs, module boundaries, dependency rules, plugin API design | Implementation |
| **Knowledge (CKO)** | Ontology, classical texts, catalogues, glossary, cross-references, conflicts, Knowledge Graph | Calculations |
| **Benchmark (CBO)** | Benchmark specs, gold-standard datasets, accuracy metrics, validation methodology, ML model evals | Algorithm implementation |
| **Research Data (CRDO)** | Research datasets, metadata, data standards, import pipelines, dataset quality/versioning, sync protocols | Benchmark rules, software implementation |

---

## Phase Breakdown

### Phase III.1 — Mobile Apps (React Native) (4-5 weeks)

**Goal:** Native iOS + Android apps with full offline-first capability. Users can cast charts, read reports, run basic research queries on mobile without connectivity.

**Engineering (CEO-ENG):**
- React Native app architecture (TypeScript, Expo or bare RN)
- Core features: birth chart generation, D1/D9 display, Dasha timeline, yoga detection, basic reports
- Offline-first SQLite sync with local PostgreSQL data (bidirectional)
- Push notification support (upcoming transits, Dasha changes)
- In-app purchase integration (premium reports, specialized analyses)
- iOS App Store + Google Play submission process

**Architecture (CAO):**
- ADR: Mobile sync protocol (CRDT vs last-write-wins vs manual merge)
- ADR: Offline cache eviction strategy
- ADR: Push notification provider choice (FCM, APNs, unified)
- Design: Plugin swizzling for mobile (extend without modifying core)

**Quality (QA):**
- Mobile device lab (iOS + Android physical devices, various versions)
- Offline/online transition testing
- App store submission checklist + compliance review

---

### Phase III.2 — Plugin Marketplace & API (3-4 weeks)

**Goal:** Open AstroOS to third-party plugins. Developers can create custom calculators, reports, UI components, AI models. Marketplace provides discovery, reviews, and payments (if monetized).

**Engineering (CEO-ENG):**
- Plugin sandbox architecture (isolated JavaScript/Python execution)
- Plugin API surface: chart data, yoga detection, knowledge queries, report generation
- Marketplace backend: listing, search, ratings, versioning, payment (Stripe)
- Developer portal: docs, sandbox, plugin validation CI
- Plugin lifecycle (install, update, enable/disable, uninstall)

**Architecture (CAO):**
- ADR: Plugin security model (sandbox CPU/memory limits, network access, data isolation)
- ADR: Plugin signing and verification
- ADR: Marketplace tax/legal considerations
- Design: Hit-and-run plugin API (plugins can call core engines, core can call plugins)

**Knowledge (CKO):**
- Plugin taxonomy: which astrology categories do plugins cover? (yoga detection, report themes, data import)
- Plugin markup/review for accuracy

**Governance (GOV):**
- Plugin submission guidelines, code of conduct, content policy
- Payment processing compliance (GDPR, PCI-DSS if handling cards directly)

---

### Phase III.3 — Real-Time Collaboration (3 weeks)

**Goal:** Multi-user research projects. Teams can work on the same chart/research simultaneously, see each other's cursors, chat inline, version snapshots.

**Engineering (CEO-ENG):**
- WebSocket-based real-time sync (Operational Transformation or CRDT)
- Presence indicators (who's viewing/editing)
- Inline comments, @mentions, annotations
- Project sharing (public/private links, team workspaces)
- History/versioning (snapshot comparison, time-travel)

**Architecture (CAO):**
- ADR: Sync protocol (OT vs CRDT)
- ADR: Conflict resolution strategy
- ADR: Real-time infrastructure (websocket scaling, room management)
- Design: Privacy model (role-based access control for projects)

**Quality (QA):**
- Concurrent user stress test (10+ users on same project)
- Network partition recovery (what happens when connection drops?)
- Privacy test: B cannot access A's private projects

---

### Phase III.4 — Advanced Analytics & Benchmarking Tools (3-4 weeks)

**Goal:** Power-user analytics suite. Cohort analysis, correlation studies, statistical significance testing, custom query builder, visualizable data exports.

**Engineering (CEO-ENG):**
- Query builder UI (drag-and-drop variables, filters, aggregations)
- Statistical analysis engine (Pearson correlation, chi-squared, t-tests, Bayes factors)
- Cohort segmentation (group births by criteria, compare outcomes)
- Visualization library (interactive scatter plots, heatmaps, time series)
- Report automation (scheduled PDF/email exports)

**Benchmark (CBO):**
- Benchmark statistical methods: validate significance calculations against known datasets
- A/B testing framework for research hypotheses

**Knowledge (CKO):**
- Documentation: explain statistical methods in astrological context (is this correlation spurious?)
- Guardrails: warn users about p-hacking, multiple comparison problems

**Research Data (CRDO):**
- Curate open research datasets (publicat Birth-death data for statistical testing)
- Data governance: anonymization best practices, consent management

---

### Phase III.5 — Internationalization & Localization (2-3 weeks)

**Goal:** Global readiness. UI translations, cultural adaptations, regional astrological variations (Jyotish vs Western vs Chinese).

**Engineering (CEO-ENG):**
- i18n infrastructure: message extraction, translation memory
- RTL support (for Arabic/Hebrew, if applicable)
- Locale-specific defaults (date formats, house systems, ayanamsa preferences)
- Regional astronomy: ecliptic vs sidereal, local star maps

**Knowledge (CKO):**
- Cultural adaptation guidelines: which classical texts cover which regions?
- Terminology normalization across schools of astrology
- Glossary translations (English ⇄ Spanish, Hindi, French, German, etc.)

**Quality (QA):**
- Linguistic QA: native speaker reviews of translations
- Functional testing with different locales (RTL layout, date parsing)

---

### Phase III.6 — Developer Experience (API Exposure) (2 weeks)

**Goal:** External developers can build on AstroOS. Public REST API, GraphQL endpoint, Python/JS SDKs **with passport and API key system**, webhook triggers.

**Engineering (CEO-ENG):**
- Public API documentation (OpenAPI 3.0 spec)
- OAuth 2.0 flow for third-party apps
- API key management panel for users
- Rate limiting and quotas
- Webhook system (on event X, POST to URL Y)
- Developer portal with API references, interactive playground

**Architecture (CAO):**
- ADR: API authentication model (OAuth 2.0 vs API keys)
- ADR: Rate limiting algorithm (token bucket, sliding window)
- ADR: Backward compatibility policy (deprecation timeline)

**Governance (GOV):**  
- API toS for third-party developers (acceptable use, data usage)
- API abuse detection (monitoring, blocking)

---

## Success Criteria (M3 Definition)

1. **Mobile apps published** — iOS + Android apps downloadable, generate chart offline
2. **Plugin marketplace live** — 10+ plugins submitted (third-party), 1000+ downloads total
3. **Real-time collaboration** — 10+ concurrent users on one project, no conflicts
4. **Advanced analytics core** — correlated birth-death sample dataset with significance p<0.05
5. **i18n coverage** — 5 languages localized (ES, HI, FR, DE, AR)
6. **Public API live** — API keys awarded to 10+ developers, 1000+ authenticated requests/day

---

## Out of Scope (for now)

- Full SaaS multi-tenancy (that's Phase IV)
- Machine learning model training (Phase IV)
- Blockchain/crypto integrations (consultation marketdx)
- VR/AR chart visualization (遥远 future)

---

*Last updated: 2026-07-19*