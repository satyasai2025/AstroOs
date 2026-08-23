'use client';

import React, { useState } from 'react';
import { YogaResultResponse, YogaDefinitionResponse, YogaActivationResponse } from '@/lib/types';
import { getYogaKnowledge } from '@/lib/yogaKnowledge';
import { StrengthProgressBar } from './StrengthProgressBar';
import { YogaActivationTimelineMini } from './YogaActivationTimelineMini';

interface YogaDetailPanelProps {
  yoga: YogaResultResponse | null;
  definition: YogaDefinitionResponse | null;
  activations?: YogaActivationResponse[];
  currentActivation?: YogaActivationResponse | null;
  dashaSystem?: string;
}

type TabType = 'overview' | 'strength' | 'activation' | 'references' | 'related' | 'ai';

export function YogaDetailPanel({
  yoga,
  definition,
  activations = [],
  currentActivation = null,
  dashaSystem,
}: YogaDetailPanelProps) {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const knowledge = yoga ? getYogaKnowledge(yoga) : null;

  if (!yoga) {
    return (
      <div className="h-full flex items-center justify-center p-8 text-center" style={{ backgroundColor: "var(--bg-card)" }}>
        <div className="space-y-3">
          <div className="w-16 h-16 mx-auto rounded-full bg-cyan-950/40 border border-cyan-500/30 flex items-center justify-center text-2xl text-cyan-400">
            🕉️
          </div>
          <p className="text-base font-bold text-slate-900 dark:text-slate-100">Select a Yoga to Inspect</p>
          <p className="text-xs font-medium text-slate-700 dark:text-slate-300 max-w-xs">
            View formation rules, strength score breakdown, dasha activation periods, and classical literature excerpts.
          </p>
        </div>
      </div>
    );
  }

  const satisfiedConditions = yoga.satisfied || [];
  const missingConditions = yoga.missing || [];
  const involvedPlanets = yoga.involved_planets || [];
  const involvedHouses = yoga.involved_houses || [];
  const trace = yoga.trace || [];
  const counterExamples = yoga.counter_examples || [];
  const classicalReferences: { source: string; chapter: string | number | null; verse: string | number | null; excerpt: string }[] = [];
  const relatedYogas: string[] = [];

  const tabs: { key: TabType; label: string }[] = [
    { key: 'overview', label: 'Overview' },
    { key: 'strength', label: 'Strength' },
    { key: 'activation', label: 'Activation' },
    { key: 'references', label: 'References' },
    { key: 'related', label: 'Related Yogas' },
    { key: 'ai', label: 'AI Explanation' },
  ];

  return (
    <div className="h-full flex flex-col font-sans">
      {/* Header */}
      <div className="p-5 border-b shadow-md" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}>
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-amber-500 to-cyan-600 flex items-center justify-center text-2xl shadow-lg border border-cyan-400/40">
              🕉️
            </div>
            <div>
              <h2 className="text-xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">{yoga.name}</h2>
              <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-cyan-100 text-cyan-900 border border-cyan-600/40 dark:bg-cyan-950/60 dark:text-cyan-300">
                  {definition?.category || 'Vedic Yoga'}
                </span>
                <span className={yoga.is_present 
                  ? 'bg-emerald-100 text-emerald-900 border border-emerald-600/40 dark:bg-emerald-950/60 dark:text-emerald-300 font-bold px-2.5 py-0.5 rounded-full text-xs' 
                  : 'bg-amber-100 text-amber-900 border border-amber-600/40 dark:bg-amber-950/60 dark:text-amber-300 font-bold px-2.5 py-0.5 rounded-full text-xs'
                }>
                  {yoga.is_present ? 'Active ✓' : 'Dormant'}
                </span>
                {yoga.strength_score !== undefined && (
                  <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                    Strength: <strong className="text-cyan-400">{yoga.strength_score}%</strong>
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1 border-b" style={{ borderColor: "var(--border-primary)" }}>
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-3 py-1.5 text-xs font-bold transition rounded-lg whitespace-nowrap cursor-pointer ${
                activeTab === tab.key
                  ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/40'
                  : 'text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-800/40'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {activeTab === 'overview' && (
          <div className="space-y-5">
            <div className="rounded-2xl border p-4 shadow-sm" style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
              <p className="text-slate-800 dark:text-slate-200 text-xs sm:text-sm leading-relaxed font-medium">
                {knowledge?.description ? (
                  knowledge.description
                ) : (
                  <span className="text-slate-400 italic">
                    A classical planetary combination detected in your natal chart. Detailed interpretation requires the yoga knowledge base.
                  </span>
                )}
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Formation Conditions */}
              <div className="rounded-2xl border p-4 shadow-sm" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100 mb-3">
                  Formation Conditions {(satisfiedConditions.length + missingConditions.length) > 0 ? `(${satisfiedConditions.length}/${satisfiedConditions.length + missingConditions.length})` : ''}
                </h3>
                {satisfiedConditions.length > 0 || missingConditions.length > 0 ? (
                  <div className="space-y-2">
                    {satisfiedConditions.slice(0, 5).map((cond, idx) => (
                      <div key={`s-${idx}`} className="flex items-start gap-2 p-2 rounded-xl bg-emerald-100 text-emerald-900 border border-emerald-600/40 dark:bg-emerald-950/40 dark:text-emerald-300 font-semibold">
                        <svg className="w-4 h-4 text-emerald-600 dark:text-emerald-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        <p className="text-xs">{cond}</p>
                      </div>
                    ))}
                    {missingConditions.slice(0, 5).map((cond, idx) => (
                      <div
                        key={`m-${idx}`}
                        className="flex items-start gap-2 p-2 rounded-xl border font-semibold text-slate-700 dark:text-slate-300"
                        style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}
                      >
                        <svg className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 00-1.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                        </svg>
                        <p className="text-xs">{cond}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No condition trace returned for this yoga</p>
                )}
              </div>

              {/* Involved Planets & Houses */}
              <div className="rounded-2xl border p-4 shadow-sm" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100 mb-3">Involved Grahas &amp; Bhavas</h3>
                {involvedPlanets.length > 0 || involvedHouses.length > 0 ? (
                  <div className="space-y-3">
                    {involvedPlanets.length > 0 && (
                      <div>
                        <p className="text-xs font-bold text-slate-800 dark:text-slate-200 mb-1.5">Planets</p>
                        <div className="flex flex-wrap gap-1.5">
                          {involvedPlanets.map((planet, idx) => (
                            <span key={idx} className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-cyan-100 text-cyan-900 border border-cyan-600/40 dark:bg-cyan-950/40 dark:text-cyan-300">
                              {planet}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {involvedHouses.length > 0 && (
                      <div>
                        <p className="text-xs font-bold text-slate-800 dark:text-slate-200 mb-1.5">Houses</p>
                        <div className="flex flex-wrap gap-1.5">
                          {involvedHouses.map((house, idx) => (
                            <span key={idx} className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-amber-100 text-amber-900 border border-amber-600/40 dark:bg-amber-950/40 dark:text-amber-300">
                              {house}{getOrdinalSuffix(house)}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No involved planets or houses returned for this yoga</p>
                )}
              </div>

              {/* Strength */}
              <div className="rounded-2xl border p-4 shadow-sm" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100 mb-3">Potency Score</h3>
                {yoga.strength && (
                  <span className={`inline-block text-xs px-2.5 py-0.5 rounded-full font-bold mb-3 ${
                    yoga.strength === 'full' ? 'bg-emerald-100 text-emerald-900 border border-emerald-600/40 dark:bg-emerald-950/40 dark:text-emerald-300' :
                    yoga.strength === 'partial' ? 'bg-amber-100 text-amber-900 border border-amber-600/40 dark:bg-amber-950/40 dark:text-amber-300' :
                    'bg-rose-100 text-rose-900 border border-rose-600/40 dark:bg-rose-950/40 dark:text-rose-300'
                  }`}>
                    {yoga.strength} potency
                  </span>
                )}
                {yoga.strength_score != null ? (
                  <div className="mt-2 flex items-center justify-center">
                    <div className="relative w-20 h-20">
                      <svg className="w-20 h-20 transform -rotate-90">
                        <circle cx="40" cy="40" r="35" stroke="currentColor" strokeWidth="6" fill="none" className="text-slate-800" />
                        <circle
                          cx="40"
                          cy="40"
                          r="35"
                          stroke="currentColor"
                          strokeWidth="6"
                          fill="none"
                          strokeDasharray={`${2 * Math.PI * 35}`}
                          strokeDashoffset={`${2 * Math.PI * 35 * (1 - (yoga.strength_score ?? 0) / 100)}`}
                          className={(yoga.strength_score ?? 0) >= 80 ? 'text-emerald-400' : (yoga.strength_score ?? 0) >= 50 ? 'text-amber-400' : 'text-rose-400'}
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-lg font-extrabold text-slate-900 dark:text-slate-100">{yoga.strength_score}%</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">
                    Numerical 0-100 score requires strength evaluation.
                  </p>
                )}
              </div>
            </div>

            {trace.length > 0 && (
              <div className="rounded-2xl border p-4 shadow-sm" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100 mb-3">Evaluation Logic Trace</h3>
                <div className="space-y-1.5">
                  {trace.map((step, idx) => (
                    <div
                      key={idx}
                      className="flex items-start gap-2 text-xs font-semibold text-slate-900 dark:text-slate-100 p-2.5 rounded-xl border"
                      style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}
                    >
                      <span className="text-cyan-500 dark:text-cyan-400 font-bold flex-shrink-0">↳</span>
                      <span className="leading-relaxed">{step}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {counterExamples.length > 0 && (
              <div className="bg-rose-950/30 text-rose-200 border border-rose-500/40 rounded-2xl p-4 shadow-sm">
                <h3 className="text-xs font-bold text-rose-300 uppercase tracking-wider mb-2">Counter-Examples (Weaken/Cancel)</h3>
                <div className="space-y-1">
                  {counterExamples.map((ex, idx) => (
                    <p key={idx} className="text-xs font-semibold text-rose-200">• {ex}</p>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'strength' && (
          <div className="space-y-5 max-w-lg">
            <div className="rounded-2xl border p-4 shadow-sm space-y-4" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}>
              {yoga.strength && (
                <div>
                  <p className="text-xs font-bold text-slate-800 dark:text-slate-200 mb-1.5">Categorical Strength Assessment</p>
                  <span className={`inline-block text-xs px-3 py-1 rounded-full font-bold ${
                    yoga.strength === 'full' ? 'bg-emerald-100 text-emerald-900 border border-emerald-600/40 dark:bg-emerald-950/60 dark:text-emerald-300' :
                    yoga.strength === 'partial' ? 'bg-amber-100 text-amber-900 border border-amber-600/40 dark:bg-amber-950/60 dark:text-amber-300' :
                    'bg-rose-100 text-rose-900 border border-rose-600/40 dark:bg-rose-950/60 dark:text-rose-300'
                  }`}>
                    {yoga.strength} strength
                  </span>
                </div>
              )}
              {yoga.strength_score != null ? (
                <div>
                  <p className="text-xs font-bold text-slate-800 dark:text-slate-200 mb-2">Quantified Score (0-100% Scale)</p>
                  <StrengthProgressBar score={yoga.strength_score} size="md" />
                </div>
              ) : (
                <p className="text-xs text-slate-400 italic">
                  Numerical 0-100 score requires full multi-varga strength evaluation.
                </p>
              )}
            </div>

            {counterExamples.length > 0 && (
              <div className="rounded-2xl border border-rose-500/40 bg-rose-950/20 p-4 shadow-sm">
                <p className="text-xs font-bold text-rose-300 mb-2">Counter-examples weakening this yoga</p>
                <div className="space-y-1">
                  {counterExamples.map((ex, idx) => (
                    <p key={idx} className="text-xs font-semibold text-rose-200">• {ex}</p>
                  ))}
                </div>
              </div>
            )}

            {!yoga.strength && yoga.strength_score == null && counterExamples.length === 0 && (
              <div className="text-center py-8 rounded-2xl border p-4" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}>
                <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">No strength metrics available for this yoga</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'activation' && (
          <div className="space-y-4">
            {activations.length > 0 ? (
              <YogaActivationTimelineMini
                activations={activations}
                currentActivation={currentActivation ?? null}
                dashaSystem={dashaSystem}
              />
            ) : (
              <div className="text-center py-8 rounded-2xl border p-6 space-y-2" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}>
                <div className="text-2xl text-cyan-400">⏳</div>
                <p className="text-sm font-bold text-slate-900 dark:text-slate-100">No Dasha Activation Periods Triggered</p>
                <p className="text-xs text-slate-700 dark:text-slate-300 font-medium max-w-sm mx-auto">
                  Run Vimshottari / Yogini Dasha timeline evaluation to inspect precise activation dates for this planetary combination.
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'references' && (
          <div className="space-y-3">
            {classicalReferences.length > 0 ? (
              classicalReferences.map((ref: any, idx: number) => (
                <div key={idx} className="rounded-2xl border p-4 space-y-2 backdrop-blur-sm shadow-md" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}>
                  <p className="text-xs font-bold text-cyan-400 flex items-center gap-1.5">
                    <span>📖</span>
                    <span>{ref.source}</span>
                    {ref.chapter != null && <span>— Ch. {ref.chapter}</span>}
                    {ref.verse != null && <span>, v. {ref.verse}</span>}
                  </p>
                  {ref.excerpt && (
                    <p className="text-xs text-slate-800 dark:text-slate-200 leading-relaxed font-medium italic border-l-2 border-cyan-500/40 pl-3">
                      "{ref.excerpt}"
                    </p>
                  )}
                </div>
              ))
            ) : knowledge?.classicalReferences && knowledge.classicalReferences.some((r) => r.excerpt) ? (
              knowledge.classicalReferences.filter((r) => r.excerpt).map((ref, idx) => (
                <div key={idx} className="rounded-2xl border p-4 space-y-2 backdrop-blur-sm shadow-md" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}>
                  <p className="text-xs font-bold text-cyan-400 flex items-center gap-1.5">
                    <span>📖</span>
                    <span>{ref.source}</span>
                    {ref.chapter != null && <span>— Ch. {ref.chapter}</span>}
                    {ref.verse != null && <span>, v. {ref.verse}</span>}
                  </p>
                  {ref.excerpt && (
                    <p className="text-xs text-slate-800 dark:text-slate-200 leading-relaxed font-medium italic border-l-2 border-cyan-500/40 pl-3">
                      "{ref.excerpt}"
                    </p>
                  )}
                </div>
              ))
            ) : (
              <div className="rounded-2xl border p-6 text-center space-y-2" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}>
                <p className="text-xs font-medium text-slate-400 italic">No classical reference verses linked for {yoga.name}.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'related' && (
          <div className="space-y-3">
            {(relatedYogas.length > 0 ? relatedYogas : knowledge?.relatedYogas ?? []).length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {(relatedYogas.length > 0 ? relatedYogas : knowledge?.relatedYogas ?? []).map(
                  (name: string, idx: number) => (
                    <div key={idx} className="rounded-xl border p-3 text-xs font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2 backdrop-blur-sm" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}>
                      <span className="text-cyan-400">✦</span>
                      <span>{name}</span>
                    </div>
                  ),
                )}
              </div>
            ) : (
              <div className="rounded-2xl border p-6 text-center" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}>
                <p className="text-xs font-medium text-slate-400 italic">No related yogas linked in database.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'ai' && (
          <div className="space-y-4">
            {knowledge?.effects && (knowledge.effects.positive.length > 0 || knowledge.effects.negative.length > 0) ? (
              <>
                {knowledge.effects.positive.length > 0 && (
                  <div className="rounded-2xl border border-emerald-500/40 bg-emerald-950/20 p-4 shadow-sm space-y-2">
                    <h3 className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                      <span>✨</span> Positive Manifestation Effects
                    </h3>
                    <ul className="space-y-1.5 text-xs text-emerald-200 font-medium">
                      {knowledge.effects.positive.map((e, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="text-emerald-400 font-bold">•</span>
                          <span>{e}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {knowledge.effects.negative.length > 0 && (
                  <div className="rounded-2xl border border-rose-500/40 bg-rose-950/20 p-4 shadow-sm space-y-2">
                    <h3 className="text-xs font-bold text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
                      <span>⚠️</span> Potential Afflictions &amp; Friction
                    </h3>
                    <ul className="space-y-1.5 text-xs text-rose-200 font-medium">
                      {knowledge.effects.negative.map((e, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="text-rose-400 font-bold">•</span>
                          <span>{e}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                <div className="rounded-xl border p-3 text-xs flex justify-between font-bold" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}>
                  <span className="text-slate-700 dark:text-slate-300">Overall Manifestation Intensity:</span>
                  <span className="text-cyan-400 capitalize">{knowledge.effects.intensity}</span>
                </div>
              </>
            ) : (
              <div className="rounded-2xl border p-6 text-center space-y-2" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}>
                <div className="text-2xl text-cyan-400">🤖</div>
                <p className="text-sm font-bold text-slate-900 dark:text-slate-100">AI Synthesis Pending Knowledge Base Entry</p>
                <p className="text-xs text-slate-700 dark:text-slate-300 font-medium max-w-sm mx-auto">
                  Rule evaluation completed. Detailed AI natural-language synthesis will populate once knowledge base entry is mapped.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function getOrdinalSuffix(n: number): string {
  const s = ['th', 'st', 'nd', 'rd'];
  const v = n % 100;
  return s[(v - 20) % 10] || s[v] || s[0];
}