"use client";

import { usePipelineStore } from "@/store/pipeline-store";
import { ErrorBoundary } from "@/components/common";

export function PipelineList() {
  const pipelines = usePipelineStore((s) => s.pipelines);
  const loading = usePipelineStore((s) => s.loading);
  const error = usePipelineStore((s) => s.error);
  const select = usePipelineStore((s) => s.select);
  const currentId = usePipelineStore((s) => s.currentId);

  if (loading) return <div className="text-xs text-muted-foreground p-4">Loading pipelines...</div>;
  if (error) return <ErrorBoundary error={error} />;

  const displayed = pipelines.slice(0, 10);

  return (
    <div className="space-y-1">
      <h3 className="px-1 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">Recent Pipelines</h3>
      {displayed.map((p) => (
        <button
          key={p.workflow_id}
          onClick={() => select(p.workflow_id)}
          className={`w-full rounded-lg px-3 py-2 text-left text-xs transition-colors ${
            currentId === p.workflow_id
              ? "bg-emerald-500/10 text-emerald-300"
              : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
          }`}
        >
          <div className="font-medium">{p.topic || "Untitled"}</div>
          <div className="mt-0.5 flex items-center gap-2 text-[10px] opacity-60">
            <span className="capitalize">{p.status}</span>
            {p.total_tokens != null && (
              <>
                <span>·</span>
                <span>{(p.total_tokens / 1000).toFixed(0)}k tokens</span>
              </>
            )}
          </div>
        </button>
      ))}
    </div>
  );
}
