"use client";

import { SBCChakraGrid } from "@/components/charts/SBCChakraGrid";

export const dynamic = "force-dynamic";

export default function SBCPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1 border-b pb-4" style={{ borderColor: "var(--border-primary)" }}>
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-950/60 border border-cyan-500/30 text-cyan-400 font-bold shadow-inner">
            ⚡
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
              Sarvatobhadra Chakra (SBC)
            </h1>
            <p className="text-xs text-slate-700 dark:text-slate-300 font-medium mt-0.5">
              Full 9x9 concentric SBC matrix with live planetary Vedha ray tracing and 10 Sangyas analysis.
            </p>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border p-4 sm:p-6 shadow-xl backdrop-blur-sm" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
        <SBCChakraGrid />
      </div>
    </div>
  );
}
