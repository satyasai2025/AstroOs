"use client";

import { useEffect, useState, useMemo, useRef } from "react";
import * as d3 from "d3";
import { NATURAL_RELATIONSHIPS, PLANET_SYMBOLS, rashiLordFromApiName } from "@/lib/astro";
import { getCurrentDashaChain } from "@/lib/kpiScoring";
import type {
  AspectSchema,
  DashaPeriodResponse,
  PlanetPositionSchema,
  WorkflowAnalysisResponse,
} from "@/lib/types";

/* ─── Types ──────────────────────────────────────────────────────── */

interface Props {
  planets: PlanetPositionSchema[];
  aspects: AspectSchema[];
  mahadashas?: DashaPeriodResponse[];
  result?: WorkflowAnalysisResponse;
  size?: number;
}

type LinkKind = "aspect" | "mutualAspect" | "friend" | "enemy" | "dispositor" | "nakshatraLord" | "conjunction" | "parivartana" | "yuddha" | "yoga" | "dasha";

interface GraphLink {
  source: string;
  target: string;
  kind: LinkKind;
  weight: number;
  label: string;
}

interface SimNode extends d3.SimulationNodeDatum {
  id: string;
  x: number;
  y: number;
  fx: number | null;
  fy: number | null;
}

/* ─── Constants ──────────────────────────────────────────────────── */

const ALL_KINDS: LinkKind[] = [
  "friend", "enemy", "aspect", "mutualAspect", "conjunction",
  "parivartana", "dispositor", "nakshatraLord", "yoga", "dasha", "yuddha",
];

const KIND_LABELS: Record<LinkKind, string> = {
  friend: "Friend", enemy: "Enemy", aspect: "Aspect",
  mutualAspect: "Mutual Aspect", conjunction: "Conjunction",
  parivartana: "Parivartana", dispositor: "Dispositor",
  nakshatraLord: "Nakshatra Lord", yoga: "Yoga", dasha: "Dasha",
  yuddha: "Yuddha",
};

const EDGE_COLORS: Record<LinkKind, string> = {
  friend: "#22c55e",
  enemy: "#ef4444",
  aspect: "#3b82f6",
  mutualAspect: "#8b5cf6",
  conjunction: "#f59e0b",
  parivartana: "#06b6d4",
  dispositor: "#6366f1",
  nakshatraLord: "#a855f7",
  yoga: "#ec4899",
  dasha: "#f97316",
  yuddha: "#dc2626",
};

/** Traditional graha colors for planet nodes */
const PLANET_THEME: Record<string, { fill: string; glow: string; stroke: string }> = {
  Sun:     { fill: "#f5a623", glow: "#f5a62340", stroke: "#d4881a" },
  Moon:    { fill: "#d4dce8", glow: "#d4dce840", stroke: "#a8b4c4" },
  Mars:    { fill: "#e04040", glow: "#e0404040", stroke: "#b03030" },
  Mercury: { fill: "#7cb342", glow: "#7cb34240", stroke: "#5a8a2a" },
  Jupiter: { fill: "#c8a050", glow: "#c8a05040", stroke: "#a07830" },
  Venus:   { fill: "#e8a0c8", glow: "#e8a0c840", stroke: "#c07898" },
  Saturn:  { fill: "#607890", glow: "#60789040", stroke: "#4a5a6a" },
  Rahu:    { fill: "#503060", glow: "#50306040", stroke: "#3a2048" },
  Ketu:    { fill: "#806880", glow: "#80688040", stroke: "#604860" },
};

const PLANET_NAMES = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"];

/* ─── Helpers ────────────────────────────────────────────────────── */

