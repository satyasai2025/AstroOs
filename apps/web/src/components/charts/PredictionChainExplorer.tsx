"use client";

import { useMemo, useState } from "react";
import {
  getHouseLordStrength,
  getCurrentDashaChain,
  careerIndex,
  marriageIndex,
  wealthPotential,
  healthRisk,
  CAREER_YOGA_KEYWORDS,
  type HealthRiskLabel,
} from "@/lib/kpiScoring";
import { PLANET_SYMBOLS } from "@/lib/astro";
import type { WorkflowAnalysisResponse } from "@/lib/types";

interface PredictionChainExplorerProps {
  result: WorkflowAnalysisResponse;
}

type LifeArea = "marriage" | "career" | "wealth" | "health";

interface ChainNode {
  label: string;
  sublabel: string;
  badge?: string;
  badgeColor?: string;
}

const LIFE_AREAS: { key: LifeArea; label: string }[] = [
  { key: "marriage", label: "Marriage" },
  { key: "career", label: "Career" },
  { key: "wealth", label: "Wealth" },
  { key: "health", label: "Health" },
];

const STRONG = "#34d399";
const WEAK = "#f87171";
const NEUTRAL = "var(--accent)";

function strengthBadge(score: number | null | undefined): { badge: string; color: string } {
  if (score == null) return { badge: "No data", color: "var(--text-muted)" };
  if (score >= 6.5) return { badge: `${score.toFixed(1)}/10 · Strong`, color: STRONG };
  if (score >= 4) return { badge: `${score.toFixed(1)}/10 · Moderate`, color: "#fbbf24" };
  return { badge: `${score.toFixed(1)}/10 · Weak`, color: WEAK };
}

/**
 * Builds the real, chart-specific chain of reasoning behind one of the
 * synthesized KPI indices (lib/kpiScoring.ts) — this is AstroOS's honest
 * take on the vision doc's "Knowledge Graph" flow sketch (Marriage → 7th
 * House → Venus → Jupiter → Navamsa → Dasha → Prediction). Each life area
 * also shows its own classically-relevant divisional (varga) chart, not
 * just D9 for everything — Navamsa (D9) for marriage, Dasamsha (D10) for
 * career, Hora (D2) for wealth, Trimshamsha (D30) for health — see
 * vargaNode() below. Rather than a
 * generic abstract ontology graph (which would need the still-sparse
 * Karakatva database to be meaningfully populated — see the Karakatva
 * Explorer's honest scope note), this shows the ACTUAL computed values
 * for THIS chart that feed into the corresponding index, in the order
 * they're combined. Every node here traces back to a real field already
 * used by kpiScoring.ts — nothing is invented for this view.
 */
