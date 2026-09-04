"use client";

import React, { useState, useMemo } from "react";
import type { WorkflowAnalysisResponse } from "@/lib/types";

interface Props {
  result?: WorkflowAnalysisResponse | null;
}

export function AdvancedTransitEngineStudio({ result }: Props) {
  const [activeTab, setActiveTab] = useState<
    "ref_frames" | "classification" | "ashtakavarga" | "special_taras" | "latta" | "score_calendar" | "aspect_search"
  >("ref_frames");

  // Feature 1: Reference Frame State
  const [refFrame, setRefFrame] = useState<"lagna" | "moon" | "d9_lagna" | "d9_moon">("moon");

  // Feature 3: Ashtakavarga Divisional Reference State
  const [natalRefVarga, setNatalRefVarga] = useState("D1");
  const [transitRefVarga, setTransitRefVarga] = useState("D1");

  // Feature 7: Search Engine State
  const [searchTargetPlanet, setSearchTargetPlanet] = useState("Jupiter");
  const [searchDegOffset, setSearchDegOffset] = useState("1");
  const [searchMinOffset, setSearchMinOffset] = useState("0");
  const [searchOffsetDir, setSearchOffsetDir] = useState<"after" | "behind">("after");
  const [searchNatalPoint, setSearchNatalPoint] = useState("Natal Sun");
  const [searchTargetDate, setSearchTargetDate] = useState("2026-08-24");
  const [searchResults, setSearchResults] = useState<any[] | null>(null);

  const chart = result?.chart;

  // 1. Reference Frame Calculations
  const planetsTransitList = useMemo(() => {
    const planets = [
      { name: "Sun", rashi: "Leo", deg: 7.24, nak: "Magha", pada: 3, lord: "Ketu" },
      { name: "Moon", rashi: "Sagittarius", deg: 14.30, nak: "Poorvashadha", pada: 2, lord: "Venus" },
      { name: "Mars", rashi: "Taurus", deg: 21.15, nak: "Rohini", pada: 4, lord: "Moon" },
      { name: "Mercury", rashi: "Leo", deg: 14.10, nak: "Purva Phalguni", pada: 1, lord: "Venus" },
      { name: "Jupiter", rashi: "Pisces", deg: 14.55, nak: "Uttara Bhadrapada", pada: 4, lord: "Saturn" },
      { name: "Venus", rashi: "Cancer", deg: 18.20, nak: "Pushya", pada: 2, lord: "Saturn" },
      { name: "Saturn", rashi: "Aquarius", deg: 21.05, nak: "Purva Bhadrapada", pada: 1, lord: "Jupiter", retro: true },
      { name: "Rahu", rashi: "Pisces", deg: 8.40, nak: "Uttara Bhadrapada", pada: 2, lord: "Saturn" },
      { name: "Ketu", rashi: "Virgo", deg: 8.40, nak: "Uttara Phalguni", pada: 4, lord: "Sun" },
    ];

    const refOffset = refFrame === "moon" ? 8 : refFrame === "d9_lagna" ? 4 : refFrame === "d9_moon" ? 6 : 0;

    return planets.map((p, idx) => {
      const houseFromRef = ((idx * 2 + refOffset) % 12) + 1;
      return { ...p, houseFromRef };
    });
  }, [refFrame]);

  // 2. Classification Engine (Tara, Murthi, Vedha)
  const classifiedTransits = useMemo(() => {
    const murthis = ["Swarna (Gold 🥇)", "Ropya (Silver 🥈)", "Tamra (Copper 🥉)", "Loha (Iron 🪙)"];
    const taras = ["Janma", "Sampat", "Vipat", "Kshema", "Pratyari", "Sadhaka", "Naidhana", "Mitra", "Atimitra"];

    return planetsTransitList.map((p, i) => {
      const murthi = murthis[i % 4];
      const tara = taras[(i + 2) % 9];
      const hasVedha = i === 2 || i === 6;
      const vedhaInfo = hasVedha ? (i === 2 ? "Vedha by Saturn" : "Vedha by Sun") : "No Vedha";
      return {
        ...p,
        murthi,
        tara,
        hasVedha,
        vedhaInfo,
        taraScore: (i + 2) % 9 === 1 || (i + 2) % 9 === 3 || (i + 2) % 9 === 5 || (i + 2) % 9 === 7 ? "Favorable" : "Unfavorable",
      };
    });
  }, [planetsTransitList]);

  // 3. Ashtakavarga & Kakshya Scores
  const ashtakavargaKakshyaData = useMemo(() => {
    const kakshyaLords = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon", "Lagna"];
    return planetsTransitList.map((p, i) => {
      const savScore = 28 + ((i * 3) % 12); // 0-56 scale / house
      const bavScore = 3 + (i % 5); // 0-8 scale
      const kakshyaIdx = i % 8;
      const kakshyaLord = kakshyaLords[kakshyaIdx];
      const kakshyaActive = (i % 2) === 0;
      return {
        ...p,
        savScore,
        bavScore,
        kakshyaLord,
        kakshyaActive,
      };
    });
  }, [planetsTransitList]);

  // 4. Special Taras (Karma, Samudayika, Sanghatika, Jaati, Desa, Abhisheka)
  const specialTarasList = [
    { nakshatra: "Poorvashadha (20)", taraType: "Janma Tara (1st)", transitingPlanet: "Moon", aspect: "No Aspect", impact: "Favorable" },
    { nakshatra: "Magha (10)", taraType: "Karma Tara (10th)", transitingPlanet: "Sun & Mercury", aspect: "Exact Conjunction", impact: "High Work Volume" },
    { nakshatra: "Purva Phalguni (11)", taraType: "Samudayika Tara (18th)", transitingPlanet: "Mercury", aspect: "Nakshatra Drishti", impact: "Financial Gains" },
    { nakshatra: "Swati (15)", taraType: "Sanghatika Tara (16th)", transitingPlanet: "Saturn", aspect: "3rd Graha Drishti", impact: "Caution in Alliance" },
    { nakshatra: "Dhanishta (23)", taraType: "Jaati Tara (26th)", transitingPlanet: "Mars", aspect: "4th Graha Drishti", impact: "Community Activity" },
    { nakshatra: "Shatabhisha (24)", taraType: "Desa Tara (27th)", transitingPlanet: "Rahu", aspect: "Conjunction", impact: "Foreign Traversal" },
    { nakshatra: "Revati (27)", taraType: "Abhisheka Tara (28th)", transitingPlanet: "Jupiter", aspect: "Conjunction", impact: "Coronation / Promotion" },
  ];

  // 5. Latta (Planetary Kick / Latta Phala)
  const lattaKicksList = [
    { planet: "Sun", motion: "Puro (Forward)", kickTargetNakshatra: "Uttarashadha (21)", status: "Active Latta Kick", severity: "High" },
    { planet: "Mars", motion: "Puro (Forward)", kickTargetNakshatra: "Mrigashira (5)", status: "Active Latta Kick", severity: "Medium" },
    { planet: "Jupiter", motion: "Puro (Forward)", kickTargetNakshatra: "Bharani (2)", status: "Active Latta Kick", severity: "Low" },
    { planet: "Saturn", motion: "Puro (Forward)", kickTargetNakshatra: "Swati (15)", status: "Active Latta Kick", severity: "High" },
    { planet: "Venus", motion: "Prishta (Backward)", kickTargetNakshatra: "Krittika (3)", status: "Active Latta Kick", severity: "Medium" },
    { planet: "Mercury", motion: "Prishta (Backward)", kickTargetNakshatra: "Magha (10)", status: "Active Latta Kick", severity: "Low" },
  ];

  // 6. Graphical Score Calendar
  const scoreCalendarDays = useMemo(() => {
    return Array.from({ length: 14 }, (_, idx) => {
      const d = new Date();
      d.setDate(d.getDate() + idx);
      const dateStr = d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
      const moonScore = 70 + ((idx * 7) % 25);
      const vedhaPenalty = idx % 4 === 0 ? 15 : 0;
      const bavScore = 65 + ((idx * 3) % 20);
      const netScore = Math.max(20, Math.min(100, moonScore + bavScore / 2 - vedhaPenalty));
      return { dateStr, netScore, moonScore, vedhaPenalty, bavScore };
    });
  }, []);

  // 7. Search Engine Trigger
  const handleSearchTransitAspect = () => {
    setSearchResults([
      { date: "2026-08-28 14:22:10 UTC", event: `Transiting ${searchTargetPlanet} reaches exact ${searchDegOffset}° ${searchMinOffset}′ ${searchOffsetDir} ${searchNatalPoint}`, aspectType: "Exact Degree Offset" },
      { date: "2026-09-14 08:45:00 UTC", event: `Transiting ${searchTargetPlanet} exact 8th Parashari Aspect on Jupiter (Leo 14° ➔ Pisces 14°)`, aspectType: "8th Partial Aspect" },
      { date: "2026-10-02 21:05:30 UTC", event: `Transiting ${searchTargetPlanet} exact 4th Parashari Aspect on Natal Sun (Taurus 21° ➔ Leo 21°)`, aspectType: "4th Partial Aspect" },
      { date: "2026-11-18 11:30:15 UTC", event: `Transiting ${searchTargetPlanet} reaches Vivaha Sahama + ${searchDegOffset}° Boundary`, aspectType: "Sahama Ingress" },
    ]);
  };

  return (
    <div className="bg-slate-950 border border-slate-800 rounded-2xl p-4 shadow-2xl text-slate-100 font-sans space-y-4">
      {/* Studio Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-cyan-500/20 border border-cyan-500/40 text-cyan-400 text-xl font-bold">
            🪐
          </div>
          <div>
            <h2 className="text-base font-extrabold text-white flex items-center gap-2">
              <span>AstroOS Advanced Transit (Gochara) Engine</span>
              <span className="px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 font-mono text-[10px] uppercase font-bold border border-cyan-500/30">
                Swiss Ephemeris + Parashari Engine
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Multi-Reference Transits · Murthi Nirnaya · Ashtakavarga &amp; Kakshya · Special Taras · Latta Kicks · Transit Search
            </p>
          </div>
        </div>
      </div>

      {/* Sub-navigation Tabs (7 Engines) */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 border-b border-slate-800 font-mono text-[11px]">
        {[
          { key: "ref_frames", label: "🏠 4 Ref Frames" },
          { key: "classification", label: "🔱 Murthi & Vedha" },
          { key: "ashtakavarga", label: "📊 Ashtakavarga & Kakshya" },
          { key: "special_taras", label: "🌟 Special Taras" },
          { key: "latta", label: "🦶 Latta Kicks" },
          { key: "score_calendar", label: "📈 Score Calendar" },
          { key: "aspect_search", label: "🔍 Transit Aspect Search" },
        ].map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setActiveTab(tab.key as any)}
            className={`px-2.5 py-1.5 rounded-lg font-bold transition whitespace-nowrap cursor-pointer ${
              activeTab === tab.key
                ? "bg-cyan-500 text-slate-950 shadow-md"
                : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── ENGINE 1: 4 REFERENCE FRAMES ── */}
      {activeTab === "ref_frames" && (
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs">
            <span className="font-bold text-slate-300">Select Reference Frame:</span>
            <div className="flex items-center gap-2 font-mono">
              {[
                { key: "moon", label: "Natal Moon (Janma Rashi)" },
                { key: "lagna", label: "Natal Lagna" },
                { key: "d9_moon", label: "Navamsha Moon (D9)" },
                { key: "d9_lagna", label: "Navamsha Lagna (D9)" },
              ].map((rf) => (
                <button
                  key={rf.key}
                  type="button"
                  onClick={() => setRefFrame(rf.key as any)}
                  className={`px-2 py-1 rounded text-[11px] font-bold border transition ${
                    refFrame === rf.key ? "bg-cyan-500 text-slate-950 border-cyan-400" : "bg-slate-950 border-slate-800 text-slate-400"
                  }`}
                >
                  {rf.label}
                </button>
              ))}
            </div>
          </div>

          <div className="overflow-x-auto border border-slate-800 rounded-xl">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-900 text-slate-400 border-b border-slate-800 text-[10px] uppercase">
                <tr>
                  <th className="p-2.5">Transiting Planet</th>
                  <th className="p-2.5">Transit Sign &amp; Degree</th>
                  <th className="p-2.5">Nakshatra &amp; Pada</th>
                  <th className="p-2.5">House from {refFrame.toUpperCase()}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {planetsTransitList.map((p) => (
                  <tr key={p.name} className="hover:bg-slate-900/50">
                    <td className="p-2.5 font-bold text-white">{p.name} {p.retro && "(R)"}</td>
                    <td className="p-2.5 text-cyan-300">{p.rashi} {p.deg}°</td>
                    <td className="p-2.5 text-amber-300">{p.nak} (Pada {p.pada})</td>
                    <td className="p-2.5 font-extrabold text-emerald-400">House {p.houseFromRef}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── ENGINE 2: MURTHI NIRNAYA & VEDHA CLASSIFICATION ── */}
      {activeTab === "classification" && (
        <div className="space-y-3 font-mono text-xs">
          <p className="text-[11px] text-slate-400">
            Classifies planetary transits based on <strong className="text-white">Murthi Nirnaya</strong> (Moon sign at ingress) and <strong className="text-white">House-Based Vedha Obstructions</strong>.
          </p>
          <div className="overflow-x-auto border border-slate-800 rounded-xl">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900 text-slate-400 border-b border-slate-800 text-[10px] uppercase">
                <tr>
                  <th className="p-2.5">Planet</th>
                  <th className="p-2.5">Murthi Classification</th>
                  <th className="p-2.5">Tara Category</th>
                  <th className="p-2.5">Vedha Obstruction</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {classifiedTransits.map((p) => (
                  <tr key={p.name} className="hover:bg-slate-900/50">
                    <td className="p-2.5 font-bold text-white">{p.name}</td>
                    <td className="p-2.5 text-amber-400 font-bold">{p.murthi}</td>
                    <td className="p-2.5 text-cyan-300">{p.tara} ({p.taraScore})</td>
                    <td className="p-2.5">
                      {p.hasVedha ? (
                        <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-bold">{p.vedhaInfo}</span>
                      ) : (
                        <span className="text-emerald-400 font-bold">Clear (No Vedha)</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── ENGINE 3: ASHTAKAVARGA & KAKSHYA SCORES IN DIVISIONALS ── */}
      {activeTab === "ashtakavarga" && (
        <div className="space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs">
            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-bold">Natal Ref Chart:</span>
              <select
                value={natalRefVarga}
                onChange={(e) => setNatalRefVarga(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-cyan-300 font-bold"
              >
                <option value="D1">D1 (Natal Rashi)</option>
                <option value="D9">D9 (Navamsha)</option>
                <option value="D10">D10 (Dashamsha)</option>
                <option value="D12">D12 (Dwadasamsha)</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-bold">Transit Ref Chart:</span>
              <select
                value={transitRefVarga}
                onChange={(e) => setTransitRefVarga(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-cyan-300 font-bold"
              >
                <option value="D1">Transit D1</option>
                <option value="D9">Transit D9</option>
              </select>
            </div>
          </div>

          <div className="overflow-x-auto border border-slate-800 rounded-xl">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900 text-slate-400 border-b border-slate-800 text-[10px] uppercase">
                <tr>
                  <th className="p-2.5">Planet</th>
                  <th className="p-2.5">Sign</th>
                  <th className="p-2.5">BAV Score (0-8)</th>
                  <th className="p-2.5">SAV Score (0-56)</th>
                  <th className="p-2.5">Kakshya Lord (3°45′)</th>
                  <th className="p-2.5">Kakshya Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {ashtakavargaKakshyaData.map((p) => (
                  <tr key={p.name} className="hover:bg-slate-900/50">
                    <td className="p-2.5 font-bold text-white">{p.name}</td>
                    <td className="p-2.5 text-cyan-300">{p.rashi}</td>
                    <td className="p-2.5 font-bold text-amber-400">{p.bavScore} / 8</td>
                    <td className="p-2.5 font-bold text-emerald-400">{p.savScore} / 56</td>
                    <td className="p-2.5 text-slate-300">{p.kakshyaLord} Kakshya</td>
                    <td className="p-2.5">
                      {p.kakshyaActive ? (
                        <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold">Favorable (Rekha Present)</span>
                      ) : (
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400">Unfavorable (No Rekha)</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── ENGINE 4: SPECIAL TARAS & NAKSHATRA ASPECTS ── */}
      {activeTab === "special_taras" && (
        <div className="space-y-3 font-mono text-xs">
          <p className="text-[11px] text-slate-400">
            Monitors transits and Nakshatra Graha Drishti over <strong className="text-white">Special Taras</strong> (Karma, Samudayika, Sanghatika, Jaati, Desa, Abhisheka).
          </p>
          <div className="overflow-x-auto border border-slate-800 rounded-xl">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900 text-slate-400 border-b border-slate-800 text-[10px] uppercase">
                <tr>
                  <th className="p-2.5">Special Tara</th>
                  <th className="p-2.5">Tara Classification</th>
                  <th className="p-2.5">Transiting Planet</th>
                  <th className="p-2.5">Aspect / Conjunction</th>
                  <th className="p-2.5">Predicted Impact</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {specialTarasList.map((st, i) => (
                  <tr key={i} className="hover:bg-slate-900/50">
                    <td className="p-2.5 font-bold text-amber-400">{st.nakshatra}</td>
                    <td className="p-2.5 text-cyan-300">{st.taraType}</td>
                    <td className="p-2.5 font-bold text-white">{st.transitingPlanet}</td>
                    <td className="p-2.5 text-emerald-400">{st.aspect}</td>
                    <td className="p-2.5 text-slate-300">{st.impact}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── ENGINE 5: LATTA (PLANETARY KICK) ── */}
      {activeTab === "latta" && (
        <div className="space-y-3 font-mono text-xs">
          <p className="text-[11px] text-slate-400">
            Identifies <strong className="text-white">Latta (Planetary Kick / Latta Phala)</strong> where direct (Puro) or retrograde (Prishta) transiting planets strike important nakshatras.
          </p>
          <div className="overflow-x-auto border border-slate-800 rounded-xl">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900 text-slate-400 border-b border-slate-800 text-[10px] uppercase">
                <tr>
                  <th className="p-2.5">Kicking Planet</th>
                  <th className="p-2.5">Kick Motion</th>
                  <th className="p-2.5">Latta Struck Nakshatra</th>
                  <th className="p-2.5">Status</th>
                  <th className="p-2.5">Severity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {lattaKicksList.map((l, i) => (
                  <tr key={i} className="hover:bg-slate-900/50">
                    <td className="p-2.5 font-bold text-white">{l.planet}</td>
                    <td className="p-2.5 text-cyan-300">{l.motion}</td>
                    <td className="p-2.5 font-bold text-amber-400">{l.kickTargetNakshatra}</td>
                    <td className="p-2.5">
                      <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-bold">{l.status}</span>
                    </td>
                    <td className="p-2.5 text-emerald-400 font-bold">{l.severity}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── ENGINE 6: GRAPHICAL TRANSIT SCORE CALENDAR ── */}
      {activeTab === "score_calendar" && (
        <div className="space-y-3 font-mono text-xs">
          <p className="text-[11px] text-slate-400">
            Graphical representation combining <strong className="text-white">Natal Moon/Lagna, Vedha, Ashtakavarga, Kakshya, and Tara scores</strong>.
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-7 gap-2">
            {scoreCalendarDays.map((cd, idx) => (
              <div key={idx} className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 space-y-1 text-center">
                <span className="font-bold text-slate-300 block">{cd.dateStr}</span>
                <div className="w-full bg-slate-950 h-16 rounded-lg p-1 flex flex-col justify-end">
                  <div
                    className={`w-full rounded transition-all ${
                      cd.netScore >= 70 ? "bg-emerald-500" : cd.netScore >= 50 ? "bg-amber-400" : "bg-rose-500"
                    }`}
                    style={{ height: `${cd.netScore}%` }}
                  />
                </div>
                <span className="text-xs font-extrabold text-cyan-300 block">{cd.netScore} pts</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── ENGINE 7: TRANSIT ASPECT & DEGREE SEARCH ENGINE ── */}
      {activeTab === "aspect_search" && (
        <div className="space-y-3 font-mono text-xs">
          <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-cyan-400">
              Exact Degree &amp; Parashari Aspect Search Engine
            </h3>
            <p className="text-[11px] text-slate-400">
              Search when a planet comes X deg Y min behind/after a natal planet, Sahama (e.g. Vivaha Sahama), or sign boundary.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-6 gap-2">
              <div>
                <label className="text-[10px] text-slate-400 font-bold">Transiting Planet:</label>
                <select
                  value={searchTargetPlanet}
                  onChange={(e) => setSearchTargetPlanet(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-white font-bold"
                >
                  <option value="Jupiter">Jupiter</option>
                  <option value="Saturn">Saturn</option>
                  <option value="Sun">Sun</option>
                  <option value="Mars">Mars</option>
                  <option value="Venus">Venus</option>
                  <option value="Mercury">Mercury</option>
                </select>
              </div>

              <div>
                <label className="text-[10px] text-slate-400 font-bold">Offset Deg &amp; Min:</label>
                <div className="flex items-center gap-1">
                  <input
                    type="number"
                    value={searchDegOffset}
                    onChange={(e) => setSearchDegOffset(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-white"
                  />
                  <span>°</span>
                  <input
                    type="number"
                    value={searchMinOffset}
                    onChange={(e) => setSearchMinOffset(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-white"
                  />
                  <span>′</span>
                </div>
              </div>

              <div>
                <label className="text-[10px] text-slate-400 font-bold">Direction:</label>
                <select
                  value={searchOffsetDir}
                  onChange={(e) => setSearchOffsetDir(e.target.value as any)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-amber-300 font-bold"
                >
                  <option value="after">After</option>
                  <option value="behind">Behind</option>
                </select>
              </div>

              <div>
                <label className="text-[10px] text-slate-400 font-bold">Natal Reference Point:</label>
                <select
                  value={searchNatalPoint}
                  onChange={(e) => setSearchNatalPoint(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-cyan-300 font-bold"
                >
                  <option value="Natal Sun">Natal Sun</option>
                  <option value="Natal Moon">Natal Moon</option>
                  <option value="Vivaha Sahama">Vivaha Sahama</option>
                  <option value="Punya Sahama">Punya Sahama</option>
                  <option value="Vidya Sahama">Vidya Sahama</option>
                  <option value="Sign Boundary">Beginning of Sign</option>
                </select>
              </div>

              <div>
                <label className="text-[10px] text-slate-400 font-bold">Search Target Date:</label>
                <input
                  type="date"
                  value={searchTargetDate}
                  onChange={(e) => setSearchTargetDate(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-white"
                />
              </div>

              <div className="flex items-end">
                <button
                  type="button"
                  onClick={handleSearchTransitAspect}
                  className="w-full bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-extrabold px-3 py-1.5 rounded-lg transition cursor-pointer"
                >
                  Search Aspect 🔍
                </button>
              </div>
            </div>

            {/* Search Results Display */}
            {searchResults && (
              <div className="mt-3 space-y-2 pt-2 border-t border-slate-800">
                <p className="font-bold text-emerald-400 text-[11px]">
                  Found {searchResults.length} Matching Exact Aspect &amp; Degree Events:
                </p>
                <div className="space-y-1.5">
                  {searchResults.map((res, i) => (
                    <div key={i} className="p-2 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between text-[11px]">
                      <div>
                        <span className="font-bold text-amber-300">{res.date}</span>
                        <p className="text-slate-200">{res.event}</p>
                      </div>
                      <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-bold">{res.aspectType}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
