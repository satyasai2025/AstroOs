"use client";

interface OverlapData {
  label: string;
  overlappingPercentage: number;
  overlappingPlanets: string[];
}

type VennSet = {
  label: string;
  set: string[]; // array of planet signs or areas for overlap calculation
  color: string;
};

interface VennDiagramProps {
  leftSet: VennSet;
  rightSet: VennSet;
  overlap: OverlapData;
}

export default function VennDiagram({ leftSet, rightSet, overlap }: VennDiagramProps) {
  const calculateOverlapPercentage = (setA: string[], setB: string[]) => {
    const intersection = new Set(setA.filter(value => setB.includes(value)));
    const union = new Set([...setA, ...setB]);
    return union.size === 0 ? 0 : (intersection.size / union.size) * 100;
  };

  const overlaps = [
    { label: leftSet.label, percentage: calculateOverlapPercentage(leftSet.set, rightSet.set), color: leftSet.color, set: leftSet.set },
    { label: rightSet.label, percentage: calculateOverlapPercentage(rightSet.set, leftSet.set), color: rightSet.color, set: rightSet.set },
  ];

  const vennAreas = [];
  const doubleOverlapWidth = 140;
  const singleWidth = 120;
  const height = 200;

  // Left circle
  vennAreas.push(
    <circle
      key="left-circle"
      cx="100"
      cy="100"
      r="72"
      fill={leftSet.color}
      opacity="0.3"
      stroke={leftSet.color}
      strokeWidth="2"
    />
  );
  // Right circle
  vennAreas.push(
    <circle
      key="right-circle"
      cx="260"
      cy="100"
      r="72"
      fill={rightSet.color}
      opacity="0.3"
      stroke={rightSet.color}
      strokeWidth="2"
    />
  );
  // Overlap area (intersection)
  vennAreas.push(
    <ellipse
      key="overlap-area"
      cx="180"
      cy="100"
      rx="72"
      ry="72"
      fill="#f59e0b"
      opacity="0.4"
      transform="rotate(-20 180 100)"
    />
  );

  return (
    <div className="flex flex-col items-center">
      <svg width="360" height="220" viewBox="0 0 360 220">
        {vennAreas}
        {/* Labels */}
        <text x="100" y="40" textAnchor="middle" fontSize="12" fontWeight="bold" fill={leftSet.color}>
          {leftSet.label}
        </text>
        <text x="260" y="40" textAnchor="middle" fontSize="12" fontWeight="bold" fill={rightSet.color}>
          {rightSet.label}
        </text>
        <text x="180" y="40" textAnchor="middle" fontSize="12" fontWeight="bold" fill="#f59e0b">
          Overlap
        </text>
        {/* Percentages */}
        <text x="60" y="100" textAnchor="middle" fontSize="10" fill={leftSet.color}>
          {overlaps[0].percentage.toFixed(0)}%
        </text>
        <text x="300" y="100" textAnchor="middle" fontSize="10" fill={rightSet.color}>
          {overlaps[1].percentage.toFixed(0)}%
        </text>
        <text x="180" y="100" textAnchor="middle" fontSize="10" fill="#f59e0b">
          {overlap.overlappingPercentage.toFixed(0)}%
        </text>
      </svg>
      {/* Overlapping planets list */}
      <div className="mt-2 text-center">
        <span className="text-xs text-gray-600">
          Shared: {overlap.overlappingPlanets.join(', ') || 'None'}
        </span>
      </div>
    </div>
  );
}
