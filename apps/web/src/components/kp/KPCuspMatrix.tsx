"use client";

/**
 * KP Cusp Matrix — all 12 cusps with their Star/Sub/Sub-Sub Lords and
 * what the cusp's Sub Lord (CSL) signifies. Click a cusp to open its
 * detail (KPCuspDetail).
 */

import { useMemo, useState } from "react";
import {
  buildKPCusps,
  HOUSE_SIGNIFICATIONS,
  type KPCusp,
} from "@/lib/kpAnalysis";
import type { D1ChartResponse } from "@/lib/types";
import { formatLongitude } from "@/lib/formatAstro";
import { KPCuspDetail } from "@/components/kp/KPCuspDetail";

interface Props {
  chart: D1ChartResponse;
}

export function KPCuspMatrix({ chart }: Props) {
  const cusps = useMemo(() => buildKPCusps(chart), [chart]);
  const [selected, setSelected] = useState<KPCusp | null>(null);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {cusps.map((cusp) => (
          <button
            key={cusp.house_number}
            type="button"
            onClick={() => setSelected(cusp)}
            className="glass-card p-4 text-left transition hover:opacity-90"
            style={{ border: selected?.house_number === cusp.house_number ? "1px solid var(--accent)" : undefined }}
            aria-label={`Cusp ${cusp.house_number} detail`}
          >
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>
                Cusp {cusp.house_number}
              </span>
              <span className="rounded-full px-2 py-0.5 text-[10px] font-medium" style={{ backgroundColor: "rgba(251,191,36,0.15)", color: "#fbbf24" }}>
                {cusp.rashi}
              </span>
            </div>
            <dl className="space-y-1 text-xs" style={{ color: "var(--text-secondary)" }}>
              <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Longitude</dt><dd>{formatLongitude(cusp.longitude)}</dd></div>
              <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Sign Lord</dt><dd>{cusp.sign_lord ?? "—"}</dd></div>
              <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Star Lord</dt><dd>{cusp.star_lord || "—"}</dd></div>
              <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Sub Lord</dt><dd className="font-semibold" style={{ color: "var(--accent)" }}>{cusp.sub_lord || "—"}</dd></div>
              <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Sub-Sub</dt><dd>{cusp.sub_sub_lord || "—"}</dd></div>
              <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Signifies</dt><dd>{cusp.csl_signifies.length ? cusp.csl_signifies.join(", ") : "—"}</dd></div>
            </dl>
            <p className="mt-2 text-[10px] leading-relaxed" style={{ color: "var(--text-muted)" }}>
              {HOUSE_SIGNIFICATIONS[cusp.house_number]}
            </p>
          </button>
        ))}
      </div>

      {selected && (
        <KPCuspDetail cusp={selected} chart={chart} onClose={() => setSelected(null)} />
      )}
    </div>
  );
}
