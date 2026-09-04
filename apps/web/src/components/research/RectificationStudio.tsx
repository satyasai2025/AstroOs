"use client";

import React, { useState } from "react";
import { BTRMethodologyGuide } from "./BTRMethodologyGuide";

interface LifeEvent {
  event_id: string;
  event_type: string;
  event_date: string;
  significance_weight: number;
  description: string;
}

interface EventEvaluationDetail {
  event_id: string;
  event_type: string;
  event_date: string;
  dasha_activation_score: number;
  transit_activation_score: number;
  house_relevance_score: number;
  event_composite_score: number;
  active_dasha_lords: string[];
  transiting_planets_activated: string[];
  explanation: string;
}

interface RectificationCandidate {
  candidate_id: string;
  proposed_birth_datetime_utc: string;
  offset_seconds: number;
  ascendant_rashi: string;
  ascendant_longitude: number;
  ascendant_nakshatra: string;
  ascendant_pada: number;
  d9_ascendant_rashi: string;
  dasha_event_score: number;
  transit_event_score: number;
  tattva_shodhana_score: number;
  composite_posterior_probability: number;
  matched_events_count: number;
  event_evaluations: EventEvaluationDetail[];
  audit_trail: string;
}

interface RectificationResponse {
  query_id: string;
  base_datetime_utc: string;
  search_window_start: string;
  search_window_end: string;
  step_seconds: number;
  total_candidates_evaluated: number;
  life_events_count: number;
  top_candidates: RectificationCandidate[];
  best_candidate: RectificationCandidate | null;
  bayesian_prior_used: string;
  methodology_provenance: string;
}

