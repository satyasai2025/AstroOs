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
      <div className="h-full flex items-center justify-center text-gray-400 p-8 text-center">
        <div>
          <svg className="w-16 h-16 mx-auto mb-4 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-lg">Select a yoga from the list</p>
          <p className="text-sm mt-2">View detailed analysis, strength breakdown, and activation timeline</p>
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
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-slate-300 dark:border-slate-800" style={{ backgroundColor: "var(--bg-card)" }}>
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-amber-500 to-cyan-500 flex items-center justify-center text-3xl shadow-lg border border-cyan-400/40">
              🕉️
            </div>
            <div>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{yoga.name}</h2>
              <div className="flex items-center gap-2 mt-1">
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-cyan-100 text-cyan-900 border border-cyan-600/40 dark:bg-cyan-950/40 dark:text-cyan-300">
                  {definition?.category || 'Yoga'}
                </span>
                <span className={yoga.is_present 
                  ? 'bg-emerald-100 text-emerald-900 border border-emerald-600/40 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-600/40 font-bold px-2.5 py-0.5 rounded-full text-xs' 
                  : 'bg-amber-100 text-amber-900 border border-amber-600/40 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-600/40 font-bold px-2.5 py-0.5 rounded-full text-xs'
                }>
                  {yoga.is_present ? 'Active' : 'Dormant'}
                </span>
                {yoga.strength_score !== undefined && (
                  <span className="text-xs font-bold text-slate-700 dark:text-slate-300">
                    Strength: {yoga.strength_score}%
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-2 border-b border-slate-300 dark:border-slate-800">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 text-sm font-bold transition border-b-2 ${
                activeTab === tab.key
                  ? 'border-cyan-500 text-cyan-600 dark:text-cyan-400'
                  : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div>
              <p className="text-slate-800 dark:text-slate-200 text-sm leading-relaxed font-medium">
                {knowledge?.description ? (
                  knowledge.description
                ) : (
                  <span className="text-slate-500 dark:text-slate-400 italic">
                    A classical planetary combination detected in your chart. Detailed interpretation requires the yoga definition database.
                  </span>
                )}
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Formation Conditions */}
              <div className="rounded-xl border p-4" style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 mb-3">
                  Formation Conditions {(satisfiedConditions.length + missingConditions.length) > 0 ? `(${satisfiedConditions.length}/${satisfiedConditions.length + missingConditions.length})` : ''}
                </h3>
                {satisfiedConditions.length > 0 || missingConditions.length > 0 ? (
                  <div className="space-y-2">
                    {satisfiedConditions.slice(0, 5).map((cond, idx) => (
                      <div key={`s-${idx}`} className="flex items-start gap-2 p-2 rounded-lg bg-emerald-100 text-emerald-900 border border-emerald-600/40 dark:bg-emerald-950/40 dark:text-emerald-300 font-semibold">
                        <svg className="w-4 h-4 text-emerald-600 dark:text-emerald-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        <p className="text-xs">{cond}</p>
                      </div>
                    ))}
                    {missingConditions.slice(0, 5).map((cond, idx) => (
                      <div key={`m-${idx}`} className="flex items-start gap-2 p-2 rounded-lg bg-slate-200 text-slate-700 border border-slate-300 dark:bg-slate-900/60 dark:text-slate-400 dark:border-slate-800">
                        <svg className="w-4 h-4 text-slate-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 00-1.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                        </svg>
                        <p className="text-xs">{cond}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 dark:text-slate-400 italic">No condition trace returned by the rule engine for this yoga</p>
                )}
              </div>

              {/* Involved Planets & Houses */}
              <div className="rounded-xl border p-4" style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 mb-3">Involved Planets &amp; Houses</h3>
                {involvedPlanets.length > 0 || involvedHouses.length > 0 ? (
                  <div className="space-y-3">
                    {involvedPlanets.length > 0 && (
                      <div>
                        <p className="text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">Planets</p>
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
                        <p className="text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">Houses</p>
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
                  <p className="text-xs text-slate-500 dark:text-slate-400 italic">No involved planets or houses returned for this yoga</p>
                )}
              </div>

              {/* Strength */}
              <div className="rounded-xl border p-4" style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 mb-3">Strength</h3>
                {yoga.strength && (
                  <span className={`inline-block text-xs px-2.5 py-0.5 rounded-full font-bold mb-3 ${
                    yoga.strength === 'full' ? 'bg-emerald-100 text-emerald-900 border border-emerald-600/40 dark:bg-emerald-950/40 dark:text-emerald-300' :
                    yoga.strength === 'partial' ? 'bg-amber-100 text-amber-900 border border-amber-600/40 dark:bg-amber-950/40 dark:text-amber-300' :
                    'bg-rose-100 text-rose-900 border border-rose-600/40 dark:bg-rose-950/40 dark:text-rose-300'
                  }`}>
                    {yoga.strength}
                  </span>
                )}
                {yoga.strength_score != null ? (
                  <div className="mt-2 flex items-center justify-center">
                    <div className="relative w-20 h-20">
                      <svg className="w-20 h-20 transform -rotate-90">
                        <circle cx="40" cy="40" r="35" stroke="currentColor" strokeWidth="6" fill="none" className="text-slate-300 dark:text-slate-800" />
                        <circle
                          cx="40"
                          cy="40"
                          r="35"
                          stroke="currentColor"
                          strokeWidth="6"
                          fill="none"
                          strokeDasharray={`${2 * Math.PI * 35}`}
                          strokeDashoffset={`${2 * Math.PI * 35 * (1 - (yoga.strength_score ?? 0) / 100)}`}
                          className={(yoga.strength_score ?? 0) >= 80 ? 'text-emerald-500' : (yoga.strength_score ?? 0) >= 50 ? 'text-amber-500' : 'text-rose-500'}
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-lg font-bold text-slate-900 dark:text-slate-100">{yoga.strength_score}%</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 dark:text-slate-400 italic">
                    Numerical 0-100 score requires the with-strength evaluation.
                  </p>
                )}
              </div>
            </div>

            {trace.length > 0 && (
              <div className="rounded-xl border p-4" style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 mb-3">Evaluation Trace</h3>
                <div className="space-y-1">
                  {trace.map((step, idx) => (
                    <p key={idx} className="text-xs text-slate-700 dark:text-slate-300 font-mono">{step}</p>
                  ))}
                </div>
              </div>
            )}

            {counterExamples.length > 0 && (
              <div className="bg-rose-100 text-rose-950 dark:bg-rose-950/40 dark:text-rose-200 border border-rose-600/40 rounded-xl p-4">
                <h3 className="text-sm font-bold text-rose-800 dark:text-rose-300 mb-3">Counter-Examples (Weaken/Cancel)</h3>
                <div className="space-y-1">
                  {counterExamples.map((ex, idx) => (
                    <p key={idx} className="text-xs font-semibold">{ex}</p>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'strength' && (
          <div className="space-y-4 max-w-md">
            {yoga.strength && (
              <div>
                <p className="text-xs text-gray-400 mb-1">Categorical strength (always available)</p>
                <span className={`inline-block text-sm px-3 py-1 rounded-full ${
                  yoga.strength === 'full' ? 'bg-green-900/30 text-green-400' :
                  yoga.strength === 'partial' ? 'bg-yellow-900/30 text-yellow-400' :
                  'bg-red-900/30 text-red-400'
                }`}>
                  {yoga.strength}
                </span>
              </div>
            )}
            {yoga.strength_score != null ? (
              <div>
                <p className="text-xs text-gray-400 mb-1">Numerical score</p>
                <StrengthProgressBar score={yoga.strength_score} size="md" />
              </div>
            ) : (
              <p className="text-xs text-gray-500 italic">
                Numerical 0-100 score requires the with-strength evaluation, which is currently unavailable.
              </p>
            )}
            {counterExamples.length > 0 && (
              <div>
                <p className="text-xs text-gray-400 mb-2">Counter-examples weakening this yoga</p>
                <div className="space-y-1">
                  {counterExamples.map((ex, idx) => (
                    <p key={idx} className="text-xs text-gray-500">{ex}</p>
                  ))}
                </div>
              </div>
            )}
            {!yoga.strength && yoga.strength_score == null && counterExamples.length === 0 && (
              <div className="text-center py-8">
                <p className="text-sm text-gray-400">No strength data available for this yoga</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'activation' && (
          <div>
            {activations.length > 0 ? (
              <YogaActivationTimelineMini
                activations={activations}
                currentActivation={currentActivation ?? null}
                dashaSystem={dashaSystem}
              />
            ) : (
              <div className="text-center py-8">
                <p className="text-sm text-gray-400">No activation timeline data available</p>
                <p className="text-xs text-gray-500 mt-2">
                  Run the timeline evaluation to see Dasha activation periods for this yoga
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'references' && (
          <div className="space-y-3">
            {classicalReferences.length > 0 ? (
              classicalReferences.map((ref: any, idx: number) => (
                <div key={idx} className="bg-gray-800/30 rounded-lg p-4">
                  <p className="text-xs font-semibold text-gray-300">
                    {ref.source}
                    {ref.chapter != null ? ` — Ch. ${ref.chapter}` : ''}
                    {ref.verse != null ? `, v. ${ref.verse}` : ''}
                  </p>
                  {ref.excerpt && (
                    <p className="text-xs text-gray-400 mt-2 italic">{ref.excerpt}</p>
                  )}
                </div>
              ))
            ) : knowledge?.classicalReferences && knowledge.classicalReferences.some((r) => r.excerpt) ? (
              knowledge.classicalReferences.filter((r) => r.excerpt).map((ref, idx) => (
                <div key={idx} className="bg-gray-800/30 rounded-lg p-4">
                  <p className="text-xs font-semibold text-gray-300">
                    {ref.source}
                    {ref.chapter != null ? ` — Ch. ${ref.chapter}` : ''}
                    {ref.verse != null ? `, v. ${ref.verse}` : ''}
                  </p>
                  {ref.excerpt && (
                    <p className="text-xs text-gray-400 mt-2 italic">{ref.excerpt}</p>
                  )}
                </div>
              ))
            ) : (
              <p className="text-xs text-gray-500 italic">No classical references available</p>
            )}
          </div>
        )}

        {activeTab === 'related' && (
          <div className="space-y-2">
            {(relatedYogas.length > 0 ? relatedYogas : knowledge?.relatedYogas ?? []).length > 0 ? (
              (relatedYogas.length > 0 ? relatedYogas : knowledge?.relatedYogas ?? []).map(
                (name: string, idx: number) => (
                  <div key={idx} className="bg-gray-800/30 rounded-lg p-3 text-sm text-gray-300">
                    {name}
                  </div>
                ),
              )
            ) : (
              <p className="text-xs text-gray-500 italic">No related yogas found</p>
            )}
          </div>
        )}

        {activeTab === 'ai' && (
          <div className="space-y-4">
            {knowledge?.effects && (knowledge.effects.positive.length > 0 || knowledge.effects.negative.length > 0) ? (
              <>
                {knowledge.effects.positive.length > 0 && (
                  <div className="bg-green-900/10 border border-green-900/30 rounded-lg p-4">
                    <h3 className="text-sm font-semibold text-green-400 mb-2">Positive Effects</h3>
                    <ul className="space-y-1 list-disc list-inside">
                      {knowledge.effects.positive.map((e, idx) => (
                        <li key={idx} className="text-xs text-gray-300">{e}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {knowledge.effects.negative.length > 0 && (
                  <div className="bg-red-900/10 border border-red-900/30 rounded-lg p-4">
                    <h3 className="text-sm font-semibold text-red-400 mb-2">Negative Effects</h3>
                    <ul className="space-y-1 list-disc list-inside">
                      {knowledge.effects.negative.map((e, idx) => (
                        <li key={idx} className="text-xs text-gray-300">{e}</li>
                      ))}
                    </ul>
                  </div>
                )}
                <p className="text-xs text-gray-500">
                  Intensity: <span className="text-gray-300 capitalize">{knowledge.effects.intensity}</span>
                </p>
              </>
            ) : (
              <div className="text-center py-8">
                <p className="text-sm text-gray-400">No AI explanation available</p>
                <p className="text-xs text-gray-500 mt-2">
                  This yoga is not yet in the knowledge base — explanation is limited to formation rules
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