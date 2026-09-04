"use client";

import { ReactNode, useState } from "react";
import { UpgradeModal } from "@/components/premium/UpgradeModal";

interface FeatureGateProps {
  children: ReactNode;
  featureName: string;
  isLocked?: boolean;
  requiredPlan?: "PRO" | "RESEARCH";
  description?: string;
  fallback?: ReactNode;
}

export function FeatureGate({
  children,
  featureName,
  isLocked = false,
  requiredPlan = "PRO",
  description,
  fallback,
}: FeatureGateProps) {
  const [modalOpen, setModalOpen] = useState(false);

  if (!isLocked) {
    return <>{children}</>;
  }

  if (fallback) {
    return (
      <>
        <div onClick={() => setModalOpen(true)} className="cursor-pointer">
          {fallback}
        </div>
        <UpgradeModal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          featureName={featureName}
          requiredPlan={requiredPlan}
          description={description}
        />
      </>
    );
  }

  return (
    <>
      <div
        onClick={() => setModalOpen(true)}
        className="relative group cursor-pointer overflow-hidden rounded-xl border border-slate-800 bg-slate-900/40 p-4 transition hover:border-cyan-500/40"
      >
        <div className="opacity-40 pointer-events-none filter blur-[1px]">
          {children}
        </div>
        <div className="absolute inset-0 flex items-center justify-center bg-slate-950/70 p-4 text-center">
          <div className="space-y-1.5">
            <span className="inline-flex items-center gap-1 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-2.5 py-0.5 text-[10px] font-bold text-cyan-300">
              🔒 {requiredPlan} Plan Required
            </span>
            <p className="text-xs font-semibold text-white">{featureName}</p>
            <p className="text-[11px] text-cyan-400 group-hover:underline font-medium">
              Click to unlock &rarr;
            </p>
          </div>
        </div>
      </div>
      <UpgradeModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        featureName={featureName}
        requiredPlan={requiredPlan}
        description={description}
      />
    </>
  );
}
