import { cn } from "@/lib/utils";

interface StatusDotProps {
  status: string;
  size?: "sm" | "md";
  pulse?: boolean;
  className?: string;
}

const COLORS: Record<string, { bg: string; shadow: string }> = {
  pending: { bg: "bg-slate-400", shadow: "shadow-none" },
  queued: { bg: "bg-slate-400", shadow: "shadow-none" },
  running: { bg: "bg-blue-400", shadow: "shadow-blue-400/50" },
  completed: { bg: "bg-emerald-400", shadow: "shadow-emerald-400/50" },
  success: { bg: "bg-emerald-400", shadow: "shadow-emerald-400/50" },
  failed: { bg: "bg-red-400", shadow: "shadow-red-400/50" },
  error: { bg: "bg-red-400", shadow: "shadow-red-400/50" },
  cancelled: { bg: "bg-amber-400", shadow: "shadow-amber-400/50" },
  review: { bg: "bg-amber-400", shadow: "shadow-amber-400/50" },
  idle: { bg: "bg-slate-400", shadow: "shadow-none" },
  active: { bg: "bg-emerald-400", shadow: "shadow-emerald-400/50" },
  degraded: { bg: "bg-amber-400", shadow: "shadow-amber-400/50" },
  healthy: { bg: "bg-emerald-400", shadow: "shadow-emerald-400/50" },
};

export function StatusIndicatorInstance({ status, size = "md", pulse: forcePulse, className }: StatusDotProps) {
  const sizes = { sm: "h-1.5 w-1.5", md: "h-2 w-2" };
  const color = COLORS[status] ?? { bg: "bg-slate-400", shadow: "shadow-none" };
  const shouldPulse = forcePulse ?? (status === "running" || status === "active");

  return (
    <span
      className={cn(
        "inline-block rounded-full shadow-sm",
        sizes[size],
        color.bg,
        color.shadow,
        shouldPulse && "animate-pulse-soft",
        className,
      )}
    />
  );
}