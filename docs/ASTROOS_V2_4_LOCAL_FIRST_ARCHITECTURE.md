# AstroOS v2.4.0 — Local-First Research Platform Architecture

**Knowledge-Centric Vedic Research System — Single-User, Single-Machine**

---

## Executive Summary

AstroOS is a **local-first, single-user personal research platform** for Vedic astrology. This architecture transforms it into a **Knowledge-Centric Enterprise Research Platform** where knowledge is the primary asset, using **Vedic Ontology**, **Rule-Based Pattern Matching**, **Classical Literature Integration**, and **Reverse Search Capabilities**.

**Key Design Constraints:**
- **Local-first, single-user** — everything runs on a single machine
- **Native PostgreSQL** is the only database (localhost:5432)
- **No Docker, Kubernetes, Helm, cloud deployment, or enterprise infrastructure**
- **Redis is optional** (JWT denylist only, gracefully disabled if absent)
- **FastAPI + Next.js run locally**
- **Mobile apps connect to localhost:8000**

---

## 1. Updated Processing Flow

```
┌─────────────────────┐
│   User Input/Query  │  ← Web UI, Mobile, or CLI
│  - Chart data      │
│  - Research Q      │
│  - Pattern Search  │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   Vedic Ontology    │  ← Semantic understanding of Vedic entities
│   Resolver          │    (Kundali, Yoga, Dasha, Graha, Rashi)
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Calculation Engine │  ← Swiss Ephemeris + all divisional charts
│   (position data)   │    D1-D60, Shadbala, Ashtakavarga
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│    Rule Engine      │  ← Pattern recognition logic
│  (Yoga Detection)   │    IF-THEN rules, classical constraints
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Knowledge Engine &  │  ← BPHS, Saravali, Phaladeepika
│ Classical References│    - Sanskrit text corpus
│                     │    - Commentary cross-references
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Research & Reverse │  ← Pattern correlation across charts
│   Search Engine     │    - Reverse pattern matching
│                     │    - Statistical significance
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  AI Explain Engine  │  ← Natural language explanations
│  (with citations)   │    - Confidence scores
│                     │    - Literature source linking
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  UI Workspace Canvas│  ← Interactive research environment
│  (Research UI)      │    - Multi-chart comparer
│                     │    - Cross-reference panel
└─────────────────────┘
```

---

## 2. Architecture Overview (Local-Only)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Browser (Next.js)                                                 │
│  React UI, TanStack Query, TailwindCSS                             │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTPS / JSON
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  FastAPI (Python 3.11) — Modular Monolith                          │
│                                                                     │
│  ├── api/                    (HTTP Routers)                        │
│  │   ├── auth/               (JWT + local users)                   │
│  │   ├── charts/             (Chart calculation)                   │
│  │   ├── rules/              (Rule engine)                         │
│  │   ├── knowledge/          (Knowledge graph)                     │
│  │   ├── search/             (Reverse search)                      │
│  │   ├── explain/            (AI explanations)                     │
│  │   └── projects/           (Research projects)                   │
│                                                                     │
│  ├── services/               (Business Logic)                      │
│  │   ├── vedic_ontology/     (Entity resolution)                   │
│  │   ├── calculation_engine/ (Swiss Ephemeris wrapper)             │
│  │   ├── rule_engine/        (Yoga detection, pattern matching)    │
│  │   ├── knowledge_engine/   (Text references, citations)          │
│  │   ├── search_engine/      (Reverse pattern search)              │
│  │   ├── explain_engine/     (NLG with rule tracing)              │
│  │   └── project_manager/    (CRUD, snapshots, comparisons)       │
│                                                                     │
│  ├── core/                   (Shared utilities)                    │
│  │   ├── database/           (PostgreSQL + SQLAlchemy + Alembic)   │
│  │   ├── auth/               (JWT, optional Redis denylist)        │
│  │   └── config/             (Pydantic settings)                   │
│                                                                     │
│  └── worker/                 (In-process background jobs)          │
│      ├── cpu_pool/           (Chart calculations)                  │
│      ├── io_pool/            (File I/O, network)                   │
│      └── ai_pool/            (Knowledge graph queries)             │
└──────────┬──────────────────────────────────────────────────────────┘
           │                          │
           ▼                          ▼
