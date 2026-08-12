/**
 * PlanetExplorer — deterministic interpretation engine.
 *
 * Pure, template-based and fully offline. It derives a Core Expression plus
 * Supporting / Modifying factors, a factual Activation and an Evidence list
 * from the *actual* chart values in a PlanetContext — never from a generic
 * horoscope and never from fabrications. Every claim it makes points back at
 * data that is genuinely present, which keeps the Evidence panel honest.
 */

import { KARAKATVA_BASIC, NATURAL_RELATIONSHIPS } from "@/lib/astro";
import { REF_UNAVAILABLE } from "@/lib/astroStructural";
import { resolveStructuralColumns, type PlanetContext } from "./context";

export type EvidenceKind =
  | "structural"
  | "strength"
  | "relationship"
  | "yoga"
  | "dasha"
  | "transit";

export interface EvidenceItem {
  label: string;
  /** Tab/source this derives from. */
  source: string;
  kind: EvidenceKind;
}

export interface PlanetInterpretation {
  coreExpression: string;
  supporting: string[];
  modifying: string[];
  activation: string;
  evidence: EvidenceItem[];
}

function relToDispositor(ctx: PlanetContext): { rel: string; isFriendly: boolean } | null {
  if (!ctx.position) return null;
  const natural = NATURAL_RELATIONSHIPS[ctx.planet];
  if (!natural || !ctx.dispositor || ctx.dispositor === ctx.planet) return null;
  if (natural.friends.includes(ctx.dispositor)) return { rel: `friendly dispositor ${ctx.dispositor}`, isFriendly: true };
  if (natural.enemies.includes(ctx.dispositor)) return { rel: `enemy dispositor ${ctx.dispositor}`, isFriendly: false };
  return { rel: `neutral dispositor ${ctx.dispositor}`, isFriendly: true };
}

