"use client";

import { useState } from "react";
import Link from "next/link";
import { Modal } from "@/components/ui";
import { initiateCheckout } from "@/lib/billing";

interface UpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  featureName: string;
  requiredPlan?: "PRO" | "RESEARCH";
  description?: string;
}

export function UpgradeModal({
  isOpen,
  onClose,
  featureName,
  requiredPlan = "PRO",
  description,
}: UpgradeModalProps) {
  const [loading, setLoading] = useState(false);

  const handleInstantUpgrade = async () => {
    setLoading(true);
    try {
      const res = await initiateCheckout({
        plan_code: requiredPlan,
        billing_cycle: "monthly",
        currency: "INR",
      });
      if (res.checkout_url) {
        window.location.href = res.checkout_url;
      }
    } catch {
      window.location.href = "/pricing";
    }
  };

  return (
    <Modal
      open={isOpen}
      onClose={onClose}
      title="Unlock Premium Feature"
      width={540}
    >
      <div className="space-y-6 pt-2">
        <div className="text-center space-y-2">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-2xl">
            ✨
          </div>
          <h3 className="text-lg font-bold text-white">
            {featureName} is a {requiredPlan} Feature
          </h3>
          <p className="text-xs text-slate-400 leading-relaxed max-w-sm mx-auto">
            {description ||
              `Upgrade to the AstroOS ${requiredPlan} tier to unlock advanced predictive calculation tools, unlimited chart saves, and research workspaces.`}
          </p>
        </div>

        {/* Benefits Preview */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-2.5 text-xs text-slate-300">
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
            {requiredPlan} Plan Highlights:
          </p>
          <div className="flex items-center gap-2">
            <span className="text-cyan-400">✓</span>
            <span>{requiredPlan === "RESEARCH" ? "100 Saved Charts & Custom AstroDSL Rule IDE" : "50 Saved Horoscopes & Full Chart Edit Mode"}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-cyan-400">✓</span>
            <span>{requiredPlan === "RESEARCH" ? "Statistical Correlation & Full Knowledge Graph" : "Prashna Engine & Narrative PDF Export Reports"}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-cyan-400">✓</span>
            <span>Transparent pricing starting from ₹1,999/mo (+ 18% GST)</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 pt-2">
          <Link
            href="/pricing"
            onClick={onClose}
            className="flex-1 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-750 py-2.5 text-center text-xs font-bold text-slate-200 transition"
          >
            Compare All Plans
          </Link>
          <button
            type="button"
            onClick={handleInstantUpgrade}
            disabled={loading}
            className="flex-1 rounded-xl bg-cyan-500 hover:bg-cyan-400 py-2.5 text-center text-xs font-bold text-slate-950 transition shadow"
          >
            {loading ? "Starting Checkout..." : `Upgrade to ${requiredPlan} Now`}
          </button>
        </div>
      </div>
    </Modal>
  );
}
