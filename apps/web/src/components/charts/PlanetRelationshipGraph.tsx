"use client";

import { useEffect, useState, useMemo } from "react";
import * as d3 from "d3";
import { NATURAL_RELATIONSHIPS, PLANET_SYMBOLS, rashiLordFromApiName } from "@/lib/astro";
import { getCurrentDashaChain } from "@/lib/kpiScoring";
import { PlanetDetailPanel } from "@/components/charts/PlanetDetailPanel";
import type {
  AspectSchema,
  DashaPeriodResponse,
  PlanetPositionSchema,
  WorkflowAnalysisResponse,
  YogaResultResponse,
} from "@/lib/types";

interface PlanetRelationshipGraphProps {
  /** Full positions, not just names — dispositor/parivartana/yuddha detection
   * needs each planet's rashi and longitude, not just its identity. */
  planets: PlanetPositionSchema[];
  aspects: AspectSchema[];
  /** Active/present yogas for this chart — used for Yoga Participation edges.
   * Optional so existing callers that don't pass it just lose that one edge
   * kind rather than breaking. */
  yogas?: YogaResultResponse[];
  /** Real dasha tree for this chart — used for Dasha Relationship edges +
   * highlighting whichever planet's own period is running right now. */
  mahadashas?: DashaPeriodResponse[];
  /** Full workflow result — when provided, clicking a planet opens the same
   * rich PlanetDetailPanel used on the Chart tab (real computed data: house,
   * aspects, strength, yogas, varga positions, transit, classical
   * relationships) instead of just a bare tooltip. Optional so this
   * component still works standalone. */
  result?: WorkflowAnalysisResponse;
  size?: number;
}

interface GraphNode extends d3.SimulationNodeDatum {
  id: string;
}

type LinkKind =
  | "aspect"
  | "mutualAspect"
  | "friend"
  | "enemy"
  | "dispositor"
  | "nakshatraLord"
  | "conjunction"
  | "parivartana"
  | "yuddha"
  | "yoga"
  | "dasha";

interface GraphLink {
  source: string;
  target: string;
  kind: LinkKind;
  label: string;
}

/**
 * Graha Yuddha (planetary war) — classically only among these 5 grahas
 * (BPHS); Sun/Moon/Rahu/Ketu are excluded (Sun causes combustion instead,
 * not war; Rahu/Ketu are shadow points with no physical war). Two of these
 * are "at war" when conjunct within 1 degree of longitude.
 */
const YUDDHA_ELIGIBLE = new Set(["Mercury", "Venus", "Mars", "Jupiter", "Saturn"]);
const YUDDHA_ORB_DEGREES = 1;

/** MD -> AD -> PD -> ... matching the depth getCurrentDashaChain() walks —
 * same list used in KPSignificatorExplorer, kept local here to avoid a
 * cross-component import for one array. */
const DASHA_LEVEL_NAMES = ["Mahadasha", "Antardasha", "Pratyantardasha", "Sookshma", "Prana"];

/**
 * Colors loosely follow the vision doc's proposed scheme (Green=Friendly,
 * Blue=Neutral, Red=Enemy, Purple=Yoga, Gold=Raj-Yoga-grade, Black=
 * Affliction), adapted for a dark UI where pure black is invisible: Yuddha
 * (the doc's clearest "Affliction") stays in the red family instead. The
 * doc's 6 categories don't map 1:1 onto the 11 edge kinds actually
 * computed here, so a few extra hues (teal/indigo/amber) were added to
 * keep kinds that aren't Friend/Enemy/Yoga visually distinct from each
 * other — not an attempt to invent new classical color symbolism.
 */
