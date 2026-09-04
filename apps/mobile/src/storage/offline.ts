/**
 * AstroOS Mobile — Offline Storage
 *
 * SQLite-based cache for chart computations. When the user computes a chart
 * online, the result is cached locally. When offline, cached results are
 * served from the local store.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Config } from '../config';

const CACHE_PREFIX = '@astroos/cache/';

interface CacheEntry<T = unknown> {
  key: string;
  data: T;
  cachedAt: number; // unix timestamp
  ttl: number;      // seconds
}

function isExpired(entry: CacheEntry): boolean {
  return Date.now() / 1000 - entry.cachedAt > entry.ttl;
}

/**
 * Store a value in the offline cache.
 */
export async function cacheSet<T>(key: string, data: T, ttl?: number): Promise<void> {
  const entry: CacheEntry<T> = {
    key,
    data,
    cachedAt: Math.floor(Date.now() / 1000),
    ttl: ttl ?? Config.cacheTtlSeconds,
  };
  await AsyncStorage.setItem(CACHE_PREFIX + key, JSON.stringify(entry));
}

/**
 * Retrieve a value from the offline cache.
 * Returns null if the key doesn't exist or the entry has expired.
 */
export async function cacheGet<T>(key: string): Promise<T | null> {
  try {
    const raw = await AsyncStorage.getItem(CACHE_PREFIX + key);
    if (!raw) return null;
    const entry: CacheEntry<T> = JSON.parse(raw);
    if (isExpired(entry)) {
      await AsyncStorage.removeItem(CACHE_PREFIX + key);
      return null;
    }
    return entry.data;
  } catch {
    return null;
  }
}

/**
 * Clear all cached entries.
 */
export async function cacheClear(): Promise<void> {
  const keys = await AsyncStorage.getAllKeys();
  const cacheKeys = keys.filter((k) => k.startsWith(CACHE_PREFIX));
  await AsyncStorage.multiRemove(cacheKeys);
}

/**
 * Get the number of cached entries.
 */
export async function cacheSize(): Promise<number> {
  const keys = await AsyncStorage.getAllKeys();
  return keys.filter((k) => k.startsWith(CACHE_PREFIX)).length;
}
