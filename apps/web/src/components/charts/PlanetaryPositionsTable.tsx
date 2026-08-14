"use client";

import type { AscendantSchema, PlanetPositionSchema } from "@/lib/types";
import { formatLongitude, nakshatraAbbrev, rashiAbbrev } from "@/lib/formatAstro";

interface PlanetaryPositionsTableProps {
  ascendant: AscendantSchema;
  planets: PlanetPositionSchema[];
  /** Optional link target for the "View All" affordance. */
  href?: string;
  /** Set false to omit the header row + card chrome (inline embedding). */
  standalone?: boolean;
}

/**
 * JHora-style planetary positions table. Rows: Lagna first, then the
 * nine grahas. Columns: Body | Longitude | Nakshatra | Pada | Rasi |
 * Navamsa — longitudes in deg/sign/min/sec form, signs/nakshatras as
 * short abbreviations. Uses the app-wide formatters from
 * lib/formatAstro.ts so every chart view stays consistent.
 */
export function PlanetaryPositionsTable({
  ascendant,
  planets,
  href,
  standalone,
}: PlanetaryPositionsTableProps) {
  const rows = [
    {
      key: "lagna",
      body: "Lagna",
      longitude: formatLongitude(ascendant.sidereal_longitude),
      nakshatra: nakshatraAbbrev(ascendant.nakshatra),
      pada: ascendant.pada,
      rashi: rashiAbbrev(ascendant.rashi),
      navamsa: rashiAbbrev(ascendant.navamsa_rashi),
      retro: false,
    },
    ...planets.map((p) => ({
      key: p.planet,
      body: p.planet.charAt(0).toUpperCase() + p.planet.slice(1),
      longitude: formatLongitude(p.sidereal_longitude),
      nakshatra: nakshatraAbbrev(p.nakshatra),
      pada: p.pada,
      rashi: rashiAbbrev(p.rashi),
      navamsa: rashiAbbrev(p.navamsa_rashi),
      retro: p.is_retrograde,
    })),
  ];

  const table = (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr
            className="border-b text-xs uppercase"
            style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}
          >
            <th className="py-2 pr-3">Body</th>
            <th className="py-2 pr-3">Longitude</th>
            <th className="py-2 pr-3">Nakshatra</th>
            <th className="py-2 pr-3">Pada</th>
            <th className="py-2 pr-3">Rasi</th>
            <th className="py-2 pr-3">Navamsa</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr
              key={r.key}
              className="border-b"
              style={{ borderColor: "var(--border-primary)", color: "var(--text-primary)" }}
            >
              <td className="py-2 pr-3 font-medium capitalize">
                {r.body}
                {r.retro ? <span className="ml-1 text-xs" style={{ color: "var(--text-muted)" }}>(R)</span> : null}
              </td>
              <td className="py-2 pr-3 font-mono whitespace-nowrap">{r.longitude}</td>
              <td className="py-2 pr-3 capitalize">{r.nakshatra}</td>
              <td className="py-2 pr-3">{r.pada}</td>
              <td className="py-2 pr-3">{r.rashi}</td>
              <td className="py-2 pr-3">{r.navamsa}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  if (standalone) return table;

  return (
    <div className="obsidian-card p-5">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
          Planetary Positions
        </h2>
        {href && (
          <a href={href} className="text-[11px] underline" style={{ color: "var(--text-muted)" }}>
            View All
          </a>
        )}
      </div>
      {table}
    </div>
  );
}
