"use client";

import { useMemo, useState } from "react";
import type { JaiminiBundleResponse } from "@/lib/types";

interface Props {
  bundle?: JaiminiBundleResponse | null;
  rashiNames?: string[];
  planetPositions?: Array<{ planet: string; rashi: string; degree: number; is_retrograde?: boolean }>;
}

const RASHIS = [
  "Aries", "Taurus", "Gemini", "Cancer",
  "Leo", "Virgo", "Libra", "Scorpio",
  "Sagittarius", "Capricorn", "Aquarius", "Pisces"
];

const RASHI_SANSKRIT: Record<string, string> = {
  aries: "Mesha",
  taurus: "Vrishabha",
  gemini: "Mithuna",
  cancer: "Karka",
  leo: "Simha",
  virgo: "Kanya",
  libra: "Tula",
  scorpio: "Vrishchika",
  sagittarius: "Dhanu",
  capricorn: "Makara",
  aquarius: "Kumbha",
  pisces: "Meena",
};

const NATURAL_BENEFICS = new Set(["jupiter", "venus", "mercury"]);
const NATURAL_MALEFICS = new Set(["sun", "mars", "saturn", "rahu", "ketu"]);

interface ArgalaPairConfig {
  type: "Primary" | "Secondary";
  argalaHouse: number;
  virodhaHouse: number;
  label: string;
  signification: string;
  sutraRef: string;
}

const ARGALA_CONFIGS: ArgalaPairConfig[] = [
  {
    type: "Primary",
    argalaHouse: 2,
    virodhaHouse: 12,
    label: "2nd House Argala (Dhana / Sustenance)",
    signification: "Nourishment, accumulated resources, and speech intervening upon the anchor",
    sutraRef: "Jaimini Upadesa Sutras 1.1.4 (Dhanasukhlabhabhyo)",
  },
  {
    type: "Primary",
    argalaHouse: 4,
    virodhaHouse: 10,
    label: "4th House Argala (Sukha / Foundation)",
    signification: "Inner peace, domicile, mother, education, and emotional foundation",
    sutraRef: "Jaimini Upadesa Sutras 1.1.4",
  },
  {
    type: "Primary",
    argalaHouse: 11,
    virodhaHouse: 3,
    label: "11th House Argala (Labha / Fulfillment)",
    signification: "Gains, elder siblings, network circles, and realization of desires",
    sutraRef: "Jaimini Upadesa Sutras 1.1.4",
  },
  {
    type: "Secondary",
    argalaHouse: 5,
    virodhaHouse: 9,
    label: "5th House Argala (Putra / Intellect)",
    signification: "Secondary intervention: creative genius, purva punya, discernment, and progeny",
    sutraRef: "Jaimini Upadesa Sutras 1.1.5 (Kamasthasya / Sutargala)",
  },
];

