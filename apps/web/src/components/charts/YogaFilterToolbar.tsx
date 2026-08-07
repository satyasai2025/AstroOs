'use client';

import React from 'react';

interface YogaFilterToolbarProps {
  searchQuery: string;
  onSearchChange: (value: string) => void;
  categoryFilter: string;
  onCategoryChange: (value: string) => void;
  activeOnly: boolean;
  onActiveOnlyChange: (value: boolean) => void;
  beneficOnly: boolean;
  onBeneficOnlyChange: (value: boolean) => void;
  maleficOnly: boolean;
  onMaleficOnlyChange: (value: boolean) => void;
  minStrength: number | null;
  onMinStrengthChange: (value: number | null) => void;
  sortBy: string;
  onSortByChange: (value: string) => void;
  categories: string[];
  resultCount: number;
  totalCount: number;
  categoryCounts: Record<string, number>;
  onClearFilters: () => void;
  hasActiveFilters: boolean;
}

export function YogaFilterToolbar({
  searchQuery,
  onSearchChange,
  categoryFilter,
  onCategoryChange,
  activeOnly,
  onActiveOnlyChange,
  beneficOnly,
  onBeneficOnlyChange,
  maleficOnly,
  onMaleficOnlyChange,
  minStrength,
  onMinStrengthChange,
  sortBy,
  onSortByChange,
  categories,
  resultCount,
  totalCount,
  categoryCounts,
  onClearFilters,
  hasActiveFilters,
}: YogaFilterToolbarProps) {
  return (
    <div className="flex flex-col gap-4">
      {/* Top Row - Search and Actions */}
      <div className="flex items-center gap-3">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search yogas, planets, houses..."
            className="w-full pl-10 pr-8 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/50"
          />
          {searchQuery && (
            <button
              onClick={() => onSearchChange('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-300"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>

        {/* Filters Button */}
        <div className="relative">
          <button className="flex items-center gap-2 px-4 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-sm text-gray-300 hover:bg-gray-800 transition">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            <span>Filters</span>
            {hasActiveFilters && (
              <span className="w-2 h-2 bg-purple-500 rounded-full"></span>
            )}
          </button>
        </div>

        {/* Sort By */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">Sort by:</span>
          <select
            value={sortBy}
            onChange={(e) => onSortByChange(e.target.value)}
            className="px-3 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-sm text-gray-300 focus:outline-none focus:border-purple-500/50"
          >
            <option value="strength_desc">Strength</option>
            <option value="strength_asc">Strength (Low to High)</option>
            <option value="name_asc">Name (A-Z)</option>
            <option value="name_desc">Name (Z-A)</option>
          </select>
        </div>

        {/* Action Icons */}
        <div className="flex items-center gap-2 ml-auto">
          <button className="p-2 text-gray-400 hover:text-gray-300 transition" title="Export">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          </button>
          <button className="p-2 text-gray-400 hover:text-gray-300 transition" title="Duplicate">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </button>
          <button className="p-2 text-gray-400 hover:text-gray-300 transition" title="Help">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 ml-2 cursor-pointer"></div>
        </div>
      </div>

      {/* Category Tabs */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => onCategoryChange('all')}
          className={`px-4 py-1.5 rounded-full text-sm font-medium transition ${
            categoryFilter === 'all'
              ? 'bg-purple-500/20 text-purple-400 border border-purple-500/50'
              : 'text-gray-400 hover:text-gray-300'
          }`}
        >
          All <span className="ml-1 text-xs opacity-75">{categoryCounts['all'] || totalCount}</span>
        </button>
        {categories.slice(0, 5).map((category) => {
          const count = categoryCounts[category] || Math.floor(totalCount / (categories.length || 1));
          return (
            <button
              key={category}
              onClick={() => onCategoryChange(category)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition ${
                categoryFilter === category
                  ? 'bg-purple-500/20 text-purple-400 border border-purple-500/50'
                  : 'text-gray-400 hover:text-gray-300'
              }`}
            >
              {category}
              <span className="ml-1 text-xs opacity-75">{count}</span>
            </button>
          );
        })}
        <button className="text-gray-400 hover:text-gray-300 text-sm ml-2">Others</button>
      </div>

      {/* Secondary Filters Row */}
      {hasActiveFilters && (
        <div className="flex items-center gap-3 text-xs">
          <span className="text-gray-400">Active filters:</span>
          {activeOnly && (
            <span className="px-2 py-1 bg-purple-900/30 text-purple-300 rounded border border-purple-800/30">
              Active Only
            </span>
          )}
          {beneficOnly && (
            <span className="px-2 py-1 bg-green-900/30 text-green-300 rounded border border-green-800/30">
              Benefic
            </span>
          )}
          {maleficOnly && (
            <span className="px-2 py-1 bg-red-900/30 text-red-300 rounded border border-red-800/30">
              Malefic
            </span>
          )}
          {minStrength !== null && (
            <span className="px-2 py-1 bg-yellow-900/30 text-yellow-300 rounded border border-yellow-800/30">
              Strength ≥ {minStrength}
            </span>
          )}
          <button
            onClick={onClearFilters}
            className="text-purple-400 hover:text-purple-300 ml-auto"
          >
            Clear all
          </button>
        </div>
      )}
    </div>
  );
}