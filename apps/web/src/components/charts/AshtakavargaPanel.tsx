import { useMemo, useState } from "react";
import type {
  AllAshtakavargaResponse,
  BhinnashtakavargaResponse,
  WorkflowAnalysisResponse,
} from "@/lib/types";

const RASHI_NAMES = [
  "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
  "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
];

const RASHI_SYMBOLS = [
  "♈", "♉", "♊", "♋", "♌", "♍",
  "♎", "♏", "♐", "♑", "♒", "♓",
];

const PLANET_ORDER = [
  "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
];

const PLANET_SYMBOLS: Record<string, string> = {
  Sun: "☉", Moon: "☽", Mars: "♂", Mercury: "☿",
  Jupiter: "♃", Venus: "♀", Saturn: "♄", Rahu: "☊", Ketu: "☋",
};

function planetLabel(p: string): string {
  return p.charAt(0).toUpperCase() + p.slice(1);
}

/** Color for a SAV bindu count on the 0–56 scale (Sarvashtakavarga). */
function savColor(count: number): string {
  if (count >= 40) return "#22c55e";       // green - very strong
  if (count >= 32) return "#84cc16";       // light green
  if (count >= 24) return "#facc15";       // yellow - average
  if (count >= 16) return "#fb923c";       // orange
  return "#ef4444";                        // red - weak
}

/** Color for a BAV bindu count on the 0–8 scale. */
function bavBg(count: number): string {
  const alpha = 0.15 + (count / 8) * 0.55;
  const base = count >= 5 ? "34,197,94" : count >= 3 ? "250,204,21" : "239,68,68";
  return `rgba(${base}, ${alpha})`;
}

function toRashiIndex(rashi: string): number {
  const idx = RASHI_NAMES.findIndex((r) => r.toLowerCase() === rashi.toLowerCase());
  return idx === -1 ? 0 : idx;
}

interface Row {
  house: number;
  rashi: string;
  symbol: string;
  count: number;
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function SectionHeader({ icon, title, subtitle }: { icon?: string; title: string; subtitle?: string }) {
  return (
    <div className="mb-3 flex items-baseline gap-2">
      {icon && <span className="text-lg" aria-hidden="true">{icon}</span>}
      <h3 className="text-sm font-semibold uppercase tracking-wide text-amber-300/80">{title}</h3>
      {subtitle && <span className="text-xs text-slate-500">{subtitle}</span>}
    </div>
  );
}

function HeroMetrics({ sarva }: { sarva: NonNullable<AllAshtakavargaResponse["sarvashtakavarga"]> }) {
  const rows: Row[] = sarva.bindus_by_rashi
    .map((count, i) => ({ house: i + 1, rashi: RASHI_NAMES[i], symbol: RASHI_SYMBOLS[i], count }))
    .sort((a, b) => b.count - a.count);

  const strongest = rows[0];
  const weakest = rows[rows.length - 1];
  const avg = sarva.total_bindus / 12;

  const totalRating =
    sarva.total_bindus >= 337 ? "Excellent" : sarva.total_bindus >= 300 ? "Very Good" : sarva.total_bindus >= 260 ? "Good" : "Average";

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <div className="glass-card p-4">
        <p className="text-xs text-slate-500">Total SAV Score</p>
        <p className="mt-1 text-3xl font-bold" style={{ color: "var(--text-primary)" }}>{sarva.total_bindus}</p>
        <p className="text-xs font-medium text-emerald-400">{totalRating}</p>
        <p className="mt-1 text-[11px] text-slate-500">Classical checksum: 337</p>
      </div>
      <div className="glass-card p-4">
        <p className="text-xs text-slate-500">Strongest House</p>
        <p className="mt-1 text-xl font-semibold" style={{ color: "var(--text-primary)" }}>
          {strongest.house}<sup>th</sup> House
        </p>
        <p className="text-xs font-medium text-emerald-400">{strongest.count} Points <span className="text-slate-500">· {strongest.symbol} {strongest.rashi}</span></p>
      </div>
      <div className="glass-card p-4">
        <p className="text-xs text-slate-500">Weakest House</p>
        <p className="mt-1 text-xl font-semibold" style={{ color: "var(--text-primary)" }}>
          {weakest.house}<sup>th</sup> House
        </p>
        <p className="text-xs font-medium text-red-400">{weakest.count} Points <span className="text-slate-500">· {weakest.symbol} {weakest.rashi}</span></p>
      </div>
      <div className="glass-card p-4">
        <p className="text-xs text-slate-500">Average per House</p>
        <p className="mt-1 text-xl font-semibold" style={{ color: "var(--text-primary)" }}>{avg.toFixed(1)}</p>
        <p className="text-xs text-slate-500">across all 12 rashis</p>
      </div>
    </div>
  );
}