export function ArgalaFlowGraph({ bundle, planetPositions = [] }: Props) {
  const [selectedReferenceType, setSelectedReferenceType] = useState<"standard" | "bhava" | "graha">("standard");
  const [selectedReference, setSelectedReference] = useState<string>("Lagna");
  const [hoveredNode, setHoveredNode] = useState<number | null>(null);
  const [showCalculationTrace, setShowCalculationTrace] = useState<boolean>(true);

  // Derive available reference items
  const atmakarakaPlanet = bundle?.chara_karaka?.atmakaraka?.planet ?? "Sun";
  const lagnaRashiName = bundle?.chara_dasha?.lagna_rashi ?? "Aries";

  // Resolve active anchor sign
  const resolvedAnchorRashi = useMemo(() => {
    const cleanRef = selectedReference.toLowerCase().trim();
    if (cleanRef === "lagna") {
      return lagnaRashiName;
    }
    if (cleanRef === "atmakaraka" || cleanRef === "ak") {
      const p = planetPositions.find((pos) => pos.planet.toLowerCase() === atmakarakaPlanet.toLowerCase());
      return p ? p.rashi : lagnaRashiName;
    }
    if (cleanRef === "moon") {
      const p = planetPositions.find((pos) => pos.planet.toLowerCase() === "moon");
      return p ? p.rashi : lagnaRashiName;
    }
    // Bhava house check (e.g. "house 4")
    if (cleanRef.startsWith("house ")) {
      const hNum = parseInt(cleanRef.replace("house ", ""), 10);
      if (!isNaN(hNum) && hNum >= 1 && hNum <= 12) {
        const lagnaIdx = RASHIS.findIndex((r) => r.toLowerCase() === lagnaRashiName.toLowerCase());
        const validIdx = lagnaIdx >= 0 ? lagnaIdx : 0;
        return RASHIS[(validIdx + hNum - 1) % 12];
      }
    }
    // Planet check
    const matchedPlanet = planetPositions.find((pos) => pos.planet.toLowerCase() === cleanRef);
    if (matchedPlanet) {
      return matchedPlanet.rashi;
    }
    // Direct Rashi name
    const matchedRashi = RASHIS.find((r) => r.toLowerCase() === cleanRef);
    if (matchedRashi) return matchedRashi;

    return lagnaRashiName;
  }, [selectedReference, lagnaRashiName, atmakarakaPlanet, planetPositions]);

  const anchorRashiIndex = useMemo(() => {
    const idx = RASHIS.findIndex((r) => r.toLowerCase() === resolvedAnchorRashi.toLowerCase());
    return idx >= 0 ? idx : 0;
  }, [resolvedAnchorRashi]);

  const getRashiForHouse = (h: number): string => {
    return RASHIS[(anchorRashiIndex + h - 1) % 12];
  };

  const getPlanetsInHouse = (h: number) => {
    const targetRashi = getRashiForHouse(h);
    return planetPositions.filter((p) => p.rashi.toLowerCase() === targetRashi.toLowerCase());
  };

  // Full calculation chain per pair
  const evaluatedPairs = useMemo(() => {
    return ARGALA_CONFIGS.map((cfg) => {
      const argalaRashi = getRashiForHouse(cfg.argalaHouse);
      const virodhaRashi = getRashiForHouse(cfg.virodhaHouse);

      const argalaPlanets = getPlanetsInHouse(cfg.argalaHouse);
      const virodhaPlanets = getPlanetsInHouse(cfg.virodhaHouse);

      const numArgala = argalaPlanets.length;
      const numVirodha = virodhaPlanets.length;

      const isActive = numArgala > 0;
      // Jaimini Rule: Virodha cancels Argala when Virodha count >= Argala count
      const isCancelled = isActive && numVirodha >= numArgala;
      const isUnobstructed = isActive && numVirodha === 0;
      const isPartiallyResisted = isActive && numVirodha > 0 && numVirodha < numArgala;

      // Benefic / Malefic breakdown
      const benefics = argalaPlanets.filter((p) => NATURAL_BENEFICS.has(p.planet.toLowerCase()));
      const malefics = argalaPlanets.filter((p) => NATURAL_MALEFICS.has(p.planet.toLowerCase()) || p.planet.toLowerCase() === "moon");
      const strengthScore = benefics.length - malefics.length;
      const netEffectiveForce = isCancelled ? 0 : strengthScore;

      let obstructionReason = "";
      if (!isActive) {
        obstructionReason = `House ${cfg.argalaHouse} (${argalaRashi}) is unoccupied; argala intervention remains latent.`;
      } else if (isCancelled) {
        obstructionReason = `Cancelled: ${numArgala} intervening planet(s) [${argalaPlanets.map((p) => p.planet).join(", ")}] countered by ${numVirodha} obstructing planet(s) [${virodhaPlanets.map((p) => p.planet).join(", ")}] in House ${cfg.virodhaHouse} (${virodhaRashi}).`;
      } else if (isPartiallyResisted) {
        obstructionReason = `Partially Resisted: ${numArgala} intervening planet(s) dominate over ${numVirodha} obstruction(s) in House ${cfg.virodhaHouse}; net force remains active (${strengthScore > 0 ? `+${strengthScore}` : strengthScore}).`;
      } else {
        obstructionReason = `Unobstructed Free Flow: ${numArgala} planet(s) [${argalaPlanets.map((p) => p.planet).join(", ")}] with 0 counter-obstructions in House ${cfg.virodhaHouse}. Net force: ${strengthScore > 0 ? `+${strengthScore}` : strengthScore}.`;
      }

      return {
        ...cfg,
        argalaRashi,
        virodhaRashi,
        argalaPlanets,
        virodhaPlanets,
        numArgala,
        numVirodha,
        isActive,
        isCancelled,
        isUnobstructed,
        isPartiallyResisted,
        benefics,
        malefics,
        strengthScore,
        netEffectiveForce,
        obstructionReason,
      };
    });
  }, [anchorRashiIndex, planetPositions]);

  const netChartArgalaScore = evaluatedPairs.reduce((acc, p) => acc + p.netEffectiveForce, 0);

  return (
    <div className="rounded-2xl border p-5 glass-card" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
      {/* Header & Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-amber-500/20 text-xs font-bold text-amber-400">
              ⚡
            </span>
            <h2 className="text-base font-bold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
              Jaimini Argala &amp; Virodhargala Calculation Chain
            </h2>
          </div>
          <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
            Intervention rays (2nd, 4th, 11th, 5th), planetary obstruction vectors, and unblocked force balance
          </p>
        </div>

        {/* Reference Selector Tabs */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Group mode */}
          <div className="flex rounded-lg border p-0.5" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}>
            <button
              type="button"
              onClick={() => {
                setSelectedReferenceType("standard");
                setSelectedReference("Lagna");
              }}
              className={`rounded-md px-2 py-1 text-xs font-medium transition-all ${
                selectedReferenceType === "standard" ? "bg-[var(--accent)] text-[var(--accent-text)] shadow-sm" : "text-[var(--text-secondary)]"
              }`}
            >
              Primary
            </button>
            <button
              type="button"
              onClick={() => {
                setSelectedReferenceType("bhava");
                setSelectedReference("House 1");
              }}
              className={`rounded-md px-2 py-1 text-xs font-medium transition-all ${
                selectedReferenceType === "bhava" ? "bg-[var(--accent)] text-[var(--accent-text)] shadow-sm" : "text-[var(--text-secondary)]"
              }`}
            >
              12 Bhavas
            </button>
            <button
              type="button"
              onClick={() => {
                setSelectedReferenceType("graha");
                setSelectedReference("Sun");
              }}
              className={`rounded-md px-2 py-1 text-xs font-medium transition-all ${
                selectedReferenceType === "graha" ? "bg-[var(--accent)] text-[var(--accent-text)] shadow-sm" : "text-[var(--text-secondary)]"
              }`}
            >
              Grahas
            </button>
          </div>

          {/* Sub-selectors */}
          {selectedReferenceType === "standard" && (
            <div className="flex rounded-lg border p-0.5" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}>
              {["Lagna", "Atmakaraka", "Moon"].map((ref) => (
                <button
                  key={ref}
                  type="button"
                  onClick={() => setSelectedReference(ref)}
                  className={`rounded-md px-2.5 py-1 text-xs font-medium transition-all ${
                    selectedReference === ref ? "bg-amber-500/20 text-amber-300 font-bold" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                  }`}
                >
                  {ref}
                </button>
              ))}
            </div>
          )}

          {selectedReferenceType === "bhava" && (
            <select
              value={selectedReference}
              onChange={(e) => setSelectedReference(e.target.value)}
              className="rounded-lg border px-2.5 py-1 text-xs outline-none"
              style={{
                borderColor: "var(--border-primary)",
                backgroundColor: "var(--bg-input)",
                color: "var(--text-primary)",
              }}
            >
              {Array.from({ length: 12 }, (_, i) => i + 1).map((h) => (
                <option key={h} value={`House ${h}`}>
                  House {h} ({getRashiForHouse(h)})
                </option>
              ))}
            </select>
          )}

          {selectedReferenceType === "graha" && (
            <select
              value={selectedReference}
              onChange={(e) => setSelectedReference(e.target.value)}
              className="rounded-lg border px-2.5 py-1 text-xs outline-none"
              style={{
                borderColor: "var(--border-primary)",
                backgroundColor: "var(--bg-input)",
                color: "var(--text-primary)",
              }}
            >
              {["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"].map((g) => (
                <option key={g} value={g}>
                  {g}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* Active Anchor Banner */}
      <div className="mb-5 rounded-xl border p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}>
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg flex items-center justify-center font-bold text-xs bg-amber-500/20 text-amber-400 border border-amber-500/40">
            REF
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold" style={{ color: "var(--text-primary)" }}>
                Active Anchor: <span className="text-amber-400 font-mono">{resolvedAnchorRashi}</span> ({RASHI_SANSKRIT[resolvedAnchorRashi.toLowerCase()] ?? resolvedAnchorRashi})
              </span>
              <span className="text-[11px] px-2 py-0.2 rounded bg-amber-500/10 text-amber-300 font-medium">
                {selectedReference}
              </span>
            </div>
            <p className="text-[11px] mt-0.5" style={{ color: "var(--text-muted)" }}>
              Resident Planets: {getPlanetsInHouse(1).map((p) => p.planet).join(", ") || "None (Unoccupied Sign)"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 self-end sm:self-center">
          <div className="text-right">
            <span className="text-[10px] uppercase font-semibold text-[var(--text-muted)] block">Net Argala Force</span>
            <span
              className={`font-mono text-sm font-bold ${
                netChartArgalaScore > 0 ? "text-emerald-400" : netChartArgalaScore < 0 ? "text-rose-400" : "text-slate-300"
              }`}
            >
              {netChartArgalaScore > 0 ? `+${netChartArgalaScore}` : netChartArgalaScore} Unblocked
            </span>
          </div>
        </div>
      </div>

      {/* Vector Flow Grid: 4 Pairs */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {evaluatedPairs.map((pair, idx) => (
          <div
            key={idx}
            className="rounded-xl border p-4 transition-all"
            style={{
              borderColor: hoveredNode === pair.argalaHouse ? "var(--accent)" : "var(--border-primary)",
              backgroundColor: "var(--bg-card)",
            }}
            onMouseEnter={() => setHoveredNode(pair.argalaHouse)}
            onMouseLeave={() => setHoveredNode(null)}
          >
            {/* Pair Header */}
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span
                  className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase tracking-wider ${
                    pair.type === "Primary" ? "bg-amber-500/20 text-amber-300 border border-amber-500/30" : "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                  }`}
                >
                  {pair.type}
                </span>
                <span className="text-xs font-bold" style={{ color: "var(--text-primary)" }}>
                  {pair.label}
                </span>
              </div>

              {/* Status Badge */}
              <span
                className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${
                  pair.isUnobstructed
                    ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                    : pair.isPartiallyResisted
                    ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                    : pair.isCancelled
                    ? "bg-rose-500/20 text-rose-400 border border-rose-500/40"
                    : "bg-slate-500/10 text-slate-400 border border-slate-500/20"
                }`}
              >
                {pair.isUnobstructed
                  ? "✓ Unobstructed"
                  : pair.isPartiallyResisted
                  ? "⚠ Partial Resistance"
                  : pair.isCancelled
                  ? "✗ Cancelled"
                  : "○ Latent (Empty)"}
              </span>
            </div>

            <p className="text-[11px] mb-3 text-[var(--text-muted)] italic">
              {pair.signification}
            </p>

            {/* Vector Interaction Chain Box */}
            <div className="rounded-lg border p-3 space-y-2 text-xs" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}>
              {/* Argala Ray */}
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[11px] font-semibold text-amber-400">
                    Intervention Ray (H{pair.argalaHouse} → {pair.argalaRashi}):
                  </span>
                  <div className="mt-0.5 text-xs text-[var(--text-primary)]">
                    {pair.argalaPlanets.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5 mt-1">
                        {pair.argalaPlanets.map((p) => {
                          const isBen = NATURAL_BENEFICS.has(p.planet.toLowerCase());
                          return (
                            <span
                              key={p.planet}
                              className={`px-1.5 py-0.5 rounded text-[10px] font-medium border ${
                                isBen ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40" : "bg-rose-500/20 text-rose-300 border-rose-500/40"
                              }`}
                            >
                              {p.planet} ({isBen ? "+Benefic" : "-Malefic"})
                            </span>
                          );
                        })}
                      </div>
                    ) : (
                      <span className="text-[var(--text-muted)] italic">No occupying grahas</span>
                    )}
                  </div>
                </div>
                <span className="font-mono text-xs text-amber-300 font-bold">
                  {pair.numArgala} {pair.numArgala === 1 ? "Graha" : "Grahas"}
                </span>
              </div>

              {/* Virodhargala Shield / Counter Ray */}
              <div className="flex items-start justify-between pt-2 border-t" style={{ borderColor: "var(--border-primary)" }}>
                <div>
                  <span className="text-[11px] font-semibold text-rose-400">
                    Obstruction Ray (H{pair.virodhaHouse} → {pair.virodhaRashi}):
                  </span>
                  <div className="mt-0.5 text-xs text-[var(--text-primary)]">
                    {pair.virodhaPlanets.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5 mt-1">
                        {pair.virodhaPlanets.map((p) => (
                          <span
                            key={p.planet}
                            className="px-1.5 py-0.5 rounded text-[10px] font-medium border bg-slate-500/20 text-slate-300 border-slate-500/40"
                          >
                            {p.planet}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-[var(--text-muted)] italic">0 Obstructions (Clear Pathway)</span>
                    )}
                  </div>
                </div>
                <span className="font-mono text-xs text-rose-400 font-bold">
                  {pair.numVirodha} {pair.numVirodha === 1 ? "Graha" : "Grahas"}
                </span>
              </div>

              {/* Calculation Verdict */}
              <div className="pt-2 border-t flex items-center justify-between text-[11px]" style={{ borderColor: "var(--border-primary)" }}>
                <span className="text-[var(--text-secondary)] font-medium">
                  {pair.obstructionReason}
                </span>
                <span className="font-mono font-bold text-xs text-cyan-300 ml-2 whitespace-nowrap">
                  Force: {pair.netEffectiveForce > 0 ? `+${pair.netEffectiveForce}` : pair.netEffectiveForce}
                </span>
              </div>
            </div>

            {/* Classical Sutra Citation */}
            <div className="mt-2 flex justify-between items-center text-[10px] text-[var(--text-muted)]">
              <span>Classical Source:</span>
              <span className="font-mono text-amber-400/80">{pair.sutraRef}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Step-by-Step Calculation Trace Table */}
      <div className="rounded-xl border p-4" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
        <div className="flex items-center justify-between mb-3 cursor-pointer" onClick={() => setShowCalculationTrace(!showCalculationTrace)}>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-[var(--accent)]">
              Calculation Chain Audit Trace
            </span>
            <span className="text-[10px] text-[var(--text-muted)]">
              (Parashara &amp; Jaimini Upadesha Sutras 1.1.4–1.1.9)
            </span>
          </div>
          <button type="button" className="text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
            {showCalculationTrace ? "Hide Trace ▲" : "Show Trace ▼"}
          </button>
        </div>

        {showCalculationTrace && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b text-[var(--text-muted)]" style={{ borderColor: "var(--border-primary)" }}>
                  <th className="pb-2">Pair</th>
                  <th className="pb-2">Argala House ($H_a$)</th>
                  <th className="pb-2">Occupants</th>
                  <th className="pb-2">Virodha House ($H_v$)</th>
                  <th className="pb-2">Obstructions</th>
                  <th className="pb-2">Evaluation ($N_v \ge N_a$)</th>
                  <th className="pb-2 text-right">Net Force</th>
                </tr>
              </thead>
              <tbody className="divide-y" style={{ borderColor: "var(--border-primary)" }}>
                {evaluatedPairs.map((p, idx) => (
                  <tr key={idx} className="hover:bg-slate-500/5">
                    <td className="py-2.5 font-semibold text-[var(--text-primary)]">{p.label.split(" ")[0]} ({p.type})</td>
                    <td className="py-2.5">House {p.argalaHouse} ({p.argalaRashi})</td>
                    <td className="py-2.5 font-mono text-amber-300">
                      {p.argalaPlanets.map((x) => x.planet).join(", ") || "—"}
                    </td>
                    <td className="py-2.5">House {p.virodhaHouse} ({p.virodhaRashi})</td>
                    <td className="py-2.5 font-mono text-rose-300">
                      {p.virodhaPlanets.map((x) => x.planet).join(", ") || "—"}
                    </td>
                    <td className="py-2.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                          p.isCancelled ? "bg-rose-500/20 text-rose-400" : p.isUnobstructed ? "bg-emerald-500/20 text-emerald-400" : "text-[var(--text-muted)]"
                        }`}
                      >
                        {p.isCancelled ? "True (Cancelled)" : p.isUnobstructed ? "False (Clear)" : "Latent"}
                      </span>
                    </td>
                    <td className="py-2.5 text-right font-mono font-bold" style={{ color: p.netEffectiveForce > 0 ? "#4ade80" : p.netEffectiveForce < 0 ? "#f87171" : "var(--text-muted)" }}>
                      {p.netEffectiveForce > 0 ? `+${p.netEffectiveForce}` : p.netEffectiveForce}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
