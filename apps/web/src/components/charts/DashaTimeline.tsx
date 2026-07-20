"use client";

import { useEffect, useRef, useState, useMemo, useCallback } from "react";
import * as d3 from "d3";
import { PLANET_ABBREV, PLANET_SYMBOLS } from "@/lib/astro";
import type { DashaTreeResponse, DashaPeriodResponse } from "@/lib/types";

interface DashaTimelineProps {
  dasha: DashaTreeResponse;
  /** Height in pixels for the main chart area. */
  height?: number;
}

const LEVEL_COLORS: Record<number, string> = {
  1: "#fbbf24", // Mahadasha — amber
  2: "#a78bfa", // Antardasha — purple
  3: "#34d399", // Pratyantar — green
  4: "#f87171", // Sookshma — red
  5: "#38bdf8", // Prana — blue
};

const LEVEL_NAMES = ["Mahadasha", "Antardasha", "Pratyantar", "Sookshma", "Prana"];

function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return dateStr;
  }
}

function computeCountdown(endDate: string): string {
  const now = new Date();
  const end = new Date(endDate);
  const diff = end.getTime() - now.getTime();

  if (diff <= 0) return "Ended";

  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const months = Math.floor(days / 30);
  const remainingDays = days % 30;

  if (months > 12) {
    const years = Math.floor(months / 12);
    const remMonths = months % 12;
    return `${years}y ${remMonths}m`;
  }
  if (months > 0) return `${months}m ${remainingDays}d`;
  return `${days}d`;
}

/**
 * Flatten the dasha tree to find the current running period
 * (the one whose start <= now <= end).
 */
function findCurrentPeriod(periods: DashaPeriodResponse[]): DashaPeriodResponse | null {
  const now = new Date();
  for (const p of periods) {
    const start = new Date(p.start_date);
    const end = new Date(p.end_date);
    if (now >= start && now <= end) {
      // Try to find a more granular child period
      if (p.children.length > 0) {
        const child = findCurrentPeriod(p.children);
        if (child) return child;
      }
      return p;
    }
  }
  return null;
}

/**
 * Find the next period that will begin after the current one ends.
 */
function findNextPeriod(
  mahadashas: DashaPeriodResponse[],
): DashaPeriodResponse | null {
  const now = new Date();
  for (const md of mahadashas) {
    if (new Date(md.start_date) > now) return md;
    if (new Date(md.end_date) > now) {
      // We're inside this mahadasha — check its antardashas
      if (md.children.length > 0) {
        for (const ad of md.children) {
          if (new Date(ad.start_date) > now) return ad;
          if (new Date(ad.end_date) > now && ad.children.length > 0) {
            return findNextPeriod(ad.children) ?? ad;
          }
        }
      }
    }
  }
  return null;
}

/**
 * DashaTimeline renders a horizontal D3.js timeline of mahadasha periods
 * with nested antardasha blocks, highlighting the current period and showing
 * a countdown to the next period.
 */
