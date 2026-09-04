"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import * as d3 from "d3";
import { rashiLordFromApiName } from "@/lib/astro";
import { getCurrentDashaChain } from "@/lib/kpiScoring";
import type { WorkflowAnalysisResponse } from "@/lib/types";

type NodeType = "planet" | "house" | "yoga" | "dasha";

interface GNode extends d3.SimulationNodeDatum {
  id: string;
  type: NodeType;
  label: string;
}

interface GLink {
  source: string;
  target: string;
  label: string;
}

const TYPE_COLOR: Record<NodeType, string> = {
  planet: "#f97316", // orange
  house: "#3b82f6", // blue
  yoga: "#22c55e", // green
  dasha: "#06b6d4", // cyan
};

const TYPE_LABEL: Record<NodeType, string> = {
  planet: "Planets",
  house: "Houses",
  yoga: "Yogas",
  dasha: "Dasha",
};

const TYPE_ORDER: NodeType[] = ["planet", "house", "yoga", "dasha"];

/**
 * Knowledge Graph Explorer — real data only. Nodes/edges are derived
 * straight from this chart's WorkflowAnalysisResponse (planets, houses,
 * *present* yogas, and the currently-running dasha chain) — nothing
 * fabricated. Node types this app doesn't yet compute distinctly (Rule,
 * Transit, Karaka as their own graph objects) are deliberately left out
 * rather than faked; a yoga's classical source is still shown in its
 * detail panel via YogaResultResponse.source_text.
 */
