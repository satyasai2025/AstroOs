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
  /**
   * Which chart type the modal should jump straight into when opened,
   * skipping the "choose a type" step — e.g. the compatibility report
   * page's "Check Another Compatibility" button sets this to
   * "compatibility" before navigating back to /dashboard, so the modal
   * is already on the compatibility form rather than the type picker.
   * Matches CreateChartModal's ChartTypeId values; null means "let the
   * user choose" (the plain "New Chart" flow).
   */
  createModalInitialType: string | null;
  openCreateModal: (initialType?: string) => void;
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
  createModalInitialType: null,
  openCreateModal: (initialType) => set({ createModalOpen: true, createModalInitialType: initialType ?? null }),
  closeCreateModal: () => set({ createModalOpen: false, createModalInitialType: null }),
  transitChart: null,
  setTransitChart: (chart) => set({ transitChart: chart }),
}));