function buildGraphLinks(planets: PlanetPositionSchema[], aspects: AspectSchema[]): GraphLink[] {
  const links: GraphLink[] = [];
  const byName = new Map(planets.map((p) => [p.planet, p]));

  // Natural relationships
  for (const p of planets) {
    const nat = NATURAL_RELATIONSHIPS[p.planet];
    if (!nat) continue;
    for (const f of nat.friends) {
      if (byName.has(f)) links.push({ source: p.planet, target: f, kind: "friend", weight: 1, label: "Friend" });
    }
    for (const e of nat.enemies) {
      if (byName.has(e)) links.push({ source: p.planet, target: e, kind: "enemy", weight: 1, label: "Enemy" });
    }
  }

  // Aspects
  for (const a of aspects) {
    if (!a.from_planet || !a.to_planet) continue;
    const isMutual = aspects.some(
      (b) => b.from_planet === a.to_planet && b.to_planet === a.from_planet,
    );
    links.push({
      source: a.from_planet,
      target: a.to_planet,
      kind: isMutual ? "mutualAspect" : "aspect",
      weight: 2,
      label: `${a.aspect_type} Aspect`,
    });
  }

  // Dispositor
  for (const p of planets) {
    const lord = rashiLordFromApiName(p.rashi);
    if (lord && lord !== p.planet && byName.has(lord)) {
      links.push({ source: p.planet, target: lord, kind: "dispositor", weight: 1, label: "Dispositor" });
    }
  }

  // Nakshatra lord
  for (const p of planets) {
    if (p.nakshatra_lord && p.nakshatra_lord !== p.planet && byName.has(p.nakshatra_lord)) {
      links.push({ source: p.planet, target: p.nakshatra_lord, kind: "nakshatraLord", weight: 1, label: "Nakshatra Lord" });
    }
  }

  // Deduplicate
  const seen = new Set<string>();
  return links.filter((l) => {
    const key = [l.source, l.target, l.kind].sort().join("|");
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function angleForIndex(i: number, total: number): number {
  return (2 * Math.PI * i) / total - Math.PI / 2;
}

/* ─── SVG Defs ───────────────────────────────────────────────────── */

function SvgDefs() {
  return (
    <defs>
      {/* Glow filter */}
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

      {/* Arrowhead markers for each edge kind */}
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
          <path d="M0,0 L10,3 L0,6 Z" fill={EDGE_COLORS[kind]} opacity="0.8" />
        </marker>
      ))}

      {/* Planet gradients */}
      {Object.entries(PLANET_THEME).map(([name, t]) => (
        <radialGradient key={name} id={`v2grad-${name}`} cx="35%" cy="35%" r="65%">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.3" />
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

  // Responsive measurement — use parent container for width
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

  // Dasha chain
  const dashaChain = useMemo(
    () => (mahadashas ? getCurrentDashaChain(mahadashas) : []),
    [mahadashas],
  );
  const activeDashaPlanets = useMemo(() => {
    const s = new Set<string>();
    dashaChain.forEach((p) => s.add(p.lord));
    return s;
  }, [dashaChain]);

  // Graph links
  const allLinks = useMemo(() => buildGraphLinks(planets, aspects), [planets, aspects]);

  // Edge weight map for link thickness
  const linkWeight = useMemo(() => {
    const map = new Map<string, number>();
    allLinks.forEach((l) => {
      const key = [l.source, l.target].sort().join("|");
      map.set(key, (map.get(key) ?? 0) + l.weight);
    });
    return map;
  }, [allLinks]);

  // Filtered links
  const filteredLinks = useMemo(
    () => allLinks.filter((l) => activeKinds.has(l.kind)),
    [allLinks, activeKinds],
  );

  // ── Force simulation (synchronous — run to completion, then set positions once) ──
  useEffect(() => {
    const radius = graphSize * 0.36;
    const nodes: SimNode[] = planetNames.map((name) => {
      if (selected && name === selected) {
        return { id: name, x: center, y: center, fx: center, fy: center };
      }
      const idx = planetNames.indexOf(name);
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
      .force(
        "collision",
        d3.forceCollide().radius(graphSize * 0.12),
      )
      .force("x", d3.forceX(center).strength(selected ? 0.3 : 0.05))
      .force("y", d3.forceY(center).strength(selected ? 0.3 : 0.05))
      .alphaDecay(0.03);

    // Run simulation to completion synchronously
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

  // ── Handlers ────────────────────────────────────────────────────

  const toggleKind = (kind: LinkKind) => {
    setActiveKinds((prev) => {
      const next = new Set(prev);
      if (next.has(kind)) next.delete(kind);
      else next.add(kind);
      return next;
    });
  };

  // ── Compute curved edge path ────────────────────────────────────

  const edgePath = (sx: number, sy: number, tx: number, ty: number): string => {
    const mx = (sx + tx) / 2;
    const my = (sy + ty) / 2;
    const dx = tx - sx;
    const dy = ty - sy;
    const dist = Math.sqrt(dx * dx + dy * dy) || 1;
    // Perpendicular offset for curve
    const curveAmount = dist * 0.15;
    const cx = mx + (-dy / dist) * curveAmount;
    const cy = my + (dx / dist) * curveAmount;
    return `M${sx},${sy} Q${cx},${cy} ${tx},${ty}`;
  };

  // Midpoint of a quadratic bezier
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

  // ── Selected planet data ────────────────────────────────────────

  const selectedPlanet = useMemo(
    () => (selected ? planets.find((p) => p.planet === selected) : null),
    [selected, planets],
  );

  const selectedConnections = useMemo(() => {
    if (!selected) return [];
    return filteredLinks.filter((l) => l.source === selected || l.target === selected);
  }, [selected, filteredLinks]);

  // ── Relationship summary stats ──────────────────────────────────

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

  // ── Render ──────────────────────────────────────────────────────

  const nodeRadius = graphSize * 0.045;

  return (
    <div className="flex flex-col w-full" style={{ fontFamily: "'Inter', sans-serif" }}>
      {/* ── Header ── */}
      <div className="flex items-center justify-between mb-4 px-2">
        <div>
          <h2 className="text-xl font-bold" style={{ color: "#e2e8f0" }}>
            Planet Relationship Graph
          </h2>
          <p className="text-xs mt-1" style={{ color: "#94a3b8" }}>
            Interactive visualization of planetary relationships, aspects, and influences
          </p>
        </div>
      </div>

      {/* ── Filter toolbar ── */}
      <div className="flex flex-wrap gap-2 mb-4 px-2">
        {ALL_KINDS.map((kind) => {
          const active = activeKinds.has(kind);
          const color = EDGE_COLORS[kind];
          return (
            <button
              key={kind}
              type="button"
              onClick={() => toggleKind(kind)}
              className="flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-all"
              style={{
                backgroundColor: active ? `${color}20` : "transparent",
                color: active ? color : "#64748b",
                border: `1px solid ${active ? `${color}60` : "#1e293b"}`,
              }}
            >
              <span
                className="inline-block h-2 w-2 rounded-full"
                style={{ backgroundColor: active ? color : "#475569" }}
              />
              {KIND_LABELS[kind]}
            </button>
          );
        })}
      </div>

      {/* ── Main layout: graph + right panel ── */}
      <div className="flex gap-4 flex-1 min-h-0">
        {/* ── Graph area ── */}
        <div className="flex-1 relative min-w-0">
          {/* Zoom controls */}
          <div className="absolute top-4 left-4 z-10 flex flex-col gap-1">
            {[
              { label: "+", action: () => setZoom((z) => Math.min(z + 0.15, 2.5)) },
              { label: "−", action: () => setZoom((z) => Math.max(z - 0.15, 0.4)) },
              { label: "⤢", action: () => { setZoom(1); } },
            ].map((btn) => (
              <button
                key={btn.label}
                type="button"
                onClick={btn.action}
                className="flex h-9 w-9 items-center justify-center rounded-lg text-sm font-bold transition-colors"
                style={{
                  backgroundColor: "#1e293b",
                  color: "#94a3b8",
                  border: "1px solid #334155",
                }}
              >
                {btn.label}
              </button>
            ))}
          </div>

          {/* SVG Canvas */}
          <div ref={containerRef} style={{ width: "100%", minHeight: 400, overflow: "hidden", borderRadius: "12px", backgroundColor: "#0c1222" }}>
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
                <radialGradient id="bg-grad" cx="50%" cy="50%" r="70%">
                  <stop offset="0%" stopColor="#111d30" />
                  <stop offset="100%" stopColor="#080e1a" />
                </radialGradient>
              </defs>
              <SvgDefs />

              {/* Background */}
              <rect x="0" y="0" width={graphSize} height={graphSize} fill="url(#bg-grad)" rx="12" />

              {/* Edges */}
              {filteredLinks.map((link, i) => {
                const s = positions[link.source];
                const t = positions[link.target];
                if (!s || !t) return null;
                if (link.source === link.target) return null;

                const weight = linkWeight.get([link.source, link.target].sort().join("|")) ?? 1;
                const maxWeight = 5;
                const strokeWidth = 0.8 + (Math.min(weight, maxWeight) / maxWeight) * 1.4;

                const isDimmed = selected && link.source !== selected && link.target !== selected;
                const opacity = isDimmed ? 0.15 : 0.7;

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
                    {/* Edge label */}
                    {!isDimmed && (
                      <text
                        x={bezierMidpoint(s.x, s.y, t.x, t.y).x}
                        y={bezierMidpoint(s.x, s.y, t.x, t.y).y}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fill={EDGE_COLORS[link.kind]}
                        fontSize={9}
                        fontWeight={500}
                        opacity={0.85}
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
                    {/* Glow halo */}
                    <circle
                      cx={pos.x}
                      cy={pos.y}
                      r={r * 2.2}
                      fill={theme.glow}
                      filter="url(#v2-glow-lg)"
                      opacity={isSelected ? 0.6 : 0.3}
                    />

                    {/* Dasha ring */}
                    {isDasha && (
                      <circle
                        cx={pos.x}
                        cy={pos.y}
                        r={r + 6}
                        fill="none"
                        stroke="#f97316"
                        strokeWidth={2}
                        strokeDasharray="4 3"
                        opacity={0.7}
                      />
                    )}

                    {/* Selection ring */}
                    {isSelected && (
                      <circle
                        cx={pos.x}
                        cy={pos.y}
                        r={r + 3}
                        fill="none"
                        stroke={theme.fill}
                        strokeWidth={2}
                        opacity={0.6}
                      />
                    )}

                    {/* Planet sphere */}
                    <circle
                      cx={pos.x}
                      cy={pos.y}
                      r={r}
                      fill={`url(#v2grad-${name})`}
                      stroke={theme.stroke}
                      strokeWidth={1}
                      filter="url(#v2-glow)"
                    />

                    {/* Highlight */}
                    <circle
                      cx={pos.x - r * 0.22}
                      cy={pos.y - r * 0.22}
                      r={r * 0.5}
                      fill="white"
                      opacity={0.12}
                    />

                    {/* Label */}
                    <text
                      x={pos.x}
                      y={pos.y + r + 14}
                      textAnchor="middle"
                      fill="#c8d6e5"
                      fontSize={11}
                      fontWeight={600}
                      fontFamily="'Cinzel', serif"
                      letterSpacing="0.05em"
                    >
                      {PLANET_SYMBOLS[name] ?? ""} {name}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>

          {/* Help text */}
          <p className="mt-2 text-xs px-2" style={{ color: "#64748b" }}>
            Click a planet to center the graph on it. Use filter buttons above to show/hide relationship types.
          </p>
        </div>

        {/* ── Right panel ── */}
        <div
          className="w-72 flex-shrink-0 flex flex-col gap-4 overflow-y-auto"
          style={{ maxHeight: graphSize }}
        >
          {/* Planet info card */}
          {selectedPlanet ? (
            <div
              className="rounded-xl p-4"
              style={{ backgroundColor: "#111827", border: "1px solid #1e293b" }}
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-bold" style={{ color: "#e2e8f0" }}>
                  {PLANET_SYMBOLS[selectedPlanet.planet] ?? ""} {selectedPlanet.planet}
                </h3>
                <button
                  type="button"
                  onClick={() => setSelected(null)}
                  className="text-xs px-2 py-1 rounded"
                  style={{ color: "#64748b", backgroundColor: "#1e293b" }}
                >
                  ✕
                </button>
              </div>

              <div className="space-y-2 text-xs" style={{ color: "#94a3b8" }}>
                <div className="flex justify-between">
                  <span>Sign</span>
                  <span style={{ color: PLANET_THEME[selectedPlanet.planet]?.fill ?? "#e2e8f0" }}>
                    {selectedPlanet.rashi}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Degree</span>
                  <span style={{ color: "#e2e8f0" }}>
                    {Math.floor(selectedPlanet.sidereal_longitude % 30)}°{Math.floor(((selectedPlanet.sidereal_longitude % 1) + 1) % 1 * 60)}&apos;
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>House</span>
                  <span style={{ color: "#e2e8f0" }}>
                    {selectedPlanet.house_number ?? "—"}
                  </span>
                </div>
                {selectedPlanet.is_combust && (
                  <div className="flex justify-between">
                    <span>Combustion Orb</span>
                    <span style={{ color: "#e2e8f0" }}>{selectedPlanet.combustion_orb?.toFixed(1)}°</span>
                  </div>
                )}
              </div>

              {/* Natural relationships */}
              <div className="mt-4 pt-3" style={{ borderTop: "1px solid #1e293b" }}>
                <h4 className="text-xs font-semibold mb-2" style={{ color: "#94a3b8" }}>
                  Natural Relationships
                </h4>
                {(() => {
                  const nat = NATURAL_RELATIONSHIPS[selectedPlanet.planet];
                  if (!nat) return null;
                  return (
                    <div className="space-y-1 text-xs" style={{ color: "#94a3b8" }}>
                      {nat.friends.length > 0 && (
                        <div>
                          <span style={{ color: "#22c55e" }}>Friends:</span>{" "}
                          <span style={{ color: "#e2e8f0" }}>{nat.friends.join(", ")}</span>
                        </div>
                      )}
                      {nat.enemies.length > 0 && (
                        <div>
                          <span style={{ color: "#ef4444" }}>Enemies:</span>{" "}
                          <span style={{ color: "#e2e8f0" }}>{nat.enemies.join(", ")}</span>
                        </div>
                      )}
                      {nat.neutrals.length > 0 && (
                        <div>
                          <span style={{ color: "#94a3b8" }}>Neutrals:</span>{" "}
                          <span style={{ color: "#e2e8f0" }}>{nat.neutrals.join(", ")}</span>
                        </div>
                      )}
                    </div>
                  );
                })()}
              </div>

              {/* Connections */}
              {selectedConnections.length > 0 && (
                <div className="mt-4 pt-3" style={{ borderTop: "1px solid #1e293b" }}>
                  <h4 className="text-xs font-semibold mb-2" style={{ color: "#94a3b8" }}>
                    Connections ({selectedConnections.length})
                  </h4>
                  <div className="space-y-1.5">
                    {selectedConnections.map((c, i) => {
                      const other = c.source === selected ? c.target : c.source;
                      return (
                        <div key={i} className="flex items-center gap-2 text-xs">
                          <span
                            className="inline-block h-2 w-2 rounded-full flex-shrink-0"
                            style={{ backgroundColor: EDGE_COLORS[c.kind] }}
                          />
                          <span style={{ color: EDGE_COLORS[c.kind] }}>{c.label}</span>
                          <span style={{ color: "#64748b" }}>→</span>
                          <span style={{ color: "#e2e8f0" }}>{other}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div
              className="rounded-xl p-4 text-center"
              style={{ backgroundColor: "#111827", border: "1px solid #1e293b" }}
            >
              <p className="text-xs" style={{ color: "#64748b" }}>
                Click a planet to see its details
              </p>
            </div>
          )}

          {/* Graph Controls */}
          <div
            className="rounded-xl p-4"
            style={{ backgroundColor: "#111827", border: "1px solid #1e293b" }}
          >
            <h4 className="text-xs font-semibold mb-3" style={{ color: "#94a3b8" }}>
              Graph Controls
            </h4>
            <div className="space-y-2">
              {[
                { label: "Zoom", value: `${Math.round(zoom * 100)}%` },
                { label: "Edges", value: `${filteredLinks.length} / ${allLinks.length}` },
                { label: "Planets", value: `${planets.length}` },
              ].map((item) => (
                <div key={item.label} className="flex justify-between text-xs">
                  <span style={{ color: "#64748b" }}>{item.label}</span>
                  <span style={{ color: "#e2e8f0" }}>{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Bottom summary cards ── */}
      <div className="grid grid-cols-3 gap-4 mt-4 px-2">
        {/* Relationship Summary */}
        <div
          className="rounded-xl p-4"
          style={{ backgroundColor: "#111827", border: "1px solid #1e293b" }}
        >
          <h4 className="text-xs font-semibold mb-3" style={{ color: "#94a3b8" }}>
            Relationship Summary
          </h4>
          <div className="space-y-2 text-xs">
            {[
              { label: "Friends", count: summaryStats.friend, color: "#22c55e" },
              { label: "Enemies", count: summaryStats.enemy, color: "#ef4444" },
              { label: "Aspects", count: summaryStats.aspect, color: "#3b82f6" },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full" style={{ backgroundColor: item.color }} />
                  <span style={{ color: "#94a3b8" }}>{item.label}</span>
                </div>
                <span style={{ color: "#e2e8f0" }}>
                  {item.count} ({summaryStats.total > 0 ? Math.round((item.count / summaryStats.total) * 100) : 0}%)
                </span>
              </div>
            ))}
          </div>
          <div className="mt-3 pt-2" style={{ borderTop: "1px solid #1e293b" }}>
            <span className="text-xs" style={{ color: "#64748b" }}>
              Total Relationships: {summaryStats.total}
            </span>
          </div>
        </div>

        {/* Influence Strength */}
        <div
          className="rounded-xl p-4"
          style={{ backgroundColor: "#111827", border: "1px solid #1e293b" }}
        >
          <h4 className="text-xs font-semibold mb-3" style={{ color: "#94a3b8" }}>
            Influence Strength
          </h4>
          <div className="space-y-3 text-xs">
            {[
              { label: "Natural Friends", pct: summaryStats.friend > 0 ? 85 : 30, color: "#22c55e" },
              { label: "Aspects", pct: summaryStats.aspect > 0 ? 72 : 40, color: "#3b82f6" },
              { label: "Dasha Active", pct: activeDashaPlanets.size > 0 ? 90 : 20, color: "#f97316" },
            ].map((item) => (
              <div key={item.label}>
                <div className="flex justify-between mb-1">
                  <span style={{ color: "#94a3b8" }}>{item.label}</span>
                  <span style={{ color: "#e2e8f0" }}>{item.pct}%</span>
                </div>
                <div className="h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: "#1e293b" }}>
                  <div
                    className="h-full rounded-full"
                    style={{ width: `${item.pct}%`, backgroundColor: item.color }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Key Insights */}
        <div
          className="rounded-xl p-4"
          style={{ backgroundColor: "#111827", border: "1px solid #1e293b" }}
        >
          <h4 className="text-xs font-semibold mb-3" style={{ color: "#94a3b8" }}>
            Key Insights
          </h4>
          <div className="space-y-2 text-xs" style={{ color: "#94a3b8" }}>
            {filteredLinks.length > 0 && (
              <p>
                <span style={{ color: "#22c55e" }}>✦</span>{" "}
                {filteredLinks.filter((l) => l.kind === "friend").length > 0
                  ? `${filteredLinks.filter((l) => l.kind === "friend").length} natural friendship connections detected.`
                  : "No natural friendships in current filter."}
              </p>
            )}
            {activeDashaPlanets.size > 0 && (
              <p>
                <span style={{ color: "#f97316" }}>✦</span>{" "}
                Active dasha periods: {[...activeDashaPlanets].join(", ")}.
              </p>
            )}
            <p>
              <span style={{ color: "#3b82f6" }}>✦</span>{" "}
              {filteredLinks.filter((l) => l.kind === "aspect" || l.kind === "mutualAspect").length} aspect connections visualized.
            </p>
          </div>
        </div>
      </div>

      {/* ── Dasha Timeline ── */}
      {dashaChain.length > 0 && (
        <div
          className="rounded-xl p-4 mt-4 mx-2"
          style={{ backgroundColor: "#111827", border: "1px solid #1e293b" }}
        >
          <div className="flex items-center justify-between mb-2">
            <div>
              <h4 className="text-xs font-semibold" style={{ color: "#94a3b8" }}>
                Dasha Timeline
              </h4>
              <span className="text-[10px]" style={{ color: "#64748b" }}>
                Vimshottari Dasha
              </span>
            </div>
            <span
              className="text-[10px] px-2 py-0.5 rounded"
              style={{ backgroundColor: "#1e293b", color: "#f97316" }}
            >
              Active
            </span>
          </div>
          <div className="flex gap-1 overflow-x-auto pb-1">
            {dashaChain.map((period, i) => {
              const isActive = activeDashaPlanets.has(period.lord);
              return (
                <div
                  key={i}
                  className="flex-shrink-0 rounded-lg px-3 py-1.5 text-center"
                  style={{
                    backgroundColor: isActive ? `${PLANET_THEME[period.lord]?.fill ?? "#f97316"}20` : "#0f172a",
                    border: `1px solid ${isActive ? (PLANET_THEME[period.lord]?.fill ?? "#f97316") + "60" : "#1e293b"}`,
                  }}
                >
                  <div className="text-[10px] font-semibold" style={{ color: PLANET_THEME[period.lord]?.fill ?? "#e2e8f0" }}>
                    {period.lord}
                  </div>
                  <div className="text-[9px]" style={{ color: "#64748b" }}>
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