export function GraphExplorer({ result, size = 640 }: { result: WorkflowAnalysisResponse; size?: number }) {
  const [activeTypes, setActiveTypes] = useState<Set<NodeType>>(new Set(TYPE_ORDER));
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [measuredWidth, setMeasuredWidth] = useState(size);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver(([entry]) => {
      const w = entry.contentRect.width;
      if (w > 100) setMeasuredWidth(Math.floor(w));
    });
    observer.observe(el);
    const w = el.getBoundingClientRect().width;
    if (w > 100) setMeasuredWidth(Math.floor(w));
    return () => observer.disconnect();
  }, []);

  const graphSize = measuredWidth;

  const presentYogas = useMemo(() => result.yogas.results.filter((y) => y.is_present), [result]);
  const dashaChain = useMemo(() => getCurrentDashaChain(result.dasha.mahadashas), [result]);
  const currentMD = dashaChain[0] ?? null;

  const { nodes: allNodes, links: allLinks } = useMemo(() => {
    const nodes: GNode[] = [];
    const links: GLink[] = [];

    for (const p of result.chart.planets) {
      nodes.push({ id: `planet:${p.planet}`, type: "planet", label: p.planet });
    }
    for (const h of result.chart.houses) {
      nodes.push({ id: `house:${h.house_number}`, type: "house", label: `House ${h.house_number}` });
      const lord = rashiLordFromApiName(h.rashi);
      if (lord) {
        links.push({ source: `house:${h.house_number}`, target: `planet:${lord}`, label: `${lord} is lord of House ${h.house_number}` });
      }
    }
    for (const p of result.chart.planets) {
      links.push({ source: `planet:${p.planet}`, target: `house:${p.house_number}`, label: `${p.planet} occupies House ${p.house_number}` });
    }
    for (const y of presentYogas) {
      const yid = `yoga:${y.yoga_id}`;
      nodes.push({ id: yid, type: "yoga", label: y.name });
      for (const pl of y.involved_planets) {
        links.push({ source: yid, target: `planet:${pl}`, label: `${pl} participates in ${y.name}` });
      }
      for (const hn of y.involved_houses) {
        links.push({ source: yid, target: `house:${hn}`, label: `House ${hn} involved in ${y.name}` });
      }
    }
    if (currentMD) {
      const did = `dasha:${currentMD.lord}`;
      nodes.push({ id: did, type: "dasha", label: `${currentMD.lord} Dasha` });
      links.push({ source: did, target: `planet:${currentMD.lord}`, label: `${currentMD.lord}'s own Mahadasha is running now` });
    }

    return { nodes, links };
  }, [result, presentYogas, currentMD]);

  const visibleNodes = useMemo(() => allNodes.filter((n) => activeTypes.has(n.type)), [allNodes, activeTypes]);
  const visibleIds = useMemo(() => new Set(visibleNodes.map((n) => n.id)), [visibleNodes]);
  const visibleLinks = useMemo(
    () => allLinks.filter((l) => visibleIds.has(l.source) && visibleIds.has(l.target)),
    [allLinks, visibleIds],
  );

  const [positions, setPositions] = useState<Record<string, { x: number; y: number }>>({});

  useEffect(() => {
    const simNodes: GNode[] = allNodes.map((n) => ({ ...n }));
    const simLinks = allLinks.map((l) => ({ ...l }));

    const simulation = d3
      .forceSimulation(simNodes)
      .force(
        "link",
        d3
          .forceLink<GNode, d3.SimulationLinkDatum<GNode>>(simLinks as unknown as d3.SimulationLinkDatum<GNode>[])
          .id((d) => (d as GNode).id)
          .distance(graphSize * 0.18),
      )
      .force("charge", d3.forceManyBody().strength(-graphSize * 0.4))
      .force("center", d3.forceCenter(graphSize / 2, graphSize / 2))
      .force("collide", d3.forceCollide(graphSize * 0.06))
      .stop();

    simulation.tick(300);

    const next: Record<string, { x: number; y: number }> = {};
    for (const n of simNodes) {
      const margin = 36;
      next[n.id] = {
        x: Math.max(margin, Math.min(graphSize - margin, n.x ?? graphSize / 2)),
        y: Math.max(margin, Math.min(graphSize - margin, n.y ?? graphSize / 2)),
      };
    }
    setPositions(next);
  }, [allNodes, allLinks, graphSize]);

  const toggleType = (t: NodeType) => {
    setActiveTypes((prev) => {
      const next = new Set(prev);
      if (next.has(t)) next.delete(t);
      else next.add(t);
      return next;
    });
  };

  const q = query.trim().toLowerCase();
  const matchesQuery = (n: GNode) => !q || n.label.toLowerCase().includes(q);

  const neighborIds = (id: string) =>
    new Set(
      visibleLinks.flatMap((l) => (l.source === id ? [l.target] : l.target === id ? [l.source] : [])),
    );

  const selectedNeighbors = selectedId ? neighborIds(selectedId) : new Set<string>();
  const selectedNode = allNodes.find((n) => n.id === selectedId) ?? null;

  const nodeById = (id: string) => allNodes.find((n) => n.id === id) ?? null;

  const renderDetails = () => {
    if (!selectedNode) {
      return (
        <p className="text-xs" style={{ color: "var(--text-muted)" }}>
          Click a node to see its real, chart-derived relationships.
        </p>
      );
    }

    if (selectedNode.type === "planet") {
      const planetName = selectedNode.label;
      const pos = result.chart.planets.find((p) => p.planet === planetName);
      const connectedYogas = presentYogas.filter((y) => y.involved_planets.includes(planetName));
      return (
        <div className="space-y-3 text-xs">
          <div>
            <p className="font-semibold" style={{ color: "var(--text-primary)" }}>{planetName}</p>
            <p style={{ color: "var(--text-muted)" }}>Planet</p>
          </div>
          {pos && (
            <dl className="space-y-1">
              <Row label="House" value={String(pos.house_number)} />
              <Row label="Sign" value={pos.rashi} />
              <Row label="Dignity" value={pos.dignity ?? "—"} />
              <Row label="Nakshatra" value={pos.nakshatra} />
              <Row label="Retrograde" value={pos.is_retrograde ? "Yes" : "No"} />
            </dl>
          )}
          {connectedYogas.length > 0 && (
            <div>
              <p className="mb-1 font-semibold" style={{ color: "var(--text-secondary)" }}>Yogas</p>
              <ul className="space-y-0.5">
                {connectedYogas.map((y) => (
                  <li key={y.yoga_id} style={{ color: "var(--text-primary)" }}>{y.name}</li>
                ))}
              </ul>
            </div>
          )}
          {currentMD?.lord === planetName && (
            <p style={{ color: TYPE_COLOR.dasha }}>Own Mahadasha is running right now.</p>
          )}
        </div>
      );
    }

    if (selectedNode.type === "house") {
      const houseNumber = Number(selectedNode.label.replace("House ", ""));
      const cusp = result.chart.houses.find((h) => h.house_number === houseNumber);
      const occupants = result.chart.planets.filter((p) => p.house_number === houseNumber);
      const lord = cusp ? rashiLordFromApiName(cusp.rashi) : null;
      const connectedYogas = presentYogas.filter((y) => y.involved_houses.includes(houseNumber));
      return (
        <div className="space-y-3 text-xs">
          <div>
            <p className="font-semibold" style={{ color: "var(--text-primary)" }}>{selectedNode.label}</p>
            <p style={{ color: "var(--text-muted)" }}>House</p>
          </div>
          <dl className="space-y-1">
            <Row label="Sign" value={cusp?.rashi ?? "—"} />
            <Row label="Lord" value={lord ?? "—"} />
            <Row label="Occupants" value={occupants.length ? occupants.map((p) => p.planet).join(", ") : "None"} />
          </dl>
          {connectedYogas.length > 0 && (
            <div>
              <p className="mb-1 font-semibold" style={{ color: "var(--text-secondary)" }}>Yogas</p>
              <ul className="space-y-0.5">
                {connectedYogas.map((y) => (
                  <li key={y.yoga_id} style={{ color: "var(--text-primary)" }}>{y.name}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      );
    }

    if (selectedNode.type === "yoga") {
      const yid = selectedNode.id.replace("yoga:", "");
      const y = presentYogas.find((yy) => yy.yoga_id === yid);
      if (!y) return null;
      return (
        <div className="space-y-3 text-xs">
          <div>
            <p className="font-semibold" style={{ color: "var(--text-primary)" }}>{y.name}</p>
            <p style={{ color: "var(--text-muted)" }}>Yoga · {y.category}</p>
          </div>
          <dl className="space-y-1">
            <Row label="Source" value={y.source_text} />
            <Row label="Strength" value={y.strength ?? "—"} />
            <Row label="Planets" value={y.involved_planets.join(", ") || "—"} />
            <Row label="Houses" value={y.involved_houses.join(", ") || "—"} />
          </dl>
          {y.satisfied.length > 0 && (
            <div>
              <p className="mb-1 font-semibold" style={{ color: "var(--text-secondary)" }}>Satisfied conditions</p>
              <ul className="space-y-0.5">
                {y.satisfied.map((s, i) => (
                  <li key={i} style={{ color: "var(--text-primary)" }}>{s}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      );
    }

    if (selectedNode.type === "dasha" && currentMD) {
      return (
        <div className="space-y-3 text-xs">
          <div>
            <p className="font-semibold" style={{ color: "var(--text-primary)" }}>{selectedNode.label}</p>
            <p style={{ color: "var(--text-muted)" }}>Currently Running Mahadasha</p>
          </div>
          <dl className="space-y-1">
            <Row label="Lord" value={currentMD.lord} />
            <Row label="Start" value={new Date(currentMD.start_date).toLocaleDateString()} />
            <Row label="End" value={new Date(currentMD.end_date).toLocaleDateString()} />
          </dl>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search nodes… (e.g. Mars, House 10, Raja Yoga)"
          className="field-input"
          style={{ maxWidth: 340 }}
          aria-label="Search graph nodes"
        />
        <span className="text-xs" style={{ color: "var(--text-muted)" }}>
          {visibleNodes.length} nodes · {visibleLinks.length} relationships
        </span>
      </div>

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start">
        <div className="w-full space-y-2 lg:w-48 lg:shrink-0">
          <div className="glass-card p-3">
            <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
              Node Types
            </h4>
            <div className="flex flex-col gap-1">
              {TYPE_ORDER.map((t) => {
                const active = activeTypes.has(t);
                const count = allNodes.filter((n) => n.type === t).length;
                return (
                  <button
                    key={t}
                    type="button"
                    onClick={() => toggleType(t)}
                    disabled={count === 0}
                    className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-left text-xs transition"
                    style={{ color: active ? "var(--text-primary)" : "var(--text-muted)", opacity: count === 0 ? 0.4 : 1 }}
                    aria-pressed={active}
                  >
                    <span
                      className="h-2.5 w-2.5 shrink-0 rounded-full"
                      style={{ backgroundColor: active ? TYPE_COLOR[t] : "var(--border-default)" }}
                    />
                    <span className="flex-1">{TYPE_LABEL[t]}</span>
                    <span style={{ color: "var(--text-muted)" }}>{count}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        <div className="min-w-0 flex-1">
          <div className="glass-card p-4">
            <div ref={containerRef} style={{ width: "100%" }}>
              <svg width={graphSize} height={graphSize} viewBox={`0 0 ${graphSize} ${graphSize}`} role="img" aria-label="Knowledge graph explorer">
                {visibleLinks.map((l, i) => {
                  const s = positions[l.source];
                  const t = positions[l.target];
                  if (!s || !t) return null;
                  const highlighted = selectedId && (l.source === selectedId || l.target === selectedId);
                  const dimmed = selectedId && !highlighted;
                  return (
                    <line
                      key={i}
                      x1={s.x} y1={s.y} x2={t.x} y2={t.y}
                      stroke="var(--border-primary)"
                      strokeWidth={highlighted ? 1.6 : 0.8}
                      opacity={dimmed ? 0.15 : 0.6}
                    />
                  );
                })}
                {visibleNodes.map((n) => {
                  const pos = positions[n.id];
                  if (!pos) return null;
                  const active = selectedId === n.id;
                  const isNeighbor = selectedId ? selectedNeighbors.has(n.id) : false;
                  const dimmed = selectedId !== null && !active && !isNeighbor;
                  const faded = q !== "" && !matchesQuery(n);
                  return (
                    <g
                      key={n.id}
                      transform={`translate(${pos.x}, ${pos.y})`}
                      onClick={() => setSelectedId(active ? null : n.id)}
                      style={{ cursor: "pointer" }}
                      opacity={dimmed || faded ? 0.25 : 1}
                      className="transition-opacity"
                    >
                      {active && <circle r={20} fill={TYPE_COLOR[n.type]} opacity={0.18} />}
                      <circle r={active ? 12 : 9} fill={TYPE_COLOR[n.type]} stroke="var(--bg-card)" strokeWidth={1.5} />
                      <text
                        y={active ? 26 : 22}
                        textAnchor="middle"
                        style={{ fontSize: 9, fill: "var(--text-secondary)", pointerEvents: "none", userSelect: "none" }}
                      >
                        {n.label}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>
            {visibleNodes.length === 0 && (
              <p className="p-6 text-center text-sm" style={{ color: "var(--text-muted)" }}>
                No nodes match the current filters.
              </p>
            )}
          </div>
        </div>

        <div className="w-full space-y-3 lg:w-72 lg:shrink-0">
          <div className="glass-card p-4">
            <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
              Details
            </h4>
            {renderDetails()}
          </div>
          {selectedId && (
            <div className="glass-card p-4">
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
                Connected Nodes ({selectedNeighbors.size})
              </h4>
              <ul className="space-y-1 text-xs">
                {Array.from(selectedNeighbors).map((id) => {
                  const n = nodeById(id);
                  if (!n) return null;
                  return (
                    <li key={id}>
                      <button
                        type="button"
                        onClick={() => setSelectedId(id)}
                        className="flex items-center gap-2 text-left hover:underline"
                        style={{ color: "var(--text-primary)" }}
                      >
                        <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: TYPE_COLOR[n.type] }} />
                        {n.label}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-3">
      <dt style={{ color: "var(--text-muted)" }}>{label}</dt>
      <dd className="text-right" style={{ color: "var(--text-primary)" }}>{value}</dd>
    </div>
  );
}
