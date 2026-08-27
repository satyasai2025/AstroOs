"use client";

import { useEffect, useState } from "react";
import { SettingsLayout } from "@/components/settings/SettingsLayout";
import {
  NotificationPreferences,
  fetchNotificationPreferences,
  updateNotificationPreferences,
} from "@/lib/billing";
import { Card } from "@/components/ui";

export default function NotificationSettingsPage() {
  const [prefs, setPrefs] = useState<NotificationPreferences | null>(null);
  const [quotaWarnings, setQuotaWarnings] = useState(true);
  const [productUpdates, setProductUpdates] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const data = await fetchNotificationPreferences();
        setPrefs(data);
        setQuotaWarnings(data.quota_warnings);
        setProductUpdates(data.product_updates);
      } catch (err: any) {
        setErrorMessage(err.message || "Failed to load notification settings.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSavedSuccess(false);
    setErrorMessage(null);

    try {
      const updated = await updateNotificationPreferences({
        quota_warnings: quotaWarnings,
        product_updates: productUpdates,
      });
      setPrefs(updated);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 4000);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to update notification preferences.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <SettingsLayout
      title="Email &amp; Notification Preferences"
      description="Manage transactional email alerts, quota threshold warnings, and technique announcements."
    >
      <form onSubmit={handleSave} className="space-y-8">
        {savedSuccess && (
          <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3.5 text-xs text-emerald-300 font-semibold flex items-center gap-2">
            <span>✓</span>
            <span>Notification preferences updated successfully.</span>
          </div>
        )}

        {errorMessage && (
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3.5 text-xs text-red-400">
            {errorMessage}
          </div>
        )}

        {/* ── Mandatory Transactional Emails (Opt-Out Not Permitted) ── */}
        <Card className="p-6 border border-slate-800 bg-slate-900/60 space-y-4">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white">Required Transactional Emails</h3>
              <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-semibold text-slate-400">
                System Mandatory
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Essential transactional notifications required to maintain account integrity and legal billing compliance.
            </p>
          </div>

          <div className="space-y-4 pt-3 border-t border-slate-800/80">
            {/* Billing */}
            <div className="flex items-start justify-between gap-4 p-3.5 rounded-xl bg-slate-950/40 border border-slate-800">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-slate-200">
                    Billing, Invoices &amp; Subscription Receipts
                  </span>
                  <span className="text-[10px] text-cyan-400 font-bold">Always Active</span>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">
                  Order receipts, GST invoices, grace period reminders, and subscription renewal confirmations.
                </p>
              </div>
              <input
                type="checkbox"
                checked={true}
                disabled
                className="h-4 w-4 rounded border-slate-700 bg-slate-800 text-cyan-500 cursor-not-allowed opacity-70"
              />
            </div>

            {/* Security */}
            <div className="flex items-start justify-between gap-4 p-3.5 rounded-xl bg-slate-950/40 border border-slate-800">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-slate-200">
                    Security Alerts &amp; Password Resets
                  </span>
                  <span className="text-[10px] text-cyan-400 font-bold">Always Active</span>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">
                  Password reset verification links, remote login notices, and security credential updates.
                </p>
              </div>
              <input
                type="checkbox"
                checked={true}
                disabled
                className="h-4 w-4 rounded border-slate-700 bg-slate-800 text-cyan-500 cursor-not-allowed opacity-70"
              />
            </div>
          </div>
        </Card>

        {/* ── Configurable Notifications ── */}
        <Card className="p-6 border border-slate-800 bg-slate-900/60 space-y-4">
          <div>
            <h3 className="text-base font-bold text-white">Configurable Notifications</h3>
            <p className="text-xs text-slate-400 mt-1">
              Choose which operational reminders and feature updates you wish to receive.
            </p>
          </div>

          <div className="space-y-4 pt-3 border-t border-slate-800/80">
            {/* Quota Warnings */}
            <label className="flex items-start justify-between gap-4 p-3.5 rounded-xl bg-slate-950/40 border border-slate-800 hover:border-slate-700 cursor-pointer transition">
              <div>
                <span className="text-sm font-semibold text-slate-200">
                  Usage Quota Threshold Alerts
                </span>
                <p className="text-xs text-slate-400 mt-0.5">
                  Receive an email alert when you reach 80% and 100% of your saved horoscopes or monthly research runs.
                </p>
              </div>
              <input
                type="checkbox"
                checked={quotaWarnings}
                onChange={(e) => setQuotaWarnings(e.target.checked)}
                className="h-4 w-4 rounded border-slate-700 bg-slate-800 text-cyan-500 focus:ring-cyan-400/20"
              />
            </label>

            {/* Product Updates */}
            <label className="flex items-start justify-between gap-4 p-3.5 rounded-xl bg-slate-950/40 border border-slate-800 hover:border-slate-700 cursor-pointer transition">
              <div>
                <span className="text-sm font-semibold text-slate-200">
                  Product Updates &amp; Technique Releases
                </span>
                <p className="text-xs text-slate-400 mt-0.5">
                  Monthly digest covering new classical chart techniques, AstroDSL additions, and calculation updates.
                </p>
              </div>
              <input
                type="checkbox"
                checked={productUpdates}
                onChange={(e) => setProductUpdates(e.target.checked)}
                className="h-4 w-4 rounded border-slate-700 bg-slate-800 text-cyan-500 focus:ring-cyan-400/20"
              />
            </label>
          </div>
        </Card>

        {/* ── Submit Action ── */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving || loading}
            className="rounded-xl bg-cyan-500 hover:bg-cyan-400 px-6 py-2.5 text-xs font-bold text-slate-950 transition shadow"
          >
            {saving ? "Saving Changes..." : "Save Notification Preferences"}
          </button>
        </div>
      </form>
    </SettingsLayout>
  );
}
