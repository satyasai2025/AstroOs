/**
 * Hook for computing and caching birth charts.
 */
import { useState, useCallback } from 'react';
import { api } from '../api/client';
import { cacheGet, cacheSet } from '../storage/offline';

interface BirthData {
  birth_datetime_utc: string;
  latitude: number;
  longitude: number;
  ayanamsa?: string;
  house_system?: string;
}

interface UseChartResult {
  chart: Record<string, unknown> | null;
  loading: boolean;
  error: string | null;
  fromCache: boolean;
  compute: (data: BirthData) => Promise<void>;
}

export function useChart(): UseChartResult {
  const [chart, setChart] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fromCache, setFromCache] = useState(false);

  const compute = useCallback(async (data: BirthData) => {
    setLoading(true);
    setError(null);
    setFromCache(false);

    const cacheKey = `chart:${data.birth_datetime_utc}:${data.latitude}:${data.longitude}:${data.ayanamsa ?? 'lahiri'}:${data.house_system ?? 'W'}`;

    try {
      // Try the API first
      const result = await api.computeChart(data);
      setChart(result as Record<string, unknown>);
      await cacheSet(cacheKey, result);
    } catch {
      // Offline — try cache
      const cached = await cacheGet<Record<string, unknown>>(cacheKey);
      if (cached) {
        setChart(cached);
        setFromCache(true);
      } else {
        setError('Unable to compute chart. No cached data available.');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  return { chart, loading, error, fromCache, compute };
}
