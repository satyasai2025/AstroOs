"use client";

import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { RelocationStudio } from "@/components/research/RelocationStudio";

export default function RelocationPage() {
  return (
    <AppShell sectionColor="--section-research">
      <div className="max-w-7xl mx-auto space-y-6 pb-12">
        <div className="p-4 rounded-xl bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border border-amber-500/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-500/20 text-amber-300 text-lg">
              ✨
            </div>
            <div>
              <div className="text-sm font-semibold text-white flex items-center gap-2">
                Consumer Relocation Discovery Studio Active
              </div>
              <p className="text-xs text-slate-300">
                Looking for ranked best locations, life motives (Career, Wealth, Marriage), and visual city dossiers?
              </p>
            </div>
          </div>
          <Link
            href="/relocation"
            className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs flex items-center gap-2 transition-colors shrink-0 shadow-lg shadow-amber-500/20"
          >
            <span>🧭</span>
            Open Discovery Studio →
          </Link>
        </div>

        <RelocationStudio />
      </div>
    </AppShell>
  );
}
