"use client";

import { useState, useEffect } from "react";
import {
  evaluateSBCSangyaRayMatrix,
  type SBCSangyaRayMatrixResponse,
  type SangyaVedhaStatus,
  type SBCRayCollision,
} from "@/lib/kpSbcAnalysis";

interface Props {
  natalChart?: Record<string, unknown>;
}

const DEFAULT_NATAL_CHART = {
  planets: [
    { planet: "Moon", nakshatra: "Rohini", longitude: 45.0, house_number: 1 },
    { planet: "Jupiter", nakshatra: "Pushya", longitude: 105.0, house_number: 4 },
    { planet: "Sun", nakshatra: "Magha", longitude: 125.0, house_number: 5 },
    { planet: "Mercury", nakshatra: "Purva Phalguni", longitude: 140.0, house_number: 5 },
    { planet: "Venus", nakshatra: "Hasta", longitude: 165.0, house_number: 6 },
    { planet: "Mars", nakshatra: "Anuradha", longitude: 220.0, house_number: 8 },
    { planet: "Saturn", nakshatra: "Shravana", longitude: 285.0, house_number: 10 },
    { planet: "Rahu", nakshatra: "Shatabhisha", longitude: 310.0, house_number: 11 },
    { planet: "Ketu", nakshatra: "Purva Phalguni", longitude: 130.0, house_number: 5 },
  ],
};

