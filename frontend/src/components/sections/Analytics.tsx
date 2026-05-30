"use client";

import { usePipelineStore } from "@/store/pipeline-store";
import { StatsGrid } from "@/components/analytics";
import type { AnalyticsSummary } from "@/types/api";

export function Analytics() {
  const pipelines = usePipelineStore((s) => s.pipelines);
  const completed = pipelines.filter((p) => p.status === "completed");
  const failed = pipelines.filter((p) => p.status === "failed");

  const summary: AnalyticsSummary = {
    totalPipelines: pipelines.length,
    successRate: pipelines.length > 0 ? completed.length / pipelines.length : 0,
    avgExecutionTimeMs: completed.reduce((a, p) => a + (p.total_latency ?? 0), 0) / (completed.length || 1),
    totalTokens: pipelines.reduce((a, p) => a + (p.total_tokens ?? 0), 0),
    costEstimate: 0,
  };

  return (
    <div className="space-y-4">
      <StatsGrid data={summary} />
      <div className="rounded-xl border border-border bg-card/30 p-4">
        <h3 className="mb-3 text-xs font-semibold text-foreground">Completion Rate</h3>
        <div className="flex items-center gap-4">
          <div className="h-20 w-20 rounded-full border-4 border-emerald-500/30 flex items-center justify-center">
            <span className="text-lg font-bold text-emerald-400">{Math.round(summary.successRate * 100)}%</span>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-xs">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              <span className="text-muted-foreground">Completed: {completed.length}</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className="h-2 w-2 rounded-full bg-red-400" />
              <span className="text-muted-foreground">Failed: {failed.length}</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className="h-2 w-2 rounded-full bg-slate-500" />
              <span className="text-muted-foreground">Total: {pipelines.length}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
