"use client";

import type { ReactNode } from "react";
import {
  PLANET_SYMBOLS,
  RASHIS,
  rashiIndexFromApiName,
  rashiLordFromApiName,
  NATURAL_RELATIONSHIPS,
  KARAKATVA_BASIC,
  CHART_COLORS,
} from "@/lib/astro";
import { titleCaseToken as titleCase } from "@/lib/api";
import type { D1ChartResponse } from "@/lib/types";

const KENDRA_HOUSES = [1, 4, 7, 10];
const TRIKONA_HOUSES = [1, 5, 9];
const DUSTHANA_HOUSES = [6, 8, 12];
const UPACHAYA_HOUSES = [3, 6, 10, 11];

function houseNature(house: number): string[] {
  const tags: string[] = [];
  if (KENDRA_HOUSES.includes(house)) tags.push("Kendra");
  if (TRIKONA_HOUSES.includes(house)) tags.push("Trikona");
  if (DUSTHANA_HOUSES.includes(house)) tags.push("Dusthana");
  if (UPACHAYA_HOUSES.includes(house)) tags.push("Upachaya");
  return tags;
}

interface Props {
  chart: D1ChartResponse;
  activePlanet: string | null;
  activeHouse: number | null;
}

function Row({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-center justify-between text-xs">
      <span style={{ color: "var(--text-muted)" }}>{label}</span>
      <span className="font-medium" style={{ color: "var(--text-primary)" }}>{value}</span>
    </div>
  );
}

function Badge({ children, color }: { children: ReactNode; color?: string }) {
  return (
    <span
      className="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase"
      style={{ border: `1px solid ${color ?? "var(--border-primary)"}`, color: color ?? "var(--text-secondary)" }}
    >
      {children}
    </span>
  );
}

