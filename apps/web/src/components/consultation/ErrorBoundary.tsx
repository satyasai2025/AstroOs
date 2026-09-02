"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
  fallbackMessage?: string;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ConsultationErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Astrological Visualization Error:", error, errorInfo);
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div
          role="alert"
          aria-live="assertive"
          className="bg-white dark:bg-slate-900 border border-rose-300 dark:border-rose-900/60 rounded-2xl p-6 text-center space-y-3 my-4 shadow-sm"
        >
          <div className="w-10 h-10 rounded-full bg-rose-100 dark:bg-rose-950/60 border border-rose-300 dark:border-rose-500/40 text-rose-600 dark:text-rose-400 flex items-center justify-center mx-auto text-lg">
            ⚠️
          </div>
          <h4 className="text-sm font-bold text-rose-700 dark:text-rose-300">
            {this.props.fallbackTitle || "Visualization Error"}
          </h4>
          <p className="text-xs text-slate-600 dark:text-slate-400 max-w-md mx-auto">
            {this.props.fallbackMessage ||
              "Unable to render this astrological calculation module due to an unexpected data format or calculation timeout."}
          </p>
          {this.state.error && (
            <div className="text-[10px] font-mono text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-slate-950 p-2 rounded-lg max-w-lg mx-auto overflow-x-auto border border-slate-200 dark:border-slate-800">
              {this.state.error.message}
            </div>
          )}
          <button
            type="button"
            onClick={this.handleRetry}
            className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 dark:bg-slate-800 dark:hover:bg-slate-700 text-white rounded-lg text-xs font-semibold transition cursor-pointer shadow-sm"
          >
            Retry Rendering
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export const DashboardErrorBoundary = ConsultationErrorBoundary;
