"use client";

import { useEffect, useState, useMemo, useRef } from "react";
import * as d3 from "d3";
import { NATURAL_RELATIONSHIPS, PLANET_SYMBOLS } from "@/lib/astro";
import { getCurrentDashaChain } from "@/lib/kpiScoring";
import { PlanetDetailPanel } from "@/components/charts/PlanetDetailPanel";
import { buildGraphLinks, ALL_LINK_KINDS, type LinkKind } from "@/lib/planetRelationshipGraph";
import type {
  AspectSchema,
  DashaPeriodResponse,
  PlanetPositionSchema,
  WorkflowAnalysisResponse,
  YogaResultResponse,
} from "@/lib/types";

/* ─── Types ──────────────────────────────────────────────────────── */

interface Props {
  planets: PlanetPositionSchema[];
  aspects: AspectSchema[];
  yogas?: YogaResultResponse[];
  mahadashas?: DashaPeriodResponse[];
  result?: WorkflowAnalysisResponse;
  size?: number;
}

interface SimNode extends d3.SimulationNodeDatum {
  id: string;
  x: number;
  y: number;
  fx: number | null;
  fy: number | null;
}

/* ─── Constants ──────────────────────────────────────────────────── */

const ALL_KINDS: LinkKind[] = ALL_LINK_KINDS;

const KIND_LABELS: Record<LinkKind, string> = {
  friend: "Friend",
  enemy: "Enemy",
  aspect: "Aspect",
  mutualAspect: "Mutual Aspect",
  conjunction: "Conjunction",
  parivartana: "Parivartana",
  dispositor: "Dispositor",
  nakshatraLord: "Nakshatra Lord",
  yoga: "Yoga",
  dasha: "Dasha",
  yuddha: "Yuddha",
};

const EDGE_COLORS: Record<LinkKind, string> = {
  friend: "#10b981",       // emerald
  enemy: "#f43f5e",        // rose
  aspect: "#38bdf8",       // sky/cyan
  mutualAspect: "#a855f7", // purple
  conjunction: "#f59e0b",  // amber
  parivartana: "#06b6d4",  // cyan
  dispositor: "#6366f1",   // indigo
  nakshatraLord: "#c084fc",// violet
  yoga: "#ec4899",         // pink
  dasha: "#f97316",        // orange
  yuddha: "#e11d48",       // rose-red
};

/** Traditional graha colors for planet nodes */
const PLANET_THEME: Record<string, { fill: string; glow: string; stroke: string }> = {
  Sun:     { fill: "#fb923c", glow: "rgba(251, 146, 60, 0.35)", stroke: "#ea580c" },
  Moon:    { fill: "#38bdf8", glow: "rgba(56, 189, 248, 0.35)", stroke: "#0284c7" },
  Mars:    { fill: "#f87171", glow: "rgba(248, 113, 113, 0.35)", stroke: "#dc2626" },
  Mercury: { fill: "#34d399", glow: "rgba(52, 211, 153, 0.35)", stroke: "#059669" },
  Jupiter: { fill: "#fbbf24", glow: "rgba(251, 191, 36, 0.35)", stroke: "#d97706" },
  Venus:   { fill: "#f472b6", glow: "rgba(244, 114, 182, 0.35)", stroke: "#db2777" },
  Saturn:  { fill: "#a78bfa", glow: "rgba(167, 139, 250, 0.35)", stroke: "#7c3aed" },
  Rahu:    { fill: "#818cf8", glow: "rgba(129, 140, 248, 0.35)", stroke: "#4f46e5" },
  Ketu:    { fill: "#c084fc", glow: "rgba(192, 132, 252, 0.35)", stroke: "#9333ea" },
};

const PLANET_NAMES = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"];

const LINK_WEIGHT: Record<LinkKind, number> = {
  friend: 2,
  enemy: 2,
  dispositor: 3,
  nakshatraLord: 4,
  aspect: 5,
  conjunction: 6,
  dasha: 6,
  yoga: 7,
  mutualAspect: 8,
  yuddha: 9,
  parivartana: 10,
};

/* ─── Helpers ────────────────────────────────────────────────────── */

function angleForIndex(i: number, total: number): number {
  return (2 * Math.PI * i) / total - Math.PI / 2;
}

