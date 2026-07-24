"use client";

import { useMemo, useState } from "react";
import { PLANET_SYMBOLS, rashiLordFromApiName } from "@/lib/astro";
import type { HouseCuspSchema, PlanetPositionSchema, PlanetStrengthSchema } from "@/lib/types";

export interface HouseDependencyNetworkProps {
  /** D1 house cusps for the current chart — used to find each house's rashi
   * (sign), which in turn identifies its ruling lord. */
  houses: HouseCuspSchema[];
  /** D1 planet strengths — lord condition (dignity/placement/strength_score)
   * drives edge color/thickness. */
  planetStrengths: PlanetStrengthSchema[];
  /** Full D1 planet positions — needed for occupants (which planets sit in
   * each house) and each lord's own placement house, which is what the
   * "Nth lord in Mth" edges are built from. */
  planets: PlanetPositionSchema[];
}

/** Minimum strength_score (out of 0-10) a house's lord needs to avoid being
 * flagged "weak". Presentation heuristic, not a classical rule — documented
 * here so it's easy to tune later. Shared with the edge weak/strong split. */
const WEAK_STRENGTH_THRESHOLD = 4;

const WEAK_COLOR = "#f87171";
const STRONG_COLOR = "#34d399";

/** Standard classical Bhava names + one-line significations for all 12
 * houses (BPHS-style house-signification list) — shown in the house detail
 * panel, not computed per-chart (fixed classical reference, same category
 * of data as NATURAL_RELATIONSHIPS/KARAKATVA_BASIC elsewhere in the app). */
const HOUSE_BHAVA: Record<number, { name: string; area: string }> = {
  1: { name: "Tanu Bhava", area: "Self, body, personality" },
  2: { name: "Dhana Bhava", area: "Wealth, family, speech" },
  3: { name: "Sahaja Bhava", area: "Siblings, courage, effort" },
  4: { name: "Sukha Bhava", area: "Home, mother, comforts" },
  5: { name: "Putra Bhava", area: "Children, intellect, creativity" },
  6: { name: "Ripu/Roga Bhava", area: "Enemies, disease, debt, service" },
  7: { name: "Kalatra Bhava", area: "Marriage, partnerships" },
  8: { name: "Ayu/Randhra Bhava", area: "Longevity, transformation, sudden events" },
  9: { name: "Dharma Bhava", area: "Fortune, father, higher learning" },
  10: { name: "Karma Bhava", area: "Career, status, public standing" },
  11: { name: "Labha Bhava", area: "Gains, income, elder siblings, friends" },
  12: { name: "Vyaya Bhava", area: "Losses, expenses, foreign lands, moksha" },
};

function ordinal(n: number): string {
  const suffixes = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return `${n}${suffixes[(v - 20) % 10] ?? suffixes[v] ?? suffixes[0]}`;
}

function houseRef(n: number): string {
  return n === 1 ? "Lagna (1st)" : `${ordinal(n)} house`;
}

/** Wrap a house-counting offset back into 1-12. */
function wrapHouse(n: number): number {
  return (((n - 1) % 12) + 12) % 12 + 1;
}

