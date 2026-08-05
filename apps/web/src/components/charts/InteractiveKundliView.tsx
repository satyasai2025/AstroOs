"use client";

import { useState, useMemo, useCallback } from "react";
import {
  RASHIS,
  RASHI_LORDS,
  PLANET_SYMBOLS,
  NAKSHATRAS,
  rashiIndexFromLongitude,
} from "@/lib/astro";
import type {
  D1ChartResponse,
  PlanetPositionSchema,
  AspectSchema,
  HouseCuspSchema,
  AllVargaChartsResponse,
  ShadbalaTotalResponse,
  WorkflowAnalysisRequest,
} from "@/lib/types";
import { naturalRelationship } from "@/lib/planetRelations";
import { useShadbalaAll } from "@/lib/shadbala";
import { useKarakatvaSearch, type Karakatva } from "@/lib/karakatva";
import { useAvastha } from "@/lib/avastha";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface InteractiveKundliViewProps {
  chart: D1ChartResponse;
  /** Optional: pre-selected planet to pin on mount */
  initialPlanet?: string;
  /** Divisional charts, when the caller's analysis computed them
   * (request.include_vargas) — powers the Divisional Charts card. */
  vargas?: AllVargaChartsResponse | null;
  /** Per-planet Shadbala totals from the same /workflow/analyze
   * response — powers the Strength card's Shadbala row. */
  shadbala?: ShadbalaTotalResponse[] | null;
  /** Original birth request, needed to compute Digbala and Avastha
   * (both are compute-only endpoints, not part of the saved chart). */
  request?: WorkflowAnalysisRequest | null;
}

type TabId = "chart" | "planets" | "houses" | "aspects";

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

const PLANET_COLORS: Record<string, string> = {
  Sun: "#F5A623",
  Moon: "#B0BEC5",
  Mars: "#EF4444",
  Mercury: "#22C55E",
  Jupiter: "#F59E0B",
  Venus: "#EC4899",
  Saturn: "#6366F1",
  Rahu: "#8B5CF6",
  Ketu: "#8B5CF6",
  "Ascendant": "#06CFFF",
};

const DIGNITY_COLORS: Record<string, string> = {
  exalted: "#22C55E",
  own_sign: "#06CFFF",
  moolatrikona: "#06CFFF",
  friendly: "#3B82F6",
  neutral: "#B0BEC5",
  debilitated: "#EF4444",
  enemy: "#F97316",
};

const DIGNITY_LABELS: Record<string, string> = {
  exalted: "Exalted (Uccha)",
  own_sign: "Own Sign (Swa)",
  moolatrikona: "Moolatrikona",
  friendly: "Friendly",
  neutral: "Neutral",
  debilitated: "Debilitated (Neecha)",
  enemy: "Enemy",
};

/** North Indian diamond kundli — 12 houses as SVG polygon paths.
 *  Layout (houses numbered 1-12 anti-clockwise from top-center):
 *
 *           12  1   2
 *        11 /  TOP  \  3
 *         /  1    2   \
 *   10   | 11   12 |  4
 *         \  9   10 /
 *        9 \ BOT / 5
 *           8  7  6
 *
 *  The diamond is rotated 45°. Ascendant is house 1 (top).
 */

const CHART_SIZE = 480;
const CX = CHART_SIZE / 2;
const CY = CHART_SIZE / 2;
const HALF = CHART_SIZE * 0.42;

// Outer diamond points (rotated square)
const DIAMOND = {
  top: { x: CX, y: CY - HALF },
  right: { x: CX + HALF, y: CY },
  bottom: { x: CX, y: CY + HALF },
  left: { x: CX - HALF, y: CY },
};

// House geometry: North Indian style
// House 1 (Ascendant) is the top-center triangle
// Houses progress counter-clockwise
function getHousePolygon(houseNum: number): string {
  const t = DIAMOND.top;
  const r = DIAMOND.right;
  const b = DIAMOND.bottom;
  const l = DIAMOND.left;

  const triangles: Record<number, string> = {
    1: `${t.x},${t.y} ${CX},${CY} ${r.x},${r.y}`,           // top-right (ASC)
    2: `${CX},${CY} ${r.x},${r.y} ${b.x},${b.y}`,           // right (house 2)
    3: `${CX},${CY} ${b.x},${b.y} ${l.x},${l.y}`,           // bottom (house 3)
    4: `${CX},${CY} ${l.x},${l.y} ${t.x},${t.y}`,           // left (house 4)
  };

  // Houses 5-8 share triangles 1-4 but in the outer regions
  // Houses 9-12 are the small corner triangles
  // For a standard North Indian layout we split the 4 quadrants further

  // Refined: standard North Indian has 12 houses
  // Top quadrant: houses 12, 1, 2
  // Right quadrant: houses 2, 3, 4 (wait, let me think again)
  //
  // Standard North Indian diamond layout:
  // The ascendant house (1) is at top center.
  // From ASC, signs go counter-clockwise. Houses also go counter-clockwise.
  //
  // Actually in North Indian (diamond) chart, houses are FIXED positions,
  // and the SIGNS rotate based on the ascendant.
  // But for the interactive view, we draw the fixed 12-house grid.
  //
  // Let me use a simpler approach: divide the diamond into 12 triangular sectors.

  return triangles[1]; // fallback
}

// Simplified: 12 triangular house zones
function houseCenter(houseNum: number): { x: number; y: number } {
  // Distribute 12 houses around the diamond
  // House 1 starts at top (270° in standard math, -90° in SVG)
  const angles = [
    -90, -60, -30, 0, 30, 60, 90, 120, 150, 180, 210, 240,
  ];
  const angleDeg = angles[(houseNum - 1) % 12];
  const angleRad = (angleDeg * Math.PI) / 180;
  const dist = HALF * 0.55;
  return {
    x: CX + dist * Math.cos(angleRad),
    y: CY + dist * Math.sin(angleRad),
  };
}

