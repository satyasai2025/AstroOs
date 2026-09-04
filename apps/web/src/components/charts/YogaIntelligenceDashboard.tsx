'use client';

import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { YogaResultResponse, YogaDefinitionResponse, YogaActivationResponse, WorkflowAnalysisRequest } from '@/lib/types';
import {
  useYogaCatalog,
  useYogaStrengthEvaluation,
  useYogaTimelineEvaluation,
} from '@/lib/yoga';
import { getYogaKnowledgeByName } from '@/lib/yogaKnowledge';
import { YogaCard } from './YogaCard';
import { YogaFilterToolbar } from './YogaFilterToolbar';
import { YogaDetailPanel } from './YogaDetailPanel';

interface YogaIntelligenceDashboardProps {
  result?: {
    yogas: {
      results: YogaResultResponse[];
    };
  };
  request?: WorkflowAnalysisRequest | null;
}

function toYogaEvaluationRequest(
  request: WorkflowAnalysisRequest | null | undefined,
): {
  birth_datetime_utc: string;
  latitude: number;
  longitude: number;
  ayanamsa: WorkflowAnalysisRequest['ayanamsa'];
  house_system: WorkflowAnalysisRequest['house_system'];
} | null {
  if (!request) return null;
  return {
    birth_datetime_utc: request.birth_datetime_utc,
    latitude: request.latitude,
    longitude: request.longitude,
    ayanamsa: request.ayanamsa,
    house_system: request.house_system,
  };
}

function natureOf(name: string): 'benefic' | 'malefic' | null {
  const entry = getYogaKnowledgeByName(name);
  const tags = entry?.tags ?? [];
  if (tags.includes('malefic') || tags.includes('dosha')) return 'malefic';
  if (tags.length > 0) return 'benefic';
  return null;
}

