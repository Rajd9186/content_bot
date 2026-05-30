import { cn } from "@/lib/utils";
import type { AgentMetrics } from "@/types/api";

interface AgentStatusProps {
  agent: AgentMetrics;
  className?: string;
}

export function AgentStatus({ agent, className }: AgentStatusProps) {
  const ok = agent.successRate > 0.8;
  return (
    <div className={cn("rounded-xl border border-border bg-card/30 p-4", className)}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-foreground">{agent.name}</span>
        <span
          className={cn(
            "h-2 w-2 rounded-full",
            ok ? "bg-emerald-400" : "bg-amber-400",
            ok ? "" : "animate-pulse-soft",
          )}
        />
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2 text-[10px]">
        <div>
          <span className="text-muted-foreground/60">Pipeline Runs</span>
          <p className="font-medium text-foreground">{agent.executions}</p>
        </div>
        <div>
          <span className="text-muted-foreground/60">Success Rate</span>
          <p className={cn("font-medium", ok ? "text-emerald-400" : "text-amber-400")}>
            {Math.round(agent.successRate * 100)}%
          </p>
        </div>
        <div>
          <span className="text-muted-foreground/60">Avg Latency</span>
          <p className="font-medium text-foreground">{(agent.avgLatencyMs / 1000).toFixed(1)}s</p>
        </div>
        <div>
          <span className="text-muted-foreground/60">Tokens</span>
          <p className="font-medium text-foreground">{(agent.avgTokens / 1000).toFixed(0)}k</p>
        </div>
      </div>
    </div>
  );
}
