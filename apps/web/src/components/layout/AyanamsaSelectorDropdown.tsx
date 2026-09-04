"use client";

import React from "react";
import { useWorkflowStore } from "@/lib/store";

const AYANAMSA_OPTIONS = [
  { id: "Lahiri", label: "Lahiri" },
  { id: "Raman", label: "Raman" },
  { id: "KP", label: "KP" },
  { id: "Fagan_Bradley", label: "Fagan" },
  { id: "Yukteshwar", label: "Yukteshwar" },
];

export function AyanamsaSelectorDropdown() {
  const request = useWorkflowStore((s) => s.request);
  const setRequest = useWorkflowStore((s) => s.setRequest);

  const currentAyanamsa = request?.ayanamsa || "Lahiri";

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newAyanamsa = e.target.value;
    if (request) {
      setRequest({
        ...request,
        ayanamsa: newAyanamsa as any,
      });
    }
  };

  return (
    <div className="flex items-center gap-1 rounded-md border border-slate-700/80 bg-slate-900/80 px-2 py-1 text-xs text-slate-200 shadow-sm whitespace-nowrap">
      <label htmlFor="ayanamsa-selector" className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
        Ayanamsa:
      </label>
      <select
        id="ayanamsa-selector"
        aria-label="Select Ayanamsa System"
        value={currentAyanamsa}
        onChange={handleChange}
        className="bg-transparent font-bold text-cyan-400 focus:outline-none cursor-pointer text-xs"
      >
        {AYANAMSA_OPTIONS.map((opt) => (
          <option key={opt.id} value={opt.id} className="bg-slate-900 text-slate-100">
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}
