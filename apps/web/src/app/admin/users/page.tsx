/**
 * AstroOS — Admin User Management Page
 *
 * Dedicated page for managing admin users (roles, suspension).
 * Rendered within the AdminLayout.
 */

"use client";

import { UserManagementPanel } from "@/components/admin/UserManagementPanel";

export default function AdminUsersPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">User Management</h1>
        <p className="text-sm text-[var(--text-muted)]">Manage admin accounts, roles, and access permissions</p>
      </div>

      <UserManagementPanel />
    </div>
  );
}
