"use client";

import { useEffect, useState, useRef } from "react";
import {
  Activity, AlertCircle, BookOpen, Brain, Bot, CheckCircle2,
  ChevronDown, Cpu, FileOutput, RefreshCw, Search, Sparkles,
  Trash2, TrendingUp, X, Zap
} from "lucide-react";
import { cn } from "@/lib/utils";
import { usePipelineStore } from "@/store/pipeline-store";
import { useProjectStore } from "@/store/project-store";

interface FeedEvent {
  id: string;
  type: string;
  icon: React.ReactNode;
  title: string;
  description: string;
  timestamp: Date;
  severity: "info" | "success" | "warning" | "error";
}

const EVENT_CONFIG: Record<string, { icon: React.ElementType; color: string; severity: FeedEvent["severity"] }> = {
  research: { icon: Search, color: "text-blue-400", severity: "info" },
  memory_retrieved: { icon: Brain, color: "text-violet-400", severity: "info" },
  skill_applied: { icon: Sparkles, color: "text-amber-400", severity: "info" },
  output_generated: { icon: FileOutput, color: "text-emerald-400", severity: "success" },
  compliance: { icon: CheckCircle2, color: "text-emerald-400", severity: "success" },
  provider_failover: { icon: RefreshCw, color: "text-red-400", severity: "warning" },
  agent_retry: { icon: RefreshCw, color: "text-amber-400", severity: "warning" },
  pipeline_failed: { icon: AlertCircle, color: "text-red-400", severity: "error" },
  pipeline_completed: { icon: CheckCircle2, color: "text-emerald-400", severity: "success" },
  memory_pinned: { icon: Brain, color: "text-yellow-400", severity: "info" },
  fact_check: { icon: CheckCircle2, color: "text-emerald-400", severity: "success" },
  llm_request: { icon: Cpu, color: "text-blue-400", severity: "info" },
};

function buildFeedEvents(pipelineEvents: any[], projectEvents: any[] = []): FeedEvent[] {
  const events: FeedEvent[] = [];

  for (const event of pipelineEvents) {
    const node = event.node || "";
    const type = event.type || "";
    let title = "";
    let description = "";

    switch (type) {
      case "node_started":
        title = `${node.replace(/_/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase())} started`;
        description = `Agent began processing`;
        break;
      case "node_completed":
        title = `${node.replace(/_/g, " ")} completed`;
        description = `${(event.latency_ms || 0) < 1000 ? event.latency_ms + "ms" : (event.latency_ms / 1000).toFixed(1) + "s"}${event.tokens_used ? ` · ${event.tokens_used.toLocaleString()} tokens` : ""}`;
        break;
      case "node_failed":
        title = `${node} failed`;
        description = event.error || "Unknown error";
        break;
      case "pipeline_completed":
        title = "Pipeline completed";
        description = "All stages finished successfully";
        break;
      case "pipeline_failed":
        title = "Pipeline failed";
        description = event.error || "Pipeline encountered an error";
        break;
      default:
        continue;
    }

    const config = EVENT_CONFIG[type] || EVENT_CONFIG[node] || { icon: Activity, color: "text-muted-foreground", severity: "info" as const };
    const Icon = config.icon;

    events.push({
      id: `${type}-${node}-${Math.random()}`,
      type,
      icon: <Icon className="h-3.5 w-3.5" />,
      title,
      description,
      timestamp: new Date(),
      severity: config.severity,
    });
  }

  return events.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
}

interface ActivityFeedProps {
  maxItems?: number;
  autoRefresh?: boolean;
  compact?: boolean;
}

