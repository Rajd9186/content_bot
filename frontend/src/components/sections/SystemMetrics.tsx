"use client";

import { usePipelineStore } from "@/store/pipeline-store";

export function SystemMetrics() {
  const pipelines = usePipelineStore((s) => s.pipelines);
  const totalRuns = pipelines.length;
  const totalTokens = pipelines.reduce((a, p) => a + (p.total_tokens ?? 0), 0);
  const totalDuration = pipelines.reduce((a, p) => a + (p.total_latency ?? 0), 0);

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-border bg-card/30 p-5">
        <h3 className="text-sm font-semibold text-foreground">System Metrics</h3>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-xl border border-border bg-card/30 p-4">
          <span className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground/60">Pipeline Runs</span>
          <p className="mt-1 text-2xl font-bold text-foreground">{totalRuns}</p>
        </div>
        <div className="rounded-xl border border-border bg-card/30 p-4">
          <span className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground/60">Tokens Used</span>
          <p className="mt-1 text-2xl font-bold text-foreground">{(totalTokens / 1000).toFixed(0)}k</p>
        </div>
        <div className="rounded-xl border border-border bg-card/30 p-4">
          <span className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground/60">Avg Time</span>
          <p className="mt-1 text-2xl font-bold text-foreground">
            {totalRuns > 0 ? `${Math.round(totalDuration / totalRuns / 1000)}s` : "N/A"}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card/30 p-4">
          <span className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground/60">Uptime</span>
          <p className="mt-1 text-2xl font-bold text-emerald-400">99.9%</p>
        </div>
      </div>
    </div>
  );
}
