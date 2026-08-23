'use client';

import React from 'react';
import { YogaResultResponse } from '@/lib/types';
import { getYogaKnowledge, YOGA_CATEGORY_COLORS } from '@/lib/yogaKnowledge';

interface YogaCardProps {
  yoga: YogaResultResponse;
  definition?: any;
  onClick: () => void;
  isSelected: boolean;
}

export function YogaCard({ yoga, definition, onClick, isSelected }: YogaCardProps) {
  const knowledge = getYogaKnowledge(yoga);
  const categoryColor = definition?.category
    ? YOGA_CATEGORY_COLORS[definition.category as keyof typeof YOGA_CATEGORY_COLORS] || '#9CA3AF'
    : '#9CA3AF';

  const displayName = yoga.name || 'Unknown Yoga';
  const isPresent = yoga.is_present;
  const strengthScore = yoga.strength_score ?? null;

  return (
    <div
      onClick={onClick}
      className={`p-4 rounded-xl border cursor-pointer transition-all ${
        isSelected
          ? 'bg-cyan-950/30 border-cyan-500 shadow-md shadow-cyan-500/20'
          : 'hover:border-slate-500 hover:bg-slate-800/40'
      }`}
      style={{
        backgroundColor: isSelected ? undefined : 'var(--bg-card)',
        borderColor: isSelected ? undefined : 'var(--border-primary)',
      }}
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div 
          className="w-12 h-12 rounded-full flex items-center justify-center text-2xl flex-shrink-0 border border-cyan-500/30"
          style={{ backgroundColor: `${categoryColor}25` }}
        >
          🕉️
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 truncate">{displayName}</h3>
          </div>

          {/* Category & Status */}
          <div className="flex items-center gap-2 mb-2">
            <span 
              className="text-xs px-2 py-0.5 rounded-full font-bold border"
              style={{ 
                backgroundColor: `${categoryColor}25`,
                color: categoryColor,
                borderColor: `${categoryColor}40`
              }}
            >
              {definition?.category || 'Yoga'}
            </span>
            <span className={isPresent 
              ? 'bg-emerald-100 text-emerald-900 border border-emerald-600/40 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-600/40 font-bold px-2 py-0.5 rounded-full text-xs' 
              : 'bg-amber-100 text-amber-900 border border-amber-600/40 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-600/40 font-bold px-2 py-0.5 rounded-full text-xs'
            }>
              {isPresent ? 'Active' : 'Dormant'}
            </span>
          </div>

          {/* Planets & House */}
          <div className="text-xs text-slate-700 dark:text-slate-300 font-semibold mb-3">
            {(yoga.involved_planets && yoga.involved_planets.length > 0) && (
              <span>
                {yoga.involved_planets.slice(0, 2).join(' • ')}
              </span>
            )}
            {(yoga.involved_houses && yoga.involved_houses.length > 0) && (
              <span className="ml-2">
                Houses {yoga.involved_houses.slice(0, 2).join(', ')}
              </span>
            )}
          </div>

          {/* Strength Bar */}
          {strengthScore !== null && strengthScore !== undefined && (
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-700 dark:text-slate-300 font-bold">Strength</span>
                <div className="flex items-center gap-2">
                  <span className={`text-sm font-bold ${
                    strengthScore >= 80 ? 'text-emerald-600 dark:text-emerald-300' : strengthScore >= 50 ? 'text-amber-600 dark:text-amber-300' : 'text-rose-600 dark:text-rose-300'
                  }`}>
                    {strengthScore}%
                  </span>
                </div>
              </div>
              <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-1.5">
                <div
                  className="h-1.5 rounded-full transition-all"
                  style={{ 
                    width: `${strengthScore}%`,
                    backgroundColor: strengthScore >= 80 ? '#10B981' : strengthScore >= 50 ? '#F59E0B' : '#EF4444'
                  }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Strength Circle */}
        {strengthScore !== null && strengthScore !== undefined && (
          <div className="relative w-14 h-14 flex-shrink-0">
            <svg className="w-14 h-14 transform -rotate-90">
              <circle
                cx="28"
                cy="28"
                r="24"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
                className="text-slate-300 dark:text-slate-800"
              />
              <circle
                cx="28"
                cy="28"
                r="24"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
                strokeDasharray={`${2 * Math.PI * 24}`}
                strokeDashoffset={`${2 * Math.PI * 24 * (1 - strengthScore / 100)}`}
                className={getStrengthCircleClass(strengthScore)}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className={`text-xs font-bold ${
                strengthScore >= 80 ? 'text-emerald-600 dark:text-emerald-300' : strengthScore >= 50 ? 'text-amber-600 dark:text-amber-300' : 'text-rose-600 dark:text-rose-300'
              }`}>{strengthScore}%</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function getStrengthColor(score: number): string {
  if (score >= 80) return '#10B981'; // green-500
  if (score >= 50) return '#F59E0B'; // yellow-500
  return '#EF4444'; // red-500
}

function getStrengthCircleClass(score: number): string {
  if (score >= 80) return 'text-green-500';
  if (score >= 50) return 'text-yellow-500';
  return 'text-red-500';
}

function getOrdinalSuffix(n: number): string {
  const s = ['th', 'st', 'nd', 'rd'];
  const v = n % 100;
  return s[(v - 20) % 10] || s[v] || s[0];
}