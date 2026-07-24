# AstroOS v2.4.0 — Enterprise Research Platform Architecture
**Knowledge-Centric Vedic Research System with Advanced Pattern Analysis**

---

## Executive Summary

AstroOS is transforming from a chart-centric astrology platform into an **Enterprise Research Platform** where knowledge is the primary asset. The system now centers on **Vedic Ontology**, **Rule-Based Pattern Matching**, **Classical Literature Integration**, and **Reverse Search Capabilities**.

---

## 1. Updated Processing Flow

```
┌─────────────────────┐
│   User Input/Query  │
│  - Chart data      │
│  - Research Q      │
│  - Pattern Search  │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   Vedic Ontology    │  ← Semantic understanding of Vedic entities
│   Resolver          │  (Kundali, Yoga, Dasha, Graha, Rashi)
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Calculation Engine │  ← Swiss Ephemeris + all divisional charts
│   ( position data)  │    D1-D60, Shadbala, Ashtakavarga
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
│                     │    - Knowledge graph visualization
└─────────────────────┘
```

---

## 2. Research UI Workspace Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  AstroOS Research Workspace — Dark Obsidian Theme                  │
├─────────────┬─────────────┬─────────────┬─────────────┬───────────┤
│             │             │             │             │           │
│  Nav Panel  │   Query     │  Multi-     │  Classical  │  AI       │
│  - Chart    │  Builder    │  Chart      │  Text       │  Explain  │
│    Explorer │  - Vedic    │  Comparer   │  Cross-     │  Panel    │
│  - Workspace│    Ontology │  - Side-by- │  Reference  │  - Source│
│  - Research │  - Rule     │    side     │  Browser    │    citations│
│    Projects │    Builder  │  - Sync     │  - BPHS     │  - Confidence│
│  - Reverse  │  - Pattern  │    scroll   │  - Saravali │    scores  │
│    Search   │    search   │  - Diff     │  - Jataka   │  - Logic   │
│             │             │    view     │  - Muhurta  │    trace   │
│             │             │             │             │           │
├─────────────┴─────────────┴─────────────┴─────────────┴───────────┤
│  Workspace Canvas (Main Content Area)                              │
│  ┌───────────────────────────────────────────────────────────────┐│
│  │  [Dynamic content based on active tab]                        ││
│  │  - Interactive charts with layered annotations                ││
│  │  - Knowledge graph (Neo4j) visualization                      ││
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

## 3. Dark Obsidian Theme Specification (Tailwind)

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

