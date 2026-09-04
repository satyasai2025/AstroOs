"use client";

import { useState } from "react";
import { Card } from "@/components/ui";

const BPHS_CHAPTERS = [
  {
    chapter: 1,
    name: "The Creation (Srishti Krama)",
    slokas: "Slokas 1–15",
    description: "Invocation of Lord Vishnu and the cosmic manifestation of Grahas.",
  },
  {
    chapter: 3,
    name: "Planetary Characters and Description (Graha Guna Swaroopa)",
    slokas: "Slokas 1–62",
    description: "Detailed natural benefics/malefics, exaltation/debilitation degrees, colors, castes, and dhatus.",
  },
  {
    chapter: 12,
    name: "Effects of the 1st House (Lagna Bhava Phala)",
    slokas: "Slokas 1–28",
    description: "Physical constitution, longevity, character, complexion, and health.",
  },
  {
    chapter: 36,
    name: "Special Planetary Yogas (Raja Yogas)",
    slokas: "Slokas 1–45",
    description: "Kendra-Trikona lord associations, Gaja Kesari, Dharma-Karmadhipati, and Vipareeta Raja Yogas.",
  },
  {
    chapter: 46,
    name: "Vimshottari Dasha System",
    slokas: "Slokas 1–110",
    description: "The 120-year nakshatra-based planetary period calculations and sub-period antardashas.",
  },
];

export default function AdminBphsSlokasPage() {
  const [chapters, setChapters] = useState(BPHS_CHAPTERS);
  const [search, setSearch] = useState("");

  const filtered = chapters.filter(
    (c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.description.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div>
        <div className="inline-flex items-center gap-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-0.5 text-xs font-semibold text-amber-400">
          <span>📜</span>
          <span>Brihat Parashara Hora Shastra &bull; Sloka Corpus</span>
        </div>
        <h1 className="text-2xl font-extrabold text-white mt-2">
          BPHS Chapter &amp; Sloka Registry
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Authoritative classical Sanskrit treatise chapters used by the Governed AI RAG engine.
        </p>
      </div>

      <div className="flex gap-4">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search chapters or topics (e.g. Raja Yoga, Vimshottari, Dasha)..."
          className="flex-1 rounded-xl border border-slate-700 bg-slate-950 px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:border-amber-400 focus:outline-none"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered.map((c) => (
          <Card key={c.chapter} className="p-5 border border-slate-800 bg-slate-900/60 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-amber-400 text-xs">Chapter {c.chapter}</span>
              <span className="text-[11px] text-slate-400 font-mono">{c.slokas}</span>
            </div>
            <h3 className="text-sm font-bold text-white">{c.name}</h3>
            <p className="text-xs text-slate-300 leading-relaxed">{c.description}</p>
          </Card>
        ))}
      </div>
    </div>
  );
}
