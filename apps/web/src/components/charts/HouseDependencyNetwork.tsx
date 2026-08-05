"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import * as d3 from "d3";
import { PLANET_SYMBOLS, rashiLordFromApiName } from "@/lib/astro";
import type { HouseCuspSchema, PlanetPositionSchema, PlanetStrengthSchema } from "@/lib/types";

export interface HouseDependencyNetworkProps {
  houses: HouseCuspSchema[];
  planetStrengths: PlanetStrengthSchema[];
  planets: PlanetPositionSchema[];
  // Optional external filter control
  activeKinds?: Set<EdgeKind>;
  onFilterChange?: (kinds: Set<EdgeKind>) => void;
  // Optional external selection control
  selectedHouse?: number | null;
  onHouseSelect?: (house: number | null) => void;
}

// ── EDGE TYPES ──────────────────────────────────────────────────────────────
type EdgeKind = "lordship" | "aspect" | "parivartana" | "argala" | "trinal" | "angular" | "dusthana" | "functional" | "maraka";

// Shared fallback for missing houses (when input data lacks a house_number)
// Prevents "Cannot read properties of undefined" crashes downstream.
const EMPTY_HOUSE_INFO = {
  houseNumber: 0,
  rashi: null,
  lord: null,
  lordPlacementHouse: null,
  lordStrength: null as PlanetStrengthSchema | null,
  occupants: [] as PlanetPositionSchema[],
  weak: false,
  weakReasons: [] as string[],
} as const;

interface HouseEdge {
  id: string;
  from: number;
  to: number;
  kind: EdgeKind;
  lord: string;
  label: string;
  weak: boolean;
  strengthScore: number;
  description: string;
}

const EDGE_KIND_LABEL: Record<EdgeKind, string> = {
  lordship: "Lordship",
  aspect: "Aspect",
  parivartana: "Parivartana",
  argala: "Argala",
  trinal: "Trinal",
  angular: "Angular",
  dusthana: "Dusthana",
  functional: "Functional",
  maraka: "Maraka",
};

const EDGE_COLORS: Record<EdgeKind, string> = {
  lordship: "#F5A623",        // gold
  aspect: "#8B5CF6",          // violet
  parivartana: "#06CFFF",     // cyan
  argala: "#22C55E",          // green
  trinal: "#FBBF24",          // yellow
  angular: "#3B82F6",         // blue
  dusthana: "#EF4444",        // red
  functional: "#EC4899",      // pink
  maraka: "#F97316",          // orange
};

// ── NODE THEME ──────────────────────────────────────────────────────────────
const WEAK_STRENGTH_THRESHOLD = 4;
const HOUSE_RADIUS = 22; // base circle radius when not selected
const SELECTED_RADIUS_BOOST = 6; // +6 = 28 when selected

// ── SVG FILTERS ──────────────────────────────────────────────────────────────
const SvgDefs = () => (
  <defs>
    {/* Glow filter for edges and nodes */}
    <filter id="glow-sm" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="5" result="blur" />
      <feMerge>
        <feMergeNode in="blur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>
    <filter id="glow-lg" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="12" result="blur" />
      <feMerge>
        <feMergeNode in="blur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>

    {/* Background radial gradient */}
    <radialGradient id="bg-grad" cx="50%" cy="50%" r="70%">
      <stop offset="0%" stopColor="#111d30" />
      <stop offset="100%" stopColor="#080e1a" />
    </radialGradient>

    {/* Per-house sphere gradients will be created dynamically in SVG */}
    {Array.from({ length: 12 }, (_, i) => i + 1).map((h) => {
      const sign = [
        "", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
      ][h];
      const hue = (h * 30 - 90) % 360; // simple rainbow spread for visual variety
      const fill = `hsl(${hue}, 70%, 50%)`;
      const stroke = `hsl(${hue}, 80%, 40%)`;
      return (
        <radialGradient key={h} id={`house-grad-${h}`} cx="35%" cy="35%" r="65%">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.3" />
          <stop offset="40%" stopColor={fill} stopOpacity="1" />
          <stop offset="100%" stopColor={stroke} stopOpacity="1" />
        </radialGradient>
      );
    })}

    {/* Arrow markers for each edge kind */}
    {(Object.keys(EDGE_COLORS) as EdgeKind[]).map((kind) => (
      <marker
        key={kind}
        id={`arrow-${kind}`}
        viewBox="0 0 10 10"
        refX="9"
        refY="5"
        markerWidth="6"
        markerHeight="6"
        orient="auto-start-reverse"
      >
        <path d="M0,0 L10,5 L0,10 z" fill={EDGE_COLORS[kind]} />
      </marker>
    ))}
  </defs>
);

