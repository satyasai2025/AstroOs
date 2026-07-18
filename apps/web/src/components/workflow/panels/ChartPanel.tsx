import type { D1ChartResponse } from "@/lib/types";

export function ChartPanel({ chart }: { chart: D1ChartResponse }) {
  return (
    <div className="space-y-6">
      <div className="glass-card p-5">
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-amber-300/80">
          Ascendant
        </h3>
        <p className="text-2xl font-bold text-white">
          {chart.ascendant.rashi}{" "}
          <span className="text-base font-normal text-slate-400">
            {chart.ascendant.rashi_degree.toFixed(2)}°
          </span>
        </p>
        <p className="mt-1 text-sm text-slate-400">
          Nakshatra: {chart.ascendant.nakshatra} (pada {chart.ascendant.pada})
        </p>
        <p className="mt-3 text-xs text-slate-500">
          Ayanamsa: {chart.ayanamsa_system} ({chart.ayanamsa_value.toFixed(4)}°) · House
          system: {chart.house_system} · Julian Day: {chart.julian_day.toFixed(4)}
        </p>
      </div>

      <div className="glass-card overflow-x-auto p-5">
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-amber-300/80">
          Planetary Positions
        </h3>
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-white/10 text-xs uppercase tracking-wide text-slate-500">
              <th className="py-2 pr-4">Planet</th>
              <th className="py-2 pr-4">Rashi</th>
              <th className="py-2 pr-4">Degree</th>
              <th className="py-2 pr-4">House</th>
              <th className="py-2 pr-4">Nakshatra</th>
              <th className="py-2 pr-4">Dignity</th>
              <th className="py-2">Flags</th>
            </tr>
          </thead>
          <tbody>
            {chart.planets.map((p) => (
              <tr key={p.planet} className="border-b border-white/5 text-slate-200">
                <td className="py-2 pr-4 font-medium capitalize">{p.planet}</td>
                <td className="py-2 pr-4 capitalize">{p.rashi}</td>
                <td className="py-2 pr-4">{p.rashi_degree.toFixed(2)}°</td>
                <td className="py-2 pr-4">{p.house_number}</td>
                <td className="py-2 pr-4">
                  {p.nakshatra} ({p.pada})
                </td>
                <td className="py-2 pr-4 capitalize">{p.dignity ?? "—"}</td>
                <td className="py-2 text-xs text-slate-400">
                  {p.is_retrograde && "Retrograde "}
                  {p.is_combust && "Combust"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
