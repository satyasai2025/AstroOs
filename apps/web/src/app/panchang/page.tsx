'use client';

import { LandingHeader } from "@/components/landing/LandingHeader";
import { PanchangWorkspaceView } from "@/components/panchang/PanchangWorkspaceView";
import { Footer } from "@/components/layout/Footer";

export default function PublicPanchangPage() {
  return (
    <div className="flex min-h-dvh flex-col justify-between bg-[#060814] text-slate-100 relative overflow-hidden">
      {/* Ambient background blur */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[350px] bg-gradient-to-b from-cyan-950/20 via-sky-950/10 to-transparent blur-3xl pointer-events-none" />
      <LandingHeader />
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 relative z-10">
        <PanchangWorkspaceView />
      </main>
      <Footer />
    </div>
  );
}
