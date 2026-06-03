"use client";

import { useMemo, memo } from "react";
import {
  Activity, AlertCircle, ArrowDown, ArrowUp, BarChart3, Bot,
  CheckCircle2, Clock, Cpu, Filter, Layers, RefreshCw, Timer,
  TrendingUp, Wifi, Zap
} from "lucide-react";
import { cn } from "@/lib/utils";
import { usePipelineStore } from "@/store/pipeline-store";
import { useProvidersStats } from "@/hooks/use-providers-stats";

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
  human_review: "Human Review",
  finalizer: "Final Output",
};

const PIPELINE_STAGES = [
  "skill_retrieval", "memory_retrieval", "research", "planner",
  "writer", "seo", "fact_checker", "compliance", "review", "finalizer",
] as const;

const PROVIDER_LABELS: Record<string, string> = {
  groq: "Groq", nvidia: "NVIDIA", openai: "OpenAI", ollama: "Ollama", anthropic: "Anthropic",
};

const PROVIDER_COLORS: Record<string, string> = {
  groq: "bg-emerald-500", nvidia: "bg-blue-500", openai: "bg-violet-500",
  ollama: "bg-orange-500", anthropic: "bg-amber-500",
};

interface StageHeatmapProps {
  stages: { id: string; status: string; latency_ms?: number; tokens_used?: number }[];
  onStageClick?: (stageId: string) => void;
}

const StageHeatmap = memo(function StageHeatmap({ stages, onStageClick }: StageHeatmapProps) {
  const getStatusStyle = (status: string) => {
    switch (status) {
      case "completed": case "success": return "bg-emerald-500/20 border-emerald-500/30 text-emerald-400";
      case "running": case "pending": return "bg-blue-500/20 border-blue-500/30 text-blue-400 animate-pulse";
      case "failed": case "error": return "bg-red-500/20 border-red-500/30 text-red-400";
      case "skipped": return "bg-amber-500/20 border-amber-500/30 text-amber-400";
      default: return "bg-secondary/40 border-border text-muted-foreground";
    }
  };

  return (
    <div className="rounded-2xl border border-border bg-card/40 p-4">
      <div className="flex items-center gap-2 mb-4">
        <Layers className="h-4 w-4 text-violet-400" />
        <h3 className="text-sm font-semibold text-foreground">Workflow Heatmap</h3>
      </div>
      <div className="grid grid-cols-5 gap-2 sm:grid-cols-5">
        {stages.map((stage) => (
          <button
            key={stage.id}
            onClick={() => onStageClick?.(stage.id)}
            className={cn(
              "flex flex-col items-center justify-center rounded-xl border p-2.5 transition-all duration-200 hover:-translate-y-0.5",
              getStatusStyle(stage.status),
            )}
          >
            <span className="text-[9px] font-semibold text-center leading-tight mb-1">
              {NODE_LABELS[stage.id]?.split(" ")[0] ?? stage.id}
            </span>
            <div className="h-1.5 w-full bg-secondary/40 rounded-full overflow-hidden">
              <div className={cn(
                "h-full rounded-full transition-all",
                stage.status === "completed" ? "bg-emerald-400" :
                stage.status === "running" ? "bg-blue-400 animate-pulse" :
                stage.status === "failed" ? "bg-red-400" :
                "bg-slate-600"
              )} style={{ width: stage.status === "pending" ? "30%" : "100%" }} />
            </div>
            {stage.latency_ms != null && stage.latency_ms > 0 && (
              <span className="text-[8px] mt-1 opacity-70">
                {stage.latency_ms < 1000 ? `${stage.latency_ms}ms` : `${(stage.latency_ms / 1000).toFixed(1)}s`}
              </span>
            )}
          </button>
        ))}
      </div>
      <div className="flex items-center gap-4 mt-3 pt-3 border-t border-border/40">
        <div className="flex items-center gap-1.5 text-[9px] text-muted-foreground">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" /> Completed
        </div>
        <div className="flex items-center gap-1.5 text-[9px] text-muted-foreground">
          <span className="h-1.5 w-1.5 rounded-full bg-blue-400 animate-pulse" /> Running
        </div>
        <div className="flex items-center gap-1.5 text-[9px] text-muted-foreground">
          <span className="h-1.5 w-1.5 rounded-full bg-red-400" /> Failed
        </div>
        <div className="flex items-center gap-1.5 text-[9px] text-muted-foreground">
          <span className="h-1.5 w-1.5 rounded-full bg-slate-600" /> Pending
        </div>
      </div>
    </div>
  );
});

