"use client";

import { usePipelineStore } from "@/store/pipeline-store";
import { useProvidersStats } from "@/hooks/use-providers-stats";
import { AgentGrid } from "@/components/agents/AgentGrid";
import { ProviderHealth } from "@/components/agents/ProviderHealth";
import { CircuitBreakerStatus } from "@/components/agents/CircuitBreakerStatus";
import { TokenBudget } from "@/components/agents/TokenBudget";
import type { AgentMetrics, ProviderHealthStatus } from "@/types/api";
import { cn } from "@/lib/utils";

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

const PIPELINE_STAGES = [
  "skill_retrieval", "memory_retrieval", "research", "planner",
  "writer", "seo", "fact_checker", "compliance", "human_review", "finalizer",
] as const;

const PROVIDER_LABELS: Record<string, string> = {
  groq: "Groq",
  nvidia: "NVIDIA",
  openai: "OpenAI",
  ollama: "Ollama",
  anthropic: "Anthropic",
};

function deriveAgentMetrics(status: ReturnType<typeof usePipelineStore.getState>["status"]): AgentMetrics[] {
  if (!status?.nodes) return [];

  return PIPELINE_STAGES
    .filter((stage) => stage in status.nodes)
    .map((stage) => {
      const node = status.nodes[stage];
      const isSuccess = node.status === "success" || node.status === "completed";
      const isFailed = node.status === "failed" || node.status === "error";
      const isRunning = node.status === "running";

      const actions = node.actions ?? [];
      const agentStartAction = actions.find((a: { action: string }) => a.action === "agent_start");
      const providerModel = agentStartAction?.details?.match(/using\s+([^\/]+)\/([^\s]+)/);
      const provider = providerModel?.[1] ?? null;
      const model = providerModel?.[2] ?? null;

      const llmResponse = actions.filter((a: { action: string }) =>
        a.action === "llm_response" || a.action === "llm_response_received"
      );
      const successAction = actions.find((a: { success?: boolean }) => a.success === true);
      const failedAction = actions.find((a: { success?: boolean }) => a.success === false);

      return {
        name: stage,
        status: node.status,
        successRate: isSuccess ? 1 : isFailed ? 0 : 0.5,
        avgTokens: node.tokens_used ?? 0,
        avgLatencyMs: node.latency_ms ?? 0,
        executions: 1,
        model: model ?? "—",
        provider: provider ?? "—",
        tokens_used: node.tokens_used,
        latency_ms: node.latency_ms,
        retry_count: node.retry_count,
        actions_count: actions.length,
      } satisfies AgentMetrics;
    });
}

function buildProviderHealthFromStats(stats: ReturnType<typeof useProvidersStats>["stats"]): ProviderHealthStatus[] {
  return Object.entries(stats).map(([key, s]) => {
    let healthStatus: ProviderHealthStatus["status"] = "healthy";
    if (s.circuit_state === "open") healthStatus = "circuit_open";
    else if (s.success_rate < 0.7) healthStatus = "degraded";
    else if (s.total_calls === 0) healthStatus = "down";

    return {
      provider: PROVIDER_LABELS[key] ?? key,
      status: healthStatus,
      model: "—",
      rateLimit: {
        remaining: s.rpm_limit - s.rpm_used,
        limit: s.rpm_limit,
        resetsInMs: 60000,
      },
      circuitBreaker: {
        state: s.circuit_state as "closed" | "open" | "half_open",
        failureCount: 0,
        threshold: 10,
        resetTimeoutMs: 30000,
      },
    };
  });
}

