"use client";

import { useMemo } from "react";
import { usePipelineStore } from "@/store/pipeline-store";
import type { AgentAction, NodeInfo } from "@/types/api";

const PIPELINE_STAGES = [
  "skill_retrieval", "memory_retrieval", "research", "planner",
  "writer", "seo", "fact_checker", "compliance", "human_review", "finalizer",
] as const;

export interface AgentNode {
  name: string;
  status: string;
  latency_ms: number;
  tokens_used: number;
  started_at: string | null;
  completed_at: string | null;
  actions: AgentAction[];
  output: Record<string, unknown>;
  retry_count: number;
  error: string | null;
  provider: string | null;
  model: string | null;
}

function extractProviderModel(details: string): { provider: string | null; model: string | null } {
  const match = details.match(/using\s+([^\/]+)\/([^\s\)]+)/);
  return { provider: match?.[1] ?? null, model: match?.[2] ?? null };
}

export function useAgentNodes(): AgentNode[] {
  const status = usePipelineStore((s) => s.status);
  const events = usePipelineStore((s) => s.events);

  return useMemo(() => {
    const nodes: Record<string, AgentNode> = {};

    if (status?.nodes) {
      for (const stage of PIPELINE_STAGES) {
        if (!(stage in status.nodes)) continue;
        const node = status.nodes[stage];
        if (!node) continue;

        let provider: string | null = null;
        let model: string | null = null;
        for (const action of node.actions ?? []) {
          if (action.action === "agent_start" && action.details) {
            const ex = extractProviderModel(action.details);
            provider = ex.provider;
            model = ex.model;
            break;
          }
        }

        nodes[stage] = {
          name: stage,
          status: node.status,
          latency_ms: node.latency_ms,
          tokens_used: node.tokens_used,
          started_at: node.started_at,
          completed_at: node.completed_at,
          actions: node.actions ?? [],
          output: node.output ?? {},
          retry_count: node.retry_count,
          error: node.error,
          provider,
          model,
        };
      }
    }

    for (const event of events) {
      if (!event.node) continue;
      if (event.type !== "node_completed" && event.type !== "node_running" && event.type !== "node_failed") continue;

      const existing = nodes[event.node];

      if (existing) {
        if (event.actions && event.actions.length > (existing.actions.length || 0)) {
          let provider: string | null = existing.provider;
          let model: string | null = existing.model;
          for (const action of event.actions) {
            if (action.action === "agent_start" && action.details) {
              const ex = extractProviderModel(action.details);
              provider = ex.provider ?? provider;
              model = ex.model ?? model;
              break;
            }
          }
          nodes[event.node] = {
            ...existing,
            status: event.status ?? existing.status,
            latency_ms: event.latency_ms ?? existing.latency_ms,
            tokens_used: event.tokens_used ?? existing.tokens_used,
            actions: event.actions ?? existing.actions,
            provider,
            model,
          };
        }
      } else {
        let provider: string | null = null;
        let model: string | null = null;
        for (const action of event.actions ?? []) {
          if (action.action === "agent_start" && action.details) {
            const ex = extractProviderModel(action.details);
            provider = ex.provider;
            model = ex.model;
            break;
          }
        }
        nodes[event.node] = {
          name: event.node,
          status: event.status ?? "running",
          latency_ms: event.latency_ms ?? 0,
          tokens_used: event.tokens_used ?? 0,
          started_at: event.started_at ?? null,
          completed_at: event.completed_at ?? null,
          actions: event.actions ?? [],
          output: {},
          retry_count: 0,
          error: event.error ?? null,
          provider,
          model,
        };
      }
    }

    return Object.values(nodes);
  }, [status, events]);
}