function AgentStatusPanel({ agentMetrics }: { agentMetrics: any[] }) {
  const running = agentMetrics.filter((a) => a.status === "running" || a.status === "pending");
  const completed = agentMetrics.filter((a) => a.status === "completed" || a.status === "success");
  const failed = agentMetrics.filter((a) => a.status === "failed" || a.status === "error");
  const queued = agentMetrics.filter((a) => a.status === "pending" && !running.length);
  const avgTokens = agentMetrics.length > 0
    ? Math.round(agentMetrics.reduce((s, a) => s + (a.tokens_used ?? 0), 0) / agentMetrics.length)
    : 0;
  const avgLatency = agentMetrics.length > 0
    ? Math.round(agentMetrics.reduce((s, a) => s + (a.latency_ms ?? 0), 0) / agentMetrics.length)
    : 0;

  const counts = [
    { label: "Running", value: running.length, icon: <Activity className="h-4 w-4 text-blue-400" />, color: "text-blue-400", bg: "bg-blue-500/10" },
    { label: "Completed", value: completed.length, icon: <CheckCircle2 className="h-4 w-4 text-emerald-400" />, color: "text-emerald-400", bg: "bg-emerald-500/10" },
    { label: "Failed", value: failed.length, icon: <AlertCircle className="h-4 w-4 text-red-400" />, color: "text-red-400", bg: "bg-red-500/10" },
    { label: "Avg Tokens", value: avgTokens > 0 ? avgTokens.toLocaleString() : "—", icon: <Cpu className="h-4 w-4 text-violet-400" />, color: "text-violet-400", bg: "bg-violet-500/10" },
    { label: "Avg Latency", value: avgLatency > 0 ? `${avgLatency}ms` : "—", icon: <Timer className="h-4 w-4 text-amber-400" />, color: "text-amber-400", bg: "bg-amber-500/10" },
  ];

  return (
    <>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
        {counts.map((c) => (
          <div key={c.label} className={cn("rounded-2xl border border-border p-3", c.bg)}>
            <div className="flex items-center gap-2 mb-1">
              {c.icon}
              <span className="text-[10px] font-medium text-muted-foreground">{c.label}</span>
            </div>
            <div className={cn("text-xl font-bold", c.color)}>{c.value}</div>
          </div>
        ))}
      </div>

      <StageHeatmap
        stages={PIPELINE_STAGES.map((stage) => {
          const metric = agentMetrics.find((a) => a.name === stage);
          return {
            id: stage,
            status: metric?.status ?? "pending",
            latency_ms: metric?.latency_ms,
            tokens_used: metric?.tokens_used,
          };
        })}
      />
    </>
  );
}

function ProviderDistribution({ stats }: { stats: Record<string, any> }) {
  const totalCalls = Object.values(stats).reduce((s: number, p: any) => s + (p.total_calls || 0), 0);

  return (
    <div className="rounded-2xl border border-border bg-card/40 p-4">
      <div className="flex items-center gap-2 mb-4">
        <BarChart3 className="h-4 w-4 text-violet-400" />
        <h3 className="text-sm font-semibold text-foreground">Provider Distribution</h3>
      </div>

      {totalCalls === 0 ? (
        <p className="text-xs text-muted-foreground text-center py-6">No call data yet</p>
      ) : (
        <div className="space-y-3">
          {Object.entries(stats)
            .sort(([, a], [, b]) => (b.total_calls || 0) - (a.total_calls || 0))
            .map(([key, s]: [string, any]) => {
              const pct = totalCalls > 0 ? ((s.total_calls || 0) / totalCalls * 100) : 0;
              const barColor = PROVIDER_COLORS[key] || "bg-violet-500";
              const avgLatency = (s.average_latency || 0).toFixed(0);
              const success = (s.success_rate * 100).toFixed(0);
              const active = s.active_requests || 0;

              return (
                <div key={key} className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={cn("h-2 w-2 rounded-full", barColor)} />
                      <span className="text-[11px] font-semibold text-foreground capitalize">
                        {PROVIDER_LABELS[key] || key}
                      </span>
                      <span className="text-[10px] text-muted-foreground">
                        {active > 0 && `${active} active`}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
                      <span>{avgLatency}ms</span>
                      <span className={Number(success) >= 95 ? "text-emerald-400" : Number(success) >= 80 ? "text-amber-400" : "text-red-400"}>
                        {success}%
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
                      <div
                        className={cn("h-full rounded-full transition-all duration-500", barColor)}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="text-[10px] text-muted-foreground w-10 text-right">
                      {pct.toFixed(1)}%
                    </span>
                  </div>
                </div>
              );
            })}
        </div>
      )}
    </div>
  );
}