┌──────────────────┐     ┌────────────────────────┐
│  PostgreSQL 16   │     │  Redis 7 (OPTIONAL)    │
│  (localhost)     │     │  (JWT denylist only)   │
│                  │     │  Gracefully disabled    │
│  ┌──────────────┐│     │  if not running         │
│  │ Core tables  ││     └────────────────────────┘
│  │ pgvector ext ││
│  └──────────────┘│
└──────────────────┘
```

---

## 3. Database Schema (PostgreSQL Only)

### 3.1 Core Tables

```sql
-- Users & Auth
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'researcher',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Birth Charts
CREATE TABLE charts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    name VARCHAR(255),
    date_of_birth TIMESTAMPTZ NOT NULL,
    latitude DECIMAL(10, 6) NOT NULL,
    longitude DECIMAL(10, 6) NOT NULL,
    ayanamsa VARCHAR(50) DEFAULT 'lahiri',
    chart_data JSONB NOT NULL,  -- Full chart calculation
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_charts_user_id ON charts(user_id);
CREATE INDEX idx_charts_dob ON charts(date_of_birth);

-- Planetary Positions (for fast queries)
CREATE TABLE chart_positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id UUID REFERENCES charts(id) ON DELETE CASCADE,
    planet_id VARCHAR(10) NOT NULL,  -- sun, moon, mars, etc.
    sign_id VARCHAR(10) NOT NULL,    -- aries, taurus, etc.
    house_number INT NOT NULL,
    degree DECIMAL(8, 4) NOT NULL,
    retrograde BOOLEAN DEFAULT FALSE,
    dignity VARCHAR(50),  -- exalted, own_sign, moolatrikona, etc.
    nakshatra VARCHAR(50),
    pada INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_positions_chart ON chart_positions(chart_id);
CREATE INDEX idx_positions_planet ON chart_positions(planet_id);
CREATE INDEX idx_positions_sign ON chart_positions(sign_id);
CREATE INDEX idx_positions_house ON chart_positions(house_number);

-- Yogas Detected
CREATE TABLE chart_yogas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id UUID REFERENCES charts(id) ON DELETE CASCADE,
    yoga_id VARCHAR(100) NOT NULL,
    yoga_name VARCHAR(255) NOT NULL,
    strength DECIMAL(5, 4),  -- 0.0 to 1.0
    description TEXT,
    sources JSONB,  -- Classical references
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_yogas_chart ON chart_yogas(chart_id);
CREATE INDEX idx_yogas_yoga_id ON chart_yogas(yoga_id);

-- Life Events (for correlation)
CREATE TABLE life_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id UUID REFERENCES charts(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_date TIMESTAMPTZ NOT NULL,
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_events_chart ON life_events(chart_id);
CREATE INDEX idx_events_type ON life_events(event_type);

-- Rule Engine Rules
CREATE TABLE rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id VARCHAR(100) UNIQUE NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    conditions JSONB NOT NULL,
    effects JSONB NOT NULL,
    source VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_rules_type ON rules(rule_type);

-- Classical Text References
CREATE TABLE classical_references (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    text_name VARCHAR(100) NOT NULL,  -- BPHS, Saravali, etc.
    chapter INT,
    verse INT,
    sanskrit TEXT,
    translation TEXT,
    commentary TEXT,
    embedding VECTOR(1536),  -- pgvector for semantic search
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_references_text ON classical_references(text_name);
CREATE INDEX idx_references_embedding ON classical_references USING ivfflat (embedding vector_cosine_ops);

-- Research Projects
CREATE TABLE research_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    chart_ids UUID[],
    queries JSONB,  -- Saved query definitions
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Query Cache (optional performance optimization)
CREATE TABLE query_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_hash VARCHAR(64) UNIQUE NOT NULL,
    query_params JSONB NOT NULL,
    result JSONB NOT NULL,
    result_count INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '1 hour')
);

