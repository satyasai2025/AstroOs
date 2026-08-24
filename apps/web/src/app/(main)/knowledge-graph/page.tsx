"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { AREA_LABELS, type LifeArea } from "@/lib/predictions/types";
import { useWorkflowStore } from "@/lib/store";
import { useMyCharts } from "@/lib/charts";
import { useAnalyzeWorkflow } from "@/lib/workflow";
import type { WorkflowAnalysisRequest, WorkflowAnalysisResponse } from "@/lib/types";
import { HouseDependencyNetwork } from "@/components/charts/HouseDependencyNetwork";
import PlanetRelationshipGraph2 from "@/components/charts/PlanetRelationshipGraph2";
import { TransitTimeline } from "@/components/charts/TransitTimeline";
import { DashaTimeline } from "@/components/charts/DashaTimeline";
import { PredictionChainExplorer } from "@/components/charts/PredictionChainExplorer";
import YogasPanel from "@/components/charts/YogasPanel";
import { GraphExplorer } from "@/components/charts/knowledge-graph/GraphExplorer";
import { PredictionChainGraph } from "@/components/charts/predictions/PredictionChainGraph";
import { PredictionRelatedRules } from "@/components/charts/predictions/PredictionRelatedRules";
import { PredictionDataSources } from "@/components/charts/predictions/PredictionDataSources";
import { buildPredictionGraph } from "@/lib/predictions/chainEngine";
import { useAvastha } from "@/lib/avastha";
import { useShadbalaAll } from "@/lib/shadbala";

const AREA_KEYS = Object.keys(AREA_LABELS) as LifeArea[];

type CategoryId =
  | "all"
  | "prediction-engine"
  | "entity-relationships"
  | "strength-analysis"
  | "time-based"
  | "research"
  | "classical-knowledge";

const CATEGORY_TABS: { id: CategoryId; label: string }[] = [
  { id: "all", label: "All Visualizations" },
  { id: "prediction-engine", label: "Prediction Engine" },
  { id: "entity-relationships", label: "Entity Relationships" },
  { id: "strength-analysis", label: "Strength Analysis" },
  { id: "time-based", label: "Time Based" },
  { id: "research", label: "Research" },
  { id: "classical-knowledge", label: "Classical Knowledge" },
];

type SortMode = "default" | "az" | "za";

interface GraphCard {
  id: string;
  number: number;
  title: string;
  description: string;
  categories: CategoryId[];
  /** Real route this card links to when it has no inline renderer (e.g.
   * Classical Rule Graph, which has no structured rule-graph component
   * yet — kept honest as an external link rather than fabricated inline
   * content). Renderable cards ignore this and open in place. */
  href: ((area: LifeArea) => string) | null;
  legend: string[];
  /** Node/edge dot count for the mini thumbnail — purely illustrative
   * (a small fixed diagram per graph shape), not a live measurement. */
  thumbNodes: number;
}

