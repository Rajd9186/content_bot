"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { useAgentNodes } from "@/hooks/use-agent-nodes";
import type { AgentAction } from "@/types/api";

const NODE_LABELS: Record<string, string> = {
  research: "Research",
  planner: "Planner",
  writer: "Writer",
  seo: "SEO",
  fact_checker: "Fact Checker",
  compliance: "Compliance",
  human_review: "Review",
  finalizer: "Finalizer",
  skill_retrieval: "Skill Retrieval",
  memory_retrieval: "Memory Retrieval",
};

const ACTION_ICONS: Record<string, string> = {
  agent_start: "▶",
  llm_request: "◈",
  llm_response: "◉",
  parse_output: "◆",
  retry: "↺",
  error: "✕",
  skipped: "⊘",
};

function ActionItem({ action, index }: { action: AgentAction; index: number }) {
  const icon = ACTION_ICONS[action.action] ?? "•";
  const isError = action.action === "error" || action.success === false;
  const isSuccess = action.success === true;

  return (
    <div
      className="flex items-start gap-2.5 animate-fade-in"
      style={{ animationDelay: `${index * 40}ms` }}
    >
      <div
        className={cn(
          "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[9px] font-bold",
          isError ? "bg-red-500/20 text-red-400" :
          isSuccess ? "bg-emerald-500/20 text-emerald-400" :
          "bg-secondary text-muted-foreground",
        )}
      >
        {icon}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline gap-2">
          <span className={cn(
            "text-[11px] font-medium",
            isError ? "text-red-400" :
            isSuccess ? "text-emerald-400" :
            "text-foreground",
          )}>
            {action.action.replace(/_/g, " ")}
          </span>
          {action.timestamp && (
            <span className="text-[9px] text-muted-foreground">
              {new Date(action.timestamp).toLocaleTimeString()}
            </span>
          )}
        </div>
        <p className="mt-0.5 text-[10px] text-muted-foreground leading-relaxed line-clamp-2">
          {action.details}
        </p>
      </div>
    </div>
  );
}

function NodeActivityCard({
  nodeName,
  status,
  latencyMs,
  tokensUsed,
  startedAt,
  completedAt,
  actions,
  error,
}: {
  nodeName: string;
  status: string;
  latencyMs?: number;
  tokensUsed?: number;
  startedAt?: string | null;
  completedAt?: string | null;
  actions: AgentAction[];
  error?: string | null;
}) {
  const [expanded, setExpanded] = useState(false);
  const label = NODE_LABELS[nodeName] ?? nodeName;
  const hasActions = actions.length > 0;

  return (
    <div
      className={cn(
        "rounded-xl border transition-all duration-200",
        status === "success" || status === "completed" ? "border-emerald-500/20 bg-emerald-500/5" :
        status === "failed" ? "border-red-500/20 bg-red-500/5" :
        status === "running" ? "border-blue-500/20 bg-blue-500/5" :
        "border-border bg-secondary/30",
      )}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-3 p-3 text-left"
      >
        <div
          className={cn(
            "h-2 w-2 rounded-full shrink-0",
            status === "success" || status === "completed" ? "bg-emerald-400" :
            status === "failed" ? "bg-red-400" :
            status === "running" ? "bg-blue-400 animate-pulse-soft" :
            "bg-slate-500",
          )}
        />

        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold text-foreground">{label}</p>
          <p className="text-[10px] text-muted-foreground capitalize">{status}</p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          {latencyMs != null && (
            <span className="text-[10px] text-muted-foreground">
              {(latencyMs / 1000).toFixed(1)}s
            </span>
          )}
          {tokensUsed != null && tokensUsed > 0 && (
            <span className="text-[10px] text-muted-foreground">
              {tokensUsed.toLocaleString()} tok
            </span>
          )}
          {hasActions && (
            <span className={cn(
              "text-[10px] font-medium transition-transform duration-200",
              expanded ? "rotate-90 text-violet-400" : "text-muted-foreground",
            )}>
              ▶
            </span>
          )}
        </div>
      </button>

      {error && (
        <div className="px-3 pb-2">
          <p className="text-[10px] text-red-400 rounded bg-red-500/10 px-2 py-1">
            {error}
          </p>
        </div>
      )}

      {expanded && hasActions && (
        <div className="border-t border-border/50 px-3 pb-3 pt-2">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide">
              Agent Activity Log
            </span>
            <span className="text-[10px] text-muted-foreground">
              {actions.length} step{actions.length !== 1 ? "s" : ""}
            </span>
          </div>
          <div className="space-y-2">
            {actions.map((action, i) => (
              <ActionItem key={i} action={action} index={i} />
            ))}
          </div>
          {startedAt && (
            <div className="mt-2 flex items-center gap-3 text-[9px] text-muted-foreground/60 border-t border-border/50 pt-2">
              <span>Started: {new Date(startedAt).toLocaleTimeString()}</span>
              {completedAt && (
                <span>Completed: {new Date(completedAt).toLocaleTimeString()}</span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function AgentActivityPanel() {
  const agentNodes = useAgentNodes();

  if (agentNodes.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card/30 p-4">
        <h3 className="mb-3 text-xs font-semibold text-foreground flex items-center gap-2">
          <span className="h-1.5 w-1.5 rounded-full bg-violet-400" />
          Agent Activities
        </h3>
        <p className="text-[11px] text-muted-foreground">Waiting for agents to start...</p>
      </div>
    );
  }

  const completedCount = agentNodes.filter(
    (a) => a.status === "success" || a.status === "completed",
  ).length;

  return (
    <div className="rounded-xl border border-border bg-card/30 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-xs font-semibold text-foreground flex items-center gap-2">
          <span className={cn(
            "h-1.5 w-1.5 rounded-full animate-pulse-soft",
            completedCount === agentNodes.length ? "bg-emerald-400" : "bg-violet-400",
          )} />
          Agent Activities
        </h3>
        <span className="text-[10px] text-muted-foreground">
          {completedCount}/{agentNodes.length} complete
        </span>
      </div>

      <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1 scrollbar-thin">
        {agentNodes.map((node) => (
          <NodeActivityCard
            key={node.name}
            nodeName={node.name}
            status={node.status}
            latencyMs={node.latency_ms}
            tokensUsed={node.tokens_used}
            startedAt={node.started_at}
            completedAt={node.completed_at}
            actions={node.actions}
            error={node.error}
          />
        ))}
      </div>
    </div>
  );
}