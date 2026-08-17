"use client";

import { useState } from "react";
import { useTarabalaReport, type PlanetTara } from "@/lib/tarabala";

const NAKSHATRAS = [
  "ashwini", "bharani", "krittika", "rohini", "mrigashira", "ardra", "punarvasu", "pushya", "ashlesha",
  "magha", "purva_phalguni", "uttara_phalguni", "hasta", "chitra", "swati", "vishakha", "anuradha",
  "jyeshtha", "mula", "purva_ashadha", "uttara_ashadha", "shravana", "dhanishtha", "shatabhisha",
  "purva_bhadrapada", "uttara_bhadrapada", "revati",
];

const PLANET_GLYPHS: Record<string, string> = {
  sun: "Su", moon: "Mo", mars: "Ma", mercury: "Me", jupiter: "Ju",
  venus: "Ve", saturn: "Sa", rahu: "Ra", ketu: "Ke",
};

function TaraRow({ p }: { p: PlanetTara }) {
  return (
    <tr className="border-b" style={{ borderColor: "var(--border-primary)" }}>
      <td className="py-1 pr-3" style={{ color: "var(--text-primary)" }}>{PLANET_GLYPHS[p.planet] ?? p.planet}</td>
      <td className="py-1 pr-3" style={{ color: "var(--text-secondary)" }}>{p.nakshatra}</td>
      <td className="py-1 pr-3 capitalize" style={{ color: "var(--text-secondary)" }}>{p.name}</td>
      <td className="py-1">
        <span
          className="rounded-full px-1.5 py-0.5 text-[9px] font-medium uppercase"
          style={{
            color: p.is_favorable ? "#34d399" : "#f87171",
            border: `1px solid ${p.is_favorable ? "#34d399" : "#f87171"}`,
          }}
        >
          {p.is_favorable ? "Favorable" : "Unfavorable"}
        </span>
      </td>
    </tr>
  );
}

/**
 * AstroOS — Navatara / Tarabala display. Standalone research tool:
 * takes Janma Nakshatra + birth datetime directly (not yet wired to a
 * saved chart's workflow data) since this is a new, independent
 * technique from the rest of the chart pages — see
 * apps/api/services/tarabala_report_service.py.
 */
