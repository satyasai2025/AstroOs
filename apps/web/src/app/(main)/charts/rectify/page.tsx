"use client";

import { useCallback, useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Badge, Button, Card, Input, Select, type SelectOption } from "@/components/ui";
import { api } from "@/lib/api";
import type { AyanamsaCode } from "@/lib/types";

const AYANAMSA_OPTIONS: SelectOption[] = [
  { value: "lahiri", label: "Lahiri (default)" },
  { value: "kp", label: "Krishnamitra (KP)" },
  { value: "raman", label: "Raman" },
  { value: "yukteshwar", label: "Yukteshwar" },
  { value: "fagan_bradley", label: "Fagan/Bradley" },
  { value: "true_chitra", label: "True Chitra" },
  { value: "true_pushya", label: "True Pushya" },
];

interface Boundary {
  label: string;
  minutes_since_previous: number;
  minutes_until_next: number;
  degrees_since_previous: number;
  degrees_until_next: number;
}
interface Interval {
  rashi: string;
  start_utc: string;
  end_utc: string;
  duration_minutes: number;
  contains_birth: boolean;
}
interface ScanResponse {
  sidereal_longitude: number;
  rashi: string;
  rashi_degree: number;
  nakshatra: string;
  pada: number;
  arcmin_per_minute: number;
  boundaries: Boundary[];
  intervals: Interval[];
}
interface DerivedPoint {
  name: string;
  sidereal_longitude: number;
  rashi: string;
  rashi_degree: number;
  nakshatra: string;
  pada: number;
  house_number: number;
}
interface UpagrahaResponse {
  upagrahas: DerivedPoint[];
  special_lagnas: DerivedPoint[];
  is_daytime_birth: boolean;
  weekday: string;
  starting_lord: string;
  part_duration_minutes: number;
}
interface ShiftResponse {
  shifted_birth_datetime_utc: string;
  shift_minutes: number;
  direction: string;
  resulting_rashi: string;
  resulting_rashi_degree: number;
}
interface PlanetPeriod {
  planet: string;
  rashi: string;
  rashi_degree: number;
  is_retrograde: boolean;
  speed_deg_per_day: number;
  days_since_entry: number | null;
  days_until_exit: number | null;
  previous_rashi: string | null;
  next_rashi: string | null;
}
interface SignChangeResponse {
  planets: PlanetPeriod[];
}
interface VargaChart {
  varga: string;
  divisor: number;
  ascendant: { varga_rashi: string; varga_rashi_degree: number };
}
interface AllVargas {
  charts: Record<string, VargaChart>;
}

const titleCase = (s: string) =>
  s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

/** UTC ISO string → local-time HH:MM:SS as rendered by the browser. */
function timeOf(iso: string): string {
  return new Date(iso).toLocaleTimeString(undefined, { hour12: false });
}

function degOf(d: number): string {
  const deg = Math.floor(d);
  const minFloat = (d - deg) * 60;
  const min = Math.floor(minFloat);
  const sec = Math.round((minFloat - min) * 60);
  return `${deg}° ${String(min).padStart(2, "0")}' ${String(sec).padStart(2, "0")}"`;
}