CREATE INDEX idx_cache_hash ON query_cache(query_hash);
CREATE INDEX idx_cache_expires ON query_cache(expires_at);
```

### 3.2 pgvector Extension

```sql
-- Enable pgvector for semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- Index for fast similarity search on classical references
-- Using IVFFlat index (suitable for < 100k rows)
-- For larger datasets, use HNSW index
CREATE INDEX idx_references_embedding ON classical_references
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

---

## 4. FastAPI Modular Structure

```
services/
├── main.py                         # FastAPI application entry
├── api/
│   ├── __init__.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── router.py               # /auth/login, /auth/register
│   │   ├── endpoints/
│   │   │   ├── login.py
│   │   │   ├── register.py
│   │   │   └── token.py
│   │   └── schemas.py
│   │
│   ├── charts/
│   │   ├── __init__.py
│   │   ├── router.py               # /charts/*
│   │   ├── endpoints/
│   │   │   ├── calculate.py        # POST /charts/calculate
│   │   │   ├── divisional.py       # GET /charts/{id}/d[2-60]
│   │   │   ├── dasha.py            # GET /charts/{id}/dasha
│   │   │   └── shadbala.py         # GET /charts/{id}/shadbala
│   │   └── schemas.py
│   │
│   ├── rules/
│   │   ├── __init__.py
│   │   ├── router.py               # /rules/*
│   │   ├── endpoints/
│   │   │   ├── evaluate.py         # POST /rules/evaluate
│   │   │   ├── yugas.py            # POST /rules/yogas/detect
│   │   │   └── conditions.py       # GET /rules/conditions
│   │   └── schemas.py
│   │
│   ├── knowledge/
│   │   ├── __init__.py
│   │   ├── router.py               # /knowledge/*
│   │   ├── endpoints/
│   │   │   ├── graph.py            # POST /knowledge/graph/query
│   │   │   ├── entities.py         # GET /knowledge/entities/search
│   │   │   └── texts.py            # GET /knowledge/texts/{id}
│   │   └── schemas.py
│   │
│   ├── search/
│   │   ├── __init__.py
│   │   ├── router.py               # /search/*
│   │   ├── endpoints/
│   │   │   ├── pattern.py          # POST /search/pattern
│   │   │   ├── similar.py          # GET /search/similar/{chart_id}
│   │   │   └── correlate.py        # POST /search/correlate
│   │   └── schemas.py
│   │
│   ├── explain/
│   │   ├── __init__.py
│   │   ├── router.py               # /explain/*
│   │   ├── endpoints/
│   │   │   ├── chart.py            # POST /explain/chart
│   │   │   ├── yoga.py             # POST /explain/yoga
│   │   │   └── rule_trace.py       # POST /explain/trace
│   │   └── schemas.py
│   │
│   └── projects/
│       ├── __init__.py
│       ├── router.py               # /projects/*
│       ├── endpoints/
│       │   ├── crud.py             # CRUD operations
│       │   ├── snapshots.py        # /projects/{id}/snapshots
│       │   └── export.py           # /projects/{id}/export
│       └── schemas.py
│
├── services/
│   ├── __init__.py
│   ├── vedic_ontology/
│   │   ├── __init__.py
│   │   ├── resolver.py             # Map query terms to entities
│   │   ├── constants.py            # Rashis, Nakshatras, Yogas
│   │   └── validators.py          # Entity validation
│   │
│   ├── calculation_engine/
│   │   ├── __init__.py
│   │   ├── ephemeris.py            # Swiss Ephemeris wrapper
│   │   ├── ayanamsa.py             # Lahiri, Raman, etc.
│   │   ├── charts.py               # D1-D60 calculators
│   │   ├── dasha.py                # Vimshottari, Yogini, etc.
│   │   ├── shadbala/
│   │   │   ├── calculator.py
│   │   │   ├── sthana_bala.py
│   │   │   └── dig_bala.py
│   │   └── ashtakavarga.py         # Bindu calculation
│   │
│   ├── rule_engine/
│   │   ├── __init__.py
│   │   ├── engine.py               # Main rule evaluator
│   │   ├── yoga_detector.py        # Yoga pattern matching
│   │   ├── condition_parser.py     # Parse rule conditions
│   │   └── rules/
│   │       ├── yoga_rules.yaml     # Yoga definitions
│   │       ├── planetary_rules.yaml
│   │       └── house_rules.yaml
│   │
│   ├── knowledge_engine/
│   │   ├── __init__.py
│   │   ├── graph.py                # PostgreSQL-based knowledge graph
│   │   ├── entity_resolver.py      # Map terms to graph nodes
│   │   ├── pattern_matcher.py      # Subgraph pattern matching
│   │   ├── text_search.py          # Semantic search with pgvector
│   │   └── importers/
│   │       ├── import_bphs.py
│   │       ├── import_saravali.py
│   │       └── import_jataka.py
│   │
│   ├── search_engine/
│   │   ├── __init__.py
│   │   ├── pattern_query.py        # Build search from user input
│   │   ├── pattern_matcher.py      # Match against stored charts
│   │   ├── statistical.py          # Significance testing
│   │   └── ranking.py              # Rank results by relevance
│   │
│   ├── explain_engine/
│   │   ├── __init__.py
│   │   ├── explainer.py            # Main explainer logic
│   │   ├── citation_engine.py      # Source linking
│   │   ├── confidence.py           # Confidence calculation
│   │   └── templates/
│   │       ├── chart_explanation.j2
│   │       └── yoga_explanation.j2
│   │
│   └── project_manager/
│       ├── __init__.py
│       ├── crud.py                 # Project CRUD operations
│       ├── snapshots.py            # Chart snapshots & comparisons
│       └── export.py               # CSV/JSON/PDF export
│
├── core/
│   ├── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py           # SQLAlchemy async engine
│   │   ├── session.py              # Async session factory
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   └── migrations/             # Alembic migrations
│   │       └── versions/
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── jwt.py                  # JWT token handling
│   │   ├── dependencies.py         # FastAPI dependencies
│   │   └── password.py             # bcrypt hashing
│   │
│   └── config/
│       ├── __init__.py
│       └── settings.py             # Pydantic settings
│
├── worker/
│   ├── __init__.py
│   ├── cpu_pool.py                 # CPU-intensive tasks (chart calc)
│   ├── io_pool.py                  # I/O-bound tasks (file read)
│   └── ai_pool.py                  # AI/Knowledge graph queries
│
├── data/
│   ├── classical_texts/
│   │   ├── bphs/
│   │   │   ├── chapters/
│   │   │   └── verses.jsonl
│   │   ├── saravali/
│   │   ├── phaladeepika/
│   │   └── embeddings/
│   │       └── *.npy
│   └── mappings/
│       ├── yoga_to_entities.json
│       └── graha_entities.json
│
├── tests/
│   ├── unit/
│   │   ├── test_calculation_engine.py
│   │   ├── test_rule_engine.py
│   │   ├── test_knowledge_engine.py
│   │   └── test_search_engine.py
│   ├── integration/
│   │   ├── test_api_endpoints.py
│   │   └── test_database.py
│   └── fixtures/
│       ├── charts.json
│       └── rules.json
│
├── requirements.txt
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── script.py.mako
└── README.md
```

