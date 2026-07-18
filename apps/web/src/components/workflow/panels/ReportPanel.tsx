import type { BenchmarkResponse, ChartReportResponse } from "@/lib/types";

export function ReportPanel({
  report,
  benchmark,
}: {
  report: ChartReportResponse;
  benchmark: BenchmarkResponse;
}) {
  return (
    <div className="space-y-6">
      <div className="glass-card p-5">
        <h3 className="mb-1 text-sm font-semibold uppercase tracking-wide text-amber-300/80">
          {report.title}
        </h3>
        <p className="mb-4 text-xs text-slate-500">
          Subject: {report.subject_name} · Generated{" "}
          {new Date(report.metadata.generated_at).toUTCString()}
        </p>

        <div className="space-y-4">
          {[...report.sections]
            .sort((a, b) => a.order - b.order)
            .map((section) => (
              <div key={section.section_type} className="border-t border-white/5 pt-4 first:border-none first:pt-0">
                <h4 className="mb-2 text-sm font-medium text-slate-100">{section.title}</h4>
                <pre className="overflow-x-auto whitespace-pre-wrap break-words text-xs text-slate-400">
                  {JSON.stringify(section.data, null, 2)}
                </pre>
              </div>
            ))}
        </div>
      </div>

      <div className={`glass-card p-5 ${
        benchmark.status === "passed" ? "border-emerald-500/30" :
        benchmark.status === "failed" ? "border-red-500/30" :
        "border-dashed"
      }`}>
        <h3 className="mb-1 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Benchmark Validation
        </h3>

        {benchmark.status === "not_applicable" ? (
          <p className="text-sm text-slate-400">{benchmark.detail}</p>
        ) : (
          <div className="space-y-3 text-sm">
            <div className="flex items-center gap-2">
              <span className={`inline-block h-2 w-2 rounded-full ${
                benchmark.status === "passed" ? "bg-emerald-400" : "bg-red-400"
              }`} />
              <span className={benchmark.status === "passed" ? "text-emerald-300" : "text-red-300"}>
                {benchmark.status.toUpperCase()}
              </span>
              <span className="text-xs text-slate-500">
                vs {benchmark.reference_name} ({benchmark.reference_id})
              </span>
            </div>
            <div className="grid grid-cols-3 gap-4 text-xs">
              <div>
                <span className="text-slate-500">Mean Error</span>
                <p className="text-slate-200">{benchmark.mean_error}°</p>
              </div>
              <div>
                <span className="text-slate-500">Max Error</span>
                <p className="text-slate-200">{benchmark.max_error}°</p>
              </div>
              <div>
                <span className="text-slate-500">Tolerance</span>
                <p className="text-slate-200">±{benchmark.tolerance}°</p>
              </div>
            </div>
            {benchmark.planets.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-slate-500">
                      <th className="text-left py-1 pr-2">Planet</th>
                      <th className="text-right px-2">Computed</th>
                      <th className="text-right px-2">Expected</th>
                      <th className="text-right px-2">Error</th>
                      <th className="text-right pl-2">OK</th>
                    </tr>
                  </thead>
                  <tbody>
                    {benchmark.planets.map((p) => (
                      <tr key={p.planet} className="border-t border-white/5">
                        <td className="py-1 pr-2 text-slate-300">{p.planet}</td>
                        <td className="text-right px-2 text-slate-400">{p.computed_longitude.toFixed(2)}°</td>
                        <td className="text-right px-2 text-slate-400">{p.expected_longitude.toFixed(2)}°</td>
                        <td className={`text-right px-2 ${p.within_tolerance ? "text-emerald-400" : "text-red-400"}`}>
                          {p.error_degrees.toFixed(4)}°
                        </td>
                        <td className="text-right pl-2">{p.within_tolerance ? "✓" : "✗"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