export function SBCSangyaRayMatrix({ natalChart }: Props) {
  const [data, setData] = useState<SBCSangyaRayMatrixResponse | null>(null);
  const [selectedSangyaKey, setSelectedSangyaKey] = useState<string>("karma");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadMatrix() {
      try {
        setLoading(true);
        setError(null);
        const chart = natalChart || DEFAULT_NATAL_CHART;
        const res = await evaluateSBCSangyaRayMatrix(chart);
        setData(res);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load SBC Sangya Ray Matrix.");
      } finally {
        setLoading(false);
      }
    }
    loadMatrix();
  }, [natalChart]);

  const activeSangya = data?.sangya_statuses.find((s) => s.sangya_key === selectedSangyaKey) || data?.sangya_statuses[0];

  return (
    <div className="space-y-6" data-testid="sbc-sangya-ray-matrix">
      {/* 1. Header & Confluence Badge */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
            SARVATOBHADRA CHAKRA (SBC) ANALYSIS
          </span>
          <h2 className="text-xl font-bold text-slate-900 mt-1 flex items-center gap-2">
            <span>☸️</span> 10 Classical Sangyas &amp; Transit-to-Natal Vedha Ray Matrix
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Full 9x9 Chakra coordinate mapping with motion-based ray trajectory casting (Front, Left, Right, All 3).
          </p>
        </div>

        {data && (
          <div className="flex items-center gap-3 bg-white p-2.5 rounded-xl border border-slate-200 shadow-sm text-xs">
            <span className="text-slate-400 font-medium">Net Confluence:</span>
            <span
              className={`font-bold font-mono px-2.5 py-0.5 rounded ${
                data.overall_sbc_confluence_score > 0
                  ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                  : data.overall_sbc_confluence_score < 0
                  ? "bg-red-100 text-red-800 border border-red-300"
                  : "bg-slate-100 text-slate-700 border border-slate-200"
              }`}
            >
              {data.overall_sbc_confluence_score > 0 ? `+${data.overall_sbc_confluence_score}` : data.overall_sbc_confluence_score} / 10.0
            </span>
          </div>
        )}
      </div>

      {/* 2. KP Cross-Link Summary Banner */}
      {data && (
        <div className="p-4 rounded-xl bg-indigo-50 border border-indigo-200 flex items-start gap-3 text-xs text-indigo-950 shadow-sm">
          <span className="text-base leading-none mt-0.5">🔗</span>
          <div>
            <strong className="text-indigo-900 font-bold block mb-0.5">KP &amp; SBC Synchronized Evidence</strong>
            <span className="text-indigo-900 leading-relaxed font-medium">{data.kp_cross_link_summary}</span>
          </div>
        </div>
      )}

      {loading ? (
        <div className="p-8 text-center text-xs text-slate-400 bg-white border border-slate-200 rounded-xl">Computing 9x9 SBC Vedha Rays &amp; 10 Sangyas…</div>
      ) : error ? (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-xs text-red-800">{error}</div>
      ) : data ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: 10 Sangyas Table */}
          <div className="lg:col-span-7 space-y-3">
            <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
              <span className="font-bold uppercase tracking-wider text-slate-700">10 Classical Sangyas (Natal Moon: {data.natal_moon_nakshatra})</span>
              <span className="font-semibold">{data.sangya_statuses.length} Sangyas</span>
            </div>

            <div className="border rounded-xl overflow-hidden border-slate-200 bg-white shadow-sm max-h-[600px] overflow-y-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-100/90 text-slate-700 border-b border-slate-200 text-[11px] font-bold uppercase tracking-wider sticky top-0 z-10 backdrop-blur">
                  <tr>
                    <th className="p-3">Sangya</th>
                    <th className="p-3">Nakshatra</th>
                    <th className="p-3">Benefic Vedhas</th>
                    <th className="p-3">Malefic Obstr</th>
                    <th className="p-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-800">
                  {data.sangya_statuses.map((s) => {
                    const isSelected = s.sangya_key === selectedSangyaKey;
                    return (
                      <tr
                        key={s.sangya_key}
                        onClick={() => setSelectedSangyaKey(s.sangya_key)}
                        className={`cursor-pointer transition ${
                          isSelected ? "bg-indigo-50/90 font-medium border-l-4 border-l-indigo-600" : "hover:bg-slate-50"
                        }`}
                      >
                        <td className="p-3">
                          <div className="font-bold text-slate-900 text-sm">{s.sangya_name}</div>
                          <div className="text-[11px] text-slate-400 font-normal line-clamp-1">{s.domain}</div>
                        </td>
                        <td className="p-3 font-mono text-[11px] text-slate-700 font-medium">
                          {s.natal_nakshatra} ({s.natal_nakshatra_number})
                        </td>
                        <td className="p-3 text-emerald-700 font-mono text-[11px] font-semibold">
                          {s.benefic_hits.map((h) => h.transit_planet).join(", ") || "-"}
                        </td>
                        <td className="p-3 text-red-700 font-mono text-[11px] font-semibold">
                          {s.malefic_hits.map((h) => h.transit_planet).join(", ") || "-"}
                        </td>
                        <td className="p-3">
                          <span
                            className={`text-[11px] px-2.5 py-0.5 rounded-full font-semibold ${
                              s.net_score > 0
                                ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                                : s.is_obstructed
                                ? "bg-red-100 text-red-800 border border-red-300"
                                : "bg-slate-100 text-slate-700 border border-slate-200"
                            }`}
                          >
                            {s.verdict.split(" ")[0]}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Right Column: Sangya Detail & Ray Inspector */}
          <div className="lg:col-span-5 space-y-4">
            {activeSangya && (
              <div className="p-5 rounded-2xl border border-slate-200 bg-white shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                  <div>
                    <span className="text-[10px] font-mono text-indigo-700 uppercase font-bold tracking-wider">SANGYA DETAIL INSPECTOR</span>
                    <h2 className="text-base font-bold text-slate-900">{activeSangya.sangya_name}</h2>
                  </div>
                  <span className="text-xs font-mono text-slate-400 font-semibold bg-slate-100 px-2 py-1 rounded">
                    Cell ({activeSangya.grid_coord.row}, {activeSangya.grid_coord.col})
                  </span>
                </div>

                <p className="text-xs text-slate-700 leading-relaxed font-medium">
                  <strong className="text-slate-900 font-bold">Signification Domain: </strong>{activeSangya.domain}
                </p>

                {/* Ray Hits Breakdown */}
                <div className="space-y-2">
                  <div className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    Active Vedha Ray Hits ({activeSangya.benefic_hits.length + activeSangya.malefic_hits.length} Total)
                  </div>

                  {activeSangya.benefic_hits.length > 0 && (
                    <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 space-y-1.5 text-xs text-emerald-950">
                      <strong className="font-bold text-emerald-900 block">Benefic Vedha Rays (+Shielding):</strong>
                      {activeSangya.benefic_hits.map((h, i) => (
                        <div key={i} className="flex justify-between items-center text-[11px] font-medium text-emerald-900">
                          <span>• {h.transit_planet} from {h.source_cell.element_name}</span>
                          <span className="font-mono font-bold text-emerald-700">Ray: {h.ray_direction}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {activeSangya.malefic_hits.length > 0 && (
                    <div className="p-3.5 rounded-xl bg-red-50 border border-red-200 space-y-1.5 text-xs text-red-950">
                      <strong className="font-bold text-red-900 block">Malefic Obstruction Rays (-Affliction):</strong>
                      {activeSangya.malefic_hits.map((h, i) => (
                        <div key={i} className="flex justify-between items-center text-[11px] font-medium text-red-900">
                          <span>• {h.transit_planet} from {h.source_cell.element_name}</span>
                          <span className="font-mono font-bold text-red-700">Ray: {h.ray_direction}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {activeSangya.benefic_hits.length === 0 && activeSangya.malefic_hits.length === 0 && (
                    <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-400 text-center font-medium">
                      No direct Vedha ray collisions targeting this Sangya at the transit moment.
                    </div>
                  )}
                </div>

                {/* Audit Trace */}
                <div className="space-y-1.5">
                  <div className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    Sangya Ray Calculation Trace
                  </div>
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1 font-mono text-[11px] text-slate-800">
                    {activeSangya.audit_trace.map((step, idx) => (
                      <div key={idx} className="flex items-start gap-1.5">
                        <span className="text-indigo-600 font-bold">›</span>
                        <span>{step}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
