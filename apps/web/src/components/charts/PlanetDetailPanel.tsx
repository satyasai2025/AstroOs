"use client";

import { useState, type ReactNode } from "react";
import { NATURAL_RELATIONSHIPS, KARAKATVA_BASIC, PLANET_SYMBOLS } from "@/lib/astro";
import { Tabs } from "@/components/ui";
import type { WorkflowAnalysisResponse } from "@/lib/types";

type DetailTab = "overview" | "relationships" | "strength" | "research";

interface PlanetDetailPanelProps {
  /** Planet name, e.g. "Mars". Null renders an empty-state prompt. */
  planet: string | null;
  result: WorkflowAnalysisResponse;
  /** True when this planet was clicked (pinned) rather than just hovered — see charts/page.tsx. */
  pinned?: boolean;
  /** Clears the pin, e.g. from a close button. */
  onUnpin?: () => void;
  /** Skips this panel's own glass-card wrapper, for embedding inside a shared card. */
  bare?: boolean;
}

function Row({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-center justify-between py-1 text-sm">
      <span style={{ color: "var(--text-muted)" }}>{label}</span>
      <span style={{ color: "var(--text-primary)" }} className="font-medium text-right">
        {value}
      </span>
    </div>
  );
}

function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <h4
      className="mb-1.5 mt-4 text-xs font-semibold uppercase tracking-wide first:mt-0"
      style={{ color: "var(--accent)" }}
    >
      {children}
    </h4>
  );
}

/**
 * Interactive Kundli side panel — updates to show everything AstroOS knows
 * about whichever planet is currently hovered/selected in the chart.
 *
 * Mixes two kinds of data, kept visually distinct:
 *  - Computed for THIS chart (house, sign, aspects, strength, yogas, varga
 *    positions) — comes straight from the workflow analysis response.
 *  - Classical reference data (natural friends/enemies, basic karakatva) —
 *    fixed astrological knowledge, not chart-specific, from lib/astro.ts.
 *
 * Digbala/Cheshtabala breakdown and Avastha aren't shown yet — the backend
 * computes them internally (services/shadbala_engine.py) but doesn't expose
 * them on the API response yet. Rather than fabricate numbers, this panel
 * only shows what's real today.
 */
