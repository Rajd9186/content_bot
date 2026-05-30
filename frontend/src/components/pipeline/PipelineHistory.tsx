"use client";

import { cn } from "@/lib/utils";
import { usePipelineStore } from "@/store/pipeline-store";
import { formatRelativeTime } from "@/lib/format";
import { ErrorBoundary } from "@/components/common";

export function PipelineHistory() {
  const pipelines = usePipelineStore((s) => s.pipelines);
  const loading = usePipelineStore((s) => s.loading);
  const error = usePipelineStore((s) => s.error);
  const select = usePipelineStore((s) => s.select);

  if (loading) return <div className="text-xs text-muted-foreground p-4">Loading history...</div>;
  if (error) return <ErrorBoundary error={error} />;

  return (
    <div className="space-y-2">
      {pipelines.map((p) => (
        <button
          key={p.workflow_id}
          onClick={() => select(p.workflow_id)}
          className="w-full rounded-xl border border-border bg-card/30 p-4 text-left transition-all hover:border-emerald-500/20 hover:bg-card/50"
        >
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-foreground">{p.topic || "Untitled"}</h4>
            <span
              className={cn(
                "rounded-full px-2 py-0.5 text-[10px] font-medium",
                p.status === "completed" ? "bg-emerald-500/10 text-emerald-300" :
                p.status === "failed" ? "bg-red-500/10 text-red-300" :
                p.status === "running" ? "bg-blue-500/10 text-blue-300" :
                "bg-slate-500/10 text-slate-300",
              )}
            >
              {p.status}
            </span>
          </div>
          <div className="mt-2 flex items-center gap-3 text-[10px] text-muted-foreground">
            <span>{formatRelativeTime(p.created_at)}</span>
            {p.total_tokens != null && <span>· {(p.total_tokens / 1000).toFixed(0)}k tokens</span>}
          </div>
        </button>
      ))}
    </div>
  );
}