export function TarabalaPanel() {
  const [janmaNakshatra, setJanmaNakshatra] = useState("ashwini");
  const [lagnaNakshatra, setLagnaNakshatra] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [birthTime, setBirthTime] = useState("00:00");
  const [dashaChain, setDashaChain] = useState("");

  const birthDatetimeUtc = birthDate ? `${birthDate}T${birthTime}:00Z` : null;

  const { data, isLoading, error } = useTarabalaReport(
    birthDatetimeUtc
      ? {
          janma_nakshatra: janmaNakshatra,
          birth_datetime_utc: birthDatetimeUtc,
          lagna_nakshatra: lagnaNakshatra || null,
          dasha_chain: dashaChain
            ? dashaChain.split(",").map((s) => s.trim().toLowerCase()).filter(Boolean)
            : null,
        }
      : null
  );

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <label className="text-xs" style={{ color: "var(--text-muted)" }}>
          Janma Nakshatra
          <select
            value={janmaNakshatra}
            onChange={(e) => setJanmaNakshatra(e.target.value)}
            className="mt-1 block w-full rounded border px-2 py-1 text-xs"
            style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
          >
            {NAKSHATRAS.map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </label>
        <label className="text-xs" style={{ color: "var(--text-muted)" }}>
          Lagna Nakshatra (optional)
          <select
            value={lagnaNakshatra}
            onChange={(e) => setLagnaNakshatra(e.target.value)}
            className="mt-1 block w-full rounded border px-2 py-1 text-xs"
            style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
          >
            <option value="">—</option>
            {NAKSHATRAS.map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </label>
        <label className="text-xs" style={{ color: "var(--text-muted)" }}>
          Birth date (UTC)
          <input
            type="date"
            value={birthDate}
            onChange={(e) => setBirthDate(e.target.value)}
            className="mt-1 block w-full rounded border px-2 py-1 text-xs"
            style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
          />
        </label>
        <label className="text-xs" style={{ color: "var(--text-muted)" }}>
          Birth time (UTC)
          <input
            type="time"
            value={birthTime}
            onChange={(e) => setBirthTime(e.target.value)}
            className="mt-1 block w-full rounded border px-2 py-1 text-xs"
            style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
          />
        </label>
      </div>

      <label className="block text-xs" style={{ color: "var(--text-muted)" }}>
        Active dasha chain, Mahadasha first, comma-separated (optional — e.g. venus,sun,moon)
        <input
          type="text"
          value={dashaChain}
          onChange={(e) => setDashaChain(e.target.value)}
          placeholder="venus,sun,moon"
          className="mt-1 block w-full rounded border px-2 py-1 text-xs"
          style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
        />
      </label>

      {!birthDatetimeUtc && (
        <p className="text-xs" style={{ color: "var(--text-muted)" }}>
          Enter a birth date to compute.
        </p>
      )}
      {isLoading && <p className="text-xs" style={{ color: "var(--text-muted)" }}>Computing…</p>}
      {error && <p className="text-xs" style={{ color: "#f87171" }}>Could not compute Tarabala.</p>}

      {data && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-4 text-xs" style={{ color: "var(--text-secondary)" }}>
            {data.yearly_name && (
              <span>
                <strong>Yearly Tara:</strong> Age {data.yearly_age} → position {data.yearly_position} ({data.yearly_name})
              </span>
            )}
            {data.best_stars && (
              <span>
                <strong>Best stars (Moon∩Lagna):</strong> {data.best_stars.join(", ") || "none"}
              </span>
            )}
          </div>

          <div>
            <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>
              Special Points (28-scheme)
            </h4>
            <div className="w-full overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b text-[10px] uppercase tracking-wide" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
                    <th className="py-1 pr-3">Nakshatra</th>
                    <th className="py-1 pr-3">From Moon</th>
                    <th className="py-1">From Lagna</th>
                  </tr>
                </thead>
                <tbody>
                  {data.special_points.map((sp) => (
                    <tr key={sp.name} className="border-b" style={{ borderColor: "var(--border-primary)" }}>
                      <td className="py-1 pr-3 capitalize" style={{ color: "var(--text-primary)" }}>{sp.name}</td>
                      <td className="py-1 pr-3" style={{ color: "var(--text-secondary)" }}>{sp.from_moon}</td>
                      <td className="py-1" style={{ color: "var(--text-secondary)" }}>{sp.from_lagna ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-1 text-[10px]" style={{ color: "var(--text-muted)" }}>
              A separate 28-nakshatra (Abhijit-inclusive) named-point scheme, distinct from the 9-cycle
              Tarabala tables below — see packages/shared/tarabala.py for sourcing.
            </p>
          </div>

          {data.total_active_levels > 0 && (
            <div className="text-xs" style={{ color: "var(--text-secondary)" }}>
              <strong>Dasha-hierarchy convergence:</strong> {data.favorable_level_count} / {data.total_active_levels} active levels
              in a favorable lordship Tara
              {data.all_levels_favorable && (
                <span className="ml-2 rounded-full border px-1.5 py-0.5 text-[9px] font-medium uppercase" style={{ color: "#34d399", borderColor: "#34d399" }}>
                  All favorable
                </span>
              )}
              <ul className="mt-1 space-y-0.5">
                {data.lordship_tarabala.map((l) => (
                  <li key={l.dasha_level}>
                    Level {l.dasha_level} ({PLANET_GLYPHS[l.lord] ?? l.lord}) → {l.position_name}{" "}
                    {l.is_favorable ? "✓" : "✗"}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div>
            <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>
              Natal Tarabala
            </h4>
            <div className="w-full overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b text-[10px] uppercase tracking-wide" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
                    <th className="py-1 pr-3">Planet</th>
                    <th className="py-1 pr-3">Natal Nakshatra</th>
                    <th className="py-1 pr-3">Tara</th>
                    <th className="py-1">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.natal_tarabala.map((p) => <TaraRow key={p.planet} p={p} />)}
                </tbody>
              </table>
            </div>
          </div>

          <div>
            <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>
              Transit Tarabala
            </h4>
            <div className="w-full overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b text-[10px] uppercase tracking-wide" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
                    <th className="py-1 pr-3">Planet</th>
                    <th className="py-1 pr-3">Current Nakshatra</th>
                    <th className="py-1 pr-3">Tara</th>
                    <th className="py-1">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.transit_tarabala.map((p) => <TaraRow key={p.planet} p={p} />)}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
