"use client";

import { Card } from "@/components/ui";
import { SBCChakraGrid } from "@/components/charts/SBCChakraGrid";

export default function SBCPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
          Sarvatobhadra Chakra
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Full 9x9 SBC grid with live planet positions and Vedha ray highlighting.
        </p>
      </div>
      <Card>
        <SBCChakraGrid />
      </Card>
    </div>
  );
}