export function AgentMonitor() {
  const status = usePipelineStore((s) => s.status);
  const pipelines = usePipelineStore((s) => s.pipelines);
  const { stats: providerStats, loading: providersLoading, lastRefresh } = useProvidersStats();

  const agentMetrics = deriveAgentMetrics(status);
  const hasPipelineData = agentMetrics.length > 0;
  const hasProviderData = Object.keys(providerStats).length > 0;

  const totalTokens = agentMetrics.reduce((sum, a) => sum + (a.tokens_used ?? 0), 0);
  const completedCount = agentMetrics.filter((a) =>
    a.status === "success" || a.status === "completed"
  ).length;
  const tpmUsed = Object.values(providerStats).reduce((sum, p) => sum + p.tpm_used, 0);
  const tpmLimit = Object.values(providerStats).reduce((sum, p) => sum + p.tpm_limit, 0);
  const anyCircuitOpen = Object.values(providerStats).some((p) => p.circuit_state === "open");
  const anyHalfOpen = Object.values(providerStats).some((p) => p.circuit_state === "half_open");
  const worstState = anyCircuitOpen ? "open" : anyHalfOpen ? "half_open" : "closed";

  const providerHealth = buildProviderHealthFromStats(providerStats);

  return (
    <div className="space-y-4">
      <AgentGrid agents={agentMetrics} />

      {hasProviderData && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <ProviderHealth providers={providerHealth} />
          <CircuitBreakerStatus
            state={worstState}
            failureCount={Object.values(providerStats).filter((p) => p.circuit_state === "open").length}
            threshold={Object.keys(providerStats).length}
          />
          <TokenBudget used={tpmUsed} limit={tpmLimit} />
        </div>
      )}

      {!hasPipelineData && !hasProviderData && (
        <div className="rounded-2xl border border-border bg-card/30 p-6 text-center">
          <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-secondary">
            <span className="text-lg">◈</span>
          </div>
          <p className="text-sm font-medium text-foreground">No agent data yet</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Run a pipeline to see real-time agent metrics and provider stats.
          </p>
        </div>
      )}

      {hasProviderData && (
        <div className="rounded-2xl border border-border bg-card/30 p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide">
              Provider Stats
            </span>
            {lastRefresh && (
              <span className="text-[9px] text-muted-foreground">
                Updated {lastRefresh.toLocaleTimeString()}
              </span>
            )}
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-5">
            {Object.entries(providerStats).map(([key, s]) => (
              <div key={key} className="rounded-xl border border-border bg-secondary/30 p-2.5">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-bold text-foreground capitalize">
                    {PROVIDER_LABELS[key] ?? key}
                  </span>
                  <span className={cn(
                    "h-1.5 w-1.5 rounded-full",
                    s.circuit_state === "closed" ? "bg-emerald-400" :
                    s.circuit_state === "half_open" ? "bg-amber-400 animate-pulse-soft" :
                    "bg-red-400",
                  )} />
                </div>
                <div className="space-y-0.5">
                  <div className="flex justify-between text-[9px]">
                    <span className="text-muted-foreground">Calls</span>
                    <span className="text-foreground font-medium">{(s.total_calls || 0).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-[9px]">
                    <span className="text-muted-foreground">RPM</span>
                    <span className="text-foreground font-medium">{s.rpm_used}/{s.rpm_limit}</span>
                  </div>
                  <div className="flex justify-between text-[9px]">
                    <span className="text-muted-foreground">TPM</span>
                    <span className="text-foreground font-medium">{(s.tpm_used / 1000).toFixed(0)}k</span>
                  </div>
                  <div className="flex justify-between text-[9px]">
                    <span className="text-muted-foreground">Latency</span>
                    <span className="text-foreground font-medium">{(s.average_latency || 0).toFixed(0)}ms</span>
                  </div>
                  <div className="flex justify-between text-[9px]">
                    <span className="text-muted-foreground">Success</span>
                    <span className={cn(
                      "font-medium",
                      (s.success_rate || 1) >= 0.95 ? "text-emerald-400" :
                      (s.success_rate || 1) >= 0.8 ? "text-amber-400" :
                      "text-red-400",
                    )}>
                      {((s.success_rate || 1) * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}