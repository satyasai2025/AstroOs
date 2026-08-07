'use client';

import React, { useState } from 'react';
import { YogaResultResponse, YogaDefinitionResponse, YogaActivationResponse } from '@/lib/types';
import { getYogaKnowledge } from '@/lib/yogaKnowledge';
import { StrengthProgressBar } from './StrengthProgressBar';
import { YogaActivationTimelineMini } from './YogaActivationTimelineMini';

interface YogaDetailPanelProps {
  yoga: YogaResultResponse | null;
  definition: YogaDefinitionResponse | null;
  /** Optional Dasha activation timeline for the selected yoga. */
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

  const formationRules = yoga.satisfied;
  const missingRules = yoga.missing;
  const involvedPlanets = yoga.involved_planets ?? [];
  const involvedHouses = yoga.involved_houses ?? [];
  const strengthScore = yoga.strength_score;
  const positiveResults = knowledge?.effects.positive ?? [];
  const negativeFactors = knowledge?.effects.negative ?? [];
  const classicalReferences = knowledge?.classicalReferences ?? [];
  const relatedYogas = knowledge?.relatedYogas ?? [];

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
      <div className="p-6 border-b border-gray-800">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-yellow-600 to-orange-600 flex items-center justify-center text-3xl">
              🕉️
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-100">{yoga.name}</h2>
              <div className="flex items-center gap-2 mt-1">
                <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-purple-900/30 text-purple-400">
                  {yoga.category || 'Yoga'}
                </span>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                  yoga.is_present ? 'bg-green-900/30 text-green-400' : 'bg-gray-800 text-gray-500'
                }`}>
                  {yoga.is_present ? 'Active' : 'Dormant'}
                </span>
                {strengthScore !== null && strengthScore !== undefined && (
                  <span className="text-xs text-gray-500">
                    Strength: {strengthScore}%
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-1 border-b border-gray-800">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 text-sm font-medium transition border-b-2 ${
                activeTab === tab.key
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
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
              <p className="text-gray-300 leading-relaxed">
                {knowledge?.description ||
                  `A classical ${yoga.category || 'yoga'} combination in this chart. See formation rules below.`}
              </p>
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
              {/* Formation Rules */}
              <div className="bg-gray-800/30 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">
                  Formation Rules ({formationRules.length}/{formationRules.length + missingRules.length})
                </h3>
                <div className="space-y-2">
                  {formationRules.map((rule, idx) => (
                    <div key={idx} className="flex items-start gap-2 p-2 rounded bg-green-900/20">
                      <svg className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      <p className="text-xs text-gray-300">{rule}</p>
                    </div>
                  ))}
                  {missingRules.map((rule, idx) => (
                    <div key={`m-${idx}`} className="flex items-start gap-2 p-2 rounded bg-gray-800/50">
                      <svg className="w-4 h-4 text-gray-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                      <p className="text-xs text-gray-500">{rule}</p>
                    </div>
                  ))}
                  {formationRules.length === 0 && missingRules.length === 0 && (
                    <p className="text-xs text-gray-500">No rule conditions recorded.</p>
                  )}
                </div>
              </div>

              {/* Planet Positions */}
              <div className="bg-gray-800/30 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">Contributing Planets</h3>
                {involvedPlanets.length > 0 ? (
                  <div className="space-y-2">
                    {involvedPlanets.slice(0, 6).map((planet, idx) => (
                      <div key={idx} className="flex items-center gap-2 p-2 bg-gray-900/50 rounded">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-xs">
                          {planet[0]}
                        </div>
                        <p className="text-xs font-medium text-gray-200">{planet}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-gray-500">No planet data recorded.</p>
                )}
                {involvedHouses.length > 0 && (
                  <p className="text-xs text-gray-500 mt-3">
                    Houses: {involvedHouses.join(', ')}
                  </p>
                )}
              </div>

              {/* Strength Summary */}
              <div className="bg-gray-800/30 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">Strength</h3>
                {strengthScore !== null && strengthScore !== undefined ? (
                  <div className="flex items-center justify-center py-2">
                    <StrengthProgressBar score={strengthScore} size="lg" />
                  </div>
                ) : (
                  <p className="text-xs text-gray-500">
                    No numerical strength computed for this yoga in the base workflow result.
                  </p>
                )}
              </div>
            </div>

            {/* Positive and Weakening */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <div className="bg-gray-800/30 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-green-400 mb-3 flex items-center gap-2">
                  Positive Indications
                </h3>
                <div className="space-y-2">
                  {positiveResults.length > 0 ? (
                    positiveResults.map((result, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-xs">
                        <svg className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        <span className="text-gray-300">{result}</span>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-gray-500">No specific positive results recorded.</p>
                  )}
                </div>
              </div>

              <div className="bg-gray-800/30 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-red-400 mb-3 flex items-center gap-2">
                  Weakening Factors
                </h3>
                <div className="space-y-2">
                  {negativeFactors.length > 0 ? (
                    negativeFactors.map((factor, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-xs">
                        <svg className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                        </svg>
                        <span className="text-gray-300">{factor}</span>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-gray-500">No weakening factors recorded for this yoga.</p>
                  )}
                  {yoga.counter_examples?.length > 0 && (
                    <div className="pt-2 border-t border-gray-800">
                      <p className="text-xs text-gray-400 mb-1 font-medium">Counter-examples (when it may not manifest)</p>
                      {yoga.counter_examples.map((c, idx) => (
                        <p key={idx} className="text-xs text-gray-500 flex items-start gap-1">
                          <span className="text-gray-600">•</span> {c}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'strength' && (
          <div className="space-y-6">
            <div className="bg-gray-800/30 rounded-lg p-6">
              <h3 className="text-sm font-semibold text-gray-300 mb-4">Overall Strength</h3>
              {strengthScore !== null && strengthScore !== undefined ? (
                <div className="flex flex-col items-center justify-center">
                  <StrengthProgressBar score={strengthScore} size="lg" />
                  <p className="text-xs text-gray-500 mt-3">
                    0-100 numerical strength computed by the YogaEngine&apos;s with-strength endpoint.
                  </p>
                </div>
              ) : (
                <p className="text-sm text-gray-500 text-center">
                  No numerical strength available — the base workflow evaluates yogas without strength
                  scoring. Run the with-strength evaluation to see a 0-100 figure.
                </p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'activation' && (
          <div className="space-y-6">
            <div className="bg-gray-800/30 rounded-lg p-6">
              <h3 className="text-sm font-semibold text-gray-300 mb-4">Dasha Activation Timeline</h3>
              {activations.length > 0 ? (
                <YogaActivationTimelineMini
                  activations={activations}
                  currentActivation={currentActivation}
                  dashaSystem={dashaSystem}
                />
              ) : (
                <p className="text-sm text-gray-500 text-center py-8">
                  No activation timeline data available for this yoga.
                </p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'references' && (
          <div className="space-y-4">
            {classicalReferences.length > 0 ? (
              classicalReferences.map((ref, idx) => (
                <div key={idx} className="bg-gray-800/30 border border-gray-700/30 rounded-lg p-4">
                  <p className="text-sm text-gray-300 italic mb-2">"{ref.excerpt}"</p>
                  {ref.source && (
                    <p className="text-xs text-gray-500">
                      — {ref.source}
                      {ref.chapter && `, Chapter ${ref.chapter}`}
                      {ref.verse && `, Verse ${ref.verse}`}
                    </p>
                  )}
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500 text-center py-8">No classical references available.</p>
            )}
          </div>
        )}

        {activeTab === 'related' && (
          <div className="space-y-4">
            {relatedYogas.length > 0 ? (
              <div className="grid grid-cols-2 gap-4">
                {relatedYogas.slice(0, 6).map((relatedYoga, idx) => (
                  <div key={idx} className="bg-gray-800/30 border border-gray-700/30 rounded-lg p-4 flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                      <span className="text-lg">🕉️</span>
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-200">{relatedYoga}</p>
                      <p className="text-xs text-gray-500">Related classical yoga</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 text-center py-8">No related yogas found.</p>
            )}
          </div>
        )}

        {activeTab === 'ai' && (
          <div className="bg-gradient-to-br from-purple-900/20 to-blue-900/20 border border-purple-800/30 rounded-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <h3 className="text-sm font-semibold text-purple-300">AI Insight</h3>
            </div>
            <p className="text-sm text-gray-300 leading-relaxed mb-4">
              {yoga.name} is {yoga.is_present ? 'active' : 'dormant'} in this chart
              {strengthScore !== null && strengthScore !== undefined
                ? `, with a numerical strength of ${strengthScore}% (${strengthScore >= 80 ? 'strong' : strengthScore >= 50 ? 'moderate' : 'developing'}).`
                : '.'}{' '}
              {knowledge?.description ? `${knowledge.description.substring(0, 150)}...` : ''}
            </p>
            <p className="text-xs text-gray-400">
              Reference: {yoga.source_text || definition?.source_text || 'BPHS'} · Rule version{' '}
              {yoga.rule_version || definition?.rule_version || '—'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
