"use client";

import React, { useState } from "react";

export function NakshatraArchitectureBanner() {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="mb-6 rounded-2xl border border-cyan-500/30 bg-slate-950/90 p-4 shadow-2xl backdrop-blur-md text-slate-100 font-sans">
      {/* Banner Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-cyan-500/20 border border-cyan-500/40 text-cyan-400 text-lg font-bold">
            🌌
          </div>
          <div>
            <h2 className="text-base font-extrabold text-white flex items-center gap-2">
              <span>AstroOS Nakshatra Core Engine</span>
              <span className="px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 font-mono text-[10px] uppercase font-bold border border-cyan-500/30">
                Swiss Ephemeris Pipeline
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Central Computational Hub for 27 Nakshatras, 108 Padas, 9 Taras, Navamsha Mappings &amp; Special Rules
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setIsExpanded((prev) => !prev)}
          className="px-3 py-1 rounded-lg border border-slate-700 bg-slate-900 text-xs font-bold text-slate-300 hover:bg-slate-800 transition cursor-pointer"
        >
          {isExpanded ? "Hide Architecture Flow ▴" : "View Architecture Flow ▾"}
        </button>
      </div>

      {/* Expanded Architectural Engine Grid */}
      {isExpanded && (
        <div className="mt-4 space-y-4">
          {/* Top Ephemeris Data Bar */}
          <div className="flex items-center justify-between p-2.5 rounded-xl bg-cyan-950/40 border border-cyan-500/30 text-xs font-mono text-cyan-300">
            <div className="flex items-center gap-2">
              <span>🪐</span>
              <span className="font-bold">SWISS EPHEMERIS / ASTRONOMICAL INPUTS:</span>
              <span className="text-slate-300">Planetary Longitudes · Speeds · Retrogrades · Fixed Stars · Constellations</span>
            </div>
            <span className="text-[10px] text-cyan-400 uppercase font-bold">Precision &lt; 0.001″</span>
          </div>

          {/* 9 Core Computational Engines Grid */}
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2">
              Core Calculation Modules (9 Engines)
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-9 gap-2">
              {/* Engine 1 */}
              <div className="p-2 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-[10px] font-bold text-cyan-400 block">1. Position</span>
                <p className="text-[10px] text-slate-400 mt-0.5 leading-tight">
                  Longitude ➔ Rashi ➔ Nakshatra ➔ Pada (3°20′)
                </p>
              </div>

              {/* Engine 2 */}
              <div className="p-2 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-[10px] font-bold text-cyan-400 block">2. Structure</span>
                <p className="text-[10px] text-slate-400 mt-0.5 leading-tight">
                  27 Nakshatras, 108 Padas, Navamsha Lords
                </p>
              </div>

              {/* Engine 3 */}
              <div className="p-2 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-[10px] font-bold text-cyan-400 block">3. Relation</span>
                <p className="text-[10px] text-slate-400 mt-0.5 leading-tight">
                  9 Tara Balas (Janma ➔ Atimitra)
                </p>
              </div>

              {/* Engine 4 */}
              <div className="p-2 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-[10px] font-bold text-cyan-400 block">4. Lords &amp; Dasha</span>
                <p className="text-[10px] text-slate-400 mt-0.5 leading-tight">
                  Vimshottari Sequence &amp; Dasha Lords
                </p>
              </div>

              {/* Engine 5 */}
              <div className="p-2 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-[10px] font-bold text-cyan-400 block">5. Special Rules</span>
                <p className="text-[10px] text-slate-400 mt-0.5 leading-tight">
                  Gandanta, Tripadi, Deva/Yama
                </p>
              </div>

              {/* Engine 6 */}
              <div className="p-2 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-[10px] font-bold text-cyan-400 block">6. Namakshara</span>
                <p className="text-[10px] text-slate-400 mt-0.5 leading-tight">
                  Sound Syllables &amp; Avakahada Chakra
                </p>
              </div>

              {/* Engine 7 */}
              <div className="p-2 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-[10px] font-bold text-cyan-400 block">7. Context</span>
                <p className="text-[10px] text-slate-400 mt-0.5 leading-tight">
                  Lagna &amp; Moon Nakshatra Bhava Lords
                </p>
              </div>

              {/* Engine 8 */}
              <div className="p-2 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-[10px] font-bold text-cyan-400 block">8. Transit</span>
                <p className="text-[10px] text-slate-400 mt-0.5 leading-tight">
                  Live Gochara over Janma Nakshatra
                </p>
              </div>

              {/* Engine 9 */}
              <div className="p-2 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-[10px] font-bold text-cyan-400 block">9. Muhurta</span>
                <p className="text-[10px] text-slate-400 mt-0.5 leading-tight">
                  Tara Bala Check &amp; Timing Suitability
                </p>
              </div>
            </div>
          </div>

          {/* Key Calculation Flow Pipeline */}
          <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1.5 font-mono text-[11px]">
            <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400 block">
              ⚡ Key Calculation Pipeline Flow Example:
            </span>
            <div className="flex flex-wrap items-center gap-1.5 text-slate-200">
              <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-bold">Planet 14°40′ Cancer</span>
              <span className="text-slate-500">➔</span>
              <span className="px-2 py-0.5 rounded bg-slate-800 text-cyan-300 font-bold">Rashi: Cancer</span>
              <span className="text-slate-500">➔</span>
              <span className="px-2 py-0.5 rounded bg-slate-800 text-cyan-300 font-bold">Nakshatra: Pushya</span>
              <span className="text-slate-500">➔</span>
              <span className="px-2 py-0.5 rounded bg-slate-800 text-amber-300 font-bold">Pada: 4</span>
              <span className="text-slate-500">➔</span>
              <span className="px-2 py-0.5 rounded bg-slate-800 text-amber-300 font-bold">Lord: Saturn</span>
              <span className="text-slate-500">➔</span>
              <span className="px-2 py-0.5 rounded bg-slate-800 text-emerald-300 font-bold">Navamsha: Virgo</span>
              <span className="text-slate-500">➔</span>
              <span className="px-2 py-0.5 rounded bg-slate-800 text-emerald-300 font-bold">Nav Lord: Mercury</span>
              <span className="text-slate-500">➔</span>
              <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-bold">Bhava: 10th</span>
              <span className="text-slate-500">➔</span>
              <span className="px-2 py-0.5 rounded bg-cyan-500 text-slate-950 font-extrabold">Final Synthesis</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
