"use client";

import dynamic from "next/dynamic";

const RelocationDiscoveryStudio = dynamic(
  () =>
    import("@/components/relocation/RelocationDiscoveryStudio").then(
      (mod) => mod.RelocationDiscoveryStudio
    ),
  {
    ssr: false,
    loading: () => (
      <div className="max-w-7xl mx-auto space-y-6 pb-12 p-12 text-center text-slate-400 text-xs font-mono">
        <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-amber-400 border-t-transparent mb-2" />
        <p>Loading Relocation Studio...</p>
      </div>
    ),
  }
);

export default function RelocationPage() {
  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-12">
      <RelocationDiscoveryStudio />
    </div>
  );
}