---

## 5. Research UI Workspace Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  AstroOS Research Workspace — Dark Obsidian Theme                  │
├─────────────┬─────────────┬─────────────┬─────────────┬───────────┤
│             │             │             │             │           │
│  Nav Panel  │   Query     │  Multi-     │  Classical  │  AI       │
│  - Dashboard│  Builder    │  Chart      │  Text       │  Explain  │
│  - Chart    │  - Vedic    │  Comparer   │  Cross-     │  Panel    │
│    Explorer │    Ontology │  - Side-by- │  Reference  │  - Source│
│  - Workspace│  - Rule     │    side     │  Browser    │    citations│
│  - Research │    Builder  │  - Sync     │  - BPHS     │  - Confidence│
│  - Reverse  │  - Pattern  │    scroll   │  - Saravali │    scores  │
│    Search   │    search   │  - Diff     │  - Jataka   │  - Logic   │
│             │             │    view     │  - Muhurta  │    trace   │
│             │             │             │             │           │
├─────────────┴─────────────┴─────────────┴─────────────┴───────────┤
│  Workspace Canvas (Main Content Area)                              │
│  ┌───────────────────────────────────────────────────────────────┐│
│  │  [Dynamic content based on active tab]                        ││
│  │  - Interactive charts with layered annotations                ││
│  │  - Knowledge graph visualization                              ││
│  │  - Rule engine trace visualization                            ││
│  │  - Comparative analysis matrices                              ││
│  │  - Literature citation panel                                  ││
│  └───────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────┤
│  Status Bar ───────────────────────────────────────────────────────│
│  Research Mode: [Pattern Search] │ Rule Count: 24 │ Cache: 47%   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Dark Obsidian Theme Specification