function SAVHeatmap({ sarva, onSelectHouse }: {
  sarva: NonNullable<AllAshtakavargaResponse["sarvashtakavarga"]>;
  onSelectHouse: (house: number) => void;
}) {
  const max = Math.max(...sarva.bindus_by_rashi, 1);
  return (
    <div className="glass-card p-4">
      <SectionHeader icon="🕉" title="Sarvashtakavarga Chakra" subtitle="click a house for details" />
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {sarva.bindus_by_rashi.map((count, i) => (
          <button
            key={RASHI_NAMES[i]}
            type="button"
            onClick={() => onSelectHouse(i + 1)}
            title={`${RASHI_NAMES[i]} — ${count} bindus`}
            className="group rounded-lg border p-3 text-left transition hover:-translate-y-0.5 hover:shadow-lg"
            style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
          >
            <div className="flex items-center justify-between text-xs">
              <span style={{ color: "var(--text-muted)" }}>{RASHI_SYMBOLS[i]} {RASHI_NAMES[i].slice(0, 3)}</span>
              <span className="font-semibold" style={{ color: savColor(count) }}>{count}</span>
            </div>
            <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-white/5">
              <div className="h-full rounded-full" style={{ width: `${(count / max) * 100}%`, backgroundColor: savColor(count) }} />
            </div>
            <p className="mt-1 text-[10px]" style={{ color: "var(--text-muted)" }}>House {i + 1}</p>
          </button>
        ))}
      </div>
      <div className="mt-3 flex items-center gap-3 text-[10px]" style={{ color: "var(--text-muted)" }}>
        <span className="flex items-center gap-1"><span className="inline-block h-2 w-2 rounded-full" style={{ background: "#ef4444" }} /> Low</span>
        <span className="flex items-center gap-1"><span className="inline-block h-2 w-2 rounded-full" style={{ background: "#facc15" }} /> Average</span>
        <span className="flex items-center gap-1"><span className="inline-block h-2 w-2 rounded-full" style={{ background: "#22c55e" }} /> High</span>
      </div>
    </div>
  );
}