--astro-overlay: rgba(11, 14, 20, 0.95); /* Modal backdrop */
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
      borderWidth: {
        'hairline': '1px',
      },
    },
  },
}
```

---

## 4. Architecture Layers

### 4.1 Client Layer (Next.js Research UI)

```
frontend/
├── app/
│   ├── (research)/
│   │   ├── dashboard/
│   │   │   ├── page.tsx              # Research workspace home
│   │   │   └── components/
│   │   │       ├── NavPanel.tsx      # Left navigation
│   │   │       ├── QueryBuilder.tsx  # Query construction UI
│   │   │       ├── MultiChartPanel.tsx
│   │   │       ├── ClassicalTextPanel.tsx
│   │   │       ├── AIExplainPanel.tsx
│   │   │       └── WorkspaceCanvas.tsx
│   │   ├── chart-explorer/
│   │   │   ├── page.tsx
│   │   │   ├── KundaliViewer.tsx
│   │   │   ├── HouseExplorer.tsx
│   │   │   └── PlanetaryAspects.tsx
│   │   ├── multi-comparer/
│   │   │   ├── page.tsx
│   │   │   ├── ChartGrid.tsx
│   │   │   ├── DiffViewer.tsx
│   │   │   └── SyncScroller.tsx
│   │   ├── reverse-search/
│   │   │   ├── page.tsx
│   │   │   ├── PatternQuery.tsx     # "Find charts with Sun in 10th + Mars in 1st"
│   │   │   ├── ResultsTable.tsx
│   │   │   └── statistical-analysis.tsx
│   │   ├── knowledge-graph/
│   │   │   ├── page.tsx
│   │   │   ├── GraphVisualizer.tsx  # Neo4j vis (Cytoscape/D3)
│   │   │   ├── EntitySearch.tsx
│   │   │   └── RelationshipMap.tsx
│   │   ├── classical-texts/
│   │   │   ├── page.tsx
│   │   │   ├── TextBrowser.tsx      # BPHS, Saravali reader
│   │   │   ├── CitationHighlighter.tsx
│   │   │   └── VerseContext.tsx
│   │   └── projects/
│   │       ├── page.tsx
│   │       ├── ProjectDashboard.tsx
│   │       ├── ResearchNotes.tsx
│   │       └── SavedQueries.tsx
│   └── layout.tsx
├── components/
│   ├── ui/                           # Reusable components
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Tabs.tsx
│   │   ├── Modal.tsx
│   │   ├── TreeView.tsx
│   │   └── chart/
│   │       ├── NatalChart.tsx       # D1 wheel
│   │       ├── DivisionalGrid.tsx   # D2-D60 grid view
│   │       ├── AspectDiagram.tsx
│   │       ├── ShadbalaBars.tsx
│   │       └── AshtakavargaGrid.tsx
│   ├── research/
│   │   ├── RuleTraceViewer.tsx      # Visualize which rules fired
│   │   ├── ConfidenceBadge.tsx      # AI confidence display
│   │   ├── CitationChip.tsx
│   │   ├── YogaCard.tsx
│   │   └── PlanetaryEffects.tsx
│   └── shared/
│       ├── VedicInput.tsx           # Rashi/Graha/ Nakshatra pickers
│       ├── DateTimePicker.tsx       // With ayanamsa selector
│       └── LocationSearch.tsx
├── lib/
│   ├── api/
│   │   ├── charts.ts
│   │   ├── rules.ts
│   │   ├── knowledge.ts
│   │   ├── reverse-search.ts
│   │   └── explain.ts
│   ├── hooks/
│   │   ├── useResearchQuery.ts
│   │   ├── useMultiChartSync.ts
│   │   ├── useRuleEngine.ts
│   │   └── useKnowledgeGraph.ts
│   ├── utils/
│   │   ├── vedic-constants.ts       // Rashis, Nakshatras, Yogas
│   │   ├── formatters.ts
│   │   └── pattern-matcher.ts
│   └── stores/
│       ├── researchStore.ts         // Zustand store
│       ├── chartStore.ts
│       └── uiStateStore.ts
├── styles/
│   ├── globals.css                  // Tailwind + custom Obsidian theme
│   ├── components.css               // Component-specific styles
│   └── animations.css               // Glow, scanline, decoding effects
└── types/
    ├── chart.ts
    ├── rule.ts
    ├── knowledge.ts
    └── research.ts
```

### 4.2 Knowledge & AI Layer

```
services/
├── ai-explain-service/
│   ├── app/
│   │   ├── main.py                   # FastAPI app
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── explain.py   # POST /explain/chart
│   │   │   │   │   ├── citations.py
│   │   │   │   │   └── confidence.py
│   │   │   │   └── schemas.py
│   │   │   └── deps.py
│   │   ├── core/
│   │   │   ├── explainer.py         # Main explainer logic
│   │   │   ├── citation_engine.py   # Source linking
│   │   │   ├── confidence_calculator.py
│   │   │   └── prompt_templates/
│   │   │       ├── chart_explanation.j2
│   │   │       ├── yoga_explanation.j2
│   │   │       └── rule_trace.j2
│   │   ├── models/
│   │   │   ├── llm_client.py        # Anthropic + OpenAI clients
│   │   │   ├── embeddings.py        # Text embeddings for retrieval
│   │   │   └── reranker.py
│   │   ├── integrations/
│   │   │   ├── neo4j_client.py      # Knowledge graph queries
│   │   │   ├── vector_store.py      # Chroma/Pinecone for literature
│   │   │   └── postgres_client.py
│   │   └── config.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── knowledge-graph-service/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── graph.py         # /graph/traverse, /graph/paths
│   │   │       ├── entities.py      # /entities/search
│   │   │       └── yoga_patterns.py # /yoga/patterns
│   │   ├── core/
│   │   │   ├── neo4j_queries.py     # Cypher queries
│   │   │   ├── entity_resolver.py   # Map query terms to graph nodes
│   │   │   └── pattern_matcher.py   # Subgraph isomorphism
│   │   ├── models/
│   │   │   ├── graph_schema.py      # Node/Edge definitions
│   │   │   └── dto.py
│   │   └── config.py
│   ├── data/
│   │   ├── importers/
│   │   │   ├── import_bphs.py       # Load BPHS verses
│   │   │   ├── import_saravali.py
│   │   │   └── import_jataka.py
│   │   └── mappings/
│   │       ├── yoga_to_entities.json
│   │       └── graha_entities.json
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
└── literature-vector-db/
    ├── app/
    │   ├── main.py
    │   ├── api/
    │   │   └── v1/
    │   │       ├── search.py         # Semantic search over texts
    │   │       ├── verses.py
    │   │       └── commentary.py
    │   ├── core/
    │   │   ├── embeddings.py         # Generate text embeddings
    │   │   ├── vector_store.py       # Chroma/Weaviate wrapper
    │   │   └── retrieval.py          # Hybrid search (keyword + vector)
    │   ├── data/
    │   │   ├── bphs/
    │   │   │   ├── chapters/
    │   │   │   ├── verses.jsonl
    │   │   │   └── embeddings/
    │   │   ├── saravali/
    │   │   └── translations/
    │   └── config.py
    ├── tests/
    ├── Dockerfile
    └── requirements.txt