export default function RectifyPage() {
  const [savedCharts, setSavedCharts] = useState<any[]>([]);
  const [selectedChartId, setSelectedChartId] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [birthTime, setBirthTime] = useState("");
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [ayanamsa, setAyanamsa] = useState<AyanamsaCode>("lahiri");

  const [scan, setScan] = useState<ScanResponse | null>(null);
  const [upa, setUpa] = useState<UpagrahaResponse | null>(null);
  const [shift, setShift] = useState<ShiftResponse | null>(null);
  const [signs, setSigns] = useState<SignChangeResponse | null>(null);
  /** Birth times before each applied shift, oldest first — powers undo. */
  const [history, setHistory] = useState<{ date: string; time: string }[]>([]);
  const [vargas, setVargas] = useState<AllVargas | null>(null);
  /** Varga lagnas as they were before the most recent shift, so the table
   *  can mark which divisionals the birth-time change actually moved. */
  const [prevVargas, setPrevVargas] = useState<Record<string, string> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const populate = (c: any) => {
    const d = new Date(c.birth_datetime_utc);
    setBirthDate(d.toISOString().split("T")[0]);
    setBirthTime(d.toISOString().split("T")[1].slice(0, 5));
    setLatitude(c.birth_latitude?.toString() ?? "");
    setLongitude(c.birth_longitude?.toString() ?? "");
    setAyanamsa((c.ayanamsa as AyanamsaCode) ?? "lahiri");
  };

  useEffect(() => {
    void (async () => {
      try {
        const d = await api.get<{ charts: any[] }>(
          "/api/v1/horoscope/my-charts?limit=50&offset=0",
        );
        setSavedCharts(d.charts ?? []);
        if (d.charts?.length) {
          setSelectedChartId(d.charts[0].id);
          populate(d.charts[0]);
        }
      } catch {
        setSavedCharts([]);
      }
    })();
  }, []);

  const body = useCallback((dateOverride?: string, timeOverride?: string) => {
    const d = dateOverride ?? birthDate;
    const t = timeOverride ?? birthTime;
    const lat = parseFloat(latitude);
    const lng = parseFloat(longitude);
    if (!d || !t || Number.isNaN(lat) || Number.isNaN(lng)) return null;
    // A bare HH:MM would silently drop the seconds that decide a boundary case.
    const hhmmss = t.length === 5 ? `${t}:00` : t;
    return {
      birth_datetime_utc: `${d}T${hhmmss}Z`,
      latitude: lat,
      longitude: lng,
      ayanamsa,
      house_system: "W",
    };
  }, [birthDate, birthTime, latitude, longitude, ayanamsa]);

  const analyse = useCallback(async (dateOverride?: string, timeOverride?: string) => {
    const b = body(dateOverride, timeOverride);
    if (!b) {
      setError("Enter a valid birth date, time, latitude and longitude.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const [s, u, sc, vg] = await Promise.all([
        api.post<ScanResponse>("/api/v1/horoscope/lagna-scan", { ...b, window_hours: 2 }),
        api.post<UpagrahaResponse>("/api/v1/horoscope/upagrahas", b),
        api.post<SignChangeResponse>("/api/v1/horoscope/planet-sign-change", b),
        api.post<AllVargas>("/api/v1/divisional/all", b),
      ]);
      setScan(s);
      setUpa(u);
      setSigns(sc);
      setVargas(vg);
      setShift(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed.");
    } finally {
      setLoading(false);
    }
  }, [body]);

  /** Applies the shift for real: rewrites the birth time and re-analyses,
   *  the way JHora's "Change birthtime to move lagna to" does. Merely
   *  reporting the new time would leave the chart showing the old one. */
  const doShift = useCallback(
    async (direction: "next" | "previous") => {
      const b = body();
      if (!b) return;
      setError(null);
      try {
        const res = await api.post<ShiftResponse>(
          "/api/v1/horoscope/shift-birthtime",
          { ...b, direction },
        );
        setShift(res);

        // Keep full seconds — the boundary is decided inside the minute.
        const iso = res.shifted_birth_datetime_utc;
        const [nextDate, rest] = iso.replace("Z", "").split("T");
        const nextTime = rest.split(".")[0];

        // Snapshot the current varga lagnas first — after re-analysis they
        // are overwritten, and the diff is the point of the exercise.
        if (vargas) {
          setPrevVargas(
            Object.fromEntries(
              Object.entries(vargas.charts).map(([k, v]) => [k, v.ascendant.varga_rashi]),
            ),
          );
        }
        setHistory((h) => [...h, { date: birthDate, time: birthTime }]);
        setBirthDate(nextDate);
        setBirthTime(nextTime);
        await analyse(nextDate, nextTime);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Shift failed.");
      }
    },
    [body, analyse, birthDate, birthTime, vargas],
  );

  const undoLast = useCallback(async () => {
    if (!history.length) return;
    const prev = history[history.length - 1];
    setHistory((h) => h.slice(0, -1));
    setPrevVargas(null);
    setBirthDate(prev.date);
    setBirthTime(prev.time);
    setShift(null);
    await analyse(prev.date, prev.time);
  }, [history, analyse]);

  const undoAll = useCallback(async () => {
    if (!history.length) return;
    const first = history[0];
    setHistory([]);
    setPrevVargas(null);
    setBirthDate(first.date);
    setBirthTime(first.time);
    setShift(null);
    await analyse(first.date, first.time);
  }, [history, analyse]);

  const rashiBoundary = scan?.boundaries.find((b) => b.label === "rashi");
  const isFragile = (rashiBoundary?.minutes_until_next ?? 999) < 5;

  return (
    <AppShell>
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
        <div>
          <h1 style={{ fontSize: "var(--text-2xl)", fontWeight: "var(--weight-bold)", margin: 0 }}>
            Birth-Time Rectification
          </h1>
          <p style={{ color: "var(--text-secondary)", marginTop: "var(--space-1)" }}>
            How sensitive this chart is to the recorded birth time, plus the
            upagrahas and special lagnas derived from the sunrise/sunset frame.
          </p>
        </div>

        {error && (
          <Card glow="gold">
            <p style={{ color: "var(--danger-400)", margin: 0 }}>{error}</p>
          </Card>
        )}

        {/* ── Birth data ─────────────────────────────────────────────── */}
        <Card padding="var(--space-4)">
          <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", marginTop: 0 }}>
            Birth Data
          </h2>
          {savedCharts.length > 0 && (
            <div style={{ marginBottom: "var(--space-4)" }}>
              <Select
                label="Load from Saved Chart"
                value={selectedChartId}
                onChange={(id) => {
                  setSelectedChartId(id);
                  const c = savedCharts.find((x) => x.id === id);
                  if (c) populate(c);
                }}
                options={savedCharts.map((c) => ({
                  value: c.id,
                  label: `${c.subject_name} · ${new Date(c.birth_datetime_utc).toLocaleDateString()}`,
                }))}
              />
            </div>
          )}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))",
              gap: "var(--space-3)",
            }}
          >
            <Input label="Birth Date" type="date" value={birthDate} onChange={setBirthDate} required />
            <Input label="Birth Time (UTC)" type="time" step={1} value={birthTime} onChange={setBirthTime} required
              hint="Seconds matter near a sign boundary" />
            <Input label="Latitude" type="number" value={latitude} onChange={setLatitude} placeholder="e.g. 22.3" />
            <Input label="Longitude" type="number" value={longitude} onChange={setLongitude} placeholder="e.g. 73.2" />
            <div style={{ width: "100%" }}>
              <Select
                label="Ayanamsa"
                options={AYANAMSA_OPTIONS}
                value={ayanamsa}
                onChange={(v) => setAyanamsa(v as AyanamsaCode)}
              />
            </div>
          </div>
          <div style={{ marginTop: "var(--space-4)" }}>
            <Button variant="gold" size="lg" disabled={loading} onClick={() => void analyse()}>
              {loading ? "Analysing…" : "Analyse Chart"}
            </Button>
          </div>
        </Card>

        {/* ── Lagna sensitivity ──────────────────────────────────────── */}
        {scan && (
          <Card padding="var(--space-4)" glow={isFragile ? "gold" : undefined}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "var(--space-2)" }}>
              <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", margin: 0 }}>
                Lagna — {titleCase(scan.rashi)} {degOf(scan.rashi_degree)}
              </h2>
              <Badge tone={isFragile ? "danger" : "success"}>
                {isFragile ? "Near a sign boundary" : "Stable"}
              </Badge>
            </div>
            <p style={{ color: "var(--text-secondary)", fontSize: "var(--text-sm)" }}>
              {titleCase(scan.nakshatra)} pada {scan.pada} · moves{" "}
              <strong>{scan.arcmin_per_minute.toFixed(2)}′ per minute</strong> of
              birth-time error
            </p>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))", gap: "var(--space-3)", marginTop: "var(--space-3)" }}>
              {scan.boundaries.map((b) => (
                <div key={b.label} style={{ padding: "var(--space-3)", borderRadius: "var(--radius-md)", background: "var(--surface-2)" }}>
                  <div style={{ fontSize: "var(--text-xs)", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-tertiary)" }}>
                    {b.label}
                  </div>
                  <div style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)" }}>
                    {b.minutes_until_next < 1
                      ? `${(b.minutes_until_next * 60).toFixed(0)} sec`
                      : `${b.minutes_until_next.toFixed(1)} min`}
                  </div>
                  <div style={{ fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>
                    until change · {b.minutes_since_previous.toFixed(1)} min since last
                  </div>
                </div>
              ))}
            </div>

            <h3 style={{ fontSize: "var(--text-sm)", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-tertiary)", marginTop: "var(--space-4)" }}>
              Lagna timeline (±2 h, local time)
            </h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
              {scan.intervals.map((iv, i) => (
                <div
                  key={i}
                  style={{
                    display: "flex", justifyContent: "space-between", alignItems: "center",
                    padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)",
                    background: iv.contains_birth ? "var(--gold-950, var(--surface-3))" : "var(--surface-2)",
                    border: iv.contains_birth ? "1px solid var(--gold-500, var(--border-subtle))" : "1px solid transparent",
                    fontSize: "var(--text-sm)",
                  }}
                >
                  <span style={{ fontWeight: iv.contains_birth ? "var(--weight-semibold)" : "normal" }}>
                    {titleCase(iv.rashi)}
                  </span>
                  <span style={{ color: "var(--text-muted)", fontFamily: "monospace" }}>
                    {timeOf(iv.start_utc)} – {timeOf(iv.end_utc)} ({iv.duration_minutes.toFixed(0)} min)
                  </span>
                  {iv.contains_birth && <Badge tone="gold">birth</Badge>}
                </div>
              ))}
            </div>

            <div style={{ display: "flex", gap: "var(--space-3)", marginTop: "var(--space-4)", flexWrap: "wrap", alignItems: "center" }}>
              <Button onClick={() => doShift("previous")}>← Move lagna to previous sign</Button>
              <Button onClick={() => doShift("next")}>Move lagna to next sign →</Button>
              {history.length > 0 && (
                <>
                  <Button onClick={undoLast}>Undo last</Button>
                  <Button onClick={undoAll}>Undo all</Button>
                  <span style={{ fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>
                    {history.length} change{history.length > 1 ? "s" : ""} applied
                  </span>
                </>
              )}
            </div>
            {shift && (
              <p style={{ marginTop: "var(--space-3)", fontSize: "var(--text-sm)" }}>
                Birth time moved {shift.shift_minutes > 0 ? "forward" : "back"} by{" "}
                <strong>{Math.abs(shift.shift_minutes).toFixed(2)} min</strong> to{" "}
                <strong style={{ fontFamily: "monospace" }}>
                  {timeOf(shift.shifted_birth_datetime_utc)}
                </strong>{" "}
                — the chart above now reflects it.
              </p>
            )}
          </Card>
        )}

        {/* ── Upagrahas & special lagnas ─────────────────────────────── */}
        {upa && (
          <Card padding="var(--space-4)">
            <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", marginTop: 0 }}>
              Upagrahas &amp; Special Lagnas
            </h2>
            <p style={{ color: "var(--text-secondary)", fontSize: "var(--text-sm)", marginTop: 0 }}>
              {upa.is_daytime_birth ? "Day" : "Night"} birth · Vedic weekday{" "}
              <strong>{titleCase(upa.weekday)}</strong> · first eighth-part ruled by{" "}
              <strong>{titleCase(upa.starting_lord)}</strong> · each part{" "}
              {upa.part_duration_minutes.toFixed(1)} min
            </p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))", gap: "var(--space-3)", marginTop: "var(--space-3)" }}>
              {[...upa.upagrahas, ...upa.special_lagnas].map((p) => (
                <div key={p.name} style={{ padding: "var(--space-3)", borderRadius: "var(--radius-md)", background: "var(--surface-2)" }}>
                  <div style={{ fontWeight: "var(--weight-semibold)" }}>{titleCase(p.name)}</div>
                  <div style={{ fontSize: "var(--text-sm)", color: "var(--text-secondary)" }}>
                    {titleCase(p.rashi)} {degOf(p.rashi_degree)}
                  </div>
                  <div style={{ fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>
                    {titleCase(p.nakshatra)} pada {p.pada} · bhava {p.house_number}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
        {/* ── Divisional lagnas ──────────────────────────────────────── */}
        {vargas && (
          <Card padding="var(--space-4)">
            <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", marginTop: 0 }}>
              Divisional Lagnas
            </h2>
            <p style={{ color: "var(--text-secondary)", fontSize: "var(--text-sm)", marginTop: 0 }}>
              Recomputed with the birth time above. Vargas divide the sign, so
              they shift far faster than D1 — moving the lagna one sign can turn
              over most of these. Changed ones are marked after a shift.
            </p>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))",
                gap: "var(--space-2)",
                marginTop: "var(--space-3)",
              }}
            >
              {Object.entries(vargas.charts)
                .sort((a, b) => a[1].divisor - b[1].divisor)
                .map(([code, v]) => {
                  const before = prevVargas?.[code];
                  const changed = before != null && before !== v.ascendant.varga_rashi;
                  return (
                    <div
                      key={code}
                      style={{
                        padding: "var(--space-2) var(--space-3)",
                        borderRadius: "var(--radius-md)",
                        background: "var(--surface-2)",
                        border: `1px solid ${changed ? "var(--gold-500, var(--border-default))" : "transparent"}`,
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ fontWeight: "var(--weight-semibold)", fontSize: "var(--text-sm)" }}>
                          {code}
                        </span>
                        {changed && <Badge tone="gold">changed</Badge>}
                      </div>
                      <div style={{ fontSize: "var(--text-sm)", color: "var(--text-secondary)" }}>
                        {titleCase(v.ascendant.varga_rashi)}
                      </div>
                      {changed && (
                        <div style={{ fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>
                          was {titleCase(before!)}
                        </div>
                      )}
                    </div>
                  );
                })}
            </div>
          </Card>
        )}

        {/* ── Planet sign changes ────────────────────────────────────── */}
        {signs && (
          <Card padding="var(--space-4)">
            <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", marginTop: 0 }}>
              When Will Each Planet Change Sign?
            </h2>
            <p style={{ color: "var(--text-secondary)", fontSize: "var(--text-sm)", marginTop: 0 }}>
              Scanned, not extrapolated — a retrograde planet can station and
              cross a boundary far later, or in the opposite direction.
            </p>
            <div style={{ overflowX: "auto", marginTop: "var(--space-3)" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "var(--text-sm)" }}>
                <thead>
                  <tr style={{ textAlign: "left", color: "var(--text-tertiary)", fontSize: "var(--text-xs)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                    <th style={{ padding: "var(--space-2)" }}>Graha</th>
                    <th style={{ padding: "var(--space-2)" }}>Position</th>
                    <th style={{ padding: "var(--space-2)" }}>Entered</th>
                    <th style={{ padding: "var(--space-2)" }}>Leaves in</th>
                    <th style={{ padding: "var(--space-2)" }}>Into</th>
                  </tr>
                </thead>
                <tbody>
                  {signs.planets.map((p) => (
                    <tr key={p.planet} style={{ borderTop: "1px solid var(--border-subtle)" }}>
                      <td style={{ padding: "var(--space-2)", fontWeight: "var(--weight-medium)" }}>
                        {titleCase(p.planet)}
                        {p.is_retrograde && (
                          <span style={{ marginLeft: 6 }}>
                            <Badge tone="danger">R</Badge>
                          </span>
                        )}
                      </td>
                      <td style={{ padding: "var(--space-2)" }}>
                        {titleCase(p.rashi)} {degOf(p.rashi_degree)}
                      </td>
                      <td style={{ padding: "var(--space-2)", color: "var(--text-muted)" }}>
                        {p.days_since_entry != null ? `${p.days_since_entry.toFixed(1)} d ago` : "—"}
                      </td>
                      <td style={{ padding: "var(--space-2)", fontWeight: "var(--weight-medium)" }}>
                        {p.days_until_exit != null ? `${p.days_until_exit.toFixed(1)} d` : "—"}
                      </td>
                      <td style={{ padding: "var(--space-2)" }}>
                        {p.next_rashi ? titleCase(p.next_rashi) : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </div>
    </AppShell>
  );
}
