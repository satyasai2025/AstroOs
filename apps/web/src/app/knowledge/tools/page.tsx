"use client";

import { useState } from "react";
import { Card, KnowledgeGraph, SearchInput, Tabs, Timeline } from "@/components/ui";

type Tab = "compare" | "relationships" | "timeline" | "search";

const JUPITER_GRAPH_NODES = [
  { id: "jupiter", x: 150, y: 90, label: "Jupiter", color: "var(--gold-400)", size: 26 },
  { id: "sun", x: 60, y: 40, label: "Sun", color: "var(--cyan-400)", size: 16 },
  { id: "moon", x: 240, y: 40, label: "Moon", color: "var(--cyan-400)", size: 16 },
  { id: "mercury", x: 250, y: 150, label: "Mercury", color: "var(--violet-400)", size: 14 },
  { id: "wealth", x: 60, y: 150, label: "Wealth (2H)", color: "var(--success-400)", size: 14 },
];
const JUPITER_GRAPH_EDGES = [
  { from: "jupiter", to: "sun" },
  { from: "jupiter", to: "moon" },
  { from: "jupiter", to: "mercury" },
  { from: "jupiter", to: "wealth" },
];

const TIMELINE_EVENTS = [
  { title: "Guru Mahadasha Begins", date: "2018-05", description: "Illustrative classical timeline sample.", tone: "gold" as const },
  { title: "Gaja Kesari Yoga active", date: "2019-11", description: "Jupiter-Moon Kendra relationship.", tone: "cyan" as const },
  { title: "Guru Mahadasha Ends", date: "2034-05", tone: "gold" as const },
];

export default function KnowledgeToolsPage() {
  const [tab, setTab] = useState<Tab>("relationships");
  const [search, setSearch] = useState("");

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
          Knowledge Tools
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Compare entities, explore relationships, and search the knowledge base.
        </p>
      </div>

      <div className="mb-4">
        <Tabs
          tabs={[
            { key: "compare", label: "Compare Entities" },
            { key: "relationships", label: "Relationship Map" },
            { key: "timeline", label: "Timeline Explorer" },
            { key: "search", label: "Advanced Search" },
          ]}
          active={tab}
          onChange={(k) => setTab(k as Tab)}
        />
      </div>

      {tab === "compare" && (
        <Card>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            Side-by-side entity comparison isn't wired to a real reference-data endpoint yet — see{" "}
            <a href="/knowledge/browse" style={{ color: "var(--cyan-400)" }}>
              Knowledge Browse
            </a>{" "}
            for individual entities.
          </p>
        </Card>
      )}

      {tab === "relationships" && (
        <Card>
          <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-tertiary)" }}>
            Jupiter Relationship Map
          </h4>
          <KnowledgeGraph nodes={JUPITER_GRAPH_NODES} edges={JUPITER_GRAPH_EDGES} width={340} height={220} />
          <p className="mt-3 text-xs" style={{ color: "var(--text-tertiary)" }}>
            Illustrative classical relationships (friends/aspects) — for a chart-specific version
            with real computed data, see Planet Relationship Graph under Analysis.
          </p>
        </Card>
      )}

      {tab === "timeline" && (
        <Card>
          <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-tertiary)" }}>
            Sample Classical Timeline
          </h4>
          <Timeline events={TIMELINE_EVENTS} />
          <p className="mt-3 text-xs" style={{ color: "var(--text-tertiary)" }}>
            Illustrative — for a chart-specific dasha/transit timeline with real computed dates, see
            Dasha Analysis and Transit Analysis under Analysis.
          </p>
        </Card>
      )}

      {tab === "search" && (
        <Card>
          <SearchInput value={search} onChange={setSearch} placeholder="Search yogas, karakatvas, texts…" />
          <p className="mt-3 text-xs" style={{ color: "var(--text-tertiary)" }}>
            Advanced cross-category search isn't wired to a real endpoint yet — Karakatva search
            already works at{" "}
            <a href="/karakatva" style={{ color: "var(--cyan-400)" }}>
              /karakatva
            </a>
            .
          </p>
        </Card>
      )}
    </div>
  );
}
