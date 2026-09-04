"use client";

import { useState } from "react";
import { api } from "@/lib/api";

interface IngestionResponse {
  ingested_cohort_id: string;
  cohort_tag: string;
  total_received: number;
  total_accepted: number;
  total_rejected: number;

  duplicates_detected: number;
  provenance_hash: string;
  calculated_charts: number;
  benchmark_results?: {
    technique_evaluated: string;
    sample_size: number;
    observed_success_rate: number;
    chi_square_statistic: number;
    p_value: number;
    is_statistically_significant: boolean;
    odds_ratio: number | null;
  } | null;
  rejection_summary: Array<{ event_id: string; reason: string; code: string }>;
}

export function CohortIngestionGateway() {
  const [cohortTag, setCohortTag] = useState("Empirical_Longevity_Study_2026");
  const [roddenThreshold, setRoddenThreshold] = useState("B");
  const [technique, setTechnique] = useState("marriage_timing");
  const [isIngesting, setIsIngesting] = useState(false);
  const [result, setResult] = useState<IngestionResponse | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  const handleSimulatedBatchIngest = async () => {
    setIsIngesting(true);
    setFeedback(null);

    // High quality empirical sample payload
    const mockPayload = {
      cohort_tag: cohortTag,
      cohort_description: "Automated empirical research cohort ingestion with full QC and deduplication",
      min_rodden_rating: roddenThreshold,
      hypothesis_technique: technique,
      auto_trigger_benchmark: true,
      raw_records: [
        {
          event_id: "EV-01",
          subject_id: "SUBJ-01",
          event_type: "marriage",
          actual_date: "2020-05-15",
          birth_datetime_utc: "1990-05-15T09:00:00Z",
          birth_latitude: 19.076,
          birth_longitude: 72.8777,
          birth_confidence: "AA",
          event_date_confidence: "exact_date",
          event_verification: "official_document",
        },
        {
          event_id: "EV-02",
          subject_id: "SUBJ-02",
          event_type: "marriage",
          actual_date: "2018-11-20",
          birth_datetime_utc: "1988-11-20T04:30:00Z",
          birth_latitude: 28.6139,
          birth_longitude: 77.209,
          birth_confidence: "A",
          event_date_confidence: "exact_date",
          event_verification: "official_document",
        },
        {
          event_id: "EV-03",
          subject_id: "SUBJ-03",
          event_type: "marriage",
          actual_date: "2015-02-14",
          birth_datetime_utc: "1985-03-21T00:45:00Z",
          birth_latitude: 19.076,
          birth_longitude: 72.8777,
          birth_confidence: "AA",
          event_date_confidence: "exact_date",
          event_verification: "official_document",
        },
        {
          event_id: "EV-04",
          subject_id: "SUBJ-04",
          event_type: "marriage",
          actual_date: "2021-12-10",
          birth_datetime_utc: "1995-03-08T15:15:00Z",
          birth_latitude: 12.9767,
          birth_longitude: 77.5901,
          birth_confidence: "B",
          event_date_confidence: "exact_date",
          event_verification: "official_document",
        },
        // Injected duplicate for QC audit verification
        {
          event_id: "EV-05",
          subject_id: "SUBJ-01",
          event_type: "marriage",
          actual_date: "2020-05-15",
          birth_datetime_utc: "1990-05-15T09:00:00Z",
          birth_latitude: 19.076,
          birth_longitude: 72.8777,
          birth_confidence: "AA",
          event_date_confidence: "exact_date",
          event_verification: "official_document",
        },
      ],
    };

    try {
      const data = await api.post<IngestionResponse>("/api/v1/research/cohort-ingest", mockPayload);
      setResult(data);
      setFeedback("Cohort ingestion and statistical benchmarking completed successfully!");
    } catch (err: unknown) {
      setFeedback(err instanceof Error ? err.message : "Ingestion gateway request failed.");
    } finally {
      setIsIngesting(false);
    }
  };

  return (
    <div className="rounded-2xl border p-5 glass-card mb-4" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-500/20 text-xs font-bold text-indigo-600">
              📥
            </span>
            <h2 className="text-base font-bold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
              Research Cohort Ingestion Gateway
            </h2>
          </div>
          <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
            Multi-tier QC, Rodden audit, duplicate deduplication, and direct statistical hypothesis testing
          </p>
        </div>

        <button
          type="button"
          onClick={handleSimulatedBatchIngest}
          disabled={isIngesting}
          className="rounded-lg px-4 py-2 text-xs font-bold transition-all disabled:opacity-50"
          style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
        >
          {isIngesting ? "Auditing & Ingesting Cohort…" : "Ingest & Benchmark Cohort"}
        </button>
      </div>

      {/* Configuration Controls Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-5">
        <div>
          <label className="block text-xs font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
            Cohort Identifier Tag:
          </label>
          <input 
            type="text"
            value={cohortTag}
            onChange={(e) => setCohortTag(e.target.value)}
            aria-label="Cohort Identifier Tag"
            className="w-full rounded-lg border px-3 py-1.5 text-xs outline-none"
            style={{
              borderColor: "var(--border-primary)",
              backgroundColor: "var(--bg-input)",
              color: "var(--text-primary)",
            }}
          />
        </div>

        <div>
          <label className="block text-xs font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
            Min Rodden Confidence:
          </label>
          <select
            value={roddenThreshold}
            onChange={(e) => setRoddenThreshold(e.target.value)}
            className="w-full rounded-lg border px-3 py-1.5 text-xs outline-none"
            style={{
              borderColor: "var(--border-primary)",
              backgroundColor: "var(--bg-input)",
              color: "var(--text-primary)",
            }}
          >
            <option value="AA">Grade AA (Birth Certificate In Hand)</option>
            <option value="A">Grade A (From Memory / Direct Quote)</option>
            <option value="B">Grade B (Biography / Published Source)</option>
            <option value="C">Grade C (Caution / Unverified Source)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
            Benchmark Hypothesis Technique:
          </label>
          <select
            value={technique}
            onChange={(e) => setTechnique(e.target.value)}
            className="w-full rounded-lg border px-3 py-1.5 text-xs outline-none"
            style={{
              borderColor: "var(--border-primary)",
              backgroundColor: "var(--bg-input)",
              color: "var(--text-primary)",
            }}
          >
            <option value="marriage_timing">Marriage Timing (7th Lord / Dasha)</option>
            <option value="wealth_dhana">Wealth &amp; Dhana Yogas (2nd/11th Lords)</option>
            <option value="gajakesari_yoga">Gajakesari Yoga (Jupiter-Moon Kendra)</option>
            <option value="panch_mahapurusha">Pancha Mahapurusha Yoga</option>
          </select>
        </div>
      </div>

      {feedback && (
        <div
          className="rounded-lg border p-3 text-xs font-medium mb-4"
          style={{
            borderColor: "var(--status-success)",
            backgroundColor: "rgba(34, 197, 94, 0.08)",
            color: "var(--status-success)",
          }}
        >
          {feedback}
        </div>
      )}

      {/* Results Matrix */}
      {result && (
        <div className="rounded-xl border p-4" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}>
          <div className="flex items-center justify-between mb-3 border-b pb-2" style={{ borderColor: "var(--border-primary)" }}>
            <span className="text-xs font-bold" style={{ color: "var(--text-primary)" }}>
              Ingestion QC Summary · <span className="font-mono text-cyan-400">{result.ingested_cohort_id}</span>
            </span>
            <span className="text-[11px] font-mono text-[var(--text-muted)]">
              SHA-256: {result.provenance_hash.slice(0, 16)}…
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
            <div className="rounded-lg border p-2.5 text-center" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
              <span className="text-[10px] text-[var(--text-muted)] block">SUBMITTED</span>
              <span className="text-base font-bold" style={{ color: "var(--text-primary)" }}>{result.total_received}</span>
            </div>
            <div className="rounded-lg border p-2.5 text-center" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
              <span className="text-[10px] text-[var(--text-muted)] block">QC ACCEPTED</span>
              <span className="text-base font-bold text-emerald-400">{result.total_accepted}</span>
            </div>
            <div className="rounded-lg border p-2.5 text-center" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
              <span className="text-[10px] text-[var(--text-muted)] block">DUPLICATES BLOCKED</span>
              <span className="text-base font-bold text-amber-400">{result.duplicates_detected}</span>
            </div>
            <div className="rounded-lg border p-2.5 text-center" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
              <span className="text-[10px] text-[var(--text-muted)] block">CALCULATED CHARTS</span>
              <span className="text-base font-bold text-cyan-400">{result.calculated_charts}</span>
            </div>
          </div>

          {/* Direct Benchmark Statistical Result */}
          {result.benchmark_results && (
            <div className="rounded-lg border p-3.5" style={{ borderColor: "var(--accent)", backgroundColor: "rgba(56, 189, 248, 0.05)" }}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold" style={{ color: "var(--text-primary)" }}>
                  Empirical Hypothesis Verdict: {result.benchmark_results.technique_evaluated}
                </span>
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${
                    result.benchmark_results.is_statistically_significant
                      ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
                      : "bg-amber-500/20 text-amber-400 border-amber-500/40"
                  }`}
                >
                  {result.benchmark_results.is_statistically_significant
                    ? "✓ Statistically Significant (p < 0.05)"
                    : "ℹ️ Baseline Equivalence"}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                <div>
                  <span className="text-[10px] text-[var(--text-muted)] block">Sample Size (N)</span>
                  <span className="font-semibold" style={{ color: "var(--text-primary)" }}>{result.benchmark_results.sample_size}</span>
                </div>
                <div>
                  <span className="text-[10px] text-[var(--text-muted)] block">Observed Success</span>
                  <span className="font-semibold text-emerald-400">{(result.benchmark_results.observed_success_rate * 100).toFixed(1)}%</span>
                </div>
                <div>
                  <span className="text-[10px] text-[var(--text-muted)] block">Chi-Square (χ²)</span>
                  <span className="font-semibold font-mono" style={{ color: "var(--text-primary)" }}>{result.benchmark_results.chi_square_statistic}</span>
                </div>
                <div>
                  <span className="text-[10px] text-[var(--text-muted)] block">Exact P-Value</span>
                  <span className="font-semibold font-mono text-cyan-400">{result.benchmark_results.p_value}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
