"use client";

import dynamic from "next/dynamic";

const AgentGrid = dynamic(() => import("@/components/agents/AgentGrid").then((m) => ({ default: m.AgentGrid })), { ssr: false });
const ProviderHealth = dynamic(() => import("@/components/agents/ProviderHealth").then((m) => ({ default: m.ProviderHealth })), { ssr: false });
const CircuitBreakerStatus = dynamic(() => import("@/components/agents/CircuitBreakerStatus").then((m) => ({ default: m.CircuitBreakerStatus })), { ssr: false });
const TokenBudget = dynamic(() => import("@/components/agents/TokenBudget").then((m) => ({ default: m.TokenBudget })), { ssr: false });
import { usePipelineStore } from "@/store/pipeline-store";

export function AgentMonitor() {
  const pipelines = usePipelineStore((s) => s.pipelines);
  const completed = pipelines.filter((p) => p.status === "completed");
  const failed = pipelines.filter((p) => p.status === "failed");

  const mockAgents: import("@/types/api").AgentMetrics[] = [
    { name: "Research Agent", status: "active", successRate: pipelines.length > 0 ? (pipelines.length - failed.length) / pipelines.length : 1, avgTokens: 150000, avgLatencyMs: 3200, executions: pipelines.length, model: "gpt-4o" },
    { name: "Writing Agent", status: "active", successRate: completed.length > 0 ? 1 : 0, avgTokens: 250000, avgLatencyMs: 4800, executions: completed.length, model: "gpt-4o" },
    { name: "Review Agent", status: "idle", successRate: completed.length > 0 ? 1 : 0, avgTokens: 80000, avgLatencyMs: 2100, executions: completed.length, model: "gpt-4o" },
  ];

  const mockProviders: import("@/types/api").ProviderHealthStatus[] = [
    { provider: "OpenAI", status: "healthy", model: "gpt-4o", rateLimit: { remaining: 100, limit: 500, resetsInMs: 60000 } },
    { provider: "Groq", status: "healthy", model: "mixtral-8x7b", rateLimit: { remaining: 50, limit: 200, resetsInMs: 60000 } },
    { provider: "NVIDIA", status: "healthy", model: "nemotron-3-super-120b", rateLimit: { remaining: 80, limit: 300, resetsInMs: 60000 } },
    { provider: "Ollama", status: "down", model: "gpt-oss:120b", rateLimit: null },
  ];

  return (
    <div className="space-y-4">
      <AgentGrid agents={mockAgents} />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <ProviderHealth providers={mockProviders} />
        <CircuitBreakerStatus state="closed" failureCount={2} threshold={10} />
        <TokenBudget used={480000} limit={12000000} />
      </div>
    </div>
  );
}
