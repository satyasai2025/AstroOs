# AstroOS Enterprise Research Platform — Frontend Implementation Guide

## Overview

This document outlines the complete frontend structure for the knowledge-centric astrology research platform. The implementation follows a component-based architecture using Next.js 15 with App Router, React, and Tailwind CSS.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Routing & Layout](#routing--layout)
3. [State Management](#state-management)
4. [Theme & Styling](#theme--styling)
5. [Core Components](#core-components)
6. [API Integration](#api-integration)
7. [Performance Considerations](#performance-considerations)
8. [Development Scripts](#development-scripts)

---

## Project Structure

```
frontend/
├── app/
│   ├── (auth)/                    # Authentication routes (grouped)
│   │   ├── login/page.tsx
│   │   └── layout.tsx
│   ├── (research)/               # Research workspace (grouped layout)
│   │   ├── layout.tsx            # Shared research layout (NavPanel, QueryBuilder, Workspace, RightPanels)
│   │   ├── page.tsx              # Dashboard (default)
│   │   ├── chart-explorer/page.tsx
│   │   ├── multi-comparer/page.tsx
│   │   ├── reverse-search/page.tsx
│   │   ├── knowledge-graph/page.tsx
│   │   ├── classical-texts/page.tsx
│   │   └── projects/page.tsx
│   ├── api/                      # Next.js API routes (if not using separate services)
│   │   └── v1/
│   │       ├── research/execute/route.ts
│   │       ├── search/pattern/route.ts
│   │       ├── explain/chart/route.ts
│   │       └── graph/query/route.ts
│   ├── layout.tsx                # Root layout (includes theme provider)
│   ├── page.tsx                  # Homepage / login redirect
│   └── globals.css               # Global styles + Tailwind directives
├── components/
│   ├── layout/
│   │   ├── NavPanel.tsx          # Left navigation bar (6 icons + tooltips)
│   │   ├── WorkspaceCanvas.tsx   # Main content area (swappable tabs)
│   │   ├── RightPanels.tsx       # Right sidebar (multi-chart, text, AI panels)
│   │   └── StatusBar.tsx         # Bottom status bar (cache, connectivity)
│   ├── pages/
│   │   ├── ResearchDashboardPage.tsx  # Landing page with metrics
│   │   ├── ChartExplorerPage.tsx      # Kundali viewer (D1 wheel, positions)
│   │   ├── MultiComparerPage.tsx      # Side-by-side chart comparison
│   │   ├── ReverseSearchPage.tsx      # Pattern-based search
│   │   ├── KnowledgeGraphPage.tsx     # Graph visualization (Cytoscape)
│   │   ├── ClassicalTextsPage.tsx     # BPHS, Saravali browser
│   │   └── ProjectsPage.tsx           # Research project management
│   ├── research/
│   │   ├── QueryBuilder.tsx      # Top query builder with Vedic ontology
│   │   ├── ChartViewer.tsx       # Reusable D1/D2-D60 chart component
│   │   ├── MultiChartGrid.tsx    # Grid layout for multi-comparer
│   │   ├── RuleTraceViewer.tsx   # Visual rule matching trace
│   │   ├── CitationHighlighter.tsx # Literature citations display
│   │   └── YogaCard.tsx          # Yoga display card
│   ├── shared/
│   │   ├── VedicInput.tsx        # Dropdowns for Rashi, Graha, Nakshatra
│   │   ├── DateTimePicker.tsx    // With ayanamsa selector
│   │   ├── LocationSearch.tsx    // Geocoder + manual lat/lon
│   │   └── ChartThumbnail.tsx    // Mini D1 wheel component
│   └── ui/
│       ├── Card.tsx
│       ├── Button.tsx
│       ├── Tabs.tsx
│       ├── Modal.tsx
│       ├── TreeView.tsx
│       └── chart/
│           ├── NatalChart.tsx   // SVG D1 wheel
│           ├── DivisionalGrid.tsx
│           ├── AspectDiagram.tsx
│           ├── ShadbalaBars.tsx
│           └── AshtakavargaGrid.tsx
├── lib/
│   ├── api/
│   │   ├── charts.ts            # Chart calculation API
│   │   ├── rules.ts             # Rule engine API
│   │   ├── knowledge.ts         # Knowledge graph API
│   │   ├── reverse-search.ts    # Pattern search API
│   │   ├── explain.ts           # AI explanation API
│   │   └── auth.ts              # Authentication helpers
│   ├── hooks/
│   │   ├── useResearchQuery.ts  # Hook for executing research queries
│   │   ├── useMultiChartSync.ts # Sync scroll between charts
│   │   ├── useRuleEngine.ts     # Rule evaluation hook
│   │   ├── useKnowledgeGraph.ts # Graph data fetching
│   │   ├── useAIExplain.ts      # AI explanation with streaming
│   │   └── useAuth.ts           # Authentication state
│   ├── stores/
│   │   ├── researchStore.ts     # Zustand global state
│   │   ├── chartStore.ts        # Chart cache & state
│   │   ├── uiStateStore.ts      # Modal, sidebar states
│   │   └── authStore.ts         # User session
│   ├── utils/
│   │   ├── vedic-constants.ts   // Rashi, Nakshatra, Yoga definitions
│   │   ├── formatters.ts        // Date, coordinate formatting
│   │   ├── pattern-matcher.ts   // Client-side pattern validation
│   │   └── chart-helpers.ts     // Chart transformation utilities
│   └── types/
│       ├── chart.ts
│       ├── rule.ts
│       ├── knowledge.ts
│       ├── research.ts
│       └── api.ts
└── styles/
    ├── globals.css               # Tailwind imports + custom CSS variables
    ├── components.css            # Component-specific styles
    ├── animations.css            # Glow, scanline, decoding effects
    └── obsidian-theme.css        # Dark theme overrides

```

---

## Routing & Layout

### Next.js App Router Structure

```typescript
// app/layout.tsx (Root)
export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-astro-bg-primary text-astro-text-primary">
        <AuthProvider>
          <ThemeProvider>
            {children}
          </ThemeProvider>
        </AuthProvider>
      </body>
    </html>
  )
}

// app/(research)/layout.tsx
// This is the main research workspace layout with:
// - Left: NavPanel (16 columns)
// - Middle: QueryBuilder + WorkspaceCanvas
// - Right: RightPanels (toggleable)
// - Bottom: StatusBar
```

### Protected Research Routes

The `(research)` group is protected by a middleware that checks authentication. If unauthenticated, redirects to `/login`.

---

## State Management (Zustand)

The project uses **Zustand** for global state, with separate stores for different concerns:

### `researchStore.ts` — Primary Research State

```typescript
interface ResearchState {
  // Workspace
  activeTab: TabId
  tabs: Tab[]
  setActiveTab: (tabId: string) => void

  // Query
  query: ResearchQuery
  setQuery: (partial: Partial<ResearchQuery>) => void
  isQuerying: boolean
  executeQuery: (query?: ResearchQuery) => Promise<void>

  // Results
  charts: ChartData[]
  matchingRules: RuleResult[]
  knowledgeGraph: GraphData
  explanation: AIExplanation | null
  cachedStats: CacheStats

  // Multi-chart
  selectedCharts: ChartData[]
  selectCharts: (ids: string[]) => void
  comparisonLayout: ComparisonLayout
  setComparisonLayout: (layout: ComparisonLayout) => void

  // UI state
  rightPanelOpen: boolean
  activeRightPanel: PanelId
}
```

### `chartStore.ts` — Chart Cache

```typescript
interface ChartStore {
  currentChart: ChartData | null
  chartHistory: ChartData[]
  addToHistory: (chart: ChartData) => void
  clearHistory: () => void
}
```

---

## Theme & Styling

The **Dark Obsidian** theme is implemented using:

1. **Tailwind CSS** with custom color palette
2. **CSS variables** for theme colors
3. **Component-specific classes** for borders, glows, text hierarchy

### Tailwind Config

```javascript
// tailwind.config.js
module.exports = {
  darkMode: 'class',
  content: [
    './frontend/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        astro: {
          bg: {
            primary: '#0B0E14',    // Deep black
            secondary: '#121824',  // Dark gray-blue
            tertiary: '#1A2332',   // Elevated surface
            quaternary: '#243447'  // Hover states
          },
          border: {
            default: '#1F293D',    // Dark blue-gray
            light: '#2D3748',      // Lighter border
            glow: '#00D4FF'        // Accent glow color
          },
          text: {
            primary: '#F0F4F8',    // Off-white
            secondary: '#9CA3AF',  // Muted
            muted: '#6B7280'       // Subtitles
          },
          accent: {
            cyan: '#00D4FF',       // Primary (tech blue)
            magenta: '#FF00FF',   // Secondary (purple)
            amber: '#FFB800',     // Tertiary (golden)
            emerald: '#10B981',   // Success (green)
            crimson: '#EF4444',   // Error (red)
          }
        }
      },
      boxShadow: {
        'astro-glow': '0 0 8px rgba(0, 212, 255, 0.4), 0 0 16px rgba(0, 212, 255, 0.4)',
        'astro-glow-magenta': '0 0 8px rgba(255, 0, 255, 0.4), 0 0 16px rgba(255, 0, 255, 0.4)',
        'astro-glow-amber': '0 0 8px rgba(255, 184, 0, 0.4), 0 0 16px rgba(255, 184, 0, 0.4)',
      },
      fontSize: {
        'hud-xs': ['10px', { lineHeight: '14px' }],
        'hud-sm': ['12px', { lineHeight: '16px' }],
        'hud-md': ['14px', { lineHeight: '20px' }],
      }
    },
  },
  plugins: [],
}
```

### CSS Variables (globals.css)

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --astro-bg-primary: #0B0E14;
  --astro-bg-secondary: #121824;
  --astro-bg-tertiary: #1A2332;
  --astro-border: #1F293D;
  --astro-text-primary: #F0F4F8;
  --astro-text-secondary: #9CA3AF;
  --astro-text-muted: #6B7280;
  --astro-accent-cyan: #00D4FF;
  --astro-accent-magenta: #FF00FF;
  --astro-accent-amber: #FFB800;
  --astro-accent-emerald: #10B981;
}

* {
  box-sizing: border-box;
}

body {
  font-family: 'Inter', system-ui, sans-serif;
  background: var(--astro-bg-primary);
  color: var(--astro-text-primary);
}

/* Scrollbar styling */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: var(--astro-bg-secondary);
}
::-webkit-scrollbar-thumb {
  background: var(--astro-border);
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: var(--astro-accent-cyan);
}

/* Decoding text animation */
@keyframes decode {
  0% { content: attr(data-shuffle); opacity: 0.5; }
  100% { content: attr(data-text); opacity: 1; }
}
.decode-text::after {
  animation: decode 0.5s ease-out forwards;
}

/* Scanline effect (optional) */
.scanlines {
  background: linear-gradient(
    to bottom,
    transparent 50%,
    rgba(0, 212, 255, 0.03) 50%
  );
  background-size: 100% 4px;
}
```

---

## Core Components

### Layout Components

#### `NavPanel.tsx`

```tsx
export function NavPanel() {
  const navItems = [
    { id: 'research-dashboard', icon: '📊', label: 'Dashboard' },
    { id: 'chart-explorer', icon: '📈', label: 'Chart' },
    { id: 'multi-comparer', icon: '⚖️', label: 'Compare' },
    { id: 'reverse-search', icon: '🔍', label: 'Reverse' },
    { id: 'knowledge-graph', icon: '🕸️', label: 'Graph' },
    { id: 'classical-texts', icon: '📜', label: 'Texts' },
    { id: 'projects', label: 'Projects', icon: '📁' },
  ]

  return (
    <nav className="flex flex-col items-center py-4 gap-2">
      {navItems.map(item => (
        <NavButton key={item.id} item={item} />
      ))}
    </nav>
  )
}
```

#### `QueryBuilder.tsx`

Rich query construction UI with:
- Vedic Ontology picker (dropdown for entity types)
- Natural language text input
- Advanced query builder panel (sparkles button)
- Active filter chips (removable)
- Execute button with loading state

Uses the `researchStore.executeQuery()` action.

#### `WorkspaceCanvas.tsx`

Swappable content area that renders the active tab's page component. Uses Next.js `<Outlet />` or conditional rendering.

#### `RightPanels.tsx`

Collapsible right sidebar with four panels:
1. **Multi-Chart**: Chart grid with layout selector, sync scroll toggle
2. **Classical Texts**: BPHS/Saravali browser with verse highlighter
3. **AI Explain**: Rule trace, confidence, limitations, citations
4. **Knowledge Graph**: Related entity list (compact view)

Each panel is a separate component, shown conditionally based on `activePanel` state.

---

## Feature Pages

### ResearchDashboardPage.tsx

Landing page showing:
- **Key Metrics**: 4 cards (Charts Analyzed, Yogas Detected, Active Rules, Literature Refs)
- **Quick Actions**: 6 cards (New Analysis, Reverse Search, Compare, Graph, Texts, Quick Example)
- **Recent Analyses**: List of user's recent work
- **Live Sample Sets**: Pre-built research queries (Raja Yoga, Moon Exaltation, etc.)
- **System Status**: Rule engine, graph DB, cache, API health

Uses mock data; replace with real API calls.

### ChartExplorerPage.tsx

Two-column layout:
- Left: Birth details form (DateTimePicker, LocationSearch, Ayanamsa selector)
- Right: D1 wheel + planetary positions table + detected yogas

Click "Generate Chart" → calls `calculateChart()` API → display results → auto-execute yoga detection rule engine.

### MultiComparerPage.tsx

- Top controls: Add Chart, Clear All, Layout (grid/side-by-side/diff), Sync Scroll, Highlight Diffs
- Main area: grid of selected charts (stored in `researchStore.selectedCharts`)
- Bottom: Comparison summary (if >=2 charts)

Charts are added from ChartExplorer or via "Add Chart" button (opens chart picker modal - to be implemented).

### ReverseSearchPage.tsx

Two-column:
- Left: Pattern builder (planet positions, yoga pattern selector, aspect pattern)
- Right: Results table with match percentage, actions (View, Add to Comparer, Export)

Search sends POST to `/api/v1/search/pattern`.

### KnowledgeGraphPage.tsx

- Left: Graph controls (entity types, relationship types to show, refresh)
- Right: Cytoscape.js visualization container (full-size)

Graph data from `/api/v1/graph/query`. Implement zoom, pan, node expansion on click.

### ClassicalTextsPage.tsx

Three-column layout within full page:
- Left: Text selector + chapter list
- Center: Verse content (Sanskrit + translation + commentary)
- Right: Related yogas, chart examples, citation tools

Swipeable chapters, translation dropdown, citation copy button.

---

## API Integration

All API calls go through typed service modules in `lib/api/`:

```typescript
// lib/api/charts.ts
import { ChartData, ChartCalculationRequest } from '@/types/api'

export async function calculateChart(params: ChartCalculationRequest): Promise<ChartData> {
  const res = await fetch('/api/v1/calculate/chart', {
    method: 'POST',
    body: JSON.stringify(params),
  })
  if (!res.ok) throw new Error('Failed to calculate chart')
  return res.json()
}
```

API routes can either:
1. **Proxy to microservices** (recommended for production)
2. **Call directly** from Next.js server actions (simpler for v1 microservices architecture)

---

## Performance Considerations

- **Code Splitting**: Pages lazy-loaded via `next/dynamic` if needed
- **Virtual Scrolling**: For large result tables (1000+ rows), use `react-window` or `tanstack-virtual`
- **Graph Memoization**: Cache graph query results with React Query
- **Image Optimization**: Chart thumbnails use `next/image`
- **Suspense Boundaries**: Each page wrapped in `<Suspense>` with loading skeleton

---

## Development Scripts

```json
{
  "scripts": {
    "dev": "next dev --turbopack",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  }
}
```

---

## Next Steps

1. Implement the missing UI components (chart SVG, table virtualization)
2. Connect to real backend APIs (see `ASTROOS_V2_4_ENTERPRISE_RESEARCH_ARCHITECTURE.md`)
3. Add authentication & RBAC middleware
4. Add unit tests for Zustand stores and API utilities
5. Implement microservice proxy layer

The architecture is now ready for implementation of the backend services (ai-explain-service, knowledge-graph-service, literature-vector-db, calculation-engine, rule-engine, reverse-search-engine, correlation-engine).

**Request the backend diagram and flow code implementation in the next prompt** to complete the system.

---

*Last Updated: 2026-07-24*