function HouseRanking({ sarva }: { sarva: NonNullable<AllAshtakavargaResponse["sarvashtakavarga"]> }) {
  const rows: Row[] = sarva.bindus_by_rashi
    .map((count, i) => ({ house: i + 1, rashi: RASHI_NAMES[i], symbol: RASHI_SYMBOLS[i], count }))
    .sort((a, b) => b.count - a.count);

  const medals = ["🥇", "🥈", "🥉"];
  const max = rows[0].count;

  return (
    <div className="glass-card p-4">
      <SectionHeader icon="🏆" title="House Ranking" />
      <ol className="space-y-1.5">
        {rows.map((r, idx) => (
          <li key={r.house} className="flex items-center gap-2 text-xs">
            <span className="w-6 shrink-0 text-center">{medals[idx] ?? idx + 1}</span>
            <span className="w-24 shrink-0 font-medium" style={{ color: "var(--text-primary)" }}>
              {r.house}<sup>th</sup> · {r.symbol} {r.rashi.slice(0, 3)}
            </span>
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-white/5">
              <div className="h-full rounded-full" style={{ width: `${(r.count / max) * 100}%`, backgroundColor: savColor(r.count) }} />
            </div>
            <span className="w-7 shrink-0 text-right font-semibold" style={{ color: savColor(r.count) }}>{r.count}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

function PlanetSelector({ planets, selected, onSelect }: {
  planets: string[];
  selected: string;
  onSelect: (p: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {planets.map((p) => {
        const active = p === selected;
        return (
          <button
            key={p}
            type="button"
            onClick={() => onSelect(p)}
            aria-pressed={active}
            className="rounded-full px-2.5 py-1 text-xs font-semibold transition"
            style={{
              backgroundColor: active ? "var(--accent)" : "var(--bg-card)",
              color: active ? "var(--accent-text)" : "var(--text-secondary)",
              border: `1px solid ${active ? "var(--accent)" : "var(--border-primary)"}`,
            }}
            title={planetLabel(p)}
          >
            <span aria-hidden="true">{PLANET_SYMBOLS[p] ?? ""}</span> <span className="hidden sm:inline">{planetLabel(p)}</span>
          </button>
        );
      })}
    </div>
  );
}

function BAVHeatmap({ bhinna, planets }: {
  bhinna: BhinnashtakavargaResponse[];
  planets: string[];
}) {
  const byPlanet = new Map(bhinna.map((b) => [b.target_planet, b]));
  return (
    <div className="glass-card p-4">
      <SectionHeader icon="🗺️" title="Bhinnashtakavarga Heatmap" subtitle="planet support per house" />
      <div className="overflow-x-auto">
        <table className="w-full min-w-[420px] border-collapse text-center text-xs">
          <thead>
            <tr>
              <th className="p-1 text-left text-slate-500">Planet</th>
              {RASHI_NAMES.map((r, i) => (
                <th key={r} className="p-1 font-normal text-slate-500" title={`${r}`}>
                  <span className="block text-[10px]">{RASHI_SYMBOLS[i]}</span>
                  <span className="hidden lg:block text-[9px]">{i + 1}</span>
                </th>
              ))}
              <th className="p-1 text-slate-500">Total</th>
            </tr>
          </thead>
          <tbody>
            {planets.map((planet) => {
              const b = byPlanet.get(planet);
              if (!b) return null;
              return (
                <tr key={planet}>
                  <td className="p-1 text-left font-medium" style={{ color: "var(--text-primary)" }}>
                    <span aria-hidden="true">{PLANET_SYMBOLS[planet] ?? ""}</span> <span className="hidden sm:inline">{planetLabel(planet)}</span>
                  </td>
                  {b.bindus_by_rashi.map((count, i) => (
                    <td key={i} className="p-1">
                      <span
                        className="inline-block h-6 w-6 rounded-md text-[11px] font-semibold leading-6"
                        style={{ backgroundColor: bavBg(count), color: count >= 5 ? "#dcfce7" : count <= 2 ? "#fee2e2" : "var(--text-primary)" }}
                        title={`${RASHI_NAMES[i]}: ${count}`}
                      >
                        {count}
                      </span>
                    </td>
                  ))}
                  <td className="p-1 font-semibold" style={{ color: "var(--text-primary)" }}>{b.total_bindus}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="mt-3 flex items-center justify-between text-[10px]" style={{ color: "var(--text-muted)" }}>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1"><span className="inline-block h-2 w-2 rounded-full" style={{ background: "rgba(239,68,68,.6)" }} /> 0–2</span>
          <span className="flex items-center gap-1"><span className="inline-block h-2 w-2 rounded-full" style={{ background: "rgba(250,204,21,.6)" }} /> 3–4</span>
          <span className="flex items-center gap-1"><span className="inline-block h-2 w-2 rounded-full" style={{ background: "rgba(34,197,94,.6)" }} /> 5–8</span>
        </div>
        <span>Scale: 0–8 bindus per house</span>
      </div>
    </div>
  );
}

function PlanetStrengthCards({ bhinna, planets, onSelect }: {
  bhinna: BhinnashtakavargaResponse[];
  planets: string[];
  onSelect: (p: string) => void;
}) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
      {planets.map((planet) => {
        const b = bhinna.find((x) => x.target_planet === planet);
        if (!b) return null;
        const avg = b.total_bindus / 12;
        const strong = b.bindus_by_rashi
          .map((c, i) => ({ h: i + 1, c }))
          .filter((x) => x.c >= 5)
          .map((x) => x.h);
        const weak = b.bindus_by_rashi
          .map((c, i) => ({ h: i + 1, c }))
          .filter((x) => x.c <= 2)
          .map((x) => x.h);
        const max = Math.max(...b.bindus_by_rashi, 1);
        return (
          <button
            key={planet}
            type="button"
            onClick={() => onSelect(planet)}
            className="glass-card p-4 text-left transition hover:-translate-y-0.5 hover:shadow-lg"
          >
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                <span aria-hidden="true">{PLANET_SYMBOLS[planet] ?? ""}</span> {planetLabel(planet)}
              </p>
              <span className="text-xs text-slate-500">Avg {avg.toFixed(1)}</span>
            </div>
            <div className="mt-2 flex gap-1">
              {b.bindus_by_rashi.map((count, i) => (
                <div key={i} className="h-2 flex-1 rounded-full" style={{ backgroundColor: bavBg(count), maxWidth: 8 }} title={`${RASHI_NAMES[i]}: ${count}`} />
              ))}
            </div>
            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[11px]">
              {strong.length > 0 && (
                <span className="flex items-center gap-1">
                  <span className="text-emerald-400">▲</span> Strong: <span className="text-slate-300">{strong.join(", ")}</span>
                </span>
              )}
              {weak.length > 0 && (
                <span className="flex items-center gap-1">
                  <span className="text-red-400">▼</span> Weak: <span className="text-slate-300">{weak.join(", ")}</span>
                </span>
              )}
            </div>
            <p className="mt-2 text-xs text-slate-500">Total: <span className="font-semibold text-slate-300">{b.total_bindus}</span> bindus</p>
          </button>
        );
      })}
    </div>
  );
}

function HouseDetail({ house, sarva, bhinna, onClose }: {
  house: number;
  sarva: NonNullable<AllAshtakavargaResponse["sarvashtakavarga"]>;
  bhinna: BhinnashtakavargaResponse[];
  onClose: () => void;
}) {
  const idx = house - 1;
  const rashi = RASHI_NAMES[idx];
  const sav = sarva.bindus_by_rashi[idx];
  const benefics = bhinna.filter((b) => b.bindus_by_rashi[idx] >= 5).map((b) => planetLabel(b.target_planet));
  const average = bhinna.filter((b) => b.bindus_by_rashi[idx] >= 3 && b.bindus_by_rashi[idx] <= 4).map((b) => planetLabel(b.target_planet));
  const malefics = bhinna.filter((b) => b.bindus_by_rashi[idx] <= 2).map((b) => planetLabel(b.target_planet));

  return (
    <div className="glass-card p-4">
      <div className="mb-2 flex items-center justify-between">
        <SectionHeader icon="🏠" title={`House ${house} — ${rashi}`} />
        <button type="button" onClick={onClose} className="text-xs text-slate-400 hover:text-slate-200" aria-label="Close house detail">✕</button>
      </div>
      <div className="mb-3 flex items-center gap-3">
        <span className="text-3xl" aria-hidden="true">{RASHI_SYMBOLS[idx]}</span>
        <div>
          <p className="text-xs text-slate-500">Total SAV</p>
          <p className="text-2xl font-bold" style={{ color: savColor(sav) }}>{sav}</p>
        </div>
      </div>
      <div className="grid grid-cols-1 gap-2 text-xs sm:grid-cols-3">
        <div className="rounded-lg bg-emerald-500/10 p-2">
          <p className="mb-1 font-medium text-emerald-400">Benefics (≥5)</p>
          <p style={{ color: "var(--text-primary)" }}>{benefics.length > 0 ? benefics.join(", ") : "—"}</p>
        </div>
        <div className="rounded-lg bg-white/5 p-2">
          <p className="mb-1 font-medium text-slate-300">Average (3–4)</p>
          <p style={{ color: "var(--text-primary)" }}>{average.length > 0 ? average.join(", ") : "—"}</p>
        </div>
        <div className="rounded-lg bg-red-500/10 p-2">
          <p className="mb-1 font-medium text-red-400">Malefics (≤2)</p>
          <p style={{ color: "var(--text-primary)" }}>{malefics.length > 0 ? malefics.join(", ") : "—"}</p>
        </div>
      </div>
    </div>
  );
}

function TransitAssistant({ transits, sarva }: {
  transits: WorkflowAnalysisResponse["transits"];
  sarva: NonNullable<AllAshtakavargaResponse["sarvashtakavarga"]>;
}) {
  const planets = useMemo(
    () => (transits.planets ?? []).filter((p) => p.planet !== "rahu" && p.planet !== "ketu" && p.ashtakavarga_bindus !== null),
    [transits],
  );
  const [selected, setSelected] = useState(planets[0]?.planet ?? planets[0]?.planet ?? "");

  const current = planets.find((p) => p.planet === selected) ?? planets[0];
  if (!current) {
    return (
      <div className="glass-card p-4">
        <SectionHeader icon="⭐" title="Transit Assistant" />
        <p className="text-sm text-slate-400">Transit data not available for this chart.</p>
      </div>
    );
  }

  const transitRashiIdx = current.transit_rashi ? toRashiIndex(current.transit_rashi) : 0;
  const transitSav = current.ashtakavarga_bindus ?? 0;
  const rating = transitSav >= 5 ? "★★★★★" : transitSav >= 4 ? "★★★★☆" : transitSav >= 3 ? "★★★☆☆" : transitSav >= 2 ? "★★☆☆☆" : "★☆☆☆☆";
  const verdict = transitSav >= 5 ? "Excellent period — strong planetary support." : transitSav >= 4 ? "Good — favorable support." : transitSav >= 3 ? "Average — mixed results." : transitSav <= 1 ? "Avoid risk — weak support." : "Neutral — proceed with care.";

  // Show SAV for each rashi as future transit zones
  const zones = sarva.bindus_by_rashi
    .map((count, i) => ({ rashi: RASHI_NAMES[i], symbol: RASHI_SYMBOLS[i], count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 3);

  return (
    <div className="glass-card p-4">
      <SectionHeader icon="⭐" title="Transit Assistant" subtitle="SAV suitability by transit" />
      <div className="flex flex-wrap items-center gap-1.5">
        {planets.map((p) => (
          <button
            key={p.planet}
            type="button"
            onClick={() => setSelected(p.planet)}
            className="rounded-full px-2.5 py-1 text-xs font-semibold transition"
            style={{
              backgroundColor: p.planet === current.planet ? "var(--accent)" : "var(--bg-card)",
              color: p.planet === current.planet ? "var(--accent-text)" : "var(--text-secondary)",
              border: `1px solid ${p.planet === current.planet ? "var(--accent)" : "var(--border-primary)"}`,
            }}
          >
            <span aria-hidden="true">{PLANET_SYMBOLS[planetLabel(p.planet)] ?? ""}</span> {planetLabel(p.planet)}
          </button>
        ))}
      </div>
      <div className="mt-3 grid grid-cols-1 gap-2 rounded-lg border p-3 sm:grid-cols-3" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
        <div>
          <p className="text-xs text-slate-500">Current Transit</p>
          <p className="font-semibold" style={{ color: "var(--text-primary)" }}>{current.transit_rashi}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">House from Moon</p>
          <p className="font-semibold" style={{ color: "var(--text-primary)" }}>{current.house_from_natal_moon}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">SAV</p>
          <p className="font-semibold" style={{ color: savColor(transitSav) }}>{transitSav}</p>
        </div>
      </div>
      <p className="mt-2 text-lg tracking-tight" aria-label={`Rating ${rating}`}>{rating}</p>
      <p className="text-xs" style={{ color: "var(--text-secondary)" }}>{verdict}</p>

      <div className="mt-3">
        <p className="mb-1.5 text-xs text-slate-500">Top transit zones</p>
        <div className="flex gap-2">
          {zones.map((z) => (
            <div key={z.rashi} className="flex-1 rounded-lg border p-2 text-center" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
              <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{z.symbol} {z.rashi.slice(0, 3)}</p>
              <p className="text-xs font-medium" style={{ color: savColor(z.count) }}>{z.count}</p>
              <p className="text-[10px] text-slate-500">{z.count >= 32 ? "Excellent" : z.count >= 24 ? "Good" : "Average"}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function PredictionCards({ sarva, transits }: {
  sarva: NonNullable<AllAshtakavargaResponse["sarvashtakavarga"]>;
  transits: WorkflowAnalysisResponse["transits"];
}) {
  // Simple heuristics from SAV house strengths + transit positions.
  const houses = sarva.bindus_by_rashi;
  const score = (h: number) => houses[h - 1] ?? 0;
  const stars = (n: number) => (n >= 40 ? "★★★★★" : n >= 32 ? "★★★★☆" : n >= 26 ? "★★★☆☆" : n >= 20 ? "★★☆☆☆" : "★☆☆☆☆");

  // Average of relevant houses for each domain
  const health = Math.round((score(1) + score(6) + score(8)) / 3);
  const career = Math.round((score(10) + score(2) + score(11)) / 3);
  const finance = Math.round((score(2) + score(11) + score(5)) / 3);
  const marriage = Math.round((score(7) + score(2)) / 2);
  const education = Math.round((score(4) + score(5) + score(9)) / 3);
  const travel = Math.round((score(3) + score(12) + score(9)) / 3);

  const items = [
    { label: "Career", value: career },
    { label: "Finance", value: finance },
    { label: "Marriage", value: marriage },
    { label: "Education", value: education },
    { label: "Health", value: health },
    { label: "Travel", value: travel },
  ];

  return (
    <div className="glass-card p-4">
      <SectionHeader icon="🔮" title="Prediction Strength" subtitle="based on SAV house support" />
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {items.map((item) => (
          <div key={item.label} className="rounded-lg border p-2.5 text-center" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
            <p className="text-xs" style={{ color: "var(--text-secondary)" }}>{item.label}</p>
            <p className="mt-0.5 text-sm tracking-tight">{stars(item.value)}</p>
            <p className="text-[10px]" style={{ color: savColor(item.value) }}>{item.value} pts</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function ClassicalReferences({ version }: { version: string }) {
  const sources = [
    { name: "BPHS", text: "Brihat Parashara Hora Shastra — the foundational classical source for Ashtakavarga rules." },
    { name: "Saravali", text: "Kalyana Varma's Saravali — companion treatise with extensive Ashtakavarga guidelines." },
    { name: "Phaladeepika", text: "Mantreswara's Phaladeepika — houses and Ashtakavarga interpretation." },
    { name: "Jataka Parijata", text: "Vaidyanatha Dikshita — advanced transit and Ashtakavarga analysis." },
  ];
  return (
    <div className="glass-card p-4">
      <SectionHeader icon="📜" title="Classical References" subtitle={`rule version ${version}`} />
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {sources.map((s) => (
          <details key={s.name} className="group rounded-lg border p-3" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
            <summary className="cursor-pointer text-xs font-semibold" style={{ color: "var(--text-primary)" }}>
              <span className="group-open:hidden">▸ </span><span className="hidden group-open:inline">▾ </span>{s.name}
            </summary>
            <p className="mt-2 text-xs" style={{ color: "var(--text-secondary)" }}>{s.text}</p>
          </details>
        ))}
      </div>
    </div>
  );
}

function ExportPanel() {
  const handleExportCsv = () => {
    // Placeholder — actual CSV export wires to the live chart data via a prop.
  };
  const btn = "rounded-lg border px-3 py-1.5 text-xs font-semibold transition hover:opacity-90";
  return (
    <div className="glass-card p-4">
      <SectionHeader icon="📤" title="Export" />
      <div className="flex flex-wrap gap-2">
        <button type="button" onClick={handleExportCsv} className={btn} style={{ borderColor: "var(--border-primary)", color: "var(--text-secondary)" }}>CSV</button>
        <button type="button" className={btn} style={{ borderColor: "var(--border-primary)", color: "var(--text-secondary)" }}>PNG</button>
        <button type="button" className={btn} style={{ borderColor: "var(--border-primary)", color: "var(--text-secondary)" }}>PDF</button>
        <button type="button" className={btn} style={{ borderColor: "var(--border-primary)", color: "var(--text-secondary)" }}>Research Report</button>
      </div>
    </div>
  );
}

// ── Main Panel ───────────────────────────────────────────────────────────────

interface Props {
  result: WorkflowAnalysisResponse;
}

export default function AshtakavargaPanel({ result }: Props) {
  const av = result.ashtakavarga;
  const [selectedPlanet, setSelectedPlanet] = useState<string>("Sun");
  const [selectedHouse, setSelectedHouse] = useState<number | null>(null);

  if (!av) {
    return (
      <div className="glass-card flex flex-col items-center gap-4 p-8 text-center">
        <h2 className="text-lg font-semibold">Ashtakavarga</h2>
        <p className="text-sm text-slate-400">
          Ashtakavarga data is not available for this chart. Run a full analysis
          with the strength module enabled to populate the Ashtakavarga workspace.
        </p>
      </div>
    );
  }

  // Traditional graha order; any extra entries (Rahu/Ketu etc.) appended.
  const byPlanet = new Map(av.bhinnashtakavarga.map((b) => [b.target_planet, b]));
  const orderedPlanets: string[] = [
    ...PLANET_ORDER.filter((p) => byPlanet.has(p)),
    ...Array.from(byPlanet.keys()).filter((p) => !PLANET_ORDER.includes(p)),
  ];

  const sarva = av.sarvashtakavarga;

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>Ashtakavarga</h2>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            Research-grade workspace — BAV · SAV · Transit · Predictions
          </p>
        </div>
        <span className="rounded-full border px-3 py-1 text-xs" style={{ borderColor: sarva.checksum_valid ? "#22c55e" : "#ef4444", color: sarva.checksum_valid ? "#4ade80" : "#f87171" }}>
          {sarva.checksum_valid ? "✓ SAV checksum valid (337)" : "✗ SAV checksum invalid"}
        </span>
      </div>

      {/* 1. Hero Summary */}
      <HeroMetrics sarva={sarva} />

      {/* 2. Main visualization: left SAV heatmap + right insights */}
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_420px]">
        <div className="space-y-4">
          <SAVHeatmap sarva={sarva} onSelectHouse={(h) => setSelectedHouse(h)} />
          {selectedHouse && (
            <HouseDetail
              house={selectedHouse}
              sarva={sarva}
              bhinna={av.bhinnashtakavarga}
              onClose={() => setSelectedHouse(null)}
            />
          )}
          <BAVHeatmap bhinna={av.bhinnashtakavarga} planets={orderedPlanets} />
        </div>
        <div className="space-y-4">
          <PlanetSelector planets={orderedPlanets} selected={selectedPlanet} onSelect={setSelectedPlanet} />
          <HouseRanking sarva={sarva} />
          <TransitAssistant transits={result.transits} sarva={sarva} />
        </div>
      </div>

      {/* 3. Planet-wise BAV cards */}
      <PlanetStrengthCards bhinna={av.bhinnashtakavarga} planets={orderedPlanets} onSelect={setSelectedPlanet} />

      {/* 4. Predictions */}
      <PredictionCards sarva={sarva} transits={result.transits} />

      {/* 5. Classical references + export */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ClassicalReferences version={sarva.rule_version} />
        <ExportPanel />
      </div>
    </div>
  );
}