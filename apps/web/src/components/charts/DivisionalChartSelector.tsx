"use client";

import React from "react";
import { VARGA_DIVISORS } from "@/lib/astro";

export const PRIMARY_VARGAS = ["D1"] as const;

export const ALL_OTHER_VARGAS = [
  "D2",
  "D3",
  "D4",
  "D5",
  "D6",
  "D7",
  "D8",
  "D9",
  "D10",
  "D11",
  "D12",
  "D16",
  "D20",
  "D24",
  "D27",
  "D30",
  "D40",
  "D45",
  "D60",
  "D81",
  "D108",
  "D144",
] as const;

export const ALL_CLASSICAL_VARGAS = [
  ...PRIMARY_VARGAS,
  ...ALL_OTHER_VARGAS,
] as const;

interface DivisionalChartSelectorProps {
  selectedVarga: string;
  onSelectVarga: (varga: string) => void;
  availableVargas?: string[];
  compact?: boolean;
}

export function DivisionalChartSelector({
  selectedVarga,
  onSelectVarga,
  availableVargas,
  compact = false,
}: DivisionalChartSelectorProps) {
  const isAvailable = (vk: string) =>
    !availableVargas || availableVargas.length === 0 || vk === "D1" || availableVargas.includes(vk);

  return (
    <div className="relative inline-flex items-center shrink-0 font-mono">
      <select
        value={selectedVarga}
        onChange={(e) => onSelectVarga(e.target.value)}
        aria-label="Select divisional varga chart"
        className="rounded-lg px-3 py-1 text-xs font-bold border transition cursor-pointer bg-slate-100 dark:bg-slate-800 text-cyan-600 dark:text-cyan-400 border-slate-300 dark:border-slate-700 hover:border-cyan-500 focus:outline-none shadow-sm"
      >
        <option value="D1">D1 — Rashi Chart</option>
        {ALL_OTHER_VARGAS.map((vk) => {
          const meta = VARGA_DIVISORS[vk];
          const available = isAvailable(vk);
          return (
            <option key={vk} value={vk} disabled={!available}>
              {vk} — {meta?.label || vk}
            </option>
          );
        })}
      </select>
    </div>
  );
}
