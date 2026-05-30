"use client";

import { usePipelineStore } from "@/store/pipeline-store";

export function Orchestration() {
  const pipelines = usePipelineStore((s) => s.pipelines);
  const running = pipelines.filter((p) => p.status === "running");

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-border bg-card/30 p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-foreground">Orchestration</h3>
          <span className="rounded-full bg-blue-500/10 px-2.5 py-0.5 text-[10px] font-medium text-blue-300">
            {running.length} active
          </span>
        </div>
        <p className="text-xs text-muted-foreground">
          Manage concurrent pipeline executions and provider routing.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-border bg-card/30 p-4">
          <span className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground/60">Active</span>
          <p className="mt-1 text-2xl font-bold text-foreground">{running.length}</p>
        </div>
        <div className="rounded-xl border border-border bg-card/30 p-4">
          <span className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground/60">Max Concurrent</span>
          <p className="mt-1 text-2xl font-bold text-foreground">2</p>
        </div>
        <div className="rounded-xl border border-border bg-card/30 p-4">
          <span className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground/60">Queue</span>
          <p className="mt-1 text-2xl font-bold text-muted-foreground">{Math.max(0, pipelines.length - 2)}</p>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card/30 p-4">
        <h4 className="text-xs font-semibold text-foreground mb-3">Provider Failover Chain</h4>
        <div className="flex items-center gap-2 text-[11px]">
          <span className="rounded bg-emerald-500/10 px-2 py-1 text-emerald-300">OpenAI</span>
          <span className="text-muted-foreground">→</span>
          <span className="rounded bg-blue-500/10 px-2 py-1 text-blue-300">Groq</span>
          <span className="text-muted-foreground">→</span>
          <span className="rounded bg-slate-500/10 px-2 py-1 text-slate-300">Ollama</span>
        </div>
      </div>
    </div>
  );
}