function buildChain(area: LifeArea, result: WorkflowAnalysisResponse): { nodes: ChainNode[]; finalLabel: string; finalValue: string; finalColor: string } {
  const { chart, dasha } = result;
  const dashaChain = getCurrentDashaChain(dasha.mahadashas);
  const dashaLords = dashaChain.slice(0, 2).map((p) => p.lord);

  function dashaRelevanceNode(relevantPlanets: (string | null)[]): ChainNode {
    const relevant = relevantPlanets.filter((p): p is string => !!p);
    const active = dashaLords.filter((l) => relevant.includes(l));
    return {
      label: "Current Dasha",
      sublabel: dashaLords.length > 0 ? dashaLords.join(" / ") : "No active period found",
      badge: active.length > 0 ? `Activating ${active.join(", ")}` : "Not currently activating this chain",
      badgeColor: active.length > 0 ? STRONG : "var(--text-muted)",
    };
  }

  /**
   * The classical "confirming" divisional chart differs per life area —
   * Navamsa (D9) for marriage, Dasamsha (D10) for career, and so on.
   * Reused across all four areas below with the right varga key per area,
   * instead of always checking D9 regardless of what's being asked (the
   * bug this was fixed from — Career was showing the planet's D9 placement,
   * which isn't the classically relevant varga for career at all).
   */
  function vargaNode(vargaKey: string, vargaLabel: string, planet: string | null, note?: string): ChainNode | null {
    if (!planet) return null;
    const vc = result.vargas?.charts[vargaKey];
    const vp = vc?.planet_positions.find((p) => p.planet === planet);
    if (!vp) {
      return {
        label: `${planet} in ${vargaLabel} (${vargaKey})`,
        sublabel: `${vargaKey} not computed for this analysis`,
      };
    }
    return {
      label: `${planet} in ${vargaLabel} (${vargaKey})`,
      sublabel: note ? `${vp.varga_rashi} · House ${vp.varga_house_number} — ${note}` : `${vp.varga_rashi} · House ${vp.varga_house_number}`,
    };
  }

  if (area === "marriage") {
    const seventh = getHouseLordStrength(7, chart.houses, chart.planet_strengths);
    const venus = chart.planet_strengths.find((p) => p.planet === "Venus");
    const jupiter = chart.planet_strengths.find((p) => p.planet === "Jupiter");
    const seventhBadge = strengthBadge(seventh.strength?.strength_score);
    const venusBadge = strengthBadge(venus?.strength_score);
    const jupiterBadge = strengthBadge(jupiter?.strength_score);
    const nodes: ChainNode[] = [
      { label: "Life Area", sublabel: "Marriage (Kalatra Bhava)" },
      { label: "7th House", sublabel: seventh.rashi ? `${seventh.rashi} sign` : "—" },
      { label: `Lord: ${seventh.lord ?? "—"}`, sublabel: "7th house ruler", badge: seventhBadge.badge, badgeColor: seventhBadge.color },
      { label: "Karaka: Venus", sublabel: "Spouse / romance significator", badge: venusBadge.badge, badgeColor: venusBadge.color },
      { label: "Karaka: Jupiter", sublabel: "Marital happiness significator", badge: jupiterBadge.badge, badgeColor: jupiterBadge.color },
      vargaNode("D9", "Navamsa", "Venus"),
      dashaRelevanceNode([seventh.lord, "Venus", "Jupiter"]),
    ].filter((n): n is ChainNode => n !== null);
    const value = marriageIndex(result);
    return { nodes, finalLabel: "Marriage Index", finalValue: `${value}%`, finalColor: value >= 60 ? STRONG : value >= 35 ? "#fbbf24" : WEAK };
  }

  if (area === "career") {
    const tenth = getHouseLordStrength(10, chart.houses, chart.planet_strengths);
    const tenthBadge = strengthBadge(tenth.strength?.strength_score);
    const matchedYogas = result.yogas.results.filter(
      (y) => y.is_present && CAREER_YOGA_KEYWORDS.some((kw) => y.category.toLowerCase().includes(kw) || y.name.toLowerCase().includes(kw)),
    );
    const nodes: ChainNode[] = [
      { label: "Life Area", sublabel: "Career (Karma Bhava)" },
      { label: "10th House", sublabel: tenth.rashi ? `${tenth.rashi} sign` : "—" },
      { label: `Lord: ${tenth.lord ?? "—"}`, sublabel: "10th house ruler", badge: tenthBadge.badge, badgeColor: tenthBadge.color },
      {
        label: "Career Yogas",
        sublabel: matchedYogas.length > 0 ? matchedYogas.map((y) => y.name).join(", ") : "None matched",
        badge: matchedYogas.length > 0 ? `${matchedYogas.length} present` : "0 present",
        badgeColor: matchedYogas.length > 0 ? STRONG : "var(--text-muted)",
      },
      vargaNode("D10", "Dasamsha", tenth.lord),
      dashaRelevanceNode([tenth.lord]),
    ].filter((n): n is ChainNode => n !== null);
    const value = careerIndex(result);
    return { nodes, finalLabel: "Career Index", finalValue: `${value}%`, finalColor: value >= 60 ? STRONG : value >= 35 ? "#fbbf24" : WEAK };
  }

  if (area === "wealth") {
    const second = getHouseLordStrength(2, chart.houses, chart.planet_strengths);
    const eleventh = getHouseLordStrength(11, chart.houses, chart.planet_strengths);
    const jupiter = chart.planet_strengths.find((p) => p.planet === "Jupiter");
    const secondBadge = strengthBadge(second.strength?.strength_score);
    const eleventhBadge = strengthBadge(eleventh.strength?.strength_score);
    const jupiterBadge = strengthBadge(jupiter?.strength_score);
    const nodes: ChainNode[] = [
      { label: "Life Area", sublabel: "Wealth (Dhana + Labha Bhava)" },
      { label: "2nd House", sublabel: second.rashi ? `${second.rashi} sign` : "—" },
      { label: `Lord: ${second.lord ?? "—"}`, sublabel: "2nd house ruler", badge: secondBadge.badge, badgeColor: secondBadge.color },
      { label: "11th House", sublabel: eleventh.rashi ? `${eleventh.rashi} sign` : "—" },
      { label: `Lord: ${eleventh.lord ?? "—"}`, sublabel: "11th house ruler", badge: eleventhBadge.badge, badgeColor: eleventhBadge.color },
      { label: "Karaka: Jupiter", sublabel: "Wealth/fortune significator", badge: jupiterBadge.badge, badgeColor: jupiterBadge.color },
      vargaNode("D2", "Hora", second.lord),
      dashaRelevanceNode([second.lord, eleventh.lord, "Jupiter"]),
    ].filter((n): n is ChainNode => n !== null);
    const value = wealthPotential(result);
    return { nodes, finalLabel: "Wealth Potential", finalValue: `${value}%`, finalColor: value >= 60 ? STRONG : value >= 35 ? "#fbbf24" : WEAK };
  }

  // health
  const sixth = getHouseLordStrength(6, chart.houses, chart.planet_strengths);
  const first = getHouseLordStrength(1, chart.houses, chart.planet_strengths);
  const sixthBadge = strengthBadge(sixth.strength?.strength_score);
  const firstBadge = strengthBadge(first.strength?.strength_score);
  const nodes: ChainNode[] = [
    { label: "Life Area", sublabel: "Health (Roga + Tanu Bhava)" },
    { label: "6th House", sublabel: sixth.rashi ? `${sixth.rashi} sign` : "—" },
    { label: `Lord: ${sixth.lord ?? "—"}`, sublabel: "6th house ruler (disease/injury)", badge: sixthBadge.badge, badgeColor: sixthBadge.color },
    { label: "1st House (Ascendant)", sublabel: first.rashi ? `${first.rashi} sign` : "—" },
    { label: `Lord: ${first.lord ?? "—"}`, sublabel: "Ascendant ruler (physical body)", badge: firstBadge.badge, badgeColor: firstBadge.color },
    vargaNode(
      "D30",
      "Trimshamsha",
      sixth.lord,
      "BPHS: evils/misfortunes — commonly read for health, but less universally a single \"health varga\" than D9/D10 are for marriage/career",
    ),
    dashaRelevanceNode([sixth.lord, first.lord]),
  ].filter((n): n is ChainNode => n !== null);
  const riskValue: HealthRiskLabel = healthRisk(result);
  const riskColor = riskValue === "Low" ? STRONG : riskValue === "Medium" ? "#fbbf24" : riskValue === "High" ? WEAK : "var(--text-muted)";
  return { nodes, finalLabel: "Health Risk", finalValue: riskValue, finalColor: riskColor };
}

