"use client";

import { useEffect, useState, useCallback } from "react";
import {
  AlertTriangle, ArrowDownToLine, BookOpen, Brain, ChevronDown,
  ChevronRight, Clock, Cpu, Database, FileOutput, Hash, Layers,
  MessageSquare, RefreshCw, Search, Timer, X, Zap
} from "lucide-react";
import { cn } from "@/lib/utils";
import { usePipelineStore } from "@/store/pipeline-store";
import { useAgentNodes, type AgentNode } from "@/hooks/use-agent-nodes";
import type { AgentAction } from "@/types/api";

const NODE_LABELS: Record<string, string> = {
  skill_retrieval: "Skill Retrieval",
  memory_retrieval: "Memory Retrieval",
  research: "Research",
  planner: "Planner",
  writer: "Writer",
  seo: "SEO",
  fact_checker: "Fact Check",
  compliance: "Compliance",
  review: "Review",
  finalizer: "Final Output",
  prompt: "Prompt",
};

const ACTION_ICONS: Record<string, React.ReactNode> = {
  agent_start: <Zap className="h-3 w-3" />,
  llm_request: <Cpu className="h-3 w-3" />,
  llm_response: <ArrowDownToLine className="h-3 w-3" />,
  parse_output: <FileOutput className="h-3 w-3" />,
  retry: <RefreshCw className="h-3 w-3" />,
  error: <AlertTriangle className="h-3 w-3" />,
  skipped: <X className="h-3 w-3" />,
};

