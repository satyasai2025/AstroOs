# AstroOS Vision v3 — Interactive Intelligence Platform Roadmap

> Source: `astroos my vision.txt` (uploaded 2026-07-22). This document breaks that
> vision into buildable phases, honestly scoped against what already exists in
> the codebase today. No code changes were made writing this — planning only.

## Build status (updated 2026-07-23)

Phases 1, 2, 3, 4, 5, 6, 7, 8, and 9 are built and syntax-verified (comment-aware
brace/paren balance check on every TS/TSX file, `ast.parse` on every Python file —
this sandbox has no access to your actual Postgres database or a running
`pnpm dev`/`uvicorn`, so none of this has been LIVE-tested yet). Restart both
servers and click through it — that's the one thing only you can verify.

What to check first: `/dashboard` (KPI scorecards + search bar appear after
running an analysis), `/charts` (7 tabs: Chart View with hover-driven side
panel, Nakshatra/Pada, Dasha Timeline, Strength, Relationships, House Network,
Timeline, Prediction Chains), `/karakatva` (new nav link — search will show
empty results until you run `python -m apps.api.scripts.seed_knowledge` once).

Phase 10 (architecture consolidation) is deliberately not started — per its
own section below, it's meant to happen after the individual pieces are
validated against real use, not before. Also open: the two synthesized-KPI
and Prediction-Chain-Explorer formulas use documented default weights (see
`apps/web/src/lib/kpiScoring.ts`), not your own formulas — replace them
whenever you're ready to define your own.

## Deployment constraint (per your instruction, 2026-07-22)

**No Docker, no Kubernetes, no Redis.** Everything below assumes:
- Local development: native PostgreSQL + `uvicorn` (backend) + `pnpm dev` (frontend), exactly as it runs today.
- Future production: a plain Oracle Cloud VM running the same two processes (uvicorn + a Next.js build) behind a reverse proxy — no containers, no orchestration, no managed cache layer.
- This matches a decision already on record in `CLAUDE_START_HERE.md` / `ASTROOS_V2_STATUS.md` (Phase II amendment, 2026-07-20): Docker/K8s/Helm are permanently out of scope unless you explicitly reverse that.
- If a caching layer is ever genuinely needed (e.g. the Karakatva search gets slow), the local-first answer is an in-process cache or a Postgres materialized view — not Redis — unless you decide otherwise later.

## What today's AstroOS already gives this vision a head start on

The backend (`apps/api`) already computes, per chart, everything most of the new
visualizations would consume: D1 planets/houses/aspects/dignities, all 15 varga
charts, 6 dasha systems, Shadbala totals, Ashtakavarga, current transits, yoga
detection, and a rule engine. None of this needs to be recomputed — the new
frontend visualizations are a presentation layer over data the API already
returns from `POST /api/v1/workflow/analyze`. That's the good news: most of
this roadmap is frontend + a handful of new scoring/domain modules, not a
backend rewrite.

The one area that's genuinely thin is the **Karakatva Explorer** — see Phase 5.

---

## Phase 1 — Interactive Kundli Core (do this first)
**Effort: Medium — Backend: ready. Frontend: new.**

Replace the current static North Indian chart + side table (`apps/web/src/components/charts/NorthIndianChart.tsx`) with the hover-driven version from your vision: mouse over a planet → a side panel updates live with House, Sign, Nakshatra, Pada, Degree, Friends/Enemies, Aspects, Conjunctions, Karakatva, Yogas, Strength, Shadbala, Digbala, Combust/Retro, Avastha, and D9/D10/D60 position.

Every one of those fields is already in the `/workflow/analyze` response (chart, vargas, shadbala, ashtakavarga) except Digbala/Cheshtabala/Avastha, which would need a quick check of whether `shadbala_engine` already computes sub-components or only totals.

Includes: the top dashboard search bar (Search Person / DOB / TOB / POB / Compare Charts / AI Search — AI Search itself is deferred to Phase 9, the bar and basic search are not).

## Phase 2 — Dashboard KPI Scorecards
**Effort: Medium-Large — needs your domain input, not just code.**

