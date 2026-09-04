"use client";

import React, { useState, useEffect } from "react";

export interface CandidateProfile {
  profile_id: string;
  name: string;
  description: string;
  dataset_id: string;
  status: "DRAFT_CANDIDATE" | "ACTIVE";
  technique_weights: Record<string, number>;
  primary_brier_score: number;
  primary_log_loss: number;
  diagnostic_f1: number;
  diagnostic_roc_auc: number | null;
  roc_auc_status: string;
  created_at: string;
  activated_at?: string | null;
  activated_by?: string | null;
}

export interface AuditRecord {
  audit_id: string;
  timestamp: string;
  dataset_id: string;
  dataset_version: string;
  event_type: string;
  train_events_count: number;
  holdout_events_count: number;
  primary_brier_score: number;
  primary_log_loss: number;
  diagnostic_f1: number;
  diagnostic_roc_auc: number | null;
  roc_auc_status: string;
  candidate_profile_id: string;
  status: string;
  action: string;
  notes: string;
}

export function BacktestCalibrationDashboard() {
  const [profiles, setProfiles] = useState<CandidateProfile[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditRecord[]>([]);
  const [activeTab, setActiveTab] = useState<"profiles" | "audit">("profiles");

  // Form states for creating a new candidate draft
  const [profileName, setProfileName] = useState<string>("Candidate Calibration Profile v1");
  const [datasetId, setDatasetId] = useState<string>("ds-marriage-benchmark-01");
  const [brierScore, setBrierScore] = useState<number>(0.042);
  const [logLoss, setLogLoss] = useState<number>(0.135);
  const [f1Score, setF1Score] = useState<number>(0.875);
  const [rocAuc, setRocAuc] = useState<number>(0.920);

  useEffect(() => {
    fetchProfiles();
    fetchAuditLogs();
  }, []);

  const fetchProfiles = async () => {
    try {
      const res = await fetch("/api/v1/research/calibration/profiles");
      if (res.ok) {
        const data = await res.json();
        setProfiles(data);
      }
    } catch {
      // offline fallback
    }
  };

  const fetchAuditLogs = async () => {
    try {
      const res = await fetch("/api/v1/research/calibration/audit-trail");
      if (res.ok) {
        const data = await res.json();
        setAuditLogs(data);
      }
    } catch {
      // offline fallback
    }
  };

  const handleCreateCandidateDraft = async () => {
    try {
      const res = await fetch("/api/v1/research/calibration/profiles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: profileName,
          description: "User generated empirical weight profile draft",
          dataset_id: datasetId,
          technique_weights: {
            chara_dasha_v1: 0.85,
            vimshottari_v1: 0.70,
            argala_obstruction_v1: 0.90,
          },
          holdout_brier_score: brierScore,
          holdout_log_loss: logLoss,
          diagnostic_f1: f1Score,
          diagnostic_roc_auc: rocAuc,
          roc_auc_status: "VALID",
        }),
      });

      if (res.ok) {
        fetchProfiles();
        fetchAuditLogs();
        alert("Draft candidate profile created with status: DRAFT_CANDIDATE!");
      }
    } catch (err: any) {
      alert(`Error creating draft profile: ${err.message}`);
    }
  };

  const handleActivateProfile = async (profileId: string) => {
    try {
      const res = await fetch(`/api/v1/research/calibration/profiles/${profileId}/activate`, {
        method: "POST",
      });
      if (res.ok) {
        fetchProfiles();
        fetchAuditLogs();
        alert(`Candidate profile '${profileId}' explicitly activated!`);
      }
    } catch (err: any) {
      alert(`Error activating profile: ${err.message}`);
    }
  };

  return (
    <div className="w-full max-w-7xl mx-auto p-6 bg-slate-900 text-slate-100 rounded-xl shadow-2xl border border-slate-800 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              Priority 10 Engine
            </span>
            <h2 className="text-2xl font-bold tracking-tight text-white">
              Autonomous Backtesting & Dynamic Weight Calibration
            </h2>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Primary Brier Score & Log-Loss calibration with diagnostic F1/ROC-AUC, draft candidate profiles, and immutable audit logs.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center space-x-2 bg-slate-950 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setActiveTab("profiles")}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              activeTab === "profiles"
                ? "bg-indigo-600 text-white shadow-md"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Candidate Profiles ({profiles.length})
          </button>
          <button
            onClick={() => setActiveTab("audit")}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              activeTab === "audit"
                ? "bg-indigo-600 text-white shadow-md"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Immutable Audit Log ({auditLogs.length})
          </button>
        </div>
      </div>

      {activeTab === "profiles" ? (
        <div className="space-y-6">
          {/* Create Draft Candidate Profile Form */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-4">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300 border-b border-slate-800 pb-2">
              Generate New Draft Candidate Weight Profile
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Profile Name</label>
                <input
                  type="text"
                  value={profileName}
                  onChange={(e) => setProfileName(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-1.5 text-xs text-white"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Dataset ID</label>
                <input
                  type="text"
                  value={datasetId}
                  onChange={(e) => setDatasetId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-1.5 text-xs text-white"
                />
              </div>
              <div>
                <label className="block text-xs text-emerald-400 mb-1">Primary Brier Score</label>
                <input
                  type="number"
                  step="0.001"
                  value={brierScore}
                  onChange={(e) => setBrierScore(parseFloat(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-1.5 text-xs text-emerald-300 font-mono"
                />
              </div>
              <div>
                <label className="block text-xs text-emerald-400 mb-1">Primary Log Loss</label>
                <input
                  type="number"
                  step="0.001"
                  value={logLoss}
                  onChange={(e) => setLogLoss(parseFloat(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-1.5 text-xs text-emerald-300 font-mono"
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-2">
              <span className="text-xs text-slate-500">
                Note: Candidate weight profiles are ALWAYS saved as <strong className="text-amber-400">DRAFT_CANDIDATE</strong> and require explicit user activation.
              </span>
              <button
                onClick={handleCreateCandidateDraft}
                className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 text-xs font-semibold rounded-lg shadow transition-colors"
              >
                Create Draft Candidate Profile
              </button>
            </div>
          </div>

          {/* List of Candidate Profiles */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {profiles.map((p) => (
              <div
                key={p.profile_id}
                className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-3 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <h2 className="font-bold text-white text-base">{p.name}</h2>
                  <span
                    className={`text-xs px-2.5 py-0.5 rounded-full font-mono font-semibold ${
                      p.status === "ACTIVE"
                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                        : "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                    }`}
                  >
                    {p.status}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs font-mono bg-slate-900 p-3 rounded border border-slate-800/80">
                  <div>
                    <span className="text-slate-400">Primary Brier:</span>{" "}
                    <strong className="text-emerald-400">{p.primary_brier_score}</strong>
                  </div>
                  <div>
                    <span className="text-slate-400">Primary Log Loss:</span>{" "}
                    <strong className="text-emerald-400">{p.primary_log_loss}</strong>
                  </div>
                  <div>
                    <span className="text-slate-400">Diagnostic F1:</span>{" "}
                    <strong className="text-indigo-400">{p.diagnostic_f1}</strong>
                  </div>
                  <div>
                    <span className="text-slate-400">ROC-AUC:</span>{" "}
                    <strong className="text-indigo-400">
                      {p.diagnostic_roc_auc !== null ? p.diagnostic_roc_auc : "N/A (" + p.roc_auc_status + ")"}
                    </strong>
                  </div>
                </div>

                {p.status === "DRAFT_CANDIDATE" && (
                  <button
                    onClick={() => handleActivateProfile(p.profile_id)}
                    className="w-full bg-emerald-600 hover:bg-emerald-500 text-white py-2 text-xs font-semibold rounded-lg shadow-lg transition-colors"
                  >
                    Explicitly Activate Candidate Profile
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      ) : (
        /* Immutable Audit Trail Log Table */
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-white">Immutable Calibration Audit Trail</h2>
          <div className="overflow-x-auto bg-slate-950 border border-slate-800 rounded-xl">
            <table className="w-full text-left text-xs text-slate-300 font-mono">
              <thead className="bg-slate-900 text-slate-400 uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">Audit ID</th>
                  <th className="px-4 py-3">Timestamp</th>
                  <th className="px-4 py-3">Action</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Brier Score</th>
                  <th className="px-4 py-3">Log Loss</th>
                  <th className="px-4 py-3">ROC-AUC Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {auditLogs.map((log) => (
                  <tr key={log.audit_id} className="hover:bg-slate-900/50">
                    <td className="px-4 py-3 text-indigo-400 font-bold">{log.audit_id}</td>
                    <td className="px-4 py-3 text-slate-400">{log.timestamp.slice(0, 19)}</td>
                    <td className="px-4 py-3 text-slate-200">{log.action}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] ${
                          log.status === "ACTIVE"
                            ? "bg-emerald-500/20 text-emerald-400"
                            : "bg-amber-500/20 text-amber-400"
                        }`}
                      >
                        {log.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-emerald-400">{log.primary_brier_score}</td>
                    <td className="px-4 py-3 text-emerald-400">{log.primary_log_loss}</td>
                    <td className="px-4 py-3 text-indigo-300">{log.roc_auc_status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