// ── FORCE-DIRECTED LAYOUT ───────────────────────────────────────────────────
function useForceSimulation(
  nodes: { id: number }[],
  links: { source: number; target: number }[],
  selected: number | null,
  width: number
) {
  return useMemo(() => {
    if (!nodes.length || width <= 0) return new Map<number, { x: number; y: number }>();

    const center = width / 2;
    const radius = width * 0.36;

    // Initialize positions in a circle
    const initial = new Map<number, { x: number; y: number }>();
    nodes.forEach((n, i) => {
      if (selected && n.id === selected) {
        initial.set(n.id, { x: center, y: center });
      } else {
        const angle = (i / nodes.length) * 2 * Math.PI - Math.PI / 2;
        initial.set(n.id, {
          x: center + radius * Math.cos(angle),
          y: center + radius * Math.sin(angle),
        });
      }
    });

    // Convert to d3 format with x,y
    const simNodes = nodes.map((n) => ({
      ...n,
      x: initial.get(n.id)!.x,
      y: initial.get(n.id)!.y,
      ...(selected && n.id === selected ? { fx: center, fy: center } : {}),
    }));

    const sim = d3
      .forceSimulation(simNodes as any)
      .force(
        "link",
        d3.forceLink(links as any).id((d: any) => d.id).distance(width * 0.28).strength(0.6)
      )
      .force("charge", d3.forceManyBody().strength(-width * 0.4))
      .force("center", d3.forceCenter(center, center).strength(selected ? 0 : 0.8))
      .force("collision", d3.forceCollide().radius(width * 0.12))
      .force("x", d3.forceX(center).strength(selected ? 0.3 : 0.05))
      .force("y", d3.forceY(center).strength(selected ? 0.3 : 0.05))
      .alphaDecay(0.03);

    sim.tick(300);
    sim.stop();

    const pos = new Map<number, { x: number; y: number }>();
    const margin = width * 0.1;
    simNodes.forEach((n) => {
      pos.set(n.id, {
        x: Math.max(margin, Math.min(width - margin, n.x ?? center)),
        y: Math.max(margin, Math.min(width - margin, n.y ?? center)),
      });
    });
    return pos;
  }, [nodes, links, selected, width]);
}

// ── HELPER: QUADRATIC BEZIER PATH ───────────────────────────────────────────
const edgePath = (
  sx: number, sy: number,
  tx: number, ty: number,
  curveFactor = 0.15
): string => {
  const mx = (sx + tx) / 2;
  const my = (sy + ty) / 2;
  const dx = tx - sx;
  const dy = ty - sy;
  const dist = Math.sqrt(dx * dx + dy * dy) || 1;
  const curveAmount = dist * curveFactor;
  // Perpendicular offset
  const cx = mx + (-dy / dist) * curveAmount;
  const cy = my + (dx / dist) * curveAmount;
  return `M${sx},${sy} Q${cx},${cy} ${tx},${ty}`;
};

// ── HOUSE DATA COMPUTATION ───────────────────────────────────────────────────
const HOUSE_BHAVA: Record<number, { name: string; area: string }> = {
  1: { name: "Tanu Bhava", area: "Self, body, personality" },
  2: { name: "Dhana Bhava", area: "Wealth, family, speech" },
  3: { name: "Sahaja Bhava", area: "Siblings, courage, effort" },
  4: { name: "Sukha Bhava", area: "Home, mother, comforts" },
  5: { name: "Putra Bhava", area: "Children, intellect, creativity" },
  6: { name: "Ripu/Roga Bhava", area: "Enemies, disease, service" },
  7: { name: "Kalatra Bhava", area: "Marriage, partnerships" },
  8: { name: "Mrityu Bhava", area: "Longevity, occult, transformation" },
  9: { name: "Bhagya Bhava", area: "Dharma, fortune, higher learning" },
  10: { name: "Karma Bhava", area: "Career, status, reputation" },
  11: { name: "Labha Bhava", area: "Gains, aspirations, friends" },
  12: { name: "Vyaya Bhava", area: "Losses, confinement, spirituality" },
};

function ordinal(n: number): string {
  const s = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return n + (s[(v - 20) % 10] ?? s[v] ?? s[0]);
}

function houseRef(n: number): string {
  return n === 1 ? "Lagna (1st)" : `${ordinal(n)} house`;
}

function wrapHouse(n: number): number {
  return (((n - 1) % 12) + 12) % 12 + 1;
}

/**
 * Which houses a planet aspects FROM a given placement house, using the
 * classical whole-sign (Rashi Drishti) counting convention. All planets
 * get the universal 7th-house aspect; Mars, Jupiter and Saturn
 * additionally get their special aspects.
 */
function aspectedHousesFromPlacement(planet: string, placementHouse: number): number[] {
  const houses = new Set<number>();
  houses.add(wrapHouse(placementHouse + 6)); // 7th — universal
  if (planet === "Mars") {
    houses.add(wrapHouse(placementHouse + 3)); // 4th
    houses.add(wrapHouse(placementHouse + 7)); // 8th
  } else if (planet === "Jupiter") {
    houses.add(wrapHouse(placementHouse + 4)); // 5th
    houses.add(wrapHouse(placementHouse + 8)); // 9th
  } else if (planet === "Saturn") {
    houses.add(wrapHouse(placementHouse + 2)); // 3rd
    houses.add(wrapHouse(placementHouse + 9)); // 10th
  }
  return [...houses];
}