/**
 * Which houses a planet aspects FROM a given placement house, using the
 * classical whole-sign (Rashi Drishti) counting convention — this is
 * deliberately separate from chart.aspects (which is exact-degree,
 * planet-to-planet, with orbs) because "does the 7th lord aspect Lagna"
 * needs to work even when Lagna has no occupant to be in orb of. All
 * planets get the universal 7th-house aspect; Mars, Jupiter and Saturn
 * additionally get their well-known special aspects. Rahu/Ketu never
 * appear here because they're never a rashi lord (rashiLordFromApiName
 * only returns the 7 classical grahas).
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

interface HouseInfo {
  houseNumber: number;
  rashi: string | null;
  lord: string | null;
  lordPlacementHouse: number | null;
  lordStrength: PlanetStrengthSchema | null;
  occupants: PlanetPositionSchema[];
  weak: boolean;
  weakReasons: string[];
}

type EdgeKind = "placement" | "aspect";

interface HouseEdge {
  id: string;
  from: number;
  to: number;
  kind: EdgeKind;
  lord: string;
  label: string;
  weak: boolean;
  strengthScore: number;
}

const NODE_R = 22;
const EDGE_KIND_LABEL: Record<EdgeKind, string> = {
  placement: "Lord Placement",
  aspect: "Lord Aspect",
};

/**
 * House Dependency Network — a real directed graph over all 12 houses,
 * built from two classical, computable relationships (not a fabricated
 * "flow"):
 *
 *  - Placement: house N's lord physically sits in house M → "Nth lord in
 *    Mth" (e.g. "10th lord in 2nd").
 *  - Aspect: house N's lord, from wherever it sits, casts a classical
 *    whole-sign aspect onto house M → "Nth lord aspects [Mth/Lagna]"
 *    (e.g. "7th lord aspects Lagna").
 *
 * Any house can have several outgoing edges (one placement + up to three
 * aspects, since Mars/Jupiter/Saturn cast extra aspects) and any number of
 * incoming edges from other houses whose lord happens to land on or aspect
 * it — this is a real many-to-many graph, not a linear chain.
 *
 * Edge color (red/green) and thickness both come from the SAME real
 * signal: the strength_score/dignity of the lord mediating that
 * dependency (weak = debilitated, in a dusthana, or low strength_score —
 * same criteria as the rest of this app's strength panels).
 */