- Strength Score, Current Dasha, Current Transit: derivable directly from existing Shadbala/dasha/transit data — cheap.
- Career Index, Marriage Index, Wealth Potential, Mental Stability, Health Risk: these are **new synthesis logic**, not raw data. Nothing in the backend today computes "Marriage Index: 68%" as a single number — it would need a defined formula (which houses/planets/yogas feed into it, and their weights). This is astrological-domain design work I'd need your judgment on before writing scoring code, similar to how AstroSage/AstroTalk define their proprietary index formulas.

## Phase 3 — Planet Relationship Graph
**Effort: Medium.** Aspect and dignity data already exists per chart. New: a D3 force-directed graph component, plus confirming the classical natural friend/enemy/neutral table exists somewhere as backend constants (if not, it's a small, well-defined static dataset to add).

## Phase 4 — House Dependency Network
**Effort: Medium-Large.** Needs two new pieces of domain content: (1) a static house → life-area mapping (1st→Body→Health→Confidence...), which is content you'd define once, and (2) house-strength scoring (is a house "weak" — from lord placement, benefic/malefic occupancy, aspects) — new logic, moderate complexity. The cascading red-highlight animation itself is a straightforward D3 graph once the data model exists.

## Phase 5 — Karakatva Explorer
**Effort: Extra-Large — this is a content project, not primarily a coding one.**

Reality check on what exists today (checked directly):
- The domain model already fits your vision well — `apps/api/domain/knowledge.py` already has a `Karakatva` entity (subject/graha/sign/house signification), plus `KnowledgeBook`/`KnowledgeVerse`/`KnowledgeRule`.
- There's real curated content already: `knowledge/catalogues/karakatvas/` (graha, bhava, house, nakshatra significations, source-cited to BPHS ch.33) — roughly **350 entries**, not 25,000.
- The database tables for this are **completely empty** — 0 rows.
- An import pipeline exists (`apps/api/services/knowledge_import_pipeline.py`) to load the YAML into the DB, but it's **dead code** (never called anywhere) and **broken** against the current YAML structure (expects an older, flatter format).

Realistic phasing within this phase: (a) fix the import pipeline and wire it into a seed step, (b) build the search/explorer UI against the ~350 real entries so it's genuinely useful early, (c) treat expanding 350 → thousands of significations as an ongoing content workstream running in parallel with everything else, not a blocking prerequisite.

## Phase 6 — Knowledge Graph Visualizations
**Effort: Medium.** Visualizes chains like Marriage → 7th House → Venus → Jupiter → Navamsa → Dasha → Prediction as a flow graph. Depends on Phase 5 having real content to walk through — low value before that.

## Phase 7 — Heatmaps & Radar Charts
**Effort: Small — quick win, can be done anytime, including in parallel with Phase 1.** Planet Strength bar heatmap and the spider/radar chart both sit directly on existing Shadbala output. Pure frontend, no new backend work.

## Phase 8 — Timelines
**Effort: Medium.** Transit Timeline (2025/Jan/Feb.../Saturn enters Pisces → Career↑) and the Life Event Timeline (Birth→School→Marriage...) both merge existing Dasha + Transit + Events data into one scrollable timeline component. The life-events portion can reuse the already-built Events module.

## Phase 9 — Compare Charts + AI Search
**Effort: Small-Medium.** Chart comparison already partially exists (`/charts/compare`, comparison report backend) — needs polishing to match this dashboard's UX. "AI Search" (natural-language search across saved charts / karakatvas) should start as plain keyword search first; true AI/semantic search is a later upgrade, not a Phase 1 requirement.

## Phase 10 — Architecture Consolidation ("AI Assistant" orchestration layer)
**Effort: Medium, do this last.** Once Phases 1–9 exist as working pieces, formalize the orchestration layer your architecture diagram describes (AI Assistant → Kundli/Rule/Prediction engines → Knowledge Graph DB → Visualization Layer) as an actual consolidation refactor. Doing this first, before individual pieces exist and prove themselves, risks over-architecting against requirements that haven't been validated yet.

---

## Recommended build order

1. Phase 1 (Interactive Kundli) — biggest visual "wow", backend already ready.
2. Phase 7 (Heatmap/Radar) — cheap parallel win, do alongside Phase 1.
3. Phase 2 (KPIs) — but pause on Career/Marriage/Wealth/Health indices until we define the scoring formulas together.
4. Phase 3 (Relationship Graph), then Phase 8 (Timelines).
5. Phase 4 (House Dependency Network).
6. Phase 5 (Karakatva Explorer) — start the pipeline fix + UI early, content expansion runs continuously in the background.
7. Phase 6 (Knowledge Graph Visualizations) once Phase 5 has content.
8. Phase 9 (Compare + Search polish).
9. Phase 10 (architecture consolidation) last.

## Open questions for you before Phase 2 and Phase 4 can really start

- What should feed Career Index / Marriage Index / Wealth Potential / Mental Stability / Health Risk, and how are they weighted? (This is the one place I can't guess — it's your product's proprietary logic.)
- Is there an existing source you want for the natural friend/enemy/neutral planet table (Phase 3) and the house→life-area mapping (Phase 4), or should I draft one from BPHS for your review?

---

## Phase 11 — Feature-parity backlog (from reference screenshots, 2026-07-23)

**Status: catalogued only, not started.** You shared screenshots of a reference
app (AstroNidan-branded) plus a fuller dashboard mockup of AstroOS's own
sidebar/section list. Explicitly deferred — "baad me karenge" — logged here
so nothing gets lost. Not scoped/estimated yet; do that when you're ready to
pick this up.

Gaps identified against what AstroOS has today:

1. **8 Gati (planetary speed classification)** — Sama/Sheeghra/Sheeghratara/
   Manda/Mandatara/Vakra/Anuvakra/Kutila, from Surya Siddhanta. Raw
   `speed_deg_per_day` is already computed internally (Shadbala/Chesta Bala)
   but not exposed. See tracked backlog task "[BACKLOG] Implement 8 Gati
   planetary speed classification" — 6 states are cheaply computable now
   (speed vs. classical mean motion per planet), Anuvakra/Kutila need
   multi-day trajectory tracking, don't fabricate thresholds for those.
2. **Today's Pulse** — a daily 0-100 "positivity strength" gauge with
   strong/weak planets, lucky colors/numbers, and a short daily-prediction
   list. New synthesis logic, same category of design work as Phase 2's
   indices (needs your formula/weights, not just code).
3. **Personality DNA** — Ayurdosha, Guna, Temperament, Varna, Shiva-Shakti,
   Element classification from the chart. Classical categories exist in
   Jyotish texts (e.g. Ayurdosha from Moon sign/nakshatra) but the exact
   derivation rules need sourcing before building — same "don't fabricate"
   caution as everything else in this app.
4. **Personality Wordcloud** — a visual word-cloud rendering of personality
   trait keywords. Pure presentation layer once trait data exists (depends
   on #3 or a simpler keyword-from-dignity/house-placement heuristic).
5. **Numerology Study** — Psychic/Destiny/Name number from name + birth
   date. A separate, well-defined classical system (Chaldean/Pythagorean
   numerology), not Vedic astrology — self-contained, no chart-engine
   dependency.
6. **Yoga grouping by category** — current Yoga Engine already detects
   yogas; the reference groups results under named categories (Surya
   Yogas, Chandra Yogas, Raja Yogas) as a display layer, not new detection
   logic.
7. **Remedies section** — nothing exists for this today; would need a
   sourced remedy-per-affliction dataset (gemstones/mantras/donations tied
   to specific dosha/weak-planet findings) — content project like Phase 5's
   Karakatva Explorer, not just code.
8. **Consultation/booking commerce** (live chat/call with astrologers,
   pricing, booking) — out of scope for a research platform unless the
   product direction changes to include paid consultations.
9. **Dashboard chrome polish** — quick-nav cards row (Today's Pulse/Life
   Insights/Dasha Period/Personality/Strengths/Yogas), profile card with
   photo-initial avatar + age/location, Astrology Tools sidebar (Prashna,
   Panchang, Muhurat, Mundane — these are distinct chart types AstroOS
   doesn't compute at all yet, not just missing UI).

None of Phase 11 is scheduled. Revisit when you're ready — probably after
Phase 10, since most of these are new presentation layers or entirely new
domain modules, not fixes to what already exists.
