"use client";

import { useState } from "react";
import {
  BHAVA_PARAMS,
  GRAHA_PARAMS,
  NAKSHATRA_PARAMS,
  RASHI_PARAMS,
  REF_UNAVAILABLE,
} from "@/lib/astroStructural";
import type { WorkflowAnalysisResponse } from "@/lib/types";
import { resolveStructuralColumns, type PlanetContext, type StructuralColumn } from "./context";
import type { PlanetExplorerTab } from "../PlanetExplorerPanel";

const SUTRA_NAMES = [
  "Mobility (Chara/Sthira) / Movement style / Purushartha goal / Navamsha Sign link",
  "Internal Guna / Psychological Guna / Geometric shape / Tri-Guna matrix",
  "Tatva (Element) / Elemental Rule / Functional Nature / Purushartha Purpose",
  "Gender/Temperament / Gender (Linga) / Upachaya Growth / Vimshottari Lord",
  "Lordship (Adhipati) / Planetary Cabinet / Maraka Status / Ruling Deity",
  "Compass Direction / Directional Strength / Bhava Karaka / Physical Symbol",
  "Varna (Inclination) / Varna Class / Bhavat Bhavam / Direction of Motion",
  "Diurnal Strength / Dhatu Material / Argala Influence / Nadi Constitution",
  "Rising Method / Abode/Residence / Yoga Formation / Gana Temperament",
  "Physical Form/Feet / Taste (Rasa) / Aspect Rules / Yoni Animal Symbol",
  "Natural Abode / Time Cycle Rule / Compass Direction / Gender Alignment",
  "Material Type / Vision (Drishti) / Cosmic Mapping / Soul Caste (Varna)",
  "Body Part Alignment / Anatomical System / Chara/Sthira Base / Sacred Tree (Vriksha)",
];

const ELEMENT_ICONS: Record<string, string> = {
  air: "💨",
  fire: "🔥",
  earth: "🌍",
  water: "💧",
  ether: "✨",
  smoke: "🌫️",
  kama: "🎯",
  dharma: "☸️",
  artha: "🏛️",
  moksha: "🕊️",
};

function getElementIcon(val: string): string {
  const v = val.toLowerCase();
  for (const [k, icon] of Object.entries(ELEMENT_ICONS)) {
    if (v.includes(k)) return icon;
  }
  return "⚡";
}

function getRashiDescription(rashi: string | undefined, sutra: number, val: string): string {
  if (val === REF_UNAVAILABLE) return "Reference unavailable for this specific parameter.";
  if (sutra === 2) {
    if (val.toLowerCase().includes("air")) return "Light, mobile, adaptive, intellectual, communicative. Dual nature expresses through exchange.";
    if (val.toLowerCase().includes("fire")) return "Dynamic, energetic, pioneering, visionary. Active expression through initiate power.";
    if (val.toLowerCase().includes("earth")) return "Grounded, stabilizing, pragmatic, resourceful. Material crystallization through patience.";
    if (val.toLowerCase().includes("water")) return "Intuitive, receptive, deep, protective. Emotional integration through cyclical flows.";
  }
  return `${val}. Governs the raw qualitative matrix and field mode of ${rashi ?? "the sign"}.`;
}

function getGrahaDescription(planet: string, sutra: number, val: string): string {
  if (val === REF_UNAVAILABLE) return "Reference unavailable for this specific parameter.";
  if (sutra === 2) {
    if (planet === "Mars") return "Energy, drive, action, courage, initiative, protection. Transforms through activity.";
    if (planet === "Sun") return "Willpower, vitality, sovereignty, illuminating clarity. Radiates core central consciousness.";
    if (planet === "Moon") return "Receptivity, mind, emotional nourishment, perception. Refracts light into felt awareness.";
    if (planet === "Jupiter") return "Expansion, higher wisdom, dharma, benevolence. Synthesizes knowledge into truth.";
    if (planet === "Venus") return "Harmony, aesthetic appreciation, diplomacy, devotion. Connects and refines relational energy.";
    if (planet === "Saturn") return "Discipline, endurance, structural order, realism. Solidifies experience through time.";
    if (planet === "Mercury") return "Analysis, agility, discernment, verbal skill. Translates concepts into operational reality.";
    if (planet === "Rahu") return "Unconventional pursuit, amplification, worldly appetite. Catalyzes unprecedented experimentation.";
    if (planet === "Ketu") return "Internalization, detachment, spiritual discernment. Dissolves material fixations into essence.";
  }
  return `${val}. The energetic planetary driver expressing ${planet}'s specific nature.`;
}

