"use client";

import type { ReactNode } from "react";
import { KARAKATVA_BASIC, PLANET_SYMBOLS } from "@/lib/astro";
import type { PlanetContext } from "./context";

const KENDRA = [1, 4, 7, 10];
const TRIKONA = [1, 5, 9];
const DUSTHANA = [6, 8, 12];
const UPACHAYA = [3, 6, 10, 11];

function functionalNature(house: number): string[] {
  const tags: string[] = [];
  if (KENDRA.includes(house)) tags.push("Kendra (hub)");
  if (TRIKONA.includes(house)) tags.push("Trikona (dharma)");
  if (DUSTHANA.includes(house)) tags.push("Dusthana (challenge)");
  if (UPACHAYA.includes(house)) tags.push("Upachaya (growth)");
  return tags;
}

function Row({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3 py-1 text-sm">
      <span style={{ color: "var(--text-muted)" }}>{label}</span>
      <span className="text-right font-medium capitalize" style={{ color: "var(--text-primary)" }}>
        {value}
      </span>
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

function Empty({ text }: { text: string }) {
  return <p className="text-sm" style={{ color: "var(--text-muted)" }}>{text}</p>;
}

interface Props {
  ctx: PlanetContext;
}

/**
 * Overview — the orientation layer. Answers the basic question first (what /
 * where / who rules) before the deeper Structure tab decomposes nature across
 * Rashi / Graha / Bhava / Nakshatra.
 */
export function OverviewTab({ ctx }: Props) {
  const { position, strength, dispositor, houseOwnerOf } = ctx;

  if (!position) {
    return <Empty text={`No position data available for ${ctx.planet} in this chart.`} />;
  }

  const rashiLord = "—";
  const nakshatraLord = position.nakshatra_lord || "—";
  const karakatva = KARAKATVA_BASIC[ctx.planet] ?? [];
  const nature = functionalNature(position.house_number);

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
      <div className="rounded-2xl border p-5" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
        <h3 className="mb-2 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
          Planet Identity
        </h3>
        <div className="border-t pt-2" style={{ borderColor: "var(--border-primary)" }}>
          <Row label="Planet" value={`${PLANET_SYMBOLS[ctx.planet] ?? ""} ${ctx.planet}`} />
          <Row label="Rashi" value={position.rashi} />
          <Row label="Degree" value={`${position.rashi_degree.toFixed(2)}°`} />
          <Row label="Nakshatra" value={position.nakshatra} />
          <Row label="Pada" value={position.pada} />
          <Row label="Bhava" value={position.house_number} />
          <Row label="Rashi Lord (dispositor)" value={dispositor ?? rashiLord} />
          <Row label="Nakshatra Lord" value={nakshatraLord} />
          {position.is_retrograde && <Row label="Motion" value="Retrograde" />}
        </div>
      </div>

      <div className="rounded-2xl border p-5" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
        <h3 className="mb-2 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
          Core Status
        </h3>
        <div className="border-t pt-2" style={{ borderColor: "var(--border-primary)" }}>
          <Row label="Functional Nature" value={nature.length ? nature.join(", ") : "Neutral"} />
          <Row label="House Occupation" value={position.house_number} />
          <Row
            label="House Ownership"
            value={houseOwnerOf.length ? houseOwnerOf.sort((a, b) => a - b).map((h) => `House ${h}`).join(", ") : "—"}
          />
          <Row label="Dignity" value={position.dignity ?? "—"} />
          <Row label="Strength" value={strength ? `${strength.score} / 100 (${strength.band})` : "—"} />
        </div>
        {karakatva.length > 0 && (
          <>
            <SectionLabel>Natural Signification (Karakatva)</SectionLabel>
            <div className="flex flex-wrap gap-1.5">
              {karakatva.map((k) => (
                <span
                  key={k}
                  className="rounded-full px-2 py-0.5 text-xs"
                  style={{ backgroundColor: "var(--bg-input)", border: "1px solid var(--border-primary)", color: "var(--text-secondary)" }}
                >
                  {k}
                </span>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}