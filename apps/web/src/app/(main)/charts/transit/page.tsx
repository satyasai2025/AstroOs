"use client";

import { TransitAlerts } from "@/components/charts/transit/TransitAlerts";
import { TransitWheel } from "@/components/charts/transit/TransitWheel";
import { VedhaAnalysisPanel } from "@/components/charts/VedhaAnalysisPanel";
import { AnimatedTransitIntegration } from "@/app/(main)/charts/AnimatedTransitIntegration";
import { SplitWorkspaceLayout } from "@/components/layout/SplitWorkspaceLayout";
import { AppShell } from "@/components/layout/AppShell";
import { Badge, Button, Card, DonutChart, KpiCard, Table, Tabs, Timeline, type TableColumn, type TimelineEvent, ShareButton } from "@/components/ui";
import { PLANET_SYMBOLS, nakshatraFromLongitude } from "@/lib/astro";
import { formatPosition } from "@/lib/formatAstro";
import { getCurrentDashaChain } from "@/lib/kpiScoring";
import { useWorkflowStore } from "@/lib/store";
import { useAnalyzeWorkflow } from "@/lib/workflow";
import { useMyCharts } from "@/lib/charts";
import { useLiveTransit, useTransitPatterns } from "@/lib/transitPatterns";
import type { BirthChartSummary, TransitPatternsRequest, TransitPlanetResponse, TransitRequest, WorkflowAnalysisRequest } from "@/lib/types";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";

export const dynamic = "force-dynamic";

/**
 * /charts/transit — Transit Analysis console, rebuilt to match the
 * "AstroOS Transit Analysis v2" reference design pixel-for-pixel in
 * structure (controls row, 6 KPI cards, chart/positions/impact row,
 * house-activation/returns/alerts row, Vedha analysis, aspects-table/
 * settings row).
 *
 * Every value traces to a real backend field EXCEPT where explicitly
 * marked "heuristic" (documented inline, same convention as
 * lib/kpiScoring.ts) or "not computed" (Eclipses — this backend has no
 * eclipse calculation; shown honestly rather than invented). Gati (the
 * classical 8-fold planetary speed classification) is real, computed
 * from actual ephemeris speed data — see the backend's
 * services/gati_classifier.py for its classification rules and caveats.
 */

const GATI_LABELS: Record<string, string> = {
  vakra: "Vakra",
  vikala: "Vikala",
  mandatara: "Mandatara",
  manda: "Manda",
  sama: "Sama",
  chara: "Chara",
  atichara: "Atichara",
};

const GATI_TONE: Record<string, "danger" | "gold" | "neutral" | "success"> = {
  vakra: "danger",
  vikala: "gold",
  mandatara: "gold",
  manda: "gold",
  sama: "neutral",
  chara: "success",
  atichara: "success",
};

function formatDegree(deg: number): string {
  const whole = Math.floor(deg);
  const minutes = Math.round((deg - whole) * 60);
  return `${whole}° ${minutes}'`;
}

/** Real aspect_type values are 'opposition' | 'trine' | 'square' |
 * 'special_graha' (see TransitAspectResponse) — the last one reads oddly
 * inline ("Jupiter special_graha to natal Rahu"), so it gets a human label.
 * Used as `{transiting} {label} to natal {natal}` — must NOT include "to". */
function aspectTypeLabel(aspectType: string): string {
  return aspectType === "special_graha" ? "special aspect" : aspectType;
}