function getBhavaDescription(house: number | undefined, sutra: number, val: string): string {
  if (val === REF_UNAVAILABLE) return "Reference unavailable for this specific parameter.";
  if (sutra === 2) {
    if (house === 1) return "Self-identity, vitality, physical emergence, orientation of destiny.";
    if (house === 2) return "Accumulated wealth, family values, speech, lineage support.";
    if (house === 3) return "Courage, sibling bonds, communicative initiative, self-effort.";
    if (house === 4) return "Inner contentment, mother, emotional foundations, dwellings and vehicles.";
    if (house === 5) return "Creative intelligence, past merit (Purva Punya), speculation, discernment.";
    if (house === 6) return "Overcoming challenges, debt resolution, service, daily health disciplines.";
    if (house === 7) return "Partnerships, public relations, contracts, complementary unions.";
    if (house === 8) return "Transformation, hidden matters, longevity, research, occult, inheritance.";
    if (house === 9) return "Higher truth, fortune, guru guidance, principled life orientation.";
    if (house === 10) return "Executive authority, vocation, status, visible contributions to society.";
    if (house === 11) return "Aspirations, networking, social expansion, realizing major life gains.";
    if (house === 12) return "Spiritual liberation, solitude, transcendental pursuits, detachment.";
  }
  return `${val}. Sets the contextual theater of action for House ${house ?? 1}.`;
}

function getNakshatraDescription(nakshatra: string | undefined, pada: number | undefined, sutra: number, val: string): string {
  if (val === REF_UNAVAILABLE) return "Reference unavailable for this specific parameter.";
  if (sutra === 2) {
    if (nakshatra?.toLowerCase().includes("ardra")) return "To break, purify and renew through storms of experience; seek truth beyond illusions.";
    if (nakshatra?.toLowerCase().includes("ashwini")) return "To initiate rapid healing, pioneer swift breakthroughs and conquer obstacles.";
    if (nakshatra?.toLowerCase().includes("bharani")) return "To endure transformative trials and midwife creative rebirth.";
    if (nakshatra?.toLowerCase().includes("krittika")) return "To cut through falsehood with fiery discernment and protect the sacred.";
    if (nakshatra?.toLowerCase().includes("rohini")) return "To nurture beauty, attract abundance and manifest material creative growth.";
    if (nakshatra?.toLowerCase().includes("mrigashira")) return "To search with gentle curiosity and discover hidden avenues of knowledge.";
    if (nakshatra?.toLowerCase().includes("magha")) return "To anchor ancestral lineage, embody sovereign dignity and noble responsibility.";
  }
  return `${val}. Refines the underlying soul intention of ${nakshatra ?? "Nakshatra"} Pada ${pada ?? 1}.`;
}

interface Props {
  ctx: PlanetContext;
  result: WorkflowAnalysisResponse;
  onNavigateTab?: (tab: PlanetExplorerTab) => void;
}