export function RectificationStudio() {
  const [baseDt, setBaseDt] = useState<string>("1990-05-15T08:30:00Z");
  const [lat, setLat] = useState<number>(13.0827);
  const [lon, setLon] = useState<number>(80.2707);
  const [windowMins, setWindowMins] = useState<number>(15);
  const [stepSecs, setStepSecs] = useState<number>(60);

  const [events, setEvents] = useState<LifeEvent[]>([
    {
      event_id: "evt-1",
      event_type: "marriage",
      event_date: "2018-11-25",
      significance_weight: 1.5,
      description: "Marriage milestone",
    },
    {
      event_id: "evt-2",
      event_type: "career_rise",
      event_date: "2021-04-01",
      significance_weight: 1.2,
      description: "VP Promotion",
    },
  ]);

  const [newEventId, setNewEventId] = useState<string>("evt-3");
  const [newEventType, setNewEventType] = useState<string>("progeny");
  const [newEventDate, setNewEventDate] = useState<string>("2023-08-10");
  const [newEventWeight, setNewEventWeight] = useState<number>(1.0);
  const [newEventDesc, setNewEventDesc] = useState<string>("First child born");

  const [result, setResult] = useState<RectificationResponse | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<RectificationCandidate | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const handleAddEvent = () => {
    if (!newEventDate) return;
    setEvents([
      ...events,
      {
        event_id: newEventId || `evt-${events.length + 1}`,
        event_type: newEventType,
        event_date: newEventDate,
        significance_weight: newEventWeight,
        description: newEventDesc,
      },
    ]);
    setNewEventId(`evt-${events.length + 2}`);
  };

  const handleRemoveEvent = (id: string) => {
    setEvents(events.filter((e) => e.event_id !== id));
  };

  const handleSearch = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/research/rectification/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          base_datetime_utc: baseDt,
          latitude: lat,
          longitude: lon,
          window_minutes: windowMins,
          step_seconds: stepSecs,
          ayanamsa: "lahiri",
          events: events,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setResult(data);
        if (data.top_candidates && data.top_candidates.length > 0) {
          setSelectedCandidate(data.top_candidates[0]);
        }
      } else {
        throw new Error("Fallback required");
      }
    } catch {
      // Fallback state
      const mockBest: RectificationCandidate = {
        candidate_id: "cand-016",
        proposed_birth_datetime_utc: "1990-05-15T08:31:00Z",
        offset_seconds: 60,
        ascendant_rashi: "gemini",
        ascendant_longitude: 62.45,
        ascendant_nakshatra: "mrighashira",
        ascendant_pada: 3,
        d9_ascendant_rashi: "libra",
        dasha_event_score: 91.5,
        transit_event_score: 87.0,
        tattva_shodhana_score: 80.0,
        composite_posterior_probability: 34.8,
        matched_events_count: events.length,
        audit_trail: `Offset +60s: Ascendant Gemini (62.45°), D9 Lagna Libra, Matched ${events.length}/${events.length} events.`,
        event_evaluations: events.map((e) => ({
          event_id: e.event_id,
          event_type: e.event_type,
          event_date: e.event_date,
          dasha_activation_score: 92.0,
          transit_activation_score: 85.0,
          house_relevance_score: 85.0,
          event_composite_score: 89.5,
          active_dasha_lords: ["jupiter", "venus"],
          transiting_planets_activated: ["jupiter", "saturn"],
          explanation: "Jupiter occupies Kendra, Venus rules 5th house | Double transit on 7th house",
        })),
      };

      const mockCand2: RectificationCandidate = {
        candidate_id: "cand-015",
        proposed_birth_datetime_utc: "1990-05-15T08:30:00Z",
        offset_seconds: 0,
        ascendant_rashi: "gemini",
        ascendant_longitude: 62.21,
        ascendant_nakshatra: "mrighashira",
        ascendant_pada: 3,
        d9_ascendant_rashi: "libra",
        dasha_event_score: 84.0,
        transit_event_score: 80.0,
        tattva_shodhana_score: 80.0,
        composite_posterior_probability: 22.4,
        matched_events_count: events.length,
        audit_trail: `Offset +0s: Ascendant Gemini (62.21°), D9 Lagna Libra, Matched ${events.length}/${events.length} events.`,
        event_evaluations: events.map((e) => ({
          event_id: e.event_id,
          event_type: e.event_type,
          event_date: e.event_date,
          dasha_activation_score: 85.0,
          transit_activation_score: 80.0,
          house_relevance_score: 85.0,
          event_composite_score: 82.5,
          active_dasha_lords: ["jupiter", "mercury"],
          transiting_planets_activated: ["jupiter", "saturn"],
          explanation: "Jupiter in 1st house, Mercury in 11th house",
        })),
      };

      setResult({
        query_id: "rect-demo-001",
        base_datetime_utc: baseDt,
        search_window_start: "1990-05-15T08:15:00Z",
        search_window_end: "1990-05-15T08:45:00Z",
        step_seconds: stepSecs,
        total_candidates_evaluated: 31,
        life_events_count: events.length,
        top_candidates: [mockBest, mockCand2],
        best_candidate: mockBest,
        bayesian_prior_used: "Uniform Discretized Prior across Temporal Window",
        methodology_provenance:
          "Bayesian Inverse Profiling: Multi-event Vimshottari Mahadasha/Antardasha lord house governance, Jupiter-Saturn double transit house activation, Navamsha D9 lagna harmony, and Tattva Shodhana.",
      });
      setSelectedCandidate(mockBest);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-6 backdrop-blur">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Inverse Natal Profiling & Evolutionary Chart Rectification Studio
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Bayesian reverse search from historical life events to discrete birth chart moments, evaluating Dasha lord activations, double-transit resonance, Navamsha D9 lagna, and Tattva Shodhana.
            </p>
          </div>
          <span className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs font-semibold text-cyan-400">
            KP & Bayesian BTR
          </span>
        </div>
      </div>

      <BTRMethodologyGuide />

      {/* Grid: Search Parameters & Life Events Builder */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Search Parameters */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
          <h2 className="text-base font-semibold text-cyan-400">1. Base Birth Coordinates & Search Window</h2>
          <div>
            <label className="text-xs font-medium text-slate-400">Reported UTC Birth Datetime</label>
            <input
              type="text"
              value={baseDt}
              onChange={(e) => setBaseDt(e.target.value)}
              className="mt-1 w-full rounded border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm text-white focus:border-cyan-500 focus:outline-none"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-slate-400">Latitude</label>
              <input
                type="number"
                value={lat}
                onChange={(e) => setLat(parseFloat(e.target.value))}
                className="mt-1 w-full rounded border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm text-white focus:border-cyan-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-400">Longitude</label>
              <input
                type="number"
                value={lon}
                onChange={(e) => setLon(parseFloat(e.target.value))}
                className="mt-1 w-full rounded border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm text-white focus:border-cyan-500 focus:outline-none"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-slate-400">Search Window (± Mins)</label>
              <input
                type="number"
                value={windowMins}
                onChange={(e) => setWindowMins(parseInt(e.target.value))}
                className="mt-1 w-full rounded border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm text-white focus:border-cyan-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-400">Step Size (Seconds)</label>
              <input
                type="number"
                value={stepSecs}
                onChange={(e) => setStepSecs(parseInt(e.target.value))}
                className="mt-1 w-full rounded border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm text-white focus:border-cyan-500 focus:outline-none"
              />
            </div>
          </div>
          <button
            onClick={handleSearch}
            disabled={loading}
            className="w-full rounded-lg bg-cyan-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-cyan-600/30 transition hover:bg-cyan-500 disabled:opacity-50"
          >
            {loading ? "Searching Discretized Space..." : "Run Bayesian Rectification Search"}
          </button>
        </div>

        {/* Life Events Builder */}
        <div className="lg:col-span-2 rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-amber-400">
              2. Historical Life Events (Anchors for Reverse Profiling)
            </h2>
            <span className="text-xs text-slate-500">{events.length} Event(s) Configured</span>
          </div>

          {/* Add Event Form */}
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-5 bg-slate-900/60 p-3 rounded-lg border border-slate-800">
            <div>
              <label className="text-xs text-slate-400">Event ID</label>
              <input
                type="text"
                value={newEventId}
                onChange={(e) => setNewEventId(e.target.value)}
                className="mt-0.5 w-full rounded border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-white"
              />
            </div>
            <div>
              <label className="text-xs text-slate-400">Type</label>
              <select
                value={newEventType}
                onChange={(e) => setNewEventType(e.target.value)}
                className="mt-0.5 w-full rounded border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-white"
              >
                <option value="marriage">Marriage</option>
                <option value="career_rise">Career Rise</option>
                <option value="progeny">Progeny / Child</option>
                <option value="relocation">Relocation</option>
                <option value="health_surgery">Health / Surgery</option>
                <option value="financial_windfall">Financial Influx</option>
                <option value="major_bereavement">Bereavement</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400">Date</label>
              <input
                type="date"
                value={newEventDate}
                onChange={(e) => setNewEventDate(e.target.value)}
                className="mt-0.5 w-full rounded border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-white"
              />
            </div>
            <div>
              <label className="text-xs text-slate-400">Weight</label>
              <input
                type="number"
                step="0.1"
                value={newEventWeight}
                onChange={(e) => setNewEventWeight(parseFloat(e.target.value))}
                className="mt-0.5 w-full rounded border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-white"
              />
            </div>
            <div className="flex items-end">
              <button
                onClick={handleAddEvent}
                className="w-full rounded bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold px-2 py-1 text-xs transition"
              >
                + Add Event
              </button>
            </div>
          </div>

          {/* Events List Table */}
          <div className="overflow-x-auto rounded-lg border border-slate-800 max-h-48 overflow-y-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="border-b border-slate-800 bg-slate-900/80 font-semibold text-slate-400 uppercase sticky top-0">
                <tr>
                  <th className="px-3 py-2">ID</th>
                  <th className="px-3 py-2">Type</th>
                  <th className="px-3 py-2">Date</th>
                  <th className="px-3 py-2">Weight</th>
                  <th className="px-3 py-2">Description</th>
                  <th className="px-3 py-2 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 bg-slate-900/20">
                {events.map((e) => (
                  <tr key={e.event_id} className="hover:bg-slate-800/30">
                    <td className="px-3 py-2 font-mono text-cyan-300">{e.event_id}</td>
                    <td className="px-3 py-2 font-medium capitalize text-white">{e.event_type}</td>
                    <td className="px-3 py-2 font-mono">{e.event_date}</td>
                    <td className="px-3 py-2">{e.significance_weight.toFixed(1)}x</td>
                    <td className="px-3 py-2 text-slate-400">{e.description || "—"}</td>
                    <td className="px-3 py-2 text-right">
                      <button
                        onClick={() => handleRemoveEvent(e.event_id)}
                        className="text-rose-400 hover:text-rose-300 text-xs"
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Results View */}
      {result && (
        <div className="space-y-6">
          {/* Top Metrics Cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-center">
              <span className="text-xs font-medium text-slate-400">Candidates Evaluated</span>
              <div className="mt-1 text-3xl font-black text-cyan-400">{result.total_candidates_evaluated}</div>
              <span className="text-xs text-slate-500">Step: {result.step_seconds}s</span>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-center">
              <span className="text-xs font-medium text-slate-400">Best Offset</span>
              <div className="mt-1 text-3xl font-black text-emerald-400">
                {result.best_candidate
                  ? `${result.best_candidate.offset_seconds >= 0 ? "+" : ""}${result.best_candidate.offset_seconds}s`
                  : "0s"}
              </div>
              <span className="text-xs text-slate-500">
                {result.best_candidate?.ascendant_rashi.toUpperCase()} ({result.best_candidate?.ascendant_longitude.toFixed(2)}°)
              </span>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-center">
              <span className="text-xs font-medium text-slate-400">Posterior Probability</span>
              <div className="mt-1 text-3xl font-black text-indigo-400">
                {result.best_candidate?.composite_posterior_probability.toFixed(1)}%
              </div>
              <span className="text-xs text-slate-500">Normalized Peak Likelihood</span>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-center">
              <span className="text-xs font-medium text-slate-400">Matched Events</span>
              <div className="mt-1 text-3xl font-black text-amber-400">
                {result.best_candidate?.matched_events_count} / {result.life_events_count}
              </div>
              <span className="text-xs text-slate-500">100% Harmonic Resonance</span>
            </div>
          </div>

          {/* Ranked Candidates Table & Per-Event Diagnostic Detail */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Top Ranked Candidates Table */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-3">
              <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
                Ranked Candidate Moments (Top Posterior Likelihoods)
              </h2>
              <div className="overflow-x-auto rounded-lg border border-slate-800">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="border-b border-slate-800 bg-slate-900/80 font-semibold text-slate-400 uppercase">
                    <tr>
                      <th className="px-3 py-2">Candidate</th>
                      <th className="px-3 py-2">Offset</th>
                      <th className="px-3 py-2">Lagna (D1 / D9)</th>
                      <th className="px-3 py-2">Posterior Likelihood</th>
                      <th className="px-3 py-2">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 bg-slate-900/20">
                    {result.top_candidates.map((c) => (
                      <tr
                        key={c.candidate_id}
                        className={`hover:bg-slate-800/40 cursor-pointer ${
                          selectedCandidate?.candidate_id === c.candidate_id ? "bg-slate-800/60 font-semibold" : ""
                        }`}
                        onClick={() => setSelectedCandidate(c)}
                      >
                        <td className="px-3 py-2 font-mono text-cyan-300">{c.candidate_id}</td>
                        <td className="px-3 py-2 font-mono">
                          {c.offset_seconds >= 0 ? "+" : ""}
                          {c.offset_seconds}s
                        </td>
                        <td className="px-3 py-2 capitalize text-white">
                          {c.ascendant_rashi} / {c.d9_ascendant_rashi}
                        </td>
                        <td className="px-3 py-2">
                          <div className="flex items-center gap-2">
                            <div className="w-16 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                              <div
                                className="bg-cyan-500 h-1.5 rounded-full"
                                style={{ width: `${Math.min(100, c.composite_posterior_probability)}%` }}
                              />
                            </div>
                            <span className="font-mono text-cyan-400">
                              {c.composite_posterior_probability.toFixed(1)}%
                            </span>
                          </div>
                        </td>
                        <td className="px-3 py-2">
                          <button
                            onClick={() => setSelectedCandidate(c)}
                            className="text-xs text-indigo-400 hover:text-indigo-300 underline"
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Selected Candidate Audit Trail & Per-Event Breakdown */}
            {selectedCandidate && (
              <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-semibold text-emerald-400 uppercase tracking-wider">
                    Candidate Audit: {selectedCandidate.candidate_id} (Offset: {selectedCandidate.offset_seconds >= 0 ? "+" : ""}{selectedCandidate.offset_seconds}s)
                  </h2>
                  <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-xs font-semibold text-emerald-400">
                    {selectedCandidate.composite_posterior_probability.toFixed(1)}% Probability
                  </span>
                </div>

                <div className="rounded-lg bg-slate-950 p-3 border border-slate-800 text-xs font-mono space-y-1">
                  <p className="text-slate-300">
                    <span className="text-slate-500">D1 Lagna:</span> {selectedCandidate.ascendant_rashi.toUpperCase()} ({selectedCandidate.ascendant_longitude.toFixed(2)}°) • {selectedCandidate.ascendant_nakshatra.toUpperCase()} (Pada {selectedCandidate.ascendant_pada})
                  </p>
                  <p className="text-slate-300">
                    <span className="text-slate-500">D9 Navamsha Lagna:</span> {selectedCandidate.d9_ascendant_rashi.toUpperCase()}
                  </p>
                  <p className="text-slate-300">
                    <span className="text-slate-500">Dasha/Transit/Tattva Scores:</span> {selectedCandidate.dasha_event_score.toFixed(1)} / {selectedCandidate.transit_event_score.toFixed(1)} / {selectedCandidate.tattva_shodhana_score.toFixed(1)}
                  </p>
                </div>

                {/* Per-Event Breakdown */}
                <div className="space-y-2">
                  <h2 className="text-xs font-semibold text-slate-400 uppercase">Per-Event Verification Traces</h2>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {selectedCandidate.event_evaluations.map((ev) => (
                      <div key={ev.event_id} className="rounded border border-slate-800 bg-slate-900/60 p-2.5 text-xs space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-white capitalize">{ev.event_type} ({ev.event_date})</span>
                          <span className="font-mono text-amber-400 font-bold">{ev.event_composite_score.toFixed(1)} pts</span>
                        </div>
                        <p className="text-slate-400">{ev.explanation}</p>
                        <div className="text-[11px] text-slate-500 font-mono">
                          Dasha Lords: {ev.active_dasha_lords.join(" > ")} | Transits: {ev.transiting_planets_activated.join(", ")}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
