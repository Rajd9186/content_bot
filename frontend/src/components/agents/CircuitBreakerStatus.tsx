import { cn } from "@/lib/utils";

interface CircuitBreakerStatusProps {
  state: "closed" | "open" | "half_open";
  failureCount: number;
  threshold: number;
  className?: string;
}

export function CircuitBreakerStatus({ state, failureCount, threshold, className }: CircuitBreakerStatusProps) {
  const label = state === "closed" ? "Closed" : state === "open" ? "Open" : "Half-Open";
  const color =
    state === "closed" ? "bg-emerald-400" :
    state === "open" ? "bg-red-400" :
    "bg-amber-400";

  return (
    <div className={cn("rounded-xl border border-border bg-card/30 p-4", className)}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-foreground">Circuit Breaker</span>
        <span className={cn("h-2 w-2 rounded-full", color, state === "half_open" ? "animate-pulse-soft" : "")} />
      </div>
      <div className="mt-3 space-y-2">
        <div className="flex items-center justify-between text-[10px]">
          <span className="text-muted-foreground/60">State</span>
          <span className="font-medium text-foreground">{label}</span>
        </div>
        <div className="flex items-center justify-between text-[10px]">
          <span className="text-muted-foreground/60">Failures</span>
          <span className={cn("font-medium", state !== "closed" ? "text-red-400" : "text-foreground")}>{failureCount}/{threshold}</span>
        </div>
        <div className="h-1.5 rounded-full bg-white/5">
          <div
            className={cn("h-full rounded-full transition-all", color.replace("bg-", "bg-").replace("400", "400/70"))}
            style={{ width: `${Math.min((failureCount / threshold) * 100, 100)}%` }}
          />
        </div>
      </div>
    </div>
  );
}
