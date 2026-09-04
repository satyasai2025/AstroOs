/** SavedComparisonsManager - Handles persistence of comparison sets */
'use client';

import { useState, useEffect, useCallback } from 'react';

export interface SavedComparison {
  id: string;
  name: string;
  charts: string[];
  comparisonType: string;
  userNotes: string;
  aiSummary: string;
  createdAt: string;
  modifiedAt: string;
  pinned: boolean;
}

const STORAGE_KEY = 'astroos_saved_comparisons';

function persist(comparisons: SavedComparison[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(comparisons));
  } catch (e) {
    console.error('Failed to save comparisons:', e);
  }
}

export function useSavedComparisons() {
  const [savedComparisons, setSavedComparisons] = useState<SavedComparison[]>([]);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        setSavedComparisons(JSON.parse(stored));
      }
    } catch (e) {
      console.error('Failed to load saved comparisons:', e);
    } finally {
      setIsLoaded(true);
    }
  }, []);

  const saveComparison = useCallback((comparison: Omit<SavedComparison, 'id' | 'createdAt' | 'modifiedAt'>) => {
    const newComparison: SavedComparison = {
      ...comparison,
      id: Date.now().toString(),
      createdAt: new Date().toISOString(),
      modifiedAt: new Date().toISOString(),
    };
    setSavedComparisons((prev) => {
      const updated = [newComparison, ...prev];
      persist(updated);
      return updated;
    });
    return newComparison;
  }, []);

  const updateComparison = useCallback((id: string, updates: Partial<SavedComparison>) => {
    setSavedComparisons((prev) => {
      const updated = prev.map((c) =>
        c.id === id ? { ...c, ...updates, modifiedAt: new Date().toISOString() } : c,
      );
      persist(updated);
      return updated;
    });
  }, []);

  const deleteComparison = useCallback((id: string) => {
    setSavedComparisons((prev) => {
      const updated = prev.filter((c) => c.id !== id);
      persist(updated);
      return updated;
    });
  }, []);

  const togglePin = useCallback((id: string) => {
    setSavedComparisons((prev) => {
      const target = prev.find((c) => c.id === id);
      if (!target) return prev;
      const updated = prev.map((c) =>
        c.id === id ? { ...c, pinned: !target.pinned, modifiedAt: new Date().toISOString() } : c,
      );
      persist(updated);
      return updated;
    });
  }, []);

  const reorderComparisons = useCallback((newOrder: SavedComparison[]) => {
    setSavedComparisons(newOrder);
    persist(newOrder);
  }, []);

  return {
    savedComparisons,
    isLoaded,
    saveComparison,
    updateComparison,
    deleteComparison,
    togglePin,
    reorderComparisons,
  };
}
