"use client";

import { cn } from "@/lib/utils";
import { usePipelineStore } from "@/store/pipeline-store";

export function PipelineTimeline() {
  const timeline = usePipelineStore((s) => s.timeline);
  const entries = timeline?.timeline ?? [];

  if (!entries.length) {
    return <div className="p-4 text-xs text-muted-foreground">No timeline data available</div>;
  }

  return (
    <div className="space-y-0">
      {entries.map((t, i) => (
        <div key={i} className="relative flex gap-4 pb-6 last:pb-0">
          {i < entries.length - 1 && (
            <div className="absolute left-[7px] top-3 h-full w-px bg-border" />
          )}
          <div className="flex flex-col items-center">
            <div
              className={cn(
                "h-[14px] w-[14px] rounded-full border-2",
                t.status === "completed" ? "border-emerald-400 bg-emerald-400/20" :
                t.status === "running" ? "border-blue-400 bg-blue-400/20 animate-pulse-soft" :
                t.status === "failed" ? "border-red-400 bg-red-400/20" :
                "border-slate-500 bg-slate-500/20",
              )}
            />
          </div>
          <div className="min-w-0 pt-0.5">
            <p className="text-xs font-medium text-foreground">{t.node}</p>
            <p className="text-[10px] text-muted-foreground">
              {t.status}
              {t.latency_ms != null ? ` · ${(t.latency_ms / 1000).toFixed(1)}s` : ""}
            </p>
            {t.error && (
              <p className="mt-1 text-[9px] text-red-400">{t.error}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
