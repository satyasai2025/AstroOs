interface Props {
  chart: unknown;
  activePlanet: string | null;
}

export default function PlanetExplorerPanel({ chart, activePlanet }: Props) {
  return (
    <div>
      <h2>Planet Explorer Panel</h2>
      {/* Add planet explorer-specific content here */}
    </div>
  );
}