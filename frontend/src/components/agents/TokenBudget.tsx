import { cn } from "@/lib/utils";

interface TokenBudgetProps {
  used: number;
  limit: number;
  className?: string;
}

export function TokenBudget({ used, limit, className }: TokenBudgetProps) {
  const pct = Math.min((used / limit) * 100, 100);
  const color =
    pct < 60 ? "bg-emerald-400" :
    pct < 85 ? "bg-amber-400" :
    "bg-red-400";

  return (
    <div className={cn("rounded-xl border border-border bg-card/30 p-4", className)}>
      <span className="text-xs font-semibold text-foreground">Token Budget</span>
      <div className="mt-3 space-y-2">
        <div className="flex items-center justify-between text-[10px]">
          <span className="text-muted-foreground/60">Used</span>
          <span className="font-medium text-foreground">{(used / 1000).toFixed(0)}k / {(limit / 1000).toFixed(0)}k</span>
        </div>
        <div className="h-2 rounded-full bg-white/5">
          <div
            className={cn("h-full rounded-full transition-all duration-500", color)}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    </div>
  );
}
