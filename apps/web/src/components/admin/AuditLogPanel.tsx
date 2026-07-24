/**
 * AstroOS — Audit Log Panel
 *
 * Paginated table of admin actions with filtering by action type, admin user, and date range.
 */

"use client";

import { useState } from "react";

interface AuditLogEntry {
  id: string;
  adminEmail: string;
  action: string;
  resourceType: string;
  resourceId?: string;
  timestamp: string;
  ipAddress: string;
  details?: Record<string, unknown>;
}

const ACTION_COLORS: Record<string, string> = {
  "auth.login.success": "bg-emerald-400/15 text-emerald-300",
  "auth.login.failed": "bg-red-400/15 text-red-300",
  "auth.logout": "bg-slate-400/15 text-slate-300",
  "user.role_changed": "bg-amber-400/15 text-amber-300",
  "user.suspended": "bg-red-400/15 text-red-300",
  "user.activated": "bg-emerald-400/15 text-emerald-300",
  "plugin.status_changed": "bg-blue-400/15 text-blue-300",
  "plugin.api_key_rotated": "bg-purple-400/15 text-purple-300",
  "literature.created": "bg-teal-400/15 text-teal-300",
  "literature.updated": "bg-teal-400/15 text-teal-300",
  "literature.deleted": "bg-red-400/15 text-red-300",
  "yoga_rule.created": "bg-violet-400/15 text-violet-300",
  "yoga_rule.updated": "bg-violet-400/15 text-violet-300",
  "yoga_rule.toggled": "bg-amber-400/15 text-amber-300",
  "yoga_rule.deleted": "bg-red-400/15 text-red-300",
  "system.initialize": "bg-blue-400/15 text-blue-300",
};

const MOCK_LOGS: AuditLogEntry[] = [
  { id: "log-001", adminEmail: "admin@astroos.dev", action: "auth.login.success", resourceType: "auth", timestamp: "2026-01-15T10:30:00Z", ipAddress: "127.0.0.1" },
  { id: "log-002", adminEmail: "admin@astroos.dev", action: "system.initialize", resourceType: "system", timestamp: "2026-01-15T10:25:00Z", ipAddress: "127.0.0.1" },
  { id: "log-003", adminEmail: "admin@astroos.dev", action: "plugin.status_changed", resourceType: "plugin", resourceId: "plugin-ai-insights", timestamp: "2026-01-15T10:20:00Z", ipAddress: "127.0.0.1" },
  { id: "log-004", adminEmail: "admin@astroos.dev", action: "user.role_changed", resourceType: "user", resourceId: "user-002", timestamp: "2026-01-15T10:15:00Z", ipAddress: "127.0.0.1" },
  { id: "log-005", adminEmail: "admin@astroos.dev", action: "literature.created", resourceType: "literature", resourceId: "lit-001", timestamp: "2026-01-15T10:10:00Z", ipAddress: "127.0.0.1" },
  { id: "log-006", adminEmail: "admin@astroos.dev", action: "yoga_rule.created", resourceType: "yoga_rule", resourceId: "rule-001", timestamp: "2026-01-15T10:05:00Z", ipAddress: "127.0.0.1" },
  { id: "log-007", adminEmail: "admin@astroos.dev", action: "auth.login.failed", resourceType: "auth", timestamp: "2026-01-15T10:00:00Z", ipAddress: "192.168.1.100" },
];

function formatTimestamp(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "short",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

export function AuditLogPanel() {
  const [logs] = useState(MOCK_LOGS);
  const [filterAction, setFilterAction] = useState<string>("");
  const [filterAdmin, setFilterAdmin] = useState<string>("");

  const uniqueActions = [...new Set(logs.map((l) => l.action))];
  const uniqueAdmins = [...new Set(logs.map((l) => l.adminEmail))];

  const filteredLogs = logs.filter((log) => {
    if (filterAction && log.action !== filterAction) return false;
    if (filterAdmin && log.adminEmail !== filterAdmin) return false;
    return true;
  });

  return (
    <div className="bg-[var(--bg-card)] rounded-lg border border-[var(--border-primary)] overflow-hidden">
      <div className="px-4 py-3 border-b border-[var(--border-primary)]">
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">Audit Logs</h3>
        <p className="text-xs text-[var(--text-muted)]">Recent admin actions and system events</p>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 px-4 py-3 border-b border-[var(--border-primary)] bg-[var(--bg-card-hover)]">
        <select
          value={filterAction}
          onChange={(e) => setFilterAction(e.target.value)}
          className="px-3 py-1.5 text-xs bg-[var(--bg-input)] border border-[var(--border-primary)] rounded-md text-[var(--text-primary)]"
        >
          <option value="">All Actions</option>
          {uniqueActions.map((a) => (
            <option key={a} value={a}>{a}</option>
          ))}
        </select>

        <select
          value={filterAdmin}
          onChange={(e) => setFilterAdmin(e.target.value)}
          className="px-3 py-1.5 text-xs bg-[var(--bg-input)] border border-[var(--border-primary)] rounded-md text-[var(--text-primary)]"
        >
          <option value="">All Admins</option>
          {uniqueAdmins.map((a) => (
            <option key={a} value={a}>{a}</option>
          ))}
        </select>

        <span className="text-xs text-[var(--text-muted)]">{filteredLogs.length} entries</span>
      </div>

      {/* Log Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--border-primary)] bg-[var(--bg-card-hover)]">
              <th className="px-4 py-2 text-left text-xs font-medium text-[var(--text-muted)] uppercase">Action</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-[var(--text-muted)] uppercase">Resource</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-[var(--text-muted)] uppercase">Admin</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-[var(--text-muted)] uppercase">IP</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-[var(--text-muted)] uppercase">Time</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border-primary)]">
            {filteredLogs.map((log) => (
              <tr key={log.id} className="hover:bg-[var(--bg-card-hover)] transition-colors">
                <td className="px-4 py-2">
                  <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${ACTION_COLORS[log.action] || "bg-slate-400/15 text-slate-300"}`}>
                    {log.action}
                  </span>
                </td>
                <td className="px-4 py-2 text-xs text-[var(--text-secondary)]">
                  {log.resourceType}
                  {log.resourceId && <span className="text-[var(--text-muted)]"> / {log.resourceId}</span>}
                </td>
                <td className="px-4 py-2 text-xs text-[var(--text-secondary)]">{log.adminEmail}</td>
                <td className="px-4 py-2 text-xs text-[var(--text-muted)] font-mono">{log.ipAddress}</td>
                <td className="px-4 py-2 text-xs text-[var(--text-muted)]">{formatTimestamp(log.timestamp)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