/**
 * PredictionChainExplorer — pick a life area, see the real computed chain
 * of house → lord → karaka strength → Navamsa position → current Dasha
 * relevance → final index, for THIS chart. AstroOS's honestly-scoped
 * answer to the vision doc's "Knowledge Graph" prediction-chain sketch —
 * see the component's main doc-comment on buildChain() for why this
 * approach was chosen over a generic ontology graph.
 */
export function PredictionChainExplorer({ result }: PredictionChainExplorerProps) {
  const [area, setArea] = useState<LifeArea>("marriage");
  const chain = useMemo(() => buildChain(area, result), [area, result]);

  return (
    <div className="glass-card p-5">
      <h3 className="mb-1 text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
        Prediction Chain Explorer
      </h3>
      <p className="mb-4 text-xs" style={{ color: "var(--text-muted)" }}>
        The real chain of house, lord, and karaka data behind each KPI index — not a generic
        knowledge graph, but this chart's actual computed values in sequence.
      </p>

      <div className="mb-5 flex flex-wrap gap-2">
        {LIFE_AREAS.map((a) => (
          <button
            key={a.key}
            type="button"
            onClick={() => setArea(a.key)}
            className="rounded-full px-3 py-1 text-xs font-medium transition"
            style={{
              backgroundColor: area === a.key ? "var(--accent)" : "var(--bg-card)",
              color: area === a.key ? "var(--accent-text)" : "var(--text-secondary)",
              border: `1px solid ${area === a.key ? "var(--accent)" : "var(--border-primary)"}`,
            }}
          >
            {a.label}
          </button>
        ))}
      </div>

      <div className="flex flex-col items-center">
        {chain.nodes.map((node, i) => (
          <div key={i} className="flex w-full max-w-md flex-col items-center">
            <div
              className="w-full rounded-lg p-3"
              style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)" }}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                  {PLANET_SYMBOLS[node.label.replace("Lord: ", "").replace("Karaka: ", "")] ?? ""} {node.label}
                </span>
                {node.badge && (
                  <span
                    className="rounded-full px-2 py-0.5 text-[10px] font-medium"
                    style={{ color: node.badgeColor ?? "var(--text-secondary)", border: `1px solid ${node.badgeColor ?? "var(--border-primary)"}` }}
                  >
                    {node.badge}
                  </span>
                )}
              </div>
              <p className="mt-0.5 text-xs" style={{ color: "var(--text-secondary)" }}>
                {node.sublabel}
              </p>
            </div>
            <svg width={20} height={22} viewBox="0 0 20 22" aria-hidden="true">
              <line x1={10} y1={0} x2={10} y2={14} stroke={NEUTRAL} strokeWidth={2} />
              <polygon points="5,14 15,14 10,22" fill={NEUTRAL} />
            </svg>
          </div>
        ))}

        <div
          className="w-full max-w-md rounded-lg p-4 text-center"
          style={{ backgroundColor: "var(--bg-card)", border: `2px solid ${chain.finalColor}` }}
        >
          <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>
            {chain.finalLabel}
          </span>
          <p className="mt-1 text-2xl font-bold" style={{ color: chain.finalColor }}>
            {chain.finalValue}
          </p>
        </div>
      </div>
    </div>
  );
}
