'use client';

import React from 'react';

interface StrengthProgressBarProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export function StrengthProgressBar({ score, size = 'md', showLabel = true }: StrengthProgressBarProps) {
  const getColor = (score: number) => {
    if (score >= 80) return '#10B981'; // green-500
    if (score >= 50) return '#F59E0B'; // yellow-500
    return '#EF4444'; // red-500
  };

  const sizeClasses = {
    sm: 'h-1.5',
    md: 'h-2',
    lg: 'h-3',
  };

  const textSizes = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  return (
    <div className="w-full">
      <div className={`w-full bg-gray-700 rounded-full ${sizeClasses[size]} overflow-hidden`}>
        <div
          className={`${sizeClasses[size]} rounded-full transition-all duration-500`}
          style={{ 
            width: `${score}%`,
            backgroundColor: getColor(score)
          }}
        />
      </div>
      {showLabel && (
        <div className="flex justify-between items-center mt-1">
          <span className={`${textSizes[size]} text-gray-400`}>Strength</span>
          <span className={`${textSizes[size]} font-bold`} style={{ color: getColor(score) }}>
            {score}%
          </span>
        </div>
      )}
    </div>
  );
}