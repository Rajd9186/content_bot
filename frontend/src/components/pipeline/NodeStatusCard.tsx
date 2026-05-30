"use client";

import { cn } from "@/lib/utils";
import { usePipelineStore } from "@/store/pipeline-store";
import { PIPELINE_STAGES } from "@/lib/constants";

const STAGE_LABELS: Record<string, string> = {
  research: "Research",
  planner: "Planner",
  writer: "Writer",
  seo: "SEO",
  fact_checker: "Fact Checker",
  compliance: "Compliance",
  human_review: "Review",
  finalizer: "Finalizer",
};

export function NodeStatusCard() {
  const events = usePipelineStore((s) => s.events);

  const stages = Array.from(PIPELINE_STAGES).map((stage) => {
    const event = events.find((e) => e.node === stage);
    return {
      id: stage,
      label: STAGE_LABELS[stage] ?? stage,
      status: event?.type ?? "pending",
      duration: event?.latency_ms,
    };
  });

  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
      {stages.map((stage) => (
        <div
          key={stage.id}
          className={cn(
            "rounded-lg border p-3 transition-all duration-300",
            stage.status === "node_completed" ? "border-emerald-500/30 bg-emerald-500/5" :
            stage.status === "node_running" ? "border-blue-500/30 bg-blue-500/5" :
            stage.status === "node_failed" ? "border-red-500/30 bg-red-500/5" :
            "border-border bg-black/20",
          )}
        >
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "h-2 w-2 rounded-full",
                stage.status === "node_completed" ? "bg-emerald-400" :
                stage.status === "node_running" ? "bg-blue-400 animate-pulse-soft" :
                stage.status === "node_failed" ? "bg-red-400" :
                "bg-slate-500",
              )}
            />
            <span className="text-[10px] font-medium text-foreground">{stage.label}</span>
          </div>
          {stage.duration != null && (
            <p className="mt-1 text-[10px] text-muted-foreground">{(stage.duration / 1000).toFixed(1)}s</p>
          )}
        </div>
      ))}
    </div>
  );
}
