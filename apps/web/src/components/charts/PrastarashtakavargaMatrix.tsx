"use client";

import { useMemo, useState } from "react";

const PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"];
const KAKSHYA_LORDS = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon", "Lagna"];
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

// Canonical BPHS Chapter 66 Ashtakavarga Contribution Table
const BINDU_TABLE: Record<string, Record<string, number[]>> = {
  sun: {
    sun: [1, 2, 4, 7, 8, 9, 10, 11],
    moon: [3, 6, 10, 11],
    mars: [1, 2, 4, 7, 8, 9, 10, 11],
    mercury: [3, 5, 6, 9, 10, 11, 12],
    jupiter: [5, 6, 9, 11],
    venus: [6, 7, 12],
    saturn: [1, 2, 4, 7, 8, 9, 10, 11],
    lagna: [3, 4, 6, 10, 11, 12],
  },
  moon: {
    sun: [3, 6, 7, 8, 10, 11],
    moon: [1, 3, 6, 7, 9, 10, 11],
    mars: [2, 3, 5, 6, 10, 11],
    mercury: [1, 3, 4, 5, 7, 8, 10, 11],
    jupiter: [1, 2, 4, 7, 8, 10, 11],
    venus: [3, 4, 5, 7, 9, 10, 11],
    saturn: [3, 5, 6, 11],
    lagna: [3, 6, 10, 11],
  },
  mars: {
    sun: [3, 5, 6, 10, 11],
    moon: [3, 6, 11],
    mars: [1, 2, 4, 7, 8, 10, 11],
    mercury: [3, 5, 6, 11],
    jupiter: [6, 10, 11, 12],
    venus: [6, 8, 11, 12],
    saturn: [1, 4, 7, 8, 9, 10, 11],
    lagna: [1, 3, 6, 10, 11],
  },
  mercury: {
    sun: [5, 6, 9, 11, 12],
    moon: [2, 4, 6, 8, 10, 11],
    mars: [1, 2, 4, 7, 8, 9, 10, 11],
    mercury: [1, 3, 5, 6, 9, 10, 11, 12],
    jupiter: [6, 8, 11, 12],
    venus: [1, 2, 3, 4, 5, 8, 9, 11],
    saturn: [1, 2, 4, 7, 8, 9, 10, 11],
    lagna: [1, 2, 4, 6, 8, 10, 11],
  },
  jupiter: {
    sun: [1, 2, 3, 4, 7, 8, 9, 10, 11],
    moon: [2, 5, 7, 9, 11],
    mars: [1, 2, 4, 7, 8, 10, 11],
    mercury: [1, 2, 4, 5, 6, 9, 10, 11],
    jupiter: [1, 2, 3, 4, 7, 8, 10, 11],
    venus: [2, 5, 6, 9, 10, 11],
    saturn: [3, 5, 6, 12],
    lagna: [1, 2, 4, 5, 6, 7, 9, 10, 11],
  },
  venus: {
    sun: [8, 11, 12],
    moon: [1, 2, 3, 4, 5, 8, 9, 11, 12],
    mars: [3, 5, 6, 9, 11, 12],
    mercury: [3, 5, 6, 9, 11],
    jupiter: [5, 8, 9, 10, 11],
    venus: [1, 2, 3, 4, 5, 8, 9, 10, 11],
    saturn: [3, 4, 5, 8, 9, 10, 11],
    lagna: [1, 2, 3, 4, 5, 8, 9, 11],
  },
  saturn: {
    sun: [1, 2, 4, 7, 8, 10, 11],
    moon: [3, 6, 11],
    mars: [3, 5, 6, 10, 11, 12],
    mercury: [6, 8, 9, 10, 11, 12],
    jupiter: [5, 6, 11, 12],
    venus: [6, 11, 12],
    saturn: [3, 5, 6, 11],
    lagna: [1, 3, 4, 6, 10, 11],
  },
};

interface Props {
  natalPositions?: Array<{ planet: string; rashi: string }>;
  lagnaRashi?: string;
  transitingPlanet?: string;
  transitingDegree?: number;
  transitingRashi?: string;
}

