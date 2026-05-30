import { cn } from "@/lib/utils";

interface MetricsCardProps {
  label: string;
  value: string | number;
  change?: { value: number; positive: boolean };
  icon?: string;
  className?: string;
}

export function MetricsCard({ label, value, change, icon, className }: MetricsCardProps) {
  return (
    <div className={cn("rounded-xl border border-border bg-card/30 p-4", className)}>
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground/60">{label}</span>
        {icon && <span className="text-base text-muted-foreground/40">{icon}</span>}
      </div>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-2xl font-bold text-foreground">{value}</span>
        {change && (
          <span className={cn("text-xs font-medium", change.positive ? "text-emerald-400" : "text-red-400")}>
            {change.positive ? "+" : ""}{change.value}%
          </span>
        )}
      </div>
    </div>
  );
}
