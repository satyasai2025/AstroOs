function linePath(points: number[], w: number, h: number, max: number): string {
  return points.map((p, i) => `${i === 0 ? "M" : "L"} ${(i / (points.length - 1)) * w} ${h - (p / max) * h}`).join(" ");
}

interface LineChartProps {
  data: number[];
  color?: string;
  height?: number;
  label?: string;
}

export function LineChart({ data = [], color = "var(--cyan-400)", height = 160, label }: LineChartProps) {
  const max = Math.max(...data, 1) * 1.15;
  const w = 480;
  const path = linePath(data, w, height, max);
  const areaPath = `${path} L ${w} ${height} L 0 ${height} Z`;
  const gid = "lc-" + data.length + "-" + Math.round(max);
  return (
    <div>
      {label && <div style={{ fontSize: "var(--text-sm)", color: "var(--text-secondary)", marginBottom: 8, fontWeight: "var(--weight-medium)" }}>{label}</div>}
      <svg viewBox={`0 0 ${w} ${height}`} width="100%" height={height} preserveAspectRatio="none">
        <defs>
          <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.35" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={areaPath} fill={`url(#${gid})`} stroke="none" />
        <path d={path} fill="none" stroke={color} strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
      </svg>
    </div>
  );
}

interface BarDatum {
  value: number;
  label: string;
}

interface BarChartProps {
  data: BarDatum[];
  color?: string;
  height?: number;
  label?: string;
}

export function BarChart({ data = [], color = "var(--violet-400)", height = 160, label }: BarChartProps) {
  const max = Math.max(...data.map((d) => d.value), 1) * 1.15;
  return (
    <div>
      {label && <div style={{ fontSize: "var(--text-sm)", color: "var(--text-secondary)", marginBottom: 8, fontWeight: "var(--weight-medium)" }}>{label}</div>}
      <div style={{ display: "flex", alignItems: "flex-end", gap: 10, height }}>
        {data.map((d, i) => (
          <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 6, height: "100%", justifyContent: "flex-end" }}>
            <div
              style={{
                width: "100%",
                height: `${(d.value / max) * 100}%`,
                borderRadius: "6px 6px 2px 2px",
                background: `linear-gradient(180deg, ${color}, transparent 150%)`,
                boxShadow: `0 0 12px ${color}55`,
                minHeight: 4,
              }}
            />
            <span style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)" }}>{d.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

interface RadarDatum {
  value: number;
  label: string;
}

interface RadarChartProps {
  data: RadarDatum[];
  color?: string;
  size?: number;
}

export function RadarChart({ data = [], color = "var(--violet-400)", size = 200 }: RadarChartProps) {
  const c = size / 2;
  const r = size / 2 - 28;
  const n = data.length;
  const max = 100;
  const pt = (i: number, val: number): [number, number] => {
    const ang = (Math.PI * 2 * i) / n - Math.PI / 2;
    const rad = (val / max) * r;
    return [c + rad * Math.cos(ang), c + rad * Math.sin(ang)];
  };
  const poly = data.map((d, i) => pt(i, d.value).join(",")).join(" ");
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {[0.25, 0.5, 0.75, 1].map((f) => (
        <polygon key={f} points={data.map((_, i) => pt(i, max * f).join(",")).join(" ")} fill="none" stroke="var(--border-default)" strokeWidth="1" />
      ))}
      {data.map((_, i) => {
        const [x, y] = pt(i, max);
        return <line key={i} x1={c} y1={c} x2={x} y2={y} stroke="var(--border-default)" strokeWidth="1" />;
      })}
      <polygon points={poly} fill={color} fillOpacity="0.2" stroke={color} strokeWidth="2" />
      {data.map((d, i) => {
        const [x, y] = pt(i, max + 14);
        return (
          <text key={i} x={x} y={y} textAnchor="middle" fontSize="11" fontFamily="var(--font-mono)" fill="var(--text-tertiary)">
            {d.label}
          </text>
        );
      })}
    </svg>
  );
}

interface DonutSegment {
  value: number;
  color: string;
}

interface DonutChartProps {
  segments: DonutSegment[];
  size?: number;
  thickness?: number;
}

export function DonutChart({ segments = [], size = 140, thickness = 18 }: DonutChartProps) {
  const total = segments.reduce((s, x) => s + x.value, 0) || 1;
  const r = (size - thickness) / 2;
  const c = 2 * Math.PI * r;
  let offset = 0;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <g transform={`rotate(-90 ${size / 2} ${size / 2})`}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--border-subtle)" strokeWidth={thickness} />
        {segments.map((s, i) => {
          const len = (s.value / total) * c;
          const el = (
            <circle
              key={i}
              cx={size / 2}
              cy={size / 2}
              r={r}
              fill="none"
              stroke={s.color}
              strokeWidth={thickness}
              strokeDasharray={`${len} ${c - len}`}
              strokeDashoffset={-offset}
              strokeLinecap="butt"
            />
          );
          offset += len;
          return el;
        })}
      </g>
    </svg>
  );
}