/** Get the SVG path for a North Indian diamond house sector */
function housePath(houseNum: number): string {
  const t = DIAMOND.top;
  const r = DIAMOND.right;
  const b = DIAMOND.bottom;
  const l = DIAMOND.left;
  const w = CHART_SIZE * 0.002; // line width compensation

  // Major diagonals divide the diamond into 4 quadrants
  // Cross lines divide each quadrant into 3 houses
  // Total: 12 triangular sectors

  // Quadrant 1: Top to Right (houses 1, 2, 3) — top-right half
  // Quadrant 2: Right to Bottom (houses 4, 5, 6) — bottom-right
  // Quadrant 3: Bottom to Left (houses 7, 8, 9) — bottom-left
  // Quadrant 4: Left to Top (houses 10, 11, 12) — top-left

  // Subdivide each quadrant edge into 3 equal segments
  const edgePoints = (a: { x: number; y: number }, b: { x: number; y: number }) => [
    a,
    { x: a.x + (b.x - a.x) / 3, y: a.y + (b.y - a.y) / 3 },
    { x: a.x + (2 * (b.x - a.x)) / 3, y: a.y + (2 * (b.y - a.y)) / 3 },
    b,
  ];

  const topRight = edgePoints(t, r); // [t, p1, p2, r]
  const rightBottom = edgePoints(r, b); // [r, p3, p4, b]
  const bottomLeft = edgePoints(b, l); // [b, p5, p6, l]
  const leftTop = edgePoints(l, t); // [l, p7, p8, t]

  // Each house is a triangle from center (CX,CY) to two adjacent edge points
  const houseEdges: { a: { x: number; y: number }; b: { x: number; y: number } }[] = [
    // Houses 1-3: top → right
    { a: topRight[0], b: topRight[1] },
    { a: topRight[1], b: topRight[2] },
    { a: topRight[2], b: topRight[3] },
    // Houses 4-6: right → bottom
    { a: rightBottom[0], b: rightBottom[1] },
    { a: rightBottom[1], b: rightBottom[2] },
    { a: rightBottom[2], b: rightBottom[3] },
    // Houses 7-9: bottom → left
    { a: bottomLeft[0], b: bottomLeft[1] },
    { a: bottomLeft[1], b: bottomLeft[2] },
    { a: bottomLeft[2], b: bottomLeft[3] },
    // Houses 10-12: left → top
    { a: leftTop[0], b: leftTop[1] },
    { a: leftTop[1], b: leftTop[2] },
    { a: leftTop[2], b: leftTop[3] },
  ];

  const idx = ((houseNum - 1) % 12);
  const edge = houseEdges[idx];
  return `M ${CX},${CY} L ${edge.a.x},${edge.a.y} L ${edge.b.x},${edge.b.y} Z`;
}

function houseLabelPos(houseNum: number): { x: number; y: number } {
  const t = DIAMOND.top;
  const r = DIAMOND.right;
  const b = DIAMOND.bottom;
  const l = DIAMOND.left;

  const edgePoints = (a: { x: number; y: number }, bp: { x: number; y: number }) => [
    a,
    { x: a.x + (bp.x - a.x) / 3, y: a.y + (bp.y - a.y) / 3 },
    { x: a.x + (2 * (bp.x - a.x)) / 3, y: a.y + (2 * (bp.y - a.y)) / 3 },
    bp,
  ];

  const topRight = edgePoints(t, r);
  const rightBottom = edgePoints(r, b);
  const bottomLeft = edgePoints(b, l);
  const leftTop = edgePoints(l, t);

  const houseEdges = [
    ...[0, 1, 2].map((i) => [topRight[i], topRight[i + 1]]),
    ...[0, 1, 2].map((i) => [rightBottom[i], rightBottom[i + 1]]),
    ...[0, 1, 2].map((i) => [bottomLeft[i], bottomLeft[i + 1]]),
    ...[0, 1, 2].map((i) => [leftTop[i], leftTop[i + 1]]),
  ];

  const idx = ((houseNum - 1) % 12);
  const [a, bp] = houseEdges[idx];
  return {
    x: (CX + a.x + bp.x) / 3,
    y: (CY + a.y + bp.y) / 3,
  };
}

/* ------------------------------------------------------------------ */
/*  Sub-components                                                     */
/* ------------------------------------------------------------------ */

function PlanetBadge({
  planet,
  position,
  x,
  y,
  isHovered,
  isPinned,
  onHover,
  onLeave,
  onClick,
}: {
  planet: string;
  position: PlanetPositionSchema;
  x: number;
  y: number;
  isHovered: boolean;
  isPinned: boolean;
  onHover: () => void;
  onLeave: () => void;
  onClick: () => void;
}) {
  const color = PLANET_COLORS[planet] || "#B0BEC5";
  const symbol = PLANET_SYMBOLS[planet] || planet[0];
  const active = isHovered || isPinned;
  const r = active ? 22 : 18;

  return (
    <g
      onMouseEnter={onHover}
      onMouseLeave={onLeave}
      onClick={onClick}
      style={{ cursor: "pointer" }}
    >
      {/* Glow ring on hover/pin */}
      {active && (
        <circle
          cx={x}
          cy={y}
          r={r + 4}
          fill="none"
          stroke={color}
          strokeWidth={1.5}
          opacity={0.4}
        />
      )}
      {/* Badge background */}
      <circle
        cx={x}
        cy={y}
        r={r}
        fill="var(--obsidian-surface)"
        stroke={color}
        strokeWidth={active ? 2 : 1.2}
        opacity={0.95}
      />
      {/* Planet symbol */}
      <text
        x={x}
        y={y}
        textAnchor="middle"
        dominantBaseline="central"
        fill={color}
        fontSize={planet === "Ascendant" ? 11 : 13}
        fontFamily="var(--font-mono)"
        fontWeight="bold"
      >
        {symbol}
      </text>
      {/* Retrograde indicator */}
      {position.is_retrograde && (
        <text
          x={x + r - 2}
          y={y - r + 2}
          textAnchor="middle"
          dominantBaseline="central"
          fill="#F59E0B"
          fontSize={8}
          fontWeight="bold"
        >
          ℞
        </text>
      )}
      {/* Combust indicator */}
      {position.is_combust && (
        <text
          x={x - r + 2}
          y={y - r + 2}
          textAnchor="middle"
          dominantBaseline="central"
          fill="#EF4444"
          fontSize={7}
        >
          ☀
        </text>
      )}
      {/* Planet label below */}
      <text
        x={x}
        y={y + r + 10}
        textAnchor="middle"
        dominantBaseline="central"
        fill="var(--obsidian-text-secondary)"
        fontSize={9}
        fontFamily="var(--font-inter)"
      >
        {planet === "Ascendant" ? "ASC" : planet.slice(0, 3)}
      </text>
    </g>
  );
}

