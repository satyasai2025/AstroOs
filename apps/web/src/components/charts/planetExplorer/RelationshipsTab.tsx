"use client";

import type { ReactNode } from "react";
import { NATURAL_RELATIONSHIPS, PLANET_SYMBOLS } from "@/lib/astro";
import type { WorkflowAnalysisResponse } from "@/lib/types";
import type { PlanetContext } from "./context";

function Group({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-2xl border p-4" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>{title}</h4>
      {children}
    </div>
  );
}

function List({ items, tone }: { items: string[]; tone?: string }) {
  if (items.length === 0) return <p className="text-sm" style={{ color: "var(--text-muted)" }}>—</p>;
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((it) => (
        <span
          key={it}
          className="rounded-full px-2 py-0.5 text-xs capitalize"
          style={{ backgroundColor: "var(--bg-input)", border: "1px solid var(--border-primary)", color: tone ?? "var(--text-secondary)" }}
        >
          {PLANET_SYMBOLS[it] ? `${PLANET_SYMBOLS[it]} ` : ""}{it}
        </span>
      ))}
    </div>
  );
}

interface Props {
  ctx: PlanetContext;
  result: WorkflowAnalysisResponse;
}

export function RelationshipsTab({ ctx }: Props) {
  const { position, dispositor, conjunctions, aspectsReceived, aspectsGiven, houseOwnerOf } = ctx;
  const natural = NATURAL_RELATIONSHIPS[ctx.planet];

  // Aspect labelling: collapsed list of the other planets at each direction.
  const aspectsGivenList = aspectsGiven.map((a) => `${a.to_planet} (${aspectLabel(a.aspect_type)})`);
  const aspectsReceivedList = aspectsReceived.map((a) => `${a.from_planet} (${aspectLabel(a.aspect_type)})`);

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      <Group title="Dispositor">
        {position ? (
          <div className="flex items-center gap-2">
            {dispositor ? (
              <>
                <span className="text-lg" style={{ color: "var(--accent)" }}>{PLANET_SYMBOLS[dispositor] ?? ""}</span>
                <span className="text-sm capitalize" style={{ color: "var(--text-primary)" }}>{dispositor}</span>
                <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                  — lord of {position.rashi}
                </span>
                {dispositor === ctx.planet && <span className="text-xs" style={{ color: "var(--text-muted)" }}>(self)</span>}
              </>
            ) : (
              <span className="text-sm" style={{ color: "var(--text-muted)" }}>—</span>
            )}
          </div>
        ) : (
          <span className="text-sm" style={{ color: "var(--text-muted)" }}>—</span>
        )}
      </Group>

      <Group title="Conjunctions (same bhava)">
        {position ? (
          <List items={conjunctions} />
        ) : (
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>—</p>
        )}
      </Group>

      <Group title="Aspects Given">
        {aspectsGivenList.length ? (
          <ul className="space-y-1 text-sm capitalize" style={{ color: "var(--text-primary)" }}>
            {aspectsGivenList.map((a, i) => <li key={i}>{a}</li>)}
          </ul>
        ) : (
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>—</p>
        )}
      </Group>

      <Group title="Aspects Received">
        {aspectsReceivedList.length ? (
          <ul className="space-y-1 text-sm capitalize" style={{ color: "var(--text-primary)" }}>
            {aspectsReceivedList.map((a, i) => <li key={i}>{a}</li>)}
          </ul>
        ) : (
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>—</p>
        )}
      </Group>

      <Group title="House Ownership">
        {houseOwnerOf.length ? (
          <div className="flex flex-wrap gap-1.5">
            {houseOwnerOf.sort((a, b) => a - b).map((h) => (
              <span
                key={h}
                className="rounded-full px-2 py-0.5 text-xs"
                style={{ backgroundColor: "var(--bg-input)", border: "1px solid var(--border-primary)", color: "var(--text-secondary)" }}
              >
                House {h}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>—</p>
        )}
      </Group>

      <Group title="Nakshatra Lord">
        {position?.nakshatra_lord ? (
          <div className="flex items-center gap-2">
            <span className="text-lg" style={{ color: "var(--accent)" }}>{PLANET_SYMBOLS[position.nakshatra_lord] ?? ""}</span>
            <span className="text-sm capitalize" style={{ color: "var(--text-primary)" }}>{position.nakshatra_lord}</span>
            <span className="text-xs" style={{ color: "var(--text-muted)" }}>— star lord of {position.nakshatra}</span>
          </div>
        ) : (
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>—</p>
        )}
      </Group>

      {natural && (
        <div className="xl:col-span-2">
          <Group title="Natural Relationships (classical)">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div>
                <p className="mb-1 text-xs font-medium" style={{ color: "var(--success-400)" }}>Friends</p>
                <List items={natural.friends} tone="var(--success-400)" />
              </div>
              <div>
                <p className="mb-1 text-xs font-medium" style={{ color: "#ef4444" }}>Enemies</p>
                <List items={natural.enemies} tone="#ef4444" />
              </div>
              <div>
                <p className="mb-1 text-xs font-medium" style={{ color: "var(--text-secondary)" }}>Neutral</p>
                <List items={natural.neutrals} />
              </div>
            </div>
          </Group>
        </div>
      )}
    </div>
  );
}

function aspectLabel(type: string): string {
  switch (type) {
    case "conjunction": return "conjunction";
    case "opposition": return "opposition";
    case "trine": return "trine";
    case "square": return "square";
    case "sextile": return "sextile";
    default: return type;
  }
}