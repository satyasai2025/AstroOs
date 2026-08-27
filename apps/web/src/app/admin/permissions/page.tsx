"use client";

import { useState } from "react";
import { Card } from "@/components/ui";

interface RolePermission {
  id: string;
  name: string;
  description: string;
  user: boolean;
  researcher: boolean;
  admin: boolean;
  super_admin: boolean;
}

const INITIAL_PERMISSIONS: RolePermission[] = [
  {
    id: "perm_natal_calc",
    name: "Natal Chart Calculations (D1-D60)",
    description: "Access high-precision Swiss Ephemeris astronomical positions and vargas",
    user: true,
    researcher: true,
    admin: true,
    super_admin: true,
  },
  {
    id: "perm_tiered_reports",
    name: "Generate Tiered PDF Reports",
    description: "Generate 2-page, 5-page, and 8-page scholar PDF dossiers",
    user: true,
    researcher: true,
    admin: true,
    super_admin: true,
  },
  {
    id: "perm_governed_ai",
    name: "Governed Shastra AI Copilot",
    description: "Context-aware RAG queries grounded in BPHS, Jaimini, and Phaladeepika",
    user: true,
    researcher: true,
    admin: true,
    super_admin: true,
  },
  {
    id: "perm_research_studio",
    name: "Research Studio & AstroDSL Authoring",
    description: "Create research projects, run hypothesis backtests, and author AstroDSL rules",
    user: false,
    researcher: true,
    admin: true,
    super_admin: true,
  },
  {
    id: "perm_bulk_dataset_import",
    name: "Bulk Dataset Import (JHD / CSV)",
    description: "Ingest and validate large cohorts of historical birth charts",
    user: false,
    researcher: true,
    admin: true,
    super_admin: true,
  },
  {
    id: "perm_billing_management",
    name: "Billing & Revenue Administration",
    description: "Inspect global transactions, audit GST invoices, and issue refunds",
    user: false,
    researcher: false,
    admin: true,
    super_admin: true,
  },
  {
    id: "perm_user_role_assignment",
    name: "User Governance & Role Assignment",
    description: "Suspend/activate accounts and promote users to Researcher/Admin roles",
    user: false,
    researcher: false,
    admin: true,
    super_admin: true,
  },
  {
    id: "perm_system_config",
    name: "System Security & Secret Keys",
    description: "Manage Swiss Ephemeris paths, cryptographic keys, and payment gateway webhooks",
    user: false,
    researcher: false,
    admin: false,
    super_admin: true,
  },
];

export default function AdminPermissionsPage() {
  const [permissions, setPermissions] = useState<RolePermission[]>(INITIAL_PERMISSIONS);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  const togglePermission = (permId: string, roleKey: "user" | "researcher" | "admin" | "super_admin") => {
    setPermissions((prev) =>
      prev.map((p) => (p.id === permId ? { ...p, [roleKey]: !p[roleKey] } : p))
    );
  };

  const handleSave = () => {
    setSavedMessage("Role-Based Access Control matrix updated successfully.");
    setTimeout(() => setSavedMessage(null), 4000);
  };

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-0.5 text-xs font-semibold text-indigo-400">
            <span>🛡️</span>
            <span>Role-Based Access Control (RBAC) &bull; Platform Permissions</span>
          </div>
          <h1 className="text-2xl font-extrabold text-white mt-2">
            Permissions &amp; Entitlement Matrix
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Configure feature capabilities and authorization boundaries across User, Researcher, Admin, and Super Admin roles.
          </p>
        </div>
        <button
          onClick={handleSave}
          className="rounded-xl bg-indigo-600 hover:bg-indigo-500 px-5 py-2 text-xs font-bold text-white transition shadow self-start sm:self-auto"
        >
          Save Changes
        </button>
      </div>

      {savedMessage && (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-400">
          {savedMessage}
        </div>
      )}

      {/* ── Permissions Matrix Table ── */}
      <Card className="p-0 overflow-hidden border border-slate-800 bg-slate-900/60">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400">
                <th className="py-3.5 px-4 font-semibold w-1/3">Permission &amp; Capability</th>
                <th className="py-3.5 px-4 font-semibold text-center">User</th>
                <th className="py-3.5 px-4 font-semibold text-center">Researcher</th>
                <th className="py-3.5 px-4 font-semibold text-center">Admin</th>
                <th className="py-3.5 px-4 font-semibold text-center">Super Admin</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {permissions.map((perm) => (
                <tr key={perm.id} className="hover:bg-slate-800/30 transition">
                  <td className="py-3.5 px-4">
                    <div className="font-bold text-white">{perm.name}</div>
                    <div className="text-[11px] text-slate-400 mt-0.5">{perm.description}</div>
                  </td>
                  <td className="py-3.5 px-4 text-center">
                    <input
                      type="checkbox"
                      checked={perm.user}
                      onChange={() => togglePermission(perm.id, "user")}
                      className="h-4 w-4 rounded border-slate-700 bg-slate-950 text-indigo-500 focus:ring-indigo-400"
                    />
                  </td>
                  <td className="py-3.5 px-4 text-center">
                    <input
                      type="checkbox"
                      checked={perm.researcher}
                      onChange={() => togglePermission(perm.id, "researcher")}
                      className="h-4 w-4 rounded border-slate-700 bg-slate-950 text-indigo-500 focus:ring-indigo-400"
                    />
                  </td>
                  <td className="py-3.5 px-4 text-center">
                    <input
                      type="checkbox"
                      checked={perm.admin}
                      onChange={() => togglePermission(perm.id, "admin")}
                      className="h-4 w-4 rounded border-slate-700 bg-slate-950 text-indigo-500 focus:ring-indigo-400"
                    />
                  </td>
                  <td className="py-3.5 px-4 text-center">
                    <input
                      type="checkbox"
                      checked={perm.super_admin}
                      onChange={() => togglePermission(perm.id, "super_admin")}
                      className="h-4 w-4 rounded border-slate-700 bg-slate-950 text-indigo-500 focus:ring-indigo-400"
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