function TransitAnalysisPageContent() {
  const searchParams = useSearchParams();
  const result = useWorkflowStore((s) => s.result);
  const request = useWorkflowStore((s) => s.request);
  const transitChart = useWorkflowStore((s) => s.transitChart);
  const setResult = useWorkflowStore((s) => s.setResult);
  const analyze = useAnalyzeWorkflow();
  const myCharts = useMyCharts();
  const [autoLoadStarted, setAutoLoadStarted] = useState(false);
  const [activeTab, setActiveTab] = useState<"overview" | "sky_motion">("overview");

  const [houseReference, setHouseReference] = useState<"moon" | "ascendant">("moon");
  const [transitDateTime, setTransitDateTime] = useState(() => {
    const date = searchParams.get("date");
    const time = searchParams.get("time");
    return date && time ? `${date}T${time}` : "";
  });

  const queryChartId = searchParams.get("chart_id");

  // Auto-resolve chart to load: queryParam -> store transitChart -> store request -> localStorage last viewed -> default chart -> first saved chart
  const chartToLoad = useMemo(() => {
    const charts = myCharts.data?.charts ?? [];
    if (queryChartId) {
      const found = charts.find((c) => c.id === queryChartId);
      if (found) return found;
    }
    if (transitChart) return transitChart;
    if (request?.chart_id) {
      const found = charts.find((c) => c.id === request.chart_id);
      if (found) return found;
    }
    if (typeof window !== "undefined") {
      try {
        const lastViewedId = localStorage.getItem("astroos_last_viewed_chart_id");
        if (lastViewedId) {
          const found = charts.find((c) => c.id === lastViewedId);
          if (found) return found;
        }
      } catch {
        // ignore
      }
    }
    const defaultChart = charts.find((c) => c.is_default) || charts[0];
    return defaultChart || null;
  }, [queryChartId, myCharts.data?.charts, transitChart, request?.chart_id]);

  const hasMatchingResult = Boolean(
    result &&
    request &&
    (chartToLoad ? (result.chart_id === chartToLoad.id || request.subject_name === chartToLoad.subject_name) : true)
  );

  const loadChart = (target: BirthChartSummary) => {
    setAutoLoadStarted(true);
    const analyzeRequest: WorkflowAnalysisRequest = {
      birth_datetime_utc: target.birth_datetime_utc,
      latitude: target.birth_latitude,
      longitude: target.birth_longitude,
      ayanamsa: target.ayanamsa as WorkflowAnalysisRequest["ayanamsa"],
      house_system: target.house_system as WorkflowAnalysisRequest["house_system"],
      dasha_system: "vimshottari",
      include_vargas: true,
      subject_name: target.subject_name,
      place_name: target.place_name,
      persist: false,
      chart_id: target.id,
    };
    analyze.mutate(analyzeRequest, {
      onSuccess: (data) => {
        setResult(data, analyzeRequest);
        try {
          localStorage.setItem("astroos_last_viewed_chart_id", target.id);
        } catch {
          // ignore
        }
      },
    });
  };

  useEffect(() => {
    if (!chartToLoad || hasMatchingResult || autoLoadStarted) return;
    loadChart(chartToLoad);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chartToLoad, hasMatchingResult, autoLoadStarted]);

  const transitDatetimeUtc = transitDateTime ? new Date(transitDateTime).toISOString() : undefined;

  const transitRequest: TransitRequest | null = request
    ? {
        birth_datetime_utc: request.birth_datetime_utc,
        latitude: request.latitude,
        longitude: request.longitude,
        ayanamsa: request.ayanamsa,
        house_system: request.house_system,
        transit_datetime_utc: transitDatetimeUtc,
      }
    : null;
  const patternsRequest: TransitPatternsRequest | null = transitRequest;

  const liveTransit = useLiveTransit(transitRequest);
  const patternsQuery = useTransitPatterns(patternsRequest);
  const isRecalculating = liveTransit.isFetching || patternsQuery.isFetching;

  function handleRecalculate() {
    liveTransit.refetch();
    patternsQuery.refetch();
  }

  function stepDay(delta: number) {
    const base = transitDateTime ? new Date(transitDateTime) : new Date();
    base.setDate(base.getDate() + delta);
    // toISOString slice trims to the "YYYY-MM-DDTHH:mm" shape datetime-local expects
    setTransitDateTime(base.toISOString().slice(0, 16));
  }

  const activeTransits = liveTransit.data ?? result?.transits;

  const kpis = useMemo(() => {
    const planets = activeTransits?.planets ?? [];
    const benefic = planets.filter((p) => p.is_favorable_house === true);
    const challenging = planets.filter((p) => p.is_favorable_house === false);
    const retrograde = planets.filter((p) => p.is_retrograde);
    const active = planets.filter(
      (p) =>
        p.is_favorable_house === true ||
        p.is_favorable_house === false ||
        p.has_vedha ||
        p.has_vipreet_vedha ||
        p.has_nakshatra_vedha ||
        p.is_sade_sati ||
        p.is_ashtama_shani,
    );
    const rated = benefic.length + challenging.length;
    // Heuristic: favorable-house ratio, penalized for active Sade Sati /
    // Ashtama Shani — same documented-default-weight convention as
    // lib/kpiScoring.ts, not a classical or computed authority score.
    let score: number | null = rated > 0 ? Math.round((benefic.length / rated) * 100) : null;
    if (score !== null) {
      if (patternsQuery.data?.sade_sati.is_active) score -= 15;
      if (patternsQuery.data?.ashtama_shani.is_active) score -= 10;
      score = Math.max(0, Math.min(100, score));
    }
    return { benefic, challenging, retrograde, active, score };
  }, [activeTransits, patternsQuery.data]);

  // Real per-house (from natal Moon) activation, bucketed by the mix of
  // favorable/challenging planets transiting each house — a documented
  // heuristic (not a classical named metric), same spirit as the KPI
  // score above.
  const houseActivation = useMemo(() => {
    const planets = activeTransits?.planets ?? [];
    const buckets: Record<string, number[]> = {
      "Highly Activated": [],
      Activated: [],
      Moderate: [],
      Low: [],
      Challenged: [],
      "Heavily Challenged": [],
    };
    for (let house = 1; house <= 12; house++) {
      const inHouse = planets.filter((p) => p.house_from_natal_moon === house);
      const favorable = inHouse.filter((p) => p.is_favorable_house === true).length;
      const unfavorable = inHouse.filter((p) => p.is_favorable_house === false).length;
      let bucket: string;
      if (inHouse.length === 0) bucket = "Low";
      else if (favorable > 0 && unfavorable === 0) bucket = favorable >= 2 ? "Highly Activated" : "Activated";
      else if (unfavorable > 0 && favorable === 0) bucket = unfavorable >= 2 ? "Heavily Challenged" : "Challenged";
      else bucket = "Moderate";
      buckets[bucket].push(house);
    }
    return buckets;
  }, [activeTransits]);

  // Real "top influencing transits" from the aspects the backend actually
  // detected (TransitPatternsResponse.aspects — real Vedic graha drishti,
  // see aspect_engine.py), not fabricated headlines. The +/-% is a
  // heuristic (harmonious aspects benefic, tense challenging, scaled by
  // how tight the orb is — tighter orb = classically stronger), not a
  // computed classical strength value.
  //
  // Nature classification for the 4 real aspect_type values: trine (5th/
  // 9th) is the classical harmonious aspect; opposition (7th) and square
  // (4th/10th) are classically tense. "special_graha" covers Mars's 4th/8th
  // and Saturn's 3rd/10th (both classically malefic special aspects) as
  // well as Jupiter's 5th/9th (classically benefic) — since the backend
  // doesn't distinguish which planet cast a special_graha aspect in this
  // label alone, it's treated as neutral here rather than guessing.
  const topAspects = useMemo(() => {
    const aspects = patternsQuery.data?.aspects ?? [];
    const HARMONIOUS = new Set(["trine"]);
    const TENSE = new Set(["square", "opposition"]);
    const MAX_ORB = 8;
    return [...aspects]
      .map((a) => {
        const nature = HARMONIOUS.has(a.aspect_type) ? 1 : TENSE.has(a.aspect_type) ? -1 : 0;
        const tightness = Math.max(0, 1 - a.orb / MAX_ORB);
        const pct = Math.round(nature * tightness * 30);
        return { ...a, pct };
      })
      .sort((a, b) => Math.abs(b.pct) - Math.abs(a.pct))
      .slice(0, 5);
  }, [patternsQuery.data]);

  // Impact Summary donut — 5 buckets derived from real favorability +
  // aspect-nature data. Heuristic bucketing (documented), not a
  // classical 5-way scale.
  const impactSummary = useMemo(() => {
    const planets = activeTransits?.planets ?? [];
    let veryBenefic = 0, benefic = 0, neutral = 0, challenging = 0, veryChallenging = 0;
    for (const p of planets) {
      if (p.is_favorable_house === true) {
        if (p.has_vipreet_vedha) veryBenefic++;
        else benefic++;
      } else if (p.is_favorable_house === false) {
        if (p.has_vedha || p.has_nakshatra_vedha) veryChallenging++;
        else challenging++;
      } else {
        neutral++;
      }
    }
    return { veryBenefic, benefic, neutral, challenging, veryChallenging };
  }, [activeTransits]);

  const returnEvents: TimelineEvent[] | undefined = useMemo(() => {
    if (!patternsQuery.data) return undefined;
    return [...patternsQuery.data.return_periods]
      .sort((a, b) => a.orb - b.orb)
      .slice(0, 6)
      .map((r) => ({
        title: r.planet,
        date: r.is_at_return ? "At return" : r.estimated_return_date ? `~${r.estimated_return_date}` : "—",
        description: `Orb ${r.orb.toFixed(2)}°`,
        tone: r.is_at_return ? ("success" as const) : ("cyan" as const),
      }));
  }, [patternsQuery.data]);

  const columns: TableColumn<TransitPlanetResponse>[] = [
    {
      key: "planet",
      label: "Planet",
      render: (p) => (
        <span className="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
          <span className="text-amber-500 dark:text-amber-400 font-bold">{PLANET_SYMBOLS[p.planet] ?? ""}</span> {p.planet}
        </span>
      ),
    },
    {
      key: "transit_rashi",
      label: "Sign",
      render: (p) => <span className="capitalize font-medium text-slate-800 dark:text-slate-200">{p.transit_rashi}</span>,
    },
    {
      key: "transit_rashi_degree",
      label: "Degree",
      mono: true,
      render: (p) => <span className="font-mono text-slate-700 dark:text-slate-300 font-medium">{formatPosition(p.transit_rashi, p.transit_rashi_degree)}</span>,
    },
    {
      key: "transit_nakshatra",
      label: "Nakshatra",
      render: (p) => <span className="text-slate-700 dark:text-slate-300">{p.transit_nakshatra}</span>,
    },
    {
      key: "transit_pada",
      label: "Pada",
      align: "right",
      mono: true,
      render: (p) => <span className="font-mono text-slate-600 dark:text-slate-400 font-medium">{p.transit_pada}</span>,
    },
    {
      key: "is_retrograde",
      label: "Status",
      render: (p) => <Badge tone={p.is_retrograde ? "danger" : "success"}>{p.is_retrograde ? "Retrograde" : "Direct"}</Badge>,
    },
    {
      key: "gati",
      label: "Gati",
      render: (p) => <Badge tone={GATI_TONE[p.gati] ?? "neutral"}>{GATI_LABELS[p.gati] ?? p.gati}</Badge>,
    },
    {
      key: "vedha",
      label: "Vedha",
      render: (p) => {
        const hasVedha = p.has_vedha || p.has_vipreet_vedha || p.has_nakshatra_vedha;
        return <Badge tone={hasVedha ? "danger" : "neutral"}>{hasVedha ? "Yes" : "No"}</Badge>;
      },
    },
  ];

  const [selectedFallbackChartId, setSelectedFallbackChartId] = useState<string>("");

  if (!result) {
    if (analyze.isPending) {
      return (
        <div className="flex flex-col items-center justify-center gap-3 py-20" role="status">
          <span
            className="inline-block h-8 w-8 animate-spin rounded-full border-2 border-t-transparent"
            style={{ borderColor: "var(--accent)", borderTopColor: "transparent" }}
          />
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            Loading chart &amp; calculating planetary transits…
          </p>
        </div>
      );
    }

    const availableCharts = myCharts.data?.charts ?? [];

    return (
      <div className="flex flex-col items-center justify-center gap-4 py-16 px-4" role="status">
        <Card style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "1.25rem", padding: "2.5rem", textAlign: "center", maxWidth: "520px", width: "100%" }}>
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-500">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <circle cx="12" cy="12" r="9" />
              <path d="m15 9-2 6-6 2 2-6 6-2Z" />
            </svg>
          </div>
          <div>
            <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
              Select Chart for Transit Analysis
            </h2>
            <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
              Choose a saved profile to compute Gochara, Ashtama Shani, and real-time planetary aspects.
            </p>
          </div>

          {availableCharts.length > 0 ? (
            <div className="w-full space-y-3 pt-2">
              <select
                value={selectedFallbackChartId || (chartToLoad?.id ?? availableCharts[0]?.id ?? "")}
                onChange={(e) => setSelectedFallbackChartId(e.target.value)}
                className="w-full rounded-lg border px-3 py-2 text-sm shadow-sm transition"
                style={{
                  backgroundColor: "var(--bg-card)",
                  borderColor: "var(--border-primary)",
                  color: "var(--text-primary)",
                }}
              >
                {availableCharts.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.subject_name} ({new Date(c.birth_datetime_utc).toLocaleDateString()}{c.place_name ? ` · ${c.place_name}` : ""})
                  </option>
                ))}
              </select>

              <div className="flex gap-2 justify-center pt-2">
                <button
                  type="button"
                  onClick={() => {
                    const targetId = selectedFallbackChartId || chartToLoad?.id || availableCharts[0]?.id;
                    const target = availableCharts.find((c) => c.id === targetId);
                    if (target) loadChart(target);
                  }}
                  className="obsidian-btn-primary text-sm px-4 py-2"
                >
                  Load Chart &amp; Calculate Transits →
                </button>
                <Button href="/dashboard" variant="ghost" size="sm">
                  + Create New
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-3 pt-2">
              <p className="text-xs text-slate-400">No saved charts found. Create a birth chart to begin transit exploration.</p>
              <Button href="/dashboard">Create First Chart</Button>
            </div>
          )}
        </Card>
      </div>
    );
  }

  const { dasha } = result;
  const transits = activeTransits!;
  const dashaChain = getCurrentDashaChain(dasha.mahadashas);

  const dateLabel = transitDateTime
    ? new Date(transitDateTime).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })
    : "Now";

  const handleExport = () => {
    alert("Export functionality would generate a PDF or image of the transit chart");
  };

  const handlePrint = () => {
    window.print();
  };

  const handleShare = async () => {
    const url = window.location.href;
    if (navigator.share) {
      try {
        await navigator.share({
          title: `Transit Chart - ${request?.subject_name || "Chart"}`,
          text: `Transit analysis for ${request?.subject_name || "chart"}`,
          url: url,
        });
      } catch (err) {
        // User cancelled or share failed
      }
      return;
    }
    try {
      await navigator.clipboard.writeText(url);
      alert("Link copied to clipboard!");
    } catch (err) {
      alert(`Could not copy automatically. Copy this link:\n${url}`);
    }
  };

  return (
    <SplitWorkspaceLayout>
      <div className="mb-3 flex w-full max-w-full flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">
            Transit Analysis
          </h1>
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Real-time planetary movements &amp; natal impacts.
            {request && (
              <>
                {" "}
                Subject: <span className="font-semibold text-slate-800 dark:text-slate-200">{request.subject_name}</span>
              </>
            )}
          </p>
        </div>
        <div className="flex items-center gap-1.5 flex-wrap">
          {myCharts.data?.charts && myCharts.data.charts.length > 1 && (
            <select
              value={request?.chart_id || ""}
              onChange={(e) => {
                const target = myCharts.data?.charts.find((c) => c.id === e.target.value);
                if (target) loadChart(target);
              }}
              className="rounded-lg border px-2 py-1 text-xs shadow-sm font-medium"
              style={{
                backgroundColor: "var(--bg-card)",
                borderColor: "var(--border-primary)",
                color: "var(--text-primary)",
              }}
              aria-label="Switch Subject Chart"
            >
              {myCharts.data.charts.map((c) => (
                <option key={c.id} value={c.id}>
                  👤 {c.subject_name}
                </option>
              ))}
            </select>
          )}
          <Button href="/charts" variant="ghost" size="sm" aria-label="Back to charts">
            ← Back
          </Button>
          <Button variant="ghost" size="sm" onClick={handleExport} aria-label="Export chart">
            Export
          </Button>
          <Button variant="ghost" size="sm" onClick={handlePrint} aria-label="Print chart">
            Print
          </Button>
          <ShareButton />
        </div>
      </div>

      <div className="mb-3">
        <Tabs
          tabs={[
            { key: "overview", label: "Overview" },
            { key: "sky_motion", label: "Sky Motion" },
          ]}
          active={activeTab}
          onChange={(key) => setActiveTab(key as "overview" | "sky_motion")}
        />
      </div>

      {activeTab === "sky_motion" && (
        <AnimatedTransitIntegration chart={result.chart} request={request} />
      )}

      {activeTab === "overview" && (
        <>
      {/* Controls row: transit date stepper + Moon/Ascendant reference point */}
      <div className="mb-3 flex flex-wrap items-center gap-3">
        <div>
          <div
            className="flex items-center gap-1.5 rounded-lg px-2 py-1 bg-slate-100 dark:bg-slate-800/90 border border-slate-200 dark:border-slate-700 shadow-sm"
          >
            <button type="button" onClick={() => stepDay(-1)} className="px-1 text-sm font-bold text-cyan-600 dark:text-cyan-400 hover:opacity-80 transition" aria-label="Previous day">
              ‹
            </button>
            <span className="min-w-[100px] text-center font-mono text-xs text-slate-900 dark:text-slate-100 font-semibold">
              {dateLabel}
            </span>
            <button type="button" onClick={() => stepDay(1)} className="px-1 text-sm font-bold text-cyan-600 dark:text-cyan-400 hover:opacity-80 transition" aria-label="Next day">
              ›
            </button>
            <Button variant="secondary" size="sm" onClick={() => setTransitDateTime("")}>
              Today
            </Button>
          </div>
        </div>

        <div>
          <div className="flex gap-0.5 rounded-lg p-0.5 bg-slate-100 dark:bg-slate-800/90 border border-slate-200 dark:border-slate-700 shadow-sm">
            {(["moon", "ascendant"] as const).map((ref) => (
              <button
                key={ref}
                type="button"
                onClick={() => setHouseReference(ref)}
                className={`rounded-md px-2.5 py-1 text-xs font-semibold transition ${
                  houseReference === ref
                    ? "bg-cyan-500 text-white shadow-sm"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
                aria-pressed={houseReference === ref}
              >
                From {ref === "moon" ? "Moon" : "Ascendant"}
              </button>
            ))}
          </div>
        </div>

        <Button variant="secondary" size="sm" onClick={handleRecalculate} disabled={isRecalculating}>
          {isRecalculating ? "Loading…" : "Recalculate"}
        </Button>
      </div>

      {/* KPI row */}
      <div className="mb-3 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
        <KpiCard label="Active Transits" value={String(kpis.active.length)} accent="cyan" caveat="Planets with notable flag." />
        <KpiCard label="Benefic" value={String(kpis.benefic.length)} accent="cyan" caveat="Positive influence" />
        <KpiCard label="Challenging" value={String(kpis.challenging.length)} accent="gold" caveat="Need attention" />
        <KpiCard
          label="Retrograde"
          value={String(kpis.retrograde.length)}
          accent="violet"
          caveat={kpis.retrograde.length > 0 ? kpis.retrograde.map((p) => p.planet).join(", ") : "None"}
        />
        <KpiCard label="Eclipses" value="—" accent="cyan" caveat="Not computed" />
        <KpiCard
          label="Transit Score"
          value={kpis.score === null ? "—" : `${kpis.score}%`}
          accent="gold"
          caveat="Favorable-house ratio"
        />
      </div>

      {/* Chart / Positions / Impact Summary */}
      <div className="mb-3 grid grid-cols-1 gap-3 xl:grid-cols-[minmax(280px,1fr)_1.2fr_1fr]">
        <Card>
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
              Transit Chart (D1)
            </span>
          </div>
          <TransitWheel transits={transits} houseReference={houseReference} natalAscendant={result.chart.ascendant} />
        </Card>

        <Card padding="0">
          <div className="px-3 py-2 border-b border-slate-200 dark:border-slate-800">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
              Transit Positions
            </span>
          </div>
          <div className="p-2 max-h-[380px] overflow-y-auto">
            <Table<TransitPlanetResponse> columns={columns} rows={transits.planets} />
          </div>
        </Card>

        <Card>
          <div className="mb-3 text-[10px] font-bold uppercase tracking-widest text-slate-600 dark:text-slate-400">
            Transit Impact Summary
          </div>
          <div className="mb-3.5 flex items-center gap-4 p-2">
            <DonutChart
              segments={[
                { value: impactSummary.veryBenefic || 0.0001, color: "var(--success-400)" },
                { value: impactSummary.benefic || 0.0001, color: "var(--cyan-400)" },
                { value: impactSummary.neutral || 0.0001, color: "var(--text-tertiary)" },
                { value: impactSummary.challenging || 0.0001, color: "var(--gold-400)" },
                { value: impactSummary.veryChallenging || 0.0001, color: "var(--danger-400)" },
              ]}
              size={110}
            />
            <div className="flex flex-col gap-1.5 text-xs text-slate-700 dark:text-slate-300">
              <span>● Very Benefic ({impactSummary.veryBenefic})</span>
              <span>● Benefic ({impactSummary.benefic})</span>
              <span>● Neutral ({impactSummary.neutral})</span>
              <span>● Challenging ({impactSummary.challenging})</span>
              <span>● Very Challenging ({impactSummary.veryChallenging})</span>
            </div>
          </div>

          <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-slate-600 dark:text-slate-400">
            Top Influencing Transits
          </div>
          {topAspects.length === 0 ? (
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {patternsQuery.isLoading ? "Loading…" : "No notable transit-to-natal aspects detected right now."}
            </p>
          ) : (
            topAspects.map((a, i) => (
              <div key={i} className="flex justify-between py-1.5 text-xs">
                <span className="text-slate-700 dark:text-slate-300">
                  {a.transiting_planet} {aspectTypeLabel(a.aspect_type)} to natal {a.natal_planet}
                </span>
                <span style={{ color: a.pct >= 0 ? "var(--success-400)" : "var(--danger-400)", fontWeight: 600 }}>
                  {a.pct >= 0 ? "+" : ""}
                  {a.pct}%
                </span>
              </div>
            ))
          )}
        </Card>
      </div>

      {/* House Activation / Planetary Returns / Alerts */}
      <div className="mb-3 grid grid-cols-1 gap-3 xl:grid-cols-[1fr_1.2fr_0.9fr]">
        <Card>
          <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-slate-600 dark:text-slate-400">
            House Activation (from {houseReference === "moon" ? "Moon" : "Ascendant"})
          </div>
          <div className="flex flex-col sm:flex-row items-center gap-3 p-1">
            <div className="flex-shrink-0 p-1">
              <DonutChart
                size={110}
                segments={[
                  { value: houseActivation["Highly Activated"].length || 0.0001, color: "var(--success-400)" },
                  { value: houseActivation["Activated"].length || 0.0001, color: "var(--cyan-400)" },
                  { value: houseActivation["Moderate"].length || 0.0001, color: "var(--gold-400)" },
                  { value: houseActivation["Low"].length || 0.0001, color: "var(--text-tertiary)" },
                  { value: houseActivation["Challenged"].length || 0.0001, color: "var(--danger-400)" },
                  { value: houseActivation["Heavily Challenged"].length || 0.0001, color: "#7f1d1d" },
                ]}
              />
            </div>
            <div className="flex flex-col gap-1 w-full min-w-0">
              {(["Highly Activated", "Activated", "Moderate", "Low", "Challenged", "Heavily Challenged"] as const).map((label) => (
                <div key={label} className="flex items-center gap-1.5 text-xs">
                  <span className="text-slate-700 dark:text-slate-300">{label}</span>
                  <span className="ml-auto text-slate-500 dark:text-slate-400 font-mono text-[11px] truncate">
                    {houseActivation[label].join(", ") || "—"}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </Card>

        <Card>
          <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-slate-600 dark:text-slate-400">
            Planetary Returns
          </div>
          <p className="mb-2 text-xs text-slate-600 dark:text-slate-400">
            Current planet return status against natal degree coordinates.
          </p>
          {!returnEvents ? (
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Loading return-period data…
            </p>
          ) : (
            <Timeline events={returnEvents} />
          )}
        </Card>

        <TransitAlerts transits={transits} patterns={patternsQuery.data} />
      </div>

      {/* Vedha Analysis */}
      <div className="mb-3">
        <Card>
          <VedhaAnalysisPanel transits={transits} dashaChain={dashaChain} />
        </Card>
      </div>

      {/* Detailed Transit Analysis / Settings */}
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-[1.6fr_1fr]">
        <Card padding="0">
          <div className="px-4 py-3.5 border-b border-slate-200 dark:border-slate-800">
            <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              Detailed Transit Analysis
            </span>
          </div>
          <div className="p-4">
            {(patternsQuery.data?.aspects.length ?? 0) === 0 ? (
              <p className="text-sm text-slate-500 dark:text-slate-400">
                {patternsQuery.isLoading ? "Loading…" : "No transit-to-natal aspects detected right now."}
              </p>
            ) : (
              <Table
                columns={[
                  { key: "transiting_planet", label: "Transit" },
                  {
                    key: "aspect_type",
                    label: "Aspect Type",
                    render: (a) => (
                      <span className="capitalize font-medium text-slate-800 dark:text-slate-200">
                        {a.aspect_type === "special_graha" ? "Special Aspect" : a.aspect_type}
                      </span>
                    ),
                  },
                  { key: "natal_planet", label: "Natal Target" },
                  {
                    key: "orb",
                    label: "Orb",
                    mono: true,
                    render: (a) => <span className="font-mono text-slate-700 dark:text-slate-300 font-medium">{a.orb.toFixed(2)}°</span>,
                  },
                  {
                    key: "nature",
                    label: "Nature",
                    render: (a) => {
                      // than guessing which planet cast it from this field
                      // alone.
                      const harmonious = a.aspect_type === "trine";
                      const tense = a.aspect_type === "square" || a.aspect_type === "opposition";
                      const tone = harmonious ? "success" : tense ? "danger" : "neutral";
                      const label = harmonious ? "Benefic" : tense ? "Challenging" : "Neutral";
                      return <Badge tone={tone}>{label}</Badge>;
                    },
                  },
                ]}
                rows={patternsQuery.data?.aspects ?? []}
              />
            )}
          </div>
        </Card>

        <Card>
          <div className="mb-3 text-[10px] font-bold uppercase tracking-widest" style={{ color: "var(--text-tertiary)" }}>
            Transit Settings
          </div>
          <dl className="mb-4 flex flex-col gap-2 text-xs">
            <div className="flex justify-between">
              <dt style={{ color: "var(--text-muted)" }}>Ayanamsa</dt>
              <dd style={{ color: "var(--text-primary)" }}>{request?.ayanamsa}</dd>
            </div>
            <div className="flex justify-between">
              <dt style={{ color: "var(--text-muted)" }}>House System</dt>
              <dd style={{ color: "var(--text-primary)" }}>{request?.house_system}</dd>
            </div>
            <div className="flex justify-between">
              <dt style={{ color: "var(--text-muted)" }}>Transit Moment</dt>
              <dd className="font-mono" style={{ color: "var(--text-primary)" }}>
                {new Date(transits.transit_datetime_utc).toLocaleString()}
              </dd>
            </div>
          </dl>
          <Button variant="secondary" fullWidth onClick={handleRecalculate} disabled={isRecalculating}>
            {isRecalculating ? "Recalculating…" : "Recalculate Transits"}
          </Button>
        </Card>
      </div>

      {/* House Cusps — real cusp longitude per house from the natal chart's
          own house_system (Whole Sign, Placidus, etc., whatever this chart
          was generated with) — not an assumed 30°/house. Nakshatra/pada are
          derived client-side from the same sidereal_longitude the backend
          returned, via the same nakshatraFromLongitude() other pages use. */}
      <div className="mt-6">
        <Card padding="0">
          <div style={{ padding: "14px 18px", borderBottom: "1px solid var(--border-subtle)" }}>
            <span style={{ fontSize: "var(--text-sm)", fontWeight: "var(--weight-semibold)", color: "var(--text-primary)" }}>
              House Cusps
            </span>
            <span className="ml-2 text-xs" style={{ color: "var(--text-tertiary)" }}>
              {request?.house_system ?? result.chart.house_system} system — real cusp degrees, not assumed 30°/house
            </span>
          </div>
          <div style={{ padding: "10px 18px 18px" }}>
            <Table
              columns={[
                { key: "house_number", label: "House", mono: true },
                { key: "rashi", label: "Rashi", render: (h) => <span style={{ textTransform: "capitalize" }}>{h.rashi}</span> },
                { key: "sidereal_longitude", label: "Cusp Degree", mono: true, render: (h) => formatDegree(h.sidereal_longitude % 30) },
                {
                  key: "nakshatra",
                  label: "Nakshatra",
                  render: (h) => {
                    const { nakshatra, pada } = nakshatraFromLongitude(h.sidereal_longitude);
                    return (
                      <span style={{ textTransform: "capitalize" }}>
                        {nakshatra.replace(/_/g, " ")} — Pada {pada}
                      </span>
                    );
                  },
                },
                { key: "nakshatra_lord", label: "Star Lord", render: (h) => <span style={{ textTransform: "capitalize" }}>{h.nakshatra_lord}</span> },
                { key: "sub_lord", label: "Sub Lord (KP)", render: (h) => <span style={{ textTransform: "capitalize" }}>{h.sub_lord}</span> },
              ]}
              rows={result.chart.houses}
            />
          </div>
        </Card>
      </div>
        </>
      )}
    </SplitWorkspaceLayout>
  );
}

export default function TransitAnalysisPage() {
  return (
    <Suspense fallback={null}>
      <TransitAnalysisPageContent />
    </Suspense>
  );
}
