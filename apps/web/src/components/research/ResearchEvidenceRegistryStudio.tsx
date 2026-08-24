"use client";

import React, { useState, useEffect } from "react";

interface ObservedOutcomeRecord {
  outcome_id: string;
  subject_reference: string;
  domain: string;
  event_type: string;
  event_description: string;
  event_date: string;
  event_time?: string;
  event_timezone: string;
  timestamp_precision: string;
  observation_source_type: string;
  evidence_origin: string;
  verification_status: string;
  verification_method: string;
  verifier_reference: string;
  evidence_hash: string;
  source_hash: string;
  created_at: string;
  updated_at: string;
  prospective_rule_id?: string;
  experiment_id?: string;
  p11_snapshot_id?: string;
  provenance_parent?: string;
  consent_status: string;
  privacy_classification: string;
  notes: string;
  non_causal_disclosure: string;
}

interface EvidenceAuditEvent {
  audit_event_id: string;
  outcome_id: string;
  operation: string;
  previous_hash?: string;
  new_hash: string;
  actor_type: string;
  timestamp: string;
  reason: string;
  p11_snapshot_id?: string;
}

interface EvidenceRegistrySnapshot {
  snapshot_id: string;
  record_count: number;
  verified_record_count: number;
  rejected_record_count: number;
  unverified_record_count: number;
  source_distribution: Record<string, number>;
  domain_distribution: Record<string, number>;
  timestamp_precision_distribution: Record<string, number>;
  canonical_payload_hash: string;
  p11_parent_snapshot?: string;
  created_at: string;
  non_causal_disclosure: string;
  health_safety_disclosure: string;
}

const DEFAULT_RECORDS: ObservedOutcomeRecord[] = [
  {
    outcome_id: "out-default-01",
    subject_reference: "subj-anon-9901",
    domain: "MARRIAGE",
    event_type: "MARRIAGE_VERIFIED_DATE",
    event_description: "Civil marriage registration ceremony recorded",
    event_date: "2024-06-15",
    event_timezone: "UTC",
    timestamp_precision: "DAY",
    observation_source_type: "PARTICIPANT_DOCUMENT",
    evidence_origin: "OBSERVED_REAL_WORLD_EVIDENCE",
    verification_status: "INDEPENDENTLY_VERIFIED",
    verification_method: "CIVIL_REGISTRY_CERTIFICATE",
    verifier_reference: "GOV_RECORDS_REGISTRAR",
    evidence_hash: "7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a",
    source_hash: "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b",
    created_at: "2024-06-16T10:00:00Z",
    updated_at: "2024-06-16T10:00:00Z",
    prospective_rule_id: "hyp-m1",
    experiment_id: "exp-marriage-p20",
    p11_snapshot_id: "snap-p11-evidence-root",
    consent_status: "CONSENT_GRANTED",
    privacy_classification: "PSEUDONYMOUS_RESEARCH_DATA",
    notes: "Certificate verified by independent research auditor",
    non_causal_disclosure: "This registry records observed events and their verification provenance. An observed event does not establish astrological causation, predictive validity, or a physical mechanism.",
  },
  {
    outcome_id: "out-default-02",
    subject_reference: "subj-anon-8842",
    domain: "CAREER",
    event_type: "EXECUTIVE_APPOINTMENT",
    event_description: "Appointment as Vice President of Engineering verified",
    event_date: "2025-01-10",
    event_timezone: "UTC",
    timestamp_precision: "DAY",
    observation_source_type: "STRUCTURED_EXTERNAL_RECORD",
    evidence_origin: "OBSERVED_REAL_WORLD_EVIDENCE",
    verification_status: "DOCUMENTARY_VERIFIED",
    verification_method: "SEC_FILING_VERIFICATION",
    verifier_reference: "PUBLIC_REGULATORY_FILING",
    evidence_hash: "2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c",
    source_hash: "8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a",
    created_at: "2025-01-11T09:30:00Z",
    updated_at: "2025-01-11T09:30:00Z",
    experiment_id: "exp-career-founders",
    p11_snapshot_id: "snap-p11-evidence-root",
    consent_status: "CONSENT_GRANTED",
    privacy_classification: "PSEUDONYMOUS_RESEARCH_DATA",
    notes: "Public corporate filing verification",
    non_causal_disclosure: "This registry records observed events and their verification provenance. An observed event does not establish astrological causation, predictive validity, or a physical mechanism.",
  },
];