```css
/* Color Palette */
--astro-bg-primary: #0B0E14;        /* Main background */
--astro-bg-secondary: #121824;      /* Card backgrounds */
--astro-bg-tertiary: #1A2332;       /* Elevated surfaces */
--astro-border: #1F293D;            /* Primary borders */
--astro-border-light: #2D3748;      /* Secondary borders */

--astro-text-primary: #F0F4F8;      /* High-emphasis text */
--astro-text-secondary: #9CA3AF;    /* Medium-emphasis text */
--astro-text-muted: #6B7280;        /* Low-emphasis text */

--astro-accent-cyan: #00D4FF;       /* Primary accent */
--astro-accent-magenta: #FF00FF;   /* Secondary accent */
--astro-accent-amber: #FFB800;     /* Tertiary accent */
--astro-accent-emerald: #10B981;   /* Success/positive */

--astro-glow-cyan: rgba(0, 212, 255, 0.4);
--astro-glow-magenta: rgba(255, 0, 255, 0.4);
--astro-glow-amber: rgba(255, 184, 0, 0.4);
```

**Tailwind Config**:
```javascript
module.exports = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'astro': {
          'bg': { primary: '#0B0E14', secondary: '#121824', tertiary: '#1A2332' },
          'border': { default: '#1F293D', light: '#2D3748' },
          'text': { primary: '#F0F4F8', secondary: '#9CA3AF', muted: '#6B7280' },
          'accent': { cyan: '#00D4FF', magenta: '#FF00FF', amber: '#FFB800', emerald: '#10B981' },
        },
      },
      boxShadow: {
        'astro-glow': '0 0 8px var(--astro-glow-cyan), 0 0 16px var(--astro-glow-cyan)',
        'astro-glow-magenta': '0 0 8px var(--astro-glow-magenta), 0 0 16px var(--astro-glow-magenta)',
        'astro-glow-amber': '0 0 8px var(--astro-glow-amber), 0 0 16px var(--astro-glow-amber)',
      },
    },
  },
}
```

---

## 7. Knowledge Graph (PostgreSQL-Based)

Instead of Neo4j, use PostgreSQL with recursive CTEs for graph queries:

```sql
-- Knowledge Graph Schema (PostgreSQL)
CREATE TABLE knowledge_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id VARCHAR(100) UNIQUE NOT NULL,
    node_type VARCHAR(50) NOT NULL,  -- planet, house, yoga, text, author
    name VARCHAR(255) NOT NULL,
    sanskrit_name VARCHAR(255),
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_nodes_type ON knowledge_nodes(node_type);
CREATE INDEX idx_nodes_id ON knowledge_nodes(node_id);

CREATE TABLE knowledge_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES knowledge_nodes(id),
    target_id UUID REFERENCES knowledge_nodes(id),
    edge_type VARCHAR(50) NOT NULL,  -- aspects, rules, cites, in_house, etc.
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_edges_source ON knowledge_edges(source_id);
CREATE INDEX idx_edges_target ON knowledge_edges(target_id);
CREATE INDEX idx_edges_type ON knowledge_edges(edge_type);
```

### Graph Query Examples