```

**Knowledge Graph Schema (Neo4j)**:
```
(:Entity {
  id: string,
  type: 'Planet'|'House'|'Nakshatra'|'Yoga'|'Dasha'|'Text'|'Author',
  name: string,
  sanskrit_name: string,
  metadata: jsonb
})

(:Relationship {
  type: 'aspects'|'rules'|'cites'|'in_house'|'in_sign'|'conjunct'|'yoga_constituent',
  source_id: string,
  target_id: string,
  properties: {
    strength: float,
    condition: string,
    reference: string  // BPHS chapter/verse
  }
})
```

### 4.3 Core Service Layer (FastAPI)

```
services/
├── calculation-engine/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── calculate.py    # /calculate/chart, /calculate/dasha
│   │   │       ├── divisional.py   # /calculate/d[2-60]
│   │   │       └── shadbala.py     # /calculate/shadbala
│   │   ├── core/
│   │   │   ├── swiss_ephemeris.py  # Pyswisseph wrapper
│   │   │   ├── ayanamsa.py         # Lahiri, Raman, etc.
│   │   │   ├── chart_calculator.py
│   │   │   ├── dasha_calculator.py
│   │   │   ├── divisional.py       # D2-D60 calculators
│   │   │   └── shadbala/
│   │   │       ├── calculator.py
│   │   │       ├── sthana_bala.py
│   │   │       └── dig_bala.py
│   │   └── config.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── rule-engine/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── evaluate.py     # POST /rules/evaluate
│   │   │       ├── yugas.py        # /rules/yogas/detect
│   │   │       └── conditions.py   # /rules/conditions
│   │   ├── core/
│   │   │   ├── engine.py           # Main rule evaluator
│   │   │   ├── yoga_detector.py    # Yoga pattern matching
│   │   │   ├── condition_parser.py # Parse rule conditions
│   │   │   └── rule_registry.py    # Registry of all rules
│   │   ├── rules/
│   │   │   ├── yoga_rules.yaml     # Yoga definitions
│   │   │   ├── planetary_rules.yaml
│   │   │   ├── house_rules.yaml
│   │   │   └── dasha_rules.yaml
│   │   └── config.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── reverse-search-engine/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── search.py       # POST /search/pattern
│   │   │       ├── similar.py      # /search/similar/{chart_id}
│   │   │       └── correlate.py    # /search/correlate
│   │   ├── core/
│   │   │   ├── pattern_query.py    # Build search from user input
│   │   │   ├── pattern_matcher.py  # Match against stored charts
│   │   │   ├── statistical_analysis.py # Significance testing
│   │   │   └── ranking.py          # Rank results by relevance
│   │   ├── search/
│   │   │   ├── criteria/
│   │   │   │   ├── planet_position.py
│   │   │   │   ├── yoga_pattern.py
│   │   │   │   ├── aspect_pattern.py
│   │   │   │   └── house_pattern.py
│   │   │   └── strategies/
│   │   │       ├── exact_match.py
│   │   │       ├── fuzzy_match.py   # Allow orbs
│   │   │       └── correlated_match.py
│   │   └── config.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
└── correlation-engine/
    ├── app/
    │   ├── main.py
    │   ├── api/
    │   │   └── v1/
    │   │       ├── events.py        # /events/correlate
    │   │       ├── life-events.py   # /events/match
    │   │       └── patterns.py      # /patterns/discover
    │   ├── core/
    │   │   ├── correlator.py        # Event-pattern correlation
    │   │   ├── significance_test.py # Chi-square, Fisher's exact
    │   │   ├── event_classifier.py  # Categorize life events
    │   │   └── time_window.py       # Event time windows
    │   ├── models/
    │   │   └── event_type.py        # Predefined event categories
    │   └── config.py
    ├── tests/
    ├── Dockerfile
    └── requirements.txt
