"use client";

import type { ReactNode } from "react";
import { StrengthProgressBar } from "@/components/charts/StrengthProgressBar";
import { BAND_COLOR, BAND_LABEL } from "@/lib/planetStrength";
import type { WorkflowAnalysisResponse } from "@/lib/types";
import type { PlanetContext } from "./context";

function Row({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3 py-1 text-sm">
      <span style={{ color: "var(--text-muted)" }}>{label}</span>
      <span className="text-right font-medium" style={{ color: "var(--text-primary)" }}>{value}</span>
    </div>
  );
}

function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <h4 className="mb-1.5 mt-4 text-xs font-semibold uppercase tracking-wide first:mt-0" style={{ color: "var(--accent)" }}>
      {children}
    </h4>
  );
}

function Tag({ text, color }: { text: string; color: string }) {
  return (
    <span
      className="rounded-full px-2 py-0.5 text-xs"
      style={{ backgroundColor: "var(--bg-input)", border: `1px solid ${color}`, color }}
    >
      {text}
    </span>
  );
}

interface Props {
  ctx: PlanetContext;
  result: WorkflowAnalysisResponse;
}

export function StrengthTab({ ctx }: Props) {
  const { strength, shadbala, position, navamsha } = ctx;

  if (!strength) {
    return <p className="text-sm" style={{ color: "var(--text-muted)" }}>No strength data available for {ctx.planet} in this chart.</p>;
  }

  const placementTags: string[] = [];
  if (strength.isExalted) placementTags.push("Exalted");
  if (strength.isDebilitated) placementTags.push("Debilitated");
  if (strength.isOwnSign) placementTags.push("Own Sign");
  if (strength.isInKendra) placementTags.push("Kendra");
  if (strength.isInTrikona) placementTags.push("Trikona");
  if (strength.isInDusthana) placementTags.push("Dusthana");

  const shadbalaRatio =
    strength.rupas != null && strength.requiredRupas ? (strength.rupas / strength.requiredRupas).toFixed(2) : null;

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
      <div className="rounded-2xl border p-5" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
        <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
          Overall Strength
        </h3>
        <div className="mb-1 flex items-end justify-between">
          <span className="text-3xl font-bold" style={{ color: "var(--text-primary)" }}>{strength.score}%</span>
          <span style={{ color: "var(--text-secondary)", fontSize: "var(--text-sm)" }}>{BAND_LABEL[strength.band]}</span>
        </div>
        <StrengthProgressBar score={strength.score} size="lg" showLabel={false} />
        <p className="mt-3 text-xs" style={{ color: "var(--text-muted)" }}>
          A blended score: 65% Shadbala-versus-classical-minimum + 35% dignity/placement composite. Distinct from the
          planet&apos;s structural identity in the Structure tab.
        </p>
      </div>

      <div className="rounded-2xl border p-5" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
        <h3 className="mb-2 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
          Shadbala &amp; Dignity
        </h3>
        <div className="border-t pt-2" style={{ borderColor: "var(--border-primary)" }}>
          <Row label="Shadbala" value={shadbala ? `${shadbala.total_rupas.toFixed(2)} rupas` : "—"} />
          <Row
            label="Classical Minimum"
            value={strength.requiredRupas != null ? `${strength.requiredRupas} rupas` : "—"}
          />
          {shadbalaRatio && <Row label="Ratio" value={`${shadbalaRatio}× minimum`} />}
          <Row label="Dignity" value={strength.dignity ?? "—"} />
          <Row label="Retrograde" value={strength.isRetrograde ? "Yes" : "No"} />
          {position?.is_combust && <Row label="Combust" value={`Yes (orb ${position.combustion_orb?.toFixed(2) ?? "—"}°)`} />}
        </div>
        {placementTags.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {placementTags.map((t) => (
              <Tag key={t} text={t} color={BAND_COLOR[strength.band]} />
            ))}
          </div>
        )}
        {navamsha && (
          <>
            <SectionLabel>Navamsha (D9)</SectionLabel>
            <p className="text-sm capitalize" style={{ color: "var(--text-primary)" }}>
              {navamsha.rashi} · House {navamsha.house}
            </p>
          </>
        )}
      </div>
    </div>
  );
}