```sql
-- Find all nodes connected to a yoga (within 2 hops)
WITH RECURSIVE graph AS (
    SELECT target_id, edge_type, 1 as depth
    FROM knowledge_edges
    WHERE source_id = (SELECT id FROM knowledge_nodes WHERE node_id = 'yoga_raja')
    UNION ALL
    SELECT e.target_id, e.edge_type, g.depth + 1
    FROM knowledge_edges e
    JOIN graph g ON e.source_id = g.target_id
    WHERE g.depth < 2
)
SELECT n.*, g.edge_type, g.depth
FROM knowledge_nodes n
JOIN graph g ON n.id = g.target_id;

-- Find shortest path between two entities
WITH RECURSIVE path AS (
    SELECT source_id, target_id, ARRAY[source_id] as path, 1 as depth
    FROM knowledge_edges
    WHERE edge_type = 'aspects'
    UNION ALL
    SELECT e.source_id, e.target_id, p.path || e.target_id, p.depth + 1
    FROM knowledge_edges e
    JOIN path p ON e.source_id = p.target_id
    WHERE NOT e.target_id = ANY(p.path) AND p.depth < 5
)
SELECT path FROM path
WHERE source_id = (SELECT id FROM knowledge_nodes WHERE node_id = 'sun')
AND target_id = (SELECT id FROM knowledge_nodes WHERE node_id = 'moon')
ORDER BY depth LIMIT 1;
```

---

## 8. Semantic Search (pgvector)

```sql
-- Semantic search for classical text references
SELECT text_name, chapter, verse, sanskrit, translation, commentary,
       1 - (embedding <=> $1::vector) as similarity
FROM classical_references
WHERE 1 - (embedding <=> $1::vector) > 0.7  -- 70% similarity threshold
ORDER BY embedding <=> $1::vector
LIMIT 10;
```

### Embedding Generation

```python
# services/knowledge_engine/text_search.py
import numpy as np
from sentence_transformers import SentenceTransformer

class TextSearch:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    async def search_references(self, query: str, limit: int = 10):
        # Generate query embedding
        query_embedding = self.model.encode(query)

        # Search using pgvector
        result = await self.db.execute(
            text("""
                SELECT text_name, chapter, verse, sanskrit, translation, commentary,
                       1 - (embedding <=> :embedding) as similarity
                FROM classical_references
                WHERE 1 - (embedding <=> :embedding) > 0.7
                ORDER BY embedding <=> :embedding
                LIMIT :limit
            """),
            {"embedding": query_embedding.tolist(), "limit": limit}
        )
        return result.fetchall()
```

---

## 9. AI Explanation with Citations

```python
# services/explain_engine/explainer.py
from jinja2 import Template
from typing import Dict, Any, List

class AIExplainer:
    def __init__(self, db, knowledge_engine, rule_engine):
        self.db = db
        self.knowledge = knowledge_engine
        self.rules = rule_engine

    async def explain_chart(self, chart_id: str, focus: str = "general"):
        # 1. Get chart data
        chart = await self.db.get_chart(chart_id)

        # 2. Run rule engine to get matched rules
        matched_rules = await self.rules.evaluate(chart)

        # 3. Get classical references for matched rules
        references = []
        for rule in matched_rules:
            refs = await self.knowledge.get_references(rule.source)
            references.extend(refs)

        # 4. Calculate confidence
        confidence = self._calculate_confidence(matched_rules, references)

        # 5. Generate explanation using template
        template = Template(CHART_EXPLANATION_TEMPLATE)
        summary = template.render(
            chart=chart,
            rules=matched_rules,
            references=references[:3]  # Top 3 references
        )

        return {
            "summary": summary,
            "confidence": confidence,
            "rule_trace": [
                {
                    "rule_id": r.rule_id,
                    "name": r.name,
                    "matched": True,
                    "source": r.source,
                    "conditions": r.conditions
                }
                for r in matched_rules
            ],
            "classical_references": [
                {
                    "text": ref.text_name,
                    "chapter": ref.chapter,
                    "verse": ref.verse,
                    "sanskrit": ref.sanskrit,
                    "translation": ref.translation
                }
                for ref in references[:5]
            ],
            "limitations": self._get_limitations(matched_rules)
        }

    def _calculate_confidence(self, rules: List, references: List) -> float:
        if not rules:
            return 0.0
        # Simple confidence based on rule strength and reference count
        avg_strength = sum(r.strength for r in rules) / len(rules)
        ref_factor = min(len(references) / 5, 1.0)  # Max at 5 references
        return round(avg_strength * 0.7 + ref_factor * 0.3, 2)
```

