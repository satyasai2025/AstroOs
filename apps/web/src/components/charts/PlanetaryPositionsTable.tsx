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
 * Classical Vedic-style planetary positions table. Rows: Lagna first, then the
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
    ...(ascendant ? [{
      key: "lagna",
      body: "Lagna",
      longitude: formatLongitude(ascendant.sidereal_longitude ?? ascendant.rashi_degree ?? 0),
      nakshatra: nakshatraAbbrev(ascendant.nakshatra ?? ""),
      pada: ascendant.pada ?? 1,
      rashi: rashiAbbrev(ascendant.rashi ?? ""),
      navamsa: rashiAbbrev(ascendant.navamsa_rashi ?? ""),
      retro: false,
    }] : []),
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
    <div className="w-full overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-slate-200 dark:border-slate-800 text-xs uppercase tracking-wide text-slate-700 dark:text-slate-300 font-semibold bg-slate-50/50 dark:bg-slate-800/40">
            <th className="py-2.5 px-3">Body</th>
            <th className="py-2.5 px-3">Longitude</th>
            <th className="py-2.5 px-3">Nakshatra</th>
            <th className="py-2.5 px-3">Pada</th>
            <th className="py-2.5 px-3">Rasi</th>
            <th className="py-2.5 px-3">Navamsa</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
          {rows.map((r) => (
            <tr
              key={r.key}
              className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition"
            >
              <td className="py-2 px-3 font-semibold text-slate-900 dark:text-slate-100 capitalize">
                {r.body}
                {r.retro ? <span className="ml-1 text-xs text-rose-500 font-bold">(R)</span> : null}
              </td>
              <td className="py-2 px-3 font-mono text-slate-700 dark:text-slate-300 whitespace-nowrap">{r.longitude}</td>
              <td className="py-2 px-3 text-slate-700 dark:text-slate-300 capitalize">{r.nakshatra}</td>
              <td className="py-2 px-3 text-slate-800 dark:text-slate-200">{r.pada}</td>
              <td className="py-2 px-3 font-medium text-slate-800 dark:text-slate-200">{r.rashi}</td>
              <td className="py-2 px-3 text-slate-700 dark:text-slate-300">{r.navamsa}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  if (standalone) return table;

  return (
    <div className="bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm overflow-hidden">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
          Planetary Positions
        </h2>
        {href && (
          <a href={href} className="text-[11px] underline text-slate-500 dark:text-slate-400 hover:text-cyan-500">
            View All
          </a>
        )}
      </div>
      {table}
    </div>
  );
}