function ProviderDetailCards({ stats }: { stats: Record<string, any> }) {
  const totalCalls = Object.values(stats).reduce((s: number, p: any) => s + (p.total_calls || 0), 0);
  const totalActive = Object.values(stats).reduce((s: number, p: any) => s + (p.active_requests || 0), 0);
  const avgLatency = Object.values(stats).length > 0
    ? Math.round(Object.values(stats).reduce((s: number, p: any) => s + (p.average_latency || 0), 0) / Object.values(stats).length)
    : 0;

  return (
    <div className="rounded-2xl border border-border bg-card/40 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <Wifi className="h-4 w-4 text-violet-400" />
          Provider Status
        </h3>
        <span className="text-[10px] text-muted-foreground">{totalActive} active requests</span>
      </div>
      <div className="space-y-2">
        {Object.entries(stats).map(([key, s]: [string, any]) => {
          const avgLat = (s.average_latency || 0).toFixed(0);
          const success = (s.success_rate * 100).toFixed(0);
          const circuit = s.circuit_state || "closed";

          return (
            <div key={key} className="flex items-center gap-3 rounded-xl bg-secondary/40 p-2.5">
              <span className={cn(
                "h-2 w-2 rounded-full shrink-0",
                circuit === "closed" ? "bg-emerald-400" :
                circuit === "half_open" ? "bg-amber-400 animate-pulse" :
                "bg-red-400",
              )} />
              <div className="flex-1 min-w-0">
                <span className="text-[11px] font-semibold text-foreground capitalize">
                  {PROVIDER_LABELS[key] || key}
                </span>
              </div>
              <div className="flex items-center gap-3 text-[10px] text-muted-foreground shrink-0">
                <span className="hidden sm:inline">{avgLat}ms</span>
                <span className={Number(success) >= 95 ? "text-emerald-400" : Number(success) >= 80 ? "text-amber-400" : "text-red-400"}>
                  {success}%
                </span>
                <span className="hidden md:inline">{(s.total_calls || 0).toLocaleString()} calls</span>
              </div>
            </div>
          );
        })}
      </div>
      {totalCalls > 0 && (
        <div className="flex items-center justify-between mt-3 pt-3 border-t border-border/40 text-[10px] text-muted-foreground">
          <span>Total: {totalCalls.toLocaleString()} calls</span>
          <span>Avg latency: {avgLatency}ms</span>
        </div>
      )}
    </div>
  );
}

function deriveAgentMetrics(status: any): any[] {
  if (!status?.nodes) return [];

  return PIPELINE_STAGES
    .filter((stage) => stage in status.nodes)
    .map((stage) => {
      const node = status.nodes[stage];
      const actions = node.actions ?? [];
      const agentStartAction = actions.find((a: any) => a.action === "agent_start");
      const providerModel = agentStartAction?.details?.match(/using\s+([^\/]+)\/([^\s]+)/);
      const provider = providerModel?.[1] ?? null;
      const model = providerModel?.[2] ?? null;

      return {
        name: stage,
        status: node.status,
        successRate: node.status === "completed" ? 1 : node.status === "failed" ? 0 : 0.5,
        avgTokens: node.tokens_used ?? 0,
        avgLatencyMs: node.latency_ms ?? 0,
        executions: 1,
        model: model ?? "—",
        provider: provider ?? "—",
        tokens_used: node.tokens_used,
        latency_ms: node.latency_ms,
        retry_count: node.retry_count,
        actions_count: actions.length,
      };
    });
}