---

## 10. Performance & Caching (Optional Redis)

Redis is **optional** and only used for JWT denylist. If Redis is not available, the system works without it.

```python
# core/auth/jwt.py
from typing import Optional
import redis

class JWTManager:
    def __init__(self, redis_url: Optional[str] = None):
        self.redis = None
        if redis_url:
            try:
                self.redis = redis.from_url(redis_url, decode_responses=True)
                self.redis.ping()
            except:
                print("Redis not available, JWT denylist disabled")

    async def blacklist_token(self, token: str):
        if self.redis:
            await self.redis.setex(f"blacklist:{token}", 86400, "1")

    async def is_blacklisted(self, token: str) -> bool:
        if self.redis:
            return await self.redis.exists(f"blacklist:{token}")
        return False  # Always allow if Redis not available
```

### In-Process Caching

```python
# core/cache.py
from functools import lru_cache
from typing import Any, Optional
import hashlib
import json

class LocalCache:
    """Simple in-memory cache with TTL"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.cache: Dict[str, tuple] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                return value
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: Any):
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache, key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        self.cache[key] = (value, time.time())

    def make_key(self, **kwargs) -> str:
        return hashlib.sha256(json.dumps(kwargs, sort_keys=True).encode()).hexdigest()
```

---

## 11. Configuration (Pydantic)

```python
# core/config/settings.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://localhost:5432/astroos"

    # JWT
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440  # 24 hours

    # Redis (optional)
    REDIS_URL: Optional[str] = None  # Set to redis://localhost:6379 if available

    # Application
    APP_NAME: str = "AstroOS"
    APP_VERSION: str = "2.4.0"
    DEBUG: bool = False

    # Worker Pools
    CPU_POOL_WORKERS: int = 4
    IO_POOL_WORKERS: int = 2
    AI_POOL_WORKERS: int = 2

    # Knowledge Engine
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    SIMILARITY_THRESHOLD: float = 0.7

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

---

## 12. Development Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 16 (localhost)
- Node.js 18+ (for Next.js)
- Swiss Ephemeris library (pyswisseph)

### Installation

```bash
# 1. Clone repository
git clone <repository-url>
cd AstroOS

# 2. Backend setup
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

pip install -r requirements.txt

# 3. Database setup
createdb astroos
alembic upgrade head

# 4. Import classical texts
python -m services.knowledge_engine.importers.import_bphs
python -m services.knowledge_engine.importers.import_saravali

# 5. Start backend
uvicorn services.main:app --reload --host localhost --port 8000

# 6. Frontend setup
cd frontend
npm install
npm run dev
```

### Running

- **Backend API**: http://localhost:8000
- **Frontend UI**: http://localhost:3000
- **Mobile App**: Connects to localhost:8000
- **CLI**: Uses localhost:8000 by default

---

## 13. Summary

This architecture delivers a **knowledge-centric enterprise research platform** while respecting all project constraints:

1. **Local-first, single-user** — everything on one machine
2. **No Docker/Kubernetes** — runs natively
3. **PostgreSQL only** — with pgvector for vector search
4. **Modular monolith** — not 7 microservices
5. **Redis optional** — gracefully disabled if not available
6. **FastAPI + Next.js** — running locally
7. **Knowledge graph** — via PostgreSQL recursive CTEs
8. **Semantic search** — via pgvector embeddings
9. **AI explanations** — with rule tracing and citations
10. **Performance** — in-process caching, optional Redis

The system transforms AstroOS from a chart-centric platform into a **knowledge-centric research platform** where Vedic ontology, rule engines, classical references, and AI explanations work together to provide deep insights into Vedic astrology.

---

*Last Updated: 2026-07-24*