const GRAPH_CARDS: GraphCard[] = [
  {
    id: "house-dependency",
    number: 1,
    title: "House Dependency Graph",
    description: "House → Lord → Sign → Shadbala → Prediction chain for the selected life area.",
    categories: ["all", "prediction-engine", "entity-relationships", "strength-analysis"],
    href: () => "/charts?view=houses",
    legend: ["House", "Planet", "Sign", "Strength", "Result"],
    thumbNodes: 5,
  },
  {
    id: "yoga-relationship",
    number: 2,
    title: "Yoga Relationship Graph",
    description: "Planets and houses that combine to form a yoga, and its contribution to the score.",
    categories: ["all", "prediction-engine", "entity-relationships"],
    href: () => "/charts?view=yogas",
    legend: ["Planet", "House", "Relationship", "Aspect"],
    thumbNodes: 4,
  },
  {
    id: "prediction-dependency",
    number: 3,
    title: "Prediction Dependency Graph",
    description: "Visual breakdown of how House, Yogas, Dasha and Transit combine into the final score.",
    categories: ["all", "prediction-engine"],
    href: (area) => `/predictions?kpi=${area}`,
    legend: ["Primary Factor", "Sub Factor", "Contribution"],
    thumbNodes: 5,
  },
  {
    id: "planet-network",
    number: 4,
    title: "Planet Relationship Network",
    description: "Conjunctions, aspects, exchanges and dispositorships between planets, weighted by strength.",
    categories: ["all", "entity-relationships", "strength-analysis"],
    href: () => "/charts?view=relationships-v2",
    legend: ["Conjunction", "Aspect", "Exchange", "Dispositor"],
    thumbNodes: 6,
  },
  {
    id: "house-energy-flow",
    number: 5,
    title: "House Energy Flow",
    description: "Lordship and Argala flow between houses — the same real house-dependency network, filtered to flow-style edges.",
    categories: ["all", "entity-relationships"],
    href: () => "/charts?view=houses",
    legend: ["Flow", "Lordship", "Argala"],
    thumbNodes: 4,
  },
  {
    id: "dasha-influence",
    number: 6,
    title: "Dasha Influence Graph",
    description: "Vimshottari Mahadasha timeline for this chart, with the currently running period highlighted.",
    categories: ["all", "time-based", "prediction-engine"],
    href: () => "/charts?view=dasha",
    legend: ["Mahadasha", "Timeline", "Current Period"],
    thumbNodes: 4,
  },
  {
    id: "transit-impact",
    number: 7,
    title: "Transit Impact Map",
    description: "Current transit → sign → house → life area, with direction of impact.",
    categories: ["all", "time-based"],
    href: () => "/charts/transit",
    legend: ["Transit", "Sign", "House", "Impact"],
    thumbNodes: 4,
  },
  {
    id: "prediction-tree",
    number: 8,
    title: "Prediction Tree",
    description: "Pick a life area and see the real computed chain from source data through to the final prediction.",
    categories: ["all", "prediction-engine"],
    href: (area) => `/predictions?kpi=${area}`,
    legend: ["Main Factor", "Sub Factor", "Result"],
    thumbNodes: 7,
  },
  {
    id: "knowledge-explorer",
    number: 9,
    title: "Knowledge Graph Explorer",
    description: "Interactive graph of planets, houses, yogas and dasha for the loaded chart — click any node for its real relationships.",
    categories: ["all", "research", "entity-relationships"],
    href: () => "/knowledge-graph/explorer",
    legend: ["Entity", "Relationship", "Detail"],
    thumbNodes: 6,
  },
  {
    id: "classical-rule-graph",
    number: 10,
    title: "Classical Rule Graph",
    description: "Chapter → Rule → Application trail from BPHS and other classical texts.",
    categories: ["all", "research", "classical-knowledge"],
    href: () => "/knowledge/bphs",
    legend: ["Text", "Chapter", "Rule", "Application"],
    thumbNodes: 4,
  },
];

const THUMB_LAYOUTS: Record<number, { x: number; y: number }[]> = {
  4: [{ x: 20, y: 14 }, { x: 44, y: 14 }, { x: 20, y: 36 }, { x: 44, y: 36 }],
  5: [{ x: 32, y: 8 }, { x: 14, y: 26 }, { x: 50, y: 26 }, { x: 22, y: 44 }, { x: 42, y: 44 }],
  6: [{ x: 32, y: 6 }, { x: 12, y: 20 }, { x: 52, y: 20 }, { x: 12, y: 40 }, { x: 52, y: 40 }, { x: 32, y: 46 }],
  7: [{ x: 32, y: 6 }, { x: 16, y: 18 }, { x: 48, y: 18 }, { x: 8, y: 32 }, { x: 24, y: 32 }, { x: 40, y: 32 }, { x: 56, y: 32 }],
};

