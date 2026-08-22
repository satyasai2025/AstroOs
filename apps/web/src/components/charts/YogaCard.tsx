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
      className={`p-4 rounded-lg border cursor-pointer transition-all ${
        isSelected
          ? 'bg-purple-900/20 border-purple-500/50 shadow-lg shadow-purple-500/10'
          : 'bg-gray-800/30 border-gray-700/50 hover:bg-gray-800/50 hover:border-gray-600'
      }`}
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div 
          className="w-12 h-12 rounded-full flex items-center justify-center text-2xl flex-shrink-0"
          style={{ backgroundColor: `${categoryColor}20` }}
        >
          🕉️
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-sm font-semibold text-gray-200 truncate">{displayName}</h3>
            <button className="text-gray-500 hover:text-yellow-400 transition flex-shrink-0" aria-label="Action button">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            </button>
          </div>

          {/* Category & Status */}
          <div className="flex items-center gap-2 mb-2">
            <span 
              className="text-xs px-2 py-0.5 rounded-full"
              style={{ 
                backgroundColor: `${categoryColor}20`,
                color: categoryColor
              }}
            >
              {definition?.category || 'Yoga'}
            </span>
            <span className={`text-xs px-2 py-0.5 rounded-full ${
              isPresent 
                ? 'bg-green-900/30 text-green-400' 
                : 'bg-gray-800 text-gray-500'
            }`}>
              {isPresent ? 'Active' : 'Dormant'}
            </span>
          </div>

          {/* Planets & House */}
          <div className="text-xs text-gray-400 mb-3">
            {(yoga.involved_planets && yoga.involved_planets.length > 0) && (
              <span>
                {yoga.involved_planets.slice(0, 2).join(' • ')}
              </span>
            )}
            {(yoga.involved_houses && yoga.involved_houses.length > 0) && (
              <span className="ml-2 text-gray-500">
                Houses {yoga.involved_houses.slice(0, 2).join(', ')}
              </span>
            )}
          </div>

          {/* Strength Bar */}
          {strengthScore && (
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400">Strength</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold" style={{ color: getStrengthColor(strengthScore) }}>
                    {strengthScore}%
                  </span>
                </div>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-1.5">
                <div
                  className="h-1.5 rounded-full transition-all"
                  style={{ 
                    width: `${strengthScore}%`,
                    backgroundColor: getStrengthColor(strengthScore)
                  }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Strength Circle (Image Style) */}
        {strengthScore && (
          <div className="relative w-14 h-14 flex-shrink-0">
            <svg className="w-14 h-14 transform -rotate-90">
              <circle
                cx="28"
                cy="28"
                r="24"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
                className="text-gray-700"
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
              <span className="text-xs font-bold text-gray-200">{strengthScore}%</span>
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