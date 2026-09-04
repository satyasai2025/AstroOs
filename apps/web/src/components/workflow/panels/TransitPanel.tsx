import type { TransitResponse } from "@/lib/types";

export function TransitPanel({ transits }: { transits: TransitResponse }) {
  return (
    <div className="glass-card overflow-x-auto p-5">
      <h3 className="mb-1 text-sm font-semibold uppercase tracking-wide text-amber-300/80">
        Current Transits (Gochara)
      </h3>
      <p className="mb-3 text-xs text-slate-500">
        As of {new Date(transits.transit_datetime_utc).toUTCString()} · Natal Moon:{" "}
        {transits.natal_moon_rashi}
      </p>
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-white/10 text-xs uppercase tracking-wide text-slate-500">
            <th className="py-2 pr-4">Planet</th>
            <th className="py-2 pr-4">Rashi</th>
            <th className="py-2 pr-4">House from Moon</th>
            <th className="py-2">Flags</th>
          </tr>
        </thead>
        <tbody>
          {transits.planets.map((p) => (
            <tr key={p.planet} className="border-b border-white/5 text-slate-200">
              <td className="py-2 pr-4 font-medium capitalize">{p.planet}</td>
              <td className="py-2 pr-4 capitalize">{p.transit_rashi}</td>
              <td className="py-2 pr-4">{p.house_from_natal_moon}</td>
              <td className="py-2 text-xs text-slate-400">
                {p.is_sade_sati && "Sade Sati "}
                {p.is_ashtama_shani && "Ashtama Shani "}
                {p.has_vedha && `Vedha (${p.vedha_planet}) `}
                {p.has_vipreet_vedha && "Vipreet Vedha relief"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
