"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { usePipelineStore } from "@/store/pipeline-store";

interface StreamEvent {
  type: string;
  node?: string;
  timestamp: string;
  status?: string;
  latency_ms?: number;
  tokens_used?: number;
  error?: string | null;
  actions?: any[];
}

const NODE_LABELS: Record<string, string> = {
  skill_retrieval: "Skill Retrieval",
  memory_retrieval: "Memory Retrieval",
  research: "Research",
  planner: "Planner",
  source_ranking: "Source Ranking",
  fact_checker: "Fact Check",
  seo: "SEO",
  writer: "Writer",
  compliance: "Compliance",
  review: "Review",
  finalizer: "Final Output",
  human_review: "Human Review",
};

function getEventLabel(event: StreamEvent): string {
  switch (event.type) {
    case "connected": return "Pipeline connected";
    case "node_started": return `${NODE_LABELS[event.node!] ?? event.node} started`;
    case "node_running": return `${NODE_LABELS[event.node!] ?? event.node} running`;
    case "node_completed": return `${NODE_LABELS[event.node!] ?? event.node} completed`;
    case "node_failed": return `${NODE_LABELS[event.node!] ?? event.node} failed`;
    case "pipeline_completed": return "Pipeline completed";
    case "pipeline_failed": return "Pipeline failed";
    case "pipeline_cancelled": return "Pipeline cancelled";
    default: return event.type;
  }
}

function getEventColor(event: StreamEvent): string {
  switch (event.type) {
    case "connected": return "bg-violet-400";
    case "node_completed":
    case "pipeline_completed": return "bg-emerald-400";
    case "node_started":
    case "node_running": return "bg-blue-400 animate-pulse-soft";
    case "node_failed":
    case "pipeline_failed": return "bg-red-400";
    case "pipeline_cancelled": return "bg-amber-400";
    default: return "bg-slate-400";
  }
}

function StreamTimelineItem({ event, isLatest }: { event: StreamEvent; isLatest: boolean }) {
  const label = getEventLabel(event);
  const dotColor = getEventColor(event);

  const formatTime = (ts: string) => {
    try { return new Date(ts).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit" }); }
    catch { return "--:--:--"; }
  };

  const isError = event.type === "node_failed" || event.type === "pipeline_failed";
  const isSuccess = event.type === "node_completed" || event.type === "pipeline_completed";
  const isRunning = event.type === "node_started" || event.type === "node_running";

  return (
    <div
      className={cn(
        "flex items-start gap-3 transition-all duration-300",
        isLatest && "animate-fade-in",
      )}
    >
      <div className="flex flex-col items-center mt-1.5">
        <span className={cn("h-2.5 w-2.5 rounded-full", dotColor)} />
        <div className="mt-0.5 h-6 w-px bg-border" />
      </div>
      <div className="flex-1 min-w-0 pb-2">
        <div className="flex items-baseline justify-between gap-2">
          <span className={cn(
            "text-xs font-medium leading-snug",
            isError && "text-red-400",
            isSuccess && "text-emerald-400",
            isRunning && "text-blue-400",
            !isError && !isSuccess && !isRunning && "text-foreground",
          )}>
            {label}
          </span>
          <span className="text-[9px] text-muted-foreground font-mono flex-shrink-0">
            {formatTime(event.timestamp)}
          </span>
        </div>
        <div className="flex items-center gap-3 mt-0.5">
          {event.latency_ms != null && (
            <span className="text-[10px] text-muted-foreground">
              {event.latency_ms < 1000 ? `${event.latency_ms}ms` : `${(event.latency_ms / 1000).toFixed(1)}s`}
            </span>
          )}
          {event.tokens_used != null && event.tokens_used > 0 && (
            <span className="text-[10px] text-muted-foreground">
              {event.tokens_used.toLocaleString()} tok
            </span>
          )}
          {event.error && (
            <span className="text-[10px] text-red-400 truncate max-w-[150px]">{event.error}</span>
          )}
          {event.status && !event.error && (
            <span className="text-[10px] text-muted-foreground capitalize">{event.status}</span>
          )}
        </div>
        {isLatest && event.actions && event.actions.length > 0 && (
          <div className="mt-1.5 flex flex-wrap gap-1">
            {event.actions.slice(0, 3).map((a: any, i: number) => (
              <span key={i} className="text-[9px] bg-secondary/60 text-muted-foreground px-1.5 py-0.5 rounded">
                {a.action}
              </span>
            ))}
            {event.actions.length > 3 && (
              <span className="text-[9px] text-muted-foreground">+{event.actions.length - 3}</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

interface StreamTimelineProps {
  maxItems?: number;
}

export function StreamTimeline({ maxItems = 50 }: StreamTimelineProps) {
  const events = usePipelineStore((s) => s.events);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [events]);

  const recentEvents = events.slice(-maxItems);

  if (recentEvents.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card/30 p-4">
        <h3 className="mb-3 text-xs font-semibold text-foreground flex items-center gap-2">
          <span className="h-1.5 w-1.5 rounded-full bg-violet-400 animate-pulse" />
          Execution Timeline
        </h3>
        <div className="text-center py-8">
          <div className="h-8 w-8 mx-auto mb-2 rounded-full bg-secondary/60 flex items-center justify-center">
            <span className="text-muted-foreground text-lg">◷</span>
          </div>
          <p className="text-xs text-muted-foreground">Waiting for pipeline events...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-card/30 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold text-foreground flex items-center gap-2">
          <span className={cn(
            "h-1.5 w-1.5 rounded-full",
            events.some((e) => e.type === "pipeline_completed") ? "bg-emerald-400" :
            events.some((e) => e.type === "pipeline_failed") ? "bg-red-400" :
            events.some((e) => e.type === "node_started") ? "bg-blue-400 animate-pulse" :
            "bg-violet-400 animate-pulse",
          )} />
          Execution Timeline
        </h3>
        <span className="text-[10px] text-muted-foreground">{recentEvents.length} events</span>
      </div>

      <div
        ref={containerRef}
        className="max-h-[400px] overflow-y-auto scrollbar-thin pr-1"
      >
        {recentEvents.map((event, i) => (
          <StreamTimelineItem
            key={`${event.type}-${event.node}-${i}`}
            event={event as StreamEvent}
            isLatest={i === recentEvents.length - 1}
          />
        ))}
      </div>

      {events.length > maxItems && (
        <p className="text-[9px] text-muted-foreground text-center mt-2">
          +{events.length - maxItems} older events
        </p>
      )}
    </div>
  );
}