export function HouseDependencyNetwork({ houses, planetStrengths, planets }: HouseDependencyNetworkProps) {
  const [hoveredHouse, setHoveredHouse] = useState<number | null>(null);
  const [pinnedHouse, setPinnedHouse] = useState<number | null>(null);
  const [activeKinds, setActiveKinds] = useState<Set<EdgeKind>>(new Set(["placement", "aspect"]));
  const activeHouse = pinnedHouse ?? hoveredHouse;

  const houseInfoByNumber = useMemo(() => {
    const map = new Map<number, HouseInfo>();
    for (let h = 1; h <= 12; h++) {
      const cusp = houses.find((c) => c.house_number === h);
      const rashi = cusp?.rashi ?? null;
      const lord = rashiLordFromApiName(rashi);
      const lordPosition = lord ? planets.find((p) => p.planet === lord) ?? null : null;
      const lordStrength = lord ? planetStrengths.find((p) => p.planet === lord) ?? null : null;
      const occupants = planets.filter((p) => p.house_number === h);

      const weakReasons: string[] = [];
      if (lordStrength?.is_debilitated) weakReasons.push(`${lord} (lord) is debilitated`);
      if (lordStrength?.is_in_dusthana) weakReasons.push(`${lord} (lord) is in a dusthana house (6/8/12)`);
      if (lordStrength && lordStrength.strength_score < WEAK_STRENGTH_THRESHOLD) {
        weakReasons.push(`${lord} (lord) strength score ${lordStrength.strength_score.toFixed(1)} < ${WEAK_STRENGTH_THRESHOLD}`);
      }

      map.set(h, {
        houseNumber: h,
        rashi,
        lord,
        lordPlacementHouse: lordPosition?.house_number ?? null,
        lordStrength,
        occupants,
        weak: weakReasons.length > 0,
        weakReasons,
      });
    }
    return map;
  }, [houses, planets, planetStrengths]);

  const allEdges = useMemo<HouseEdge[]>(() => {
    const edges: HouseEdge[] = [];
    for (let h = 1; h <= 12; h++) {
      const info = houseInfoByNumber.get(h);
      if (!info || !info.lord || info.lordPlacementHouse === null) continue;
      const score = info.lordStrength?.strength_score ?? 0;
      const weak = info.weak;

      if (info.lordPlacementHouse !== h) {
        edges.push({
          id: `${h}-placement-${info.lordPlacementHouse}`,
          from: h,
          to: info.lordPlacementHouse,
          kind: "placement",
          lord: info.lord,
          label: `${ordinal(h)} lord (${info.lord}) in ${houseRef(info.lordPlacementHouse)}`,
          weak,
          strengthScore: score,
        });
      }

      const aspected = aspectedHousesFromPlacement(info.lord, info.lordPlacementHouse);
      for (const target of aspected) {
        if (target === h) continue; // skip "aspects its own house" self-loops
        edges.push({
          id: `${h}-aspect-${target}`,
          from: h,
          to: target,
          kind: "aspect",
          lord: info.lord,
          label: `${ordinal(h)} lord (${info.lord}) aspects ${houseRef(target)}`,
          weak,
          strengthScore: score,
        });
      }
    }
    return edges;
  }, [houseInfoByNumber]);

  const edges = useMemo(() => allEdges.filter((e) => activeKinds.has(e.kind)), [allEdges, activeKinds]);

  const toggleKind = (kind: EdgeKind) => {
    setActiveKinds((prev) => {
      const next = new Set(prev);
      if (next.has(kind)) next.delete(kind);
      else next.add(kind);
      return next;
    });
  };

  if (houses.length === 0) {
    return (
      <div className="glass-card p-6 text-sm" style={{ color: "var(--text-muted)" }}>
        No house data available to build the dependency network.
      </div>
    );
  }

  const size = 480;
  const cx = size / 2;
  const cy = size / 2;
  const r = size * 0.36;

  // Circular layout, counter-clockwise from the top starting at house 1 —
  // same rotational convention as the North Indian chart, for visual
  // consistency across the app. This is a network diagram, not a literal
  // Kundli redraw, so a fixed 12-spoke wheel (rather than a diamond) is
  // used to keep 12 nodes and ~30 directed edges legible.
  const nodePos = new Map<number, { x: number; y: number }>();
  for (let h = 1; h <= 12; h++) {
    const angle = (-(h - 1) * 30 - 90) * (Math.PI / 180);
    nodePos.set(h, { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) });
  }

  const isHouseConnected = (h: number) =>
    activeHouse !== null && edges.some((e) => (e.from === activeHouse && e.to === h) || (e.to === activeHouse && e.from === h));

  const activeInfo = activeHouse ? houseInfoByNumber.get(activeHouse) ?? null : null;
  const outgoing = activeHouse ? edges.filter((e) => e.from === activeHouse) : [];
  const incoming = activeHouse ? edges.filter((e) => e.to === activeHouse && e.from !== activeHouse) : [];

  return (
    <div className="glass-card flex w-full max-w-5xl flex-col gap-5 p-5 lg:flex-row">
      <div className="flex flex-1 flex-col items-center gap-3">
        <div className="flex w-full items-center justify-between">
          <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
            House Dependency Network
          </h3>
          {pinnedHouse && (
            <button
              type="button"
              onClick={() => setPinnedHouse(null)}
              className="text-xs underline"
              style={{ color: "var(--text-muted)" }}
            >
              Clear selection
            </button>
          )}
        </div>

        <div className="flex flex-wrap gap-2">
          {(["placement", "aspect"] as EdgeKind[]).map((kind) => {
            const active = activeKinds.has(kind);
            const count = allEdges.filter((e) => e.kind === kind).length;
            return (
              <button
                key={kind}
                type="button"
                onClick={() => toggleKind(kind)}
                className="rounded-full px-2.5 py-1 text-xs transition"
                style={{
                  border: `1px solid ${active ? "var(--accent)" : "var(--border-primary)"}`,
                  color: active ? "var(--text-primary)" : "var(--text-muted)",
                  opacity: count === 0 ? 0.4 : 1,
                }}
                disabled={count === 0}
                aria-pressed={active}
              >
                {EDGE_KIND_LABEL[kind]} ({count})
              </button>
            );
          })}
        </div>

        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label="House dependency network graph">
          <defs>
            <marker id="hdn-arrow-strong" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M0,0 L10,5 L0,10 z" fill={STRONG_COLOR} />
            </marker>
            <marker id="hdn-arrow-weak" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M0,0 L10,5 L0,10 z" fill={WEAK_COLOR} />
            </marker>
          </defs>

          {/* Edges */}
          {edges.map((e) => {
            const s = nodePos.get(e.from)!;
            const t = nodePos.get(e.to)!;
            const dx = t.x - s.x;
            const dy = t.y - s.y;
            const len = Math.sqrt(dx * dx + dy * dy) || 1;
            const ux = dx / len;
            const uy = dy / len;
            const arrowGap = 10;
            const x1 = s.x + ux * NODE_R;
            const y1 = s.y + uy * NODE_R;
            const x2 = t.x - ux * (NODE_R + arrowGap);
            const y2 = t.y - uy * (NODE_R + arrowGap);
            const color = e.weak ? WEAK_COLOR : STRONG_COLOR;
            const highlighted = activeHouse !== null && (e.from === activeHouse || e.to === activeHouse);
            const dimmed = activeHouse !== null && !highlighted;
            const strokeWidth = (highlighted ? 1.5 : 1) + (e.strengthScore / 10) * 3.5;
            return (
              <g key={e.id} opacity={dimmed ? 0.08 : 1} className="transition-opacity">
                <line
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke={color}
                  strokeWidth={strokeWidth}
                  strokeDasharray={e.kind === "aspect" ? "5 3" : undefined}
                  markerEnd={e.weak ? "url(#hdn-arrow-weak)" : "url(#hdn-arrow-strong)"}
                >
                  <title>{`${e.label} — ${e.weak ? "Weak" : "Strong"} (score ${e.strengthScore.toFixed(1)}/10)`}</title>
                </line>
              </g>
            );
          })}

          {/* Nodes */}
          {Array.from(nodePos.entries()).map(([h, pos]) => {
            const info = houseInfoByNumber.get(h);
            const isActive = activeHouse === h;
            const dimmed = activeHouse !== null && !isActive && !isHouseConnected(h);
            const badgeColor = info?.weak ? WEAK_COLOR : STRONG_COLOR;
            return (
              <g
                key={h}
                transform={`translate(${pos.x}, ${pos.y})`}
                onMouseEnter={() => setHoveredHouse(h)}
                onMouseLeave={() => setHoveredHouse(null)}
                onClick={() => setPinnedHouse((prev) => (prev === h ? null : h))}
                style={{ cursor: "pointer" }}
                opacity={dimmed ? 0.25 : 1}
                className="transition-opacity"
              >
                <circle
                  r={isActive ? NODE_R + 3 : NODE_R}
                  fill={isActive ? "var(--accent)" : "var(--bg-card)"}
                  stroke={badgeColor}
                  strokeWidth={2}
                />
                <text
                  textAnchor="middle"
                  dominantBaseline="central"
                  y={-4}
                  fontSize={13}
                  fontWeight={700}
                  fill={isActive ? "var(--accent-text)" : "var(--text-primary)"}
                >
                  {h}
                </text>
                <text
                  textAnchor="middle"
                  dominantBaseline="central"
                  y={10}
                  fontSize={9}
                  fill={isActive ? "var(--accent-text)" : "var(--text-secondary)"}
                >
                  {info?.lord ? PLANET_SYMBOLS[info.lord] ?? "" : ""}
                </text>
              </g>
            );
          })}
        </svg>

        <div className="flex flex-wrap items-center justify-center gap-4 text-xs" style={{ color: "var(--text-muted)" }}>
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-0.5 w-4" style={{ backgroundColor: STRONG_COLOR }} />
            Strong dependency — lord not debilitated/dusthana, strength ≥ {WEAK_STRENGTH_THRESHOLD}
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-0.5 w-4" style={{ backgroundColor: WEAK_COLOR }} />
            Weak — lord debilitated, in a dusthana, or strength &lt; {WEAK_STRENGTH_THRESHOLD}
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-0.5 w-4 border-t-2 border-dashed" style={{ borderColor: "var(--text-muted)" }} />
            Dashed = Aspect · Solid = Placement · thicker = stronger lord
          </span>
        </div>
      </div>

      {/* Detail panel */}
      <div className="w-full lg:w-80 lg:shrink-0">
        {!activeInfo ? (
          <div
            className="glass-card flex h-full min-h-[300px] items-center justify-center p-6 text-center text-sm"
            style={{ color: "var(--text-muted)" }}
          >
            Hover a house for a quick preview, or click it to pin this panel open.
          </div>
        ) : (
          <div className="glass-card h-full overflow-y-auto p-5">
            <div className="mb-1 flex items-center justify-between">
              <h4 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
                {ordinal(activeInfo.houseNumber)} House
              </h4>
              <span
                className="rounded-full px-2 py-0.5 text-[10px] font-medium"
                style={{
                  backgroundColor: activeInfo.weak ? `${WEAK_COLOR}26` : `${STRONG_COLOR}26`,
                  color: activeInfo.weak ? WEAK_COLOR : STRONG_COLOR,
                }}
              >
                {activeInfo.weak ? "Weak" : "Strong"}
              </span>
            </div>
            <p className="mb-3 text-xs" style={{ color: "var(--text-muted)" }}>
              {HOUSE_BHAVA[activeInfo.houseNumber]?.name} — {HOUSE_BHAVA[activeInfo.houseNumber]?.area}
            </p>

            <div className="space-y-1 text-sm" style={{ color: "var(--text-secondary)" }}>
              <p>
                Rashi: <span style={{ color: "var(--text-primary)" }}>{activeInfo.rashi ?? "—"}</span>
              </p>
              <p>
                Lord: <span style={{ color: "var(--text-primary)" }}>{activeInfo.lord ?? "—"}</span>
                {activeInfo.lordPlacementHouse && ` (sitting in ${houseRef(activeInfo.lordPlacementHouse)})`}
              </p>
              {activeInfo.lordStrength && (
                <>
                  <p>Lord Strength Score: {activeInfo.lordStrength.strength_score.toFixed(1)} / 10</p>
                  <p>Lord Dignity: {activeInfo.lordStrength.dignity ?? "—"}</p>
                </>
              )}
              <p>
                Occupants:{" "}
                {activeInfo.occupants.length > 0
                  ? activeInfo.occupants.map((p) => `${PLANET_SYMBOLS[p.planet] ?? ""} ${p.planet}`).join(", ")
                  : "None"}
              </p>
            </div>

            {activeInfo.weakReasons.length > 0 && (
              <ul className="mt-2 space-y-0.5 text-[11px]" style={{ color: WEAK_COLOR }}>
                {activeInfo.weakReasons.map((reason, i) => (
                  <li key={i}>• {reason}</li>
                ))}
              </ul>
            )}

            {outgoing.length > 0 && (
              <>
                <h5 className="mb-1 mt-4 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
                  Depends On / Reaches Toward
                </h5>
                <ul className="space-y-1 text-xs" style={{ color: "var(--text-secondary)" }}>
                  {outgoing.map((e) => (
                    <li key={e.id} style={{ color: e.weak ? WEAK_COLOR : STRONG_COLOR }}>
                      → {e.label}
                    </li>
                  ))}
                </ul>
              </>
            )}

            {incoming.length > 0 && (
              <>
                <h5 className="mb-1 mt-4 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
                  Influenced By
                </h5>
                <ul className="space-y-1 text-xs" style={{ color: "var(--text-secondary)" }}>
                  {incoming.map((e) => (
                    <li key={e.id} style={{ color: e.weak ? WEAK_COLOR : STRONG_COLOR }}>
                      ← {e.label}
                    </li>
                  ))}
                </ul>
              </>
            )}

            {outgoing.length === 0 && incoming.length === 0 && (
              <p className="mt-4 text-xs" style={{ color: "var(--text-muted)" }}>
                No placement or aspect dependencies connect this house to another under the currently
                enabled edge types.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
