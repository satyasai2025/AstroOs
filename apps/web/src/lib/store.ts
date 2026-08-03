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
  BirthChartSummary,
  WorkflowAnalysisRequest,
  WorkflowAnalysisResponse,
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
  /**
   * Whether the "Create New Chart" modal is open. Lives here (not in
   * DashboardPage's local state) because the sidebar's "New Chart" link
   * is rendered by AppShell — a separate component tree with no direct
   * access to the dashboard page's state — and needs to be able to open
   * it too.
   */
  createModalOpen: boolean;
  openCreateModal: () => void;
  closeCreateModal: () => void;
  /**
   * The saved chart selected for a transit analysis. Lives here (not in
   * CreateTransitModal's local state) so the /transit/[reportId] page can
   * read it and build the correct transit request even when the workflow
   * store's active chart (result/request) is null or a different chart.
   */
  transitChart: BirthChartSummary | null;
  setTransitChart: (chart: BirthChartSummary | null) => void;
}

export const useWorkflowStore = create<WorkflowState>((set) => ({
  result: null,
  request: null,
  setResult: (result, request) => set({ result, request }),
  clear: () => set({ result: null, request: null, transitChart: null }),
  createModalOpen: false,
  openCreateModal: () => set({ createModalOpen: true }),
  closeCreateModal: () => set({ createModalOpen: false }),
  transitChart: null,
  setTransitChart: (chart) => set({ transitChart: chart }),
}));
