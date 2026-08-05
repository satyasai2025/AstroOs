# AstroOS — Comprehensive Audit & Implementation Plan

> **Date:** 2026-08-05
> **Version:** v2.3.0 (Phase III "Lakshmi" complete)
> **Status:** Audit complete, ready for implementation

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Audit](#2-architecture-audit)
3. [Feature-by-Feature Audit](#3-feature-by-feature-audit)
4. [Known Issues & Gaps](#4-known-issues--gaps)
5. [Implementation Plan](#5-implementation-plan)
6. [Execution Order](#6-execution-order)
7. [Open Questions](#7-open-questions)

---

## 1. Project Overview

AstroOS is a Vedic astrology platform built as a monorepo with:

| Component | Technology | Location |
|-----------|-----------|----------|
| **Frontend** | Next.js (TypeScript, Tailwind CSS) | `apps/web/` |
| **Backend** | Python / FastAPI (80+ endpoints) | `apps/api/` |
| **Shared Packages** | Python | `packages/shared/`, `packages/audit_engine/`, `packages/knowledge-engine/` |
| **SDKs** | Python + TypeScript | `sdks/python/`, `sdks/typescript/` |
| **Database** | PostgreSQL + Alembic migrations | `database/` |
| **Knowledge Base** | YAML catalogues | `knowledge/`, `jyotish-knowledge-base/` |
| **Report Templates** | Jinja2 HTML | `templates/reports/` |
| **Deployment** | Docker, K8s, PM2 (local-first mandate) | `deploy/`, `Dockerfile.prod` |

### Completed Phases

| Phase | Name | Version | Status |
|-------|------|---------|--------|
| A | Platform Integration | v2.0 | ✅ Complete |
| B | Research Engine | v2.0 | ✅ Complete |
| C | Benchmark Execution | v2.0 | ✅ Complete |
| D | Knowledge Intelligence | v2.0 | ✅ Complete |
| E | AI Layer | v2.0 | ✅ Complete |
| F | Reports | v2.0 | ✅ Complete |
| G | SDK | v2.0 | ✅ Complete |
| H | Production | v2.0 | ✅ Complete |
| II | "Arundhati" | v2.2.0 | ✅ Complete |
| III | "Lakshmi" | v2.3.0 | ✅ Complete |
| IV | "Chandrika" | v2.4.0 | ⏳ DRAFT (not started) |

---

## 2. Architecture Audit

### Frontend Routes (apps/web/src/app/)

| Route | Purpose | Status |
|-------|---------|--------|
| `/` | Home page | ✅ Built |
| `/(auth)/login` | Login | ✅ Built |
| `/(auth)/register` | Register | ✅ Built |
| `/(auth)/forgot-password` | Password reset | ✅ Built |
| `/(auth)/reset-password` | Password reset | ✅ Built |
| `/admin` | Admin panel | ✅ Built |
| `/admin/health` | System health | ✅ Built |
| `/admin/literature` | Literature manager | ✅ Built |
| `/admin/plugins` | Plugin engine | ✅ Built |
| `/admin/rules` | Rule management | ✅ Built |
| `/admin/users` | User management | ✅ Built |
| `/admin-login` | Admin login | ✅ Built |
| `/charts` | Charts list | ✅ Built |
| `/charts/[chartId]` | Chart detail view | ✅ Built |
| `/charts/compare` | Compare charts | ✅ Built |
| `/charts/history` | Chart history | ✅ Built |
| `/charts/house-dependency-2` | House dependency network | ✅ Built |
| `/charts/import` | Import charts | ✅ Built |
| `/charts/transit` | Transit charts | ✅ Built |
| `/compatibility/report` | Compatibility report | ✅ Built |
| `/dashboard` | Dashboard | ✅ Built |
| `/karakatva` | Karakatva explorer | ✅ Built |
| `/knowledge` | Knowledge base | ✅ Built |
| `/knowledge/admin` | Knowledge admin | ✅ Built |
| `/knowledge/bphs` | BPHS browser | ✅ Built |
| `/knowledge/browse` | Browse knowledge | ✅ Built |
| `/knowledge/literature` | Literature | ✅ Built |
| `/knowledge/saravali` | Saravali browser | ✅ Built |
| `/knowledge/tools` | Knowledge tools | ✅ Built |
| `/life/career` | Career predictions | ✅ Built |
| `/life/health` | Health predictions | ✅ Built |
| `/life/marriage` | Marriage predictions | ✅ Built |
| `/life/timeline` | Life timeline | ✅ Built |
| `/predictions` | Prediction Chain Explorer | ✅ Built |
| `/reports` | Reports hub | ✅ Built |
| `/reports/ai` | AI reports | ✅ Built |
| `/reports/comparison` | Comparison reports | ✅ Built |
| `/reports/export` | Export reports | ✅ Built |
| `/reports/pdf` | PDF reports | ✅ Built |
| `/research` | Research hub | ✅ Built |
| `/research/cases` | Research cases | ✅ Built |
| `/research/dashboard` | Research dashboard | ✅ Built |
| `/research/datasets` | Datasets | ✅ Built |
| `/research/events` | Events | ✅ Built |
| `/research/hypotheses` | Hypotheses | ✅ Built |
| `/research/import` | Import research data | ✅ Built |
| `/research/notebook` | Research notebook | ✅ Built |
| `/research/patterns` | Pattern discovery | ✅ Built |
| `/research/projects` | Research projects | ✅ Built |
| `/research/query-builder` | Query builder | ✅ Built |
| `/research/reverse-search` | Reverse search | ✅ Built |
| `/research/rules` | Research rules | ✅ Built |
| `/settings/preferences` | Preferences | ✅ Built |
| `/settings/profile` | Profile | ✅ Built |
| `/settings/security` | Security | ✅ Built |
| `/settings/theme` | Theme | ✅ Built |
| `/transit/[reportId]` | Transit report | ✅ Built |

### Frontend Components (apps/web/src/components/)

#### charts/ (25 components)
- `AshtakavargaPanel.tsx` — Ashtakavarga display
- `AvasthaPanel.tsx` — Planetary states
- `ChartDetailPanel.tsx` — Chart detail
- `ChartDetailView.tsx` — Full chart view
- `DashaTimeline.tsx` — Dasha timeline
- `DivisionalChartsPanel.tsx` — Varga charts
- `HouseDependencyNetwork.tsx` — House dependency graph
- `InteractiveKundliView.tsx` — Interactive Kundli
- `IshtaKashtaBalaPanel.tsx` — Ishta/Kashta Bala
- `JaiminiPanel.tsx` — Jaimini astrology
- `KPSignificatorExplorer.tsx` — KP significators
- `LifeEventTimeline.tsx` — Life events
- `NakshatraPadaSelector.tsx` — Nakshatra/Pada
- `NorthIndianChart.tsx` — North Indian chart
- `PlanetDetailPanel.tsx` — Planet details
- `PlanetExplorerPanel.tsx` — Planet explorer
- `PlanetRelationshipGraph.tsx` — Planet relationships (v1)
- `PlanetRelationshipGraph2.tsx` — Planet relationships (v2)
- `PlanetStrengthHeatmap.tsx` — Strength heatmap
- `PlanetStrengthRadar.tsx` — Strength radar
- `PredictionChainExplorer.tsx` — Prediction chain (legacy)
- `RecomputeChartModal.tsx` — Recompute chart
- `TransitTimeline.tsx` — Transit timeline
- `VedhaAnalysisPanel.tsx` — Vedha analysis
- `YogasPanel.tsx` — Yogas display

#### charts/predictions/ (7 components)
- `FormulaInspector.tsx` — Formula inspection
- `PredictionDashaTimeline.tsx` — Dasha timeline in predictions
- `PredictionDataSources.tsx` — Data provenance
- `PredictionScoreBreakdown.tsx` — Score breakdown
- `PredictionScorePanel.tsx` — Final score
- `PredictionStepDetail.tsx` — Step detail
- `PredictionStepList.tsx` — Step list

#### charts/transit/ (2 components)
- `TransitAlerts.tsx` — Transit alerts
- `TransitWheel.tsx` — Transit wheel

#### dashboard/ (8 components)
- `ClassicalLiteratureView.tsx`
- `CreateChartModal.tsx`
- `CreateCompatibilityModal.tsx`
- `CreateTransitModal.tsx`
- `DashboardOverview.tsx`
- `KpiScorecards.tsx`
- `ResearchDashboard.tsx`
- `ReverseSearchView.tsx`

#### Other component directories
- `admin/` — 8 admin components
- `ai/` — 5 AI components
- `auth/` — 4 auth components
- `layout/` — 4 layout components
- `report/` — 1 report component
- `research/` — 12 research components
- `ui/` — 20 UI primitives
- `workflow/` — 3 workflow + 11 panel components

### Frontend Lib (apps/web/src/lib/)

| File | Purpose |
|------|---------|
| `predictions/chainEngine.ts` | Prediction graph builder (pure function) |
| `predictions/scoring.ts` | 9 scoring factors with documented default weights |
| `predictions/types.ts` | Prediction type definitions |
| `kpiScoring.ts` | KPI scorecard calculations |
| `astro.ts` | Astrology utilities |
| `avastha.ts` | Avastha data hooks |
| `shadbala.ts` | Shadbala data hooks |
| `transitPatterns.ts` | Transit pattern logic |
| `workflow.ts` | Workflow orchestration hooks |
| `store.ts` | Zustand state store |
| `types.ts` | Shared TypeScript types |
| `charts.ts` | Chart data hooks |
| `karakatva.ts` | Karakatva data hooks |
| `kpSignificators.ts` | KP significator logic |
| `nakshatraKnowledge.ts` | Nakshatra knowledge |
| `houseLifeAreas.ts` | House → life area mapping |
| `events.ts` | Event data hooks |
| `research.ts` | Research data hooks |
| `researchCases.ts` | Research case hooks |
| `geocoding.ts` | Geocoding hooks |
| `ai.ts` | AI hooks |
| `auth.ts` | Auth hooks |
| `admin.ts` | Admin hooks |
| `adminAuth.ts` | Admin auth hooks |
| `api.ts` | API client |
| `chart-alignment.ts` | Chart alignment |

### Backend API (apps/api/)

#### Routers (33 routers)
`admin_auth`, `admin`, `ai_phase_e`, `ai`, `ashtakavarga`, `auth`, `avastha`, `batch`, `benchmark`, `dasha`, `dataset_import`, `datasets`, `digital_twin`, `divisional`, `events`, `export`, `geocoding`, `horoscope`, `jobs`, `knowledge_graph`, `knowledge`, `report`, `research_tools`, `research`, `shadbala`, `statistics`, `timeline`, `transit_patterns`, `transit`, `visualization`, `workflow`, `ws`, `yoga`

#### Services (70+ engines)
Key engines:
- **Calculation:** `horoscope_engine`, `dasha_engine`, `divisional_engine`, `shadbala_engine` (16 sub-components), `ashtakavarga_engine`, `aspect_engine`, `graha_engine`, `house_engine`, `nakshatra_vedha_calculator`, `vedha_calculator`
- **Prediction:** `best_bet_engine`, `marriage_timing_engine`, `sadhu_padhdhati_engine`, `ot_engine`
- **Yoga:** `yoga_engine`, `yoga_predicates`, `yoga_registry`, `yoga_strength`, `yoga_timeline` + 12 yoga type modules
- **Rules:** `rule_engine`, `rule_registry` + 9 rule type modules
- **AI:** `ai_engine`, `ai_fallback`, `ai_validator`, `explanation_engine`, `hypothesis_generator`
- **Research:** `research_engine`, `research_assistant_engine`, `pattern_discovery`, `pattern_explainer`, `pattern_graph`, `hypothesis_validation_service`
- **Reports:** `report_engine`, `report_template_engine`, `batch_report_service`, `export_engine`
- **Transit:** `transit_engine`, `transit_patterns`
- **Compatibility:** `ashtakoota_engine`, `chart_comparison_engine`
- **Knowledge:** `knowledge_engine`, `knowledge_graph_engine`, `knowledge_import_pipeline`, `ontology_registry`
- **Other:** `workflow_orchestrator`, `ephemeris_service`, `geocoding_service`, `statistics_engine`, `timeline_engine`, `event_engine`, `verification_engine`, `visualization_engine`, `digital_twin_engine`

#### Shadbala Sub-components (16 modules)
`ayana_bala`, `chesta_bala`, `dig_bala`, `dina_hora_bala`, `drekkana_bala`, `drik_bala`, `ishta_kashta_bala`, `kendradi_bala`, `naisargika_bala`, `nathonnata_bala`, `ojayugmarasyamsa_bala`, `paksha_bala`, `saptavargaja_bala`, `tribhaga_bala`, `uchcha_bala`, `yuddha_bala`

#### Yoga Types (12 modules)
`arishta_yoga`, `chandra_yoga`, `composite_yogas`, `dhana_yoga`, `gajakesari`, `nabhasa_yoga`, `neecha_bhanga`, `other_classical_yogas`, `panch_mahapurusha`, `raja_yoga`, `sanyasa_yoga`, `solar_yogas`

---

## 3. Feature-by-Feature Audit

### 3.1 Prediction Chain Explorer ⭐ (Current Priority)

**Status:** ✅ Core built, needs enhancement

**What exists:**
- `/predictions` page with full layout
- `chainEngine.ts` — pure function that builds a `PredictionGraph` from chart data
- `scoring.ts` — 9 scoring factors with documented default weights:
  1. House & Sign Strength (exalted/own/debilitated/kendra/trikona/dusthana)
  2. Shadbala Total Strength (rupas + combustion)
  3. Digbala (directional strength)
  4. Aspects Received (benefic/malefic with orb)
  5. Relevant Yogas (structural match, capped at 3)
  6. Dasha Activation (Mahadasha + Antardasha match)
  7. Current Transit (favorable/Sade Sati/Ashtama Shani)
  8. Avastha (Deeptadi dignity-state)
  9. Karaka Strength (marriage/wealth only)
- 7 sub-components: StepList, StepDetail, ScorePanel, ScoreBreakdown, DashaTimeline, DataSources, FormulaInspector
- 4 life areas: career (10th), marriage (7th), wealth (2nd), health (6th)
- Confidence calculation from data completeness
- Dashboard deep-link support via `?kpi=` URL param

**What's missing:**
- [ ] Computation graph visualization (D3 force-directed graph)
- [ ] More life areas (education, children, foreign settlement, spirituality)
- [ ] Enhanced data provenance viewer
- [ ] Dashboard KPI card → deep link integration
- [ ] AI explanation from computation graph

---

### 3.2 Prediction Engine

**Status:** ✅ Partially implemented

**What exists:**
- 9 scoring factors with versioned formulas (`formulaVersion: "v1"`)
- Documented default weights (transparent, tunable)
- Confidence calculation from data availability
- `kpiScoring.ts` for dashboard KPI scorecards

**What's missing:**
- [ ] User-defined proprietary weights (current are documented defaults)
- [ ] Cross-check against benchmark charts
- [ ] More prediction modules (education, children, foreign, spirituality)
- [ ] Narrative explanations per factor

---

### 3.3 Research & Explainability

**Status:** ✅ Built, needs enhancement

**What exists:**
- Full research suite: projects, cases, datasets, hypotheses, patterns, query-builder, reverse-search, notebook
- `ExplanationPanel.tsx` in workflow
- `explanation_engine.py` in backend
- AI engine with template-based NLG (8 generators)

**What's missing:**
- [ ] AI explanation from computation graph
- [ ] Rule traceability (show which classical rules fired)
- [ ] Yoga evidence (show structural match details)
- [ ] Provenance viewer (full data source chain)

---

### 3.4 Reports

**Status:** ⚠️ Templates exist, rendering broken

**What exists:**
- 7 HTML templates in `templates/reports/`: horoscope, marriage, career, health, wealth, spiritual, transit
- `report_template_engine.py` (Jinja2 + WeasyPrint)
- `ReportExport.tsx` component
- `/reports/` pages: ai, comparison, export, pdf
- CSV export works correctly

**What's missing / broken:**
- [ ] Fix AMP-009 (router bug in `report.py`)
- [ ] Verify AMP-010 resolved (templates now exist)
- [ ] Modern interactive HTML report viewer
- [ ] Interactive sections (collapsible, expandable)
- [ ] Better export options (PDF, print, share)
- [ ] Wire Prediction Chain Explorer data into reports

---

### 3.5 Interactive Kundli Workspace

**Status:** ✅ Built, needs enhancement

**What exists:**
- `InteractiveKundliView.tsx`
- `ChartDetailView.tsx` with 7 tabs
- `PlanetDetailPanel.tsx`, `PlanetExplorerPanel.tsx`
- `NorthIndianChart.tsx`
- Hover-driven side panel

**What's missing:**
- [ ] Multi-chart workspace (tab system)
- [ ] Compare charts overlay
- [ ] Transit overlay on natal chart
- [ ] Synastry view
- [ ] Research mode integration
- [ ] AI Search
- [ ] Active chart tabs

---

### 3.6 Prediction Modules

**Status:** ✅ 4 built, 4 needed

**What exists:**
- Career (10th house)
- Marriage (7th house)
- Wealth (2nd house)
- Health (6th house)

**What's missing:**
- [ ] Education (5th house)
- [ ] Children (5th house)
- [ ] Foreign settlement (12th house)
- [ ] Spirituality (9th house)
- [ ] Richer explainable predictions for all modules

---

### 3.7 Transit Module

**Status:** ✅ Built, needs enhancement

**What exists:**
- `TransitWheel.tsx`, `TransitAlerts.tsx`, `TransitTimeline.tsx`
- `/transit/[reportId]` page
- `/charts/transit/` page
- Backend: `transit_engine.py`, `transit_patterns.py`
- Transit factor in Prediction Chain Explorer

**What's missing:**
- [ ] Better transit visualization (animated wheel)
- [ ] Transit timeline with date scrubber
- [ ] Transit explanation (classical reasoning)
- [ ] Transit → prediction impact (deeper integration)

---

### 3.8 Horary (Prashna)

**Status:** ❌ Not built

**What's missing:**
- [ ] Horary input flow (question + number)
- [ ] Prashna number support (1-108 or 1-249)
- [ ] Horary-specific calculations
- [ ] Dedicated Horary report
- [ ] Horary navigation entry

---

### 3.9 Compatibility

**Status:** ✅ Built, needs enhancement

**What exists:**
- `/compatibility/report` page
- `ComparisonWorkspace.tsx`, `EnhancedRadarChart.tsx`, `VennDiagram.tsx`
- `PdfExporter.tsx`, `CsvExporter.tsx`, `JsonExporter.tsx`
- Backend: `ashtakoota_engine.py` (Ashtakoota Guna Milan)
- `chart_comparison_engine.py`

**What's missing:**
- [ ] Better workflow (guided input → comparison → report)
- [ ] Relationship scoring beyond Ashtakoota
- [ ] Explainable compatibility (trace scores to classical rules)
- [ ] Visual comparison improvements (side-by-side chart overlay)

---

### 3.10 Dashboard

**Status:** ✅ Built, needs enhancement

**What exists:**
- `DashboardOverview.tsx`, `KpiScorecards.tsx`
- `CreateChartModal.tsx`, `CreateCompatibilityModal.tsx`, `CreateTransitModal.tsx`
- Search bar
- Redirects to chart view after creation

**What's missing:**
- [ ] Better KPI cards (clickable, with mini-sparklines)
- [ ] Research widgets
- [ ] Current period snapshot (dasha + transit)
- [ ] Transit snapshot
- [ ] Alerts panel
- [ ] Prediction shortcuts

---

### 3.11 Knowledge Layer

**Status:** ✅ Partially built

**What exists:**
- `/knowledge` (browse, BPHS, Saravali, literature, tools, admin)
- `knowledge/catalogues/` with ~350 entries (graha, bhava, house, nakshatra)
- Backend: `knowledge_engine.py`, `knowledge_graph_engine.py`, `ontology_registry.py`
- Domain model: `Karakatva`, `KnowledgeBook`, `KnowledgeVerse`, `KnowledgeRule`

**What's missing:**
- [ ] Fix `knowledge_import_pipeline.py` (dead code, broken)
- [ ] Classical rule browser
- [ ] Yoga encyclopedia
- [ ] Search across rules
- [ ] Cross-reference engine
- [ ] DB tables are empty (0 rows)

---

## 4. Known Issues & Gaps

| # | Issue | Impact | Source |
|---|-------|--------|--------|
| 1 | PDF/HTML report rendering broken | Reports don't generate | AMP-009, AMP-010 |
| 2 | Karakatva DB tables empty | Knowledge search returns nothing | V3 Roadmap |
| 3 | Knowledge import pipeline dead code | Can't seed DB | V3 Roadmap |
| 4 | Prediction formulas use default weights | Not proprietary logic | V3 Roadmap |
| 5 | No live testing done | Phases 1-9 syntax-verified only | V3 Roadmap |
| 6 | No Horary module | Missing feature | Tasks file |
| 7 | dataset_import router ungated | Security gap | V2 Status |
| 8 | Geocoding uses public Nominatim | Rate limits in production | V2 Status |
| 9 | Documentation drift | `docs/architecture.md` stale | Phase IV Roadmap |

---

## 5. Implementation Plan

### Phase 1: Prediction Chain Explorer Enhancements ⭐
**Effort:** Medium | **Dependencies:** None

| Task | Files | Description |
|------|-------|-------------|
| 1.1 Add computation graph | New: `components/charts/predictions/ComputationGraph.tsx` | D3 force-directed graph: House Lord → [Factors] → Delta → Final Score |
| 1.2 Add 4 life areas | `lib/predictions/scoring.ts`, `lib/predictions/types.ts` | Education (5th), Children (5th), Foreign (12th), Spirituality (9th) |
| 1.3 Dashboard deep links | `components/dashboard/KpiScorecards.tsx` | Make KPI cards clickable → `/predictions?chartId=X&kpi=Y` |
| 1.4 Enhanced provenance | `components/charts/predictions/FormulaInspector.tsx` | Show full API field → factor → score chain |
| 1.5 AI explanation | `components/workflow/panels/ExplanationPanel.tsx` | Feed PredictionGraph to NLG |

### Phase 2: Dashboard Redesign
**Effort:** Medium | **Dependencies:** Phase 1 (deep links)

| Task | Files | Description |
|------|-------|-------------|
| 2.1 Redesign KPI cards | `components/dashboard/KpiScorecards.tsx` | Clickable cards with score + trend |
| 2.2 Current period snapshot | New: `components/dashboard/CurrentPeriodSnapshot.tsx` | Current Mahadasha/Antardasha + transit summary |
| 2.3 Transit snapshot | New: `components/dashboard/TransitSnapshot.tsx` | Key transit events |
| 2.4 Alerts panel | New: `components/dashboard/AlertsPanel.tsx` | Sade Sati, Ashtama Shani, etc. |
| 2.5 Prediction shortcuts | `components/dashboard/DashboardOverview.tsx` | Quick-link cards to `/predictions?kpi=X` |
| 2.6 Research widgets | `components/dashboard/DashboardOverview.tsx` | Research project status |

### Phase 3: Report UI Redesign
**Effort:** Medium-Large | **Dependencies:** Phase 1 (data feed)

| Task | Files | Description |
|------|-------|-------------|
| 3.1 Fix PDF rendering | `api/routers/report.py`, `api/services/report_template_engine.py` | Fix AMP-009 router bug |
| 3.2 Verify templates | `templates/reports/*.html` | Verify AMP-010 resolved |
| 3.3 Modernize templates | `templates/reports/*.html` | Modern CSS, cards, tabs, collapsible |
| 3.4 Interactive report viewer | `apps/web/src/app/reports/` | Client-side interactive viewer |
| 3.5 Wire prediction data | `components/report/ReportExport.tsx` | Include Prediction Chain data in reports |

### Phase 4: Transit Improvements
**Effort:** Medium | **Dependencies:** None

| Task | Files | Description |
|------|-------|-------------|
| 4.1 Enhanced transit wheel | `components/charts/transit/TransitWheel.tsx` | Animation + date scrubber |
| 4.2 Scrollable timeline | `components/charts/TransitTimeline.tsx` | Key events with date navigation |
| 4.3 Transit explanation | New: `components/charts/transit/TransitExplanation.tsx` | Classical reasoning per transit |
| 4.4 Prediction impact | `lib/predictions/scoring.ts` | Deeper transit factor integration |

### Phase 5: Horary Module
**Effort:** Large | **Dependencies:** None

| Task | Files | Description |
|------|-------|-------------|
| 5.1 Horary input form | New: `app/horary/page.tsx`, `components/horary/HoraryInputForm.tsx` | Question + number (1-108) |
| 5.2 Horary engine | New: `api/services/horary_engine.py`, `api/domain/horary.py` | Number → sign → chart calculation |
| 5.3 Horary router | New: `api/routers/horary.py` | API endpoints |
| 5.4 Horary report | New: `templates/reports/horary.html` | Dedicated report template |
| 5.5 Horary result UI | New: `components/horary/HoraryResult.tsx` | Result display |
| 5.6 Navigation | `components/layout/NavPanel.tsx` | Add Horary to nav |

### Phase 6: Compatibility Improvements
**Effort:** Medium | **Dependencies:** None

| Task | Files | Description |
|------|-------|-------------|
| 6.1 Guided workflow | `app/compatibility/report/page.tsx` | Partner 1 → Partner 2 → Results flow |
| 6.2 Extended scoring | `api/services/ashtakoota_engine.py` | Planetary harmony, dasha compatibility |
| 6.3 Explainable panel | New: `components/compatibility/CompatibilityExplanation.tsx` | Trace scores to classical rules |
| 6.4 Visual comparison | `app/charts/compare/components/ComparisonWorkspace.tsx` | Side-by-side chart overlay |

### Phase 7: AI Explanations
**Effort:** Medium | **Dependencies:** Phase 1 (computation graph)

| Task | Files | Description |
|------|-------|-------------|
| 7.1 Prediction → AI | `api/services/explanation_engine.py` | Feed PredictionGraph to NLG |
| 7.2 Rule traceability | New: `components/charts/RuleTraceability.tsx` | Show fired rules with sources |
| 7.3 Yoga evidence | New: `components/charts/YogaEvidence.tsx` | Show structural match details |
| 7.4 Provenance viewer | `components/charts/predictions/FormulaInspector.tsx` | Full data source chain |

### Phase 8: Knowledge Explorer
**Effort:** Large | **Dependencies:** None

| Task | Files | Description |
|------|-------|-------------|
| 8.1 Fix import pipeline | `api/services/knowledge_import_pipeline.py` | Fix dead code, wire to seed step |
| 8.2 Rule browser | New: `app/knowledge/rules/page.tsx` | Classical rule browser |
| 8.3 Yoga encyclopedia | New: `app/knowledge/yogas/page.tsx` | Categorized, searchable yogas |
| 8.4 Cross-reference engine | `api/services/knowledge_graph_engine.py` | Link yogas → rules → karakatvas |
| 8.5 Full-text search | `api/routers/knowledge.py` | Search across knowledge base |

---

## 6. Execution Order

| Phase | Work Item | Effort | Dependencies | Priority |
|-------|-----------|--------|--------------|----------|
| 1 | Prediction Chain Explorer | Medium | None | ⭐ Highest |
| 2 | Dashboard Redesign | Medium | Phase 1 | High |
| 3 | Report UI Redesign | Medium-Large | Phase 1 | High |
| 4 | Transit Improvements | Medium | None | Medium |
| 5 | Horary Module | Large | None | Medium |
| 6 | Compatibility | Medium | None | Medium |
| 7 | AI Explanations | Medium | Phase 1 | Medium |
| 8 | Knowledge Explorer | Large | None | Lower |

### Additional Work Items

| Work Item | Effort | Notes |
|-----------|--------|-------|
| Prediction Modules (4 new) | Medium | Extend `scoring.ts` with education, children, foreign, spirituality |
| Interactive Kundli Workspace | Medium-Large | Multi-chart tabs, transit overlay, synastry |
| Prediction Engine validation | Medium | Replace default weights, benchmark validation |
| Documentation audit | Small | Fix stale claims in `docs/architecture.md` |

---

## 7. Open Questions

1. **KPI scoring formulas:** What should feed Career/Marriage/Wealth/Health indices, and how are they weighted? (Current defaults are documented but not your proprietary logic)

2. **Horary method:** Which Prashna system — KP Horary (number 1-249) or classical (number 1-108)?

3. **Report style:** Any reference design for the modern report UI, or should I design from scratch?

4. **Knowledge base:** Should I fix the existing ~350-entry catalogue first, or do you have a larger dataset to import?

5. **Life areas:** For education and children, should they share the 5th house or have different primary houses?

6. **Transit visualization:** Any reference for the animated transit wheel, or should I design from scratch?

---

## Summary

AstroOS has a **strong foundation** — the backend computes everything needed (planets, houses, vargas, dashas, shadbala, ashtakavarga, yogas, transits), and the frontend has a rich component library with 25+ chart components, a full research suite, and a working Prediction Chain Explorer.

The main work is **enhancement and gap-filling**, not rebuilding:
- Enhance the Prediction Chain Explorer with a computation graph and more life areas
- Redesign the dashboard with clickable KPI cards and snapshot widgets
- Fix and modernize the report system
- Build the missing Horary module
- Improve transit visualization
- Enhance compatibility with explainable scoring
- Wire AI explanations to the computation graph
- Fix and expand the knowledge base

**Estimated total effort:** 6-8 weeks of focused development for all 8 phases.

---

*This document was generated from a direct code audit on 2026-08-05. All file paths and component names are verified against the actual codebase.*