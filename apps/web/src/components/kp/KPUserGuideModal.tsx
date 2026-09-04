"use client";

import { useState } from "react";

interface Props {
  onClose: () => void;
}

type GuideTab = "quick_start" | "4_step_method" | "house_combinations" | "tab_walkthrough" | "ruling_planets";

export function KPUserGuideModal({ onClose }: Props) {
  const [activeTab, setActiveTab] = useState<GuideTab>("quick_start");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div
        className="relative w-full max-w-4xl max-h-[90vh] flex flex-col rounded-2xl border border-slate-700/80 bg-slate-900 text-slate-100 shadow-2xl overflow-hidden"
        style={{ borderColor: "var(--border-primary, #334155)" }}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/50">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-500/20 border border-amber-500/40 text-amber-400 font-bold text-base">
              📖
            </div>
            <div>
              <h3 className="text-base font-extrabold tracking-tight text-slate-100">
                KP Astrology Interpretation &amp; User Manual
              </h3>
              <p className="text-xs text-slate-400 font-medium">
                Krishnamurti Paddhati (KP System) — Rules, Cuspal Sub Lords, and Event Timing
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-all cursor-pointer font-bold text-sm"
          >
            ✕
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 px-6 py-2.5 border-b border-slate-800 bg-slate-900/60 overflow-x-auto text-xs font-bold">
          <button
            type="button"
            onClick={() => setActiveTab("quick_start")}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer whitespace-nowrap ${
              activeTab === "quick_start"
                ? "bg-amber-500 text-slate-950 shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            }`}
          >
            🌟 KP Golden Rule
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("4_step_method")}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer whitespace-nowrap ${
              activeTab === "4_step_method"
                ? "bg-amber-500 text-slate-950 shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            }`}
          >
            🎯 4-Step Analysis Method
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("house_combinations")}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer whitespace-nowrap ${
              activeTab === "house_combinations"
                ? "bg-amber-500 text-slate-950 shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            }`}
          >
            📋 Event House Combinations
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("ruling_planets")}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer whitespace-nowrap ${
              activeTab === "ruling_planets"
                ? "bg-amber-500 text-slate-950 shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            }`}
          >
            ⚡ Ruling Planets (RP)
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("tab_walkthrough")}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer whitespace-nowrap ${
              activeTab === "tab_walkthrough"
                ? "bg-amber-500 text-slate-950 shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            }`}
          >
            🎛️ Workspace Tabs Guide
          </button>
        </div>

        {/* Modal Body Content */}
        <div className="flex-1 p-6 overflow-y-auto space-y-6 text-xs text-slate-300 leading-relaxed">
          {/* TAB 1: QUICK START & GOLDEN RULE */}
          {activeTab === "quick_start" && (
            <div className="space-y-4 animate-in fade-in duration-150">
              <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-950/20 text-amber-200">
                <h4 className="text-sm font-bold text-amber-300 flex items-center gap-2">
                  <span>✨</span> The Golden Trio of KP Astrology
                </h4>
                <p className="mt-2 text-xs leading-relaxed text-slate-200">
                  In classical KP system founded by Prof. K.S. Krishnamurti, three levels govern every prediction:
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-3">
                  <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 text-center">
                    <span className="text-[10px] font-extrabold uppercase text-amber-400 block">1. Planet (Graha)</span>
                    <strong className="text-slate-100 text-xs block mt-1">The Source / Actor</strong>
                    <span className="text-[11px] text-slate-400 block mt-0.5">Represents who acts and initiates the energy.</span>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 text-center">
                    <span className="text-[10px] font-extrabold uppercase text-cyan-400 block">2. Star Lord (Nakshatra)</span>
                    <strong className="text-slate-100 text-xs block mt-1">The Result / Houses</strong>
                    <span className="text-[11px] text-slate-400 block mt-0.5">Dictates which houses and matters will manifest.</span>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 text-center">
                    <span className="text-[10px] font-extrabold uppercase text-emerald-400 block">3. Sub Lord (CSL)</span>
                    <strong className="text-slate-100 text-xs block mt-1">The Final Decision (YES / NO)</strong>
                    <span className="text-[11px] text-slate-400 block mt-0.5">Decides whether the event fructifies or gets vetoed.</span>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="text-sm font-bold text-slate-100">Why KP is so precise:</h4>
                <ul className="list-disc pl-5 space-y-2 text-slate-300">
                  <li>
                    <strong>Placidus Unequal Cusps (Bhava Chalit)</strong>: Unlike Whole Sign where all houses are 30°, KP uses astronomical degree cusps. A planet might be in 1st sign in Rashi, but placed in 12th house cuspal bhava.
                  </li>
                  <li>
                    <strong>Sub-Division of Nakshatras</strong>: Each of the 27 Nakshatras (13°20&apos;) is further divided into 9 unequal Sub-Lords proportional to Vimshottari Dasha years (from 40&apos; to 2°13&apos;20&quot;).
                  </li>
                  <li>
                    <strong>Deterministic Yes/No</strong>: Instead of subjective intuition, KP relies on whether the Cuspal Sub Lord (CSL) connects with favorable houses or their 12th negating houses.
                  </li>
                </ul>
              </div>
            </div>
          )}

          {/* TAB 2: 4-STEP METHOD */}
          {activeTab === "4_step_method" && (
            <div className="space-y-4 animate-in fade-in duration-150">
              <h4 className="text-sm font-bold text-slate-100">
                How an Astrologer or Researcher reads any event in KP:
              </h4>

              <div className="space-y-3">
                <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/80">
                  <div className="flex items-center gap-2 text-amber-400 font-bold text-xs">
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-amber-500/20 text-amber-300 text-[10px]">1</span>
                    Step 1: Check the Cuspal Sub Lord (CSL) for the Event Promise
                  </div>
                  <p className="mt-1.5 text-slate-300">
                    Find the primary house cusp for the question (e.g., <strong>7th Cusp for Marriage</strong>, <strong>10th Cusp for Career/Promotion</strong>). Look at its <strong>Sub Lord (CSL)</strong>.
                    Does the Star Lord of this CSL signify the supporting houses? If yes, the event is <strong>Promised in the birth chart</strong>.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/80">
                  <div className="flex items-center gap-2 text-cyan-400 font-bold text-xs">
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-cyan-500/20 text-cyan-300 text-[10px]">2</span>
                    Step 2: Inspect 4-Tier Significator Matrix (Grades A &gt; B &gt; C &gt; D)
                  </div>
                  <p className="mt-1.5 text-slate-300">
                    Check which planets have the highest potency to deliver the house results:
                  </p>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-2 font-medium text-[11px]">
                    <div className="p-2 rounded bg-slate-950 border border-slate-800">
                      <strong className="text-emerald-400 block">Grade A (Strongest)</strong>
                      Planet in the star of an occupant.
                    </div>
                    <div className="p-2 rounded bg-slate-950 border border-slate-800">
                      <strong className="text-cyan-400 block">Grade B</strong>
                      Planet occupying the house directly.
                    </div>
                    <div className="p-2 rounded bg-slate-950 border border-slate-800">
                      <strong className="text-indigo-400 block">Grade C</strong>
                      Planet in the star of the sign lord.
                    </div>
                    <div className="p-2 rounded bg-slate-950 border border-slate-800">
                      <strong className="text-slate-400 block">Grade D</strong>
                      The Sign Lord of the house itself.
                    </div>
                  </div>
                </div>

                <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/80">
                  <div className="flex items-center gap-2 text-rose-400 font-bold text-xs">
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-rose-500/20 text-rose-300 text-[10px]">3</span>
                    Step 3: Check Sub Lord Veto (Negation / Dusthana Check)
                  </div>
                  <p className="mt-1.5 text-slate-300">
                    Every house has a negation house (12th from it). For example:
                    <br />• <strong>Marriage (7th)</strong> is negated by the <strong>6th house</strong> (12th from 7th).
                    <br />• <strong>Gains (11th)</strong> is negated by the <strong>10th house</strong> (12th from 11th).
                    <br />If the Sub Lord heavily signifies the negating houses, it causes delays, obstacles, or outright denial.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/80">
                  <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs">
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-300 text-[10px]">4</span>
                    Step 4: Pinpoint Timing (Dasha + Transit + Ruling Planets)
                  </div>
                  <p className="mt-1.5 text-slate-300">
                    When the promise is confirmed:
                    <br />• <strong>Dasha</strong>: Look for Mahadasha / Antardasha / Pratyantardasha (DBA) whose lords are strong Grade A/B significators.
                    <br />• <strong>Transit (Gochar)</strong>: Sun, Jupiter, or Saturn must transit the Star or Sub of the event significators.
                    <br />• <strong>Ruling Planets (RP)</strong>: The moment of fructification will always match the Ruling Planets of the natal chart.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: HOUSE COMBINATIONS CHEAT SHEET */}
          {activeTab === "house_combinations" && (
            <div className="space-y-4 animate-in fade-in duration-150">
              <h4 className="text-sm font-bold text-slate-100">
                Classical KP House Groupings for Major Life Events:
              </h4>

              <div className="border border-slate-800 rounded-xl overflow-hidden">
                <table className="w-full text-left text-[11px]">
                  <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] font-bold border-b border-slate-800">
                    <tr>
                      <th className="p-2.5">Life Event</th>
                      <th className="p-2.5">Primary Cusp</th>
                      <th className="p-2.5 text-emerald-400">Favorable Houses (Support)</th>
                      <th className="p-2.5 text-rose-400">Adverse / Negating Houses</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 bg-slate-900/40">
                    <tr>
                      <td className="p-2.5 font-bold text-slate-100">💍 Marriage / Partnership</td>
                      <td className="p-2.5">7th Cusp</td>
                      <td className="p-2.5 font-semibold text-emerald-400">2, 7, 11</td>
                      <td className="p-2.5 text-rose-400">1, 6, 10 (Separation / Delay)</td>
                    </tr>
                    <tr>
                      <td className="p-2.5 font-bold text-slate-100">💼 Job, Employment &amp; Career</td>
                      <td className="p-2.5">6th &amp; 10th Cusps</td>
                      <td className="p-2.5 font-semibold text-emerald-400">2, 6, 10, 11</td>
                      <td className="p-2.5 text-rose-400">5, 9, 12 (Job loss / Resignation)</td>
                    </tr>
                    <tr>
                      <td className="p-2.5 font-bold text-slate-100">✈️ Foreign Travel &amp; Settlement</td>
                      <td className="p-2.5">12th Cusp</td>
                      <td className="p-2.5 font-semibold text-emerald-400">3, 9, 12</td>
                      <td className="p-2.5 text-rose-400">4 (Stay in birthplace)</td>
                    </tr>
                    <tr>
                      <td className="p-2.5 font-bold text-slate-100">💰 Wealth &amp; Financial Windfall</td>
                      <td className="p-2.5">2nd &amp; 11th Cusps</td>
                      <td className="p-2.5 font-semibold text-emerald-400">2, 6, 11</td>
                      <td className="p-2.5 text-rose-400">5, 8, 12 (Loss / Expenditure)</td>
                    </tr>
                    <tr>
                      <td className="p-2.5 font-bold text-slate-100">👶 Childbirth (Progeny)</td>
                      <td className="p-2.5">5th Cusp</td>
                      <td className="p-2.5 font-semibold text-emerald-400">2, 5, 11</td>
                      <td className="p-2.5 text-rose-400">1, 4, 10 (Complications / Denial)</td>
                    </tr>
                    <tr>
                      <td className="p-2.5 font-bold text-slate-100">🏠 Property &amp; Vehicle Purchase</td>
                      <td className="p-2.5">4th Cusp</td>
                      <td className="p-2.5 font-semibold text-emerald-400">4, 11, 12</td>
                      <td className="p-2.5 text-rose-400">3, 10 (Sale / Loss of property)</td>
                    </tr>
                    <tr>
                      <td className="p-2.5 font-bold text-slate-100">🩺 Health Recovery &amp; Longevity</td>
                      <td className="p-2.5">1st &amp; 11th Cusps</td>
                      <td className="p-2.5 font-semibold text-emerald-400">1, 5, 11</td>
                      <td className="p-2.5 text-rose-400">6, 8, 12 (Disease / Surgery)</td>
                    </tr>
                    <tr>
                      <td className="p-2.5 font-bold text-slate-100">⚖️ Litigation / Court Case Victory</td>
                      <td className="p-2.5">6th Cusp</td>
                      <td className="p-2.5 font-semibold text-emerald-400">6, 11 (Win for Native)</td>
                      <td className="p-2.5 text-rose-400">12, 5 (Win for Opponent)</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 4: RULING PLANETS (RP) */}
          {activeTab === "ruling_planets" && (
            <div className="space-y-4 animate-in fade-in duration-150">
              <div className="p-4 rounded-xl border border-cyan-500/30 bg-cyan-950/20 text-cyan-200">
                <h4 className="text-sm font-bold text-cyan-300 flex items-center gap-2">
                  <span>⚡</span> What are Ruling Planets (RP) and How to Use Them?
                </h4>
                <p className="mt-2 text-xs leading-relaxed text-slate-200">
                  Ruling Planets are the divine GPS of KP Astrology. They represent the active celestial controllers at the exact moment of a query or event.
                </p>
              </div>

              <div className="space-y-3">
                <h4 className="text-sm font-bold text-slate-100">The 5 Core Ruling Planets (Hierarchical Order):</h4>
                <ol className="list-decimal pl-5 space-y-1.5 text-slate-300">
                  <li><strong>Lagna Star Lord</strong> (Nakshatra Lord of Ascendant) — <em>Strongest</em></li>
                  <li><strong>Lagna Sign Lord</strong> (Rashi Lord of Ascendant)</li>
                  <li><strong>Moon Star Lord</strong> (Nakshatra Lord of Moon)</li>
                  <li><strong>Moon Sign Lord</strong> (Rashi Lord of Moon)</li>
                  <li><strong>Day Lord (Vara Lord)</strong> (Planet ruling the weekday at sunrise)</li>
                </ol>
                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-[11px] text-slate-300">
                  <strong className="text-amber-400">💡 Pro Tip for Astrologers:</strong> When multiple Dasha/Antardasha candidates seem capable of giving marriage or a promotion, <strong>filter them against the Ruling Planets (RP)</strong>. Only the planet that is present in both the Event Significators AND the Ruling Planets will trigger the event!
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: WORKSPACE TABS WALKTHROUGH */}
          {activeTab === "tab_walkthrough" && (
            <div className="space-y-4 animate-in fade-in duration-150">
              <h4 className="text-sm font-bold text-slate-100">
                Guide to the 11 Tabs in AstroOS KP Workspace:
              </h4>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <strong className="text-amber-400 block text-xs">1. Snapshot &amp; Overview</strong>
                  <p className="text-[11px] text-slate-400 mt-1">High-level executive dashboard showing active Dasha, primary CSLs, and Ruling Planets.</p>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <strong className="text-amber-400 block text-xs">2. ✨ Predictive AI Suite</strong>
                  <p className="text-[11px] text-slate-400 mt-1">Automated decision trees evaluating event probability across Marriage, Career, Foreign travel, and Property.</p>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <strong className="text-amber-400 block text-xs">3. Cusp Matrix (1–12)</strong>
                  <p className="text-[11px] text-slate-400 mt-1">Inspect exact Placidus degree cusps, Sign Lord, Star Lord, Sub Lord, and Sub-Sub Lord for every house.</p>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <strong className="text-amber-400 block text-xs">4. Planet Portfolio</strong>
                  <p className="text-[11px] text-slate-400 mt-1">Shows which Star Lord and Sub Lord each planet occupies, and Bhava Chalit cuspal house vs Rashi sign.</p>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <strong className="text-amber-400 block text-xs">5. Significators (A, B, C, D)</strong>
                  <p className="text-[11px] text-slate-400 mt-1">Full matrix mapping each of the 12 houses to its 4-tier planetary significators.</p>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <strong className="text-amber-400 block text-xs">6. Event Explorer &amp; Timing</strong>
                  <p className="text-[11px] text-slate-400 mt-1">Select any event to see exact timing windows, active Dasha intersections, and transit activations.</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between px-6 py-3 border-t border-slate-800 bg-slate-950/60">
          <div className="text-[11px] text-slate-400">
            AstroOS • Krishnamurti Paddhati Research Standard
          </div>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl text-xs font-bold bg-amber-500 hover:bg-amber-400 text-slate-950 transition-all cursor-pointer shadow-sm"
          >
            Got It, Thanks!
          </button>
        </div>
      </div>
    </div>
  );
}