export function ActivityFeed({ maxItems = 50, autoRefresh = true, compact = false }: ActivityFeedProps) {
  const pipelineEvents = usePipelineStore((s) => s.events);
  const projects = useProjectStore((s) => s.projects);
  const [events, setEvents] = useState<FeedEvent[]>([]);
  const [filter, setFilter] = useState<"all" | "success" | "warning" | "error">("all");
  const [expanded, setExpanded] = useState(!compact);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const newEvents = buildFeedEvents(pipelineEvents);
    setEvents(newEvents);
  }, [pipelineEvents]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      const newEvents = buildFeedEvents(pipelineEvents);
      setEvents(newEvents);
    }, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh, pipelineEvents]);

  useEffect(() => {
    if (expanded && containerRef.current) {
      containerRef.current.scrollTop = 0;
    }
  }, [expanded]);

  const filteredEvents = events.filter((e) => filter === "all" || e.severity === filter);
  const displayEvents = filteredEvents.slice(0, maxItems);

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    if (diff < 60000) return "Just now";
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  };

  const getSeverityDot = (severity: FeedEvent["severity"]) => {
    switch (severity) {
      case "success": return "bg-emerald-400";
      case "warning": return "bg-amber-400";
      case "error": return "bg-red-400";
      default: return "bg-violet-400";
    }
  };

  if (!expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        <span className={cn("h-2 w-2 rounded-full", events.length > 0 ? "bg-violet-400 animate-pulse" : "bg-slate-500")} />
        Activity Feed
        <ChevronDown className="h-3 w-3" />
      </button>
    );
  }

  return (
    <div className={cn(
      "rounded-2xl border border-border bg-card/60 backdrop-blur-xl overflow-hidden",
      compact ? "p-3" : "p-4"
    )}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={cn(
            "h-2 w-2 rounded-full",
            events.length > 0 ? "bg-violet-400 animate-pulse" : "bg-slate-500"
          )} />
          <h3 className="text-xs font-semibold text-foreground">Activity Feed</h3>
          {events.length > 0 && (
            <span className="text-[9px] text-muted-foreground">{events.length} events</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {filter !== "all" && (
            <button onClick={() => setFilter("all")} className="text-[9px] text-violet-400 hover:text-violet-300">
              Clear
            </button>
          )}
          <button
            onClick={() => setExpanded(false)}
            className="flex h-6 w-6 items-center justify-center rounded-lg hover:bg-secondary transition-colors"
          >
            <X className="h-3 w-3 text-muted-foreground" />
          </button>
        </div>
      </div>

      <div className="flex gap-1 mb-3 overflow-x-auto scrollbar-thin">
        {(["all", "success", "warning", "error"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={cn(
              "px-2 py-1 rounded-lg text-[10px] font-medium whitespace-nowrap transition-colors capitalize",
              filter === f
                ? f === "success" ? "bg-emerald-500/10 text-emerald-400" :
                  f === "warning" ? "bg-amber-500/10 text-amber-400" :
                  f === "error" ? "bg-red-500/10 text-red-400" :
                  "bg-violet-500/10 text-violet-400"
                : "text-muted-foreground hover:text-foreground bg-secondary/40"
            )}
          >
            {f}
          </button>
        ))}
      </div>

      <div ref={containerRef} className={cn("space-y-1.5 overflow-y-auto", compact ? "max-h-[300px]" : "max-h-[500px]")}>
        {displayEvents.length === 0 ? (
          <div className="text-center py-8">
            <Activity className="h-8 w-8 text-muted-foreground/20 mx-auto mb-2" />
            <p className="text-[11px] text-muted-foreground">
              {filter !== "all" ? "No events match filter" : "No activity yet — run a pipeline"}
            </p>
          </div>
        ) : (
          displayEvents.map((event, i) => (
            <div
              key={event.id}
              className={cn(
                "flex items-start gap-2.5 rounded-xl p-2 transition-all hover:bg-secondary/30",
                event.severity === "error" && "bg-red-500/5",
                event.severity === "warning" && "bg-amber-500/5",
                i === 0 && "animate-slide-up"
              )}
            >
              <div className={cn("flex h-6 w-6 items-center justify-center rounded-lg shrink-0 mt-0.5", {
                  "bg-emerald-500/10": event.severity === "success",
                  "bg-amber-500/10": event.severity === "warning",
                  "bg-red-500/10": event.severity === "error",
                  "bg-violet-500/10": event.severity === "info",
                })}>
                <span className={cn("h-1.5 w-1.5 rounded-full shrink-0", getSeverityDot(event.severity))} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[11px] font-medium text-foreground leading-snug">{event.title}</div>
                {event.description && (
                  <div className="text-[10px] text-muted-foreground leading-snug line-clamp-1 mt-0.5">
                    {event.description}
                  </div>
                )}
              </div>
              <span className="text-[9px] text-muted-foreground shrink-0 font-mono mt-0.5">
                {formatTime(event.timestamp)}
              </span>
            </div>
          ))
        )}
        {events.length > maxItems && (
          <p className="text-[9px] text-muted-foreground text-center py-2">
            +{events.length - maxItems} older events
          </p>
        )}
      </div>
    </div>
  );
}