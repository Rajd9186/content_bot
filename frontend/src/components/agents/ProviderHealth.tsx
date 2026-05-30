import { cn } from "@/lib/utils";
import type { ProviderHealthStatus } from "@/types/api";

interface ProviderHealthProps {
  providers: ProviderHealthStatus[];
  className?: string;
}

const HEALTH_LABELS: Record<string, string> = {
  healthy: "Healthy",
  degraded: "Degraded",
  down: "Down",
  circuit_open: "Circuit Open",
};

export function ProviderHealth({ providers, className }: ProviderHealthProps) {
  return (
    <div className={cn("space-y-2", className)}>
      {providers.map((p, i) => (
        <div
          key={p.provider ?? i}
          className="flex items-center justify-between rounded-lg border border-border bg-black/20 px-3 py-2"
        >
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "h-2 w-2 rounded-full",
                p.status === "healthy" ? "bg-emerald-400" :
                p.status === "degraded" ? "bg-amber-400" :
                "bg-red-400",
                p.status === "degraded" ? "animate-pulse-soft" : "",
              )}
            />
            <span className="text-xs font-medium text-foreground">{p.provider}</span>
          </div>
          <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
            <span>{p.model}</span>
            <span className={cn(
              p.status === "healthy" ? "text-emerald-400" :
              p.status === "degraded" ? "text-amber-400" :
              "text-red-400",
            )}>
              {HEALTH_LABELS[p.status] ?? p.status}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
