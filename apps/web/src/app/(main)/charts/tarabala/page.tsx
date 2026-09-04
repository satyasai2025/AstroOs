"use client";

import { TarabalaPanel } from "@/components/charts/TarabalaPanel";

export default function TarabalaPage() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
          Navatara / Tarabala
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Natal, transit, and lordship Tarabala, the yearly Tara cycle, and the Moon + Lagna dual-anchor best stars.
        </p>
      </div>
      <TarabalaPanel />
    </div>
  );
}