/* ─── SVG Defs ───────────────────────────────────────────────────── */

function SvgDefs() {
  return (
    <defs>
      <filter id="v2-glow" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="6" result="blur" />
        <feMerge>
          <feMergeNode in="blur" />
          <feMergeNode in="SourceGraphic" />
        </feMerge>
      </filter>
      <filter id="v2-glow-lg" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="12" result="blur" />
        <feMerge>
          <feMergeNode in="blur" />
          <feMergeNode in="SourceGraphic" />
        </feMerge>
      </filter>

      {ALL_KINDS.map((kind) => (
        <marker
          key={kind}
          id={`arrow-${kind}`}
          viewBox="0 0 10 6"
          refX="10"
          refY="3"
          markerWidth="8"
          markerHeight="6"
          orient="auto-start-reverse"
        >
          <path d="M0,0 L10,3 L0,6 Z" fill={EDGE_COLORS[kind]} opacity="0.85" />
        </marker>
      ))}

      {Object.entries(PLANET_THEME).map(([name, t]) => (
        <radialGradient key={name} id={`v2grad-${name}`} cx="35%" cy="35%" r="65%">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.4" />
          <stop offset="40%" stopColor={t.fill} stopOpacity="1" />
          <stop offset="100%" stopColor={t.stroke} stopOpacity="1" />
        </radialGradient>
      ))}
    </defs>
  );
}

/* ─── Main Component ─────────────────────────────────────────────── */

