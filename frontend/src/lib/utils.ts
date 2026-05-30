import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: unknown[]) {
  return twMerge(clsx(inputs));
}

export function statusColor(status: string): string {
  switch (status) {
    case "success":
    case "completed":
      return "text-emerald-400";
    case "running":
    case "created":
      return "text-blue-400";
    case "failed":
      return "text-red-400";
    case "pending":
      return "text-slate-500";
    case "skipped":
    case "cancelled":
      return "text-amber-400";
    default:
      return "text-slate-400";
  }
}

export function statusBg(status: string): string {
  switch (status) {
    case "success":
    case "completed":
      return "bg-emerald-500/10 border-emerald-500/20";
    case "running":
    case "created":
      return "bg-blue-500/10 border-blue-500/20";
    case "failed":
      return "bg-red-500/10 border-red-500/20";
    case "pending":
      return "bg-slate-500/10 border-slate-500/20";
    case "skipped":
      return "bg-amber-500/10 border-amber-500/20";
    default:
      return "bg-slate-500/10 border-slate-500/20";
  }
}

export function statusDot(status: string, animate = false): string {
  switch (status) {
    case "success":
    case "completed":
      return "bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.5)]";
    case "running":
    case "created":
      return `bg-blue-400 shadow-[0_0_8px_rgba(59,130,246,0.5)]${animate ? " animate-pulse-soft" : ""}`;
    case "failed":
      return "bg-red-400 shadow-[0_0_8px_rgba(239,68,68,0.5)]";
    case "pending":
      return "bg-slate-600";
    case "skipped":
      return "bg-amber-400";
    default:
      return "bg-slate-500";
  }
}

export function formatDuration(ms: number): string {
  if (!ms || ms <= 0) return "-";
  if (ms < 1000) return `${ms.toFixed(0)}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  const m = Math.floor(ms / 60000);
  const s = Math.round((ms % 60000) / 1000);
  return `${m}m ${s}s`;
}

export function timeAgo(dateStr: string): string {
  const d = new Date(dateStr);
  const diff = Date.now() - d.getTime();
  const s = Math.floor(diff / 1000);
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return d.toLocaleDateString();
}

export function truncate(str: string, len = 80): string {
  if (str.length <= len) return str;
  return str.slice(0, len) + "...";
}