export function YogaIntelligenceDashboard({ result, request }: YogaIntelligenceDashboardProps) {
  const [selectedYoga, setSelectedYoga] = useState<YogaResultResponse | null>(null);
  const [selectedDefinition, setSelectedDefinition] = useState<YogaDefinitionResponse | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [activeOnly, setActiveOnly] = useState(false);
  const [beneficOnly, setBeneficOnly] = useState(false);
  const [maleficOnly, setMaleficOnly] = useState(false);
  const [minStrength, setMinStrength] = useState<number | null>(null);
  const [sortBy, setSortBy] = useState<string>('strength_desc');
  const [showHelp, setShowHelp] = useState(false);

  const { data: catalogData, isLoading: catalogLoading } = useYogaCatalog();
  const catalog = catalogData?.yogas ?? [];

  const evalBody = toYogaEvaluationRequest(request);
  const { data: strengthData } = useYogaStrengthEvaluation(evalBody ?? null, { presentOnly: false });
  const { data: timelineData } = useYogaTimelineEvaluation(evalBody ?? null);

  const definitionsById = useMemo(() => {
    const m = new Map<string, YogaDefinitionResponse>();
    catalog.forEach((d) => m.set(d.yoga_id, d));
    return m;
  }, [catalog]);

  const strengthByYogaId = useMemo(() => {
    const m = new Map<string, number>();
    strengthData?.results?.forEach((r) => {
      if (r.strength_score != null) m.set(r.yoga_id, r.strength_score);
    });
    return m;
  }, [strengthData]);

  const timelineByYogaId = useMemo(() => {
    const m = new Map<string, { activations: YogaActivationResponse[]; current: YogaActivationResponse | null }>();
    timelineData?.timelines?.forEach((t) => {
      m.set(t.yoga_id, { activations: t.activations ?? [], current: t.current_activation ?? null });
    });
    return m;
  }, [timelineData]);

  const rawYogas = result?.yogas?.results ?? [];

  const enrichedYogas: YogaResultResponse[] = useMemo(() => {
    return rawYogas.map((y) => {
      const s = strengthByYogaId.get(y.yoga_id);
      return s !== undefined ? { ...y, strength_score: s } : y;
    });
  }, [rawYogas, strengthByYogaId]);

  const hasYogaData = enrichedYogas.length > 0;

  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = { all: enrichedYogas.length };
    enrichedYogas.forEach((yoga) => {
      const category = catalog.find((d) => d.yoga_id === yoga.yoga_id)?.category || 'Others';
      counts[category] = (counts[category] || 0) + 1;
    });
    return counts;
  }, [enrichedYogas, catalog]);

  const categories = useMemo(() => {
    const set = new Set<string>();
    catalog.forEach((d) => d.category && set.add(d.category));
    return Array.from(set).sort();
  }, [catalog]);

  const filteredYogas = useMemo(() => {
    let filtered = [...enrichedYogas];

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      filtered = filtered.filter((yoga) => {
        const def = definitionsById.get(yoga.yoga_id);
        return (
          yoga.name.toLowerCase().includes(q) ||
          (def?.name || '').toLowerCase().includes(q) ||
          (def?.category || '').toLowerCase().includes(q)
        );
      });
    }

    if (categoryFilter !== 'all') {
      filtered = filtered.filter((yoga) => {
        const def = definitionsById.get(yoga.yoga_id);
        return def?.category === categoryFilter;
      });
    }

    if (activeOnly) filtered = filtered.filter((yoga) => yoga.is_present);

    if (beneficOnly) {
      filtered = filtered.filter((yoga) => natureOf(yoga.name) === 'benefic');
    }
    if (maleficOnly) {
      filtered = filtered.filter((yoga) => natureOf(yoga.name) === 'malefic');
    }

    if (minStrength !== null) {
      filtered = filtered.filter((yoga) => (yoga.strength_score ?? 0) >= minStrength);
    }

    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'strength_asc': return (a.strength_score ?? 0) - (b.strength_score ?? 0);
        case 'strength_desc': return (b.strength_score ?? 0) - (a.strength_score ?? 0);
        case 'name_asc': return a.name.localeCompare(b.name);
        case 'name_desc': return b.name.localeCompare(a.name);
        default: return 0;
      }
    });

    return filtered;
  }, [enrichedYogas, searchQuery, categoryFilter, activeOnly, beneficOnly, maleficOnly, minStrength, sortBy, definitionsById]);

  // Auto-select first active yoga item on initial load
  React.useEffect(() => {
    if (!selectedYoga && filteredYogas.length > 0) {
      const firstActive = filteredYogas.find((y) => y.is_present) ?? filteredYogas[0];
      if (firstActive) {
        setSelectedYoga(firstActive);
        setSelectedDefinition(definitionsById.get(firstActive.yoga_id) ?? null);
      }
    }
  }, [filteredYogas, selectedYoga, definitionsById]);

  const handleYogaSelect = (yoga: YogaResultResponse) => {
    setSelectedYoga(yoga);
    setSelectedDefinition(definitionsById.get(yoga.yoga_id) ?? null);
  };

  const clearFilters = () => {
    setSearchQuery('');
    setCategoryFilter('all');
    setActiveOnly(false);
    setBeneficOnly(false);
    setMaleficOnly(false);
    setMinStrength(null);
    setSortBy('strength_desc');
  };

  const hasActiveFilters =
    !!searchQuery || categoryFilter !== 'all' || activeOnly || beneficOnly || maleficOnly || minStrength !== null;

  const activeTimeline = selectedYoga ? timelineByYogaId.get(selectedYoga.yoga_id) ?? null : null;

  const handleExport = () => {
    if (filteredYogas.length === 0) {
      alert('No yogas to export');
      return;
    }

    const headers = ['Name', 'Category', 'Status', 'Strength', 'Planets', 'Houses'];
    const rows = filteredYogas.map((yoga) => {
      const category = definitionsById.get(yoga.yoga_id)?.category || 'Unknown';
      return [
        yoga.name,
        category,
        yoga.is_present ? 'Active' : 'Dormant',
        yoga.strength_score ?? 'N/A',
        yoga.involved_planets.join('; '),
        yoga.involved_houses.join('; ')
      ];
    });

    const csvContent = [headers, ...rows]
      .map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `yogas-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDuplicate = async () => {
    if (!selectedYoga) {
      alert('Please select a yoga first to copy its details');
      return;
    }
    const category = definitionsById.get(selectedYoga.yoga_id)?.category || 'Unknown';
    const text = `Yoga: ${selectedYoga.name}
Category: ${category}
Status: ${selectedYoga.is_present ? 'Active' : 'Dormant'}
Strength: ${selectedYoga.strength_score ?? 'N/A'}%
Planets: ${selectedYoga.involved_planets.join(', ')}
Houses: ${selectedYoga.involved_houses.join(', ')}`;

    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
      }
      alert('Yoga details copied to clipboard!');
    } catch (err) {
      console.error('Failed to copy:', err);
      alert('Failed to copy. Please try again.');
    }
  };

  return (
    <div className="h-full flex flex-col rounded-2xl border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}>
      <div className="border-b p-4" style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
        <YogaFilterToolbar
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          categoryFilter={categoryFilter}
          onCategoryChange={setCategoryFilter}
          activeOnly={activeOnly}
          onActiveOnlyChange={setActiveOnly}
          beneficOnly={beneficOnly}
          onBeneficOnlyChange={setBeneficOnly}
          maleficOnly={maleficOnly}
          onMaleficOnlyChange={setMaleficOnly}
          minStrength={minStrength}
          onMinStrengthChange={setMinStrength}
          sortBy={sortBy}
          onSortByChange={setSortBy}
          categories={categories}
          resultCount={filteredYogas.length}
          totalCount={enrichedYogas.length}
          categoryCounts={categoryCounts}
          onClearFilters={clearFilters}
          hasActiveFilters={hasActiveFilters}
          onExport={handleExport}
          onDuplicate={handleDuplicate}
          onHelp={() => setShowHelp(true)}
        />
      </div>

      <div className="flex-1 flex overflow-hidden">
        <div className="w-96 border-r overflow-y-auto" style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
          {catalogLoading && enrichedYogas.length === 0 ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400" />
            </div>
          ) : !hasYogaData ? (
            <div className="flex items-center justify-center h-64 p-6 text-center">
              <div>
                <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">No yoga analysis available</p>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">Run a chart analysis to detect yogas</p>
              </div>
            </div>
          ) : filteredYogas.length === 0 ? (
            <div className="flex items-center justify-center h-64 p-6 text-center">
              <div>
                <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">No yogas match your filters</p>
                {hasActiveFilters && (
                  <button onClick={clearFilters} className="mt-3 text-xs text-cyan-600 dark:text-cyan-400 font-bold hover:underline">
                    Clear filters
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="p-4 space-y-3">
              {filteredYogas.map((yoga) => (
                <YogaCard
                  key={yoga.yoga_id}
                  yoga={yoga}
                  definition={definitionsById.get(yoga.yoga_id)}
                  onClick={() => handleYogaSelect(yoga)}
                  isSelected={selectedYoga?.yoga_id === yoga.yoga_id}
                />
              ))}
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto" style={{ backgroundColor: "var(--bg-card)" }}>
          {selectedYoga ? (
            <YogaDetailPanel
              yoga={selectedYoga}
              definition={selectedDefinition}
              activations={activeTimeline?.activations ?? []}
              currentActivation={activeTimeline?.current ?? null}
              dashaSystem={timelineData?.dasha_system}
            />
          ) : (
            <div className="h-full flex items-center justify-center text-slate-700 dark:text-slate-300">
              <div className="text-center p-8">
                <p className="text-lg font-bold mb-2 text-slate-900 dark:text-slate-100">Yoga Intelligence Dashboard</p>
                <p className="text-sm text-slate-600 dark:text-slate-400 max-w-md">
                  Select a yoga from the list to view detailed analysis including strength breakdown,
                  formation rules, planet positions, and Dasha activation timeline.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {showHelp && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-100">Yoga Intelligence Dashboard Help</h3>
              <button onClick={() => setShowHelp(false)} className="text-gray-400 hover:text-gray-300">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="space-y-4 text-sm text-gray-300">
              <div>
                <h4 className="font-semibold text-purple-400 mb-1">About Yogas</h4>
                <p>Yogas are planetary combinations in Vedic astrology that indicate specific life patterns, strengths, and challenges. This dashboard analyzes your birth chart to identify all present yogas.</p>
              </div>
              <div>
                <h4 className="font-semibold text-purple-400 mb-1">Strength Scores</h4>
                <p>Each yoga is assigned a strength score (0-100) based on planetary dignity, house support, aspect strength, and other classical factors. Higher scores indicate stronger, more reliable yogas.</p>
              </div>
              <div>
                <h4 className="font-semibold text-purple-400 mb-1">Categories</h4>
                <p>Yogas are categorized by their primary effect: Raja Yoga (power/authority), Dhana Yoga (wealth), Arishta Yoga (challenges), Chandra Yoga (emotional patterns), and more.</p>
              </div>
              <div>
                <h4 className="font-semibold text-purple-400 mb-1">Using Filters</h4>
                <p>Use the category tabs to filter by yoga type. Toggle Active Only to see only currently activated yogas. Use the Filters dropdown for benefic/malefic and strength thresholds.</p>
              </div>
              <div>
                <h4 className="font-semibold text-purple-400 mb-1">Detail View</h4>
                <p>Click any yoga card to view detailed analysis including formation rules, planet positions, strength breakdown, Dasha activation timeline, and classical references.</p>
              </div>
            </div>
            <button
              onClick={() => setShowHelp(false)}
              className="mt-6 w-full py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition"
            >
              Got it
            </button>
          </div>
        </div>
      )}
    </div>
  );
}