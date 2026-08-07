import type { YogaResultResponse } from "@/lib/types";

interface Props {
  result: {
    yogas: {
      results: YogaResultResponse[];
    };
  };
}

export default function YogasPanel({ result }: Props) {
  const yogas = result.yogas?.results ?? [];

  const presentYogas = yogas.filter((y) => y.is_present);
  const absentYogas = yogas.filter((y) => !y.is_present);

  const getStrengthColor = (strength: string) => {
    switch (strength.toLowerCase()) {
      case "full":
        return "var(--status-success)";
      case "partial":
        return "var(--status-warning)";
      case "cancelled":
        return "var(--status-danger)";
      default:
        return "var(--text-muted)";
    }
  };

  return (
    <div className="space-y-6">
      {presentYogas.length > 0 && (
        <div>
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
            Active Yogas ({presentYogas.length})
          </h3>
          <div className="space-y-2">
            {presentYogas.map((yoga) => (
              <div
                key={yoga.yoga_id}
                className="glass-card p-4"
                style={{ borderLeft: `3px solid ${getStrengthColor(yoga.strength)}` }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                      {yoga.name}
                    </h4>
                    <p className="mt-1 text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
                      {yoga.category}
                    </p>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {yoga.involved_planets.map((planet) => (
                        <span
                          key={planet}
                          className="rounded px-2 py-0.5 text-[10px] font-medium"
                          style={{ border: "1px solid var(--border-primary)", color: "var(--text-muted)" }}
                        >
                          {planet}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="ml-4 text-right">
                    {yoga.strength && (
                      <span
                        className="rounded-full px-2 py-1 text-[10px] font-semibold"
                        style={{ color: getStrengthColor(yoga.strength), border: `1px solid ${getStrengthColor(yoga.strength)}` }}
                      >
                        {yoga.strength}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {absentYogas.length > 0 && (
        <div>
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            Other Yogas Checked ({absentYogas.length})
          </h3>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {absentYogas.map((yoga) => (
              <div
                key={yoga.yoga_id}
                className="rounded-lg border p-3 opacity-60"
                style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
              >
                <h4 className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                  {yoga.name}
                </h4>
                <p className="mt-1 text-[10px]" style={{ color: "var(--text-muted)" }}>
                  Not present in this chart
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {yogas.length === 0 && (
        <p className="text-xs" style={{ color: "var(--text-muted)" }}>
          No yogas analyzed for this chart.
        </p>
      )}
    </div>
  );
}
