"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import type { AgentMetrics } from "@/types/api";

interface AgentStatusProps {
  agent: AgentMetrics;
  className?: string;
}

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

const ACTION_LABELS: Record<string, string> = {
  agent_start: "Started",
  llm_request: "LLM Request",
  llm_response: "LLM Response",
  parse_output: "Parsed",
  retry: "Retry",
  error: "Error",
  skipped: "Skipped",
};

export function AgentStatus({ agent, className }: AgentStatusProps) {
  const [expanded, setExpanded] = useState(false);

  const label = NODE_LABELS[agent.name] ?? agent.name;
  const isSuccess = agent.status === "success" || agent.status === "completed";
  const isFailed = agent.status === "failed" || agent.status === "error";
  const isRunning = agent.status === "running";
  const ok = agent.successRate > 0.8;

  return (
    <div
      className={cn(
        "rounded-2xl border transition-all duration-200 card-hover",
        isSuccess ? "border-emerald-500/20 bg-emerald-500/5" :
        isFailed ? "border-red-500/20 bg-red-500/5" :
        isRunning ? "border-blue-500/20 bg-blue-500/5" :
        "border-border bg-card/30",
        className,
      )}
    >
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center gap-2.5">
          <span
            className={cn(
              "h-2.5 w-2.5 rounded-full shrink-0",
              isSuccess ? "bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.4)]" :
              isFailed ? "bg-red-400 shadow-[0_0_8px_rgba(239,68,68,0.4)]" :
              isRunning ? "bg-blue-400 animate-pulse-soft shadow-[0_0_8px_rgba(59,130,246,0.4)]" :
              "bg-slate-500",
            )}
          />
          <div>
            <span className="text-xs font-bold text-foreground">{label}</span>
            {agent.provider && (
              <span className="ml-2 text-[10px] text-muted-foreground">{agent.provider}</span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {agent.model && (
            <span className="hidden sm:inline text-[10px] text-muted-foreground bg-secondary px-1.5 py-0.5 rounded">
              {agent.model}
            </span>
          )}
          {agent.actions_count != null && agent.actions_count > 0 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-[10px] text-violet-400 hover:text-violet-300 transition-colors"
            >
              {agent.actions_count} steps {expanded ? "▲" : "▼"}
            </button>
          )}
        </div>
      </div>

      <div className="px-4 pb-3 grid grid-cols-2 gap-x-4 gap-y-1.5">
        {agent.executions > 0 && (
          <>
            <div>
              <span className="text-[10px] text-muted-foreground">Pipeline Runs</span>
              <p className="text-xs font-semibold text-foreground">{agent.executions}</p>
            </div>
            <div>
              <span className="text-[10px] text-muted-foreground">Success Rate</span>
              <p className={cn(
                "text-xs font-semibold",
                isSuccess ? "text-emerald-400" :
                isFailed ? "text-red-400" :
                "text-amber-400",
              )}>
                {Math.round(agent.successRate * 100)}%
              </p>
            </div>
          </>
        )}
        {agent.latency_ms != null && agent.latency_ms > 0 && (
          <>
            <div>
              <span className="text-[10px] text-muted-foreground">Latency</span>
              <p className="text-xs font-semibold text-foreground">
                {(agent.latency_ms / 1000).toFixed(1)}s
              </p>
            </div>
            <div>
              <span className="text-[10px] text-muted-foreground">Tokens Used</span>
              <p className="text-xs font-semibold text-foreground">
                {agent.tokens_used != null ? agent.tokens_used.toLocaleString() : (agent.avgTokens / 1000).toFixed(0)}k
              </p>
            </div>
          </>
        )}
        {agent.retry_count != null && agent.retry_count > 0 && (
          <div className="col-span-2">
            <span className="text-[10px] text-amber-400">↺ {agent.retry_count} retry{agent.retry_count !== 1 ? "s" : ""}</span>
          </div>
        )}
      </div>

      {expanded && agent.executions > 0 && (
        <div className="border-t border-border/50 px-4 py-2.5">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide">Activity Summary</span>
          </div>
          <div className="space-y-1">
            {agent.executions > 0 && (
              <div className="flex items-center justify-between text-[10px]">
                <span className="text-muted-foreground">Status</span>
                <span className={cn(
                  "font-medium capitalize",
                  isSuccess ? "text-emerald-400" :
                  isFailed ? "text-red-400" :
                  "text-amber-400",
                )}>
                  {agent.status}
                </span>
              </div>
            )}
            {agent.model && (
              <div className="flex items-center justify-between text-[10px]">
                <span className="text-muted-foreground">Model</span>
                <span className="font-medium text-foreground">{agent.model}</span>
              </div>
            )}
            {agent.provider && (
              <div className="flex items-center justify-between text-[10px]">
                <span className="text-muted-foreground">Provider</span>
                <span className="font-medium text-foreground capitalize">{agent.provider}</span>
              </div>
            )}
            {agent.avgLatencyMs > 0 && (
              <div className="flex items-center justify-between text-[10px]">
                <span className="text-muted-foreground">Avg Latency</span>
                <span className="font-medium text-foreground">{(agent.avgLatencyMs / 1000).toFixed(1)}s</span>
              </div>
            )}
            {agent.avgTokens > 0 && (
              <div className="flex items-center justify-between text-[10px]">
                <span className="text-muted-foreground">Avg Tokens</span>
                <span className="font-medium text-foreground">{(agent.avgTokens / 1000).toFixed(0)}k</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}