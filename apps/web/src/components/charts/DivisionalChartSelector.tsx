"use client";

import React from "react";
import { VARGA_DIVISORS } from "@/lib/astro";

export const PRIMARY_VARGAS = [
  "D1",
  "D2",
  "D3",
  "D4",
  "D7",
  "D9",
  "D10",
  "D12",
] as const;

export const HIGHER_VARGAS = [
  "D5",
  "D6",
  "D8",
  "D11",
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
  ...HIGHER_VARGAS,
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

  const isHigherVargaSelected = HIGHER_VARGAS.includes(selectedVarga as typeof HIGHER_VARGAS[number]);

  return (
    <div className="flex items-center gap-1.5 max-w-full overflow-x-auto min-w-0 py-0.5">
      {/* Primary Varga Pills */}
      <div className="flex items-center gap-1 overflow-x-auto scrollbar-none min-w-0 focus:outline-none focus:ring-1 focus:ring-cyan-500" tabIndex={0} role="region" aria-label="Primary divisional charts">
        {PRIMARY_VARGAS.map((vk) => {
          const isActive = selectedVarga === vk;
          const available = isAvailable(vk);
          const meta = VARGA_DIVISORS[vk];

          return (
            <button
              key={vk}
              type="button"
              disabled={!available}
              onClick={() => onSelectVarga(vk)}
              title={`${meta?.label || vk} (1/${meta?.divisor || 1})`}
              className={`rounded px-2 py-1 text-xs font-bold transition whitespace-nowrap ${
                isActive
                  ? "bg-cyan-600 dark:bg-cyan-500 text-slate-950 font-extrabold shadow-sm ring-1 ring-cyan-400"
                  : available
                    ? "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700"
                    : "opacity-40 cursor-not-allowed bg-slate-100 dark:bg-slate-800 text-slate-400"
              }`}
            >
              {vk}
            </button>
          );
        })}
      </div>

      {/* More Vargas Dropdown Menu */}
      <div className="relative inline-flex items-center shrink-0">
        <select
          value={isHigherVargaSelected ? selectedVarga : ""}
          onChange={(e) => {
            if (e.target.value) {
              onSelectVarga(e.target.value);
            }
          }}
          aria-label="Select higher or micro-divisional varga chart"
          className={`rounded px-2 py-1 text-xs font-bold border transition cursor-pointer ${
            isHigherVargaSelected
              ? "bg-cyan-600 dark:bg-cyan-500 text-slate-950 border-cyan-400 shadow-sm"
              : "bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 border-slate-300 dark:border-slate-700 hover:border-cyan-500"
          }`}
        >
          <option value="" disabled={!isHigherVargaSelected}>
            {isHigherVargaSelected ? selectedVarga : "More Vargas ▼"}
          </option>
          {HIGHER_VARGAS.map((vk) => {
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
    </div>
  );
}