```

### 4.4 Data Layer

```
data/
├── postgres/
│   ├── schemas/
│   │   ├── users.sql
│   │   ├── charts.sql             # Chart master data
│   │   ├── events.sql             # Life events (user-submitted)
│   │   ├── research_projects.sql
│   │   ├── saved_queries.sql
│   │   └── citations.sql          # Literature references
│   │
│   └── migrations/
│       ├── versions/
│       │   ├── 001_initial.py
│       │   ├── 002_add_charts.py
│       │   └── 003_add_knowledge.py
│
├── neo4j/
│   ├── import/
│   │   ├── entities/
│   │   │   ├── planets.cypher
│   │   │   ├── houses.cypher
│   │   │   ├── nakshatras.cypher
│   │   │   ├── yogas.cypher
│   │   │   ├── texts.cypher
│   │   │   └── authors.cypher
│   │   ├── relationships/
│   │   │   ├── yoga_constituents.cypher
│   │   │   ├── text_citations.cypher
│   │   │   ├── graha_rules.cypher
│   │   │   └── dasha_sequences.cypher
│   │   └── constraints/
│   │       └── uniqueness.cypher
│   └── queries/
│       ├── find_charts_with_yoga.cypher
│       ├── get_entity_relationships.cypher
│       └── traverse_rules.cypher
│
└── vector-store/
    ├── chroma/
    │   ├── collections/
    │   │   ├── bphs_verses/
    │   │   │   ├── embeddings.bin
    │   │   │   ├── metadata.jsonl
    │   │   │   └── documents/
    │   │   ├── saravali/
    │   │   └── commentaries/
    │   └── config.yaml
    ├── pinecone/
    │   └── indexes/
    │       ├── astro-literature
    │       └── rule-descriptions
    └── embeddings/
        ├── bphs_chapter1.npy
        └── ...
```

---

## 5. React Component Structure (Frontend)

### 5.1 Layout Components

```typescript
// layout/AppLayout.tsx
export const AppLayout = () => {
  return (
    <div className="flex h-screen bg-astro-bg-primary text-astro-text-primary">
      <NavPanel />
      <main className="flex-1 flex">
        <QueryBuilder />
        <WorkspaceCanvas />
        <RightPanel />  {/* Multi-chart, Text, AI */}
      </main>
      <StatusBar />
    </div>
  )
}

// layout/NavPanel.tsx
export const NavPanel = () => {
  const items = [
    { id: 'chart-explorer', label: 'Chart Explorer', icon: '📊' },
    { id: 'multi-comparer', label: 'Multi Comparer', icon: '⚖️' },
    { id: 'reverse-search', label: 'Reverse Search', icon: '🔍' },
    { id: 'knowledge-graph', label: 'Knowledge Graph', icon: '🕸️' },
    { id: 'classical-texts', label: 'Classical Texts', icon: '📜' },
    { id: 'projects', label: 'Research Projects', icon: '📁' },
  ]
  // ... render navigation
}

// research/WorkspaceCanvas.tsx
export const WorkspaceCanvas = () => {
  // Swappable content area based on active nav item
  return <Outlet />  // Next.js nested route outlet
}
```

### 5.2 Core Research Components

```typescript
// research/QueryBuilder.tsx
export const QueryBuilder = () => {
  return (
    <Card className="bg-astro-bg-secondary border-hairline border-astro-border">
      <div className="flex flex-col gap-4 p-4">
        <VedicOntologyPicker
          entityTypes={['Yoga', 'PlanetaryPosition', 'Aspect', 'Dasha']}
          onSelect={handleEntitySelect}
        />
        <RuleBuilder
          rules={selectedRules}
          onRulesChange={setSelectedRules}
        />
        <PatternSearchInput
          placeholder="e.g., Find charts with Sun in 10th house AND Moon in 4th"
          onSearch={executeSearch}
        />
      </div>
    </Card>
  )
}