export default function PlanetaryRelationshipGraph2({
  planets,
  aspects,
  yogas,
  mahadashas,
  result,
  size = 600,
}: Props) {
  const [selected, setSelected] = useState<string | null>(null);
  const [positions, setPositions] = useState<Record<string, { x: number; y: number }>>({});
  const [activeKinds, setActiveKinds] = useState<Set<LinkKind>>(new Set(ALL_KINDS));
  const [zoom, setZoom] = useState(1);
  const containerRef = useRef<HTMLDivElement>(null);
  const [graphWidth, setGraphWidth] = useState(size);

  const planetNames = useMemo(() => planets.map((p) => p.planet), [planets]);

  useEffect(() => {
    const el = containerRef.current?.parentElement;
    if (!el) {
      setGraphWidth(size);
      return;
    }
    const obs = new ResizeObserver(([entry]) => {
      const w = entry.contentRect.width;
      if (w > 100) setGraphWidth(Math.floor(w));
    });
    obs.observe(el);
    const w = el.getBoundingClientRect().width;
    if (w > 100) setGraphWidth(Math.floor(w));
    return () => obs.disconnect();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const graphSize = graphWidth;
  const center = graphSize / 2;

  const dashaChain = useMemo(
    () => (mahadashas ? getCurrentDashaChain(mahadashas) : []),
    [mahadashas],
  );
  const activeDashaPlanets = useMemo(() => {
    const s = new Set<string>();
    dashaChain.forEach((p) => s.add(p.lord));
    return s;
  }, [dashaChain]);

  const allLinks = useMemo(
    () => buildGraphLinks({ planets, aspects, yogas, dashaChain }),
    [planets, aspects, yogas, dashaChain],
  );

  const linkWeight = useMemo(() => {
    const map = new Map<string, number>();
    allLinks.forEach((l) => {
      const key = [l.source, l.target].sort().join("|");
      map.set(key, (map.get(key) ?? 0) + LINK_WEIGHT[l.kind]);
    });
    return map;
  }, [allLinks]);

  const filteredLinks = useMemo(
    () => allLinks.filter((l) => activeKinds.has(l.kind)),
    [allLinks, activeKinds],
  );

  useEffect(() => {
    const radius = graphSize * 0.36;
    const nodes: SimNode[] = planetNames.map((name) => {
      if (selected && name === selected) {
        return { id: name, x: center, y: center, fx: center, fy: center };
      }
      const others = selected ? planetNames.filter((n) => n !== selected) : planetNames;
      const otherIdx = others.indexOf(name);
      const angle = angleForIndex(otherIdx, others.length);
      return {
        id: name,
        x: center + radius * Math.cos(angle),
        y: center + radius * Math.sin(angle),
        fx: null,
        fy: null,
      };
    });

    const simLinks = filteredLinks.map((l) => ({
      source: l.source,
      target: l.target,
    }));

    const sim = d3
      .forceSimulation(nodes)
      .force(
        "link",
        d3.forceLink(simLinks).id((d: any) => d.id).distance(graphSize * 0.28).strength(0.6),
      )
      .force("charge", d3.forceManyBody().strength(-graphSize * 0.4))
      .force("center", d3.forceCenter(center, center).strength(selected ? 0 : 0.8))
      .force("collision", d3.forceCollide().radius(graphSize * 0.12))
      .force("x", d3.forceX(center).strength(selected ? 0.3 : 0.05))
      .force("y", d3.forceY(center).strength(selected ? 0.3 : 0.05))
      .alphaDecay(0.03);

    sim.tick(300);
    sim.stop();

    const margin = graphSize * 0.1;
    const pos: Record<string, { x: number; y: number }> = {};
    nodes.forEach((n) => {
      if (selected && n.id === selected) {
        pos[n.id] = { x: center, y: center };
      } else {
        pos[n.id] = {
          x: Math.max(margin, Math.min(graphSize - margin, n.x ?? center)),
          y: Math.max(margin, Math.min(graphSize - margin, n.y ?? center)),
        };
      }
    });
    setPositions(pos);

    sim.nodes([]);
  }, [planetNames, filteredLinks, selected, graphSize, center]);

  const toggleKind = (kind: LinkKind) => {
    setActiveKinds((prev) => {
      const next = new Set(prev);
      if (next.has(kind)) next.delete(kind);
      else next.add(kind);
      return next;
    });
  };

  const edgePath = (sx: number, sy: number, tx: number, ty: number): string => {
    const mx = (sx + tx) / 2;
    const my = (sy + ty) / 2;
    const dx = tx - sx;
    const dy = ty - sy;
    const dist = Math.sqrt(dx * dx + dy * dy) || 1;
    const curveAmount = dist * 0.15;
    const cx = mx + (-dy / dist) * curveAmount;
    const cy = my + (dx / dist) * curveAmount;
    return `M${sx},${sy} Q${cx},${cy} ${tx},${ty}`;
  };

  const bezierMidpoint = (sx: number, sy: number, tx: number, ty: number): { x: number; y: number } => {
    const mx = (sx + tx) / 2;
    const my = (sy + ty) / 2;
    const dx = tx - sx;
    const dy = ty - sy;
    const dist = Math.sqrt(dx * dx + dy * dy) || 1;
    const curveAmount = dist * 0.15;
    const cx = mx + (-dy / dist) * curveAmount;
    const cy = my + (dx / dist) * curveAmount;
    return { x: (sx + 2 * cx + tx) / 4, y: (sy + 2 * cy + ty) / 4 };
  };

  const selectedPlanet = useMemo(
    () => (selected ? planets.find((p) => p.planet === selected) : null),
    [selected, planets],
  );

  const selectedConnections = useMemo(() => {
    if (!selected) return [];
    return filteredLinks.filter((l) => l.source === selected || l.target === selected);
  }, [selected, filteredLinks]);

  const summaryStats = useMemo<{ friend: number; enemy: number; aspect: number; total: number }>(() => {
    let friend = 0, enemy = 0, aspect = 0;
    filteredLinks.forEach((l) => {
      if (l.kind === "friend") friend++;
      else if (l.kind === "enemy") enemy++;
      else if (l.kind === "aspect" || l.kind === "mutualAspect") aspect++;
    });
    const total = friend + enemy + aspect;
    return { friend, enemy, aspect, total };
  }, [filteredLinks]);

  const nodeRadius = graphSize * 0.045;

  return (
    <div className="flex flex-col w-full space-y-4 font-sans">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b pb-3" style={{ borderColor: "var(--border-primary)" }}>
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <span>🌐</span> Planet Relationship Graph
          </h2>
          <p className="text-xs text-slate-700 dark:text-slate-300 font-medium mt-0.5">
            Interactive D3 force-directed network graph of Graha aspects, natural friendships, dispositors &amp; Yogas.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-bold px-3 py-1 rounded-full bg-cyan-950/40 text-cyan-300 border border-cyan-500/30">
          <span>{filteredLinks.length} Active Edges</span>
        </div>
      </div>

      {/* ── Filter toolbar ── */}
      <div className="flex flex-wrap gap-1.5 p-3 rounded-2xl border backdrop-blur-sm" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}>
        <span className="text-xs font-bold text-slate-800 dark:text-slate-200 mr-2 flex items-center">Filters:</span>
        {ALL_KINDS.map((kind) => {
          const active = activeKinds.has(kind);
          const color = EDGE_COLORS[kind];
          return (
            <button
              key={kind}
              type="button"
              onClick={() => toggleKind(kind)}
              className="flex items-center gap-1.5 rounded-xl px-2.5 py-1 text-xs font-bold transition-all cursor-pointer"
              style={{
                backgroundColor: active ? `${color}25` : "rgba(30, 41, 59, 0.4)",
                color: active ? color : "var(--text-muted)",
                border: `1px solid ${active ? `${color}60` : "var(--border-primary)"}`,
              }}
            >
              <span
                className="inline-block h-2 w-2 rounded-full"
                style={{ backgroundColor: active ? color : "#64748b" }}
              />
              {KIND_LABELS[kind]}
            </button>
          );
        })}
      </div>

      {/* ── Main layout: graph + right panel ── */}
      <div className="flex flex-col lg:flex-row gap-4 min-h-0">
        {/* ── Graph area ── */}
        <div className="flex-1 relative min-w-0 rounded-2xl border p-2 shadow-xl backdrop-blur-sm" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}>
          {/* Zoom controls */}
          <div className="absolute top-4 left-4 z-10 flex flex-col gap-1.5">
            {[
              { label: "+", action: () => setZoom((z) => Math.min(z + 0.15, 2.5)) },
              { label: "−", action: () => setZoom((z) => Math.max(z - 0.15, 0.4)) },
              { label: "⤢", action: () => { setZoom(1); } },
            ].map((btn) => (
              <button
                key={btn.label}
                type="button"
                onClick={btn.action}
                className="flex h-8 w-8 items-center justify-center rounded-xl text-xs font-bold transition-all cursor-pointer bg-slate-900/90 text-slate-200 border border-slate-700 shadow-md hover:bg-slate-800"
              >
                {btn.label}
              </button>
            ))}
          </div>

          {/* SVG Canvas */}
          <div ref={containerRef} style={{ width: "100%", minHeight: 450, overflow: "hidden", borderRadius: "16px", backgroundColor: "#0b0f17" }}>
            <svg
              width="100%"
              height={graphSize}
              viewBox={`0 0 ${graphSize} ${graphSize}`}
              style={{
                transform: `scale(${zoom})`,
                transformOrigin: "center center",
                transition: "transform 0.3s ease",
              }}
              role="img"
              aria-label="Planet relationship network graph v2"
            >
              <defs>
                <radialGradient id="bg-grad" cx="50%" cy="50%" r="75%">
                  <stop offset="0%" stopColor="#0f172a" />
                  <stop offset="100%" stopColor="#070a12" />
                </radialGradient>
              </defs>
              <SvgDefs />

              {/* Background */}
              <rect x="0" y="0" width={graphSize} height={graphSize} fill="url(#bg-grad)" rx="16" />

              {/* Edges */}
              {filteredLinks.map((link, i) => {
                const s = positions[link.source];
                const t = positions[link.target];
                if (!s || !t) return null;
                if (link.source === link.target) return null;

                const weight = linkWeight.get([link.source, link.target].sort().join("|")) ?? 1;
                const maxWeight = 5;
                const strokeWidth = 1.0 + (Math.min(weight, maxWeight) / maxWeight) * 1.6;

                const isDimmed = selected && link.source !== selected && link.target !== selected;
                const opacity = isDimmed ? 0.15 : 0.8;

                const path = edgePath(s.x, s.y, t.x, t.y);

                return (
                  <g key={`${link.source}-${link.target}-${link.kind}-${i}`}>
                    <path
                      d={path}
                      fill="none"
                      stroke={EDGE_COLORS[link.kind]}
                      strokeWidth={strokeWidth}
                      strokeOpacity={opacity}
                      strokeDasharray={link.kind === "aspect" || link.kind === "yuddha" ? "6 4" : undefined}
                      markerEnd={`url(#arrow-${link.kind})`}
                    />
                    {!isDimmed && (
                      <text
                        x={bezierMidpoint(s.x, s.y, t.x, t.y).x}
                        y={bezierMidpoint(s.x, s.y, t.x, t.y).y}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fill={EDGE_COLORS[link.kind]}
                        fontSize={10}
                        fontWeight={700}
                        opacity={0.9}
                        style={{ pointerEvents: "none" }}
                      >
                        {link.label}
                      </text>
                    )}
                  </g>
                );
              })}

              {/* Planet nodes */}
              {planetNames.map((name) => {
                const pos = positions[name];
                if (!pos) return null;
                const theme = PLANET_THEME[name];
                if (!theme) return null;

                const isSelected = selected === name;
                const isDimmed = selected && !isSelected && !filteredLinks.some(
                  (l) => (l.source === selected && l.target === name) || (l.target === selected && l.source === name),
                );
                const isDasha = activeDashaPlanets.has(name);
                const r = isSelected ? nodeRadius * 1.4 : nodeRadius;

                return (
                  <g
                    key={name}
                    style={{ cursor: "pointer", transition: "opacity 0.3s" }}
                    opacity={isDimmed ? 0.25 : 1}
                    onClick={() => setSelected(isSelected ? null : name)}
                  >
                    <circle
                      cx={pos.x}
                      cy={pos.y}
                      r={r * 2.2}
                      fill={theme.glow}
                      filter="url(#v2-glow-lg)"
                      opacity={isSelected ? 0.7 : 0.35}
                    />

                    {isDasha && (
                      <circle
                        cx={pos.x}
                        cy={pos.y}
                        r={r + 6}
                        fill="none"
                        stroke="#f97316"
                        strokeWidth={2.5}
                        strokeDasharray="4 3"
                        opacity={0.9}
                      />
                    )}

                    {isSelected && (
                      <circle
                        cx={pos.x}
                        cy={pos.y}
                        r={r + 4}
                        fill="none"
                        stroke={theme.fill}
                        strokeWidth={2.5}
                        opacity={0.8}
                      />
                    )}

                    <circle
                      cx={pos.x}
                      cy={pos.y}
                      r={r}
                      fill={`url(#v2grad-${name})`}
                      stroke={theme.stroke}
                      strokeWidth={1.5}
                      filter="url(#v2-glow)"
                    />

                    <circle
                      cx={pos.x - r * 0.22}
                      cy={pos.y - r * 0.22}
                      r={r * 0.5}
                      fill="white"
                      opacity={0.2}
                    />

                    <text
                      x={pos.x}
                      y={pos.y + r + 15}
                      textAnchor="middle"
                      fill="#f8fafc"
                      fontSize={12}
                      fontWeight={700}
                      fontFamily="system-ui, sans-serif"
                      letterSpacing="0.04em"
                    >
                      {PLANET_SYMBOLS[name] ?? ""} {name}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>

          <p className="mt-2 text-xs font-medium px-2 text-slate-700 dark:text-slate-300">
            Click any planet node to focus its aspects &amp; relationship rays. Toggle filter pills above to hide/show edge types.
          </p>
        </div>

        {/* ── Right panel ── */}
        <div className="w-full lg:w-80 flex-shrink-0 flex flex-col gap-4 overflow-y-auto" style={{ maxHeight: graphSize }}>
          {result ? (
            <PlanetDetailPanel
              planet={selected}
              result={result}
              pinned={selected !== null}
              onUnpin={() => setSelected(null)}
            />
          ) : selectedPlanet ? (
            <div className="rounded-2xl border p-4 shadow-xl space-y-3" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}>
              <div className="flex items-center justify-between border-b pb-2" style={{ borderColor: "var(--border-primary)" }}>
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                  <span>{PLANET_SYMBOLS[selectedPlanet.planet] ?? ""}</span> {selectedPlanet.planet} Details
                </h3>
                <button
                  type="button"
                  onClick={() => setSelected(null)}
                  className="text-xs font-bold px-2 py-0.5 rounded-lg bg-slate-800 text-slate-300 hover:text-white cursor-pointer"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-1.5 text-xs">
                <div className="flex justify-between font-medium">
                  <span className="text-slate-700 dark:text-slate-300">Sign (Rashi)</span>
                  <span className="font-bold" style={{ color: PLANET_THEME[selectedPlanet.planet]?.fill ?? "#e2e8f0" }}>
                    {selectedPlanet.rashi}
                  </span>
                </div>
                <div className="flex justify-between font-medium">
                  <span className="text-slate-700 dark:text-slate-300">Exact Longitude</span>
                  <span className="font-bold text-slate-900 dark:text-slate-100">
                    {Math.floor(selectedPlanet.sidereal_longitude % 30)}°{Math.floor(((selectedPlanet.sidereal_longitude % 1) + 1) % 1 * 60)}'
                  </span>
                </div>
                <div className="flex justify-between font-medium">
                  <span className="text-slate-700 dark:text-slate-300">House Position</span>
                  <span className="font-bold text-slate-900 dark:text-slate-100">
                    {selectedPlanet.house_number ?? "—"}th House
                  </span>
                </div>
              </div>

              {/* Natural relationships */}
              <div className="pt-2 border-t" style={{ borderColor: "var(--border-primary)" }}>
                <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 mb-1.5">
                  Natural Relationships
                </h4>
                {(() => {
                  const nat = NATURAL_RELATIONSHIPS[selectedPlanet.planet];
                  if (!nat) return null;
                  return (
                    <div className="space-y-1 text-xs">
                      {nat.friends.length > 0 && (
                        <div className="flex justify-between">
                          <span className="font-bold text-emerald-400">Friends:</span>
                          <span className="font-semibold text-slate-200">{nat.friends.join(", ")}</span>
                        </div>
                      )}
                      {nat.enemies.length > 0 && (
                        <div className="flex justify-between">
                          <span className="font-bold text-rose-400">Enemies:</span>
                          <span className="font-semibold text-slate-200">{nat.enemies.join(", ")}</span>
                        </div>
                      )}
                      {nat.neutrals.length > 0 && (
                        <div className="flex justify-between">
                          <span className="font-bold text-slate-400">Neutrals:</span>
                          <span className="font-semibold text-slate-300">{nat.neutrals.join(", ")}</span>
                        </div>
                      )}
                    </div>
                  );
                })()}
              </div>

              {/* Connections */}
              {selectedConnections.length > 0 && (
                <div className="pt-2 border-t" style={{ borderColor: "var(--border-primary)" }}>
                  <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 mb-1.5">
                    Active Connections ({selectedConnections.length})
                  </h4>
                  <div className="space-y-1.5 max-h-36 overflow-y-auto">
                    {selectedConnections.map((c, i) => {
                      const other = c.source === selected ? c.target : c.source;
                      return (
                        <div key={i} className="flex items-center gap-2 text-xs p-1 rounded bg-slate-900/60 border border-slate-800">
                          <span
                            className="inline-block h-2 w-2 rounded-full flex-shrink-0"
                            style={{ backgroundColor: EDGE_COLORS[c.kind] }}
                          />
                          <span className="font-bold" style={{ color: EDGE_COLORS[c.kind] }}>{c.label}</span>
                          <span className="text-slate-400">→</span>
                          <span className="font-semibold text-slate-200">{other}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="rounded-2xl border p-5 text-center shadow-md" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}>
              <p className="text-xs font-medium text-slate-700 dark:text-slate-300">
                Click any planet node to inspect its comprehensive aspects &amp; dignities.
              </p>
            </div>
          )}

          {/* Graph Controls */}
          <div className="rounded-2xl border p-4 shadow-md space-y-2" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}>
            <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100 border-b pb-1.5" style={{ borderColor: "var(--border-primary)" }}>
              Graph Dynamics &amp; Metrics
            </h4>
            <div className="space-y-1.5 text-xs">
              {[
                { label: "Zoom Scale", value: `${Math.round(zoom * 100)}%` },
                { label: "Active Edges", value: `${filteredLinks.length} / ${allLinks.length}` },
                { label: "Planets Rendered", value: `${planets.length}` },
              ].map((item) => (
                <div key={item.label} className="flex justify-between font-medium">
                  <span className="text-slate-700 dark:text-slate-300">{item.label}</span>
                  <span className="font-bold text-slate-900 dark:text-slate-100">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Bottom summary cards ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Relationship Summary */}
        <div className="rounded-2xl border p-4 shadow-md space-y-2.5 backdrop-blur-sm" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}>
          <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider">
            Relationship Category Summary
          </h4>
          <div className="space-y-2 text-xs">
            {[
              { label: "Friends", count: summaryStats.friend, color: "#10b981" },
              { label: "Enemies", count: summaryStats.enemy, color: "#f43f5e" },
              { label: "Aspect Rays", count: summaryStats.aspect, color: "#38bdf8" },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between font-medium">
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full" style={{ backgroundColor: item.color }} />
                  <span className="text-slate-800 dark:text-slate-200">{item.label}</span>
                </div>
                <span className="font-bold text-slate-900 dark:text-slate-100">
                  {item.count} ({summaryStats.total > 0 ? Math.round((item.count / summaryStats.total) * 100) : 0}%)
                </span>
              </div>
            ))}
          </div>
          <div className="mt-2 pt-2 border-t text-xs font-semibold text-slate-700 dark:text-slate-300 flex justify-between" style={{ borderColor: "var(--border-primary)" }}>
            <span>Total Evaluated Relationships:</span>
            <span className="font-bold text-slate-900 dark:text-slate-100">{summaryStats.total}</span>
          </div>
        </div>

        {/* Key Insights */}
        <div className="rounded-2xl border p-4 shadow-md space-y-2.5 backdrop-blur-sm" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}>
          <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider">
            Network Key Insights
          </h4>
          <div className="space-y-1.5 text-xs text-slate-800 dark:text-slate-200 font-medium">
            {filteredLinks.length > 0 && (
              <p className="flex items-start gap-2">
                <span className="text-emerald-400 font-bold">✦</span>
                <span>
                  {filteredLinks.filter((l) => l.kind === "friend").length > 0
                    ? `${filteredLinks.filter((l) => l.kind === "friend").length} natural friendship connections active.`
                    : "No natural friendships in current filter."}
                </span>
              </p>
            )}
            {activeDashaPlanets.size > 0 && (
              <p className="flex items-start gap-2">
                <span className="text-orange-400 font-bold">✦</span>
                <span>Active Dasha lords highlighted: <strong>{[...activeDashaPlanets].join(", ")}</strong>.</span>
              </p>
            )}
            <p className="flex items-start gap-2">
              <span className="text-cyan-400 font-bold">✦</span>
              <span>{filteredLinks.filter((l) => l.kind === "aspect" || l.kind === "mutualAspect").length} aspect rays visualized in force layout.</span>
            </p>
          </div>
        </div>
      </div>

      {/* ── Dasha Timeline ── */}
      {dashaChain.length > 0 && (
        <div className="rounded-2xl border p-4 shadow-md space-y-2 backdrop-blur-sm" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}>
          <div className="flex items-center justify-between border-b pb-2" style={{ borderColor: "var(--border-primary)" }}>
            <div>
              <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100">
                Vimshottari Dasha Influencers
              </h4>
              <span className="text-[10px] text-slate-700 dark:text-slate-300 font-medium">
                Active Mahadasha / Antardasha / Pratyantardasha Lord Chain
              </span>
            </div>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-orange-100 text-orange-900 border border-orange-600/40 dark:bg-orange-950/50 dark:text-orange-300">
              Active Dasha Chain
            </span>
          </div>
          <div className="flex gap-2 overflow-x-auto pb-1 pt-1">
            {dashaChain.map((period, i) => {
              const isActive = activeDashaPlanets.has(period.lord);
              const pTheme = PLANET_THEME[period.lord];
              return (
                <div
                  key={i}
                  className="flex-shrink-0 rounded-xl px-3 py-1.5 text-center transition-all"
                  style={{
                    backgroundColor: isActive ? `${pTheme?.fill ?? "#f97316"}25` : "var(--bg-secondary)",
                    border: `1px solid ${isActive ? (pTheme?.fill ?? "#f97316") + "60" : "var(--border-primary)"}`,
                  }}
                >
                  <div className="text-xs font-bold" style={{ color: pTheme?.fill ?? "var(--text-primary)" }}>
                    {PLANET_SYMBOLS[period.lord] ?? ""} {period.lord}
                  </div>
                  <div className="text-[10px] font-medium text-slate-400 capitalize">
                    {period.level}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
