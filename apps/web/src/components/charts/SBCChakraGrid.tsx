"use client";

import { useMemo, useState } from "react";
import { useMyCharts } from "@/lib/charts";
import { useSBCReport, type SBCGridPlanet, type SBCSensitivePoint } from "@/lib/sbc";
import { FULL_GRID, SBC_81_CANONICAL, vedhaPath } from "@/lib/sbcCellnumTable";
import { AiSbcAnalyzerCard } from "./AiSbcAnalyzerCard";


const UPPER_ROW = ["dhanishtha", "shatabhisha", "purva_bhadrapada", "uttara_bhadrapada", "revati", "ashwini", "bharani"];
const RIGHT_COLUMN = ["krittika", "rohini", "mrigashira", "ardra", "punarvasu", "pushya", "ashlesha"];
const BOTTOM_ROW = ["magha", "purva_phalguni", "uttara_phalguni", "hasta", "chitra", "swati", "vishakha"];
const LEFT_COLUMN = ["anuradha", "jyeshtha", "mula", "purva_ashadha", "uttara_ashadha", "abhijit", "shravana"];

const NAKSHATRA_LABEL: Record<string, string> = {
  dhanishtha: "Dhan", shatabhisha: "Sata", purva_bhadrapada: "PBha", uttara_bhadrapada: "UBha",
  revati: "Reva", ashwini: "Aswi", bharani: "Bhar",
  krittika: "Krit", rohini: "Rohi", mrigashira: "Mrig", ardra: "Ardr", punarvasu: "Puna",
  pushya: "Push", ashlesha: "Asre",
  magha: "Magh", purva_phalguni: "PPha", uttara_phalguni: "UPha", hasta: "Hast", chitra: "Chit",
  swati: "Swat", vishakha: "Visa",
  anuradha: "Anu", jyeshtha: "Jye", mula: "Mool", purva_ashadha: "PSha", uttara_ashadha: "USha",
  abhijit: "Abhi", shravana: "Srav",
};

const PLANET_SYMBOLS: Record<string, { glyph: string; color: string; label: string }> = {
  sun: { glyph: "☉", color: "#fb923c", label: "Sun" },
  moon: { glyph: "☽", color: "#60a5fa", label: "Moon" },
  mars: { glyph: "♂", color: "#f87171", label: "Mars" },
  mercury: { glyph: "☿", color: "#34d399", label: "Mercury" },
  jupiter: { glyph: "♃", color: "#fbbf24", label: "Jupiter" },
  venus: { glyph: "♀", color: "#f472b6", label: "Venus" },
  saturn: { glyph: "♄", color: "#a78bfa", label: "Saturn" },
  rahu: { glyph: "☊", color: "#818cf8", label: "Rahu" },
  ketu: { glyph: "☋", color: "#c084fc", label: "Ketu" },
};

const DIRECTION_COLOR: Record<"front" | "left" | "right", string> = {
  front: "rgba(52, 211, 153, 0.28)", // green
  left: "rgba(56, 189, 248, 0.28)",  // blue
  right: "rgba(248, 113, 113, 0.28)", // red
};

const GRID_MIN = 1;
const GRID_MAX = 9;

function buildBorder(): Record<string, [number, number]> {
  const border: Record<string, [number, number]> = {};
  UPPER_ROW.forEach((n, i) => (border[n] = [2 + i, 1]));
  RIGHT_COLUMN.forEach((n, i) => (border[n] = [9, 2 + i]));
  BOTTOM_ROW.forEach((n, i) => (border[n] = [8 - i, 9]));
  LEFT_COLUMN.forEach((n, i) => (border[n] = [1, 8 - i]));
  return border;
}

const SBC_BORDER = buildBorder();
const ALL_NAKSHATRAS = Object.keys(SBC_BORDER);

function normalizeToken(token?: string | null): string {

  if (!token) return "";
  return token.toLowerCase().trim().replace(/[\s-]+/g, "_");
}

function planetsByNakshatra(positions: SBCGridPlanet[]): Record<string, SBCGridPlanet[]> {
  const map: Record<string, SBCGridPlanet[]> = {};
  for (const p of positions) {
    const key = normalizeToken(p.nakshatra);
    (map[key] ??= []).push(p);
  }
  return map;
}

