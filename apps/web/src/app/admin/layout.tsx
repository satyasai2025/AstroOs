/**
 * AstroOS — Admin Panel Layout
 *
 * Magento-style admin shell: separate from AppShell, independent sidebar,
 * header, and admin-specific authentication using adminTokenStore.
 *
 * Features:
 * - Admin auth via adminTokenStore (astro_admin_token) — completely separate from user tokens
 * - Sidebar navigation with expandable sections
 * - Dark slate/indigo theme distinct from user-facing UI
 * - Responsive: collapsible sidebar on desktop, drawer on mobile
 */

"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { adminTokenStore, useAdminCurrentUser, useAdminLogout } from "@/lib/adminAuth";
import { AdminSidebar } from "@/components/admin/AdminSidebar";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { data: adminUser, isLoading, isError } = useAdminCurrentUser();
  const logoutMutation = useAdminLogout();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const [hydrated, setHydrated] = useState(false);

  // Hydration guard: avoid SSR/client mismatch (localStorage unavailable on server)
  useEffect(() => {
    setHydrated(true);
  }, []);

  // useAdminCurrentUser()'s query is enabled only when a token exists (see
  // lib/adminAuth.ts), so with no token it sits in isError=false, isLoading
  // =false limbo forever — isError alone can never catch "no token at all",
  // only "token present but rejected by the server". Checking token
  // presence directly closes that gap so a fully unauthenticated visit
  // actually redirects instead of silently rendering the admin shell.
  const hasToken = hydrated && !!adminTokenStore.getAccess();
  const shouldRedirect = hydrated && (!hasToken || (!isLoading && isError));

  // Redirect to admin login if not authenticated
  useEffect(() => {
    if (shouldRedirect) {
      router.push("/admin-login");
    }
  }, [shouldRedirect, router]);

  // Show loading skeleton until hydrated + auth checked
  if (!hydrated || (hasToken && isLoading)) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-[var(--bg-primary)]">
        <div className="flex items-center gap-3 text-[var(--text-secondary)]">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-400 border-t-transparent" />
          <span>Loading admin panel...</span>
        </div>
      </div>
    );
  }

  // Logout handler
  const handleLogout = async () => {
    await logoutMutation.mutateAsync();
    router.push("/admin-login");
  };

  // Not authenticated (no token, or the server rejected it)
  if (shouldRedirect) {
    return null; // Will redirect in useEffect
  }

  return (
    <div className="flex min-h-dvh bg-[var(--bg-primary)]">
      {/* Desktop Sidebar */}
      <div
        className={`hidden md:block transition-all duration-300 ${
          sidebarCollapsed ? "w-16" : "w-64"
        }`}
      >
        <AdminSidebar
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
      </div>

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Header Bar */}
        <header className="flex items-center justify-between border-b border-[var(--border-primary)] bg-[var(--bg-secondary)] px-4 py-3">
          <div className="flex items-center gap-4">
            {/* Mobile menu toggle */}
            <button
              onClick={() => setMobileDrawerOpen(!mobileDrawerOpen)}
              className="md:hidden p-1 text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              aria-label="Toggle navigation"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                {mobileDrawerOpen ? (
                  <path d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path d="M3 12h18M3 6h18M3 18h18" />
                )}
              </svg>
            </button>

            {/* Breadcrumb / Current Section */}
            <div className="text-sm text-[var(--text-muted)]">
              <span className="inline-flex items-center gap-2 px-2 py-1 rounded bg-[rgba(6,207,255,0.15)] text-[rgba(6,207,255,0.9)]">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z" />
                </svg>
                Admin
              </span>
            </div>
          </div>

          {/* Right Side */}
          <div className="flex items-center gap-3">
            {/* Admin User Info */}
            <div className="hidden sm:flex items-center gap-2 text-sm text-[var(--text-secondary)]">
              <div className="h-8 w-8 rounded-full bg-[rgba(139,92,246,0.2)] flex items-center justify-center text-[rgba(139,92,246,0.9)] font-semibold text-xs">
                {adminUser?.display_name?.charAt(0) || adminUser?.email?.charAt(0) || "A"}
              </div>
              <div>
                <p className="font-medium text-[var(--text-primary)]">{adminUser?.display_name}</p>
                <p className="text-xs text-[var(--text-muted)]">{adminUser?.email}</p>
              </div>
            </div>

            {/* Logout Button */}
            <button
              onClick={handleLogout}
              disabled={logoutMutation.isPending}
              className="px-3 py-1.5 text-sm bg-[var(--bg-card)] border border-[var(--border-primary)] rounded-md text-[var(--text-secondary)] hover:bg-[var(--bg-card-hover)] hover:text-[var(--text-primary)] disabled:opacity-50 transition-colors"
            >
              {logoutMutation.isPending ? "Logging out..." : "Logout"}
            </button>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto bg-[var(--bg-primary)] p-6">
          {children}
        </main>
      </div>

      {/* Mobile Drawer */}
      {mobileDrawerOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/60"
            onClick={() => setMobileDrawerOpen(false)}
          />
          {/* Drawer */}
          <div className="absolute left-0 top-0 h-full w-64 bg-[var(--bg-secondary)] border-r border-[var(--border-primary)]">
            <div className="p-4 border-b border-[var(--border-primary)]">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-[rgba(139,92,246,0.2)] flex items-center justify-center text-[rgba(139,92,246,0.9)] font-bold text-sm">
                  A
                </div>
                <div>
                  <span className="font-semibold text-[var(--text-primary)]">Admin Portal</span>
                  <p className="text-xs text-[var(--text-muted)]">v2.3</p>
                </div>
              </div>
            </div>
            <div className="p-4 overflow-y-auto h-[calc(100vh-80px)]">
              <AdminSidebar collapsed={false} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