const LINK_STYLE: Record<LinkKind, { stroke: string; dash?: string; label: string }> = {
  aspect: { stroke: "#60a5fa", label: "Aspect (this chart)" },
  mutualAspect: { stroke: "#38bdf8", label: "Mutual Aspect (both planets aspect each other)" },
  friend: { stroke: "#34d399", dash: "4 3", label: "Natural Friend (classical)" },
  enemy: { stroke: "#f87171", dash: "4 3", label: "Natural Enemy (classical)" },
  dispositor: { stroke: "#818cf8", dash: "2 4", label: "Dispositor (rules this planet's sign)" },
  nakshatraLord: { stroke: "#c084fc", dash: "1 3", label: "Nakshatra (Star) Lord" },
  conjunction: { stroke: "#22d3ee", label: "Conjunction (same house)" },
  parivartana: { stroke: "#facc15", label: "Parivartana (mutual sign exchange)" },
  yuddha: { stroke: "#fb7185", label: "Graha Yuddha (planetary war, < 1° orb)" },
  yoga: { stroke: "#a78bfa", label: "Yoga Participation" },
  dasha: { stroke: "#fb923c", label: "Dasha Relationship (currently running)" },
};

/**
 * Synthesized visual weight per edge kind — AstroOS's own heuristic for
 * how "thick" a connection should look when multiple relationship types
 * link the same two planets (e.g. Mars-Venus in Parivartana AND sharing a
 * Yoga draws thicker than either alone). These numbers are NOT a classical
 * measure of relationship strength — they're a UI convenience mirroring
 * the vision doc's own proposed weighting, scaled arbitrarily for legible
 * line widths. Don't read them as astrological fact.
 */
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

/**
 * Force-directed planet relationship graph — mixes real, chart-specific
 * edges (aspect/mutual-aspect/conjunction/dispositor/parivartana/yuddha/
 * nakshatra-lord/yoga/dasha, all computed from this chart's actual data)
 * with classical, fixed natural friend/enemy relationships (lib/astro.ts
 * NATURAL_RELATIONSHIPS, not chart-specific).
 *
 * Layout is computed once via d3-force (run synchronously to a settled
 * state), then rendered as plain SVG so click/hover interactions are
 * just React state + CSS, not a live physics re-render — clicking a
 * planet highlights its edges/neighbors, dims the rest, and (when a full
 * `result` is passed) opens the same rich detail panel used on the Chart
 * tab.
 *
 * NOT built here (left out deliberately, not fabricated): Timeline Mode
 * (animating edges as transits change over years) needs the backend to
 * compute transits at arbitrary future dates — today it only computes a
 * single "right now" snapshot (see TransitTimeline.tsx). Research Mode
 * (patterns mined from 100,000 verified charts) and the AI Layer
 * (free-form "why" explanations) both need infrastructure that doesn't
 * exist yet — this app has 3 verified-outcome charts, not 100,000, and no
 * LLM-explanation pipeline; building either would mean inventing data or
 * inventing explanations, which this project deliberately avoids.
 */
const ALL_KINDS: LinkKind[] = [
  "aspect",
  "mutualAspect",
  "friend",
  "enemy",
  "dispositor",
  "nakshatraLord",
  "conjunction",
  "parivartana",
  "yuddha",
  "yoga",
  "dasha",
];