export function AgentMonitor() {
  const status = usePipelineStore((s) => s.status);
  const pipelines = usePipelineStore((s) => s.pipelines);
  const events = usePipelineStore((s) => s.events);
  const { stats: providerStats, loading, lastRefresh } = useProvidersStats();

  const agentMetrics = useMemo(() => deriveAgentMetrics(status), [status]);
  const hasAgentData = agentMetrics.length > 0;
  const hasProviderData = Object.keys(providerStats).length > 0;

  return (
    <div className="space-y-4 p-1">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500/20 to-violet-600/10 border border-violet-500/20 shadow-lg shadow-violet-500/10">
            <Bot className="w-5 h-5 text-violet-400" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-foreground">Agent Monitor</h2>
            <p className="text-[10px] text-muted-foreground">
              {lastRefresh ? `Updated ${lastRefresh.toLocaleTimeString()}` : "Real-time agent & provider metrics"}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {hasAgentData && (
            <div className="text-[10px] text-muted-foreground hidden sm:block">
              {agentMetrics.length} stages
            </div>
          )}
          <div className={cn(
            "flex items-center gap-1.5 text-[10px] px-2.5 py-1 rounded-full border",
            loading ? "bg-blue-500/10 text-blue-400 border-blue-500/20" : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
          )}>
            <RefreshCw className={cn("h-3 w-3", loading && "animate-spin")} />
            {loading ? "Refreshing" : "Live"}
          </div>
        </div>
      </div>

      {!hasAgentData && !hasProviderData ? (
        <div className="flex flex-col items-center justify-center py-20 text-center rounded-2xl border border-dashed border-border">
          <Bot className="h-14 w-14 text-muted-foreground/20 mb-4" />
          <h3 className="text-sm font-semibold text-foreground mb-1">No agent data yet</h3>
          <p className="text-xs text-muted-foreground max-w-sm">
            Run a pipeline to see real-time agent metrics, workflow heatmap, and provider performance data.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {hasAgentData && <AgentStatusPanel agentMetrics={agentMetrics} />}

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {hasProviderData && (
              <>
                <ProviderDistribution stats={providerStats} />
                <ProviderDetailCards stats={providerStats} />
              </>
            )}
          </div>

          {hasAgentData && agentMetrics.some((a) => a.provider && a.provider !== "—") && (
            <div className="rounded-2xl border border-border bg-card/40 p-4">
              <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-violet-400" />
                Agent → Provider Mapping
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-[11px]">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left py-2 px-2 text-muted-foreground font-medium">Agent</th>
                      <th className="text-left py-2 px-2 text-muted-foreground font-medium">Provider</th>
                      <th className="text-left py-2 px-2 text-muted-foreground font-medium">Model</th>
                      <th className="text-right py-2 px-2 text-muted-foreground font-medium">Tokens</th>
                      <th className="text-right py-2 px-2 text-muted-foreground font-medium">Latency</th>
                    </tr>
                  </thead>
                  <tbody>
                    {agentMetrics.filter((a) => a.provider && a.provider !== "—").map((a) => (
                      <tr key={a.name} className="border-b border-border/40 hover:bg-secondary/20 transition-colors">
                        <td className="py-2 px-2 font-medium text-foreground">
                          {NODE_LABELS[a.name] ?? a.name}
                        </td>
                        <td className="py-2 px-2 capitalize text-muted-foreground">{a.provider}</td>
                        <td className="py-2 px-2 text-muted-foreground font-mono text-[10px]">{a.model}</td>
                        <td className="py-2 px-2 text-right text-muted-foreground">
                          {a.tokens_used?.toLocaleString() ?? "—"}
                        </td>
                        <td className="py-2 px-2 text-right text-muted-foreground">
                          {a.latency_ms != null && a.latency_ms > 0
                            ? a.latency_ms < 1000 ? `${a.latency_ms}ms` : `${(a.latency_ms / 1000).toFixed(1)}s`
                            : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}