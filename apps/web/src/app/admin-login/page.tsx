/**
 * AstroOS — Admin Login Page
 *
 * Standalone login page with Magento-style security aesthetic.
 * Redirects to /admin on successful authentication.
 */

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAdminCurrentUser } from "@/lib/adminAuth";
import { AdminLoginForm } from "@/components/admin/AdminLoginForm";

export default function AdminLoginPage() {
  const router = useRouter();
  const { data: adminUser, isLoading } = useAdminCurrentUser();
  const [mfaRequired, setMfaRequired] = useState(false);

  // Already logged in → redirect to admin dashboard
  useEffect(() => {
    if (adminUser && !isLoading) {
      router.push("/admin");
    }
  }, [adminUser, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--bg-primary)]">
        <div className="text-[var(--text-primary)]">Checking authentication...</div>
      </div>
    );
  }

  if (adminUser) {
    return null; // Will redirect
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[var(--bg-primary)] px-4">
      {/* Logo / Branding */}
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-2">
          AstroOS
        </h1>
        <p className="text-[var(--text-secondary)]">Admin Portal</p>
      </div>

      {/* Login Form */}
      <AdminLoginForm
        onSuccess={() => {
          router.push("/admin");
        }}
        mfaRequired={mfaRequired}
      />

      {/* Footer */}
      <div className="mt-8 text-center text-xs text-[var(--text-muted)]">
        <p>© 2026 AstroOS. All rights reserved.</p>
        <p className="mt-1">
          Unauthorized access is strictly prohibited. All activities are monitored.
        </p>
      </div>
    </div>
  );
}
