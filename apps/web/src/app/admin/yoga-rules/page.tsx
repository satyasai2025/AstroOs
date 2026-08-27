"use client";

import { useState } from "react";
import { Card } from "@/components/ui";

const INITIAL_YOGAS = [
  {
    id: "yoga_gaja_kesari",
    name: "Gaja Kesari Yoga",
    source: "Brihat Parashara Hora Shastra Ch. 36",
    condition: "Jupiter in Kendra (1, 4, 7, 10) from Lagna or Moon, aspected by benefics.",
    effect: "Confers profound intellect, lasting fame, scholarly eminence, and virtuous wealth.",
    status: "active",
  },
  {
    id: "yoga_hamsa",
    name: "Hamsa Mahapurusha Yoga",
    source: "Phaladeepika Ch. 6",
    condition: "Jupiter in Sagittarius, Pisces, or Cancer situated in a Kendra house.",
    effect: "Endows noble spiritual character, righteous conduct, and scriptural mastery.",
    status: "active",
  },
  {
    id: "yoga_bhadra",
    name: "Bhadra Mahapurusha Yoga",
    source: "Saravali Ch. 31",
    condition: "Mercury in Gemini or Virgo in a Kendra house.",
    effect: "Exceptional mathematical genius, eloquence, longevity, and high administrative post.",
    status: "active",
  },
  {
    id: "yoga_ruchaka",
    name: "Ruchaka Mahapurusha Yoga",
    source: "Brihat Parashara Hora Shastra Ch. 36",
    condition: "Mars in Aries, Scorpio, or Capricorn situated in a Kendra house.",
    effect: "Courage, martial prowess, victory over obstacles, leadership, and physical vigor.",
    status: "active",
  },
];

export default function AdminYogaRulesPage() {
  const [yogas, setYogas] = useState(INITIAL_YOGAS);

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div>
        <div className="inline-flex items-center gap-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-0.5 text-xs font-semibold text-amber-400">
          <span>📜</span>
          <span>Classical Shastra Knowledge &bull; Planetary Combinations</span>
        </div>
        <h1 className="text-2xl font-extrabold text-white mt-2">
          Yoga Rules &amp; Combinatorial Registry
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Administer verified classical planetary yogas, formation conditions, and astrological manifestation logic.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {yogas.map((y) => (
          <Card key={y.id} className="p-5 border border-slate-800 bg-slate-900/60 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white">{y.name}</h3>
              <span className="rounded-full bg-emerald-500/20 text-emerald-400 px-2 py-0.5 text-[10px] font-bold">
                {y.status}
              </span>
            </div>
            <div className="text-xs text-amber-400 font-semibold">{y.source}</div>
            <div className="rounded bg-slate-950 p-2.5 text-xs text-slate-300 font-mono">
              <span className="text-slate-500 font-bold">Condition: </span>
              {y.condition}
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">{y.effect}</p>
          </Card>
        ))}
      </div>
    </div>
  );
}
