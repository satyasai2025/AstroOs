"use client";

import type { ReactNode } from "react";
import type { WorkflowAnalysisResponse } from "@/lib/types";
import type { PlanetContext } from "./context";

function Row({ label, value, tone }: { label: string; value: ReactNode; tone?: string }) {
  return (
    <div className="flex items-center justify-between gap-3 py-1 text-sm">
      <span style={{ color: "var(--text-muted)" }}>{label}</span>
      <span className="text-right font-medium" style={{ color: tone ?? "var(--text-primary)" }}>{value}</span>
    </div>
  );
}

function Flags({ ctx }: { ctx: PlanetContext }) {
  const t = ctx.transit;
  if (!t) return null;
  const flags: { label: string; active: boolean; tone: string }[] = [
    { label: "Sade Sati", active: t.is_sade_sati, tone: "#ef4444" },
    { label: "Ashtama Shani", active: t.is_ashtama_shani, tone: "#ef4444" },
    { label: "Favorable house transit", active: t.is_favorable_house === true, tone: "var(--success-400)" },
    { label: "Nakshatra Vedha", active: t.has_nakshatra_vedha, tone: "#fbbf24" },
  ];
  const active = flags.filter((f) => f.active);
  if (active.length === 0) return null;
  return (
    <div className="mt-3 flex flex-wrap gap-1.5 border-t pt-3" style={{ borderColor: "var(--border-primary)" }}>
      {active.map((f) => (
        <span key={f.label} className="rounded-full px-2 py-0.5 text-xs font-medium" style={{ color: f.tone, backgroundColor: "var(--bg-input)", border: `1px solid ${f.tone}` }}>
          {f.label}
        </span>
      ))}
    </div>
  );
}

interface Props {
  ctx: PlanetContext;
  result: WorkflowAnalysisResponse;
}

export function TransitTab({ ctx }: Props) {
  const t = ctx.transit;
  const position = ctx.position;

  if (!t) {
    return (
      <p className="text-sm" style={{ color: "var(--text-muted)" }}>
        No current transit data available for {ctx.planet}.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
      <div className="rounded-2xl border p-5" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
        <h3 className="mb-2 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Transit → Natal</h3>
        <div className="border-t pt-2" style={{ borderColor: "var(--border-primary)" }}>
          <Row label="Current Transit" value={`${t.planet} in ${t.transit_rashi} ${t.transit_rashi_degree?.toFixed(2) ?? ""}°`} />
          <Row label="From Natal Moon" value={t.house_from_natal_moon != null ? `House ${t.house_from_natal_moon}` : "—"} />
          <Row label="Motion" value={t.is_retrograde ? "Retrograde" : "Direct"} />
          {t.gati && <Row label="Gati (speed)" value={t.gati} />}
          <Row label="Transit Nakshatra" value={t.transit_nakshatra ? `${t.transit_nakshatra} · Pada ${t.transit_pada}` : "—"} />
          {t.ashtakavarga_bindus != null && <Row label="Ashtakavarga bindus" value={String(t.ashtakavarga_bindus)} />}
        </div>
        <Flags ctx={ctx} />
      </div>

      <div className="rounded-2xl border p-5" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
        <h3 className="mb-2 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Natal Comparison</h3>
        <div className="border-t pt-2" style={{ borderColor: "var(--border-primary)" }}>
          <Row label="Natal {ctx.planet}" value={position ? `${position.rashi} ${position.rashi_degree.toFixed(2)}°` : "—"} />
          <Row label="Transit {t.planet}" value={`${t.transit_rashi} ${t.transit_rashi_degree?.toFixed(2) ?? ""}°`} />
          <Row
            label="House Interaction"
            value={position && position.house_number != null ? `Transit activates natal House ${position.house_number}` : "—"}
          />
        </div>
        {ctx.dispositor && (
          <p className="mt-3 border-t pt-3 text-xs" style={{ borderColor: "var(--border-primary)", color: "var(--text-secondary)" }}>
            Natal dispositor is {ctx.dispositor}; the transit of {t.planet} cross-references the chart through that lord.
          </p>
        )}
      </div>
    </div>
  );
}