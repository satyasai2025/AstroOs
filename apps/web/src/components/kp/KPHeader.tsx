"use client";

import { useState } from "react";
import { KPUserGuideModal } from "@/components/kp/KPUserGuideModal";

/**
 * KP Header — "Precision + Logic + Evidence" masthead with quick principles
 * and interactive "How to Use & Interpret KP" Guide modal trigger.
 */

export function KPHeader() {
  const [showGuide, setShowGuide] = useState(false);

  const principles = [
    {
      title: "1. Cuspal Sub Lord (CSL)",
      detail: "The Sub Lord of a house cusp decides if the event is promised (YES/NO).",
    },
    {
      title: "2. 4-Tier Significators",
      detail: "Grades A > B > C > D measure how strongly planets connect to houses.",
    },
    {
      title: "3. Sub Lord Veto (Negation)",
      detail: "If CSL signifies 12th from the matter (e.g. 6th for marriage), it blocks results.",
    },
    {
      title: "4. Ruling Planets (RP)",
      detail: "Lagna + Moon Star/Sign Lords at query time confirm timing accuracy.",
    },
    {
      title: "5. Timing Windows",
      detail: "Fructification happens when Dasha + Transit + RP jointly trigger positive houses.",
    },
    {
      title: "6. Evidence-Based Chain",
      detail: "0% guesswork. Every conclusion comes with a verifiable rule citation.",
    },
  ];

  return (
    <>
      <div className="mb-6 space-y-4 font-sans">
        {/* Main Banner */}
        <div
          className="border-l-4 p-5 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-md backdrop-blur-sm"
          style={{
            borderLeftColor: "#f59e0b",
            borderColor: "var(--border-primary)",
            backgroundColor: "var(--bg-card)",
          }}
        >
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-amber-100 text-amber-900 border border-amber-600/40 dark:bg-amber-950/60 dark:text-amber-300 uppercase tracking-wider shadow-xs">
                Krishnamurti Paddhati (KP Core)
              </span>
            </div>
            <h2 className="text-xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight mt-1.5 flex items-center gap-2">
              <span>🪐</span> KP Analysis &amp; Cuspal Decision Engine
            </h2>
            <p className="mt-1 text-xs sm:text-sm text-slate-800 dark:text-slate-200 max-w-2xl leading-relaxed font-semibold">
              Precision Sub Lord theory, 4-tier house significators, and deterministic timing windows.
              Every parameter is calculated strictly from Placidus cusps and sidereal coordinates.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setShowGuide(true)}
            className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-extrabold bg-amber-500 hover:bg-amber-400 text-slate-950 transition-all cursor-pointer shadow-md self-start md:self-auto shrink-0"
          >
            <span>📖</span> How to Read &amp; Use KP Guide
          </button>
        </div>

        {/* 6 Core Principles Cards */}
        <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
          {principles.map((p) => (
            <div
              key={p.title}
              className="rounded-xl border p-3.5 shadow-sm transition-all"
              style={{
                backgroundColor: "var(--bg-card)",
                borderColor: "var(--border-primary)",
              }}
            >
              <p className="text-[11px] font-extrabold uppercase tracking-wider text-amber-600 dark:text-amber-400">
                {p.title}
              </p>
              <p className="mt-1 text-xs text-slate-900 dark:text-slate-100 leading-relaxed font-semibold">
                {p.detail}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Interactive User Guide Modal */}
      {showGuide && <KPUserGuideModal onClose={() => setShowGuide(false)} />}
    </>
  );
}
