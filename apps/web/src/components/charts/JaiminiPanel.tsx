"use client";

import { useEffect, useState } from "react";
import { computeJaiminiBundle } from "@/lib/jaimini-api";
import type {
  JaiminiBundleRequest,
  JaiminiBundleResponse,
  JaiminiDashaPeriodResponse,
  PredictionEvidenceResponse,
} from "@/lib/types";

/** Same lowercase->Title-Case helper the rest of the app applies to
 * planet/rashi tokens (see lib/api.ts's _titleCaseToken) — used here only
 * for the one field (KarakamsaHouseEntryResponse.planets) deliberately
 * left out of that global normalizer's key list, since "planets" is too
 * generic a name to safely add there. */
function titleCase(value: string): string {
  return value
    .replace(/_/g, " ")
    .split(" ")
    .map((w) => (w ? w[0].toUpperCase() + w.slice(1).toLowerCase() : w))
    .join(" ");
}

interface Props {
  result: unknown;
  request?: JaiminiBundleRequest | null;
}

function SectionHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-3 flex items-baseline gap-2">
      <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
        {title}
      </h3>
      {subtitle && <span className="text-xs" style={{ color: "var(--text-muted)" }}>{subtitle}</span>}
    </div>
  );
}

function CharaKarakaTable({ bundle }: { bundle: JaiminiBundleResponse }) {
  return (
    <div className="glass-card p-4">
      <SectionHeader
        title={`Chara Karakas (${bundle.chara_karaka.scheme === "ashta_karaka" ? "8" : "7"} karakas)`}
        subtitle={`Atmakaraka: ${bundle.chara_karaka.atmakaraka.planet} · Darakaraka: ${bundle.chara_karaka.darakaraka.planet}`}
      />
      <div className="w-full overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr style={{ color: "var(--text-muted)" }}>
              <th className="pb-1 text-left">Rank</th>
              <th className="pb-1 text-left">Karaka</th>
              <th className="pb-1 text-left">Planet</th>
              <th className="pb-1 text-left">Rashi</th>
              <th className="pb-1 text-right">Karaka °</th>
              <th className="pb-1 text-left">Tiebreak</th>
            </tr>
          </thead>
          <tbody>
            {bundle.chara_karaka.karakas.map((k) => (
              <tr key={k.rank} style={{ borderTop: "1px solid var(--border-primary)" }}>
                <td className="py-1" style={{ color: "var(--text-muted)" }}>{k.rank}</td>
                <td className="py-1 font-medium" style={{ color: "var(--text-primary)" }}>{k.karaka_name}</td>
                <td className="py-1">{k.planet}{k.is_retrograde ? " (R)" : ""}</td>
                <td className="py-1">{k.rashi}</td>
                <td className="py-1 text-right">{k.karaka_degree.toFixed(2)}°</td>
                <td className="py-1" style={{ color: "var(--text-muted)" }}>{k.tiebreak_rule ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ArudhaGrid({ bundle }: { bundle: JaiminiBundleResponse }) {
  return (
    <div className="glass-card p-4">
      <SectionHeader
        title="Arudha Padas (A1–A12)"
        subtitle={`Arudha Lagna: ${bundle.arudha.arudha_lagna.rashi} · Upapada Lagna: ${bundle.arudha.upapada_lagna.rashi}`}
      />
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4">
        {bundle.arudha.padas.map((p) => (
          <div
            key={p.pada_name}
            className="rounded-lg p-2 text-xs"
            style={{ border: "1px solid var(--border-primary)" }}
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold" style={{ color: "var(--accent)" }}>{p.pada_name}</span>
              <span style={{ color: "var(--text-muted)" }}>H{p.house_number}</span>
            </div>
            <div style={{ color: "var(--text-primary)" }}>{p.rashi}</div>
            <div style={{ color: "var(--text-muted)" }}>
              Lord {p.lord} → {p.lord_rashi}
            </div>
            {p.exception_applied && (
              <div className="mt-0.5" style={{ color: "var(--accent)" }}>same/7th shift applied</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function KarakamsaCard({ bundle }: { bundle: JaiminiBundleResponse }) {
  const k = bundle.karakamsa;
  if (!k) {
    return (
      <div className="glass-card p-4 text-xs" style={{ color: "var(--text-muted)" }}>
        Karakamsa not requested for this chart.
      </div>
    );
  }
  return (
    <div className="glass-card p-4">
      <SectionHeader title="Karakamsa / Swamsa" subtitle={`Atmakaraka: ${k.atmakaraka}`} />
      <dl className="mb-3 grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
        <div><dt style={{ color: "var(--text-muted)" }}>Karakamsa</dt><dd style={{ color: "var(--text-primary)" }}>{k.karakamsa_rashi}</dd></div>
        <div><dt style={{ color: "var(--text-muted)" }}>Swamsa</dt><dd style={{ color: "var(--text-primary)" }}>{k.swamsa_rashi}</dd></div>
        <div><dt style={{ color: "var(--text-muted)" }}>D1 Atmakaraka Sign</dt><dd style={{ color: "var(--text-primary)" }}>{k.d1_atmakaraka_rashi}</dd></div>
        <div><dt style={{ color: "var(--text-muted)" }}>D1 Lagna Sign</dt><dd style={{ color: "var(--text-primary)" }}>{k.d1_lagna_rashi}</dd></div>
      </dl>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4">
        {k.relative_houses.map((h) => (
          <div key={h.house_number} className="rounded-lg p-2 text-xs" style={{ border: "1px solid var(--border-primary)" }}>
            <div className="flex items-center justify-between">
              <span className="font-semibold" style={{ color: "var(--accent)" }}>H{h.house_number}</span>
              <span style={{ color: "var(--text-primary)" }}>{h.rashi}</span>
            </div>
            <div style={{ color: "var(--text-muted)" }}>
              {h.planets.length > 0 ? h.planets.map(titleCase).join(", ") : "—"}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function RashiAspectList({ bundle }: { bundle: JaiminiBundleResponse }) {
  return (
    <div className="glass-card p-4">
      <SectionHeader title="Rashi Aspect (Rashi Drishti)" subtitle="Only occupied signs shown" />
      {bundle.rashi_aspect.aspects.length === 0 ? (
        <p className="text-xs" style={{ color: "var(--text-muted)" }}>No occupied signs to report.</p>
      ) : (
        <ul className="space-y-1 text-xs">
          {bundle.rashi_aspect.aspects.map((a, i) => (
            <li key={i} className="flex items-center gap-2">
              <span style={{ color: "var(--text-primary)" }}>{a.from_rashi}</span>
              <span style={{ color: "var(--text-muted)" }}>({a.aspecting_planets.join(", ")})</span>
              <span style={{ color: "var(--accent)" }}>→</span>
              <span style={{ color: "var(--text-primary)" }}>{a.to_rashi}</span>
              {a.aspected_planets.length > 0 && (
                <span style={{ color: "var(--text-muted)" }}>({a.aspected_planets.join(", ")})</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function DashaPeriodRow({ period, depth = 0 }: { period: JaiminiDashaPeriodResponse; depth?: number }) {
  return (
    <>
      <div
        className="flex items-center justify-between rounded px-2 py-1 text-xs"
        style={{ marginLeft: depth * 16, border: "1px solid var(--border-primary)" }}
      >
        <span style={{ color: "var(--text-primary)" }}>{period.rashi}</span>
        <span style={{ color: "var(--text-muted)" }}>
          {new Date(period.start_date).toLocaleDateString()} – {new Date(period.end_date).toLocaleDateString()}
        </span>
      </div>
      {period.sub_periods.map((sp, i) => (
        <DashaPeriodRow key={i} period={sp} depth={depth + 1} />
      ))}
    </>
  );
}

function DashaCard({ title, dasha }: { title: string; dasha: JaiminiBundleResponse["chara_dasha"] }) {
  return (
    <div className="glass-card p-4">
      <SectionHeader
        title={title}
        subtitle={`Lagna: ${dasha.lagna_rashi} · Total cycle: ${dasha.total_cycle_years}y · Depth ${dasha.max_depth}`}
      />
      <div className="max-h-72 space-y-1 overflow-y-auto">
        {dasha.periods.map((p, i) => (
          <DashaPeriodRow key={i} period={p} />
        ))}
      </div>
    </div>
  );
}

function YogaCard({ yoga }: { yoga: PredictionEvidenceResponse }) {
  return (
    <div
      className="rounded-lg p-3 text-xs"
      style={{
        border: `1px solid ${yoga.is_matched ? "var(--accent)" : "var(--border-primary)"}`,
        opacity: yoga.is_matched ? 1 : 0.6,
      }}
    >
      <div className="mb-1 flex items-center justify-between">
        <span className="font-semibold" style={{ color: yoga.is_matched ? "var(--accent)" : "var(--text-primary)" }}>
          {yoga.rule.name}
        </span>
        <span style={{ color: "var(--text-muted)" }}>
          {yoga.is_matched ? `Present · ${yoga.confidence.score}%` : "Not present"}
        </span>
      </div>
      <p className="mb-1" style={{ color: "var(--text-secondary)" }}>{yoga.explanation}</p>
      <p style={{ color: "var(--text-muted)" }}>{yoga.rule.sutra_reference}</p>
    </div>
  );
}

function YogasList({ bundle }: { bundle: JaiminiBundleResponse }) {
  const matched = bundle.yogas.filter((y) => y.is_matched).length;
  return (
    <div className="glass-card p-4">
      <SectionHeader title="Jaimini Yogas" subtitle={`${matched} of ${bundle.yogas.length} present`} />
      <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
        {bundle.yogas.map((y) => (
          <YogaCard key={y.rule.rule_id} yoga={y} />
        ))}
      </div>
    </div>
  );
}

export default function JaiminiPanel({ request }: Props) {
  const [bundle, setBundle] = useState<JaiminiBundleResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!request) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    computeJaiminiBundle(request)
      .then((data) => {
        if (!cancelled) setBundle(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to compute Jaimini bundle.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [request]);

  if (!request) {
    return (
      <div className="glass-card p-6 text-sm" style={{ color: "var(--text-muted)" }}>
        No birth data available to compute Jaimini analysis.
      </div>
    );
  }

  if (loading) {
    return (
      <div className="glass-card p-6 text-sm" style={{ color: "var(--text-muted)" }}>
        Computing Chara Karaka, Arudha, Karakamsa, Dasha, and Yogas…
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card p-6 text-sm" style={{ color: "var(--accent)" }}>
        {error}
      </div>
    );
  }

  if (!bundle) return null;

  return (
    <div className="space-y-5">
      <CharaKarakaTable bundle={bundle} />
      <ArudhaGrid bundle={bundle} />
      <KarakamsaCard bundle={bundle} />
      <RashiAspectList bundle={bundle} />
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <DashaCard title="Chara Dasha" dasha={bundle.chara_dasha} />
        <DashaCard title="Narayana Dasha" dasha={bundle.narayana_dasha} />
      </div>
      <YogasList bundle={bundle} />
    </div>
  );
}
