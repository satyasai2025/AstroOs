/**
 * AstroOS — Prediction Chain Explorer: graph builder
 *
 * The only place that turns real chart data + PREDICTION_FACTORS
 * (scoring.ts) into a PredictionGraph. Pure function, no React — the
 * resulting object is plain and serializable, so the same computation can
 * later feed an AI explanation prompt or a JSON/PDF export without being
 * recomputed.
 *
 * categories / confidence / dataSources / dashaTimeline are all DERIVED
 * from the node list here, never maintained as separate hardcoded
 * structures — adding a factor to scoring.ts automatically shows up
 * everywhere without touching this file or any UI component.
 */

import { rashiLordFromApiName } from "@/lib/astro";
import { getCurrentDashaChain } from "@/lib/kpiScoring";
import { PREDICTION_FACTORS } from "./scoring";
import {
  AREA_LABELS,
  PRIMARY_HOUSE_BY_AREA,
  type CategoryTotal,
  type ChainContext,
  type ConfidenceInfo,
  type DashaTimelineEntry,
  type DataSourceEntry,
  type LifeArea,
  type PredictionGraph,
  type PredictionNode,
  type RelatedRuleEntry,
} from "./types";
import type { AvasthaListResponse } from "@/lib/avastha";
import type { AllShadbalaResponse } from "@/lib/shadbala";
import type { WorkflowAnalysisResponse, YogaResultResponse } from "@/lib/types";

const BASELINE_SCORE = 50;
const CONFIDENCE_HIGH_THRESHOLD = 90;
const CONFIDENCE_MEDIUM_THRESHOLD = 60;

export interface BuildPredictionGraphExtras {
  avastha?: AvasthaListResponse;
  shadbalaAll?: AllShadbalaResponse;
}

function unavailableReason(factorId: string, ctx: ChainContext): string {
  if (!ctx.lord) return "The house lord could not be resolved for this chart";
  if (factorId === "digbala" && !ctx.shadbalaAll) return "Digbala breakdown (shadbala/all) hasn't loaded";
  if (factorId === "avastha" && !ctx.avastha) return "Avastha data hasn't loaded";
  return `No data found for ${ctx.lord} for this factor in this chart`;
}

function confidenceFromNodes(nodes: PredictionNode[]): ConfidenceInfo {
  const applicable = nodes.length;
  const available = nodes.filter((n) => !n.unavailable).length;
  const dataCompletePercent = applicable === 0 ? 0 : Math.round((available / applicable) * 100);
  const level: ConfidenceInfo["level"] =
    dataCompletePercent >= CONFIDENCE_HIGH_THRESHOLD ? "High" : dataCompletePercent >= CONFIDENCE_MEDIUM_THRESHOLD ? "Medium" : "Low";
  return {
    level,
    dataCompletePercent,
    missing: nodes.filter((n) => n.unavailable).map((n) => n.label),
  };
}

function categoriesFromNodes(nodes: PredictionNode[]): CategoryTotal[] {
  const byCategory = new Map<string, CategoryTotal>();
  for (const node of nodes) {
    const existing = byCategory.get(node.category);
    if (existing) {
      existing.delta += node.delta;
      existing.nodeCount += 1;
    } else {
      byCategory.set(node.category, { category: node.category, delta: node.delta, nodeCount: 1 });
    }
  }
  return Array.from(byCategory.values());
}

function dataSourcesFromNodes(nodes: PredictionNode[]): DataSourceEntry[] {
  return nodes.map((n) => ({ id: n.id, label: n.label, available: !n.unavailable, reason: n.unavailableReason }));
}

/** Real classical citations behind this graph's matched yogas — pulled
 * straight off the "yogas" node's raw.matched (itself sourced from
 * YogaResultResponse.source_text/rule_version, the backend's real rule
 * engine output). Never a fabricated scripture reference: if a chart has
 * no matched yogas, this list is simply empty. */
function relatedRulesFromNodes(nodes: PredictionNode[]): RelatedRuleEntry[] {
  const yogasNode = nodes.find((n) => n.id === "yogas");
  const matched = (yogasNode?.raw.matched as YogaResultResponse[] | undefined) ?? [];
  return matched.map((y) => ({ yogaName: y.name, sourceText: y.source_text, ruleVersion: y.rule_version }));
}

function buildDashaTimeline(result: WorkflowAnalysisResponse): DashaTimelineEntry[] {
  const mahadashas = result.dasha.mahadashas;
  const chain = getCurrentDashaChain(mahadashas);
  const currentMaha = chain[0] ?? null;
  return mahadashas.map((p) => ({
    lord: p.lord,
    level: p.level,
    startDate: p.start_date,
    endDate: p.end_date,
    isCurrent: !!currentMaha && currentMaha.lord === p.lord && currentMaha.start_date === p.start_date,
  }));
}

export function buildPredictionGraph(area: LifeArea, result: WorkflowAnalysisResponse, extras: BuildPredictionGraphExtras = {}): PredictionGraph {
  const houseNumber = PRIMARY_HOUSE_BY_AREA[area];
  const house = result.chart.houses.find((h) => h.house_number === houseNumber);
  const lord = rashiLordFromApiName(house?.rashi ?? null);

  const ctx: ChainContext = {
    area,
    result,
    houseNumber,
    lord,
    avastha: extras.avastha,
    shadbalaAll: extras.shadbalaAll,
  };

  const applicableFactors = PREDICTION_FACTORS.filter((f) => f.appliesTo(area));

  const nodes: PredictionNode[] = applicableFactors.map((factor) => {
    const available = factor.isAvailable(ctx);
    if (!available) {
      return {
        id: factor.id,
        label: factor.label,
        category: factor.category,
        formulaId: factor.id,
        formulaVersion: factor.formulaVersion,
        delta: 0,
        inputs: {},
        raw: {},
        source: [],
        detail: [],
        subFactors: [],
        maxPossible: 0,
        parentId: lord ?? `house-${houseNumber}`,
        unavailable: true,
        unavailableReason: unavailableReason(factor.id, ctx),
      };
    }
    const computed = factor.compute(ctx);
    return {
      id: factor.id,
      label: factor.label,
      category: factor.category,
      formulaId: factor.id,
      formulaVersion: factor.formulaVersion,
      delta: computed.delta,
      inputs: computed.inputs,
      raw: computed.raw,
      source: computed.source,
      detail: computed.detail,
      subFactors: computed.subFactors,
      maxPossible: computed.maxPossible,
      parentId: lord ?? `house-${houseNumber}`,
      unavailable: false,
    };
  });

  const totalDelta = nodes.reduce((sum, n) => sum + n.delta, 0);
  const finalScore = Math.round(Math.min(100, Math.max(0, BASELINE_SCORE + totalDelta)));

  return {
    area,
    areaLabel: AREA_LABELS[area],
    houseNumber,
    lord,
    baseline: BASELINE_SCORE,
    finalScore,
    finalLabel: `${AREA_LABELS[area]} Strength`,
    nodes,
    categories: categoriesFromNodes(nodes),
    confidence: confidenceFromNodes(nodes),
    dataSources: dataSourcesFromNodes(nodes),
    dashaTimeline: buildDashaTimeline(result),
    relatedRules: relatedRulesFromNodes(nodes),
  };
}