export function PrastarashtakavargaMatrix({
  natalPositions = [],
  lagnaRashi = "Aries",
  transitingPlanet = "Jupiter",
  transitingDegree = 14.5,
  transitingRashi = "Taurus",
}: Props) {
  const [selectedPlanet, setSelectedPlanet] = useState<string>("Sun");
  const [selectedRashi, setSelectedRashi] = useState<string>(transitingRashi);
  const [viewMode, setViewMode] = useState<"full_matrix" | "rashi_detail">("full_matrix");

  // Build contributor rashi map from chart props or default fallback
  const contributorRashis = useMemo(() => {
    const map: Record<string, string> = {
      lagna: lagnaRashi.toLowerCase(),
    };
    for (const p of ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]) {
      const match = natalPositions.find((np) => np.planet.toLowerCase() === p);
      map[p] = match ? match.rashi.toLowerCase() : "aries";
    }
    return map;
  }, [natalPositions, lagnaRashi]);

  // Compute 12x8 Prastara matrix dynamically
  const prastaraMatrix = useMemo(() => {
    const targetKey = selectedPlanet.toLowerCase();
    const targetTable = BINDU_TABLE[targetKey] || BINDU_TABLE.sun;

    const matrix: number[][] = [];
    for (let rIdx = 0; rIdx < 12; rIdx++) {
      const row: number[] = [];
      for (const lord of KAKSHYA_LORDS) {
        const lordKey = lord.toLowerCase();
        const lordRashi = contributorRashis[lordKey] || "aries";
        const cIdx = RASHIS.findIndex((r) => r.toLowerCase() === lordRashi.toLowerCase());
        const validCIdx = cIdx >= 0 ? cIdx : 0;
        const offset = ((rIdx - validCIdx + 12) % 12) + 1;
        const offsets = targetTable[lordKey] || [];
        row.push(offsets.includes(offset) ? 1 : 0);
      }
      matrix.push(row);
    }
    return matrix;
  }, [selectedPlanet, contributorRashis]);

  // Active Kakshya: 30 deg divided into 8 segments (3 deg 45 min = 3.75 deg each)
  const activeKakshyaIndex = Math.min(Math.floor(transitingDegree / 3.75), 7);
  const activeKakshyaLord = KAKSHYA_LORDS[activeKakshyaIndex];

  const transitingRashiIdx = RASHIS.findIndex((r) => r.toLowerCase() === transitingRashi.toLowerCase());
  const validTransitRashiIdx = transitingRashiIdx >= 0 ? transitingRashiIdx : 0;
  const transitHasBindu = prastaraMatrix[validTransitRashiIdx]?.[activeKakshyaIndex] === 1;

  const selectedRashiIdx = RASHIS.findIndex((r) => r.toLowerCase() === selectedRashi.toLowerCase());
  const validSelectedRashiIdx = selectedRashiIdx >= 0 ? selectedRashiIdx : 0;
  const currentRashiRow = prastaraMatrix[validSelectedRashiIdx] || [0, 0, 0, 0, 0, 0, 0, 0];
  const rashiBavTotal = currentRashiRow.reduce((a, b) => a + b, 0);

  return (
    <div className="rounded-2xl border p-5 glass-card" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-cyan-500/20 text-xs font-bold text-cyan-400">
              📊
            </span>
            <h2 className="text-base font-bold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
              Prastarashtakavarga Kakshya Matrix (12 × 8)
            </h2>
          </div>
          <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
            Sub-degree 8-fold planetary division (3° 45' per kakshya) computed dynamically from natal chart
          </p>
        </div>

        {/* View Mode & Planet Picker */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Toggle Full Matrix vs Rashi Detail */}
          <div className="flex rounded-lg border p-0.5" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}>
            <button
              type="button"
              onClick={() => setViewMode("full_matrix")}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-all ${
                viewMode === "full_matrix" ? "bg-[var(--accent)] text-[var(--accent-text)] font-bold shadow-sm" : "text-[var(--text-secondary)]"
              }`}
            >
              12 × 8 Grid
            </button>
            <button
              type="button"
              onClick={() => setViewMode("rashi_detail")}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-all ${
                viewMode === "rashi_detail" ? "bg-[var(--accent)] text-[var(--accent-text)] font-bold shadow-sm" : "text-[var(--text-secondary)]"
              }`}
            >
              Sign Detail
            </button>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>Table:</span>
            <select
              value={selectedPlanet}
              onChange={(e) => setSelectedPlanet(e.target.value)}
              className="rounded-lg border px-2.5 py-1 text-xs font-bold outline-none"
              style={{
                borderColor: "var(--border-primary)",
                backgroundColor: "var(--bg-input)",
                color: "var(--accent)",
              }}
            >
              {PLANETS.map((p) => (
                <option key={p} value={p}>
                  {p} Prastara
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Real-time Transit Intersect Badge */}
      <div className="mb-5 rounded-xl border p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3" style={{ borderColor: "var(--accent)", backgroundColor: "rgba(56, 189, 248, 0.06)" }}>
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg flex items-center justify-center font-bold text-xs bg-cyan-500/20 text-cyan-400 border border-cyan-500/40">
            {transitingPlanet.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-[var(--text-primary)]">
                Transit Evaluator: <span className="text-cyan-400 font-mono">{transitingPlanet}</span> @ {transitingDegree.toFixed(2)}° in {transitingRashi}
              </span>
              <span className="text-[11px] px-1.5 py-0.2 rounded bg-cyan-500/20 text-cyan-300 font-mono">
                Kakshya #{activeKakshyaIndex + 1}
              </span>
            </div>
            <p className="text-[11px] mt-0.5" style={{ color: "var(--text-muted)" }}>
              Segment Lord: <span className="font-semibold text-amber-300">{activeKakshyaLord}</span> ({(activeKakshyaIndex * 3.75).toFixed(2)}° – {((activeKakshyaIndex + 1) * 3.75).toFixed(2)}°)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`text-xs px-3 py-1 rounded-full font-bold border ${
              transitHasBindu
                ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
                : "bg-rose-500/20 text-rose-400 border-rose-500/40"
            }`}
          >
            {transitHasBindu ? "✓ Favorable Trigger (Bindu 1)" : "✗ Obstructed / Barren (Bindu 0)"}
          </span>
        </div>
      </div>

      {/* Mode 1: Full 12x8 Inspectable Matrix */}
      {viewMode === "full_matrix" && (
        <div className="overflow-x-auto rounded-xl border" style={{ borderColor: "var(--border-primary)" }}>
          <table className="w-full text-xs text-center border-collapse">
            <thead style={{ backgroundColor: "var(--bg-input)", color: "var(--text-secondary)" }}>
              <tr className="border-b text-[11px]" style={{ borderColor: "var(--border-primary)" }}>
                <th className="p-2.5 text-left font-semibold">Sign / Rashi</th>
                {KAKSHYA_LORDS.map((lord, kIdx) => (
                  <th key={lord} className="p-2.5 font-semibold">
                    <span className="block">{lord}</span>
                    <span className="text-[9px] text-[var(--text-muted)] font-mono font-normal">
                      {(kIdx * 3.75).toFixed(1)}°
                    </span>
                  </th>
                ))}
                <th className="p-2.5 font-bold text-amber-400">BAV Total</th>
              </tr>
            </thead>
            <tbody className="divide-y font-mono" style={{ borderColor: "var(--border-primary)" }}>
              {RASHIS.map((rashi, rIdx) => {
                const row = prastaraMatrix[rIdx] || [];
                const rowSum = row.reduce((a, b) => a + b, 0);
                const isTransitRashi = rashi.toLowerCase() === transitingRashi.toLowerCase();

                return (
                  <tr
                    key={rashi}
                    className={`transition-colors ${
                      isTransitRashi ? "bg-cyan-500/10 font-bold" : "hover:bg-slate-500/5"
                    }`}
                  >
                    <td className="p-2.5 text-left font-sans font-medium text-[var(--text-primary)]">
                      <div className="flex items-center gap-1.5">
                        <span>{rashi}</span>
                        <span className="text-[10px] text-[var(--text-muted)]">
                          ({RASHI_SANSKRIT[rashi.toLowerCase()] ?? rashi})
                        </span>
                        {isTransitRashi && (
                          <span className="text-[9px] px-1 py-0.2 rounded bg-cyan-500/20 text-cyan-300">
                            Transit
                          </span>
                        )}
                      </div>
                    </td>

                    {row.map((val, kIdx) => {
                      const isExactActiveCell = isTransitRashi && kIdx === activeKakshyaIndex;
                      const hasB = val === 1;

                      return (
                        <td
                          key={kIdx}
                          className={`p-2.5 ${
                            isExactActiveCell ? "bg-cyan-400/20 ring-2 ring-cyan-400 ring-inset" : ""
                          }`}
                        >
                          <span
                            className={`inline-flex h-5 w-5 items-center justify-center rounded text-[11px] font-bold ${
                              hasB
                                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                                : "text-[var(--text-muted)] opacity-30"
                            }`}
                          >
                            {val}
                          </span>
                        </td>
                      );
                    })}

                    <td className="p-2.5 font-bold text-amber-400 bg-amber-500/5">
                      {rowSum}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Mode 2: Rashi Detail Breakdown */}
      {viewMode === "rashi_detail" && (
        <div>
          {/* Rashi Selector Bar */}
          <div className="mb-4 flex flex-wrap gap-1.5">
            {RASHIS.map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => setSelectedRashi(r)}
                className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-all ${
                  selectedRashi === r
                    ? "bg-[var(--accent)] text-[var(--accent-text)] font-bold shadow-sm"
                    : "border border-[var(--border-primary)] bg-[var(--bg-input)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                }`}
              >
                {r}
              </button>
            ))}
          </div>

          <div className="mb-3 flex items-center justify-between">
            <span className="text-xs font-bold text-[var(--text-primary)]">
              {selectedRashi} ({RASHI_SANSKRIT[selectedRashi.toLowerCase()] ?? selectedRashi}) — Total BAV Points: <span className="text-amber-400">{rashiBavTotal} / 8</span>
            </span>
          </div>

          <div className="overflow-x-auto rounded-xl border" style={{ borderColor: "var(--border-primary)" }}>
            <table className="w-full text-xs text-left">
              <thead style={{ backgroundColor: "var(--bg-input)", color: "var(--text-secondary)" }}>
                <tr className="border-b" style={{ borderColor: "var(--border-primary)" }}>
                  <th className="p-3 font-semibold">Kakshya #</th>
                  <th className="p-3 font-semibold">Kakshya Lord</th>
                  <th className="p-3 font-semibold">Degree Span</th>
                  <th className="p-3 font-semibold text-center">Bindu Value</th>
                  <th className="p-3 font-semibold text-right">Classical Interpretation</th>
                </tr>
              </thead>
              <tbody className="divide-y" style={{ borderColor: "var(--border-primary)" }}>
                {KAKSHYA_LORDS.map((lord, kIdx) => {
                  const spanStart = (kIdx * 3.75).toFixed(2);
                  const spanEnd = ((kIdx + 1) * 3.75).toFixed(2);
                  const isCurrentActive = selectedRashi.toLowerCase() === transitingRashi.toLowerCase() && kIdx === activeKakshyaIndex;
                  const hasBindu = currentRashiRow[kIdx] === 1;

                  return (
                    <tr
                      key={lord}
                      className={`transition-colors ${
                        isCurrentActive ? "bg-cyan-500/10 font-semibold" : "hover:bg-slate-500/5"
                      }`}
                    >
                      <td className="p-3 text-[var(--text-muted)] font-mono">Kakshya #{kIdx + 1}</td>
                      <td className="p-3 font-medium" style={{ color: isCurrentActive ? "var(--accent)" : "var(--text-primary)" }}>
                        {lord} {isCurrentActive && <span className="text-[10px] ml-1 text-cyan-400 font-bold">(Active Live Transit)</span>}
                      </td>
                      <td className="p-3 text-[var(--text-muted)] font-mono">
                        {spanStart}° – {spanEnd}°
                      </td>
                      <td className="p-3 text-center">
                        <span
                          className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
                            hasBindu
                              ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                              : "bg-rose-500/10 text-rose-400/80 border border-rose-500/20"
                          }`}
                        >
                          {hasBindu ? "1" : "0"}
                        </span>
                      </td>
                      <td className="p-3 text-right">
                        <span className="text-[11px]" style={{ color: hasBindu ? "var(--status-success)" : "var(--text-muted)" }}>
                          {hasBindu ? "Auspicious manifestation & free flow" : "Friction / delayed fruits"}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