function formatTime(ts: string | null | undefined) {
  if (!ts) return "—";
  try { return new Date(ts).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit" }); }
  catch { return "—"; }
}

function formatDuration(ms: number | null | undefined) {
  if (ms == null) return "—";
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

function formatTokens(tokens: number | null | undefined) {
  if (tokens == null || tokens === 0) return "—";
  return `${tokens.toLocaleString()} tokens`;
}

function estimateCost(tokens: number | null | undefined, provider: string | null | undefined) {
  if (!tokens) return null;
  const per1k = provider === "openai" ? 0.01 : provider === "anthropic" ? 0.015 : provider === "nvidia" ? 0.002 : 0.001;
  return (tokens / 1000 * per1k).toFixed(4);
}

interface DetailRowProps {
  icon: React.ReactNode;
  label: string;
  value: string | number | null | undefined;
  accent?: string;
  mono?: boolean;
}

function DetailRow({ icon, label, value, accent, mono }: DetailRowProps) {
  if (value == null || value === "" || value === 0) return null;
  return (
    <div className="flex items-start gap-2.5 py-1.5 border-b border-border/40 last:border-0">
      <div className={cn(
        "flex h-7 w-7 shrink-0 items-center justify-center rounded-lg mt-0.5",
        accent === "violet" && "bg-violet-500/10 text-violet-400",
        accent === "emerald" && "bg-emerald-500/10 text-emerald-400",
        accent === "blue" && "bg-blue-500/10 text-blue-400",
        accent === "amber" && "bg-amber-500/10 text-amber-400",
        accent === "red" && "bg-red-500/10 text-red-400",
        !accent && "bg-secondary text-muted-foreground",
      )}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[10px] text-muted-foreground font-medium">{label}</div>
        <div className={cn(
          "text-xs text-foreground leading-snug",
          mono && "font-mono text-[11px]",
          accent === "red" && "text-red-400",
        )}>
          {String(value)}
        </div>
      </div>
    </div>
  );
}

interface ExecutionTimelineProps {
  actions: AgentAction[];
}

function ExecutionTimeline({ actions }: ExecutionTimelineProps) {
  const [expanded, setExpanded] = useState(false);

  if (actions.length === 0) {
    return <p className="text-xs text-muted-foreground text-center py-4">No timeline data</p>;
  }

  const getActionColor = (action: string, success?: boolean) => {
    if (success === false || action === "error") return "border-red-500/30 bg-red-500/5";
    if (success === true) return "border-emerald-500/20 bg-emerald-500/5";
    return "border-border bg-secondary/30";
  };

  return (
    <div>
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-xs font-semibold text-foreground mb-2 hover:text-violet-400 transition-colors"
      >
        {expanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        Execution Timeline ({actions.length} steps)
      </button>
      {expanded && (
        <div className="space-y-1.5 mt-2">
          {actions.map((action, i) => {
            const colorClass = getActionColor(action.action, action.success);
            const isError = action.action === "error" || action.success === false;
            const isSuccess = action.success === true;

            return (
              <div
                key={i}
                className={cn(
                  "flex items-start gap-2.5 rounded-xl border p-2.5 transition-all",
                  colorClass,
                )}
                style={{ animationDelay: `${i * 30}ms` }}
              >
                <div className={cn(
                  "flex h-6 w-6 shrink-0 items-center justify-center rounded-lg text-[10px]",
                  isError ? "bg-red-500/20 text-red-400" :
                  isSuccess ? "bg-emerald-500/20 text-emerald-400" :
                  "bg-secondary text-muted-foreground",
                )}>
                  {ACTION_ICONS[action.action] ?? "•"}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline justify-between gap-2">
                    <span className={cn(
                      "text-[11px] font-medium capitalize",
                      isError ? "text-red-400" : isSuccess ? "text-emerald-400" : "text-foreground",
                    )}>
                      {action.action.replace(/_/g, " ")}
                    </span>
                    <span className="text-[9px] text-muted-foreground flex-shrink-0 font-mono">
                      {formatTime(action.timestamp)}
                    </span>
                  </div>
                  {action.details && (
                    <p className="mt-0.5 text-[10px] text-muted-foreground leading-relaxed line-clamp-3">
                      {action.details}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

interface AgentNodeDetailProps {
  node: AgentNode;
}

function AgentNodeDetail({ node }: AgentNodeDetailProps) {
  const label = NODE_LABELS[node.name] ?? node.name;
  const isRunning = node.status === "running" || node.status === "pending";
  const isFailed = node.status === "failed" || node.status === "error";
  const isCompleted = node.status === "completed" || node.status === "success";

  const agentStartAction = node.actions.find((a) => a.action === "agent_start");
  const llmRequestAction = node.actions.find((a) => a.action === "llm_request");
  const llmResponseAction = node.actions.find((a) => a.action === "llm_response");

  const cost = estimateCost(node.tokens_used, node.provider);

  return (
    <div className="space-y-4 overflow-y-auto max-h-full">
      <div className="flex items-start gap-3">
        <div className={cn(
          "flex h-10 w-10 items-center justify-center rounded-2xl text-sm font-bold shrink-0",
          isCompleted && "bg-emerald-500/10 text-emerald-400",
          isRunning && "bg-blue-500/10 text-blue-400 animate-pulse",
          isFailed && "bg-red-500/10 text-red-400",
          !isCompleted && !isRunning && !isFailed && "bg-secondary text-muted-foreground",
        )}>
          {label.charAt(0)}
        </div>
        <div>
          <h2 className="text-sm font-bold text-foreground">{label}</h2>
          <div className="flex items-center gap-1.5 mt-0.5">
            <span className={cn(
              "status-dot",
              isCompleted && "success",
              isRunning && "running",
              isFailed && "failed",
              !isCompleted && !isRunning && !isFailed && "pending",
            )} />
            <span className={cn(
              "text-[11px] font-medium capitalize",
              isCompleted && "text-emerald-400",
              isRunning && "text-blue-400",
              isFailed && "text-red-400",
              !isCompleted && !isRunning && !isFailed && "text-muted-foreground",
            )}>
              {node.status}
            </span>
          </div>
        </div>
      </div>

      {isFailed && node.error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-3">
          <div className="flex items-center gap-2 mb-1.5">
            <AlertTriangle className="h-3.5 w-3.5 text-red-400" />
            <span className="text-[11px] font-semibold text-red-400">Error</span>
          </div>
          <p className="text-[11px] text-red-300/80 leading-relaxed">{node.error}</p>
        </div>
      )}

      <div className="space-y-1">
        <DetailRow
          icon={<Cpu className="h-3.5 w-3.5" />}
          label="Provider"
          value={node.provider ? (
            <span className="capitalize">{node.provider}</span>
          ) : undefined}
          accent="violet"
        />
        <DetailRow
          icon={<Layers className="h-3.5 w-3.5" />}
          label="Model"
          value={node.model}
          accent="violet"
        />
        <DetailRow
          icon={<Timer className="h-3.5 w-3.5" />}
          label="Latency"
          value={formatDuration(node.latency_ms)}
          accent="blue"
        />
        <DetailRow
          icon={<Hash className="h-3.5 w-3.5" />}
          label="Tokens"
          value={formatTokens(node.tokens_used)}
          accent="emerald"
        />
        {cost && (
          <DetailRow
            icon={<span className="text-[10px] font-bold">$</span>}
            label="Est. Cost"
            value={`$${cost}`}
            accent="amber"
          />
        )}
        <DetailRow
          icon={<RefreshCw className="h-3.5 w-3.5" />}
          label="Retries"
          value={node.retry_count > 0 ? String(node.retry_count) : undefined}
          accent={node.retry_count > 0 ? "red" : undefined}
        />
        <DetailRow
          icon={<Clock className="h-3.5 w-3.5" />}
          label="Started"
          value={formatTime(node.started_at)}
          accent="muted"
        />
        <DetailRow
          icon={<Clock className="h-3.5 w-3.5" />}
          label="Completed"
          value={formatTime(node.completed_at)}
          accent="muted"
        />
      </div>

      {agentStartAction?.details && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <MessageSquare className="h-3.5 w-3.5 text-violet-400" />
            <span className="text-[11px] font-semibold text-foreground">Prompt Sent</span>
          </div>
          <div className="rounded-xl bg-secondary/40 border border-border p-2.5">
            <p className="text-[10px] text-muted-foreground leading-relaxed font-mono whitespace-pre-wrap">
              {agentStartAction.details}
            </p>
          </div>
        </div>
      )}

      {llmRequestAction?.details && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Cpu className="h-3.5 w-3.5 text-blue-400" />
            <span className="text-[11px] font-semibold text-foreground">LLM Request</span>
          </div>
          <div className="rounded-xl bg-blue-500/5 border border-blue-500/20 p-2.5">
            <p className="text-[10px] text-muted-foreground leading-relaxed line-clamp-4 whitespace-pre-wrap">
              {llmRequestAction.details}
            </p>
          </div>
        </div>
      )}

      {llmResponseAction?.details && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <ArrowDownToLine className="h-3.5 w-3.5 text-emerald-400" />
            <span className="text-[11px] font-semibold text-foreground">LLM Response</span>
          </div>
          <div className="rounded-xl bg-emerald-500/5 border border-emerald-500/20 p-2.5">
            <p className="text-[10px] text-muted-foreground leading-relaxed whitespace-pre-wrap max-h-[200px] overflow-y-auto">
              {llmResponseAction.details}
            </p>
          </div>
        </div>
      )}

      {node.output && Object.keys(node.output).length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <FileOutput className="h-3.5 w-3.5 text-emerald-400" />
            <span className="text-[11px] font-semibold text-foreground">Generated Output</span>
          </div>
          <div className="rounded-xl bg-emerald-500/5 border border-emerald-500/20 p-2.5">
            <pre className="text-[10px] text-muted-foreground leading-relaxed whitespace-pre-wrap max-h-[300px] overflow-y-auto font-mono">
              {JSON.stringify(node.output, null, 2)}
            </pre>
          </div>
        </div>
      )}

      <div>
        <ExecutionTimeline actions={node.actions} />
      </div>
    </div>
  );
}

interface AgentTransparencyPanelProps {
  nodeId: string | null;
  onClose: () => void;
}

export function AgentTransparencyPanel({ nodeId, onClose }: AgentTransparencyPanelProps) {
  const agentNodes = useAgentNodes();
  const node = agentNodes.find((n) => n.name === nodeId);

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === "Escape") onClose();
  }, [onClose]);

  useEffect(() => {
    if (!nodeId) return;
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [nodeId, handleKeyDown]);

  return (
    <>
      {nodeId && (
        <div
          className="fixed inset-0 z-30 bg-black/30 backdrop-blur-sm animate-fade-in md:hidden"
          onClick={onClose}
        />
      )}
      <div
        className={cn(
          "fixed right-0 top-0 z-40 h-full w-full sm:w-[480px] bg-card/95 backdrop-blur-xl border-l border-border transform transition-transform duration-300 ease-out overflow-hidden",
          nodeId ? "translate-x-0" : "translate-x-full",
        )}
        role="complementary"
        aria-label="Agent details"
        aria-hidden={!nodeId}
      >
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between border-b border-border px-4 py-3 shrink-0">
            <div className="flex items-center gap-2">
              <Brain className="h-4 w-4 text-violet-400" />
              <span className="text-sm font-semibold text-foreground">Agent Details</span>
            </div>
            <button
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-xl hover:bg-secondary transition-colors"
            >
              <X className="h-4 w-4 text-muted-foreground" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {node ? (
              <AgentNodeDetail node={node} />
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center py-12">
                <Brain className="h-12 w-12 text-muted-foreground/20 mb-4" />
                <h3 className="text-sm font-semibold text-foreground mb-1">No agent data</h3>
                <p className="text-xs text-muted-foreground">
                  Select a pipeline node to view agent details
                </p>
              </div>
            )}
          </div>

          <div className="border-t border-border px-4 py-3 shrink-0">
            <div className="flex items-center gap-2">
              {node && (
                <span className="text-[10px] text-muted-foreground">
                  {node.actions.length} actions · {node.tokens_used?.toLocaleString() || 0} tokens · {formatDuration(node.latency_ms)}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}