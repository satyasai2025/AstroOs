"use client";

import { useState } from "react";
import type { ChartComparisonResponse } from "@/lib/types";
import { aiApi } from "@/lib/ai";

interface BirthDataEntry {
  birth_datetime_utc: string;
  latitude: number;
  longitude: number;
  subject_name: string;
}

export function ChartComparisonPanel() {
  const [personA, setPersonA] = useState<BirthDataEntry>({
    birth_datetime_utc: "",
    latitude: 0,
    longitude: 0,
    subject_name: "Person A",
  });
  const [personB, setPersonB] = useState<BirthDataEntry>({
    birth_datetime_utc: "",
    latitude: 0,
    longitude: 0,
    subject_name: "Person B",
  });
  const [ayanamsa, setAyanamsa] = useState("lahiri");
  const [houseSystem, setHouseSystem] = useState("W");
  const [result, setResult] = useState<ChartComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCompare() {
    setLoading(true);
    setError(null);
    try {
      const res = await aiApi.compareCharts({
        birth_datetime_utc_a: personA.birth_datetime_utc,
        latitude_a: personA.latitude,
        longitude_a: personA.longitude,
        subject_name_a: personA.subject_name,
        birth_datetime_utc_b: personB.birth_datetime_utc,
        latitude_b: personB.latitude,
        longitude_b: personB.longitude,
        subject_name_b: personB.subject_name,
        ayanamsa,
        house_system: houseSystem,
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Comparison failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-amber-300/80">
        Chart Comparison
      </h3>
      <p className="text-xs text-slate-400">
        Compare two birth charts side-by-side for compatibility and differences.
      </p>

      {/* Input forms */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {/* Person A */}
        <div className="rounded-lg border border-white/10 bg-white/3 p-3 space-y-2">
          <p className="text-xs font-semibold text-slate-300">{personA.subject_name}</p>
          <input
            type="datetime-local"
            value={personA.birth_datetime_utc ? personA.birth_datetime_utc.slice(0, 16) : ""}
            onChange={(e) =>
              setPersonA({ ...personA, birth_datetime_utc: e.target.value + ":00Z" })
            }
            className="w-full rounded border border-white/10 bg-white/5 px-2 py-1 text-xs text-slate-200"
            placeholder="Birth date & time"
          />
          <div className="flex gap-2">
            <input
              type="number"
              value={personA.latitude || ""}
              onChange={(e) => setPersonA({ ...personA, latitude: parseFloat(e.target.value) || 0 })}
              className="w-1/2 rounded border border-white/10 bg-white/5 px-2 py-1 text-xs text-slate-200"
              placeholder="Latitude"
            />
            <input
              type="number"
              value={personA.longitude || ""}
              onChange={(e) => setPersonA({ ...personA, longitude: parseFloat(e.target.value) || 0 })}
              className="w-1/2 rounded border border-white/10 bg-white/5 px-2 py-1 text-xs text-slate-200"
              placeholder="Longitude"
            />
          </div>
        </div>

        {/* Person B */}
        <div className="rounded-lg border border-white/10 bg-white/3 p-3 space-y-2">
          <p className="text-xs font-semibold text-slate-300">{personB.subject_name}</p>
          <input
            type="datetime-local"
            value={personB.birth_datetime_utc ? personB.birth_datetime_utc.slice(0, 16) : ""}
            onChange={(e) =>
              setPersonB({ ...personB, birth_datetime_utc: e.target.value + ":00Z" })
            }
            className="w-full rounded border border-white/10 bg-white/5 px-2 py-1 text-xs text-slate-200"
            placeholder="Birth date & time"
          />
          <div className="flex gap-2">
            <input
              type="number"
              value={personB.latitude || ""}
              onChange={(e) => setPersonB({ ...personB, latitude: parseFloat(e.target.value) || 0 })}
              className="w-1/2 rounded border border-white/10 bg-white/5 px-2 py-1 text-xs text-slate-200"
              placeholder="Latitude"
            />
            <input
              type="number"
              value={personB.longitude || ""}
              onChange={(e) => setPersonB({ ...personB, longitude: parseFloat(e.target.value) || 0 })}
              className="w-1/2 rounded border border-white/10 bg-white/5 px-2 py-1 text-xs text-slate-200"
              placeholder="Longitude"
            />
          </div>
        </div>
      </div>

      {/* Settings */}
      <div className="flex gap-3">
        <select
          value={ayanamsa}
          onChange={(e) => setAyanamsa(e.target.value)}
          className="rounded border border-white/10 bg-white/5 px-2 py-1 text-xs text-slate-200"
        >
          <option value="lahiri">Lahiri</option>
          <option value="kp">KP</option>
          <option value="raman">Raman</option>
          <option value="yukteshwar">Yukteshwar</option>
        </select>
        <select
          value={houseSystem}
          onChange={(e) => setHouseSystem(e.target.value)}
          className="rounded border border-white/10 bg-white/5 px-2 py-1 text-xs text-slate-200"
        >
          <option value="W">Whole Sign</option>
          <option value="P">Placidus</option>
          <option value="K">Koch</option>
          <option value="E">Equal</option>
        </select>
        <button
          type="button"
          onClick={handleCompare}
          disabled={loading || !personA.birth_datetime_utc || !personB.birth_datetime_utc}
          className="rounded-lg bg-amber-600 px-4 py-1.5 text-xs font-semibold text-cosmos-950 hover:bg-amber-500 disabled:opacity-40 transition-colors"
        >
          {loading ? "Comparing…" : "Compare Charts"}
        </button>
      </div>

      {error && <p className="text-xs text-red-400">{error}</p>}

      {/* Results */}
      {result && (
        <div className="space-y-4 rounded-lg border border-white/10 bg-white/3 p-4">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-slate-200">Comparison Results</p>
            <span className="rounded-full bg-amber-900/30 px-2 py-0.5 text-xs text-amber-300">
              {Math.round(result.overall_similarity * 100)}% Similar
            </span>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">{result.summary}</p>

          {/* Key Similarities */}
          {result.key_similarities.length > 0 && (
            <div>
              <p className="mb-2 text-xs font-semibold text-green-400">Key Similarities</p>
              <div className="space-y-2">
                {result.key_similarities.map((d, i) => (
                  <div key={i} className="rounded border border-green-900/30 bg-green-900/10 p-2">
                    <p className="text-xs font-medium text-slate-200">{d.dimension}</p>
                    <p className="text-xs text-slate-400">{d.commentary}</p>
                    <div className="mt-1 flex gap-4 text-xs text-slate-500">
                      <span>A: {d.chart_a_value}</span>
                      <span>B: {d.chart_b_value}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Key Differences */}
          {result.key_differences.length > 0 && (
            <div>
              <p className="mb-2 text-xs font-semibold text-red-400">Key Differences</p>
              <div className="space-y-2">
                {result.key_differences.map((d, i) => (
                  <div key={i} className="rounded border border-red-900/30 bg-red-900/10 p-2">
                    <p className="text-xs font-medium text-slate-200">{d.dimension}</p>
                    <p className="text-xs text-slate-400">{d.commentary}</p>
                    <div className="mt-1 flex gap-4 text-xs text-slate-500">
                      <span>A: {d.chart_a_value}</span>
                      <span>B: {d.chart_b_value}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Compatibility Notes */}
          {result.compatibility_notes && (
            <div className="rounded border border-blue-900/30 bg-blue-900/10 p-3">
              <p className="mb-1 text-xs font-semibold text-blue-300">Compatibility</p>
              <p className="text-xs text-slate-300">{result.compatibility_notes}</p>
            </div>
          )}

          {result.relationship_potential && (
            <div className="rounded border border-purple-900/30 bg-purple-900/10 p-3">
              <p className="mb-1 text-xs font-semibold text-purple-300">Relationship Potential</p>
              <p className="text-xs text-slate-300">{result.relationship_potential}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}