// research/MultiChartPanel.tsx
export const MultiChartPanel = () => {
  return (
    <div className="flex flex-col gap-4">
      <ComparerControls
        layout="grid" | "vertical" | "horizontal"
        syncMode={true}  // Scroll sync
        highlightDifferences={true}
      />
      <div className="flex-1">
        <ChartGrid charts={selectedCharts} />
      </div>
      <DiffViewer leftChart={c1} rightChart={c2} />
    </div>
  )
}

// research/ClassicalTextPanel.tsx
export const ClassicalTextPanel = () => {
  return (
    <div className="flex flex-col h-full">
      <TextSelector
        texts={['BPHS', 'Saravali', 'Phaladeepika']}
        selected={activeText}
        onSelect={setActiveText}
      />
      <div className="flex-1 overflow-y-auto">
        <VerseViewer
          textId={activeText}
          highlightCites={matchedCitations}
          showTranslation={true}
          showCommentary={true}
        />
      </div>
      <CitationPanel
        citations={currentCitations}
        onCitationClick={jumpToVerse}
      />
    </div>
  )
}

// research/AIExplainPanel.tsx
export const AIExplainPanel = () => {
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-3 border-b border-astro-border">
        <h3 className="text-sm font-semibold">AI Explanation</h3>
        <ConfidenceBadge score={confidence} />
      </div>
      <ExplanationViewer
        explanation={explanation}
        sources={sources}
        showLogicTrace={true}
        showConfidence={true}
      />
      <div className="border-t border-astro-border p-3">
        <CitationHighlighter citations={explanation.citations} />
      </div>
    </div>
  )
}
```

### 5.3 Knowledge Graph Visualization

```typescript
// knowledge-graph/GraphVisualizer.tsx
import cytoscape from 'cytoscape'

export const GraphVisualizer = ({ queryResults }: { queryResults: GraphData }) => {
  const containerRef = useRef<HTMLDivElement>(null)
  
  useEffect(() => {
    const cy = cytoscape({
      container: containerRef.current,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#121824',
            'border-color': '#00D4FF',
            'border-width': 1,
            'label': 'data(label)',
            'color': '#F0F4F8',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': '10px',
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 1,
            'line-color': '#2D3748',
            'curve-style': 'bezier',
            'target-arrow-shape': 'triangle',
            'target-arrow-color': '#2D3748',
          }
        },
        {
          selector: '.highlighted',
          style: {
            'border-color': '#FF00FF',
            'border-width': 2,
            'box-shadow': '0 0 10px #FF00FF',
          }
        }
      ],
      layout: {
        name: 'dagre',
        rankDir: 'LR',
        padding: 20,
      }
    })
    
    return () => cy.destroy()
  }, [])

  return <div ref={containerRef} className="w-full h-full" />
}
```

### 5.4 State Management (Zustand)

```typescript
// stores/researchStore.ts
import { create } from 'zustand'

interface ResearchState {
  // Active workspace
  activeTab: 'chart-explorer' | 'multi-comparer' | 'reverse-search' | ...
  
  // Query state
  query: {
    ontology: VedicEntity[]
    rules: Rule[]
    constraints: Constraint[]
  }
  
  // Results
  charts: ChartData[]
  matchingRules: RuleResult[]
  knowledgeGraph: GraphData
  explanation: AIExplanation | null
  
  // UI state
  selectedChartIds: string[]
  comparisonLayout: 'grid' | 'side-by-side'
  syncScroll: boolean
  
  // Actions
  setQuery: (query: Partial<Query>) => void
  setCharts: (charts: ChartData[]) => void
  selectCharts: (ids: string[]) => void
  setActiveTab: (tab: TabId) => void
  executeQuery: () => Promise<void>
}

