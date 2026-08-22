"use client";

import { useState, useEffect } from "react";
import {
  generatePairingSession,
  listPairedDevices,
  revokePairedDevice,
  getSyncStatus,
  listSyncConflicts,
  type PairingGenerateResponse,
  type PairedDevice,
  type SyncStatusResponse,
  type SyncConflictItem,
} from "@/lib/mobileSync";

export function MobileSyncHub() {
  const [pairingSession, setPairingSession] = useState<PairingGenerateResponse | null>(null);
  const [devices, setDevices] = useState<PairedDevice[]>([]);
  const [status, setStatus] = useState<SyncStatusResponse | null>(null);
  const [conflicts, setConflicts] = useState<SyncConflictItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState<boolean>(false);
  const [timeLeft, setTimeLeft] = useState<number>(0);

  const refreshData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [devRes, statRes, confRes] = await Promise.all([
        listPairedDevices(),
        getSyncStatus(),
        listSyncConflicts(),
      ]);
      setDevices(devRes.devices);
      setStatus(statRes);
      setConflicts(confRes.conflicts);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load sync status.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshData();
  }, []);

  // Timer countdown for ephemeral pairing
  useEffect(() => {
    if (!pairingSession) return;
    const expiresAt = new Date(pairingSession.expires_at_iso).getTime();

    const interval = setInterval(() => {
      const remaining = Math.max(0, Math.floor((expiresAt - Date.now()) / 1000));
      setTimeLeft(remaining);
      if (remaining <= 0) {
        clearInterval(interval);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [pairingSession]);

  const handleGeneratePairing = async () => {
    try {
      setGenerating(true);
      setError(null);
      const session = await generatePairingSession();
      setPairingSession(session);
      setTimeLeft(session.ttl_seconds);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to initiate pairing session.");
    } finally {
      setGenerating(false);
    }
  };

  const handleRevokeDevice = async (deviceId: string) => {
    if (!confirm(`Revoke device ${deviceId}? It will immediately be blocked from local synchronization.`)) {
      return;
    }
    try {
      await revokePairedDevice(deviceId);
      await refreshData();
    } catch (err: unknown) {
      alert(`Revocation failed: ${err instanceof Error ? err.message : "Unknown error"}`);
    }
  };

  return (
    <div className="space-y-6" data-testid="mobile-sync-hub">
      {/* 1. Header & Quick Status */}
      <div className="p-6 rounded-2xl border glass-card border-zinc-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              LOCAL-FIRST LAN SYNC
            </span>
            <span className="text-xs text-zinc-400">• Zero Cloud Relay</span>
          </div>
          <h2 className="text-xl font-bold text-zinc-100 mt-2">Mobile Client Synchronization Hub</h2>
          <p className="text-xs text-zinc-400 mt-1">
            Pair React Native mobile devices securely over your local Wi-Fi network for offline-first chart and research synchronization.
          </p>
        </div>

        <button
          onClick={refreshData}
          disabled={loading}
          className="px-3 py-1.5 rounded-xl bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-xs font-medium text-zinc-300 transition"
        >
          {loading ? "Refreshing…" : "↻ Refresh Ledger"}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-xs text-red-300">
          {error}
        </div>
      )}

      {/* 2. Sync Ledger Metrics Grid */}
      {status && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800">
            <span className="text-[10px] uppercase text-zinc-400 font-bold">Server Cursor</span>
            <div className="text-lg font-mono font-bold text-cyan-400 mt-1">#{status.server_cursor}</div>
          </div>
          <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800">
            <span className="text-[10px] uppercase text-zinc-400 font-bold">Synced Entities</span>
            <div className="text-lg font-mono font-bold text-zinc-200 mt-1">{status.total_entities}</div>
          </div>
          <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800">
            <span className="text-[10px] uppercase text-zinc-400 font-bold">Paired Devices</span>
            <div className="text-lg font-mono font-bold text-emerald-400 mt-1">{status.active_paired_devices}</div>
          </div>
          <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800">
            <span className="text-[10px] uppercase text-zinc-400 font-bold">Conflict Ledger</span>
            <div className="text-lg font-mono font-bold text-amber-400 mt-1">{status.total_conflicts_recorded}</div>
          </div>
        </div>
      )}

      {/* 3. LAN / QR Pairing Section */}
      <div className="p-5 rounded-2xl border glass-card border-zinc-800 space-y-4" data-testid="pairing-section">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
          <div>
            <h2 className="text-base font-bold text-zinc-100">Pair New Mobile Device</h2>
            <p className="text-xs text-zinc-400">Generate an ephemeral single-use 6-digit PIN and QR payload</p>
          </div>
          <button
            onClick={handleGeneratePairing}
            disabled={generating}
            data-testid="generate-pairing-btn"
            className="px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-zinc-950 font-bold text-xs transition shadow-sm"
          >
            {generating ? "Generating…" : "Generate LAN Pairing PIN / QR"}
          </button>
        </div>

        {pairingSession && (
          <div className="p-4 rounded-xl bg-cyan-950/20 border border-cyan-500/30 space-y-4" data-testid="active-pairing-session">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <span className="text-[10px] font-mono text-cyan-400 uppercase font-bold">EPHEMERAL PAIRING PIN (ONE-TIME USE)</span>
                <div className="text-3xl font-mono font-extrabold tracking-widest text-zinc-100 mt-1" data-testid="pairing-pin-display">
                  {pairingSession.pin_code}
                </div>
                <div className="text-xs text-zinc-400 mt-1">
                  Session ID: <code className="font-mono text-zinc-300">{pairingSession.session_id}</code>
                </div>
              </div>

              <div className="text-right">
                <span className="text-xs font-mono text-amber-400 bg-amber-950/40 px-3 py-1 rounded-full border border-amber-500/30">
                  {timeLeft > 0 ? `Expires in ${timeLeft}s` : "SESSION EXPIRED"}
                </span>
              </div>
            </div>

            {/* QR Connection Payload Box */}
            <div className="space-y-1.5 pt-2 border-t border-cyan-500/20">
              <span className="text-[10px] uppercase font-bold text-zinc-400">Mobile QR Connection Payload</span>
              <pre className="p-2.5 rounded-lg bg-zinc-950/80 border border-zinc-800 text-[11px] font-mono text-zinc-300 overflow-x-auto">
                {pairingSession.qr_payload}
              </pre>
              <p className="text-[11px] text-zinc-400">
                Scan this QR code from the AstroOS Mobile app or enter the 6-digit PIN while connected to the same local Wi-Fi.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* 4. Paired Devices Table */}
      <div className="p-5 rounded-2xl border glass-card border-zinc-800 space-y-4">
        <div className="border-b border-zinc-800 pb-3">
          <h2 className="text-base font-bold text-zinc-100">Authorized Paired Devices ({devices.length})</h2>
          <p className="text-xs text-zinc-400">Mobile clients authorized for bidirectional synchronization</p>
        </div>

        <div className="border rounded-xl overflow-hidden border-zinc-800 overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-zinc-900 text-zinc-400 border-b border-zinc-800 text-[10px] uppercase">
              <tr>
                <th className="p-2.5">Device Name</th>
                <th className="p-2.5">Type</th>
                <th className="p-2.5">Device ID</th>
                <th className="p-2.5">Last Seen</th>
                <th className="p-2.5">Status</th>
                <th className="p-2.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60 text-zinc-300" data-testid="paired-devices-table-body">
              {devices.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-4 text-center text-zinc-400">
                    No paired mobile devices yet. Generate a pairing PIN above to connect.
                  </td>
                </tr>
              ) : (
                devices.map((d) => (
                  <tr key={d.device_id} className="hover:bg-zinc-900/40">
                    <td className="p-2.5 font-bold text-zinc-100">{d.device_name}</td>
                    <td className="p-2.5 uppercase font-mono text-[10px] text-cyan-400">{d.device_type}</td>
                    <td className="p-2.5 font-mono text-zinc-400 text-[11px]">{d.device_id}</td>
                    <td className="p-2.5 text-zinc-400 text-[11px]">{d.last_seen_at_iso || "Just now"}</td>
                    <td className="p-2.5">
                      {d.is_active ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                          ACTIVE
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/20 text-red-300 border border-red-500/30">
                          REVOKED
                        </span>
                      )}
                    </td>
                    <td className="p-2.5 text-right">
                      {d.is_active && (
                        <button
                          onClick={() => handleRevokeDevice(d.device_id)}
                          className="px-2.5 py-1 rounded bg-red-500/10 hover:bg-red-500/20 text-red-400 text-[11px] font-medium border border-red-500/30 transition"
                        >
                          Revoke
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 5. Conflict Resolution Audit Ledger */}
      {conflicts.length > 0 && (
        <div className="p-5 rounded-2xl border glass-card border-amber-500/30 bg-amber-950/10 space-y-4" data-testid="conflict-ledger-panel">
          <div className="border-b border-amber-500/30 pb-3">
            <span className="text-[10px] font-mono text-amber-400 uppercase font-bold">NON-DESTRUCTIVE AUDIT TRAIL</span>
            <h2 className="text-base font-bold text-zinc-100">Conflict Resolution Ledger ({conflicts.length})</h2>
          </div>

          <div className="border rounded-xl overflow-hidden border-zinc-800 overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-zinc-900 text-zinc-400 border-b border-zinc-800 text-[10px] uppercase">
                <tr>
                  <th className="p-2">Entity ID</th>
                  <th className="p-2">Type</th>
                  <th className="p-2">Winner (Rev)</th>
                  <th className="p-2">Losing (Rev)</th>
                  <th className="p-2">Resolution Reason</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/60 text-zinc-300">
                {conflicts.map((c) => (
                  <tr key={c.conflict_id}>
                    <td className="p-2 font-mono text-cyan-400 text-[11px]">{c.entity_id}</td>
                    <td className="p-2 text-zinc-400">{c.entity_type}</td>
                    <td className="p-2 font-bold text-emerald-400">Rev {c.winning_revision} ({c.winning_device_id})</td>
                    <td className="p-2 text-zinc-400 line-through">Rev {c.losing_revision} ({c.losing_device_id})</td>
                    <td className="p-2 text-zinc-300 text-[11px]">{c.resolution_reason}</td>
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
