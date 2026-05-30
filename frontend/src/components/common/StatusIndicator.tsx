import { cn } from "@/lib/utils";

interface StatusDotProps {
  status: string;
  size?: "sm" | "md";
  pulse?: boolean;
  className?: string;
}

export function StatusIndicatorInstance({ status, size = "md", pulse: forcePulse, className }: StatusDotProps) {
  const sizes = { sm: "h-1.5 w-1.5", md: "h-2 w-2" };

  const colors: Record<string, string> = {
    pending: "bg-slate-500",
    queued: "bg-slate-400",
    running: "bg-blue-400",
    completed: "bg-emerald-400",
    success: "bg-emerald-400",
    failed: "bg-red-400",
    error: "bg-red-400",
    cancelled: "bg-amber-400",
    review: "bg-amber-400",
    idle: "bg-slate-500",
    active: "bg-emerald-400",
    degraded: "bg-amber-400",
    healthy: "bg-emerald-400",
  };

  const shouldPulse = forcePulse ?? (status === "running" || status === "active");

  return (
    <span
      className={cn(
        "inline-block rounded-full",
        sizes[size],
        colors[status] ?? "bg-slate-500",
        shouldPulse && "animate-pulse-soft",
        className,
      )}
    />
  );
}