export const ResearchEvidenceRegistryStudio: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"overview" | "register" | "verification" | "realworld" | "audit" | "snapshots">("overview");
  const [records, setRecords] = useState<ObservedOutcomeRecord[]>(DEFAULT_RECORDS);
  const [auditLog, setAuditLog] = useState<EvidenceAuditEvent[]>([]);
  const [snapshots, setSnapshots] = useState<EvidenceRegistrySnapshot[]>([]);
  const [loading, setLoading] = useState(false);

  // Form State for Ingestion
  const [subjectRef, setSubjectRef] = useState("subj-anon-1042");
  const [domain, setDomain] = useState("MARRIAGE");
  const [eventType, setEventType] = useState("MARRIAGE_VERIFIED_DATE");
  const [eventDesc, setEventDesc] = useState("Verified wedding ceremony");
  const [eventDate, setEventDate] = useState("2025-05-20");
  const [precision, setPrecision] = useState("DAY");
  const [sourceType, setSourceType] = useState("PARTICIPANT_DOCUMENT");
  const [verStatus, setVerStatus] = useState("SELF_REPORTED");
  const [verMethod, setVerMethod] = useState("DOCUMENT_INSPECTION");
  const [notes, setNotes] = useState("Registered for P32 trial");
  const [formMsg, setFormMsg] = useState<{ text: string; error: boolean } | null>(null);

  const fetchEvidence = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/research/evidence");
      if (res.ok) {
        const data = await res.json();
        setRecords(data);
      }
      const snapRes = await fetch("/api/v1/research/evidence/snapshot/latest");
      if (snapRes.ok) {
        const snapData = await snapRes.json();
        setSnapshots([snapData]);
      }
    } catch (e) {
      console.warn("Failed to fetch live evidence, using fallback:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvidence();
  }, []);

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormMsg(null);
    try {
      const res = await fetch("/api/v1/research/evidence/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subject_reference: subjectRef,
          domain: domain,
          event_type: eventType,
          event_description: eventDesc,
          event_date: eventDate,
          timestamp_precision: precision,
          observation_source_type: sourceType,
          evidence_origin: "OBSERVED_REAL_WORLD_EVIDENCE",
          verification_status: verStatus,
          verification_method: verMethod,
          verifier_reference: "RESEARCH_OPERATOR",
          notes: notes,
        }),
      });

      if (res.ok) {
        const newRecord = await res.json();
        setRecords((prev) => [newRecord, ...prev]);
        setFormMsg({ text: `Observation '${newRecord.outcome_id}' registered successfully!`, error: false });
      } else {
        const errData = await res.json();
        setFormMsg({ text: errData.detail || "Registration failed.", error: true });
      }
    } catch (err: any) {
      setFormMsg({ text: err.message || "Registration failed.", error: true });
    }
  };

  const handleCreateSnapshot = async () => {
    try {
      const res = await fetch("/api/v1/research/evidence/snapshot", { method: "POST" });
      if (res.ok) {
        const snap = await res.json();
        setSnapshots((prev) => [snap, ...prev]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const totalObs = records.length;
  const verifiedObs = records.filter((r) => ["DOCUMENTARY_VERIFIED", "INDEPENDENTLY_VERIFIED"].includes(r.verification_status)).length;
  const indepObs = records.filter((r) => r.verification_status === "INDEPENDENTLY_VERIFIED").length;
  const selfObs = records.filter((r) => r.verification_status === "SELF_REPORTED").length;
  const rejectedObs = records.filter((r) => r.verification_status === "REJECTED").length;
  const unverifiedObs = records.filter((r) => r.verification_status === "UNVERIFIED").length;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <span className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-indigo-400 font-bold text-xl">
              📜
            </span>
            <h1 className="text-2xl font-bold tracking-tight">
              Priority 32: Research Evidence Intake & Real-World Outcome Registry
            </h1>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Governed intake layer for recording genuine real-world observations with append-only verification provenance and strict non-causal disclosures.
          </p>
        </div>
      </div>

      {/* Disclosures & Health Safety Banners */}
      <div className="space-y-2">
        <div className="p-3 rounded-xl bg-indigo-950/30 border border-indigo-500/30 text-xs text-indigo-300 font-mono flex items-start gap-2">
          <span className="text-indigo-400 font-bold shrink-0">⚖️</span>
          <div>
            This registry records observed events and their verification provenance. An observed event does not establish astrological causation, predictive validity, or a physical mechanism.
          </div>
        </div>
        <div className="p-3 rounded-xl bg-rose-950/30 border border-rose-500/30 text-xs text-rose-300 font-mono flex items-start gap-2">
          <span className="text-rose-400 font-bold shrink-0">🏥</span>
          <div>
            Health-related astrology is strictly an empirical inquiry into traditional vitality typologies and must NEVER be used for medical diagnosis, clinical prediction, treatment planning, or medical decision-making.
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-800 pb-2">
        {[
          { id: "overview", label: "📊 Evidence Overview" },
          { id: "register", label: "📝 Outcome Registration" },
          { id: "verification", label: "✅ Verification Hierarchy" },
          { id: "realworld", label: "🌍 Real-World Evidence Only" },
          { id: "audit", label: "📜 Append-Only Audit Trail" },
          { id: "snapshots", label: "🔐 Immutable Snapshots" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              activeTab === tab.id
                ? "bg-slate-800 text-indigo-400 border border-slate-700"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: EVIDENCE OVERVIEW */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
              <span className="text-xs text-slate-400 uppercase font-semibold">Total Observations</span>
              <div className="text-3xl font-extrabold text-white mt-1 font-mono">{totalObs}</div>
            </div>
            <div className="p-5 rounded-2xl bg-emerald-950/20 border border-emerald-500/30">
              <span className="text-xs text-emerald-400 uppercase font-semibold">Verified</span>
              <div className="text-3xl font-extrabold text-emerald-300 mt-1 font-mono">{verifiedObs}</div>
            </div>
            <div className="p-5 rounded-2xl bg-indigo-950/20 border border-indigo-500/30">
              <span className="text-xs text-indigo-400 uppercase font-semibold">Independently Verified</span>
              <div className="text-3xl font-extrabold text-indigo-300 mt-1 font-mono">{indepObs}</div>
            </div>
            <div className="p-5 rounded-2xl bg-amber-950/20 border border-amber-500/30">
              <span className="text-xs text-amber-400 uppercase font-semibold">Self-Reported</span>
              <div className="text-3xl font-extrabold text-amber-300 mt-1 font-mono">{selfObs}</div>
            </div>
            <div className="p-5 rounded-2xl bg-rose-950/20 border border-rose-500/30">
              <span className="text-xs text-rose-400 uppercase font-semibold">Rejected</span>
              <div className="text-3xl font-extrabold text-rose-300 mt-1 font-mono">{rejectedObs}</div>
            </div>
            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
              <span className="text-xs text-slate-400 uppercase font-semibold">Unverified</span>
              <div className="text-3xl font-extrabold text-slate-300 mt-1 font-mono">{unverifiedObs}</div>
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h3 className="text-base font-bold text-white">Recent Real-World Outcome Registrations</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase font-semibold">
                    <th className="py-2.5 px-3">Outcome ID</th>
                    <th className="py-2.5 px-3">Native Ref</th>
                    <th className="py-2.5 px-3">Domain</th>
                    <th className="py-2.5 px-3">Event Date</th>
                    <th className="py-2.5 px-3">Verification Status</th>
                    <th className="py-2.5 px-3">Evidence Hash</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {records.map((r) => (
                    <tr key={r.outcome_id} className="hover:bg-slate-900/40">
                      <td className="py-2.5 px-3 text-indigo-400 font-bold">{r.outcome_id}</td>
                      <td className="py-2.5 px-3 text-slate-300">{r.subject_reference}</td>
                      <td className="py-2.5 px-3 text-slate-300 font-sans">{r.domain}</td>
                      <td className="py-2.5 px-3 text-slate-300">{r.event_date}</td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] ${
                            r.verification_status === "INDEPENDENTLY_VERIFIED"
                              ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                              : r.verification_status === "DOCUMENTARY_VERIFIED"
                              ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/30"
                              : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                          }`}
                        >
                          {r.verification_status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-400 text-[10px]">{r.evidence_hash.slice(0, 16)}…</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: OUTCOME REGISTRATION */}
      {activeTab === "register" && (
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-6 max-w-3xl">
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-white">Ingest Real-World Outcome Observation</h3>
            <p className="text-xs text-slate-400">
              Recording an observation does not establish causation or predictive validity. Input parameters are hashed canonically.
            </p>
          </div>

          {formMsg && (
            <div className={`p-3 rounded-xl text-xs font-mono border ${formMsg.error ? "bg-rose-950/40 border-rose-500/30 text-rose-300" : "bg-emerald-950/40 border-emerald-500/30 text-emerald-300"}`}>
              {formMsg.text}
            </div>
          )}

          <form onSubmit={handleRegisterSubmit} className="space-y-4 text-xs font-sans">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-slate-300 mb-1">Native Reference (Pseudonymous)</label>
                <input
                  type="text"
                  value={subjectRef}
                  onChange={(e) => setSubjectRef(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:border-indigo-500 font-mono"
                  required
                />
              </div>
              <div>
                <label className="block text-slate-300 mb-1">Domain</label>
                <select
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:border-indigo-500"
                >
                  <option value="MARRIAGE">MARRIAGE</option>
                  <option value="CAREER">CAREER</option>
                  <option value="WEALTH_FINANCE">WEALTH_FINANCE</option>
                  <option value="HEALTH_VITALITY">HEALTH_VITALITY (Vitality Typologies Only)</option>
                  <option value="EDUCATION">EDUCATION</option>
                  <option value="RELOCATION">RELOCATION</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-slate-300 mb-1">Event Type</label>
                <input
                  type="text"
                  value={eventType}
                  onChange={(e) => setEventType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:border-indigo-500 font-mono"
                  required
                />
              </div>
              <div>
                <label className="block text-slate-300 mb-1">Event Date (YYYY-MM-DD)</label>
                <input
                  type="text"
                  value={eventDate}
                  onChange={(e) => setEventDate(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:border-indigo-500 font-mono"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-slate-300 mb-1">Event Description</label>
              <textarea
                value={eventDesc}
                onChange={(e) => setEventDesc(e.target.value)}
                rows={2}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:border-indigo-500"
                required
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-slate-300 mb-1">Timestamp Precision</label>
                <select
                  value={precision}
                  onChange={(e) => setPrecision(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:border-indigo-500"
                >
                  <option value="EXACT">EXACT</option>
                  <option value="DAY">DAY</option>
                  <option value="MONTH">MONTH</option>
                  <option value="YEAR">YEAR</option>
                  <option value="APPROXIMATE">APPROXIMATE</option>
                </select>
              </div>
              <div>
                <label className="block text-slate-300 mb-1">Source Type</label>
                <select
                  value={sourceType}
                  onChange={(e) => setSourceType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:border-indigo-500"
                >
                  <option value="PARTICIPANT_SELF_REPORT">PARTICIPANT_SELF_REPORT</option>
                  <option value="PARTICIPANT_DOCUMENT">PARTICIPANT_DOCUMENT</option>
                  <option value="INDEPENDENT_DOCUMENT">INDEPENDENT_DOCUMENT</option>
                  <option value="STRUCTURED_EXTERNAL_RECORD">STRUCTURED_EXTERNAL_RECORD</option>
                </select>
              </div>
              <div>
                <label className="block text-slate-300 mb-1">Verification Status</label>
                <select
                  value={verStatus}
                  onChange={(e) => setVerStatus(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:border-indigo-500"
                >
                  <option value="SELF_REPORTED">SELF_REPORTED</option>
                  <option value="DOCUMENTARY_VERIFIED">DOCUMENTARY_VERIFIED</option>
                  <option value="INDEPENDENTLY_VERIFIED">INDEPENDENTLY_VERIFIED</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-5 py-2.5 rounded-lg text-sm transition shadow-lg shadow-indigo-600/20"
            >
              Register Real-World Outcome Record
            </button>
          </form>
        </div>
      )}

      {/* TAB 3: VERIFICATION HIERARCHY */}
      {activeTab === "verification" && (
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h3 className="text-base font-bold text-white">Verification Status & Provenance Hierarchy</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase font-semibold">
                  <th className="py-2.5 px-3">Outcome ID</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Method</th>
                  <th className="py-2.5 px-3">Verifier Ref</th>
                  <th className="py-2.5 px-3">Source Hash</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {records.map((r) => (
                  <tr key={r.outcome_id} className="hover:bg-slate-900/40">
                    <td className="py-2.5 px-3 text-indigo-400 font-bold">{r.outcome_id}</td>
                    <td className="py-2.5 px-3">
                      <span className="text-emerald-400 font-bold">{r.verification_status}</span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-300 font-sans">{r.verification_method}</td>
                    <td className="py-2.5 px-3 text-slate-300">{r.verifier_reference}</td>
                    <td className="py-2.5 px-3 text-slate-500 text-[10px]">{r.source_hash.slice(0, 20)}…</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 4: REAL-WORLD EVIDENCE ONLY */}
      {activeTab === "realworld" && (
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white">Strict Filter: OBSERVED_REAL_WORLD_EVIDENCE</h3>
            <span className="px-3 py-1 bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 rounded-full text-xs font-mono">
              Synthetic Evidence Excluded
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs font-mono">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase font-semibold">
                  <th className="py-2.5 px-3">Outcome ID</th>
                  <th className="py-2.5 px-3">Origin</th>
                  <th className="py-2.5 px-3">Native Ref</th>
                  <th className="py-2.5 px-3">Domain</th>
                  <th className="py-2.5 px-3">Event Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {records
                  .filter((r) => r.evidence_origin === "OBSERVED_REAL_WORLD_EVIDENCE")
                  .map((r) => (
                    <tr key={r.outcome_id} className="hover:bg-slate-900/40">
                      <td className="py-2.5 px-3 text-indigo-400 font-bold">{r.outcome_id}</td>
                      <td className="py-2.5 px-3">
                        <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded text-[10px]">
                          {r.evidence_origin}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-300">{r.subject_reference}</td>
                      <td className="py-2.5 px-3 text-slate-300 font-sans">{r.domain}</td>
                      <td className="py-2.5 px-3 text-slate-300">{r.event_date}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 5: AUDIT TRAIL */}
      {activeTab === "audit" && (
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h3 className="text-base font-bold text-white">Append-Only Mutation Audit Trail</h3>
          <div className="space-y-3 font-mono text-xs">
            {records.map((r) => (
              <div key={r.outcome_id} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <div className="flex items-center justify-between text-indigo-400 font-bold">
                  <span>CREATED — {r.outcome_id}</span>
                  <span className="text-slate-500 text-[10px]">{r.created_at}</span>
                </div>
                <div className="text-slate-400 text-[11px]">
                  New Content Hash: <span className="text-slate-200">{r.evidence_hash}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 6: SNAPSHOTS */}
      {activeTab === "snapshots" && (
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white">Immutable Evidence Registry Snapshots</h3>
            <button
              onClick={handleCreateSnapshot}
              className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-4 py-2 rounded-lg text-xs transition"
            >
              Generate New Snapshot
            </button>
          </div>
          <div className="space-y-3 font-mono text-xs">
            {snapshots.map((s) => (
              <div key={s.snapshot_id} className="p-5 rounded-2xl bg-slate-950 border border-indigo-500/30 space-y-2">
                <div className="flex items-center justify-between text-indigo-300 font-bold text-sm">
                  <span>{s.snapshot_id}</span>
                  <span className="text-slate-400 text-xs">{s.created_at}</span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-slate-300 text-[11px] font-sans">
                  <div>Records: <span className="font-mono text-white">{s.record_count}</span></div>
                  <div>Verified: <span className="font-mono text-emerald-400">{s.verified_record_count}</span></div>
                  <div>Rejected: <span className="font-mono text-rose-400">{s.rejected_record_count}</span></div>
                  <div>Unverified: <span className="font-mono text-amber-400">{s.unverified_record_count}</span></div>
                </div>
                <div className="text-[10px] text-slate-400 break-all">
                  Canonical SHA-256 Hash: <span className="text-indigo-300">{s.canonical_payload_hash}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