function CardThumb({ n, color }: { n: number; color: string }) {
  const nodes = THUMB_LAYOUTS[n] ?? THUMB_LAYOUTS[4];
  return (
    <svg viewBox="0 0 64 52" width="100%" height="56" aria-hidden="true">
      {nodes.slice(1).map((node, i) => (
        <line key={i} x1={nodes[0].x} y1={nodes[0].y} x2={node.x} y2={node.y} stroke={color} strokeWidth={1} opacity={0.35} />
      ))}
      {nodes.map((node, i) => (
        <circle key={i} cx={node.x} cy={node.y} r={i === 0 ? 4 : 3} fill={color} opacity={i === 0 ? 0.9 : 0.6} />
      ))}
    </svg>
  );
}

/** Renders the "Graph" tab content for cards that don't need the
 * prediction-graph machinery (those two — Prediction Dependency Graph and
 * Prediction Tree — are handled separately in VisualizationViewer so they
 * can also power real Rules/Sources tabs from the same computed graph). */
function renderGraphTab(cardId: string, result: WorkflowAnalysisResponse): React.ReactNode {
  const { chart, dasha } = result;
  switch (cardId) {
    case "house-dependency":
      return <HouseDependencyNetwork houses={chart.houses} planetStrengths={chart.planet_strengths} planets={chart.planets} />;
    case "yoga-relationship":
      return <YogasPanel result={result} />;
    case "planet-network":
      return (
        <PlanetRelationshipGraph2
          planets={chart.planets}
          aspects={chart.aspects}
          yogas={result.yogas.results}
          mahadashas={dasha.mahadashas}
          result={result}
        />
      );
    case "house-energy-flow":
      return (
        <HouseDependencyNetwork
          houses={chart.houses}
          planetStrengths={chart.planet_strengths}
          planets={chart.planets}
          activeKinds={new Set(["lordship", "argala"])}
        />
      );
    case "dasha-influence":
      return <DashaTimeline dasha={dasha} />;
    case "transit-impact":
      return <TransitTimeline dasha={dasha} transits={result.transits} />;
    case "knowledge-explorer":
      return <GraphExplorer result={result} />;
    default:
      return null;
  }
}

const INLINE_CARD_IDS = new Set([
  "house-dependency",
  "yoga-relationship",
  "prediction-dependency",
  "planet-network",
  "house-energy-flow",
  "dasha-influence",
  "transit-impact",
  "prediction-tree",
  "knowledge-explorer",
]);

/** Present-yoga source texts (real classical citations, deduped) — backs
 * the Yoga Relationship Graph's Sources tab. */
function yogaSources(result: WorkflowAnalysisResponse) {
  const seen = new Map<string, string>();
  for (const y of result.yogas.results) {
    if (y.is_present) seen.set(y.name, y.source_text);
  }
  return Array.from(seen.entries());
}

type TabId = "graph" | "explanation" | "rules" | "sources";
const TAB_LABEL: Record<TabId, string> = { graph: "Graph", explanation: "Explanation", rules: "Rules", sources: "Sources" };

function tabsForCard(cardId: string): TabId[] {
  if (cardId === "prediction-dependency" || cardId === "prediction-tree") return ["graph", "explanation", "rules", "sources"];
  if (cardId === "yoga-relationship") return ["graph", "explanation", "sources"];
  return ["graph", "explanation"];
}