export function PlanetDetailPanel({ planet, result, pinned, onUnpin, bare }: PlanetDetailPanelProps) {
  const [tab, setTab] = useState<DetailTab>("overview");
  const wrapperClass = bare ? "h-full overflow-y-auto p-4" : "glass-card h-full overflow-y-auto p-5";

  if (!planet) {
    return (
      <div
        className={
          bare
            ? "flex h-full min-h-[300px] items-center justify-center p-6 text-center text-sm"
            : "glass-card flex h-full min-h-[300px] items-center justify-center p-6 text-center text-sm"
        }
        style={{ color: "var(--text-muted)" }}
      >
        Hover a planet for a quick preview, or click it to pin this panel open —
        pinning lets you move the mouse here and scroll to see everything.
      </div>
    );
  }

  const { chart, vargas, yogas, shadbala, transits } = result;

  const position = chart.planets.find((p) => p.planet === planet);
  const strength = chart.planet_strengths.find((p) => p.planet === planet);
  const shadbalaEntry = shadbala.find((s) => s.planet === planet);
  const transitEntry = transits.planets.find((t) => t.planet === planet);
  const relationships = NATURAL_RELATIONSHIPS[planet];
  const karakatva = KARAKATVA_BASIC[planet];

  const aspectsInvolving = chart.aspects.filter(
    (a) => a.from_planet === planet || a.to_planet === planet,
  );

  const conjunctions = position
    ? chart.planets
        .filter((p) => p.planet !== planet && p.house_number === position.house_number)
        .map((p) => p.planet)
    : [];

  const yogasInvolving = yogas.results.filter(
    (y) => y.is_present && y.involved_planets.includes(planet),
  );

  const vargaPositions = (["D9", "D10", "D60"] as const)
    .map((code) => {
      const vc = vargas?.charts[code];
      const vp = vc?.planet_positions.find((p) => p.planet === planet);
      return vp ? { code, rashi: vp.varga_rashi, house: vp.varga_house_number } : null;
    })
    .filter((v): v is { code: "D9" | "D10" | "D60"; rashi: string; house: number } => v !== null);

  if (!position) {
    return (
      <div className={bare ? "p-6 text-sm" : "glass-card p-6 text-sm"} style={{ color: "var(--text-muted)" }}>
        No data available for {planet} in this chart.
      </div>
    );
  }

  return (
    <div className={wrapperClass}>
      <div className="mb-1 flex items-center gap-2">
        <span className="text-xl" style={{ color: "var(--accent)" }}>
          {PLANET_SYMBOLS[planet] ?? ""}
        </span>
        <h3 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
          {planet}
        </h3>
        {pinned && (
          <button
            type="button"
            onClick={onUnpin}
            className="ml-auto rounded-full px-2 py-0.5 text-xs font-medium"
            style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)", color: "var(--accent)" }}
            title="Click to unpin and clear this panel"
          >
            📌 Pinned — click to release
          </button>
        )}
        {position.is_retrograde && (
          <span
            className="rounded-full px-2 py-0.5 text-xs font-medium"
            style={{ backgroundColor: "rgba(239,68,68,0.15)", color: "var(--chart-ascendant)" }}
          >
            Retrograde
          </span>
        )}
        {position.is_combust && (
          <span
            className="rounded-full px-2 py-0.5 text-xs font-medium"
            style={{ backgroundColor: "rgba(251,191,36,0.15)", color: "#fbbf24" }}
          >
            Combust
          </span>
        )}
      </div>

      <div className="mb-3">
        <Tabs
          tabs={[
            { key: "overview", label: "Overview" },
            { key: "relationships", label: "Relationships" },
            { key: "strength", label: "Strength" },
            { key: "research", label: "Research" },
          ]}
          active={tab}
          onChange={(k) => setTab(k as DetailTab)}
        />
      </div>

      {tab === "overview" && (
        <>
          <SectionLabel>Position (this chart)</SectionLabel>
          <Row label="Rashi House (sign-counted)" value={position.rashi_house_number} />
          <Row label="Chalit House (cuspal)" value={position.house_number} />
          <Row label="Sign (Rashi)" value={position.rashi} />
          <Row label="Degree" value={`${position.rashi_degree.toFixed(2)}°`} />
          <Row label="Nakshatra" value={position.nakshatra} />
          <Row label="Pada" value={position.pada} />
          <Row label="Star Lord (KP)" value={position.nakshatra_lord || "—"} />
          <Row label="Sub Lord (KP)" value={position.sub_lord || "—"} />
          <Row label="Sub Sub Lord (KP)" value={position.sub_sub_lord || "—"} />
          <Row label="Dignity" value={position.dignity ?? "—"} />
          {position.is_combust && (
            <Row label="Combustion Orb" value={`${position.combustion_orb?.toFixed(2) ?? "—"}°`} />
          )}
        </>
      )}

      {tab === "relationships" && (
        <>
          {conjunctions.length > 0 && (
            <>
              <SectionLabel>Conjunctions (same house)</SectionLabel>
              <p className="text-sm" style={{ color: "var(--text-primary)" }}>
                {conjunctions.join(", ")}
              </p>
            </>
          )}

          {aspectsInvolving.length > 0 && (
            <>
              <SectionLabel>Aspects</SectionLabel>
              <div className="space-y-1">
                {aspectsInvolving.map((a, i) => (
                  <p key={i} className="text-sm" style={{ color: "var(--text-primary)" }}>
                    {a.from_planet} → {a.to_planet}{" "}
                    <span style={{ color: "var(--text-muted)" }}>
                      ({a.aspect_type}, {a.orb_degrees.toFixed(1)}° orb{a.is_applying ? ", applying" : ""})
                    </span>
                  </p>
                ))}
              </div>
            </>
          )}

          {relationships && (
            <>
              <SectionLabel>Natural Relationships (classical)</SectionLabel>
              <Row label="Friends" value={relationships.friends.join(", ") || "—"} />
              <Row label="Enemies" value={relationships.enemies.join(", ") || "—"} />
              <Row label="Neutral" value={relationships.neutrals.join(", ") || "—"} />
            </>
          )}

          {conjunctions.length === 0 && aspectsInvolving.length === 0 && !relationships && (
            <p className="text-sm" style={{ color: "var(--text-muted)" }}>
              No conjunctions, aspects, or classical relationships to show for {planet}.
            </p>
          )}
        </>
      )}

      {tab === "strength" && (
        <>
          {strength && (
            <>
              <SectionLabel>Strength</SectionLabel>
              <Row label="Strength Score" value={`${strength.strength_score.toFixed(1)} / 10`} />
              {shadbalaEntry && <Row label="Shadbala" value={`${shadbalaEntry.total_rupas.toFixed(2)} rupas`} />}
              <Row
                label="Placement"
                value={
                  [
                    strength.is_exalted && "Exalted",
                    strength.is_debilitated && "Debilitated",
                    strength.is_in_own_sign && "Own Sign",
                    strength.is_in_kendra && "Kendra",
                    strength.is_in_trikona && "Trikona",
                    strength.is_in_dusthana && "Dusthana",
                  ]
                    .filter(Boolean)
                    .join(", ") || "Neutral"
                }
              />
            </>
          )}

          {yogasInvolving.length > 0 && (
            <>
              <SectionLabel>Yogas Involving {planet}</SectionLabel>
              <div className="space-y-1">
                {yogasInvolving.map((y) => (
                  <p key={y.yoga_id} className="text-sm" style={{ color: "var(--text-primary)" }}>
                    {y.name}{" "}
                    <span style={{ color: "var(--text-muted)" }}>({y.category})</span>
                  </p>
                ))}
              </div>
            </>
          )}

          {vargaPositions.length > 0 && (
            <>
              <SectionLabel>Varga Positions</SectionLabel>
              {vargaPositions.map((v) => (
                <Row key={v.code} label={v.code} value={`${v.rashi} · House ${v.house}`} />
              ))}
            </>
          )}

          {transitEntry && (
            <>
              <SectionLabel>Current Transit</SectionLabel>
              <Row label="Transit Sign" value={transitEntry.transit_rashi} />
              <Row label="From Natal Moon" value={`House ${transitEntry.house_from_natal_moon}`} />
              {transitEntry.is_sade_sati && <Row label="Sade Sati" value="Active" />}
              {transitEntry.is_ashtama_shani && <Row label="Ashtama Shani" value="Active" />}
            </>
          )}
        </>
      )}

      {tab === "research" && (
        <>
          {karakatva ? (
            <>
              <SectionLabel>Karakatva (classical, general)</SectionLabel>
              <div className="flex flex-wrap gap-1.5">
                {karakatva.map((k) => (
                  <span
                    key={k}
                    className="rounded-full px-2 py-0.5 text-xs"
                    style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)", color: "var(--text-secondary)" }}
                  >
                    {k}
                  </span>
                ))}
              </div>
              <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
                General classical reference, not specific to this chart. The full searchable
                Karakatva database is a planned separate module.
              </p>
            </>
          ) : (
            <p className="text-sm" style={{ color: "var(--text-muted)" }}>
              No classical Karakatva reference available for {planet}.
            </p>
          )}
        </>
      )}
    </div>
  );
}
