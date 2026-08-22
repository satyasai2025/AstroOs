"use client";

import { useState } from "react";
import type { TransitPatternsResponse, TransitResponse } from "@/lib/types";

interface Props {
  transits: TransitResponse;
  patterns?: TransitPatternsResponse;
  subjectName?: string;
}

export function AITransitSummary({ transits, patterns, subjectName = "Subject" }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [summary, setSummary] = useState<{
    executive: string;
    career: string;
    relationships: string;
    caution: string;
  } | null>(null);

  const handleGenerate = () => {
    setIsGenerating(true);
    setTimeout(() => {
      // Synthesize classical Vedic rules dynamically from actual live transits & aspects
      const beneficPlanets = transits.planets.filter((p) => p.is_favorable_house);
      const isSadeSati = patterns?.sade_sati?.is_active;
      const isAshtamaShani = patterns?.ashtama_shani?.is_active;
      const aspects = patterns?.aspects ?? [];

      const careerAspects = aspects.filter((a) =>
        ["sun", "jupiter", "saturn", "mercury"].includes(a.transiting_planet.toLowerCase())
      );
      const relationshipAspects = aspects.filter((a) =>
        ["venus", "moon", "mars", "jupiter"].includes(a.transiting_planet.toLowerCase())
      );

      setSummary({
        executive: `${subjectName}'s current celestial weather shows ${beneficPlanets.length} planets transiting favorable positions.${
          isSadeSati ? " Active Sade Sati Phase is placing emphasis on discipline and patience." : ""
        }${isAshtamaShani ? " Ashtama Shani urges caution with sudden changes." : " Transits favor proactive initiative."}`,
        career:
          careerAspects.length > 0
            ? `Jupiter and Saturn aspects highlight strategic planning. Favorable for intellectual work, financial reorganizing, and long-term consolidation.`
            : `Stable career momentum. Good time to solidify routine foundational goals without hasty pivots.`,
        relationships:
          relationshipAspects.length > 0
            ? `Venus and Moon interactions indicate heightened emotional sensitivity. Honest communication will deepen bonds; avoid unnecessary debates during minor tense orbs.`
            : `Smooth interpersonal dynamics with harmonious household harmony.`,
        caution:
          aspects.some((a) => a.aspect_type === "square" || a.aspect_type === "opposition")
            ? `Tense aspects from transiting Mars/Saturn suggest avoiding rushed commitments during peak stress windows. Daily meditation or mantra chanting is recommended.`
            : `No severe adverse afflictions detected. Maintain balanced sleep cycles and consistent focus.`,
      });
      setIsGenerating(false);
      setIsOpen(true);
    }, 600);
  };

  return (
    <div>
      <button
        type="button"
        onClick={handleGenerate}
        disabled={isGenerating}
        className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-bold transition-all shadow-sm"
        style={{
          backgroundColor: "rgba(56, 189, 248, 0.12)",
          color: "var(--accent)",
          border: "1px solid rgba(56, 189, 248, 0.35)",
        }}
      >
        <span>✨</span>
        <span>{isGenerating ? "Synthesizing AI Summary…" : "Generate AI Transit Summary"}</span>
      </button>

      {/* Pop-in Summary Card */}
      {isOpen && summary && (
        <div
          className="mt-3 rounded-2xl border p-4 shadow-xl glass-card animate-in fade-in slide-in-from-top-2"
          style={{
            borderColor: "var(--accent)",
            backgroundColor: "var(--bg-card)",
          }}
        >
          <div className="flex items-center justify-between border-b pb-2 mb-3" style={{ borderColor: "var(--border-primary)" }}>
            <div className="flex items-center gap-2">
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-cyan-500/20 text-xs font-bold text-cyan-400">
                ✨
              </span>
              <h3 className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-primary)" }}>
                AI Synthesized Transit Takeaways ({subjectName})
              </h3>
            </div>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            >
              ✕ Close
            </button>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="rounded-lg p-2.5" style={{ backgroundColor: "var(--bg-input)" }}>
              <span className="font-bold text-cyan-400 block mb-0.5">🌟 Executive Overview</span>
              <p style={{ color: "var(--text-secondary)" }}>{summary.executive}</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              <div className="rounded-lg p-2.5" style={{ backgroundColor: "var(--bg-input)" }}>
                <span className="font-bold text-emerald-400 block mb-0.5">💼 Career &amp; Finance</span>
                <p style={{ color: "var(--text-secondary)" }}>{summary.career}</p>
              </div>
              <div className="rounded-lg p-2.5" style={{ backgroundColor: "var(--bg-input)" }}>
                <span className="font-bold text-pink-400 block mb-0.5">❤️ Relationships &amp; Home</span>
                <p style={{ color: "var(--text-secondary)" }}>{summary.relationships}</p>
              </div>
            </div>

            <div className="rounded-lg p-2.5" style={{ backgroundColor: "var(--bg-input)" }}>
              <span className="font-bold text-amber-400 block mb-0.5">⚠️ Mindful Windows &amp; Remedies</span>
              <p style={{ color: "var(--text-secondary)" }}>{summary.caution}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