/* ------------------------------------------------------------------ */
/*  Main Component                                                     */
/* ------------------------------------------------------------------ */

export default function InteractiveKundliView({
  chart,
  initialPlanet,
  vargas = null,
  shadbala = null,
  request = null,
}: InteractiveKundliViewProps) {
  const [activeTab, setActiveTab] = useState<TabId>("chart");
  const [hoveredPlanet, setHoveredPlanet] = useState<string | null>(null);
  const [pinnedPlanet, setPinnedPlanet] = useState<string | null>(
    initialPlanet || null,
  );
  const [hoveredHouse, setHoveredHouse] = useState<number | null>(null);
  const [selectedHouse, setSelectedHouse] = useState<number | null>(null);

  const activePlanet = pinnedPlanet ?? hoveredPlanet;
  const activeHouse = selectedHouse ?? hoveredHouse;

  // ── Extra per-planet data for the redesigned detail panel ──
  // Digbala isn't in the /workflow/analyze response (only the combined
  // Shadbala total is) — useShadbalaAll hits its own compute-only
  // endpoint, same pattern as the standalone AvasthaPanel/
  // IshtaKashtaBalaPanel elsewhere on this page. TanStack Query dedupes
  // by query key, so this doesn't double-fetch if those panels are also
  // mounted with the same `request`.
  const { data: shadbalaAll } = useShadbalaAll(request);
  const { data: avasthaData } = useAvastha(request);
  const karakatvaGraha =
    activePlanet && activePlanet !== "Ascendant" ? activePlanet.toLowerCase() : "";
  const { data: karakatvaData } = useKarakatvaSearch({ graha: karakatvaGraha });

  // ── Ascendant info ──
  const asc = chart.ascendant;
  const ascRashiIdx = rashiIndexFromLongitude(asc.sidereal_longitude);

  // ── Position planets in their houses ──
  const planetPositions = useMemo(() => {
    const positions: {
      planet: string;
      position: PlanetPositionSchema;
      x: number;
      y: number;
      houseNum: number;
    }[] = [];

    // Group planets by house
    const housePlanets: Map<number, PlanetPositionSchema[]> = new Map();
    for (const p of chart.planets) {
      const h = p.house_number;
      if (!housePlanets.has(h)) housePlanets.set(h, []);
      housePlanets.get(h)!.push(p);
    }

    for (const [houseNum, planets] of housePlanets) {
      const center = houseLabelPos(houseNum);
      // Arrange planets in a small cluster around the house center
      const count = planets.length;
      const spread = 28;
      const startX = center.x - ((count - 1) * spread) / 2;

      planets.forEach((p, i) => {
        positions.push({
          planet: p.planet,
          position: p,
          x: startX + i * spread,
          y: center.y + (i % 2 === 0 ? -4 : 4),
          houseNum,
        });
      });
    }

    // Add ascendant (always house 1)
    const ascCenter = houseLabelPos(1);
    positions.push({
      planet: "Ascendant",
      position: {
        planet: "Ascendant",
        sidereal_longitude: asc.sidereal_longitude,
        rashi: asc.rashi,
        rashi_degree: 0,
        house_number: 1,
        nakshatra: asc.nakshatra,
        pada: asc.pada,
        is_retrograde: false,
        is_combust: false,
        combustion_orb: null,
        dignity: null,
        nakshatra_lord: "",
        sub_lord: "",
        sub_sub_lord: "",
        rashi_house_number: 1,
      },
      x: ascCenter.x + 30,
      y: ascCenter.y - 15,
      houseNum: 1,
    });

    return positions;
  }, [chart]);

  // ── Aspect lines ──
  const aspectLines = useMemo(() => {
    return chart.aspects.map((aspect) => {
      const from = planetPositions.find(
        (p) => p.planet === aspect.from_planet,
      );
      const to = planetPositions.find((p) => p.planet === aspect.to_planet);
      if (!from || !to) return null;
      return { ...aspect, x1: from.x, y1: from.y, x2: to.x, y2: to.y };
    }).filter(Boolean);
  }, [chart.aspects, planetPositions]);

  // ── House data for explorer ──
  const houseData = useMemo(() => {
    return Array.from({ length: 12 }, (_, i) => {
      const houseNum = i + 1;
      const cusp = chart.houses[i];
      const planetsInHouse = chart.planets.filter(
        (p) => p.house_number === houseNum,
      );
      const houseLord = cusp ? RASHI_LORDS[cusp.rashi as keyof typeof RASHI_LORDS] || "—" : "—";
      return {
        houseNum,
        cusp,
        planets: planetsInHouse,
        lord: houseLord,
        sign: cusp?.rashi || "—",
      };
    });
  }, [chart]);

  // ── Planet detail data ──
  const planetDetail = useMemo(() => {
    if (!activePlanet || activePlanet === "Ascendant") return null;
    const pos = chart.planets.find((p) => p.planet === activePlanet);
    if (!pos) return null;

    const strength = chart.planet_strengths.find(
      (p) => p.planet === activePlanet,
    );
    const aspects = chart.aspects.filter(
      (a) =>
        a.from_planet === activePlanet || a.to_planet === activePlanet,
    );
    const conjunctions = chart.planets.filter(
      (p) =>
        p.planet !== activePlanet &&
        p.house_number === pos.house_number,
    );

    return { position: pos, strength, aspects, conjunctions };
  }, [activePlanet, chart]);

  // ── Handlers ──
  const handlePlanetClick = useCallback(
    (planet: string) => {
      setPinnedPlanet((prev) => (prev === planet ? null : planet));
    },
    [],
  );

  return (
    <div className="flex h-full flex-col lg:flex-row">
      {/* ── Left: Chart + Controls ── */}
      <div className="flex flex-1 flex-col min-w-0">
        {/* Tab bar */}
        <div
          className="flex items-center gap-1 border-b px-4 py-2"
          style={{ borderColor: "var(--obsidian-border)" }}
        >
          {(["chart", "planets", "houses", "aspects"] as TabId[]).map(
            (tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className="rounded-md px-3 py-1.5 text-xs font-medium capitalize transition-all"
                style={{
                  backgroundColor:
                    activeTab === tab
                      ? "var(--obsidian-accent-primary-soft)"
                      : "transparent",
                  color:
                    activeTab === tab
                      ? "var(--obsidian-accent-primary)"
                      : "var(--obsidian-text-muted)",
                }}
              >
                {tab}
              </button>
            ),
          )}
        </div>

        {/* Chart area */}
        <div className="flex flex-1 items-center justify-center p-4">
          <svg
            viewBox={`0 0 ${CHART_SIZE} ${CHART_SIZE}`}
            className="max-h-full max-w-full"
            style={{ filter: "drop-shadow(0 0 20px rgba(6, 207, 255, 0.08))" }}
          >
            {/* Background */}
            <rect
              x={0}
              y={0}
              width={CHART_SIZE}
              height={CHART_SIZE}
              fill="var(--obsidian-surface)"
              rx={12}
            />

            {/* House sectors */}
            {Array.from({ length: 12 }, (_, i) => {
              const houseNum = i + 1;
              const isActive = activeHouse === houseNum;
              return (
                <g key={houseNum}>
                  <path
                    d={housePath(houseNum)}
                    fill={
                      isActive
                        ? "rgba(6, 207, 255, 0.06)"
                        : "transparent"
                    }
                    stroke="var(--obsidian-border)"
                    strokeWidth={0.8}
                    onMouseEnter={() => setHoveredHouse(houseNum)}
                    onMouseLeave={() => setHoveredHouse(null)}
                    onClick={() =>
                      setSelectedHouse(
                        selectedHouse === houseNum ? null : houseNum,
                      )
                    }
                    style={{ cursor: "pointer" }}
                  />
                  {/* House number */}
                  <text
                    x={houseLabelPos(houseNum).x}
                    y={houseLabelPos(houseNum).y - 24}
                    textAnchor="middle"
                    dominantBaseline="central"
                    fill="var(--obsidian-text-muted)"
                    fontSize={8}
                    fontFamily="var(--font-mono)"
                    opacity={isActive ? 0.8 : 0.35}
                  >
                    {houseNum}
                  </text>
                </g>
              );
            })}

            {/* Outer diamond border */}
            <polygon
              points={`${DIAMOND.top.x},${DIAMOND.top.y} ${DIAMOND.right.x},${DIAMOND.right.y} ${DIAMOND.bottom.x},${DIAMOND.bottom.y} ${DIAMOND.left.x},${DIAMOND.left.y}`}
              fill="none"
              stroke="var(--obsidian-accent-primary)"
              strokeWidth={1.5}
              opacity={0.3}
            />

            {/* Cross lines */}
            <line
              x1={DIAMOND.top.x}
              y1={DIAMOND.top.y}
              x2={DIAMOND.bottom.x}
              y2={DIAMOND.bottom.y}
              stroke="var(--obsidian-border)"
              strokeWidth={0.8}
            />
            <line
              x1={DIAMOND.left.x}
              y1={DIAMOND.left.y}
              x2={DIAMOND.right.x}
              y2={DIAMOND.right.y}
              stroke="var(--obsidian-border)"
              strokeWidth={0.8}
            />

            {/* Aspect lines */}
            {activeTab === "aspects" &&
              aspectLines.map((line, i) => {
                if (!line) return null;
                const isHighlighted =
                  activePlanet &&
                  (line.from_planet === activePlanet ||
                    line.to_planet === activePlanet);
                const color =
                  line.aspect_type === "conjunction"
                    ? "#22C55E"
                    : line.aspect_type === "opposition"
                      ? "#EF4444"
                      : line.aspect_type === "trine"
                        ? "#06CFFF"
                        : line.aspect_type === "square"
                          ? "#F59E0B"
                          : "#B0BEC5";
                return (
                  <line
                    key={i}
                    x1={line.x1}
                    y1={line.y1}
                    x2={line.x2}
                    y2={line.y2}
                    stroke={color}
                    strokeWidth={isHighlighted ? 2 : 0.8}
                    strokeDasharray={
                      line.aspect_type === "conjunction" ? "none" : "4 2"
                    }
                    opacity={isHighlighted ? 0.8 : 0.25}
                  />
                );
              })}

            {/* Planet badges */}
            {activeTab !== "aspects" &&
              planetPositions.map((pp) => (
                <PlanetBadge
                  key={pp.planet}
                  planet={pp.planet}
                  position={pp.position}
                  x={pp.x}
                  y={pp.y}
                  isHovered={hoveredPlanet === pp.planet}
                  isPinned={pinnedPlanet === pp.planet}
                  onHover={() => setHoveredPlanet(pp.planet)}
                  onLeave={() => setHoveredPlanet(null)}
                  onClick={() => handlePlanetClick(pp.planet)}
                />
              ))}
          </svg>
        </div>

        {/* Info bar below chart */}
        <div
          className="flex items-center justify-between border-t px-4 py-2 text-xs"
          style={{
            borderColor: "var(--obsidian-border)",
            color: "var(--obsidian-text-muted)",
          }}
        >
          <span>
            <span style={{ color: "var(--obsidian-accent-primary)" }}>
              {asc.rashi}
            </span>{" "}
            Ascendant · {asc.nakshatra} Pada {asc.pada}
          </span>
          <span>
            {chart.houses.length} houses · {chart.planets.length} planets ·{" "}
            {chart.aspects.length} aspects
          </span>
        </div>
      </div>

      {/* ── Right: Detail Panel ── */}
      {/* Wider than lg:w-80 when showing the planet card grid — the
          other tabs (houses/aspects/overview) are simple text lists and
          stay at the narrower width. */}
      <div
        className={`w-full border-t lg:border-t-0 lg:border-l ${
          activeTab === "planets" || activePlanet ? "lg:w-[440px]" : "lg:w-80"
        }`}
        style={{ borderColor: "var(--obsidian-border)" }}
      >
        {activeTab === "planets" || activePlanet ? (
          <PlanetExplorerPanel
            planet={activePlanet}
            detail={planetDetail}
            chart={chart}
            vargas={vargas}
            shadbala={shadbala}
            digbala={shadbalaAll?.phase1.dig_bala ?? null}
            avasthas={avasthaData?.avasthas ?? null}
            karakatvas={karakatvaData?.karakatvas ?? null}
          />
        ) : activeTab === "houses" || activeHouse ? (
          <HouseExplorerPanel
            houseNum={activeHouse}
            houseData={houseData}
            ascRashiIdx={ascRashiIdx}
          />
        ) : activeTab === "aspects" ? (
          <AspectsPanel
            aspects={chart.aspects}
            activePlanet={activePlanet}
          />
        ) : (
          <ChartOverviewPanel chart={chart} asc={asc} />
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Panel: Planet Explorer                                              */
/* ------------------------------------------------------------------ */

function PlanetExplorerPanel({
  planet,
  detail,
  chart,
  vargas,
  shadbala,
  digbala,
  avasthas,
  karakatvas,
}: {
  planet: string | null;
  detail: {
    position: PlanetPositionSchema;
    strength: (typeof chart.planet_strengths)[0] | undefined;
    aspects: AspectSchema[];
    conjunctions: PlanetPositionSchema[];
  } | null;
  chart: D1ChartResponse;
  vargas?: AllVargaChartsResponse | null;
  shadbala?: ShadbalaTotalResponse[] | null;
  digbala?: { planet: string; value_shashtiamsas: number; trace: string[] }[] | null;
  avasthas?: {
    planet: string;
    baladi_avastha: string;
    baladi_trace: string[];
    deeptadi_avastha: string;
    deeptadi_trace: string[];
  }[] | null;
  karakatvas?: Karakatva[] | null;
}) {
  if (!planet || !detail) {
    return (
      <div
        className="flex h-full items-center justify-center p-6 text-center text-sm"
        style={{ color: "var(--obsidian-text-muted)" }}
      >
        Click or hover a planet in the chart to explore its details
      </div>
    );
  }

  const { position: pos, strength, aspects, conjunctions } = detail;
  const color = PLANET_COLORS[planet] || "#B0BEC5";
  const isExceptionalDignity =
    strength?.dignity === "exalted" ||
    strength?.dignity === "debilitated" ||
    strength?.dignity === "own_sign" ||
    strength?.dignity === "moolatrikona";

  const relationship = naturalRelationship(planet);
  const shadbalaRow = shadbala?.find((s) => s.planet === planet);
  const digbalaRow = digbala?.find((d) => d.planet === planet);
  const avasthaRow = avasthas?.find((a) => a.planet === planet);
  const vargaCodes: string[] = ["D9", "D10", "D60"];
  const vargaRows = vargaCodes
    .map((code) => {
      const chartForVarga = vargas?.charts[code];
      const row = chartForVarga?.planet_positions.find((p) => p.planet === planet);
      return row ? { code, sign: row.varga_rashi, house: row.varga_house_number } : null;
    })
    .filter((r): r is { code: string; sign: string; house: number } => r !== null);

  return (
    <div className="flex h-full flex-col overflow-y-auto p-4" style={{ maxHeight: "100%" }}>
      {/* Planet header */}
      <div className="mb-4 flex items-start gap-3">
        <div
          className="flex h-10 w-10 items-center justify-center rounded-lg text-lg font-bold"
          style={{
            backgroundColor: `${color}15`,
            color,
            border: `1px solid ${color}30`,
          }}
        >
          {PLANET_SYMBOLS[planet] || planet[0]}
        </div>
        <div>
          <h3
            className="text-sm font-bold capitalize"
            style={{ color: "var(--obsidian-text-primary)" }}
          >
            {planet}
          </h3>
          <span
            className="text-xs"
            style={{ color: "var(--obsidian-text-muted)" }}
          >
            {pos.rashi} · House {pos.house_number} · {pos.nakshatra} (Pada {pos.pada})
          </span>
        </div>
        <div className="ml-auto flex flex-col items-end gap-1">
          {isExceptionalDignity && strength?.dignity && (
            <span
              className="rounded-full px-2 py-0.5 text-xs font-medium"
              style={{
                backgroundColor: `${DIGNITY_COLORS[strength.dignity]}20`,
                color: DIGNITY_COLORS[strength.dignity],
              }}
            >
              {DIGNITY_LABELS[strength.dignity]?.split(" (")[0].toUpperCase()}
            </span>
          )}
          {pos.is_retrograde && (
            <span
              className="rounded-full px-2 py-0.5 text-xs font-medium"
              style={{
                backgroundColor: "rgba(245, 158, 11, 0.15)",
                color: "#F59E0B",
              }}
            >
              ℞ Retro
            </span>
          )}
        </div>
      </div>

      {/* Position details */}
      <SectionLabel>Position</SectionLabel>
      <InfoRow label="Longitude" value={`${pos.sidereal_longitude.toFixed(4)}°`} />
      <InfoRow label="Sign (Rashi)" value={pos.rashi} />
      <InfoRow
        label="Degree in Sign"
        value={`${pos.rashi_degree.toFixed(2)}° ${pos.rashi}`}
      />
      <InfoRow label="House" value={`${pos.house_number}`} />
      <InfoRow label="Nakshatra" value={pos.nakshatra} />
      <InfoRow label="Pada" value={`${pos.pada}`} />
      {pos.nakshatra_lord && (
        <InfoRow label="Star Lord" value={pos.nakshatra_lord} />
      )}
      {pos.sub_lord && <InfoRow label="Sub Lord" value={pos.sub_lord} />}

      {/* Dignity */}
      {strength && (
        <>
          <SectionLabel>Dignity</SectionLabel>
          <InfoRow
            label="Status"
            value={
              strength.dignity
                ? DIGNITY_LABELS[strength.dignity] || strength.dignity
                : "—"
            }
            valueColor={
              strength.dignity
                ? DIGNITY_COLORS[strength.dignity] || "var(--obsidian-text-secondary)"
                : undefined
            }
          />
          <InfoRow
            label="Score"
            value={`${strength.strength_score.toFixed(1)} / 10`}
          />
          {strength.is_exalted && (
            <InfoRow label="" value="✦ Exalted" valueColor="#22C55E" />
          )}
          {strength.is_debilitated && (
            <InfoRow label="" value="✦ Debilitated" valueColor="#EF4444" />
          )}
          {strength.is_in_own_sign && (
            <InfoRow label="" value="✦ Own Sign" valueColor="#06CFFF" />
          )}
          <InfoRow
            label="Position"
            value={[
              strength.is_in_kendra ? "Kendra" : null,
              strength.is_in_trikona ? "Trikona" : null,
              strength.is_in_dusthana ? "Dusthana" : null,
            ]
              .filter(Boolean)
              .join(", ") || "—"}
          />
        </>
      )}

      {/* New Phase 1 cards: Relationships / Strength / Karakatva / Divisional / Avastha */}
      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <DetailCard
          title="Relationships"
          tooltip="Naisargika Maitri — natural (permanent) friend/neutral/enemy relationship between planets, independent of this chart."
        >
          {relationship ? (
            <>
              <RelationRow label="Friends" color="#22C55E" planets={relationship.friends} />
              <RelationRow label="Neutral" color="#F59E0B" planets={relationship.neutral} />
              <RelationRow label="Enemies" color="#EF4444" planets={relationship.enemies} />
            </>
          ) : (
            <EmptyNote>Not defined for {planet} in classical texts.</EmptyNote>
          )}
        </DetailCard>

        <DetailCard
          title="Strength"
          tooltip="Shadbala: overall planetary strength from classical Shadbala algorithms. Digbala: directional strength based on orientation relative to the angles (Kendras)."
        >
          {shadbalaRow ? (
            <InfoRow label="Shadbala" value={`${shadbalaRow.total_rupas.toFixed(2)} Rupas`} />
          ) : (
            <EmptyNote>Shadbala not computed for this analysis.</EmptyNote>
          )}
          {digbalaRow ? (
            <InfoRow
              label="Digbala"
              value={`${digbalaRow.value_shashtiamsas.toFixed(2)} Shashtiamsas`}
            />
          ) : (
            <EmptyNote>Digbala needs birth data to compute.</EmptyNote>
          )}
        </DetailCard>

        <DetailCard
          title="Significations (Karakatva)"
          tooltip="Natural significations and domains this planet governs, from the curated Karakatva catalogue."
        >
          {karakatvas && karakatvas.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {karakatvas.slice(0, 6).map((k) => (
                <Pill key={k.id}>{k.subject}</Pill>
              ))}
            </div>
          ) : (
            <EmptyNote>No catalogued significations found for {planet}.</EmptyNote>
          )}
          <a
            href="/karakatva"
            className="mt-2 inline-block text-xs font-medium"
            style={{ color: "var(--obsidian-accent-primary)" }}
          >
            View all on Karakatva page →
          </a>
        </DetailCard>

        <DetailCard
          title="Divisional Charts"
          tooltip="This planet's sign and house placement in the D9 (Navamsa), D10 (Dasamsha), and D60 (Shashtiamsha) divisional charts."
        >
          {vargaRows.length > 0 ? (
            <table className="w-full text-xs">
              <thead>
                <tr style={{ color: "var(--obsidian-text-muted)" }}>
                  <th className="pb-1 text-left font-medium">Chart</th>
                  <th className="pb-1 text-left font-medium">Sign</th>
                  <th className="pb-1 text-right font-medium">House</th>
                </tr>
              </thead>
              <tbody>
                {vargaRows.map((r) => (
                  <tr key={r.code}>
                    <td className="py-0.5" style={{ color: "var(--obsidian-text-primary)" }}>
                      {r.code}
                    </td>
                    <td className="py-0.5 capitalize" style={{ color: "var(--obsidian-text-primary)" }}>
                      {r.sign}
                    </td>
                    <td className="py-0.5 text-right" style={{ color: "var(--obsidian-text-primary)" }}>
                      H{r.house}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <EmptyNote>Divisional charts weren't computed for this analysis.</EmptyNote>
          )}
        </DetailCard>
      </div>

      <div className="mt-3">
        <DetailCard
          title="Avastha (State)"
          tooltip="Planetary state and physical condition according to classical Jyotish rules — Baladi (age-state) and Deeptadi (dignity-state)."
        >
          {avasthaRow ? (
            <>
              <AvasthaRow label="Baladi" value={avasthaRow.baladi_avastha} trace={avasthaRow.baladi_trace} />
              <AvasthaRow
                label="Deeptadi"
                value={avasthaRow.deeptadi_avastha}
                trace={avasthaRow.deeptadi_trace}
              />
            </>
          ) : (
            <EmptyNote>Avastha needs birth data to compute.</EmptyNote>
          )}
        </DetailCard>
      </div>

      <p
        className="mt-4 text-xs"
        style={{ color: "var(--obsidian-text-muted)" }}
      >
        Values shown are computed from classical Jyotish algorithms using the
        current analysis. Metrics are displayed in their original units;
        normalized scores are not shown unless defined by the underlying
        calculation.
      </p>

      {/* Conjunctions */}
      {conjunctions.length > 0 && (
        <>
          <SectionLabel>Conjunctions</SectionLabel>
          {conjunctions.map((c) => (
            <InfoRow
              key={c.planet}
              label={c.planet}
              value={`${c.rashi} (${c.rashi_degree.toFixed(1)}°)`}
              valueColor={PLANET_COLORS[c.planet]}
            />
          ))}
        </>
      )}

      {/* Aspects */}
      {aspects.length > 0 && (
        <>
          <SectionLabel>Aspects ({aspects.length})</SectionLabel>
          {aspects.slice(0, 8).map((a, i) => {
            const other =
              a.from_planet === planet ? a.to_planet : a.from_planet;
            const direction =
              a.from_planet === planet ? "→" : "←";
            return (
              <InfoRow
                key={i}
                label={`${direction} ${other}`}
                value={`${a.aspect_type} (${a.orb_degrees.toFixed(1)}°)${
                  a.is_applying ? " app" : ""
                }`}
                valueColor={
                  a.aspect_type === "trine"
                    ? "#06CFFF"
                    : a.aspect_type === "opposition"
                      ? "#EF4444"
                      : a.aspect_type === "square"
                        ? "#F59E0B"
                        : "var(--obsidian-text-secondary)"
                }
              />
            );
          })}
          {aspects.length > 8 && (
            <p
              className="mt-1 text-xs"
              style={{ color: "var(--obsidian-text-muted)" }}
            >
              +{aspects.length - 8} more
            </p>
          )}
        </>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Panel: House Explorer                                               */
/* ------------------------------------------------------------------ */

function HouseExplorerPanel({
  houseNum,
  houseData,
  ascRashiIdx,
}: {
  houseNum: number | null;
  houseData: {
    houseNum: number;
    cusp: HouseCuspSchema | undefined;
    planets: PlanetPositionSchema[];
    lord: string;
    sign: string;
  }[];
  ascRashiIdx: number;
}) {
  if (!houseNum) {
    return (
      <div
        className="flex h-full items-center justify-center p-6 text-center text-sm"
        style={{ color: "var(--obsidian-text-muted)" }}
      >
        Click a house in the chart to explore its cuspal details
      </div>
    );
  }

  const house = houseData[houseNum - 1];
  if (!house) return null;

  const HOUSE_NAMES = [
    "Self / Identity",
    "Wealth / Family",
    "Siblings / Courage",
    "Home / Mother",
    "Children / Creativity",
    "Health / Enemies",
    "Marriage / Partnership",
    "Longevity / Transformation",
    "Dharma / Fortune",
    "Career / Status",
    "Gains / Friends",
    "Loss / Liberation",
  ];

  return (
    <div className="flex h-full flex-col overflow-y-auto p-4">
      <div className="mb-4">
        <h3
          className="text-sm font-bold"
          style={{ color: "var(--obsidian-accent-primary)" }}
        >
          House {houseNum}
        </h3>
        <p
          className="text-xs"
          style={{ color: "var(--obsidian-text-muted)" }}
        >
          {HOUSE_NAMES[houseNum - 1] || ""}
        </p>
      </div>

      <SectionLabel>Cuspal Details</SectionLabel>
      <InfoRow label="Sign on Cusp" value={house.sign} />
      <InfoRow label="House Lord" value={house.lord} />
      {house.cusp && (
        <>
          <InfoRow
            label="Cusp Longitude"
            value={`${house.cusp.sidereal_longitude.toFixed(4)}°`}
          />
          <InfoRow label="Star Lord" value={house.cusp.nakshatra_lord || "—"} />
          <InfoRow
            label="Sub Lord (KP)"
            value={house.cusp.sub_lord || "—"}
          />
          <InfoRow
            label="Sub Sub Lord"
            value={house.cusp.sub_sub_lord || "—"}
          />
        </>
      )}

      {/* Planets in this house */}
      <SectionLabel>
        Planets in House {houseNum} ({house.planets.length})
      </SectionLabel>
      {house.planets.length === 0 ? (
        <p
          className="text-xs"
          style={{ color: "var(--obsidian-text-muted)" }}
        >
          No planets in this house
        </p>
      ) : (
        house.planets.map((p) => (
          <InfoRow
            key={p.planet}
            label={p.planet}
            value={`${p.rashi} ${p.rashi_degree.toFixed(1)}°${
              p.is_retrograde ? " ℞" : ""
            }`}
            valueColor={PLANET_COLORS[p.planet]}
          />
        ))
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Panel: Aspects                                                     */
/* ------------------------------------------------------------------ */

function AspectsPanel({
  aspects,
  activePlanet,
}: {
  aspects: AspectSchema[];
  activePlanet: string | null;
}) {
  const grouped = useMemo(() => {
    const map = new Map<string, AspectSchema[]>();
    for (const a of aspects) {
      const key = a.aspect_type;
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(a);
    }
    return map;
  }, [aspects]);

  return (
    <div className="flex h-full flex-col overflow-y-auto p-4">
      <SectionLabel>All Aspects ({aspects.length})</SectionLabel>
      {Array.from(grouped.entries()).map(([type, list]) => {
        const color =
          type === "conjunction"
            ? "#22C55E"
            : type === "opposition"
              ? "#EF4444"
              : type === "trine"
                ? "#06CFFF"
                : type === "square"
                  ? "#F59E0B"
                  : "#B0BEC5";
        return (
          <div key={type} className="mb-3">
            <h4
              className="mb-1 text-xs font-semibold uppercase"
              style={{ color }}
            >
              {type} ({list.length})
            </h4>
            {list.map((a, i) => {
              const isHighlighted =
                activePlanet &&
                (a.from_planet === activePlanet ||
                  a.to_planet === activePlanet);
              return (
                <InfoRow
                  key={i}
                  label={`${a.from_planet} → ${a.to_planet}`}
                  value={`${a.orb_degrees.toFixed(1)}°${
                    a.is_applying ? " app" : " sep"
                  }`}
                  style={
                    isHighlighted
                      ? { backgroundColor: "rgba(6, 207, 255, 0.05)" }
                      : undefined
                  }
                />
              );
            })}
          </div>
        );
      })}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Panel: Chart Overview                                              */
/* ------------------------------------------------------------------ */

function ChartOverviewPanel({
  chart,
  asc,
}: {
  chart: D1ChartResponse;
  asc: D1ChartResponse["ascendant"];
}) {
  return (
    <div className="flex h-full flex-col overflow-y-auto p-4">
      <SectionLabel>Ascendant</SectionLabel>
      <InfoRow label="Sign" value={asc.rashi} valueColor="#06CFFF" />
      <InfoRow
        label="Longitude"
        value={`${asc.sidereal_longitude.toFixed(4)}°`}
      />
      <InfoRow label="Nakshatra" value={asc.nakshatra} />
      <InfoRow label="Pada" value={`${asc.pada}`} />

      <SectionLabel>Chart Info</SectionLabel>
      <InfoRow label="Ayanamsa" value={chart.ayanamsa_system} />
      <InfoRow
        label="Ayanamsa Value"
        value={`${chart.ayanamsa_value.toFixed(4)}°`}
      />
      <InfoRow label="House System" value={chart.house_system} />
      <InfoRow label="Planets" value={`${chart.planets.length}`} />
      <InfoRow label="Aspects" value={`${chart.aspects.length}`} />

      <SectionLabel>Panchanga</SectionLabel>
      {chart.panchanga && (
        <>
          <InfoRow
            label="Tithi"
            value={`${chart.panchanga.tithi.name} (${chart.panchanga.tithi.paksha})`}
          />
          <InfoRow label="Nakshatra" value={chart.panchanga.nakshatra.nakshatra} />
          <InfoRow label="Yoga" value={chart.panchanga.yoga.name} />
          <InfoRow label="Karana" value={chart.panchanga.karana.name} />
          <InfoRow label="Vara" value={chart.panchanga.vara.name} />
        </>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Shared UI helpers                                                   */
/* ------------------------------------------------------------------ */

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <h4
      className="mb-1.5 mt-4 text-xs font-semibold uppercase tracking-wide first:mt-0"
      style={{ color: "var(--obsidian-accent-primary)" }}
    >
      {children}
    </h4>
  );
}

function InfoRow({
  label,
  value,
  valueColor,
  style,
}: {
  label: string;
  value: string;
  valueColor?: string;
  style?: React.CSSProperties;
}) {
  return (
    <div
      className="flex items-center justify-between rounded py-1 px-1 text-sm"
      style={style}
    >
      <span style={{ color: "var(--obsidian-text-muted)" }}>{label}</span>
      <span
        className="text-right font-medium"
        style={{ color: valueColor || "var(--obsidian-text-primary)" }}
      >
        {value}
      </span>
    </div>
  );
}

/** One card in the planet panel's grid. `tooltip` renders as a native
 * title attribute on a small ⓘ mark next to the heading — no extra JS
 * tooltip library, just enough to keep engine-reasoning detail out of
 * the card's primary typography. */
function DetailCard({
  title,
  tooltip,
  children,
}: {
  title: string;
  tooltip?: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className="rounded-lg p-3"
      style={{
        backgroundColor: "var(--obsidian-surface)",
        border: "1px solid var(--obsidian-border)",
      }}
    >
      <div className="mb-2 flex items-center gap-1">
        <h4
          className="text-xs font-semibold uppercase tracking-wide"
          style={{ color: "var(--obsidian-accent-primary)" }}
        >
          {title}
        </h4>
        {tooltip && (
          <span
            title={tooltip}
            className="cursor-help text-xs"
            style={{ color: "var(--obsidian-text-muted)" }}
            aria-label={tooltip}
          >
            ⓘ
          </span>
        )}
      </div>
      {children}
    </div>
  );
}

function EmptyNote({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-xs" style={{ color: "var(--obsidian-text-muted)" }}>
      {children}
    </p>
  );
}

function Pill({ children }: { children: React.ReactNode }) {
  return (
    <span
      className="rounded-full px-2 py-0.5 text-xs capitalize"
      style={{
        backgroundColor: "var(--obsidian-accent-primary-soft)",
        color: "var(--obsidian-accent-primary)",
      }}
    >
      {children}
    </span>
  );
}

function RelationRow({
  label,
  color,
  planets,
}: {
  label: string;
  color: string;
  planets: string[];
}) {
  return (
    <div className="mb-1.5 flex items-start gap-2 text-xs">
      <span className="w-14 shrink-0" style={{ color: "var(--obsidian-text-muted)" }}>
        {label}
      </span>
      {planets.length > 0 ? (
        <div className="flex flex-wrap gap-1">
          {planets.map((p) => (
            <span
              key={p}
              className="rounded-full px-2 py-0.5 capitalize"
              style={{ backgroundColor: `${color}20`, color }}
            >
              {p}
            </span>
          ))}
        </div>
      ) : (
        <span style={{ color: "var(--obsidian-text-muted)" }}>—</span>
      )}
    </div>
  );
}

/** One Avastha row (Baladi or Deeptadi) — the trace is shown via the
 * native title attribute, not inline, per "trace preservation without
 * polluting primary card typography". */
function AvasthaRow({
  label,
  value,
  trace,
}: {
  label: string;
  value: string;
  trace: string[];
}) {
  return (
    <div className="flex items-center justify-between py-1 text-sm">
      <span style={{ color: "var(--obsidian-text-muted)" }}>{label}</span>
      <span
        title={trace.join(" · ")}
        className="cursor-help font-medium"
        style={{ color: "var(--obsidian-text-primary)" }}
      >
        {value}
      </span>
    </div>
  );
}