export function SBCChakraGrid() {
  const { data: myCharts } = useMyCharts();
  const [selectedChartId, setSelectedChartId] = useState<string>("default");
  const [transitLocal, setTransitLocal] = useState<string>("");
  const [manualJanma, setManualJanma] = useState<string>("rohini");
  const [rayFrom, setRayFrom] = useState<string | null>(null);
  const [selectedPointKey, setSelectedPointKey] = useState<string>("janma");

  // Selected chart details
  const activeChart = useMemo(() => {
    if (!myCharts?.charts?.length) return null;
    if (selectedChartId === "default") {
      return myCharts.charts.find((c) => c.is_default) || myCharts.charts[0];
    }
    return myCharts.charts.find((c) => c.id === selectedChartId) || null;
  }, [myCharts, selectedChartId]);

  const transitMomentUtc = useMemo(() => {
    if (!transitLocal) return null;
    const d = new Date(transitLocal);
    return isNaN(d.getTime()) ? null : d.toISOString();
  }, [transitLocal]);

  const reportPayload = useMemo(() => {
    if (activeChart) {
      return {
        moment_utc: transitMomentUtc,
        birth_datetime_utc: activeChart.birth_datetime_utc,
        birth_latitude: activeChart.birth_latitude,
        birth_longitude: activeChart.birth_longitude,
        ayanamsa: activeChart.ayanamsa || "lahiri",
        chart_id: activeChart.id,
      };
    }
    return {
      moment_utc: transitMomentUtc,
      janma_nakshatra: manualJanma,
    };
  }, [activeChart, transitMomentUtc, manualJanma]);


  const { data, isLoading, error } = useSBCReport(reportPayload);

  const groupedPlanets = useMemo(() => (data ? planetsByNakshatra(data.positions) : {}), [data]);

  // Ray highlighting map
  const highlightedCells = useMemo(() => {
    if (!rayFrom) return {};
    const normRay = normalizeToken(rayFrom);
    const map: Record<number, "front" | "left" | "right"> = {};
    (["front", "left", "right"] as const).forEach((dir) => {
      for (const cellnum of vedhaPath(normRay, dir)) {
        map[cellnum] = dir;
      }
    });
    return map;
  }, [rayFrom]);

  // Sensitive points indexed by nakshatra
  const sensitivePointMap = useMemo(() => {
    const map: Record<string, SBCSensitivePoint[]> = {};
    if (data?.sensitive_points) {
      for (const pt of data.sensitive_points) {
        const key = normalizeToken(pt.nakshatra_token || pt.nakshatra_name);
        (map[key] ??= []).push(pt);
      }
    }
    return map;
  }, [data]);

  const selectedPoint = useMemo(() => {
    if (!data?.sensitive_points?.length) return null;
    return data.sensitive_points.find((p) => p.key === selectedPointKey) || data.sensitive_points[0];
  }, [data, selectedPointKey]);

  const selectedPointTransit = useMemo(() => {
    if (!selectedPoint || !data?.positions) return null;
    const targetToken = normalizeToken(selectedPoint.nakshatra_token || selectedPoint.nakshatra_name);
    return data.positions.filter((p) => normalizeToken(p.nakshatra) === targetToken);
  }, [selectedPoint, data]);

  // Grid coordinates matrix (1..9 x 1..9)
  const gridCells = useMemo(() => {
    const grid: { col: number; row: number; cellnum: number }[][] = [];
    for (let row = GRID_MIN; row <= GRID_MAX; row++) {
      const rowCells: { col: number; row: number; cellnum: number }[] = [];
      for (let col = GRID_MIN; col <= GRID_MAX; col++) {
        const cellnum = FULL_GRID[`${col},${row}`];
        rowCells.push({ col, row, cellnum });
      }
      grid.push(rowCells);
    }
    return grid;
  }, []);


  return (
    <div className="space-y-4">
      {/* ── Top Bar: Title & Selectors ──────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b pb-3" style={{ borderColor: "var(--border-primary)" }}>
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold tracking-tight" style={{ color: "var(--text-primary)" }}>
            Sarvatobhadra Chakra (SBC)
          </h1>
          <span className="text-xs text-muted-foreground px-2 py-0.5 rounded border" style={{ borderColor: "var(--border-primary)" }}>
            Classical 81-Cell Matrix (28 Nakshatra + 12 Rashi + 16 Swara + 20 Akshara + 5 Tithi)
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs">
          {/* Chart selector */}
          <select
            value={selectedChartId}
            onChange={(e) => setSelectedChartId(e.target.value)}
            className="rounded border px-2.5 py-1.5 font-medium"
            style={{
              borderColor: "var(--border-primary)",
              background: "var(--bg-secondary)",
              color: "var(--text-primary)",
            }}
          >
            {myCharts?.charts?.length ? (
              myCharts.charts.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.subject_name} {c.is_default ? "(Default D1)" : "(D1)"}
                </option>
              ))
            ) : (
              <option value="default">D1 (Natal Reference)</option>
            )}
          </select>

          {/* Fallback Janma Nakshatra if no chart */}
          {!activeChart && (
            <select
              value={manualJanma}
              onChange={(e) => setManualJanma(e.target.value)}
              className="rounded border px-2.5 py-1.5 font-medium"
              style={{
                borderColor: "var(--border-primary)",
                background: "var(--bg-secondary)",
                color: "var(--text-primary)",
              }}
            >
              {ALL_NAKSHATRAS.map((n) => (
                <option key={n} value={n}>
                  Janma: {NAKSHATRA_LABEL[n] ?? n}
                </option>
              ))}
            </select>
          )}

          {/* Transit Date / Time selector */}
          <div className="flex items-center gap-1 rounded border px-2 py-1" style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)" }}>
            <span style={{ color: "var(--text-muted)" }}>Transit:</span>
            <input
              type="datetime-local"
              value={transitLocal}
              onChange={(e) => setTransitLocal(e.target.value)}
              className="bg-transparent text-xs outline-none"
              style={{ color: "var(--text-primary)" }}
            />
            {transitLocal && (
              <button
                type="button"
                onClick={() => setTransitLocal("")}
                className="text-[10px] text-muted-foreground hover:text-primary cursor-pointer px-1 py-0.5 rounded hover:bg-muted"
              >
                Now
              </button>
            )}
          </div>

        </div>
      </div>

      {isLoading && (
        <div className="p-4 text-center text-sm" style={{ color: "var(--text-muted)" }}>
          Calculating Sarvatobhadra Chakra & planetary Vedhas…
        </div>
      )}

      {error && (
        <div className="p-4 text-center text-sm rounded border my-2" style={{ borderColor: "rgba(248, 113, 113, 0.3)", background: "rgba(248, 113, 113, 0.08)", color: "#f87171" }}>
          <p className="font-semibold">Could not load SBC report</p>
          <p className="text-xs mt-1 text-muted-foreground">
            {error instanceof Error ? error.message : "An unexpected error occurred."}
          </p>
        </div>
      )}


      {data && (
        <>
          {/* ── Header Info Bar: Reference, Sangyas & Natal Attributes ──────── */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-3 p-3 rounded-lg border" style={{ background: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
            {/* Janma Reference */}
            <div className="md:col-span-3 flex flex-col justify-center border-r pr-3" style={{ borderColor: "var(--border-primary)" }}>
              <span className="text-[10px] uppercase font-semibold tracking-wider" style={{ color: "var(--text-muted)" }}>
                Reference (Janma Nakshatra)
              </span>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-base font-bold" style={{ color: "#fbbf24" }}>
                  ★ {data.janma_nakshatra ? NAKSHATRA_LABEL[data.janma_nakshatra] || data.janma_nakshatra : "Rohini"}
                </span>
                <span className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  ({data.natal_attributes?.janma_rashi_icon || "♉"} {data.natal_attributes?.janma_rashi || "Vrishabha"})
                </span>
              </div>
            </div>

            {/* Sensitive Points Chips */}
            <div className="md:col-span-5 flex flex-col justify-center border-r pr-3" style={{ borderColor: "var(--border-primary)" }}>
              <span className="text-[10px] uppercase font-semibold tracking-wider mb-1" style={{ color: "var(--text-muted)" }}>
                Active Sensitive Points (Sangyas)
              </span>
              <div className="flex flex-wrap gap-1.5">
                {data.sensitive_points?.map((pt) => {
                  const isSelected = selectedPointKey === pt.key;
                  const isJanma = pt.key === "janma";
                  const isAfflicted = pt.status === "afflicted";
                  const isActivated = pt.status === "activated";

                  let badgeBg = "rgba(255, 255, 255, 0.05)";
                  let borderCol = "var(--border-primary)";
                  let textCol = "var(--text-secondary)";

                  if (isJanma) {
                    badgeBg = "rgba(250, 204, 21, 0.15)";
                    borderCol = "#facc15";
                    textCol = "#facc15";
                  } else if (isAfflicted) {
                    badgeBg = "rgba(248, 113, 113, 0.15)";
                    borderCol = "#f87171";
                    textCol = "#f87171";
                  } else if (isActivated) {
                    badgeBg = "rgba(52, 211, 153, 0.15)";
                    borderCol = "#34d399";
                    textCol = "#34d399";
                  }

                  return (
                    <button
                      key={pt.key}
                      type="button"
                      onClick={() => {
                        setSelectedPointKey(pt.key);
                        setRayFrom(pt.nakshatra_token);
                      }}
                      className="px-2 py-0.5 rounded text-[11px] font-medium transition-all"
                      style={{
                        background: isSelected ? "rgba(56, 189, 248, 0.25)" : badgeBg,
                        border: `1px solid ${isSelected ? "#38bdf8" : borderCol}`,
                        color: isSelected ? "#38bdf8" : textCol,
                      }}
                    >
                      {isJanma && "★ "}
                      {isAfflicted && "✖ "}
                      {isActivated && "✓ "}
                      {pt.name}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Natal Attributes: Nama Akshara, Janma Rasi, Tithi, Vara */}
            <div className="md:col-span-4 grid grid-cols-4 gap-2 text-center">
              <div className="p-1 rounded border" style={{ borderColor: "var(--border-primary)", background: "var(--bg-primary)" }}>
                <div className="text-[9px] uppercase font-semibold" style={{ color: "var(--text-muted)" }}>Nama Sound</div>
                <div className="text-xs font-bold mt-0.5" style={{ color: "#38bdf8" }}>
                  {data.natal_attributes?.nama_akshara || "O"}
                </div>
              </div>
              <div className="p-1 rounded border" style={{ borderColor: "var(--border-primary)", background: "var(--bg-primary)" }}>
                <div className="text-[9px] uppercase font-semibold" style={{ color: "var(--text-muted)" }}>Janma Rasi</div>
                <div className="text-xs font-bold mt-0.5" style={{ color: "#facc15" }}>
                  {data.natal_attributes?.janma_rashi_icon} {data.natal_attributes?.janma_rashi || "Taurus"}
                </div>
              </div>
              <div className="p-1 rounded border" style={{ borderColor: "var(--border-primary)", background: "var(--bg-primary)" }}>
                <div className="text-[9px] uppercase font-semibold" style={{ color: "var(--text-muted)" }}>Tithi (Natal)</div>
                <div className="text-[11px] font-semibold mt-0.5" style={{ color: "var(--text-primary)" }}>
                  {data.natal_attributes?.tithi_group || "Purna"}
                </div>
              </div>
              <div className="p-1 rounded border" style={{ borderColor: "var(--border-primary)", background: "var(--bg-primary)" }}>
                <div className="text-[9px] uppercase font-semibold" style={{ color: "var(--text-muted)" }}>Vara (Natal)</div>
                <div className="text-[11px] font-semibold mt-0.5" style={{ color: "var(--text-primary)" }}>
                  {data.natal_attributes?.vara_name || "Friday"}
                </div>
              </div>
            </div>
          </div>

          {/* ── Main Layout: Chakra Grid on Left, Panels on Right ───────────── */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            {/* ── Left Area: Concentric 9x9 Sarvatobhadra Chakra ─────────────── */}
            <div className="lg:col-span-7 flex flex-col items-center space-y-3">
              <div className="w-full flex items-center justify-between text-xs px-1">
                <span className="font-semibold uppercase tracking-wider text-xs" style={{ color: "var(--text-primary)" }}>
                  SARVATOBHADRA CHAKRA (81 CELLS)
                </span>
                {rayFrom && (
                  <button
                    type="button"
                    onClick={() => setRayFrom(null)}
                    className="text-[11px] px-2 py-0.5 rounded-full border hover:opacity-80"
                    style={{ borderColor: "#38bdf8", color: "#38bdf8" }}
                  >
                    Clear Rays ({NAKSHATRA_LABEL[rayFrom] ?? rayFrom}) ✕
                  </button>
                )}
              </div>

              <div className="w-full overflow-x-auto flex justify-center p-2 rounded-lg border" style={{ background: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
                <table className="border-collapse text-center select-none" style={{ tableLayout: "fixed" }}>
                  <tbody>
                    {gridCells.map((rowCells, rIdx) => (
                      <tr key={rIdx}>
                        {rowCells.map((coord, cIdx) => {
                          const cellSemantic = SBC_81_CANONICAL[`${coord.col},${coord.row}`];
                          if (!cellSemantic) return null;

                          const isNakshatra = cellSemantic.category === "nakshatra";
                          const isSwara = cellSemantic.category === "swara";
                          const isAkshara = cellSemantic.category === "akshara";
                          const isRashi = cellSemantic.category === "rashi";
                          const isTithi = cellSemantic.category === "tithi";
                          const isCenter = Boolean(cellSemantic.metadata.is_center);
                          const nakToken = normalizeToken(cellSemantic.metadata.nakshatra_token);

                          const isJanma = nakToken !== "" && nakToken === normalizeToken(data.janma_nakshatra);
                          const isRayOrigin = nakToken !== "" && nakToken === normalizeToken(rayFrom);
                          const rayDirection = highlightedCells[coord.cellnum];
                          const occupants = nakToken ? groupedPlanets[nakToken] ?? [] : [];
                          const sensitivePointsHere = nakToken ? sensitivePointMap[nakToken] ?? [] : [];

                          // Background calculation
                          let cellBg = "var(--bg-primary)";
                          if (cellSemantic.layer === 2) cellBg = "rgba(255, 255, 255, 0.02)";
                          if (cellSemantic.layer === 3) cellBg = "rgba(56, 189, 248, 0.03)";
                          if (cellSemantic.layer === 4) cellBg = "rgba(250, 204, 21, 0.03)";
                          if (isCenter) cellBg = "rgba(250, 204, 21, 0.12)";

                          if (rayDirection) cellBg = DIRECTION_COLOR[rayDirection];
                          if (isRayOrigin) cellBg = "rgba(250, 204, 21, 0.35)";
                          if (isJanma && !isRayOrigin && !rayDirection) cellBg = "rgba(250, 204, 21, 0.18)";

                          // Border styling
                          let cellBorder = "1px solid var(--border-primary)";
                          if (isJanma) cellBorder = "2px solid #facc15";
                          if (isCenter) cellBorder = "2px solid #fbbf24";

                          return (
                            <td
                              key={cIdx}
                              onClick={() => {
                                if (nakToken) {
                                  setRayFrom(nakToken === normalizeToken(rayFrom) ? null : nakToken);
                                  if (sensitivePointsHere.length > 0) {
                                    setSelectedPointKey(sensitivePointsHere[0].key);
                                  }
                                }
                              }}
                              className="h-14 w-14 border p-1 align-top relative transition-all"
                              style={{
                                border: cellBorder,
                                background: cellBg,
                                cursor: nakToken ? "pointer" : "default",
                              }}
                            >
                              <div className="flex h-full flex-col justify-between items-center text-center">
                                {/* 1. Nakshatra Cell */}
                                {isNakshatra && (
                                  <div className="w-full flex justify-between items-center text-[10px] leading-tight">
                                    <span className="font-semibold" style={{ color: isJanma ? "#facc15" : "var(--text-primary)" }}>
                                      {NAKSHATRA_LABEL[nakToken] || cellSemantic.display_name_en}
                                    </span>
                                    <span className="text-[9px]" style={{ color: "var(--text-muted)" }}>
                                      {cellSemantic.metadata.nakshatra_number}
                                    </span>
                                  </div>
                                )}

                                {/* 2. Swara (Vowel) Cell */}
                                {isSwara && (
                                  <div className="flex flex-col items-center justify-center my-auto">
                                    <span className="text-[11px] font-bold text-amber-400">
                                      {cellSemantic.display_name_hi}
                                    </span>
                                    <span className="text-[8px] text-muted-foreground">
                                      {cellSemantic.display_name_en}
                                    </span>
                                  </div>
                                )}

                                {/* 3. Akshara (Consonant) Cell */}
                                {isAkshara && (
                                  <div className="flex flex-col items-center justify-center my-auto">
                                    <span className="text-[12px] font-medium" style={{ color: "var(--text-secondary)" }}>
                                      {cellSemantic.display_name_hi}
                                    </span>
                                    <span className="text-[8px]" style={{ color: "var(--text-muted)" }}>
                                      {cellSemantic.display_name_en}
                                    </span>
                                  </div>
                                )}

                                {/* 4. Rashi Cell */}
                                {isRashi && (
                                  <div className="flex flex-col items-center justify-center my-auto">
                                    <span className="text-[12px] font-bold" style={{ color: "#38bdf8" }}>
                                      {cellSemantic.metadata.symbol}
                                    </span>
                                    <span className="text-[9px]" style={{ color: "var(--text-secondary)" }}>
                                      {cellSemantic.display_name_hi}
                                    </span>
                                  </div>
                                )}

                                {/* 5. Tithi with Vara Overlay / Center Cell */}
                                {isTithi && (
                                  <div className="flex flex-col items-center justify-center my-auto w-full">
                                    {isCenter ? (
                                      <>
                                        <span className="text-[8px] font-bold uppercase tracking-wider text-amber-400">
                                          CENTER
                                        </span>
                                        <span className="text-[11px] font-extrabold text-amber-300">
                                          {data.janma_nakshatra ? NAKSHATRA_LABEL[normalizeToken(data.janma_nakshatra)] || data.janma_nakshatra : "Rohini"}
                                        </span>
                                        <span className="text-[8px] text-amber-400">
                                          {data.natal_attributes?.janma_rashi_icon || "♉"}
                                        </span>
                                      </>
                                    ) : (
                                      <>
                                        <span className="text-[10px] font-semibold" style={{ color: "#34d399" }}>
                                          {cellSemantic.display_name_hi}
                                        </span>
                                        <span className="text-[8px] px-1 rounded font-medium mt-0.5" style={{ background: "rgba(255, 255, 255, 0.06)", color: "var(--text-muted)" }}>
                                          {cellSemantic.metadata.vara_hi}
                                        </span>
                                      </>
                                    )}
                                  </div>
                                )}

                                {/* Occupant Transit Planets in this cell */}
                                {occupants.length > 0 && (
                                  <div className="flex flex-wrap items-center justify-center gap-1 my-auto">
                                    {occupants.map((p, pIdx) => {
                                      const sym = PLANET_SYMBOLS[normalizeToken(p.planet)] || { glyph: p.planet.slice(0, 2), color: "#38bdf8", label: p.planet };
                                      return (
                                        <span
                                          key={pIdx}
                                          className="inline-flex items-center px-1 rounded text-[10px] font-bold shadow-sm"
                                          style={{
                                            background: "rgba(0, 0, 0, 0.75)",
                                            color: sym.color,
                                            border: `1px solid ${sym.color}`,
                                          }}
                                        >
                                          {sym.glyph}
                                          {p.is_retrograde && <span className="text-[8px] ml-0.5">℞</span>}
                                          {p.is_combust && <span className="text-[8px] ml-0.5">🜂</span>}
                                          {p.pada && <span className="text-[8px] ml-0.5 opacity-75">{p.pada}</span>}
                                        </span>
                                      );
                                    })}
                                  </div>
                                )}


                                {/* Sensitive Point markers (e.g. ★ Janma, Karma) */}
                                {sensitivePointsHere.length > 0 && (
                                  <div className="w-full flex justify-center gap-0.5 mt-auto">
                                    {sensitivePointsHere.map((sp, spIdx) => (
                                      <span
                                        key={spIdx}
                                        className="text-[8px] font-bold px-1 rounded"
                                        style={{
                                          background: sp.status === "afflicted" ? "#f87171" : sp.status === "activated" ? "#34d399" : "#facc15",
                                          color: "#000",
                                        }}
                                      >
                                        {sp.name.slice(0, 3)}
                                      </span>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Legend */}
              <div className="w-full flex flex-wrap items-center justify-between gap-2 text-[11px] px-2" style={{ color: "var(--text-muted)" }}>
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1">
                    <span className="w-2.5 h-2.5 rounded-sm" style={{ background: DIRECTION_COLOR.front }} /> Front (Opposite)
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-2.5 h-2.5 rounded-sm" style={{ background: DIRECTION_COLOR.left }} /> Left (Direct)
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-2.5 h-2.5 rounded-sm" style={{ background: DIRECTION_COLOR.right }} /> Right (Retrograde)
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-amber-400 font-bold">★ Janma</span>
                  <span>℞ Retrograde</span>
                  <span>🜂 Combust</span>
                </div>
              </div>
            </div>

            {/* ── Right Panels: Transits, Vedhas & Sangya Status ─────────────── */}
            <div className="lg:col-span-5 space-y-3">
              {/* 1. Planetary Positions (Transit) */}
              <div className="p-3 rounded-lg border space-y-2" style={{ background: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
                <h3 className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-primary)" }}>
                  Planetary Positions (Transit)
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b text-[10px] uppercase font-semibold text-muted-foreground" style={{ borderColor: "var(--border-primary)" }}>
                        <th className="pb-1">Planet</th>
                        <th className="pb-1">Nakshatra</th>
                        <th className="pb-1">Pada</th>
                        <th className="pb-1">Motion</th>
                        <th className="pb-1">Ray</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/20">
                      {data.positions?.map((p) => {
                        const normP = normalizeToken(p.planet);
                        const normN = normalizeToken(p.nakshatra);
                        const sym = PLANET_SYMBOLS[normP] || { glyph: "●", color: "#38bdf8", label: p.planet };
                        return (
                          <tr
                            key={p.planet}
                            onClick={() => setRayFrom(normN)}
                            className="hover:bg-primary/5 cursor-pointer"
                          >
                            <td className="py-1 flex items-center gap-1.5 font-medium" style={{ color: sym.color }}>
                              <span>{sym.glyph}</span> {sym.label}
                            </td>
                            <td className="py-1" style={{ color: "var(--text-secondary)" }}>
                              {NAKSHATRA_LABEL[normN] || p.nakshatra}
                            </td>
                            <td className="py-1" style={{ color: "var(--text-muted)" }}>
                              {p.pada || 1}
                            </td>

                            <td className="py-1">
                              <span
                                className="px-1.5 py-0.5 rounded text-[10px] font-medium"
                                style={{
                                  background: p.is_retrograde ? "rgba(248, 113, 113, 0.15)" : "rgba(255, 255, 255, 0.05)",
                                  color: p.is_retrograde ? "#f87171" : "var(--text-secondary)",
                                }}
                              >
                                {p.motion}
                              </span>
                            </td>
                            <td className="py-1 font-medium" style={{ color: p.ray_direction === "Right" ? "#f87171" : "#34d399" }}>
                              {p.ray_direction}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* 2. Vedha Summary (Benefic vs Malefic Cards) */}
              <div className="p-3 rounded-lg border space-y-2.5" style={{ background: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-primary)" }}>
                    VEDHA SUMMARY
                  </h3>
                  <span className="text-[10px] text-muted-foreground uppercase font-semibold">
                    Convention: {data.convention_used || "Narapati Jayacharya"}
                  </span>
                </div>

                {/* Benefic Vedha */}
                <div className="p-2 rounded border space-y-1.5" style={{ borderColor: "rgba(52, 211, 153, 0.3)", background: "rgba(52, 211, 153, 0.05)" }}>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-emerald-400">
                      Benefic Vedha (Protective / Auspicious)
                    </span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300">
                      {data.benefic_vedhas?.length || 0} Ray(s) Active
                    </span>
                  </div>
                  {data.benefic_vedhas?.length ? (
                    <ul className="space-y-1 text-xs">
                      {data.benefic_vedhas.map((bv, idx) => (
                        <li key={idx} className="flex items-center justify-between text-muted-foreground">
                          <span>
                            <strong className="text-emerald-300">{bv.planet.toUpperCase()}</strong> ({bv.direction}) → {bv.target_points.join(", ")}
                          </span>
                          {bv.strength_factors?.dignity && (
                            <span className="text-[10px] text-emerald-400 capitalize">
                              {bv.strength_factors.dignity}
                            </span>
                          )}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-[11px] text-muted-foreground italic">No benefic Vedha hits currently.</p>
                  )}
                </div>

                {/* Malefic Vedha */}
                <div className="p-2 rounded border space-y-1.5" style={{ borderColor: "rgba(248, 113, 113, 0.3)", background: "rgba(248, 113, 113, 0.05)" }}>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-rose-400">
                      Malefic Vedha (Obstructive / Affliction)
                    </span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300">
                      {data.malefic_vedhas?.length || 0} Affliction(s) Active
                    </span>
                  </div>
                  {data.malefic_vedhas?.length ? (
                    <ul className="space-y-1 text-xs">
                      {data.malefic_vedhas.map((mv, idx) => (
                        <li key={idx} className="flex items-center justify-between text-muted-foreground">
                          <span>
                            <strong className="text-rose-300">{mv.planet.toUpperCase()}</strong> ({mv.direction}) → {mv.target_points.join(", ")}
                          </span>
                          {mv.strength_factors?.dignity && (
                            <span className="text-[10px] text-rose-400 capitalize">
                              {mv.strength_factors.dignity}
                            </span>
                          )}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-[11px] text-muted-foreground italic">No malefic afflictions currently.</p>
                  )}
                </div>
              </div>

              {/* 3. Active Sensitive Point Status Table */}
              <div className="p-3 rounded-lg border space-y-2" style={{ background: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
                <h3 className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-primary)" }}>
                  Active Sensitive Point Status (10 Sangyas)
                </h3>
                <div className="overflow-x-auto max-h-48 overflow-y-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b text-[10px] uppercase font-semibold text-muted-foreground" style={{ borderColor: "var(--border-primary)" }}>
                        <th className="pb-1">Point</th>
                        <th className="pb-1">Nakshatra</th>
                        <th className="pb-1">Status</th>
                        <th className="pb-1">Vedha Received</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/20">
                      {data.sensitive_points?.map((pt) => {
                        const isSelected = selectedPointKey === pt.key;
                        return (
                          <tr
                            key={pt.key}
                            onClick={() => {
                              setSelectedPointKey(pt.key);
                              setRayFrom(pt.nakshatra_token);
                            }}
                            className="hover:bg-primary/5 cursor-pointer transition-all"
                            style={{ background: isSelected ? "rgba(56, 189, 248, 0.1)" : undefined }}
                          >
                            <td className="py-1 font-semibold" style={{ color: pt.key === "janma" ? "#facc15" : "var(--text-primary)" }}>
                              {pt.key === "janma" && "★ "}
                              {pt.name}
                            </td>
                            <td className="py-1 text-muted-foreground">
                              {pt.nakshatra_name}
                            </td>
                            <td className="py-1">
                              <span
                                className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase"
                                style={{
                                  color: pt.status === "afflicted" ? "#f87171" : pt.status === "activated" ? "#34d399" : pt.status === "mixed" ? "#fb923c" : "var(--text-muted)",
                                }}
                              >
                                {pt.status === "afflicted" ? "✖ Afflicted" : pt.status === "activated" ? "★ Activated" : pt.status === "mixed" ? "⚡ Mixed" : "Neutral"}
                              </span>
                            </td>
                            <td className="py-1 text-[11px] text-muted-foreground">
                              {pt.vedhas_received.length > 0 ? pt.vedhas_received.join(", ") : "None"}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>

          {/* ── Classical SBC AI & Sangyas Synthesis Panel ─────────────────── */}
          {data.synthesis && (
            <div className="space-y-4 p-4 rounded-lg border" style={{ background: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
              <div className="flex items-center justify-between border-b pb-2" style={{ borderColor: "var(--border-primary)" }}>
                <div className="flex items-center gap-2">
                  <span className="text-base font-bold text-primary">
                    Classical SBC Synthesis & 10 Sangyas Analysis
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold border" style={{ borderColor: "#38bdf8", color: "#38bdf8", background: "rgba(56, 189, 248, 0.08)" }}>
                    Narapatijayacharya Svarodaya
                  </span>
                </div>
                <span className="text-xs text-muted-foreground">
                  Reference: <strong>{data.janma_nakshatra ? (NAKSHATRA_LABEL[normalizeToken(data.janma_nakshatra)] || data.janma_nakshatra) : "Janma"}</strong>
                </span>
              </div>

              {/* 1. Malefic vs Benefic Breakdown Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* Malefic Afflictions */}
                <div className="p-3 rounded-lg border space-y-2.5" style={{ background: "rgba(248, 113, 113, 0.03)", borderColor: "rgba(248, 113, 113, 0.25)" }}>
                  <div className="flex items-center justify-between text-xs font-bold" style={{ color: "#f87171" }}>
                    <span>1. Malefic Vedha Breakdown (Afflictions)</span>
                    <span>{data.synthesis.high_risk_areas.length} Active Hit{data.synthesis.high_risk_areas.length === 1 ? "" : "s"}</span>
                  </div>

                  {data.synthesis.high_risk_areas.length === 0 ? (
                    <div className="text-xs text-muted-foreground italic py-2">
                      No malefic Vedha afflictions on the 10 Sangyas at this moment.
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {data.synthesis.high_risk_areas.map((item, idx) => (
                        <div key={idx} className="p-2 rounded border text-xs space-y-1" style={{ background: "rgba(0, 0, 0, 0.2)", borderColor: "rgba(248, 113, 113, 0.2)" }}>
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-red-400">
                              {item.sangya_name} ({item.sangya_offset}th - {item.nakshatra_name})
                            </span>
                            <span className="text-[11px] font-semibold px-1.5 py-0.5 rounded text-red-300" style={{ background: "rgba(248, 113, 113, 0.15)" }}>
                              {item.transiting_planet} ({item.transiting_nakshatra}) • {item.aspect_ray} Ray
                            </span>
                          </div>
                          <div className="text-[11px] text-muted-foreground">
                            <strong>Domain Hit:</strong> {item.domain}
                          </div>
                          <div className="text-[11px] font-medium text-red-200">
                            {item.impact}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Benefic Protections */}
                <div className="p-3 rounded-lg border space-y-2.5" style={{ background: "rgba(52, 211, 153, 0.03)", borderColor: "rgba(52, 211, 153, 0.25)" }}>
                  <div className="flex items-center justify-between text-xs font-bold" style={{ color: "#34d399" }}>
                    <span>2. Benefic Vedha Breakdown (Protection / Shields)</span>
                    <span>{data.synthesis.protective_shields.length} Active Shield{data.synthesis.protective_shields.length === 1 ? "" : "s"}</span>
                  </div>

                  {data.synthesis.protective_shields.length === 0 ? (
                    <div className="text-xs text-muted-foreground italic py-2">
                      No direct benefic Vedha shields on the 10 Sangyas at this moment.
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {data.synthesis.protective_shields.map((item, idx) => (
                        <div key={idx} className="p-2 rounded border text-xs space-y-1" style={{ background: "rgba(0, 0, 0, 0.2)", borderColor: "rgba(52, 211, 153, 0.2)" }}>
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-emerald-400">
                              {item.sangya_name} ({item.sangya_offset}th - {item.nakshatra_name})
                            </span>
                            <span className="text-[11px] font-semibold px-1.5 py-0.5 rounded text-emerald-300" style={{ background: "rgba(52, 211, 153, 0.15)" }}>
                              {item.transiting_planet} ({item.transiting_nakshatra}) • {item.aspect_ray} Ray
                            </span>
                          </div>
                          <div className="text-[11px] text-muted-foreground">
                            <strong>Domain Shielded:</strong> {item.domain}
                          </div>
                          <div className="text-[11px] font-medium text-emerald-200">
                            {item.impact}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* 2. Executive Synthesis & Practical Interpretation */}
              <div className="p-3 rounded-lg border space-y-2 text-xs" style={{ background: "rgba(250, 204, 21, 0.03)", borderColor: "rgba(250, 204, 21, 0.2)" }}>
                <div className="font-bold text-amber-400 uppercase tracking-wide text-[11px]">
                  Final Synthesis & Practical Interpretation
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div className="p-2 rounded border" style={{ background: "rgba(248, 113, 113, 0.05)", borderColor: "rgba(248, 113, 113, 0.2)" }}>
                    <span className="font-semibold text-red-400">High Risk Caution: </span>
                    <span className="text-muted-foreground">{data.synthesis.executive_summary}</span>
                  </div>
                  <div className="p-2 rounded border" style={{ background: "rgba(52, 211, 153, 0.05)", borderColor: "rgba(52, 211, 153, 0.2)" }}>
                    <span className="font-semibold text-emerald-400">Saving Grace: </span>
                    <span className="text-muted-foreground">{data.synthesis.saving_grace}</span>
                  </div>
                </div>

                {data.synthesis.practical_advice.length > 0 && (
                  <div className="pt-1">
                    <div className="text-[11px] font-semibold text-amber-300 mb-1">Actionable Recommendations:</div>
                    <ul className="list-disc list-inside space-y-0.5 text-muted-foreground text-[11px]">
                      {data.synthesis.practical_advice.map((adv, aIdx) => (
                        <li key={aIdx}>{adv}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── AI SBC Event Analysis Module ───────────────────────────────── */}
          <AiSbcAnalyzerCard
            report={data ?? null}
            referenceNakshatra={data?.janma_nakshatra || manualJanma}
            transitDate={transitMomentUtc || data?.moment_utc}
          />


          {/* ── Bottom Bar: Selected Point Analysis ─────────────────────────── */}
          {selectedPoint && (

            <div className="p-4 rounded-lg border flex flex-wrap items-center justify-between gap-4" style={{ background: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="text-base font-bold text-sky-400">
                    {selectedPoint.name} ({selectedPoint.nakshatra_name})
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded-full border text-muted-foreground" style={{ borderColor: "var(--border-primary)" }}>
                    Nakshatra #{selectedPoint.nakshatra_number}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">
                  {selectedPointTransit && selectedPointTransit.length > 0 ? (
                    <>Transiting occupant: <strong className="text-primary">{selectedPointTransit.map((p) => p.planet.toUpperCase()).join(", ")}</strong></>
                  ) : (
                    "No direct transiting planet in this Nakshatra."
                  )}
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-6 text-xs">
                <div>
                  <div className="text-[10px] uppercase font-semibold text-muted-foreground">Vedha Received</div>
                  <div className="font-semibold text-primary">
                    {selectedPoint.vedhas_received.length > 0 ? selectedPoint.vedhas_received.join(", ") : "None"}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] uppercase font-semibold text-muted-foreground">Nature</div>
                  <div
                    className="font-bold uppercase"
                    style={{
                      color: selectedPoint.status === "afflicted" ? "#f87171" : selectedPoint.status === "activated" ? "#34d399" : selectedPoint.status === "mixed" ? "#fb923c" : "var(--text-muted)",
                    }}
                  >
                    {selectedPoint.status}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] uppercase font-semibold text-muted-foreground">Predicted Effect</div>
                  <div className="font-medium text-secondary-foreground">
                    {selectedPoint.status === "activated"
                      ? "Support, Growth, Auspicious elevation"
                      : selectedPoint.status === "afflicted"
                      ? "Obstacles, Delays, Precaution needed"
                      : selectedPoint.status === "mixed"
                      ? "Fluctuating results, Moderated influence"
                      : "Stable / Calm background influence"}
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}



