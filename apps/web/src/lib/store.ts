/**
 * AstroOS — Global Client-Side Store (Zustand)
 *
 * Holds the most recent workflow analysis result so that the /charts
 * pages can display it without re-running the analysis. This is a
 * client-side-only in-memory store — not persisted to disk.
 */

"use client";

import { create } from "zustand";
import type {
  WorkflowAnalysisResponse,
  WorkflowAnalysisRequest,
} from "./types";

interface WorkflowState {
  /** The last successful analysis result, if any. */
  result: WorkflowAnalysisResponse | null;
  /** The request that produced `result`. */
  request: WorkflowAnalysisRequest | null;
  /** Set both together. */
  setResult: (
    result: WorkflowAnalysisResponse,
    request: WorkflowAnalysisRequest,
  ) => void;
  /** Clear everything. */
  clear: () => void;
}

export const useWorkflowStore = create<WorkflowState>((set) => ({
  result: null,
  request: null,
  setResult: (result, request) => set({ result, request }),
  clear: () => set({ result: null, request: null }),
}));
