"use client";

export interface RadarSeries {
  name: string;
  color: string;
  /** One value (0-100) per axis, in the same order as `axes`. */
  values: number[];
}

interface EnhancedRadarChartProps {
  axes: string[];
  series: RadarSeries[];
  size?: number;
}

/** N-axis radar chart plotting 2-4 series on the same axes. Axes are spaced
 * evenly around the full circle (divide by axes.length, not length - 1 —
 * dividing by length - 1 places the first and last axis at the same angle
 * and draws them on top of each other). */
export default function EnhancedRadarChart({ axes, series, size = 300 }: EnhancedRadarChartProps) {
  const center = size / 2;
  const radius = size * 0.27;
  const labelRadius = size * 0.37;
  const numAxes = axes.length;

  const angleFor = (i: number) => (i / numAxes) * Math.PI * 2 - Math.PI / 2;

  const pointFor = (i: number, value: number) => {
    const angle = angleFor(i);
    const r = (Math.max(0, Math.min(100, value)) / 100) * radius;
    return [center + Math.cos(angle) * r, center + Math.sin(angle) * r];
  };

  const seriesPoints = series.map((s) =>
    s.values.map((v, i) => pointFor(i, v)).map((p) => p.join(",")).join(" "),
  );

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Grid rings */}
        {[0.25, 0.5, 0.75, 1].map((frac) => (
          <polygon
            key={frac}
            points={Array.from({ length: numAxes }, (_, i) => {
              const angle = angleFor(i);
              return `${center + Math.cos(angle) * radius * frac},${center + Math.sin(angle) * radius * frac}`;
            }).join(" ")}
            fill="none"
            stroke="var(--border-primary)"
            strokeWidth={1}
          />
        ))}

        {/* Axis lines */}
        {axes.map((_, i) => {
          const angle = angleFor(i);
          return (
            <line
              key={i}
              x1={center}
              y1={center}
              x2={center + Math.cos(angle) * radius}
              y2={center + Math.sin(angle) * radius}
              stroke="var(--border-primary)"
              strokeWidth={1}
            />
          );
        })}

        {/* Data polygons, one per chart */}
        {series.map((s, si) => (
          <polygon
            key={s.name + si}
            points={seriesPoints[si]}
            fill={s.color}
            fillOpacity={0.18}
            stroke={s.color}
            strokeWidth={2}
          />
        ))}

        {/* Axis labels */}
        {axes.map((label, i) => {
          const angle = angleFor(i);
          return (
            <text
              key={label}
              x={center + Math.cos(angle) * labelRadius}
              y={center + Math.sin(angle) * labelRadius}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize={11}
              fill="var(--text-secondary)"
            >
              {label}
            </text>
          );
        })}
      </svg>

      <div className="mt-2 flex flex-wrap justify-center gap-4 text-xs">
        {series.map((s) => (
          <div key={s.name} className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: s.color }} />
            <span style={{ color: "var(--text-secondary)" }}>{s.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