export function ChartDetailPanel({ chart, activePlanet, activeHouse }: Props) {
  if (!activePlanet && !activeHouse) {
    return (
      <div className="obsidian-card sticky top-4 p-5">
        <h2 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
          Chart Details
        </h2>
        <div className="flex flex-col items-center gap-2 py-8 text-center">
          <span className="text-3xl" style={{ color: "var(--text-muted)" }}>☉</span>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            Hover over a planet or house in the Lagna Chart to see its details here. Click to pin a selection.
          </p>
        </div>
        <div className="mt-4 space-y-1.5 border-t pt-3" style={{ borderColor: "var(--border-primary)" }}>
          <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            Aspect Legend
          </p>
          {Object.entries(CHART_COLORS.aspectColors).map(([type, color]) => (
            <div key={type} className="flex items-center gap-2 text-xs capitalize" style={{ color: "var(--text-secondary)" }}>
              <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
              {type}
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (activePlanet) {
    const planet = chart.planets.find((p) => p.planet.toLowerCase() === activePlanet.toLowerCase());
    if (!planet) return null;
    const name = titleCase(planet.planet);
    const symbol = PLANET_SYMBOLS[name] ?? "";
    const strength = chart.planet_strengths.find((s) => s.planet.toLowerCase() === activePlanet.toLowerCase());
    const relationships = NATURAL_RELATIONSHIPS[name];
    const karakatva = KARAKATVA_BASIC[name] ?? [];
    const relatedAspects = chart.aspects.filter(
      (a) => a.from_planet.toLowerCase() === activePlanet.toLowerCase() || a.to_planet.toLowerCase() === activePlanet.toLowerCase(),
    );

    return (
      <div className="obsidian-card sticky top-4 p-5">
        <div className="mb-3 flex items-center gap-2">
          <span className="text-2xl" style={{ color: "var(--obsidian-accent-tertiary)" }}>{symbol}</span>
          <div>
            <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{name}</h2>
            <p className="text-xs capitalize" style={{ color: "var(--text-secondary)" }}>
              {planet.rashi} {planet.rashi_degree.toFixed(2)}°{planet.is_retrograde ? " · Retrograde" : ""}
            </p>
          </div>
        </div>

        <div className="space-y-2 border-t pt-3" style={{ borderColor: "var(--border-primary)" }}>
          <Row label="House" value={planet.rashi_house_number} />
          <Row label="Nakshatra" value={`${planet.nakshatra} (pada ${planet.pada})`} />
          <Row label="Nakshatra Lord" value={planet.nakshatra_lord} />
          <Row label="Dignity" value={planet.dignity ?? "—"} />
          {planet.is_combust && <Row label="Combust" value={`Yes (orb ${planet.combustion_orb?.toFixed(2) ?? "—"}°)`} />}
          {strength && <Row label="Shadbala Strength" value={strength.strength_score.toFixed(2)} />}
        </div>

        {relatedAspects.length > 0 && (
          <div className="mt-4 border-t pt-3" style={{ borderColor: "var(--border-primary)" }}>
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
              Aspects
            </p>
            <ul className="space-y-1.5">
              {relatedAspects.map((a, i) => {
                const other = a.from_planet.toLowerCase() === activePlanet.toLowerCase() ? a.to_planet : a.from_planet;
                const color = CHART_COLORS.aspectColors[a.aspect_type as keyof typeof CHART_COLORS.aspectColors] ?? "var(--text-secondary)";
                return (
                  <li key={i} className="flex items-center justify-between text-xs">
                    <span className="capitalize" style={{ color: "var(--text-primary)" }}>{titleCase(other)}</span>
                    <Badge color={color}>{a.aspect_type}</Badge>
                  </li>
                );
              })}
            </ul>
          </div>
        )}

        {relationships && (
          <div className="mt-4 border-t pt-3" style={{ borderColor: "var(--border-primary)" }}>
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
              Natural Relationships
            </p>
            <div className="flex flex-wrap gap-1.5">
              {relationships.friends.map((f) => <Badge key={f} color="#22C55E">{f}</Badge>)}
              {relationships.enemies.map((f) => <Badge key={f} color="#EF4444">{f}</Badge>)}
              {relationships.neutrals.map((f) => <Badge key={f}>{f}</Badge>)}
            </div>
          </div>
        )}

        {karakatva.length > 0 && (
          <div className="mt-4 border-t pt-3" style={{ borderColor: "var(--border-primary)" }}>
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
              Karakatva (Significations)
            </p>
            <div className="flex flex-wrap gap-1.5">
              {karakatva.map((k) => <Badge key={k}>{k}</Badge>)}
            </div>
          </div>
        )}
      </div>
    );
  }

  // House detail
  const house = activeHouse as number;
  const ascIdx = rashiIndexFromApiName(chart.ascendant.rashi);
  const houseRashi = RASHIS[(ascIdx + house - 1) % 12];
  const lord = rashiLordFromApiName(houseRashi);
  const planetsHere = chart.planets.filter((p) => p.rashi_house_number === house);
  const nature = houseNature(house);

  return (
    <div className="obsidian-card sticky top-4 p-5">
      <div className="mb-3">
        <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>House {house}</h2>
        <p className="text-xs" style={{ color: "var(--text-secondary)" }}>{houseRashi}</p>
      </div>

      <div className="space-y-2 border-t pt-3" style={{ borderColor: "var(--border-primary)" }}>
        <Row label="Sign Lord" value={lord ?? "—"} />
        <Row label="Planets Placed" value={planetsHere.length} />
      </div>

      {nature.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-1.5 border-t pt-3" style={{ borderColor: "var(--border-primary)" }}>
          {nature.map((n) => <Badge key={n}>{n}</Badge>)}
        </div>
      )}

      {planetsHere.length > 0 && (
        <div className="mt-4 border-t pt-3" style={{ borderColor: "var(--border-primary)" }}>
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            Planets Here
          </p>
          <ul className="space-y-1.5">
            {planetsHere.map((p) => (
              <li key={p.planet} className="flex items-center justify-between text-xs">
                <span className="capitalize" style={{ color: "var(--text-primary)" }}>
                  {PLANET_SYMBOLS[titleCase(p.planet)] ?? ""} {titleCase(p.planet)}
                </span>
                <span style={{ color: "var(--text-secondary)" }}>
                  {p.rashi_degree.toFixed(2)}°{p.is_retrograde ? " (R)" : ""}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