export function StructureTab({ ctx, result, onNavigateTab }: Props) {
  const [view, setView] = useState<"map" | "matrix">("map");
  const [selectedSutra, setSelectedSutra] = useState<number>(2); // Default Sutra 3 (0-indexed 2)
  const [isExpandedFull, setIsExpandedFull] = useState(false);

  const columns = resolveStructuralColumns(ctx);

  if (columns.length === 0) {
    return (
      <div className="rounded-2xl border p-8 text-center" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>
          No position data for {ctx.planet} in this chart.
        </p>
      </div>
    );
  }

  const rashiCol = columns.find((c) => c.key === "rashi")!;
  const grahaCol = columns.find((c) => c.key === "graha")!;
  const bhavaCol = columns.find((c) => c.key === "bhava")!;
  const nakshatraCol = columns.find((c) => c.key === "nakshatra")!;

  const pos = ctx.position;
  const houseNum = pos?.house_number ?? 1;
  const rashiName = pos?.rashi ?? "Rashi";
  const nakshatraName = pos?.nakshatra ?? "Nakshatra";
  const padaNum = pos?.pada ?? 1;

  const rVal = rashiCol.values[selectedSutra] ?? REF_UNAVAILABLE;
  const gVal = grahaCol.values[selectedSutra] ?? REF_UNAVAILABLE;
  const bVal = bhavaCol.values[selectedSutra] ?? REF_UNAVAILABLE;
  const nVal = nakshatraCol.values[selectedSutra] ?? REF_UNAVAILABLE;

  const rashiDesc = getRashiDescription(rashiName, selectedSutra, rVal);
  const grahaDesc = getGrahaDescription(ctx.planet, selectedSutra, gVal);
  const bhavaDesc = getBhavaDescription(houseNum, selectedSutra, bVal);
  const nakshatraDesc = getNakshatraDescription(nakshatraName, padaNum, selectedSutra, nVal);

  return (
    <div className={`space-y-4 ${isExpandedFull ? "fixed inset-4 z-50 overflow-y-auto p-6 rounded-2xl shadow-2xl bg-slate-950 border border-slate-700" : ""}`}>
      {/* ── Table Top Action Bar ── */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
            <span>13-Parameter Structural Map</span>
            <span
              className="inline-flex items-center justify-center w-4 h-4 rounded-full text-[10px] text-slate-400 border border-slate-700 cursor-help"
              title="13 canonical Parashari coordinates cross-referenced across Rashi, Graha, Bhava, and Nakshatra."
            >
              i
            </span>
          </h3>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setView((v) => (v === "map" ? "matrix" : "map"))}
            className="rounded-lg px-3 py-1.5 text-xs font-semibold border transition"
            style={{
              borderColor: view === "matrix" ? "#10b981" : "var(--border-primary)",
              backgroundColor: view === "matrix" ? "rgba(16,185,129,0.15)" : "transparent",
              color: view === "matrix" ? "#34d399" : "var(--text-secondary)",
            }}
          >
            {view === "matrix" ? "Map View" : "Matrix View"}
          </button>

          <button
            type="button"
            onClick={() => setIsExpandedFull((v) => !v)}
            className="rounded-lg p-1.5 text-slate-400 hover:text-slate-200 border border-slate-800 hover:border-slate-700 transition"
            title={isExpandedFull ? "Exit fullscreen" : "Expand fullscreen"}
            aria-label={isExpandedFull ? "Exit fullscreen" : "Expand fullscreen"}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              {isExpandedFull ? (
                <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3" />
              ) : (
                <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* ── 13-Row Structural Map Table ── */}
      {view === "map" ? (
        <div className="overflow-x-auto rounded-2xl border" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <table className="w-full border-collapse text-left text-xs">
            <thead>
              <tr
                className="border-b text-[11px] font-semibold uppercase tracking-wider"
                style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)", backgroundColor: "rgba(15, 23, 42, 0.4)" }}
              >
                <th className="px-3.5 py-2.5 w-24">Sutra #</th>
                <th className="px-3.5 py-2.5">Rashi ({rashiName})</th>
                <th className="px-3.5 py-2.5">Graha ({ctx.planet})</th>
                <th className="px-3.5 py-2.5">Bhava ({houseNum}th)</th>
                <th className="px-3.5 py-2.5">Nakshatra ({nakshatraName} P{padaNum})</th>
              </tr>
            </thead>
            <tbody>
              {RASHI_PARAMS.map((_, i) => {
                const isSelected = selectedSutra === i;
                const rValRow = rashiCol.values[i] ?? REF_UNAVAILABLE;
                const gValRow = grahaCol.values[i] ?? REF_UNAVAILABLE;
                const bValRow = bhavaCol.values[i] ?? REF_UNAVAILABLE;
                const nValRow = nakshatraCol.values[i] ?? REF_UNAVAILABLE;

                return (
                  <tr
                    key={i}
                    onClick={() => setSelectedSutra(i)}
                    className={`cursor-pointer border-b transition-colors ${
                      isSelected
                        ? "bg-emerald-950/30 font-semibold"
                        : "hover:bg-slate-800/40"
                    }`}
                    style={{
                      borderColor: "var(--border-primary)",
                      borderLeft: isSelected ? "3px solid #10b981" : "3px solid transparent",
                    }}
                  >
                    <td className="px-3.5 py-2 font-mono font-medium text-slate-400">
                      {isSelected ? (
                        <span className="text-emerald-400 font-bold">Sutra {i + 1}</span>
                      ) : (
                        <span>{i + 1}</span>
                      )}
                    </td>
                    <td className="px-3.5 py-2" style={{ color: isSelected ? "#34d399" : "var(--text-primary)" }}>
                      {rValRow === REF_UNAVAILABLE ? <span className="text-slate-500 italic">—</span> : rValRow}
                    </td>
                    <td className="px-3.5 py-2" style={{ color: isSelected ? "#34d399" : "var(--text-primary)" }}>
                      {gValRow === REF_UNAVAILABLE ? <span className="text-slate-500 italic">—</span> : gValRow}
                    </td>
                    <td className="px-3.5 py-2" style={{ color: isSelected ? "#34d399" : "var(--text-primary)" }}>
                      {bValRow === REF_UNAVAILABLE ? <span className="text-slate-500 italic">—</span> : bValRow}
                    </td>
                    <td className="px-3.5 py-2" style={{ color: isSelected ? "#34d399" : "var(--text-primary)" }}>
                      {nValRow === REF_UNAVAILABLE ? <span className="text-slate-500 italic">—</span> : nValRow}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        /* ── Matrix View ── */
        <div className="overflow-x-auto rounded-2xl border" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <table className="w-full border-collapse text-left text-xs">
            <thead>
              <tr className="border-b uppercase tracking-wider text-[10px]" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
                <th className="px-3 py-2">Sutra</th>
                {columns.map((c) => (
                  <th key={c.key} className="px-3 py-2 capitalize">{c.entity}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {columns[0].values.map((_v, i) => (
                <tr
                  key={i}
                  onClick={() => setSelectedSutra(i)}
                  className={`border-b cursor-pointer transition ${selectedSutra === i ? "bg-emerald-950/30" : "hover:bg-slate-800/30"}`}
                  style={{ borderColor: "var(--border-primary)" }}
                >
                  <td className="px-3 py-2 font-mono text-emerald-400 font-bold">S{i + 1}</td>
                  {columns.map((c) => {
                    const val = c.values[i] ?? REF_UNAVAILABLE;
                    return (
                      <td key={c.key} className="px-3 py-2" style={{ color: val === REF_UNAVAILABLE ? "var(--text-muted)" : "var(--text-primary)" }}>
                        {val === REF_UNAVAILABLE ? "—" : val}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Active Sutra Detail Card (4 Pillars + Flow Diagram) ── */}
      <div
        className="rounded-2xl border p-5 shadow-sm space-y-4"
        style={{ borderColor: "rgba(16, 185, 129, 0.3)", backgroundColor: "var(--bg-card)" }}
      >
        {/* Card Header */}
        <div className="flex items-center justify-between border-b pb-3" style={{ borderColor: "var(--border-primary)" }}>
          <div className="flex items-center gap-2">
            <span className="rounded-lg bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 text-xs font-bold font-mono">
              Sutra {selectedSutra + 1}
            </span>
            <h4 className="text-xs font-bold text-slate-200">
              {SUTRA_NAMES[selectedSutra] || `Sutra ${selectedSutra + 1} Analysis`}
            </h4>
          </div>
          <span className="text-slate-400 text-xs">▲</span>
        </div>

        {/* 4 Pillar Grid */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {/* 1. Rashi */}
          <div className="rounded-xl border p-3 flex flex-col justify-between" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}>
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] font-bold" style={{ color: "var(--text-muted)" }}>
                  Rashi ({rashiName})
                </span>
                <span className="text-base">{getElementIcon(rVal)}</span>
              </div>
              <h5 className="text-sm font-bold text-emerald-400 mb-1">{rVal}</h5>
              <p className="text-[11px] leading-relaxed text-slate-300">{rashiDesc}</p>
            </div>
          </div>

          {/* 2. Graha */}
          <div className="rounded-xl border p-3 flex flex-col justify-between" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}>
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] font-bold" style={{ color: "var(--text-muted)" }}>
                  Graha ({ctx.planet})
                </span>
                <span className="text-base">{getElementIcon(gVal)}</span>
              </div>
              <h5 className="text-sm font-bold text-emerald-400 mb-1">{gVal}</h5>
              <p className="text-[11px] leading-relaxed text-slate-300">{grahaDesc}</p>
            </div>
          </div>

          {/* 3. Bhava */}
          <div className="rounded-xl border p-3 flex flex-col justify-between" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}>
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] font-bold" style={{ color: "var(--text-muted)" }}>
                  Bhava ({houseNum}th)
                </span>
                <span className="text-base">{getElementIcon(bVal)}</span>
              </div>
              <h5 className="text-sm font-bold text-emerald-400 mb-1">{bVal}</h5>
              <p className="text-[11px] leading-relaxed text-slate-300">{bhavaDesc}</p>
            </div>
          </div>

          {/* 4. Nakshatra */}
          <div className="rounded-xl border p-3 flex flex-col justify-between" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}>
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] font-bold" style={{ color: "var(--text-muted)" }}>
                  Nakshatra ({nakshatraName} - P{padaNum})
                </span>
                <span className="text-base">{getElementIcon(nVal)}</span>
              </div>
              <h5 className="text-sm font-bold text-emerald-400 mb-1">{nVal}</h5>
              <p className="text-[11px] leading-relaxed text-slate-300">{nakshatraDesc}</p>
            </div>
          </div>
        </div>

        {/* Structural Relationship Flow */}
        <div
          className="rounded-xl border p-3 flex flex-wrap items-center justify-between gap-3"
          style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}
        >
          <div className="flex flex-col gap-1.5 flex-1 min-w-[280px]">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Structural Relationship Flow
            </span>
            <div className="flex flex-wrap items-center gap-2 text-xs font-medium text-slate-200">
              <span className="flex items-center gap-1 text-emerald-400 font-semibold">
                {getElementIcon(rVal)} {rVal} ({rashiName})
              </span>
              <span className="text-slate-500">→</span>
              <span className="flex items-center gap-1 text-amber-400 font-semibold">
                {getElementIcon(gVal)} {gVal} ({ctx.planet})
              </span>
              <span className="text-slate-500">→</span>
              <span className="flex items-center gap-1 text-cyan-400 font-semibold">
                🎯 {bVal} ({houseNum}th)
              </span>
              <span className="text-slate-500">→</span>
              <span className="flex items-center gap-1 text-violet-400 font-semibold">
                🌧️ {nVal} ({nakshatraName})
              </span>
              <span className="text-slate-500">→</span>
              <span className="text-emerald-300 font-bold">
                {nVal !== REF_UNAVAILABLE ? nVal : "Purushartha Expression"}
              </span>
            </div>
          </div>

          <button
            type="button"
            onClick={() => onNavigateTab?.("interpretation")}
            className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 border border-emerald-500/30 transition whitespace-nowrap"
          >
            <span>View Detailed Analysis</span>
            <span>›</span>
          </button>
        </div>
      </div>
    </div>
  );
}