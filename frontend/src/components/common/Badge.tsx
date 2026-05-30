import { cn } from "@/lib/utils";

interface BadgeProps {
  variant?: "emerald" | "blue" | "amber" | "red" | "slate" | "outline";
  children: React.ReactNode;
  className?: string;
  dot?: boolean;
  pulse?: boolean;
}

export function Badge({ variant = "slate", children, className, dot, pulse }: BadgeProps) {
  const variants = {
    emerald: "bg-emerald-500/10 text-emerald-300 border-emerald-500/20",
    blue: "bg-blue-500/10 text-blue-300 border-blue-500/20",
    amber: "bg-amber-500/10 text-amber-300 border-amber-500/20",
    red: "bg-red-500/10 text-red-300 border-red-500/20",
    slate: "bg-slate-500/10 text-slate-300 border-slate-500/20",
    outline: "bg-transparent text-muted-foreground border-border",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-medium",
        variants[variant],
        className,
      )}
    >
      {(dot || pulse) && (
        <span
          className={cn(
            "h-1.5 w-1.5 rounded-full",
            pulse ? "animate-pulse-soft" : "",
            variant === "emerald" ? "bg-emerald-400" :
            variant === "blue" ? "bg-blue-400" :
            variant === "amber" ? "bg-amber-400" :
            variant === "red" ? "bg-red-400" :
            "bg-slate-400",
          )}
        />
      )}
      {children}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { variant: BadgeProps["variant"]; label: string }> = {
    pending: { variant: "slate", label: "Pending" },
    running: { variant: "blue", label: "Running" },
    completed: { variant: "emerald", label: "Completed" },
    failed: { variant: "red", label: "Failed" },
    cancelled: { variant: "amber", label: "Cancelled" },
    review: { variant: "amber", label: "Review" },
  };
  const m = map[status] ?? map.pending;
  return <Badge variant={m.variant} dot pulse={status === "running"}>{m.label}</Badge>;
}
