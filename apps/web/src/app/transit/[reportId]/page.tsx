"use client";

import { AppShell } from "@/components/layout/AppShell";
import { Button, Card, Tabs } from "@/components/ui";
import { useWorkflowStore } from "@/lib/store";
import { useLiveTransit } from "@/lib/transitPatterns";
import type { AyanamsaCode, HouseSystemCode, TransitRequest, TransitResponse } from "@/lib/types";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

function toIsoDate(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

const TABS = [
  { key: "overview", label: "Overview" },
  { key: "planets", label: "Planets" },
  { key: "houses", label: "Houses" },
  { key: "aspects", label: "Aspects" },
  { key: "timeline", label: "Timeline" },
];

export default function TransitReportPage() {
  const params = useParams();
  const reportId = params.reportId as string;
  const router = useRouter();
  const result = useWorkflowStore((s) => s.result);
  const request = useWorkflowStore((s) => s.request);
  const transitChart = useWorkflowStore((s) => s.transitChart);

  const [transitDate, setTransitDate] = useState("");
  const [transitTime, setTransitTime] = useState("10:30");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [transitData, setTransitData] = useState<TransitResponse | null>(null);
  const [activeTab, setActiveTab] = useState("overview");

  const transitDatetimeUtc = useMemo(() => {
    if (!transitDate || !transitTime) return undefined;
    return new Date(`${transitDate}T${transitTime}`).toISOString();
  }, [transitDate, transitTime]);

  const transitRequest: TransitRequest | null = useMemo(() => {
    if (!transitDatetimeUtc) return null;
    if (transitChart) {
      return {
        birth_datetime_utc: transitChart.birth_datetime_utc,
        latitude: transitChart.birth_latitude,
        longitude: transitChart.birth_longitude,
        ayanamsa: transitChart.ayanamsa as AyanamsaCode,
        house_system: transitChart.house_system as HouseSystemCode,
        transit_datetime_utc: transitDatetimeUtc,
      };
    }
    if (!request) return null;
    return {
      birth_datetime_utc: request.birth_datetime_utc,
      latitude: request.latitude,
      longitude: request.longitude,
      ayanamsa: request.ayanamsa,
      house_system: request.house_system,
      transit_datetime_utc: transitDatetimeUtc,
    };
  }, [transitDatetimeUtc, transitChart, request]);

  const liveTransit = useLiveTransit(transitRequest);
  const transits = liveTransit.data;

  useEffect(() => {
    if (reportId && reportId !== "current") {
      const decoded = decodeURIComponent(reportId);
      if (decoded.includes("T")) {
        const [date, time] = decoded.split("T");
        setTransitDate(date);
        if (time) setTransitTime(time.substring(0, 5));
        return;
      }
    }
    setTransitDate(toIsoDate(new Date()));
  }, [reportId]);

  useEffect(() => {
    if (transitRequest) {
      setIsAnalyzing(true);
      setTransitData(null);
      liveTransit.refetch();
    }
  }, [transitRequest]);

  useEffect(() => {
    if (transits) {
      setIsAnalyzing(false);
      setTransitData(transits);
    }
  }, [transits]);

  if (!transitChart && !request) {
    return (
      <AppShell>
        <div className="flex flex-col items-center justify-center gap-4 py-20">
          <Card style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "1rem", padding: "2rem", textAlign: "center" }}>
            <h2 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
              No Chart Data Available
            </h2>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              Please create a birth chart first.
            </p>
            <Link href="/dashboard">
              <Button>Create Birth Chart</Button>
            </Link>
          </Card>
        </div>
      </AppShell>
    );
  }

  const subjectName =
    transitChart?.subject_name ||
    request?.subject_name ||
    result?.report?.subject_name ||
    "Unknown";

  const planets = transitData?.planets ?? [];

  return (
    <AppShell>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
            {subjectName}'s Transit Analysis
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            {transitDate && transitTime
              ? new Date(`${transitDate}T${transitTime}`).toLocaleString("en-US", {
                  weekday: "long",
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })
              : "Current Transit"}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={() => router.push("/charts")}>
            ← Back
          </Button>
          <Button variant="ghost" size="sm" onClick={() => window.print()}>
            Print
          </Button>
        </div>
      </div>

      {isAnalyzing && !transitData && (
        <Card style={{ marginBottom: "1.5rem" }}>
          <div className="flex items-center justify-center py-10">
            <div className="text-center">
              <div
                className="mb-3 inline-block h-8 w-8 animate-spin rounded-full border-2 border-t-transparent"
                style={{ borderColor: "var(--accent)", borderTopColor: "transparent" }}
              />
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                Analyzing transits for {transitDate}...
              </p>
            </div>
          </div>
        </Card>
      )}

      {transitData && (
        <>
          <div className="mb-4">
            <Tabs tabs={TABS} active={activeTab} onChange={setActiveTab} />
          </div>

          {activeTab === "overview" && (
            <div className="space-y-6">
              <Card>
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
                      Overall Transit Score
                    </h2>
                    <p className="mt-1 text-xs" style={{ color: "var(--text-secondary)" }}>
                      Based on {planets.length} planetary positions for{" "}
                      {new Date(transitData.transit_datetime_utc).toLocaleDateString("en-US", {
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                      })}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold" style={{ color: "var(--accent)" }}>
                      {Math.min(
                        100,
                        Math.max(
                          0,
                          planets.filter((p) => p.is_favorable_house !== false).length * 12 +
                            planets.filter((p) => !p.is_retrograde).length * 4,
                        ),
                      )}
                      /100
                    </div>
                    <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                      {planets.filter((p) => p.is_favorable_house).length} favorable ·{" "}
                      {planets.filter((p) => p.is_retrograde).length} retrograde
                    </p>
                  </div>
                </div>
              </Card>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "1.5rem" }}>
                <Card>
                  <h3 className="mb-4 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                    Natal Chart
                  </h3>
                  <div className="flex items-center justify-center py-6">
                    <div className="text-center" style={{ color: "var(--text-muted)" }}>
                      <p className="text-xs">Natal chart visualization</p>
                      <p className="mt-1 text-xs">{subjectName}</p>
                    </div>
                  </div>
                </Card>
                <Card>
                  <h3 className="mb-4 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                    Transit Chart
                  </h3>
                  <div className="flex items-center justify-center py-6">
                    <div className="text-center" style={{ color: "var(--text-muted)" }}>
                      <p className="text-xs">Transit chart for {transitDate || "Current"}</p>
                    </div>
                  </div>
                </Card>
              </div>

              <Card>
                <h3 className="mb-4 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                  Transit Highlights
                </h3>
                <div className="space-y-2">
                  {planets.length > 0 ? (
                    <>
                      {planets.filter((p) => p.is_sade_sati).slice(0, 3).map((p) => (
                        <div key={`sade-${p.planet}`} className="flex items-start gap-2 text-xs">
                          <span style={{ color: "var(--gold-400)" }}>⚠</span>
                          <span style={{ color: "var(--text-secondary)" }}>
                            {p.planet} in Sade Sati (house {p.house_from_natal_moon} from Moon)
                          </span>
                        </div>
                      ))}
                      {planets.filter((p) => p.is_ashtama_shani).slice(0, 3).map((p) => (
                        <div key={`ashtama-${p.planet}`} className="flex items-start gap-2 text-xs">
                          <span style={{ color: "var(--gold-400)" }}>⚠</span>
                          <span style={{ color: "var(--text-secondary)" }}>
                            {p.planet} in Ashtama Shani (house {p.house_from_natal_moon} from Moon)
                          </span>
                        </div>
                      ))}
                      {planets.filter((p) => p.is_favorable_house).slice(0, 3).map((p) => (
                        <div key={`fav-${p.planet}`} className="flex items-start gap-2 text-xs">
                          <span style={{ color: "var(--success-400)" }}>✓</span>
                          <span style={{ color: "var(--text-secondary)" }}>
                            {p.planet} in favorable house {p.house_from_natal_moon} (from Moon)
                          </span>
                        </div>
                      ))}
                    </>
                  ) : (
                    <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                      No transit highlights for this period.
                    </p>
                  )}
                </div>
              </Card>
            </div>
          )}

          {activeTab === "planets" && (
            <Card>
              <h3 className="mb-4 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                Transit Planet Positions
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr style={{ borderBottom: "1px solid var(--border-primary)" }}>
                      <th className="px-3 py-2 text-left font-medium" style={{ color: "var(--text-muted)" }}>Planet</th>
                      <th className="px-3 py-2 text-left font-medium" style={{ color: "var(--text-muted)" }}>Sign</th>
                      <th className="px-3 py-2 text-left font-medium" style={{ color: "var(--text-muted)" }}>Deg</th>
                      <th className="px-3 py-2 text-left font-medium" style={{ color: "var(--text-muted)" }}>Nakshatra</th>
                      <th className="px-3 py-2 text-left font-medium" style={{ color: "var(--text-muted)" }}>Pada</th>
                      <th className="px-3 py-2 text-left font-medium" style={{ color: "var(--text-muted)" }}>House (Moon)</th>
                      <th className="px-3 py-2 text-left font-medium" style={{ color: "var(--text-muted)" }}>Motion</th>
                      <th className="px-3 py-2 text-left font-medium" style={{ color: "var(--text-muted)" }}>Gati</th>
                      <th className="px-3 py-2 text-left font-medium" style={{ color: "var(--text-muted)" }}>Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {planets.map((p) => (
                      <tr key={p.planet} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                        <td className="px-3 py-2 font-medium" style={{ color: "var(--text-primary)" }}>{p.planet}</td>
                        <td className="px-3 py-2" style={{ color: "var(--text-secondary)" }}>{p.transit_rashi}</td>
                        <td className="px-3 py-2" style={{ color: "var(--text-secondary)" }}>{p.transit_rashi_degree.toFixed(2)}°</td>
                        <td className="px-3 py-2" style={{ color: "var(--text-secondary)" }}>{p.transit_nakshatra}</td>
                        <td className="px-3 py-2" style={{ color: "var(--text-secondary)" }}>{p.transit_pada}</td>
                        <td className="px-3 py-2" style={{ color: "var(--text-secondary)" }}>{p.house_from_natal_moon}</td>
                        <td className="px-3 py-2" style={{ color: p.is_retrograde ? "var(--gold-400)" : "var(--success-400)" }}>
                          {p.is_retrograde ? "Retrograde" : "Direct"}
                        </td>
                        <td className="px-3 py-2" style={{ color: "var(--text-muted)" }}>{p.gati}</td>
                        <td className="px-3 py-2" style={{ color: "var(--text-muted)" }}>
                          {p.is_sade_sati && "Sade Sati "}
                          {p.is_ashtama_shani && "Ashtama Shani "}
                          {p.has_vedha && "Vedha "}
                          {p.is_favorable_house === true && "Favorable "}
                          {p.is_favorable_house === false && "Challenging"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {activeTab === "houses" && (
            <Card>
              <h3 className="mb-4 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                Transit Houses from Natal Moon
              </h3>
              <p className="mb-4 text-xs" style={{ color: "var(--text-muted)" }}>
                Natal Moon is in {transitData.natal_moon_rashi}. Each transit planet is placed in a house counted from the natal Moon.
              </p>
              <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4">
                {planets.map((p) => (
                  <div
                    key={p.planet}
                    className="rounded-lg border p-3"
                    style={{
                      borderColor: p.is_favorable_house === false ? "var(--gold-400)" : "var(--border-primary)",
                      backgroundColor: p.is_favorable_house ? "rgba(16,185,129,0.05)" : "var(--obsidian-surface)",
                    }}
                  >
                    <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{p.planet}</p>
                    <p className="mt-1 text-xs" style={{ color: "var(--text-secondary)" }}>
                      House {p.house_from_natal_moon} from Moon
                    </p>
                    <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
                      {p.transit_rashi} · {p.transit_rashi_degree.toFixed(1)}°
                    </p>
                    {p.is_favorable_house !== null && (
                      <p className="mt-1 text-xs" style={{ color: p.is_favorable_house ? "var(--success-400)" : "var(--gold-400)" }}>
                        {p.is_favorable_house ? "Favorable" : "Challenging"}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {activeTab === "aspects" && (
            <Card>
              <h3 className="mb-4 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                Transit Aspects & Vedha
              </h3>
              <div className="space-y-2">
                {planets.filter((p) => p.has_vedha || p.has_nakshatra_vedha).length > 0 ? (
                  planets.filter((p) => p.has_vedha || p.has_nakshatra_vedha).map((p) => (
                    <div key={p.planet} className="flex items-start gap-2 text-xs">
                      <span style={{ color: "var(--gold-400)" }}>⚠</span>
                      <span style={{ color: "var(--text-secondary)" }}>
                        {p.planet} — {p.has_vedha ? `Vedha from ${p.vedha_planet || "—"}` : ""}
                        {p.has_nakshatra_vedha ? ` · Nakshatra Vedha (${p.nakshatra_vedha_type || ""} → ${p.nakshatra_vedha_target || ""})` : ""}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                    No vedha aspects detected for this transit period.
                  </p>
                )}
              </div>
            </Card>
          )}

          {activeTab === "timeline" && (
            <Card>
              <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                Dynamic Date Selection
              </h3>
              <p className="mb-3 text-xs" style={{ color: "var(--text-muted)" }}>
                The same birth chart can generate multiple transit reports
              </p>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                    Date
                  </label>
                  <input
                    type="date"
                    value={transitDate}
                    onChange={(e) => setTransitDate(e.target.value)}
                    className="obsidian-input w-full [color-scheme:dark]"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                    Time
                  </label>
                  <input
                    type="time"
                    value={transitTime}
                    onChange={(e) => setTransitTime(e.target.value)}
                    className="obsidian-input w-full [color-scheme:dark]"
                  />
                </div>
              </div>
              <div className="mt-4 flex gap-2">
                <Button variant="secondary" size="sm" onClick={() => setTransitDate(toIsoDate(new Date()))}>
                  Today
                </Button>
                <Button variant="secondary" size="sm" onClick={() => {
                  const d = new Date();
                  d.setDate(d.getDate() + 1);
                  setTransitDate(toIsoDate(d));
                }}>
                  Tomorrow
                </Button>
                <Button variant="secondary" size="sm" onClick={() => {
                  const d = new Date();
                  d.setDate(d.getDate() + 7);
                  setTransitDate(toIsoDate(d));
                }}>
                  Next Week
                </Button>
              </div>
            </Card>
          )}
        </>
      )}

      {!transitData && !isAnalyzing && (
        <Card>
          <div className="flex flex-col items-center justify-center gap-3 py-10 text-center">
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              Select a date and click Analyze to load transit data.
            </p>
            <div className="grid grid-cols-2 gap-4" style={{ maxWidth: "400px", width: "100%" }}>
              <div>
                <label className="mb-1 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>Date</label>
                <input type="date" value={transitDate} onChange={(e) => setTransitDate(e.target.value)} className="obsidian-input w-full [color-scheme:dark]" />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>Time</label>
                <input type="time" value={transitTime} onChange={(e) => setTransitTime(e.target.value)} className="obsidian-input w-full [color-scheme:dark]" />
              </div>
            </div>
          </div>
        </Card>
      )}
    </AppShell>
  );
}