function VisualizationViewer({
  card,
  area,
  result,
  allCards,
  onBack,
  onOpenCard,
}: {
  card: GraphCard;
  area: LifeArea;
  result: WorkflowAnalysisResponse;
  allCards: GraphCard[];
  onBack: () => void;
  onOpenCard: (id: string) => void;
}) {
  const [activeTab, setActiveTab] = useState<TabId>("graph");
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const tabs = useMemo(() => tabsForCard(card.id), [card.id]);

  useEffect(() => {
    setActiveTab("graph");
    setSelectedNodeId(null);
  }, [card.id]);

  const isPredictionCard = card.id === "prediction-dependency" || card.id === "prediction-tree";
  const request = useWorkflowStore((s) => s.request);
  const avasthaQuery = useAvastha(request);
  const shadbalaAllQuery = useShadbalaAll(request);
  const predictionGraph = useMemo(
    () =>
      isPredictionCard
        ? buildPredictionGraph(area, result, { avastha: avasthaQuery.data, shadbalaAll: shadbalaAllQuery.data })
        : null,
    [isPredictionCard, area, result, avasthaQuery.data, shadbalaAllQuery.data],
  );

  useEffect(() => {
    if (predictionGraph) setSelectedNodeId(predictionGraph.nodes[0]?.id ?? null);
  }, [predictionGraph]);

  const related = allCards.filter((c) => c.id !== card.id && c.categories.some((cat) => card.categories.includes(cat))).slice(0, 4);

  let tabContent: React.ReactNode = null;
  if (activeTab === "graph") {
    tabContent = isPredictionCard && predictionGraph ? (
      <PredictionChainGraph graph={predictionGraph} selectedId={selectedNodeId} onSelect={setSelectedNodeId} />
    ) : (
      renderGraphTab(card.id, result)
    );
  } else if (activeTab === "explanation") {
    tabContent = (
      <div className="glass-card p-5 text-sm" style={{ color: "var(--text-secondary)" }}>
        {card.description}
        {isPredictionCard && predictionGraph && (
          <p className="mt-3" style={{ color: "var(--text-primary)" }}>
            {predictionGraph.finalLabel}: <strong>{predictionGraph.finalScore}/100</strong> — confidence {predictionGraph.confidence.level.toLowerCase()}.
          </p>
        )}
      </div>
    );
  } else if (activeTab === "rules" && predictionGraph) {
    tabContent = <PredictionRelatedRules rules={predictionGraph.relatedRules} />;
  } else if (activeTab === "sources") {
    if (isPredictionCard && predictionGraph) {
      tabContent = <PredictionDataSources sources={predictionGraph.dataSources} />;
    } else if (card.id === "yoga-relationship") {
      const sources = yogaSources(result);
      tabContent = (
        <div className="glass-card flex flex-col gap-2 p-5">
          <h3 className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>
            Classical Sources (present yogas)
          </h3>
          {sources.length === 0 ? (
            <p className="text-sm" style={{ color: "var(--text-muted)" }}>No yogas are present in this chart.</p>
          ) : (
            <ul className="space-y-2">
              {sources.map(([name, source]) => (
                <li key={name} className="text-sm">
                  <span style={{ color: "var(--text-primary)" }}>{name}</span>
                  <span style={{ color: "var(--text-muted)" }}> — {source}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      );
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-1.5 text-xs" style={{ color: "var(--text-muted)" }}>
        <button type="button" onClick={onBack} className="hover:underline" style={{ color: "var(--text-muted)" }}>
          Knowledge Graph
        </button>
        <span>›</span>
        <button type="button" onClick={onBack} className="hover:underline" style={{ color: "var(--text-muted)" }}>
          Visualizations
        </button>
        <span>›</span>
        <span style={{ color: "var(--text-secondary)" }}>{card.title}</span>
      </div>

      <div className="flex items-center gap-3">
        <button type="button" onClick={onBack} className="flex items-center gap-1.5 text-sm font-medium" style={{ color: "var(--accent)" }}>
          ← Back
        </button>
        <h2 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
          {card.title}
        </h2>
      </div>

      <div className="flex gap-1 border-b" style={{ borderColor: "var(--border-primary)" }}>
        {tabs.map((t) => (
          <button
            key={t}
            onClick={() => setActiveTab(t)}
            className="px-4 py-2 text-sm font-medium transition"
            style={{
              color: activeTab === t ? "var(--accent)" : "var(--text-secondary)",
              borderBottom: activeTab === t ? "2px solid var(--accent)" : "2px solid transparent",
            }}
          >
            {TAB_LABEL[t]}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_260px]">
        <div className="min-w-0">{tabContent}</div>
        <div className="glass-card flex h-fit flex-col gap-3 p-4">
          <h4 className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Details</h4>
          <dl className="space-y-1.5 text-xs">
            {request?.subject_name && (
              <div className="flex justify-between gap-2">
                <dt style={{ color: "var(--text-muted)" }}>Native</dt>
                <dd style={{ color: "var(--text-primary)" }}>{request.subject_name}</dd>
              </div>
            )}
            {request?.ayanamsa && (
              <div className="flex justify-between gap-2">
                <dt style={{ color: "var(--text-muted)" }}>Ayanamsa</dt>
                <dd style={{ color: "var(--text-primary)" }}>{request.ayanamsa}</dd>
              </div>
            )}
            <div className="flex justify-between gap-2">
              <dt style={{ color: "var(--text-muted)" }}>Life Area</dt>
              <dd style={{ color: "var(--text-primary)" }}>{AREA_LABELS[area]}</dd>
            </div>
          </dl>
          <div className="text-xs" style={{ color: "var(--text-muted)" }}>
            Shows: {card.legend.join(", ")}
          </div>
        </div>
      </div>

      {related.length > 0 && (
        <div className="flex flex-col gap-2">
          <h4 className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Related Visualizations</h4>
          <div className="flex flex-wrap gap-2">
            {related.map((r) => (
              <button
                key={r.id}
                type="button"
                onClick={() => (INLINE_CARD_IDS.has(r.id) ? onOpenCard(r.id) : undefined)}
                className="rounded-lg px-3 py-2 text-left text-xs"
                style={{ border: "1px solid var(--border-primary)", color: "var(--text-primary)" }}
                disabled={!INLINE_CARD_IDS.has(r.id)}
              >
                {r.number}. {r.title}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function KnowledgeGraphPage() {
  const [category, setCategory] = useState<CategoryId>("all");
  const [area, setArea] = useState<LifeArea>("career");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<SortMode>("default");
  const [view, setView] = useState<"grid" | "list">("grid");
  const [openCardId, setOpenCardId] = useState<string | null>(null);

  const result = useWorkflowStore((s) => s.result);
  const setResult = useWorkflowStore((s) => s.setResult);
  const { data: chartsData, isLoading: chartsLoading } = useMyCharts();
  const analyze = useAnalyzeWorkflow();
  const [autoRecomputeStarted, setAutoRecomputeStarted] = useState(false);

  const targetSummary = useMemo(() => {
    if (!chartsData) return null;
    return chartsData.charts.find((c) => c.is_default) ?? chartsData.charts[0] ?? null;
  }, [chartsData]);

  useEffect(() => {
    if (result || autoRecomputeStarted || !targetSummary) return;
    setAutoRecomputeStarted(true);
    const request: WorkflowAnalysisRequest = {
      birth_datetime_utc: targetSummary.birth_datetime_utc,
      latitude: targetSummary.birth_latitude,
      longitude: targetSummary.birth_longitude,
      ayanamsa: targetSummary.ayanamsa as WorkflowAnalysisRequest["ayanamsa"],
      house_system: targetSummary.house_system as WorkflowAnalysisRequest["house_system"],
      dasha_system: "vimshottari",
      include_vargas: true,
      subject_name: targetSummary.subject_name,
      place_name: targetSummary.place_name,
      persist: false,
      chart_id: targetSummary.id,
    };
    analyze.mutate(request, { onSuccess: (data) => setResult(data, request) });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [result, autoRecomputeStarted, targetSummary]);

  const cards = useMemo(() => {
    const q = search.trim().toLowerCase();
    let filtered = GRAPH_CARDS.filter((c) => c.categories.includes(category));
    if (q) {
      filtered = filtered.filter(
        (c) => c.title.toLowerCase().includes(q) || c.description.toLowerCase().includes(q),
      );
    }
    const sorted = [...filtered];
    if (sort === "az") sorted.sort((a, b) => a.title.localeCompare(b.title));
    else if (sort === "za") sorted.sort((a, b) => b.title.localeCompare(a.title));
    return sorted;
  }, [category, search, sort]);

  const relationshipTypeCount = useMemo(() => new Set(GRAPH_CARDS.flatMap((c) => c.legend)).size, []);
  const openCard = GRAPH_CARDS.find((c) => c.id === openCardId) ?? null;

  return (
    <>
      <div className="flex flex-col gap-5">
        {openCard ? (
          !result ? (
            <div className="glass-card flex flex-col items-center gap-3 p-8 text-center">
              {chartsLoading || analyze.isPending ? (
                <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Loading chart data…</p>
              ) : (
                <>
                  <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>No Chart Data Available</p>
                  <p className="text-xs" style={{ color: "var(--text-secondary)" }}>Run an analysis on the Dashboard first to populate chart data.</p>
                  <Link href="/dashboard" className="btn-primary">Go to Dashboard</Link>
                </>
              )}
            </div>
          ) : (
            <VisualizationViewer
              card={openCard}
              area={area}
              result={result}
              allCards={GRAPH_CARDS}
              onBack={() => setOpenCardId(null)}
              onOpenCard={setOpenCardId}
            />
          )
        ) : (
          <>
            <div className="flex items-center gap-1.5 text-xs" style={{ color: "var(--text-muted)" }}>
              <span>Knowledge Graph</span>
              <span>›</span>
              <span style={{ color: "var(--text-secondary)" }}>Visualizations</span>
            </div>

            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h1 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
                  Knowledge Graph Visualizations
                </h1>
                <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
                  Explore interactive visual representations of astrological relationships, prediction logic and classical knowledge.
                </p>
              </div>
              <select
                value={area}
                onChange={(e) => setArea(e.target.value as LifeArea)}
                className="field-input"
                style={{ width: "auto" }}
                aria-label="Filter by life area"
              >
                {AREA_KEYS.map((key) => (
                  <option key={key} value={key}>
                    {AREA_LABELS[key]}
                  </option>
                ))}
              </select>
            </div>

            {/* Stat tiles — every number here is real and countable from this
                page's own data (card count, distinct tag count, life-area
                count), not a fabricated platform metric. */}
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <StatTile label="Visualizations Available" value={GRAPH_CARDS.length} sub="Interactive Graphs" />
              <StatTile label="Graph Categories" value={CATEGORY_TABS.length - 1} sub="Ways to Browse" />
              <StatTile label="Relationship Tags" value={relationshipTypeCount} sub="Types of Connections Shown" />
              <StatTile label="Life Areas" value={AREA_KEYS.length} sub="Prediction Contexts" />
            </div>

            <div className="flex gap-1 overflow-x-auto border-b" style={{ borderColor: "var(--border-primary)" }}>
              {CATEGORY_TABS.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setCategory(tab.id)}
                  className="whitespace-nowrap px-4 py-2 text-sm font-medium transition"
                  style={{
                    color: category === tab.id ? "var(--accent)" : "var(--text-secondary)",
                    borderBottom: category === tab.id ? "2px solid var(--accent)" : "2px solid transparent",
                  }}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search visualizations…"
                className="field-input"
                style={{ maxWidth: 280 }}
                aria-label="Search visualizations"
              />
              <select
                value={sort}
                onChange={(e) => setSort(e.target.value as SortMode)}
                className="field-input"
                style={{ width: "auto" }}
                aria-label="Sort visualizations"
              >
                <option value="default">Sort: Default</option>
                <option value="az">Sort: A → Z</option>
                <option value="za">Sort: Z → A</option>
              </select>
              <div className="ml-auto flex gap-1 rounded-lg p-0.5" style={{ border: "1px solid var(--border-primary)" }}>
                <button
                  type="button"
                  onClick={() => setView("grid")}
                  className="rounded-md px-2 py-1 text-xs"
                  style={{ backgroundColor: view === "grid" ? "var(--border-primary)" : "transparent", color: view === "grid" ? "var(--accent)" : "var(--text-muted)" }}
                  aria-pressed={view === "grid"}
                >
                  Grid
                </button>
                <button
                  type="button"
                  onClick={() => setView("list")}
                  className="rounded-md px-2 py-1 text-xs"
                  style={{ backgroundColor: view === "list" ? "var(--border-primary)" : "transparent", color: view === "list" ? "var(--accent)" : "var(--text-muted)" }}
                  aria-pressed={view === "list"}
                >
                  List
                </button>
              </div>
            </div>

            <div className={view === "grid" ? "grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3" : "flex flex-col gap-3"}>
              {cards.map((card) => {
                const inline = INLINE_CARD_IDS.has(card.id);
                const href = !inline ? card.href?.(area) ?? null : null;
                const isActive = inline || !!href;
                const thumbColor = isActive ? "var(--accent)" : "var(--text-muted)";
                const body =
                  view === "grid" ? (
                    <div className="glass-card flex h-full flex-col gap-3 p-5 transition" style={{ opacity: isActive ? 1 : 0.55 }}>
                      <CardThumb n={card.thumbNodes} color={thumbColor} />
                      <div className="flex items-start justify-between gap-2">
                        <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                          {card.number}. {card.title}
                        </h3>
                        {!isActive && (
                          <span className="rounded-full px-1.5 py-0.5 text-[9px] uppercase tracking-wide" style={{ border: "1px solid var(--border-primary)", color: "var(--text-muted)" }}>
                            Soon
                          </span>
                        )}
                      </div>
                      <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                        {card.description}
                      </p>
                      <div className="mt-auto flex flex-wrap gap-2 pt-2">
                        {card.legend.map((l) => (
                          <span key={l} className="rounded-full px-2 py-0.5 text-[10px]" style={{ border: "1px solid var(--border-primary)", color: "var(--text-muted)" }}>
                            {l}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="glass-card flex items-center gap-4 p-4 transition" style={{ opacity: isActive ? 1 : 0.55 }}>
                      <div style={{ width: 64, flexShrink: 0 }}>
                        <CardThumb n={card.thumbNodes} color={thumbColor} />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                            {card.number}. {card.title}
                          </h3>
                          {!isActive && (
                            <span className="rounded-full px-1.5 py-0.5 text-[9px] uppercase tracking-wide" style={{ border: "1px solid var(--border-primary)", color: "var(--text-muted)" }}>
                              Soon
                            </span>
                          )}
                        </div>
                        <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                          {card.description}
                        </p>
                      </div>
                      <div className="hidden flex-wrap gap-2 sm:flex" style={{ maxWidth: 220 }}>
                        {card.legend.map((l) => (
                          <span key={l} className="rounded-full px-2 py-0.5 text-[10px]" style={{ border: "1px solid var(--border-primary)", color: "var(--text-muted)" }}>
                            {l}
                          </span>
                        ))}
                      </div>
                    </div>
                  );

                if (inline) {
                  return (
                    <button key={card.id} type="button" onClick={() => setOpenCardId(card.id)} className="block text-left">
                      {body}
                    </button>
                  );
                }
                return href ? (
                  <Link key={card.id} href={href} className="block">
                    {body}
                  </Link>
                ) : (
                  <div key={card.id} title="Not built yet">
                    {body}
                  </div>
                );
              })}
            </div>

            <p className="text-center text-xs" style={{ color: "var(--text-muted)" }}>
              Showing {cards.length} of {GRAPH_CARDS.length} visualizations
            </p>
          </>
        )}
      </div>
    </>
  );
}

function StatTile({ label, value, sub }: { label: string; value: number; sub: string }) {
  return (
    <div className="glass-card flex flex-col gap-1 p-4">
      <span className="text-xs" style={{ color: "var(--text-muted)" }}>{label}</span>
      <span className="text-2xl font-bold" style={{ color: "var(--accent)" }}>{value}</span>
      <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>{sub}</span>
    </div>
  );
}