export function DashaTimeline({ dasha, height = 180 }: DashaTimelineProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(700);
  const [selectedPeriod, setSelectedPeriod] = useState<DashaPeriodResponse | null>(null);
  const [countdownTarget, setCountdownTarget] = useState<string | null>(null);
  const [countdownText, setCountdownText] = useState<string>("");

  // Observe container width for responsive sizing
  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setContainerWidth(entry.contentRect.width);
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  const now = new Date();
  const currentTime = now.getTime();

  // Find current and next periods
  const currentPeriod = useMemo(
    () => findCurrentPeriod(dasha.mahadashas),
    [dasha.mahadashas],
  );

  const nextPeriod = useMemo(
    () => findNextPeriod(dasha.mahadashas),
    [dasha.mahadashas],
  );

  // Countdown ticker
  useEffect(() => {
    const target = countdownTarget ?? nextPeriod?.end_date;
    if (!target) return;

    const tick = () => {
      const diff = new Date(target).getTime() - Date.now();
      if (diff <= 0) {
        setCountdownText("Ended");
        return;
      }
      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      setCountdownText(`${days}d ${hours}h remaining`);
    };

    tick();
    const interval = setInterval(tick, 60000); // update every minute
    return () => clearInterval(interval);
  }, [countdownTarget, nextPeriod]);

  // D3 rendering
  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = containerWidth;
    const margin = { top: 20, right: 20, bottom: 30, left: 20 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const g = svg
      .attr("width", width)
      .attr("height", height)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Time scale for mahadashas
    const startDate = new Date(dasha.mahadashas[0]?.start_date ?? now);
    const endDate = new Date(
      dasha.mahadashas[dasha.mahadashas.length - 1]?.end_date ?? now,
    );

    const xScale = d3.scaleTime()
      .domain([startDate, endDate])
      .range([0, innerWidth]);

    // Mahadasha band (top row)
    const mdHeight = innerHeight * 0.4;
    const adHeight = innerHeight * 0.3;
    const prHeight = innerHeight * 0.25;

    // ── Mahadasha blocks ──
    dasha.mahadashas.forEach((md) => {
      const x = xScale(new Date(md.start_date));
      const w = Math.max(2, xScale(new Date(md.end_date)) - x);
      const isCurrent =
        currentPeriod &&
        currentTime >= new Date(md.start_date).getTime() &&
        currentTime <= new Date(md.end_date).getTime();

      const block = g.append("g")
        .attr("role", "button")
        .attr("tabindex", 0)
        .attr("aria-label", `${md.lord} Mahadasha: ${formatDate(md.start_date)} to ${formatDate(md.end_date)} (${md.duration_days} days)${isCurrent ? " — current period" : ""}`)
        .style("cursor", "pointer");

      block.append("rect")
        .attr("x", x)
        .attr("y", 0)
        .attr("width", w)
        .attr("height", mdHeight)
        .attr("rx", 3)
        .attr("fill", isCurrent ? "#fbbf24" : "rgba(251,191,36,0.15)")
        .attr("stroke", isCurrent ? "#fbbf24" : "rgba(251,191,36,0.3)")
        .attr("stroke-width", isCurrent ? 2 : 1);

      // Lord label
      if (w > 40) {
        const abbrev = PLANET_ABBREV[md.lord] ?? md.lord.slice(0, 2);
        const symbol = PLANET_SYMBOLS[md.lord] ?? "";
        block.append("text")
          .attr("x", x + w / 2)
          .attr("y", mdHeight / 2 - 2)
          .attr("text-anchor", "middle")
          .attr("dominant-baseline", "central")
          .style("font-size", "10px")
          .style("font-weight", "bold")
          .style("fill", isCurrent ? "#060620" : "#fbbf24")
          .text(symbol + " " + abbrev);

        // Date range
        if (w > 80) {
          block.append("text")
            .attr("x", x + w / 2)
            .attr("y", mdHeight / 2 + 10)
            .attr("text-anchor", "middle")
            .style("font-size", "7px")
            .style("fill", isCurrent ? "#060620" : "rgba(251,191,36,0.6)")
            .text(formatDate(md.start_date));
        }
      }

      // Click handler
      block.on("click", () => {
        setSelectedPeriod(md);
        setCountdownTarget(md.end_date);
      });

      block.on("keydown", (event: KeyboardEvent) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          setSelectedPeriod(md);
          setCountdownTarget(md.end_date);
        }
      });
    });

    // ── Antardasha blocks (within each Mahadasha) ──
    dasha.mahadashas.forEach((md) => {
      const mdX = xScale(new Date(md.start_date));
      const mdW = xScale(new Date(md.end_date)) - mdX;

      md.children.forEach((ad) => {
        const adX = xScale(new Date(ad.start_date));
        const adW = Math.max(1, xScale(new Date(ad.end_date)) - adX);
        const isCurrentAD =
          currentTime >= new Date(ad.start_date).getTime() &&
          currentTime <= new Date(ad.end_date).getTime();

        g.append("rect")
          .attr("x", adX)
          .attr("y", mdHeight + 4)
          .attr("width", adW)
          .attr("height", adHeight)
          .attr("rx", 2)
          .attr("fill", isCurrentAD ? "#a78bfa" : "rgba(167,139,250,0.12)")
          .attr("stroke", isCurrentAD ? "#a78bfa" : "rgba(167,139,250,0.2)")
          .attr("stroke-width", isCurrentAD ? 1.5 : 0.5)
          .style("cursor", "pointer")
          .on("click", () => {
            setSelectedPeriod(ad);
            setCountdownTarget(ad.end_date);
          });

        if (adW > 30) {
          g.append("text")
            .attr("x", adX + adW / 2)
            .attr("y", mdHeight + 4 + adHeight / 2)
            .attr("text-anchor", "middle")
            .attr("dominant-baseline", "central")
            .style("font-size", "8px")
            .style("fill", isCurrentAD ? "#060620" : "#a78bfa")
            .text(PLANET_ABBREV[ad.lord] ?? ad.lord.slice(0, 2));
        }

        // Pratyantar dasha blocks
        ad.children.forEach((pd) => {
          const pdX = xScale(new Date(pd.start_date));
          const pdW = Math.max(1, xScale(new Date(pd.end_date)) - pdX);
          const isCurrentPD =
            currentTime >= new Date(pd.start_date).getTime() &&
            currentTime <= new Date(pd.end_date).getTime();

          g.append("rect")
            .attr("x", pdX)
            .attr("y", mdHeight + adHeight + 8)
            .attr("width", pdW)
            .attr("height", prHeight)
            .attr("rx", 1)
            .attr("fill", isCurrentPD ? "#34d399" : "rgba(52,211,153,0.08)")
            .attr("stroke", isCurrentPD ? "#34d399" : "rgba(52,211,153,0.15)")
            .attr("stroke-width", isCurrentPD ? 1 : 0.5)
            .style("cursor", "pointer")
            .on("click", () => {
              setSelectedPeriod(pd);
              setCountdownTarget(pd.end_date);
            });

          if (pdW > 20) {
            g.append("text")
              .attr("x", pdX + pdW / 2)
              .attr("y", mdHeight + adHeight + 8 + prHeight / 2)
              .attr("text-anchor", "middle")
              .attr("dominant-baseline", "central")
              .style("font-size", "7px")
              .style("fill", isCurrentPD ? "#060620" : "#34d399")
              .text(PLANET_ABBREV[pd.lord]?.slice(0, 1) ?? "");
          }
        });
      });
    });

    // ── Current time indicator line ──
    const nowX = xScale(now);
    if (nowX >= 0 && nowX <= innerWidth) {
      g.append("line")
        .attr("x1", nowX)
        .attr("y1", -5)
        .attr("x2", nowX)
        .attr("y2", innerHeight + 5)
        .attr("stroke", "#ef4444")
        .attr("stroke-width", 2)
        .attr("stroke-dasharray", "4,3");

      g.append("text")
        .attr("x", nowX)
        .attr("y", -8)
        .attr("text-anchor", "middle")
        .style("font-size", "8px")
        .style("font-weight", "bold")
        .style("fill", "#ef4444")
        .text("NOW");
    }

    // ── Time axis ──
    const timeFormatter = d3.timeFormat("%Y");
    const xAxis = d3.axisBottom(xScale)
      .ticks(d3.timeYear.every(5))
      .tickFormat((d) => timeFormatter(d as Date));

    const axisGroup = g.append("g")
      .attr("transform", `translate(0,${innerHeight})`);
    xAxis(axisGroup as unknown as d3.Selection<SVGGElement, unknown, SVGGElement, unknown>);
    axisGroup.selectAll("text")
      .style("font-size", "9px")
      .style("fill", "var(--text-secondary)");

    g.selectAll(".domain").style("stroke", "var(--border-primary)");
    g.selectAll(".tick line").style("stroke", "var(--border-primary)");

  }, [dasha, containerWidth, height, currentPeriod, currentTime, now]);

  return (
    <div
      className="glass-card p-5 space-y-4"
      role="region"
      aria-label={`Dasha timeline for ${dasha.system} system`}
    >
      <div className="flex items-center justify-between">
        <div>
          <h3
            className="text-sm font-semibold uppercase tracking-wide"
            style={{ color: "var(--accent)" }}
          >
            {dasha.system} Dasha Timeline
          </h3>
          <p className="mt-0.5 text-xs" style={{ color: "var(--text-muted)" }}>
            Trigger: {dasha.trigger_planet} in {dasha.trigger_nakshatra} ·{" "}
            {dasha.total_cycle_years} year cycle
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
            Click any period to see details
          </p>
        </div>
      </div>

      {/* Legend */}
      <div
        className="flex flex-wrap gap-3 text-xs"
        role="list"
        aria-label="Timeline legend"
      >
        {Object.entries(LEVEL_COLORS).map(([level, color]) => (
          <span key={level} className="flex items-center gap-1" role="listitem">
            <span
              className="inline-block h-2.5 w-2.5 rounded-sm"
              style={{ backgroundColor: color }}
              aria-hidden="true"
            />
            <span style={{ color: "var(--text-secondary)" }}>
              {LEVEL_NAMES[parseInt(level) - 1]}
            </span>
          </span>
        ))}
        <span className="flex items-center gap-1" role="listitem">
          <span
            className="inline-block h-0.5 w-4 border-l-2 border-dashed"
            style={{ borderColor: "#ef4444" }}
            aria-hidden="true"
          />
          <span style={{ color: "var(--text-secondary)" }}>Now</span>
        </span>
      </div>

      {/* Timeline SVG */}
      <div ref={containerRef} className="overflow-x-auto">
        <svg
          ref={svgRef}
          className="w-full"
          style={{ minWidth: 500 }}
          role="img"
          aria-label={`${dasha.system} Dasha timeline chart showing Mahadasha, Antardasha, and Pratyantar Dasha periods`}
        />
      </div>

      {/* Current period + countdown */}
      {currentPeriod && (
        <div
          className="rounded-lg border p-4"
          style={{
            borderColor: "var(--accent)",
            backgroundColor: "var(--bg-card-hover)",
          }}
          role="status"
          aria-live="polite"
          aria-label={`Current dasha period: ${currentPeriod.lord}, ending ${formatDate(currentPeriod.end_date)}`}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
                Current Period
              </p>
              <p
                className="mt-1 text-lg font-bold"
                style={{ color: "var(--accent)" }}
              >
                {PLANET_SYMBOLS[currentPeriod.lord] ?? ""}{" "}
                {currentPeriod.lord}
              </p>
              <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                {formatDate(currentPeriod.start_date)} —{" "}
                {formatDate(currentPeriod.end_date)}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
                Ends in
              </p>
              <p
                className="mt-1 text-2xl font-bold tabular-nums"
                style={{ color: "var(--text-primary)" }}
              >
                {computeCountdown(currentPeriod.end_date)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Selected period detail */}
      {selectedPeriod && selectedPeriod !== currentPeriod && (
        <div
          className="rounded-lg border p-3"
          style={{
            borderColor: "var(--border-primary)",
            backgroundColor: "var(--bg-card)",
          }}
          role="region"
          aria-label={`Selected period: ${selectedPeriod.lord}`}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
                {LEVEL_NAMES[selectedPeriod.level - 1] ?? `Level ${selectedPeriod.level}`}
              </p>
              <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                {PLANET_SYMBOLS[selectedPeriod.lord] ?? ""} {selectedPeriod.lord}
              </p>
              <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                {formatDate(selectedPeriod.start_date)} —{" "}
                {formatDate(selectedPeriod.end_date)}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                {selectedPeriod.duration_days} days
              </p>
              <p className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>
                {computeCountdown(selectedPeriod.end_date)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Next period preview */}
      {nextPeriod && (
        <div
          className="rounded border p-2"
          style={{
            borderColor: "var(--border-primary)",
            backgroundColor: "var(--bg-card)",
          }}
        >
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            Next:{" "}
            <span style={{ color: "var(--text-secondary)" }}>
              {PLANET_SYMBOLS[nextPeriod.lord] ?? ""} {nextPeriod.lord}
            </span>{" "}
            starts {formatDate(nextPeriod.start_date)} ({computeCountdown(nextPeriod.start_date)})
          </p>
        </div>
      )}
    </div>
  );
}