export function PlanetRelationshipGraph({
  planets,
  aspects,
  yogas,
  mahadashas,
  result,
  size = 480,
}: PlanetRelationshipGraphProps) {
  const [selected, setSelected] = useState<string | null>(null);
  const [positions, setPositions] = useState<Record<string, { x: number; y: number }>>({});
  const [activeKinds, setActiveKinds] = useState<Set<LinkKind>>(new Set(ALL_KINDS));

  const planetNames = useMemo(() => planets.map((p) => p.planet), [planets]);

  // Currently-running dasha chain (MD -> AD -> ...), same real data/helper
  // KPSignificatorExplorer uses — not a new timing rule invented for this
  // graph.
  const dashaChain = useMemo(
    () => (mahadashas ? getCurrentDashaChain(mahadashas) : []),
    [mahadashas],
  );
  const activeDashaLordLevel = useMemo(() => {
    const map = new Map<string, string>();
    dashaChain.forEach((period, i) => {
      if (!map.has(period.lord)) map.set(period.lord, DASHA_LEVEL_NAMES[i] ?? `Level ${i + 1}`);
    });
    return map;
  }, [dashaChain]);

  const allLinks = useMemo<GraphLink[]>(() => {
    const out: GraphLink[] = [];
    const planetSet = new Set(planetNames);

    // Real aspects for this chart, split into one-way "aspect" edges and
    // "mutualAspect" edges (both planets aspect each other — a distinct,
    // classically meaningful case per the vision doc). Drawn once per
    // unordered pair either way (from_planet < to_planet for the mutual
    // case, to avoid double-drawing the same pair from both directions).
    const aspectPairKeys = new Set(
      aspects
        .filter((a) => planetSet.has(a.from_planet) && planetSet.has(a.to_planet) && a.from_planet !== a.to_planet)
        .map((a) => `${a.from_planet}|${a.to_planet}`),
    );
    for (const a of aspects) {
      if (!planetSet.has(a.from_planet) || !planetSet.has(a.to_planet) || a.from_planet === a.to_planet) continue;
      const isMutual = aspectPairKeys.has(`${a.to_planet}|${a.from_planet}`);
      if (isMutual) {
        if (a.from_planet < a.to_planet) {
          out.push({
            source: a.from_planet,
            target: a.to_planet,
            kind: "mutualAspect",
            label: `Mutual Aspect (${a.aspect_type})`,
          });
        }
      } else {
        out.push({ source: a.from_planet, target: a.to_planet, kind: "aspect", label: a.aspect_type });
      }
    }

    // Classical friend/enemy pairs, deduped (only add each unordered pair once).
    const relSeen = new Set<string>();
    for (const planet of planetNames) {
      const rel = NATURAL_RELATIONSHIPS[planet];
      if (!rel) continue;
      for (const friend of rel.friends) {
        if (!planetSet.has(friend)) continue;
        const key = [planet, friend].sort().join("|friend|");
        if (relSeen.has(key)) continue;
        relSeen.add(key);
        out.push({ source: planet, target: friend, kind: "friend", label: "Friend" });
      }
      for (const enemy of rel.enemies) {
        if (!planetSet.has(enemy)) continue;
        const key = [planet, enemy].sort().join("|enemy|");
        if (relSeen.has(key)) continue;
        relSeen.add(key);
        out.push({ source: planet, target: enemy, kind: "enemy", label: "Enemy" });
      }
    }

    // Dispositor — each planet points to the lord of the sign it occupies
    // (real, computed from this chart's actual rashi placements). Only
    // drawn when the dispositor is itself one of the displayed planets.
    const dispositorOf = new Map<string, string>();
    for (const p of planets) {
      const lord = rashiLordFromApiName(p.rashi);
      if (lord && planetSet.has(lord) && lord !== p.planet) {
        dispositorOf.set(p.planet, lord);
        out.push({ source: p.planet, target: lord, kind: "dispositor", label: `${p.planet} is disposed by ${lord}` });
      }
    }

    // Nakshatra (Star) Lord — distinct from Dispositor: this links a planet
    // to the ruler of the NAKSHATRA it occupies (a 13°20' slice), not the
    // ruler of its 30° sign. Real field already on every planet position.
    for (const p of planets) {
      const starLord = p.nakshatra_lord;
      if (starLord && planetSet.has(starLord) && starLord !== p.planet) {
        out.push({
          source: p.planet,
          target: starLord,
          kind: "nakshatraLord",
          label: `${p.planet}'s Star Lord is ${starLord}`,
        });
      }
    }

    // Conjunction — planets sharing the same (cuspal/Chalit) house, the
    // same definition already used by PlanetDetailPanel's "Conjunctions"
    // section, kept consistent here rather than redefining it by sign.
    const byHouse = new Map<number, string[]>();
    for (const p of planets) {
      if (!byHouse.has(p.house_number)) byHouse.set(p.house_number, []);
      byHouse.get(p.house_number)!.push(p.planet);
    }
    for (const group of byHouse.values()) {
      for (let i = 0; i < group.length; i++) {
        for (let j = i + 1; j < group.length; j++) {
          out.push({ source: group[i], target: group[j], kind: "conjunction", label: "Conjunction (same house)" });
        }
      }
    }

    // Parivartana (mutual sign exchange) — A is disposed by B AND B is
    // disposed by A. A real, classical yoga, not a fabricated pattern.
    const parivartanaSeen = new Set<string>();
    for (const [planet, lord] of dispositorOf) {
      if (dispositorOf.get(lord) === planet) {
        const key = [planet, lord].sort().join("|pariv|");
        if (parivartanaSeen.has(key)) continue;
        parivartanaSeen.add(key);
        out.push({ source: planet, target: lord, kind: "parivartana", label: "Parivartana (mutual exchange)" });
      }
    }

    // Graha Yuddha (planetary war) — two war-eligible grahas conjunct
    // within 1° of longitude. Computed from real sidereal_longitude.
    const yuddhaCandidates = planets.filter((p) => YUDDHA_ELIGIBLE.has(p.planet));
    for (let i = 0; i < yuddhaCandidates.length; i++) {
      for (let j = i + 1; j < yuddhaCandidates.length; j++) {
        const a = yuddhaCandidates[i];
        const b = yuddhaCandidates[j];
        const diff = Math.abs(a.sidereal_longitude - b.sidereal_longitude);
        const orb = Math.min(diff, 360 - diff);
        if (orb <= YUDDHA_ORB_DEGREES) {
          out.push({ source: a.planet, target: b.planet, kind: "yuddha", label: `Graha Yuddha (${orb.toFixed(2)}° orb)` });
        }
      }
    }

    // Yoga Participation — connect every pair of planets that are both
    // named as involved_planets on the SAME currently-present yoga (real
    // yoga-engine output, not inferred). Multi-planet yogas draw one edge
    // per pair, which is intentional: a pair backed by more shared yogas
    // should read as more strongly linked via the combined-weight system
    // below.
    if (yogas) {
      for (const y of yogas) {
        if (!y.is_present) continue;
        const involved = y.involved_planets.filter((p) => planetSet.has(p));
        for (let i = 0; i < involved.length; i++) {
          for (let j = i + 1; j < involved.length; j++) {
            out.push({ source: involved[i], target: involved[j], kind: "yoga", label: y.name });
          }
        }
      }
    }

    // Dasha Relationship — link consecutive levels of the dasha chain
    // that's actually running right now (MD lord -> AD lord -> ...), same
    // real chain KPSignificatorExplorer's "Dasha Now" column uses.
    if (dashaChain.length > 1) {
      for (let i = 0; i < dashaChain.length - 1; i++) {
        const a = dashaChain[i].lord;
        const b = dashaChain[i + 1].lord;
        if (a !== b && planetSet.has(a) && planetSet.has(b)) {
          out.push({
            source: a,
            target: b,
            kind: "dasha",
            label: `${DASHA_LEVEL_NAMES[i] ?? "Level " + (i + 1)} (${a}) running under ${DASHA_LEVEL_NAMES[i + 1] ?? "Level " + (i + 2)} (${b})`,
          });
        }
      }
    }

    return out;
  }, [planets, planetNames, aspects, yogas, dashaChain]);

  const links = useMemo(() => allLinks.filter((l) => activeKinds.has(l.kind)), [allLinks, activeKinds]);

  // Combined synthesized weight per unordered planet pair, summed across
  // every currently-visible edge kind connecting them — this is what makes
  // a pair with several simultaneous relationship types (e.g. Parivartana
  // + shared Yoga) read as a visibly thicker connection, per the vision
  // doc. See the LINK_WEIGHT comment above for the "not classical fact"
  // caveat.
  const pairWeight = useMemo(() => {
    const map = new Map<string, number>();
    for (const l of links) {
      const key = [l.source, l.target].sort().join("|");
      map.set(key, (map.get(key) ?? 0) + LINK_WEIGHT[l.kind]);
    }
    return map;
  }, [links]);

  // Top pairs by combined weight, for the "Top Relationships" summary card
  // — same real pairWeight data the edge thickness above is drawn from,
  // just ranked and listed as text for a quick scan.
  const topPairs = useMemo(() => {
    const kindsByPair = new Map<string, Set<LinkKind>>();
    for (const l of links) {
      const key = [l.source, l.target].sort().join("|");
      if (!kindsByPair.has(key)) kindsByPair.set(key, new Set());
      kindsByPair.get(key)!.add(l.kind);
    }
    return Array.from(pairWeight.entries())
      .map(([key, weight]) => ({
        key,
        planets: key.split("|"),
        weight,
        kinds: Array.from(kindsByPair.get(key) ?? []),
      }))
      .sort((a, b) => b.weight - a.weight)
      .slice(0, 6);
  }, [pairWeight, links]);

  const toggleKind = (kind: LinkKind) => {
    setActiveKinds((prev) => {
      const next = new Set(prev);
      if (next.has(kind)) next.delete(kind);
      else next.add(kind);
      return next;
    });
  };

  useEffect(() => {
    const nodes: GraphNode[] = planetNames.map((id) => ({ id }));
    // Lay out using ALL possible links (not just currently-filtered ones) so
    // toggling a filter doesn't reshuffle the node positions underneath you.
    const simLinks = allLinks.map((l) => ({ ...l }));

    const simulation = d3
      .forceSimulation(nodes)
      .force(
        "link",
        d3
          .forceLink<GraphNode, d3.SimulationLinkDatum<GraphNode>>(simLinks as unknown as d3.SimulationLinkDatum<GraphNode>[])
          .id((d) => (d as GraphNode).id)
          .distance(110),
      )
      .force("charge", d3.forceManyBody().strength(-220))
      .force("center", d3.forceCenter(size / 2, size / 2))
      .force("collide", d3.forceCollide(36))
      .stop();

    // Run synchronously to a settled layout instead of animating ticks.
    simulation.tick(300);

    const next: Record<string, { x: number; y: number }> = {};
    for (const n of nodes) {
      const margin = 40;
      next[n.id] = {
        x: Math.max(margin, Math.min(size - margin, n.x ?? size / 2)),
        y: Math.max(margin, Math.min(size - margin, n.y ?? size / 2)),
      };
    }
    setPositions(next);
  }, [planetNames, allLinks, size]);

  if (planetNames.length === 0 || Object.keys(positions).length === 0) {
    return (
      <div className="glass-card p-6 text-sm" style={{ color: "var(--text-muted)" }}>
        No planet data available to graph.
      </div>
    );
  }

  const isDimmed = (planet: string) => selected !== null && selected !== planet && !isConnected(planet);

  function isConnected(planet: string): boolean {
    if (!selected) return false;
    return links.some(
      (l) =>
        (l.source === selected && l.target === planet) ||
        (l.target === selected && l.source === planet),
    );
  }

  // Left sidebar: chart summary (real derived counts, no fabricated stats)
  // + the relationship-type filter, moved out of the graph card into its
  // own column so it reads as a persistent control panel rather than a
  // row of buttons crowding the top of the graph (mockup layout).
  const infoPanel = (
    <div className="glass-card p-4">
      <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
        Chart Info
      </h4>
      <dl className="space-y-1.5 text-xs">
        <div className="flex justify-between">
          <dt style={{ color: "var(--text-muted)" }}>Planets plotted</dt>
          <dd style={{ color: "var(--text-primary)" }}>{planetNames.length}</dd>
        </div>
        <div className="flex justify-between">
          <dt style={{ color: "var(--text-muted)" }}>Total relationships</dt>
          <dd style={{ color: "var(--text-primary)" }}>{allLinks.length}</dd>
        </div>
        <div className="flex justify-between">
          <dt style={{ color: "var(--text-muted)" }}>Visible now</dt>
          <dd style={{ color: "var(--text-primary)" }}>{links.length}</dd>
        </div>
      </dl>
    </div>
  );

  const filterPanel = (
    <div className="glass-card p-4">
      <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
        Relationship Types
      </h4>
      {/* Dynamic filtering — toggle which relationship types are shown.
          Layout stays fixed (see the simulation effect above) so toggling
          doesn't reshuffle the graph. */}
      <div className="flex flex-col gap-1.5">
        {ALL_KINDS.map((kind) => {
          const style = LINK_STYLE[kind];
          const active = activeKinds.has(kind);
          const count = allLinks.filter((l) => l.kind === kind).length;
          return (
            <button
              key={kind}
              type="button"
              onClick={() => toggleKind(kind)}
              className="flex items-center gap-1.5 rounded-lg px-2 py-1 text-left text-xs transition"
              style={{
                border: `1px solid ${active ? style.stroke : "var(--border-primary)"}`,
                color: active ? "var(--text-primary)" : "var(--text-muted)",
                opacity: count === 0 ? 0.4 : 1,
              }}
              disabled={count === 0}
              aria-pressed={active}
            >
              <span
                className="inline-block h-0.5 w-3 shrink-0"
                style={{ backgroundColor: active ? style.stroke : "var(--border-primary)" }}
              />
              <span className="flex-1">{style.label.split(" (")[0]}</span>
              <span style={{ color: "var(--text-muted)" }}>{count}</span>
            </button>
          );
        })}
      </div>
    </div>
  );

  // Right sidebar: top-weighted pairs, ranked from the same real pairWeight
  // data that drives edge thickness — a quick-scan summary rather than a
  // duplicate of the graph.
  const topPairsPanel = (
    <div className="glass-card p-4">
      <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
        Top Relationships
      </h4>
      {topPairs.length === 0 ? (
        <p className="text-xs" style={{ color: "var(--text-muted)" }}>
          No relationships match the current filters.
        </p>
      ) : (
        <ul className="space-y-2">
          {topPairs.map((pair) => (
            <li
              key={pair.key}
              className="cursor-pointer rounded-lg p-2 text-xs transition hover:opacity-80"
              style={{ border: "1px solid var(--border-primary)" }}
              onClick={() => setSelected(pair.planets[0])}
            >
              <div className="mb-1 flex items-center justify-between">
                <span className="font-medium" style={{ color: "var(--text-primary)" }}>
                  {PLANET_SYMBOLS[pair.planets[0]] ?? ""} {pair.planets[0]} – {PLANET_SYMBOLS[pair.planets[1]] ?? ""} {pair.planets[1]}
                </span>
                <span style={{ color: "var(--text-muted)" }}>{pair.weight}</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {pair.kinds.map((k) => (
                  <span
                    key={k}
                    className="rounded-full px-1.5 py-0.5"
                    style={{ backgroundColor: `${LINK_STYLE[k].stroke}22`, color: LINK_STYLE[k].stroke }}
                  >
                    {LINK_STYLE[k].label.split(" (")[0]}
                  </span>
                ))}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );

  const graphBody = (
    <div className="glass-card p-5">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
          Planet Relationship Graph
        </h3>
        {selected && (
          <button
            type="button"
            onClick={() => setSelected(null)}
            className="text-xs underline"
            style={{ color: "var(--text-muted)" }}
          >
            Clear selection
          </button>
        )}
      </div>

      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label="Planet relationship network graph">
        {/* Edges */}
        {links.map((l, i) => {
          const s = positions[l.source];
          const t = positions[l.target];
          if (!s || !t) return null;
          const highlighted = selected && (l.source === selected || l.target === selected);
          const dimmed = selected && !highlighted;
          const style = LINK_STYLE[l.kind];
          const weight = pairWeight.get([l.source, l.target].sort().join("|")) ?? LINK_WEIGHT[l.kind];
          const strokeWidth = Math.min(highlighted ? 6.5 : 5, (highlighted ? 1.8 : 1) + weight / 4);
          return (
            <g key={i} opacity={dimmed ? 0.12 : 1} className="transition-opacity">
              <line
                x1={s.x}
                y1={s.y}
                x2={t.x}
                y2={t.y}
                stroke={style.stroke}
                strokeWidth={strokeWidth}
                strokeDasharray={style.dash}
              />
            </g>
          );
        })}

        {/* Nodes */}
        {planetNames.map((planet) => {
          const pos = positions[planet];
          if (!pos) return null;
          const active = selected === planet;
          const dimmed = isDimmed(planet);
          const dashaLevel = activeDashaLordLevel.get(planet);
          return (
            <g
              key={planet}
              transform={`translate(${pos.x}, ${pos.y})`}
              onClick={() => setSelected(active ? null : planet)}
              style={{ cursor: "pointer" }}
              opacity={dimmed ? 0.3 : 1}
              className="transition-opacity"
            >
              {/* Amber outer ring — this planet's own dasha level is
                  running right now (Dasha Relationship, real dasha-tree
                  data, same as KP Significators' "Dasha Now" column). */}
              {dashaLevel && (
                <circle r={active ? 27 : 23} fill="none" stroke="#fb923c" strokeWidth={2} strokeDasharray="3 2">
                  <title>{`${planet}'s own ${dashaLevel} is running right now`}</title>
                </circle>
              )}
              <circle
                r={active ? 22 : 18}
                fill={active ? "var(--accent)" : "var(--bg-card)"}
                stroke="var(--accent)"
                strokeWidth={active ? 0 : 1.5}
              />
              <text
                textAnchor="middle"
                dominantBaseline="central"
                fontSize={14}
                fill={active ? "var(--accent-text)" : "var(--text-primary)"}
                fontWeight={600}
              >
                {PLANET_SYMBOLS[planet] ?? planet.slice(0, 2)}
              </text>
              <text
                y={active ? 34 : 30}
                textAnchor="middle"
                fontSize={10}
                fill="var(--text-secondary)"
              >
                {planet}
              </text>
            </g>
          );
        })}
      </svg>

      <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
        Click a planet to highlight its connections{result ? " and open its full detail panel" : ""}. Use the
        buttons above to show/hide each relationship type — line thickness reflects how many relationship
        types connect a given pair (AstroOS&apos;s own synthesized weighting, not a classical measure).
        {activeDashaLordLevel.size > 0 && " The dashed amber ring marks whichever planet's own dasha period is running right now."}
      </p>
    </div>
  );

  return (
    <div className="flex flex-col gap-5 lg:flex-row lg:items-start">
      {/* Left column: chart summary + relationship-type filter */}
      <div className="w-full space-y-4 lg:w-60 lg:shrink-0">
        {infoPanel}
        {filterPanel}
      </div>

      {/* Center column: the graph itself */}
      <div className="min-w-0 flex-1">{graphBody}</div>

      {/* Right column: ranked top relationships + (when available) the
          full detail panel for whichever planet is selected. */}
      <div className="w-full space-y-4 lg:w-80 lg:shrink-0">
        {topPairsPanel}
        {result && (
          <PlanetDetailPanel
            planet={selected}
            result={result}
            pinned={selected !== null}
            onUnpin={() => setSelected(null)}
          />
        )}
      </div>
    </div>
  );
}