export const useResearchStore = create<ResearchState>((set) => ({
  activeTab: 'chart-explorer',
  query: { ontology: [], rules: [], constraints: [] },
  charts: [],
  matchingRules: [],
  knowledgeGraph: { nodes: [], edges: [] },
  explanation: null,
  selectedChartIds: [],
  comparisonLayout: 'grid',
  syncScroll: true,
  
  setQuery: (newQuery) => set((state) => ({
    query: { ...state.query, ...newQuery }
  })),
  
  executeQuery: async () => {
    const response = await api.executeResearchQuery(state.query)
    set({ charts: response.charts, matchingRules: response.rules })
  },
}))
```

---

## 6. API Integration Layer

```typescript
// lib/api/research.ts
export const researchApi = {
  // Execute complex research query
  executeQuery: async (query: ResearchQuery): Promise<ResearchResponse> => {
    const res = await fetch('/api/v1/research/execute', {
      method: 'POST',
      body: JSON.stringify(query),
    })
    return res.json()
  },
  
  // Reverse pattern search
  reverseSearch: async (pattern: PatternQuery): Promise<ChartSearchResult[]> => {
    const res = await fetch('/api/v1/search/pattern', {
      method: 'POST',
      body: JSON.stringify(pattern),
    })
    return res.json()
  },
  
  // Get AI explanation
  explain: async (request: ExplainRequest): Promise<AIExplanation> => {
    const res = await fetch('/api/v1/explain/chart', {
      method: 'POST',
      body: JSON.stringify(request),
    })
    return res.json()
  },
  
  // Query knowledge graph
  queryGraph: async (query: GraphQuery):Promise<GraphData> => {
    const res = await fetch('/api/v1/graph/query', {
      method: 'POST',
      body: JSON.stringify(query),
    })
    return res.json()
  },
  
  // Search classical texts
  searchTexts: async (params: TextSearchParams): Promise<TextSearchResult[]> => {
    const res = await fetch('/api/v1/texts/search', {
      method: 'POST',
      body: JSON.stringify(params),
    })
    return res.json()
  },
}
```

---

## 7. Complete File Structure Summary

```
AstroOS/
├── frontend/                      # Next.js Research UI
│   ├── app/(research)/...
│   ├── components/
│   │   ├── ui/
│   │   ├── research/
│   │   └── shared/
│   ├── lib/
│   ├── styles/
│   └── types/
│
├── services/                      # Microservices (FastAPI)
│   ├── ai-explain-service/
│   ├── knowledge-graph-service/
│   ├── literature-vector-db/
│   ├── calculation-engine/
│   ├── rule-engine/
│   ├── reverse-search-engine/
│   └── correlation-engine/
│
├── data/                          # Database schemas & imports
│   ├── postgres/schemas/
│   ├── neo4j/import/
│   └── vector-store/
│
├── shared/                        # Shared code
│   ├── types/                    # Common TypeScript/Python types
│   ├── constants/                # Vedic constants (rashis, nakshatras)
│   ├── protocols/                # API contracts
│   └── utils/
│
├── infrastructure/
│   ├── docker/
│   │   ├── docker-compose.yml
│   │   ├── traefik/
│   │   └── postgres/
│   ├── kubernetes/
│   │   ├── namespaces/
│   │   ├── deployments/
│   │   └── services/
│   └── monitoring/
│       ├── grafana/
│       └── loki/
│
└── docs/
    ├── architecture.md            # This document
    ├── api-specs/
    │   ├── research-api.yaml
    │   ├── knowledge-graph-api.yaml
    │   └── explain-api.yaml
    ├── data-model/
    │   ├── entity-relationships.er.png
    │   └── knowledge-graph-schema.md
    └── research-workflows/
        ├── reverse-search-workflow.md
        ├── multi-chart-comparison.md
        └── classical-reference-integration.md
