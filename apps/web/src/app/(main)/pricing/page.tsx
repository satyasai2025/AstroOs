"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  BillingCycle,
  PricingCatalogResponse,
  PricingCurrency,
  PricingPlanDetail,
  SubscriptionInfo,
  fetchMySubscription,
  fetchPricingCatalog,
  initiateCheckout,
} from "@/lib/billing";
import { useCurrentUser } from "@/lib/auth";
import { Badge, Button, Card, Icon } from "@/components/ui";

export default function PricingPage() {
  const { data: user } = useCurrentUser();
  const [billingCycle, setBillingCycle] = useState<BillingCycle>("monthly");
  const [currency, setCurrency] = useState<PricingCurrency>("INR");
  const [catalog, setCatalog] = useState<PricingCatalogResponse | null>(null);
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [catData, subData] = await Promise.all([
          fetchPricingCatalog(currency),
          fetchMySubscription(),
        ]);
        setCatalog(catData);
        setSubscription(subData);
      } catch (err: any) {
        setErrorMessage(err.message || "Failed to load pricing data.");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [currency]);

  const handleCheckout = async (planCode: string) => {
    if (planCode === "FREE") return;
    if (!user) {
      window.location.href = `/login?redirect=/pricing`;
      return;
    }

    setCheckoutLoading(planCode);
    setErrorMessage(null);
    try {
      const res = await initiateCheckout({
        plan_code: planCode,
        billing_cycle: billingCycle,
        currency: currency,
      });
      if (res.checkout_url) {
        window.location.href = res.checkout_url;
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Unable to start checkout session.");
      setCheckoutLoading(null);
    }
  };

  const getPlanByCode = (code: string): PricingPlanDetail | undefined => {
    return catalog?.plans.find((p) => p.plan_code === code);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-12">
        {/* ── Header ── */}
        <div className="text-center space-y-4 max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3.5 py-1 text-xs font-semibold text-cyan-400">
            <span>✨</span>
            <span>AstroOS Premium Platform</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white">
            Transparent, India-First Vedic Research Pricing
          </h1>
          <p className="text-sm sm:text-base text-slate-400 leading-relaxed">
            Unlock professional predictive tools, custom AstroDSL rule authoring, high-precision ephemeris calculations, and statistical research workspaces.
          </p>

          {/* ── Controls: Currency & Billing Cycle ── */}
          <div className="pt-6 flex flex-col sm:flex-row items-center justify-center gap-4">
            {/* Currency Selector */}
            <div className="inline-flex items-center rounded-xl bg-slate-900 border border-slate-800 p-1">
              <button
                type="button"
                onClick={() => setCurrency("INR")}
                className={`flex items-center gap-1 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  currency === "INR"
                    ? "bg-cyan-500 text-slate-950 shadow"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                <span>₹</span>
                <span>INR (India)</span>
              </button>
              <button
                type="button"
                onClick={() => setCurrency("USD")}
                className={`flex items-center gap-1 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  currency === "USD"
                    ? "bg-cyan-500 text-slate-950 shadow"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                <span>$</span>
                <span>USD (Global)</span>
              </button>
            </div>

            {/* Monthly / Yearly Toggle */}
            <div className="inline-flex items-center rounded-xl bg-slate-900 border border-slate-800 p-1">
              <button
                type="button"
                onClick={() => setBillingCycle("monthly")}
                className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  billingCycle === "monthly"
                    ? "bg-slate-800 text-white shadow"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                Monthly
              </button>
              <button
                type="button"
                onClick={() => setBillingCycle("yearly")}
                className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  billingCycle === "yearly"
                    ? "bg-slate-800 text-white shadow"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                <span>Yearly</span>
                <span className="rounded bg-emerald-500/20 text-emerald-400 px-1.5 py-0.2 text-[10px]">
                  Save ~17%
                </span>
              </button>
            </div>
          </div>

          {errorMessage && (
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-400">
              {errorMessage}
            </div>
          )}
        </div>

        {/* ── Pricing Cards Grid ── */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 items-stretch">
          {catalog?.plans.map((plan) => {
            const isYearly = billingCycle === "yearly";
            const baseFmt = isYearly ? plan.yearly_base_formatted : plan.monthly_base_formatted;
            const taxFmt = isYearly ? plan.yearly_tax_formatted : plan.monthly_tax_formatted;
            const totalFmt = isYearly ? plan.yearly_total_formatted : plan.monthly_total_formatted;
            const isPopular = plan.plan_code === "PRO";
            const isResearch = plan.plan_code === "RESEARCH";
            const isFree = plan.plan_code === "FREE";

            return (
              <div
                key={plan.plan_code}
                className={`relative flex flex-col justify-between rounded-2xl border p-6 transition-all duration-200 ${
                  isPopular
                    ? "border-cyan-500 bg-slate-900/90 shadow-xl shadow-cyan-500/10 scale-[1.02]"
                    : "border-slate-800 bg-slate-900/50 hover:border-slate-700"
                }`}
              >
                {isPopular && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 px-3.5 py-0.5 text-[11px] font-extrabold uppercase tracking-wider text-slate-950 shadow-md">
                    Most Popular
                  </div>
                )}
                {isResearch && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-r from-purple-500 to-indigo-600 px-3.5 py-0.5 text-[11px] font-extrabold uppercase tracking-wider text-white shadow-md">
                    Scholar Choice
                  </div>
                )}

                <div className="space-y-4">
                  {/* Plan Name & Desc */}
                  <div>
                    <h3 className="text-lg font-bold text-white flex items-center justify-between">
                      <span>{plan.name}</span>
                      <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                        {plan.plan_code}
                      </span>
                    </h3>
                    <p className="text-xs text-slate-400 mt-1 min-h-[36px] leading-relaxed">
                      {plan.description}
                    </p>
                  </div>

                  {/* ── Tax Breakdown Box (Transparent Base + GST) ── */}
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3.5 space-y-2">
                    <div className="flex items-baseline justify-between">
                      <span className="text-xs text-slate-400">Base Price:</span>
                      <span className="text-sm font-bold text-slate-200">{baseFmt}</span>
                    </div>

                    {plan.tax_rate > 0 && !isFree ? (
                      <div className="flex items-baseline justify-between text-xs text-slate-400 border-t border-slate-800/80 pt-1.5">
                        <span>+ {plan.tax_rate}% {plan.tax_name}:</span>
                        <span className="text-slate-300 font-medium">{taxFmt}</span>
                      </div>
                    ) : null}

                    <div className="border-t border-slate-700/80 pt-2 flex items-baseline justify-between">
                      <span className="text-xs font-bold text-cyan-400">Total Payable:</span>
                      <div className="text-right">
                        <span className="text-xl font-extrabold text-white">{totalFmt}</span>
                        <span className="text-[10px] text-slate-500 block">
                          /{isYearly ? "year" : "month"}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Limits Summary */}
                  <div className="space-y-1.5 py-2 border-y border-slate-800/60 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Saved Horoscopes:</span>
                      <span className="font-semibold text-slate-200">
                        {plan.saved_horoscopes_limit ?? "Unlimited"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Monthly Research Runs:</span>
                      <span className="font-semibold text-slate-200">
                        {plan.research_projects_monthly_limit ?? "Unlimited"}
                      </span>
                    </div>
                  </div>

                  {/* Feature Checklist */}
                  <div className="space-y-2 pt-1">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Included Capabilities:
                    </p>
                    <ul className="space-y-2 text-xs text-slate-300">
                      {plan.features.map((feat, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-cyan-400 flex-shrink-0">✓</span>
                          <span>{feat}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* CTA Button */}
                <div className="mt-6 pt-4 border-t border-slate-800">
                  {isFree ? (
                    <button
                      disabled
                      className="w-full rounded-xl bg-slate-800 py-2.5 text-xs font-bold text-slate-400 cursor-default"
                    >
                      Included Forever
                    </button>
                  ) : (
                    <button
                      onClick={() => handleCheckout(plan.plan_code)}
                      disabled={checkoutLoading !== null}
                      className={`w-full rounded-xl py-2.5 text-xs font-bold transition-all shadow-md ${
                        isPopular
                          ? "bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-extrabold"
                          : "bg-slate-800 hover:bg-slate-700 text-white border border-slate-700"
                      }`}
                    >
                      {checkoutLoading === plan.plan_code
                        ? "Opening Checkout..."
                        : `Subscribe to ${plan.plan_code}`}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* ── Feature Comparison Matrix ── */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 sm:p-8 space-y-6">
          <div className="space-y-1">
            <h2 className="text-xl font-bold text-white">Full Feature Comparison Matrix</h2>
            <p className="text-xs text-slate-400">Detailed breakdown of computational modules and research tools across plans.</p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400">
                  <th className="py-3 px-4 font-semibold">Feature / Module</th>
                  <th className="py-3 px-4 font-semibold text-center">Free</th>
                  <th className="py-3 px-4 font-semibold text-center text-cyan-400">PRO</th>
                  <th className="py-3 px-4 font-semibold text-center text-purple-400">RESEARCH</th>
                  <th className="py-3 px-4 font-semibold text-center">CUSTOM</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                <tr>
                  <td className="py-3 px-4 font-medium">D1 to D60 Vargas & Planetary Positions</td>
                  <td className="py-3 px-4 text-center text-emerald-400">✓</td>
                  <td className="py-3 px-4 text-center text-emerald-400">✓</td>
                  <td className="py-3 px-4 text-center text-emerald-400">✓</td>
                  <td className="py-3 px-4 text-center text-emerald-400">✓</td>
                </tr>
                <tr>
                  <td className="py-3 px-4 font-medium">Vimshottari & Multi-Dasha Convergence</td>
                  <td className="py-3 px-4 text-center text-emerald-400">✓</td>
                  <td className="py-3 px-4 text-center text-emerald-400">✓</td>
                  <td className="py-3 px-4 text-center text-emerald-400">✓</td>
                  <td className="py-3 px-4 text-center text-emerald-400">✓</td>
                </tr>
                <tr>
                  <td className="py-3 px-4 font-medium">Prashna & Horary Astrology Engine</td>
                  <td className="py-3 px-4 text-center text-slate-600">—</td>
                  <td className="py-3 px-4 text-center text-emerald-400">✓</td>
                  <td className="py-3 px-4 text-center text-emerald-400">✓</td>
                  <td className="py-3 px-4 text-center text-emerald-400">✓</td>
                </tr>
                <tr>
                  <td className="py-3 px-4 font-medium">PDF Narrative & Export Reports</td>
                  <td className="py-3 px-4 text-center text-slate-600">—</td>
                  <td className="py-3 px-4 text-center text-emerald-400">✓</td>
                  <td className="py-3 px-4 text-center text-emerald-400">✓</td>
                  <td className="py-3 px-4 text-center text-emerald-400">✓</td>
                </tr>
                <tr>
                  <td className="py-3 px-4 font-medium">Custom AstroDSL Technique Rule Authoring</td>
                  <td className="py-3 px-4 text-center text-slate-600">—</td>
                  <td className="py-3 px-4 text-center text-slate-600">—</td>
                  <td className="py-3 px-4 text-center text-emerald-400">✓</td>
                  <td className="py-3 px-4 text-center text-emerald-400">✓</td>
                </tr>
                <tr>
                  <td className="py-3 px-4 font-medium">Statistical Cohort Correlation & Bayes Studio</td>
                  <td className="py-3 px-4 text-center text-slate-600">—</td>
                  <td className="py-3 px-4 text-center text-slate-600">—</td>
                  <td className="py-3 px-4 text-center text-emerald-400">✓</td>
                  <td className="py-3 px-4 text-center text-emerald-400">✓</td>
                </tr>
                <tr>
                  <td className="py-3 px-4 font-medium">Full Knowledge Graph RAG Search</td>
                  <td className="py-3 px-4 text-center text-slate-600">—</td>
                  <td className="py-3 px-4 text-center text-slate-600">—</td>
                  <td className="py-3 px-4 text-center text-emerald-400">✓</td>
                  <td className="py-3 px-4 text-center text-emerald-400">✓</td>
                </tr>
                <tr>
                  <td className="py-3 px-4 font-medium">Batch High-Throughput Processing</td>
                  <td className="py-3 px-4 text-center text-slate-600">—</td>
                  <td className="py-3 px-4 text-center text-slate-600">—</td>
                  <td className="py-3 px-4 text-center text-slate-600">—</td>
                  <td className="py-3 px-4 text-center text-emerald-400">✓</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* ── Trust & Security Banner ── */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🔒</span>
            <div>
              <p className="font-semibold text-white">Bank-Grade Payment Security</p>
              <p>All transactions processed via secure 256-bit encryption with Instant Invoice &amp; GST compliance.</p>
            </div>
          </div>
          <Link
            href="/settings/billing"
            className="inline-flex items-center gap-1 font-bold text-cyan-400 hover:text-cyan-300 transition"
          >
            <span>Manage Existing Subscription</span>
            <span>&rarr;</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