// ── MAIN COMPONENT ──────────────────────────────────────────────────────────
export function HouseDependencyNetwork({
  houses,
  planetStrengths,
  planets,
  activeKinds: externalActiveKinds,
  onFilterChange,
  selectedHouse: externalSelectedHouse,
  onHouseSelect,
}: HouseDependencyNetworkProps) {
  const [internalSelected, setInternalSelected] = useState<number | null>(null);
  const [hoveredEdge, setHoveredEdge] = useState<HouseEdge | null>(null);

  // Default all kinds including maraka
  const ALL_KINDS: EdgeKind[] = [
    "lordship", "aspect", "parivartana", "argala", "trinal", "angular", "dusthana", "functional", "maraka"
  ];

  // Use external filter state if provided, otherwise internal
  const [internalActiveKinds, setInternalActiveKinds] = useState<Set<EdgeKind>>(new Set(ALL_KINDS));
  const activeKinds = externalActiveKinds ?? internalActiveKinds;
  const setActiveKinds = onFilterChange ?? setInternalActiveKinds;

  // Use external selection if provided, otherwise internal
  const selected = externalSelectedHouse ?? internalSelected;
  const setSelected = onHouseSelect ?? setInternalSelected;

  const [zoom, setZoom] = useState(1);

  // ── Responsive container width ───────────────────────────────────────────
  const containerRef = useRef<HTMLDivElement>(null);
  const [graphWidth, setGraphWidth] = useState(600);

  useEffect(() => {
    const el = containerRef.current?.parentElement;
    if (!el) return;
    const obs = new ResizeObserver(([entry]) => {
      const w = entry.contentRect.width;
      if (w > 100) setGraphWidth(Math.floor(w));
    });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  // ── House info & lord strength helpers ────────────────────────────────────
  const houseInfoByNumber = useMemo(() => {
    const byNum = new Map<number, HouseCuspSchema>();
    houses.forEach((h) => byNum.set(h.house_number, h));
    const lordOf = new Map<string, string>();
    houses.forEach((h) => {
      const lord = rashiLordFromApiName(h.rashi);
      if (lord) lordOf.set(h.rashi, lord);
    });

    const lordStrength = new Map<string, PlanetStrengthSchema | null>();
    planetStrengths.forEach((ps) => lordStrength.set(ps.planet, ps));

    const inHouse = new Map<string, number[]>(); // planet -> [house numbers]
    planets.forEach((p) => {
      const list = inHouse.get(p.planet) || [];
      list.push(p.house_number);
      inHouse.set(p.planet, list);
    });

    const infoMap = new Map<number, {
      houseNumber: number;
      rashi: string | null;
      lord: string | null;
      lordPlacementHouse: number | null;
      lordStrength: PlanetStrengthSchema | null;
      occupants: PlanetPositionSchema[];
      weak: boolean;
      weakReasons: string[];
    }>();

    for (let h = 1; h <= 12; h++) {
      const house = byNum.get(h);
      if (!house) continue;
      const rashi = house.rashi;
      const lord = rashiLordFromApiName(rashi);
      const lordPos = inHouse.get(lord || "") || [];
      const lordHouse = lordPos.length > 0 ? lordPos[0] : null;
      const lordStr = lord ? lordStrength.get(lord) ?? null : null;
      const occs = planets.filter((p) => p.house_number === h);
      const weak = !!lordStr && (
        lordStr.dignity === "debilitated" ||
        [6, 8, 12].includes(lordHouse || 0) ||
        (lordStr.strength_score ?? 0) < WEAK_STRENGTH_THRESHOLD
      );
      const reasons: string[] = [];
      if (lordStr) {
        if (lordStr.dignity === "debilitated") reasons.push("Lord debilitated");
        if (lordHouse && [6, 8, 12].includes(lordHouse)) reasons.push("Lord in dusthana");
        if ((lordStr.strength_score ?? 0) < WEAK_STRENGTH_THRESHOLD) reasons.push("Low strength");
      }
      infoMap.set(h, {
        houseNumber: h,
        rashi,
        lord,
        lordPlacementHouse: lordHouse,
        lordStrength: lordStr,
        occupants: occs,
        weak,
        weakReasons: reasons,
      });
    }
    return infoMap;
  }, [houses, planets, planetStrengths]);

  // ── EDGE GENERATION ───────────────────────────────────────────────────────
  const allEdges = useMemo<HouseEdge[]>(() => {
    const edges: HouseEdge[] = [];

    // `get(h)` may be undefined when the house data is missing a given
    // house_number (the builder loop above `continue`s past absent houses).
    // Return a benign default so every `if (!x.lord) continue` guard below
    // handles missing houses gracefully instead of throwing.
    const info = (h: number) => houseInfoByNumber.get(h) ?? EMPTY_HOUSE_INFO;
    const score = (ps: PlanetStrengthSchema | null) => ps?.strength_score ?? 5;

    // 1. Lordship placement edges (original "placement")
    for (let h = 1; h <= 12; h++) {
      const ih = info(h);
      if (!ih.lord) continue;
      const targetHouse = ih.lordPlacementHouse;
      if (!targetHouse) continue;
      // Avoid self-loops; usually placement of lord in same house
      if (targetHouse === h) continue;

      const targetInfo = info(targetHouse);
      const targetLord = targetInfo.lord;
      const isParivartana = targetLord && targetInfo.lordPlacementHouse === h;

      const isWeak = ih.weak || targetInfo.weak;
      edges.push({
        id: `${h}-lordship->${targetHouse}`,
        from: h,
        to: targetHouse,
        kind: isParivartana ? "parivartana" : "lordship",
        lord: ih.lord,
        label: `${ordinal(h)} lord (${ih.lord}) in ${houseRef(targetHouse)}`,
        weak: isWeak,
        strengthScore: score(ih.lordStrength),
        description: isParivartana
          ? `${ih.lord} and ${targetInfo.lord} exchange houses (Parivartana Yoga) — mutual reinforcement.`
          : `${ih.lord} placed in ${houseRef(targetHouse)} influences that domain.`,
      });
    }

    // 2. Aspect edges (Rashi Drishti)
    for (let h = 1; h <= 12; h++) {
      const ih = info(h);
      const ihLord = ih.lord;
      if (!ihLord) continue;
      const aspects = aspectedHousesFromPlacement(ihLord, h);
      aspects.forEach((target) => {
        const targetInfo = info(target);
        const isWeak = ih.weak || targetInfo.weak;
        edges.push({
          id: `${h}-aspect->${target}`,
          from: h,
          to: target,
          kind: "aspect",
          lord: ihLord,
          label: `${ordinal(h)} lord (${ihLord}) aspects ${houseRef(target)}`,
          weak: isWeak,
          strengthScore: score(ih.lordStrength),
          description: `${ihLord} casts a classical aspect on ${houseRef(target)}.`,
        });
      });
    }

    // 3. Trinal relationships (1-5-9, 2-6-10, 3-7-11, 4-8-12)
    const trinalGroups = [[1, 5, 9], [2, 6, 10], [3, 7, 11], [4, 8, 12]];
    trinalGroups.forEach((group) => {
      group.forEach((from) => {
        group.forEach((to) => {
          if (from === to) return;
          const fromInfo = info(from);
          if (!fromInfo.lord) return;
          const toInfo = info(to);
          const isWeak = fromInfo.weak || toInfo.weak;
          edges.push({
            id: `trinal-${from}->${to}`,
            from,
            to,
            kind: "trinal",
            lord: fromInfo.lord,
            label: `Trinal support: ${fromInfo.lord} (${ordinal(from)}) → ${toInfo.lord} (${ordinal(to)})`,
            weak: isWeak,
            strengthScore: score(fromInfo.lordStrength),
            description: `${fromInfo.lord} (${ordinal(from)}) and ${toInfo.lord} (${ordinal(to)}) are in a harmonious trinal relationship (1-5-9 pattern).`,
          });
        });
      });
    });

    // 4. Angular relationships (Kendras: 1-4-7-10)
    const kendras = [1, 4, 7, 10];
    kendras.forEach((from) => {
      kendras.forEach((to) => {
        if (from === to) return;
        const fromInfo = info(from);
        if (!fromInfo.lord) return;
        const toInfo = info(to);
        const isWeak = fromInfo.weak || toInfo.weak;
        edges.push({
          id: `angular-${from}->${to}`,
          from,
          to,
          kind: "angular",
          lord: fromInfo.lord,
          label: `Angular link: ${ordinal(from)} → ${ordinal(to)}`,
          weak: isWeak,
          strengthScore: score(fromInfo.lordStrength),
          description: `Angular (Kendra) relationship between ${ordinal(from)} and ${ordinal(to)} — creates significant life impact.`,
        });
      });
    });

    // 5. Dusthana relationships (6-8-12 triad)
    const dusthanas = [6, 8, 12];
    dusthanas.forEach((from) => {
      dusthanas.forEach((to) => {
        if (from === to) return;
        const fromInfo = info(from);
        if (!fromInfo.lord) return;
        const toInfo = info(to);
        edges.push({
          id: `dusthana-${from}->${to}`,
          from,
          to,
          kind: "dusthana",
          lord: fromInfo.lord,
          label: `Dusthana tension: ${ordinal(from)} → ${ordinal(to)}`,
          weak: false,
          strengthScore: score(fromInfo.lordStrength),
          description: `Connection between challenging houses (${ordinal(from)} and ${ordinal(to)}) — can indicate struggles or transformation.`,
        });
      });
    });

    // 6. Argala: 2nd, 4th, 11th from a house intervene
    for (let h = 1; h <= 12; h++) {
      const ih = info(h);
      const ihLord = ih.lord;
      if (!ihLord) continue;
      [2, 4, 11].forEach((offset) => {
        const target = wrapHouse(h + offset - 1);
        const targetInfo = info(target);
        edges.push({
          id: `argala-${h}->${target}`,
          from: h,
          to: target,
          kind: "argala",
          lord: ihLord,
          label: `${ihLord} (${ordinal(h)}) gives Argala to ${ordinal(target)}`,
          weak: ih.weak || targetInfo.weak,
          strengthScore: score(ih.lordStrength),
          description: `Argala (intervention): ${ihLord} in ${ordinal(h)} actively supports/protects ${ordinal(target)}.`,
        });
      });
    }

    // 7. Functional relationships: based on natural friendships and specific house lordships
    // Example: 1st lord aspects 10th lord => functional relationship
    for (let h = 1; h <= 12; h++) {
      const ih = info(h);
      if (!ih.lord) continue;
      const targetLordPlacement = ih.lordPlacementHouse;
      if (!targetLordPlacement) continue;
      // Check if the lord of the target house aspects the current house
      const targetInfo = info(targetLordPlacement);
      if (!targetInfo.lord) continue;
      const targetAspects = aspectedHousesFromPlacement(targetInfo.lord, targetLordPlacement);
      if (targetAspects.includes(h)) {
        edges.push({
          id: `functional-${h}<-${targetLordPlacement}`,
          from: targetLordPlacement,
          to: h,
          kind: "functional",
          lord: targetInfo.lord,
          label: `Functional link: ${targetInfo.lord} (${ordinal(targetLordPlacement)}) → ${ordinal(h)}`,
          weak: ih.weak || targetInfo.weak,
          strengthScore: score(targetInfo.lordStrength),
          description: `Natural functional relationship: ${targetInfo.lord} influences ${ordinal(h)} via combined lordship and aspect.`,
        });
      }
    }

    // 8. Maraka relationships: 2nd and 7th houses are maraka (death-inflicting)
    // Their lords and planets placed there create maraka influences
    const marakaHouses = [2, 7];
    marakaHouses.forEach((from) => {
      const fromInfo = info(from);
      if (!fromInfo.lord) return;
      // Maraka lord aspects other houses
      const aspects = aspectedHousesFromPlacement(fromInfo.lord, from);
      aspects.forEach((target) => {
        const targetInfo = info(target);
        edges.push({
          id: `maraka-${from}->${target}`,
          from,
          to: target,
          kind: "maraka",
          lord: fromInfo.lord,
          label: `Maraka ${ordinal(from)} lord (${fromInfo.lord}) aspects ${ordinal(target)}`,
          weak: fromInfo.weak || targetInfo.weak,
          strengthScore: score(fromInfo.lordStrength),
          description: `${fromInfo.lord} as maraka lord of ${ordinal(from)} house influences ${ordinal(target)} — can trigger transformative events.`,
        });
      });
      // Maraka house to maraka house connection
      marakaHouses.forEach((to) => {
        if (from === to) return;
        const toInfo = info(to);
        if (!toInfo.lord) return;
        edges.push({
          id: `maraka-${from}->${to}`,
          from,
          to,
          kind: "maraka",
          lord: fromInfo.lord,
          label: `Maraka link: ${ordinal(from)} ↔ ${ordinal(to)}`,
          weak: fromInfo.weak || toInfo.weak,
          strengthScore: score(fromInfo.lordStrength),
          description: `Connection between the two maraka houses (${ordinal(from)} and ${ordinal(to)}) — intensifies maraka effects.`,
        });
      });
    });

    return edges;
  }, [houseInfoByNumber]);

  // ── Filter edges ──────────────────────────────────────────────────────────
  const edges = useMemo(() => allEdges.filter((e) => activeKinds.has(e.kind)), [allEdges, activeKinds]);

  // ── FORCE-SIMULATION LAYOUT ───────────────────────────────────────────────
  const graphSize = graphWidth;
  const nodeIds = Array.from({ length: 12 }, (_, i) => i + 1);
  const linkObjs = useMemo(() => edges.map((e) => ({ source: e.from, target: e.to })), [edges]);
  const positions = useForceSimulation(nodeIds.map((id) => ({ id })), linkObjs, selected, graphSize);

  // ── FILTER TOGGLE ─────────────────────────────────────────────────────────
  const toggleKind = (kind: EdgeKind) => {
    setActiveKinds((prev) => {
      const next = new Set(prev);
      if (next.has(kind)) next.delete(kind);
      else next.add(kind);
      return next;
    });
  };

  // ── COMPUTED STATE FOR RENDERING ──────────────────────────────────────────
  const activeInfo = selected ? houseInfoByNumber.get(selected) : null;
  const outgoing = selected ? edges.filter((e) => e.from === selected) : [];
  const incoming = selected ? edges.filter((e) => e.to === selected && e.from !== selected) : [];

  const isConnected = (h: number) =>
    selected !== null && edges.some((e) => (e.from === selected && e.to === h) || (e.to === selected && e.from === h));

  // Edge thickness based on strength
  const edgeStrokeWidth = (strengthScore: number) => 0.8 + (strengthScore / 10) * 1.4; // 0.8-2.2

  // ── RENDER ─────────────────────────────────────────────────────────────────
  return (
    <div
      className="glass-card flex w-full max-w-7xl flex-col gap-4 p-4 lg:flex-row"
      style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)" }}
    >
      {/* ── LEFT: Graph area ───────────────────────────────────────────────── */}
      <div className="flex flex-1 flex-col gap-3">
        {/* Top: filter toolbar */}
        <div className="flex w-full items-center justify-between gap-2">
          <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
            House Dependency Network
          </h3>
          {selected && (
            <button
              type="button"
              onClick={() => setSelected(null)}
              className="text-xs transition hover:underline"
              style={{ color: "var(--text-muted)" }}
            >
              Clear selection
            </button>
          )}
        </div>

        <div className="flex flex-wrap gap-1.5">
          {/* All Relationships toggle */}
          <button
            type="button"
            onClick={() => {
              const allKinds = Object.keys(EDGE_KIND_LABEL) as EdgeKind[];
              const allActive = allKinds.every((k) => activeKinds.has(k));
              setActiveKinds(allActive ? new Set() : new Set(allKinds));
            }}
            className={`px-2.5 py-1 text-xs font-medium rounded-full border transition-all ${
              activeKinds.size === Object.keys(EDGE_KIND_LABEL).length
                ? "bg-cyan-500/20 border-cyan-400 text-cyan-300 shadow-[0_0_12px_rgba(6,182,212,0.3)]"
                : "bg-transparent border-var(--border-primary) text-gray-400 hover:border-gray-500"
            }`}
          >
            All Relationships
          </button>
          {(Object.keys(EDGE_KIND_LABEL) as EdgeKind[]).map((kind) => {
            const active = activeKinds.has(kind);
            const count = allEdges.filter((e) => e.kind === kind).length;
            return (
              <button
                key={kind}
                type="button"
                onClick={() => toggleKind(kind)}
                disabled={count === 0}
                className={`px-2.5 py-1 text-xs font-medium rounded-full border transition-all ${
                  active
                    ? "bg-cyan-500/20 border-cyan-400 text-cyan-300 shadow-[0_0_12px_rgba(6,182,212,0.3)]"
                    : "bg-transparent border-var(--border-primary) text-gray-400 hover:border-gray-500"
                }`}
              >
                {EDGE_KIND_LABEL[kind]} ({count})
              </button>
            );
          })}
        </div>

        {/* Graph canvas */}
        <div ref={containerRef} className="relative flex-1 min-h-[500px] overflow-hidden rounded-lg bg-black">
          {/* Dark background gradient */}
          <div
            className="absolute inset-0"
            style={{
              background: "radial-gradient(ellipse at center, #121824 0%, #080e1a 100%)",
            }}
          />

          {/* Zoom controls */}
          <div className="absolute left-4 top-4 z-10 flex flex-col gap-1">
            {[
              { label: "+", action: () => setZoom((z) => Math.min(z + 0.15, 2.5)) },
              { label: "−", action: () => setZoom((z) => Math.max(z - 0.15, 0.4)) },
              { label: "⟲", action: () => { setZoom(1); setSelected(null); } },
            ].map((btn) => (
              <button
                key={btn.label}
                type="button"
                onClick={btn.action}
                className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#1e293b] text-[#94a3b8] text-sm font-bold border border-[#334155] shadow-lg transition"
              >
                {btn.label}
              </button>
            ))}
          </div>

          <svg
            width={graphSize}
            height={graphSize}
            viewBox={`0 0 ${graphSize} ${graphSize}`}
            style={{
              transform: `scale(${zoom})`,
              transformOrigin: "center center",
              transition: "transform 0.3s ease",
            }}
            role="img"
            aria-label="House dependency network"
          >
            <SvgDefs />

            {/* Edges */}
            {edges.map((edge, idx) => {
              const s = positions.get(edge.from);
              const t = positions.get(edge.to);
              if (!s || !t) return null;
              if (edge.from === edge.to) return null;

              const dimmed = selected && !isConnected(edge.from) && !isConnected(edge.to);
              const opacity = dimmed ? 0.15 : 0.7;

              // Label position: bezier midpoint
              const mid = (() => {
                const mx = (s.x + t.x) / 2;
                const my = (s.y + t.y) / 2;
                const curve = edgePath(s.x, s.y, t.x, t.y);
                // Approximate point at 50% along the curve
                return { x: mx, y: my };
              })();

              return (
                <g key={edge.id} className="transition-opacity duration-300" style={{ opacity }}>
                  {/* Edge line */}
                  <path
                    d={edgePath(s.x, s.y, t.x, t.y)}
                    fill="none"
                    stroke={EDGE_COLORS[edge.kind]}
                    strokeWidth={edgeStrokeWidth(edge.strengthScore)}
                    strokeOpacity={opacity}
                    markerEnd={`url(#arrow-${edge.kind})`}
                    style={{ filter: "url(#glow-sm)", transition: "stroke-opacity 0.3s" }}
                    className="cursor-pointer"
                    onMouseEnter={() => setHoveredEdge(edge)}
                    onMouseLeave={() => setHoveredEdge(null)}
                  />
                  {/* Edge label */}
                  {!dimmed && (
                    <foreignObject x={mid.x - 50} y={mid.y - 10} width={100} height={20}>
                      <div
                        className="flex items-center justify-center text-[10px] font-mono text-white rounded-full border px-1.5 truncate"
                        style={{
                          backgroundColor: "rgba(18, 24, 36, 0.9)",
                          borderColor: EDGE_COLORS[edge.kind],
                          borderWidth: "1px",
                        }}
                      >
                        {edge.label}
                      </div>
                    </foreignObject>
                  )}
                </g>
              );
            })}

            {/* House nodes */}
            {nodeIds.map((h) => {
              const pos = positions.get(h);
              if (!pos) return null;
              const info = houseInfoByNumber.get(h) ?? EMPTY_HOUSE_INFO;
              const isSelected = selected === h;
              const connected = isSelected || isConnected(h);
              const dimmed = selected && !connected;
              const r = isSelected ? HOUSE_RADIUS + SELECTED_RADIUS_BOOST : HOUSE_RADIUS;
              const labelColor = selected && dimmed ? "var(--text-muted)" : "var(--text-primary)";

              return (
                <g
                  key={h}
                  transform={`translate(${pos.x},${pos.y})`}
                  style={{ cursor: "pointer", transition: "opacity 0.3s" }}
                  opacity={dimmed ? 0.25 : 1}
                  onClick={() => setSelected(isSelected ? null : h)}
                >
                  {/* Glow halo */}
                  <circle
                    r={r * 1.8}
                    fill={isSelected ? `rgba(6, 207, 255, 0.2)` : `rgba(6, 207, 255, 0.08)`}
                    filter="url(#glow-lg)"
                  />
                  {/* Selection ring */}
                  {isSelected && (
                    <circle
                      r={r + 3}
                      fill="none"
                      stroke="#06B6D4"
                      strokeWidth="1.5"
                      strokeDasharray="4 4"
                      style={{ animation: "spin 10s linear infinite" }}
                    />
                  )}
                  {/* Main sphere */}
                  <circle
                    r={r}
                    fill={`url(#house-grad-${h})`}
                    stroke={isSelected ? "#38BDF8" : "rgba(255,255,255,0.2)"}
                    strokeWidth={isSelected ? 2 : 1}
                    filter="url(#glow-sm)"
                  />
                  {/* House number */}
                  <text
                    textAnchor="middle"
                    dy="4"
                    fill={labelColor}
                    fontSize="12"
                    fontWeight="bold"
                    fontFamily="var(--font-mono)"
                    style={{ pointerEvents: "none" }}
                  >
                    {h}
                  </text>
                  {/* House name (small) */}
                  <text
                    textAnchor="middle"
                    dy={r + 14}
                    fill="var(--text-secondary)"
                    fontSize="9"
                    fontWeight="500"
                    style={{ pointerEvents: "none" }}
                  >
                    {HOUSE_BHAVA[h]?.name.split(" ")[0] || ""}
                  </text>
                </g>
              );
            })}
          </svg>

          {/* Edge tooltip */}
          {hoveredEdge && (
            <div
              className="absolute pointer-events-none bottom-32 left-1/2 z-20 max-w-xs -translate-x-1/2 animate-fade-in"
              style={{
                backgroundColor: "rgba(18, 24, 36, 0.95)",
                border: "1px solid rgba(6, 207, 255, 0.4)",
                borderRadius: "8px",
                padding: "12px",
                boxShadow: "0 10px 40px rgba(0,0,0,0.8)",
                backdropFilter: "blur(8px)",
              }}
            >
              <div className="text-xs font-bold mb-1" style={{ color: EDGE_COLORS[hoveredEdge.kind] }}>
                {hoveredEdge.label}
              </div>
              <div className="text-[11px] text-gray-300 leading-relaxed">
                {hoveredEdge.description}
              </div>
            </div>
          )}
        </div>

        {/* Bottom timeline */}
        <div className="flex items-center justify-between gap-4 rounded-lg border border-gray-800 bg-[var(--bg-card)] px-4 py-3">
          <span className="text-[10px] font-mono uppercase text-gray-500">Dasha / Transit Timeline</span>
          <div className="flex-1 mx-6 flex items-center gap-4">
            <span className="text-[10px] font-mono text-gray-500">2020</span>
            <input
              type="range"
              min="2020"
              max="2035"
              defaultValue="2026"
              step="1"
              className="flex-1 accent-cyan-400 h-2 cursor-pointer appearance-none bg-gray-800 rounded-full"
              style={{
                backgroundSize: "50% 100%",
                background: "linear-gradient(to right, var(--accent) 0%, var(--accent) 50%, #334155 50%, #334155 100%)",
              }}
            />
            <span className="text-[10px] font-mono text-gray-500">2035</span>
          </div>
          <span className="text-xs font-bold font-mono" style={{ color: "var(--accent)" }}>
            2026
          </span>
        </div>
      </div>

      {/* ── RIGHT: Analysis panel ───────────────────────────────────────────── */}
      <div
        className="flex w-full flex-col gap-4 overflow-y-auto rounded-xl border border-gray-800 bg-[var(--bg-card)] p-5 lg:w-80 xl:w-96 backdrop-blur-md"
        style={{ maxHeight: "calc(100vh - 200px)" }}
      >
        {activeInfo ? (
          <>
            {/* Header */}
            <div className="flex items-start justify-between border-b border-gray-800 pb-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="px-2 py-0.5 text-xs font-bold rounded-md bg-cyan-900/40 text-cyan-300 border border-cyan-600/40">
                    {ordinal(activeInfo.houseNumber)} House
                  </span>
                  {activeInfo.weak ? (
                    <span className="px-2 py-0.5 text-xs font-bold rounded-md bg-red-900/40 text-red-300 border border-red-600/40">
                      Weak
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 text-xs font-bold rounded-md bg-emerald-900/40 text-emerald-300 border border-emerald-600/40">
                      Strong
                    </span>
                  )}
                </div>
                <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
                  {HOUSE_BHAVA[activeInfo.houseNumber]?.name || `House ${activeInfo.houseNumber}`}
                </h2>
                <div className="text-xs text-gray-400 font-mono mt-1">
                  {activeInfo.rashi} • Lord: {activeInfo.lord || "—"}
                </div>
              </div>
              <button
                onClick={() => setSelected(null)}
                className="text-gray-400 hover:text-white transition"
              >
                ✕
              </button>
            </div>

            {/* Strength bar */}
            <div className="space-y-2 border-b border-gray-800 pb-4">
              <div className="flex justify-between text-xs">
                <span className="text-gray-400">Functional Strength</span>
                <span className="font-mono" style={{ color: activeInfo.weak ? "var(--status-danger)" : "var(--status-success)" }}>
                  {activeInfo.lordStrength?.strength_score?.toFixed(1) ?? "N/A"}/10
                </span>
              </div>
              <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className="h-full transition-all duration-500"
                  style={{
                    width: `${(activeInfo.lordStrength?.strength_score ?? 5) * 10}%`,
                    backgroundColor: activeInfo.weak ? "var(--status-danger)" : "var(--status-success)",
                  }}
                />
              </div>
            </div>

            {/* Occupants & Lord Data */}
            <div className="space-y-3 border-b border-gray-800 pb-4 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-400">Lord Placement</span>
                <span className="font-mono" style={{ color: "var(--text-primary)" }}>
                  {activeInfo.lordPlacementHouse ? `${ordinal(activeInfo.lordPlacementHouse)} house` : "Unknown"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Occupants</span>
                <div className="flex gap-1">
                  {activeInfo.occupants.length === 0 ? (
                    <span className="font-mono text-gray-500">Vacant</span>
                  ) : (
                    activeInfo.occupants.map((occ) => (
                      <span
                        key={occ.planet}
                        className="px-1.5 py-0.5 rounded bg-amber-900/30 text-amber-300 border border-amber-600/30 font-mono text-[10px]"
                      >
                        {PLANET_SYMBOLS[occ.planet as keyof typeof PLANET_SYMBOLS] || occ.planet}
                      </span>
                    ))
                  )}
                </div>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Significations</span>
                <span className="text-right font-mono" style={{ color: "var(--text-secondary)" }}>
                  {HOUSE_BHAVA[activeInfo.houseNumber]?.area || "General"}
                </span>
              </div>
            </div>

            {/* Edge lists */}
            <div className="space-y-4">
              {outgoing.length > 0 && (
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-wide mb-2" style={{ color: "var(--accent)" }}>
                    Outgoing Connections
                  </div>
                  <div className="space-y-2">
                    {outgoing.map((edge) => (
                      <div
                        key={edge.id}
                        className="flex items-center gap-2 rounded border border-gray-800 bg-[var(--bg-card-hover)] p-2 text-xs"
                      >
                        <div
                          className="h-2 w-2 rounded-full"
                          style={{ backgroundColor: EDGE_COLORS[edge.kind], boxShadow: `0 0 8px ${EDGE_COLORS[edge.kind]}` }}
                        />
                        <div className="flex-1 font-mono" style={{ color: "var(--text-secondary)" }}>
                          {edge.label}
                        </div>
                        <div
                          className="text-[10px] px-1.5 py-0.5 rounded font-bold"
                          style={{
                            backgroundColor: edge.weak ? "rgba(239, 68, 68, 0.15)" : "rgba(34, 197, 94, 0.15)",
                            color: edge.weak ? "var(--status-danger)" : "var(--status-success)",
                            border: `1px solid ${edge.weak ? "rgba(239, 68, 68, 0.3)" : "rgba(34, 197, 94, 0.3)"}`,
                          }}
                        >
                          {edge.strengthScore.toFixed(1)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {incoming.length > 0 && (
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-wide mb-2" style={{ color: "var(--accent)" }}>
                    Incoming Influence
                  </div>
                  <div className="space-y-2">
                    {incoming.slice(0, 5).map((edge) => (
                      <div
                        key={edge.id}
                        className="flex items-center gap-2 rounded border border-gray-800 bg-[var(--bg-card-hover)] p-2 text-xs"
                      >
                        <div
                          className="h-2 w-2 rounded-full"
                          style={{ backgroundColor: EDGE_COLORS[edge.kind], boxShadow: `0 0 8px ${EDGE_COLORS[edge.kind]}` }}
                        />
                        <div className="flex-1 font-mono" style={{ color: "var(--text-secondary)" }}>
                          ← {edge.label.replace(/^.*→/, "").trim()}
                        </div>
                        <div
                          className="text-[10px] px-1.5 py-0.5 rounded font-bold"
                          style={{
                            backgroundColor: edge.weak ? "rgba(239, 68, 68, 0.15)" : "rgba(34, 197, 94, 0.15)",
                            color: edge.weak ? "var(--status-danger)" : "var(--status-success)",
                            border: `1px solid ${edge.weak ? "rgba(239, 68, 68, 0.3)" : "rgba(34, 197, 94, 0.3)"}`,
                          }}
                        >
                          {edge.strengthScore.toFixed(1)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* AI Insights */}
            <div className="mt-auto rounded-lg border border-cyan-500/30 bg-cyan-950/20 p-4">
              <div className="text-xs font-bold mb-2 text-cyan-400">AI Dependency Insights</div>
              <div className="text-[11px] leading-relaxed text-gray-300">
                {activeInfo.weak ? (
                  <>
                    <strong style={{ color: "var(--status-danger)" }}>Weak house</strong> — The lord of this house is poorly positioned, which may create challenges in its significations. Focus on strengthening through remedial measures and understanding the specific dependency patterns shown in the graph.
                  </>
                ) : (
                  <>
                    <strong style={{ color: "var(--status-success)" }}>Strong house</strong> — The lord is well-positioned, providing robust support for this house's significations. The outgoing connections indicate positive influence over related areas of life.
                  </>
                )}
              </div>
            </div>
          </>
        ) : (
          <div className="flex flex-1 flex-col items-center justify-center text-center p-6">
            <div className="text-2xl mb-4" style={{ color: "var(--accent)" }}>🏛</div>
            <h3 className="text-base font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
              House Dependency Network
            </h3>
            <p className="text-xs text-gray-400 max-w-xs">
              Click any house node to view its dependencies, lordship connections, and astrological insights.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
