import { cn } from "@/lib/utils";
import { MetricsCard } from "./MetricsCard";
import type { AnalyticsSummary } from "@/types/api";

interface StatsGridProps {
  data: AnalyticsSummary;
  className?: string;
}

export function StatsGrid({ data, className }: StatsGridProps) {
  return (
    <div className={cn("grid grid-cols-2 gap-3 lg:grid-cols-4", className)}>
      <MetricsCard label="Total Pipelines" value={data.totalPipelines} />
      <MetricsCard label="Success Rate" value={`${Math.round(data.successRate * 100)}%`} change={{ value: Math.round((data.successRate - 0.8) * 100), positive: data.successRate > 0.8 }} />
      <MetricsCard label="Avg Duration" value={`${Math.round(data.avgExecutionTimeMs / 1000)}s`} />
      <MetricsCard label="Total Tokens" value={data.totalTokens ? (data.totalTokens / 1000).toFixed(0) + "k" : "0"} />
    </div>
  );
}
