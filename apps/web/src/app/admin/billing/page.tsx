"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card } from "@/components/ui";

interface AdminPayment {
  id: string;
  user_id: string;
  amount: number;
  base_amount?: number;
  tax_amount?: number;
  tax_rate?: number;
  currency: string;
  status: string;
  provider: string;
  created_at: string;
}

interface AdminSubscription {
  id: string;
  user_id: string;
  status: string;
  billing_cycle: string;
  current_period_start: string | null;
  current_period_end: string | null;
}

interface EmailLog {
  id: string;
  recipient: string;
  template_name: string;
  delivery_status: string;
  provider_used: string;
  created_at: string;
}

export default function AdminBillingConsolePage() {
  const [payments, setPayments] = useState<AdminPayment[]>([]);
  const [subscriptions, setSubscriptions] = useState<AdminSubscription[]>([]);
  const [emailLogs, setEmailLogs] = useState<EmailLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"payments" | "subscriptions" | "emails">("payments");
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [payRes, subRes, emailRes] = await Promise.all([
          api.get<{ items: AdminPayment[]; total: number }>("/api/v1/admin/billing/payments"),
          api.get<{ items: AdminSubscription[]; total: number }>("/api/v1/admin/billing/subscriptions"),
          api.get<{ items: EmailLog[]; total: number }>("/api/v1/admin/notifications/logs"),
        ]);
        setPayments(payRes.items);
        setSubscriptions(subRes.items);
        setEmailLogs(emailRes.items);
      } catch (err) {
        console.error("Failed to load admin billing data", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleRefund = async (paymentId: string) => {
    try {
      await api.post(`/api/v1/admin/billing/refunds/${paymentId}`, {});
      setActionMessage(`Payment ${paymentId.substring(0, 8)} successfully refunded.`);
      setPayments((prev) =>
        prev.map((p) => (p.id === paymentId ? { ...p, status: "refunded" } : p))
      );
    } catch (err: any) {
      setActionMessage(`Refund failed: ${err.message}`);
    }
  };

  const formatMoney = (amount: number, curr: string) => {
    const symbol = curr.toUpperCase() === "INR" ? "₹" : "$";
    const val = curr.toUpperCase() === "INR" ? (amount / 100).toFixed(2) : (amount / 100).toFixed(2);
    return `${symbol}${val}`;
  };

  return (
    <div className="space-y-6">
      {/* ── Console Header ── */}
      <div>
        <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-0.5 text-xs font-semibold text-cyan-400">
          <span>💳</span>
          <span>Phase 13 &bull; Platform Billing &amp; Operations Console</span>
        </div>
        <h1 className="text-2xl font-extrabold text-white mt-2">
          Billing, Payments &amp; Deliverability Administration
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Administer global user transactions, GST tax breakdowns, customer subscriptions, and transactional email queues.
        </p>
      </div>

      {actionMessage && (
        <div className="rounded-xl border border-cyan-500/30 bg-cyan-500/10 p-3 text-xs text-cyan-300">
          {actionMessage}
        </div>
      )}

      {/* ── Navigation Tabs ── */}
      <div className="flex gap-2 border-b border-slate-800 pb-2 text-xs">
        <button
          onClick={() => setActiveTab("payments")}
          className={`px-4 py-2 rounded-lg font-bold transition ${
            activeTab === "payments" ? "bg-cyan-500 text-slate-950" : "text-slate-400 hover:text-white"
          }`}
        >
          Transactions &amp; GST Invoices ({payments.length})
        </button>
        <button
          onClick={() => setActiveTab("subscriptions")}
          className={`px-4 py-2 rounded-lg font-bold transition ${
            activeTab === "subscriptions" ? "bg-cyan-500 text-slate-950" : "text-slate-400 hover:text-white"
          }`}
        >
          Subscriptions &amp; Grace States ({subscriptions.length})
        </button>
        <button
          onClick={() => setActiveTab("emails")}
          className={`px-4 py-2 rounded-lg font-bold transition ${
            activeTab === "emails" ? "bg-cyan-500 text-slate-950" : "text-slate-400 hover:text-white"
          }`}
        >
          Email Queue &amp; Delivery Logs ({emailLogs.length})
        </button>
      </div>

      {/* ── Tab 1: Payments & GST Breakdown ── */}
      {activeTab === "payments" && (
        <Card className="p-0 overflow-hidden border border-slate-800 bg-slate-900/60">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400">
                  <th className="py-3 px-4 font-semibold">Date</th>
                  <th className="py-3 px-4 font-semibold">User ID</th>
                  <th className="py-3 px-4 font-semibold">Base Price</th>
                  <th className="py-3 px-4 font-semibold">GST / Tax</th>
                  <th className="py-3 px-4 font-semibold">Total Paid</th>
                  <th className="py-3 px-4 font-semibold">Gateway</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {payments.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-slate-500">
                      No payment transactions recorded.
                    </td>
                  </tr>
                ) : (
                  payments.map((p) => (
                    <tr key={p.id} className="hover:bg-slate-800/30 transition">
                      <td className="py-3 px-4 text-slate-400">
                        {new Date(p.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4 font-mono text-[11px] text-slate-300">
                        {p.user_id.substring(0, 8)}...
                      </td>
                      <td className="py-3 px-4">
                        {p.base_amount ? formatMoney(p.base_amount, p.currency) : "—"}
                      </td>
                      <td className="py-3 px-4 text-cyan-400">
                        {p.tax_amount
                          ? `${formatMoney(p.tax_amount, p.currency)} (${p.tax_rate ?? 18}%)`
                          : "₹0.00"}
                      </td>
                      <td className="py-3 px-4 font-bold text-white">
                        {formatMoney(p.amount, p.currency)}
                      </td>
                      <td className="py-3 px-4 uppercase text-[10px] font-bold text-slate-400">
                        {p.provider}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                            p.status === "succeeded"
                              ? "bg-emerald-500/20 text-emerald-400"
                              : p.status === "refunded"
                              ? "bg-amber-500/20 text-amber-400"
                              : "bg-red-500/20 text-red-400"
                          }`}
                        >
                          {p.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        {p.status === "succeeded" && (
                          <button
                            onClick={() => handleRefund(p.id)}
                            className="rounded bg-slate-800 hover:bg-slate-750 px-2 py-1 text-[11px] font-bold text-red-300 border border-slate-700"
                          >
                            Refund
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* ── Tab 2: Subscriptions ── */}
      {activeTab === "subscriptions" && (
        <Card className="p-0 overflow-hidden border border-slate-800 bg-slate-900/60">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400">
                  <th className="py-3 px-4 font-semibold">User ID</th>
                  <th className="py-3 px-4 font-semibold">Cycle</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold">Period Start</th>
                  <th className="py-3 px-4 font-semibold">Period End</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {subscriptions.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-800/30 transition">
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-300">
                      {s.user_id.substring(0, 8)}...
                    </td>
                    <td className="py-3 px-4 uppercase text-[11px]">{s.billing_cycle}</td>
                    <td className="py-3 px-4">
                      <span className="rounded-full bg-cyan-500/20 text-cyan-400 px-2 py-0.5 text-[10px] font-bold">
                        {s.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-400">
                      {s.current_period_start ? new Date(s.current_period_start).toLocaleDateString() : "—"}
                    </td>
                    <td className="py-3 px-4 text-slate-400">
                      {s.current_period_end ? new Date(s.current_period_end).toLocaleDateString() : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* ── Tab 3: Email Queue ── */}
      {activeTab === "emails" && (
        <Card className="p-0 overflow-hidden border border-slate-800 bg-slate-900/60">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400">
                  <th className="py-3 px-4 font-semibold">Date</th>
                  <th className="py-3 px-4 font-semibold">Recipient</th>
                  <th className="py-3 px-4 font-semibold">Template</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold">Provider</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {emailLogs.map((l) => (
                  <tr key={l.id} className="hover:bg-slate-800/30 transition">
                    <td className="py-3 px-4 text-slate-400">
                      {new Date(l.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">{l.recipient}</td>
                    <td className="py-3 px-4 font-bold text-white">{l.template_name}</td>
                    <td className="py-3 px-4">
                      <span className="rounded-full bg-emerald-500/20 text-emerald-400 px-2 py-0.5 text-[10px] font-bold">
                        {l.delivery_status}
                      </span>
                    </td>
                    <td className="py-3 px-4 uppercase text-[10px] text-slate-400">
                      {l.provider_used}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
