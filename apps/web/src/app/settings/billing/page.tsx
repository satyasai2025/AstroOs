"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { SettingsLayout } from "@/components/settings/SettingsLayout";
import {
  PaymentRecord,
  PlanLimitsInfo,
  SubscriptionInfo,
  fetchMyLimits,
  fetchMySubscription,
  fetchPaymentHistory,
  initiateCustomerPortal,
} from "@/lib/billing";
import { Badge, Button, Card, Icon } from "@/components/ui";

export default function BillingSettingsPage() {
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [limits, setLimits] = useState<PlanLimitsInfo | null>(null);
  const [payments, setPayments] = useState<PaymentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [portalLoading, setPortalLoading] = useState(false);
  const [portalError, setPortalError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [sub, lim, pay] = await Promise.all([
          fetchMySubscription(),
          fetchMyLimits(),
          fetchPaymentHistory(20, 0),
        ]);
        setSubscription(sub);
        setLimits(lim);
        setPayments(pay.items);
      } catch (err) {
        console.error("Failed to load billing data", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleOpenPortal = async () => {
    setPortalLoading(true);
    setPortalError(null);
    try {
      const res = await initiateCustomerPortal();
      if (res.portal_url) {
        window.location.href = res.portal_url;
      }
    } catch (err: any) {
      setPortalError(err.message || "Failed to open customer billing portal.");
      setPortalLoading(false);
    }
  };

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case "active":
        return <Badge tone="success">Active</Badge>;
      case "trialing":
        return <Badge tone="cyan">Trialing</Badge>;
      case "past_due_cancelled":
        return <Badge tone="gold">Past Due (Grace Period)</Badge>;
      case "expired":
        return <Badge tone="danger">Expired</Badge>;
      default:
        return <Badge tone="neutral">Free Community</Badge>;
    }
  };

  return (
    <SettingsLayout
      title="Billing &amp; Subscription Management"
      description="Manage your subscription plan, live usage quotas, invoices, and payment methods."
    >
      <div className="space-y-8">
        {/* ── Grace Period Warning (if past due) ── */}
        {subscription?.status === "past_due_cancelled" && (
          <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-5 text-amber-300 space-y-2">
            <div className="flex items-center gap-2 font-bold text-sm">
              <span>⚠️</span>
              <span>Payment Past Due — 3-Day Grace Window Active</span>
            </div>
            <p className="text-xs text-amber-200/90 leading-relaxed">
              We were unable to process your subscription renewal. Your premium research access remains fully active during your 3-day grace period. Please update your payment method to avoid automatic demotion to the Free plan.
            </p>
            <button
              onClick={handleOpenPortal}
              disabled={portalLoading}
              className="inline-flex items-center gap-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 px-3 py-1.5 text-xs font-bold text-slate-950 transition"
            >
              <span>Update Payment Method</span>
              <span>&rarr;</span>
            </button>
          </div>
        )}

        {/* ── Active Subscription Overview Card ── */}
        <Card className="p-6 border border-slate-200 dark:border-slate-800 bg-slate-900/60">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
            <div>
              <div className="flex items-center gap-2.5">
                <h2 className="text-xl font-bold text-white">Current Subscription</h2>
                {getStatusBadge(subscription?.status)}
              </div>
              <p className="text-xs text-slate-400 mt-1">
                {subscription
                  ? `Billing cycle active until ${new Date(subscription.current_period_end).toLocaleDateString()}`
                  : "You are currently on the Free Community plan."}
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Link
                href="/pricing"
                className="inline-flex items-center gap-1 rounded-xl bg-cyan-500 hover:bg-cyan-400 px-4 py-2 text-xs font-bold text-slate-950 transition shadow"
              >
                <span>Change / Upgrade Plan</span>
                <span>&rarr;</span>
              </Link>
              <button
                type="button"
                onClick={handleOpenPortal}
                disabled={portalLoading}
                className="inline-flex items-center gap-1 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-750 px-4 py-2 text-xs font-bold text-slate-200 transition"
              >
                <span>{portalLoading ? "Opening..." : "Customer Portal"}</span>
              </button>
            </div>
          </div>

          {portalError && (
            <div className="mt-3 rounded-lg border border-red-500/30 bg-red-500/10 p-2 text-xs text-red-400">
              {portalError}
            </div>
          )}

          {/* ── Quota & Usage Progress ── */}
          <div className="pt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Horoscopes Quota */}
            <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-300">Saved Horoscopes Quota</span>
                <span className="font-bold text-cyan-400">
                  {limits?.saved_horoscopes ? `Limit: ${limits.saved_horoscopes}` : "Unlimited"}
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full"
                  style={{ width: `${limits?.saved_horoscopes ? Math.min(100, (4 / limits.saved_horoscopes) * 100) : 10}%` }}
                />
              </div>
              <p className="text-[11px] text-slate-400">
                Active charts saved in your personal library.
              </p>
            </div>

            {/* Monthly Research Runs */}
            <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-300">Monthly Research Projects</span>
                <span className="font-bold text-purple-400">
                  {limits?.research_projects_monthly ? `${limits.research_projects_monthly} / mo` : "0 on Free"}
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-purple-500 to-indigo-500 rounded-full"
                  style={{ width: `${limits?.research_projects_monthly ? 30 : 0}%` }}
                />
              </div>
              <p className="text-[11px] text-slate-400">
                Statistical correlation &amp; AstroDSL batch runs this billing cycle.
              </p>
            </div>
          </div>
        </Card>

        {/* ── Payment History & Invoices Table ── */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white">Payment Receipts &amp; Tax History</h3>
              <p className="text-xs text-slate-400">Complete itemized audit log of past subscription invoices and GST receipts.</p>
            </div>
          </div>

          <Card className="p-0 overflow-hidden border border-slate-800 bg-slate-900/60">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400">
                    <th className="py-3 px-4 font-semibold">Date</th>
                    <th className="py-3 px-4 font-semibold">Base Price</th>
                    <th className="py-3 px-4 font-semibold">Tax / GST</th>
                    <th className="py-3 px-4 font-semibold">Total Paid</th>
                    <th className="py-3 px-4 font-semibold">Provider</th>
                    <th className="py-3 px-4 font-semibold text-center">Status</th>
                    <th className="py-3 px-4 font-semibold text-right">Receipt</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {payments.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-slate-500">
                        No payment transactions recorded yet.
                      </td>
                    </tr>
                  ) : (
                    payments.map((p) => {
                      const sym = p.currency === "INR" ? "₹" : "$";
                      const baseFmt = p.base_amount ? `${sym}${(p.base_amount / 100).toFixed(2)}` : `${sym}${(p.amount / 100).toFixed(2)}`;
                      const taxFmt = p.tax_amount ? `${sym}${(p.tax_amount / 100).toFixed(2)}` : "—";
                      const totalFmt = `${sym}${(p.amount / 100).toFixed(2)}`;

                      return (
                        <tr key={p.id} className="hover:bg-slate-800/30 transition-colors">
                          <td className="py-3 px-4 text-slate-400">
                            {new Date(p.created_at).toLocaleDateString()}
                          </td>
                          <td className="py-3 px-4 font-medium text-slate-200">
                            {baseFmt}
                          </td>
                          <td className="py-3 px-4 text-slate-400">
                            {taxFmt} {p.tax_rate ? `(${p.tax_rate}%)` : ""}
                          </td>
                          <td className="py-3 px-4 font-bold text-white">
                            {totalFmt} <span className="text-[10px] text-slate-400 font-normal">{p.currency}</span>
                          </td>
                          <td className="py-3 px-4 uppercase font-semibold text-[11px] text-slate-400">
                            {p.provider}
                          </td>
                          <td className="py-3 px-4 text-center">
                            <span
                              className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-bold ${
                                p.status === "succeeded"
                                  ? "bg-emerald-500/20 text-emerald-400"
                                  : p.status === "pending"
                                  ? "bg-amber-500/20 text-amber-400"
                                  : "bg-red-500/20 text-red-400"
                              }`}
                            >
                              {p.status}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-right">
                            {p.receipt_url ? (
                              <a
                                href={p.receipt_url}
                                target="_blank"
                                rel="noreferrer"
                                className="font-semibold text-cyan-400 hover:text-cyan-300 underline"
                              >
                                View Invoice
                              </a>
                            ) : (
                              <span className="text-slate-600">—</span>
                            )}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      </div>
    </SettingsLayout>
  );
}
