'use client';

import React, { useState, useMemo } from 'react';
import {
  YogaResultResponse,
  YogaDefinitionResponse,
  YogaActivationResponse,
  WorkflowAnalysisRequest,
} from '@/lib/types';
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

/** Derive the YogaEngine birth-data body from the workflow request. */
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

/** Benefic/malefic is not a field on the API — derive it from the knowledge
 *  base tags (BPHS tags each yoga benefic / malefic / dosha). */
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

  const { data: catalogData, isLoading: catalogLoading } = useYogaCatalog();
  const catalog = catalogData?.yogas ?? [];

  // Strength + timeline enrichment — real backend data via the dedicated
  // /yoga/evaluate/with-strength and /yoga/evaluate/timeline endpoints.
  const evalBody = toYogaEvaluationRequest(request);
  const { data: strengthData } = useYogaStrengthEvaluation(evalBody ?? null, { presentOnly: false });
  const { data: timelineData } = useYogaTimelineEvaluation(evalBody ?? null);

  // Lookup maps.
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

  // Enrich each workflow result with strength (0-100) + definition lookup.
  const enrichedYogas: YogaResultResponse[] = useMemo(() => {
    return rawYogas.map((y) => {
      const s = strengthByYogaId.get(y.yoga_id);
      return s !== undefined ? { ...y, strength_score: s } : y;
    });
  }, [rawYogas, strengthByYogaId]);

  const hasYogaData = enrichedYogas.length > 0;

  // Category counts.
  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = { all: enrichedYogas.length };
    enrichedYogas.forEach((yoga) => {
      const category = catalog.find((d) => d.yoga_id === yoga.yoga_id)?.category || 'Others';
      counts[category] = (counts[category] || 0) + 1;
    });
    return counts;
  }, [enrichedYogas, catalog]);

  // Available categories.
  const categories = useMemo(() => {
    const set = new Set<string>();
    catalog.forEach((d) => d.category && set.add(d.category));
    return Array.from(set).sort();
  }, [catalog]);

  // Filter & sort.
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

  return (
    <div className="h-full flex flex-col">
      {/* Filter toolbar */}
      <div className="border-b border-gray-800 bg-gray-900/50 p-4">
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
        />
      </div>

      {/* Two-panel layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left list */}
        <div className="w-96 border-r border-gray-800 overflow-y-auto bg-gray-900/30">
          {catalogLoading && enrichedYogas.length === 0 ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500" />
            </div>
          ) : !hasYogaData ? (
            <div className="flex items-center justify-center h-64 p-6 text-center">
              <div>
                <p className="text-sm text-gray-400">No yoga analysis available</p>
                <p className="text-xs text-gray-500 mt-2">Run a chart analysis to detect yogas</p>
              </div>
            </div>
          ) : filteredYogas.length === 0 ? (
            <div className="flex items-center justify-center h-64 p-6 text-center">
              <div>
                <p className="text-sm text-gray-400">No yogas match your filters</p>
                {hasActiveFilters && (
                  <button onClick={clearFilters} className="mt-3 text-xs text-purple-400 hover:text-purple-300">
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

        {/* Right detail */}
        <div className="flex-1 overflow-hidden bg-gray-950">
          {selectedYoga ? (
            <YogaDetailPanel
              yoga={selectedYoga}
              definition={selectedDefinition}
              activations={activeTimeline?.activations ?? []}
              currentActivation={activeTimeline?.current ?? null}
              dashaSystem={timelineData?.dasha_system}
            />
          ) : (
            <div className="h-full flex items-center justify-center text-gray-400">
              <div className="text-center p-8">
                <p className="text-lg mb-2">Yoga Intelligence Dashboard</p>
                <p className="text-sm opacity-75 max-w-md">
                  Select a yoga from the list to view detailed analysis including strength breakdown,
                  formation rules, planet positions, and Dasha activation timeline.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}