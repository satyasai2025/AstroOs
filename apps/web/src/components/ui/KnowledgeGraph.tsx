"use client";

export interface GraphNode {
  id: string;
  x: number;
  y: number;
  label: string;
  size?: number;
  color?: string;
}

export interface GraphEdge {
  from: string;
  to: string;
}

interface KnowledgeGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  width?: number;
  height?: number;
  activeId?: string;
  onSelectNode?: (id: string) => void;
}

export function KnowledgeGraph({ nodes = [], edges = [], width = 480, height = 320, activeId, onSelectNode }: KnowledgeGraphProps) {
  const byId = Object.fromEntries(nodes.map((n) => [n.id, n]));
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ overflow: "visible" }}>
      <defs>
        <radialGradient id="kg-bg" cx="50%" cy="40%" r="70%">
          <stop offset="0%" stopColor="rgba(139,92,246,0.08)" />
          <stop offset="100%" stopColor="transparent" />
        </radialGradient>
      </defs>
      <rect x="0" y="0" width={width} height={height} fill="url(#kg-bg)" />
      {edges.map((e, i) => {
        const a = byId[e.from];
        const b = byId[e.to];
        if (!a || !b) return null;
        return <line key={i} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="var(--border-strong)" strokeWidth="1.5" />;
      })}
      {nodes.map((n) => {
        const active = n.id === activeId;
        const r = n.size || 20;
        const color = n.color || "var(--cyan-400)";
        return (
          <g key={n.id} onClick={() => onSelectNode && onSelectNode(n.id)} style={{ cursor: "pointer" }}>
            <circle cx={n.x} cy={n.y} r={active ? r + 5 : r} fill={color} fillOpacity={active ? 0.28 : 0.16} stroke={color} strokeWidth={active ? 2 : 1.4} />
            <circle cx={n.x} cy={n.y} r={4} fill={color} />
            <text x={n.x} y={n.y + r + 16} textAnchor="middle" fontSize="12" fontFamily="var(--font-body)" fill={active ? "var(--text-primary)" : "var(--text-secondary)"}>
              {n.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
