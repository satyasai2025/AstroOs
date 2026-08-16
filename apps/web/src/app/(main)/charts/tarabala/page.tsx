"use client";

import { Card } from "@/components/ui";
import { TarabalaPanel } from "@/components/charts/TarabalaPanel";

export default function TarabalaPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
          Navatara / Tarabala
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Natal, transit, and lordship Tarabala, the yearly Tara cycle, and the Moon+Lagna best-stars
          intersection.
        </p>
      </div>
      <Card>
        <TarabalaPanel />
      </Card>
    </div>
  );
}
