import { cn } from "@/lib/utils";
import type { AgentMetrics } from "@/types/api";
import { AgentStatus } from "./AgentStatus";

interface AgentGridProps {
  agents: AgentMetrics[];
  className?: string;
}

export function AgentGrid({ agents, className }: AgentGridProps) {
  return (
    <div className={cn("grid grid-cols-1 gap-3 sm:grid-cols-2", className)}>
      {agents.map((agent) => (
        <AgentStatus key={agent.name} agent={agent} />
      ))}
    </div>
  );
}
