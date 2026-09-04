/**
 * AstroOS — User Management Panel
 *
 * Admin user management with role changes, suspend/activate, and research tier access controls.
 */

"use client";

import { useState } from "react";

interface AdminUser {
  id: string;
  email: string;
  displayName: string;
  role: "super_admin" | "admin";
  status: "active" | "suspended" | "locked";
  lastLoginAt: string | null;
  createdAt: string;
}

const MOCK_USERS: AdminUser[] = [
  { id: "admin-001", email: "admin@astroos.dev", displayName: "System Administrator", role: "super_admin", status: "active", lastLoginAt: "2026-01-15T10:30:00Z", createdAt: "2025-06-01T00:00:00Z" },
  { id: "admin-002", email: "editor@astroos.dev", displayName: "Content Editor", role: "admin", status: "active", lastLoginAt: "2026-01-14T15:45:00Z", createdAt: "2025-08-15T00:00:00Z" },
  { id: "admin-003", email: "viewer@astroos.dev", displayName: "Read Only User", role: "admin", status: "suspended", lastLoginAt: null, createdAt: "2025-10-20T00:00:00Z" },
];

function formatDate(iso: string | null): string {
  if (!iso) return "Never";
  try {
    return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
  } catch {
    return iso;
  }
}

export function UserManagementPanel() {
  const [users, setUsers] = useState(MOCK_USERS);

  const toggleStatus = (userId: string) => {
    setUsers((prev) =>
      prev.map((u) => {
        if (u.id === userId) {
          const newStatus = u.status === "active" ? "suspended" : "active";
          return { ...u, status: newStatus as "active" | "suspended" };
        }
        return u;
      })
    );
  };

  const changeRole = (userId: string, newRole: "super_admin" | "admin") => {
    setUsers((prev) =>
      prev.map((u) => (u.id === userId ? { ...u, role: newRole } : u))
    );
  };

  return (
    <div className="bg-[var(--bg-card)] rounded-lg border border-[var(--border-primary)] overflow-hidden">
      <div className="px-4 py-3 border-b border-[var(--border-primary)]">
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">User Management</h3>
        <p className="text-xs text-[var(--text-muted)]">Manage admin users and access permissions</p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--border-primary)] bg-[var(--bg-card-hover)]">
              <th className="px-4 py-2 text-left text-xs font-medium text-[var(--text-muted)] uppercase">User</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-[var(--text-muted)] uppercase">Role</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-[var(--text-muted)] uppercase">Status</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-[var(--text-muted)] uppercase">Last Login</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-[var(--text-muted)] uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border-primary)]">
            {users.map((user) => (
              <tr key={user.id} className="hover:bg-[var(--bg-card-hover)] transition-colors">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-[rgba(139,92,246,0.2)] flex items-center justify-center text-[rgba(139,92,246,0.9)] font-semibold text-xs">
                      {user.displayName.charAt(0)}
                    </div>
                    <div>
                      <p className="font-medium text-[var(--text-primary)]">{user.displayName}</p>
                      <p className="text-xs text-[var(--text-muted)]">{user.email}</p>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <select
                    value={user.role}
                    onChange={(e) => changeRole(user.id, e.target.value as "super_admin" | "admin")}
                    className="px-2 py-1 text-xs bg-[var(--bg-input)] border border-[var(--border-primary)] rounded-md text-[var(--text-primary)]"
                  >
                    <option value="super_admin">Super Admin</option>
                    <option value="admin">Admin</option>
                  </select>
                </td>
                <td className="px-4 py-3">
                  <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${
                    user.status === "active" ? "bg-emerald-400/15 text-emerald-300" :
                    user.status === "suspended" ? "bg-red-400/15 text-red-300" :
                    "bg-amber-400/15 text-amber-300"
                  }`}>
                    {user.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-xs text-[var(--text-muted)]">{formatDate(user.lastLoginAt)}</td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => toggleStatus(user.id)}
                    className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                      user.status === "active"
                        ? "bg-red-400/15 text-red-300 hover:bg-red-400/25"
                        : "bg-emerald-400/15 text-emerald-300 hover:bg-emerald-400/25"
                    }`}
                  >
                    {user.status === "active" ? "Suspend" : "Activate"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