```

---

## 8. Key Research Features Specification

### 8.1 Reverse Pattern Search

**User Flow**:
1. User builds query: "Find charts where Sun is in 10th house AND Moon in 4th house AND Jupiter aspects Moon"
2. Query sent to `reverse-search-engine`
3. Service translates to SQL + graph queries:
   - PostgreSQL: Filter charts by planetary positions
   - Neo4j: Find charts with specified aspects
4. Results ranked by:
   - Exact match percentage
   - Rule strength scores
   - Statistical significance (compared to population baseline)
5. Results displayed in paginated grid with:
   - Mini chart thumbnails
   - Key highlights (which conditions matched)
   - Confidence indicator
   - Life event correlations (if available)

### 8.2 Multi-Chart Comparison

**Features**:
- Select up to 6 charts for simultaneous comparison
- Side-by-side D1 wheels with color-coded differences
- Tabular view of:
  - Planetary positions (by sign/house)
  - Aspects (which aspects present/absent)
  - Yogas (which yogas present/absent)
  - Shadbala scores (comparative bars)
  - Dasha periods (timeline comparison)
- Difference highlighter: red for significant deviations (>1 sign difference)
- Sync scrolling: scroll one chart, all follow
- Export to PDF/CSV with difference summary

### 8.3 Classical Text Cross-Reference

**Workflow**:
1. User selects a yoga/planet/house combination in chart view
2. System fetches relevant verses from:
   - BPHS (Brihat Parashara Hora Shastra)
   - Saravali
   - Phaladeepika
3. Verses displayed with:
   - Original Sanskrit (if available)
   - Translation
   - Commentary
   - Source citation (chapter:verse)
4. AI Explain panel synthesizes:
   - How the chart example illustrates the classical text
   - Confidence score based on rule adherence
   - Other classical references
   - Exceptions and conditional clauses

### 8.4 AI Explanation with Confidence

**Explanation Structure**:
```json
{
  "summary": "Jupiter in the 9th house indicates strong dharma and fortune...",
  "confidence": 0.87,
  "rule_trace": [
    {
      "rule_id": "yoga_jupiter_9th_dhana",
      "rule_name": "Jupiter in 9th gives wealth",
      "source": "BPHS Chapter 12, Verse 45",
      "matched": true,
      "conditions": {
        "jupiter_in_house": 9,
        "jupiter_sign": "Sagittarius",
        "strength_factor": 1.2
      }
    }
  ],
  "classical_references": [
    {
      "text": "BPHS",
      "chapter": 12,
      "verse": 45,
      "sanskrit": "...",
      "translation": "If Jupiter is in the 9th, the native will be wealthy..."
    }
  ],
  "limitations": [
    "Effect reduced if Jupiter is combust",
    "Affordable if Saturn aspects Jupiter negatively"
  ],
  "alternative_interpretations": [
    "Saravali suggests additional effects when Moon also in kendra"
  ]
}
```

---

## 9. Performance & Scalability Considerations

### 9.1 Caching Strategy
- **Chart calculations**: Redis cache with key = hash(julian_day + lat + lon + ayanamsa) — configurable TTL
- **Knowledge graph queries**: Neo4j query result cache (10 min TTL for pattern searches)
- **AI explanations**: Cache by (chart_hash + explanation_type) — 1 hour TTL
- **Classical text lookups**: In-memory LRU cache for frequently cited verses

### 9.2 Database Optimization
- **PostgreSQL**: Indexes on `chart_id`, `user_id`, `date_of_birth`, `ayanamsa`
- **Neo4j**: Indexes on `:Entity(name)`, `:Entity(id)`, composite indexes for common patterns
- **Vector DB**: HNSW index for fast similarity search

### 9.3 Search Optimization
- **Reverse search**: Pre-compute chart signatures (planetary positions, yogas) for faster matching
- **Batch processing**: Large searches (1000+ charts) run as background jobs with WebSocket progress updates
- **Result pagination**: Server-side pagination with cursor-based navigation

---

## 10. Security & Access Control

- **Authentication**: NextAuth.js with JWT (stored in HttpOnly cookies)
- **Authorization**: RBAC
  - `researcher`: Create projects, save queries, view all charts
  - `reviewer`: All researcher + export data, view all project data
  - `admin`: All + user management, system config
- **Audit Logging**: All research queries logged with:
  - User ID
  - Query parameters
  - Results accessed
  - Timestamp
  - IP address

---

## 11. Monitoring & Observability

- **Metrics** (Prometheus):
  - `research_queries_total`, `research_queries_duration_seconds`
  - `reverse_search_results_count`
  - `ai_explain_confidence_distribution`
  - `knowledge_graph_query_latency`
- **Logs** (Loki structured):
  - Query execution with parameters
  - Rule evaluation traces
  - AI explanation generation steps
- **Tracing** (Jaeger):
  - End-to-end: Query → Rule Engine → AI Explain → Response

---

## Conclusion

This architecture establishes AstroOS as a **Knowledge-Centric Research Platform** where:

1. **Vedic Ontology** provides semantic understanding
2. **Rule Engine** applies classical logic consistently
3. **Knowledge Graph** connects entities across texts
4. **Reverse Search** enables pattern-driven discovery
5. **AI Explain** delivers source-backed explanations

The Dark Obsidian theme maintains visual cohesion while the React component structure supports complex research workflows.

---

**Next Steps**: Request backend diagram and flow code implementation in the next prompt.