/** Build the deterministic interpretation for one graha. */
export function interpret(ctx: PlanetContext): PlanetInterpretation {
  const p = ctx.position;
  const cols = resolveStructuralColumns(ctx);
  const col = (k: "rashi" | "graha" | "bhava" | "nakshatra") => cols.find((c) => c.key === k);
  const blam = (
    k: "rashi" | "graha" | "bhava" | "nakshatra",
    idx: number,
  ): string | null => {
    const c = col(k);
    const v = c?.values[idx];
    return v && v !== REF_UNAVAILABLE ? v : null;
  };

  const evidence: EvidenceItem[] = [];
  const supporting: string[] = [];
  const modifying: string[] = [];

  // Structural layer.
  const grahaGuna = blam("graha", 1); // psychological guna
  const rashiElement = blam("rashi", 2); // tatva
  const bhavaGoal = blam("bhava", 0); // purushartha
  const nakGana = blam("nakshatra", 8); // gana
  const nakDeity = blam("nakshatra", 4); // deity

  const parts: string[] = [];
  if (grahaGuna) parts.push(`a ${grahaGuna} nature`);
  if (rashiElement) parts.push(`in ${p?.rashi} (${rashiElement} sign)`);
  if (bhavaGoal) parts.push(`orienting the ${p?.house_number} house (${bhavaGoal})`);
  if (nakGana && nakDeity) parts.push(`under ${p?.nakshatra} (${nakGana}, deity ${nakDeity})`);
  else if (p?.nakshatra) parts.push(`under ${p?.nakshatra}`);

  const coreExpression = parts.length
    ? `${ctx.planet} here expresses ${parts.join(", ")}.`
    : `${ctx.planet} occupies ${p?.rashi ?? "the"} ${p ? `House ${p.house_number}` : "chart"}.`;

  if (nakGana) evidence.push({ label: `Nakshatra gana: ${nakGana}`, source: "Structure · Nakshatra", kind: "structural" });
  if (grahaGuna) evidence.push({ label: `Psychological guna: ${grahaGuna}`, source: "Structure · Graha", kind: "structural" });
  if (rashiElement) evidence.push({ label: `Element: ${rashiElement}`, source: "Structure · Rashi", kind: "structural" });

  // Strength layer.
  if (ctx.strength) {
    supporting.push(`Overall strength ${ctx.strength.score}% (${ctx.strength.band}).`);
    evidence.push({ label: `Strength ${ctx.strength.score}%`, source: "Strength", kind: "strength" });
  }
  if (ctx.strength?.isExalted) { supporting.push("Exalted placement magnifies its expression."); evidence.push({ label: "Exalted", source: "Strength", kind: "strength" }); }
  if (ctx.strength?.isOwnSign) { supporting.push("Own-sign placement gives stable authority."); evidence.push({ label: "Own sign", source: "Strength", kind: "strength" }); }
  if (ctx.strength?.isDebilitated) { modifying.push("Debilitated placement curbs the expression."); evidence.push({ label: "Debilitated", source: "Strength", kind: "strength" }); }
  if (ctx.strength?.isInDusthana) { modifying.push("Placed in a dusthana, results emerge with effort."); evidence.push({ label: `Dusthana (House ${ctx.strength.houseNumber})`, source: "Strength", kind: "strength" }); }
  if (p?.is_retrograde) { modifying.push("Retrogression turns the energy inward/repeated."); evidence.push({ label: "Retrograde", source: "Strength", kind: "strength" }); }
  if (p?.is_combust) { modifying.push("Combustion weakens visible expression."); evidence.push({ label: `Combust (orb ${p.combustion_orb?.toFixed(1) ?? "—"}°)`, source: "Strength", kind: "strength" }); }

  // Relationship layer.
  const disp = relToDispositor(ctx);
  if (disp) {
    if (disp.isFriendly) supporting.push(`Operates through a ${disp.rel}.`);
    else modifying.push(`Operates under a ${disp.rel}, adding friction.`);
    evidence.push({ label: `Dispositor: ${ctx.dispositor}`, source: "Relationships · Dispositor", kind: "relationship" });
  }
  if (ctx.conjunctions.length) {
    supporting.push(`Conjunct with ${ctx.conjunctions.join(", ")}.`);
    evidence.push({ label: `Conjunction with ${ctx.conjunctions.join(", ")}`, source: "Relationships · Conjunctions", kind: "relationship" });
  }

  // Yoga layer.
  for (const y of ctx.yogasInvolving) {
    supporting.push(`Activates the yoga ${y.name}.`);
    evidence.push({ label: `Yoga: ${y.name}`, source: "Yogas", kind: "yoga" });
  }

  // Political/karakatva.
  const kar = KARAKATVA_BASIC[ctx.planet] ?? [];
  if (kar.length && ctx.houseOwnerOf.length) {
    supporting.push(`Signifies ${kar.slice(0, 3).join(", ")} and rules ${ctx.houseOwnerOf.map((h) => `House ${h}`).join(", ")}.`);
    evidence.push({ label: `Owns ${ctx.houseOwnerOf.map((h) => `H${h}`).join(", ")}`, source: "Overview · House Ownership", kind: "relationship" });
  }

  // Activation layer.
  let activation: string;
  const chainActive = ctx.dashaChain.map((d) => d.lord);
  const activeHit = chainActive.includes(ctx.planet);
  if (activeHit) {
    const pos = chainActive.indexOf(ctx.planet);
    const host = chainActive.slice(0, pos + 1).join(" → ");
    activation = `${ctx.planet} is currently operative via the dasha chain ${host}.`;
    evidence.push({ label: `Active in dasha chain: ${host}`, source: "Dasha", kind: "dasha" });
  } else if (ctx.transit) {
    activation = `${ctx.planet} is not in the running dasha chain; its matters are currently stimulated by transit through ${ctx.transit.transit_rashi}.`;
    evidence.push({ label: `Transit through ${ctx.transit.transit_rashi}`, source: "Transit", kind: "transit" });
  } else {
    activation = `No dasha or transit activation is currently detected for ${ctx.planet}.`;
  }

  return {
    coreExpression,
    supporting,
    modifying,
    activation,
    evidence,
  };
}