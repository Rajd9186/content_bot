"use client";

import { cn } from "@/lib/utils";

interface ErrorBoundaryProps {
  error?: string | null;
  onRetry?: () => void;
  className?: string;
}

export function ErrorBoundary({ error, onRetry, className }: ErrorBoundaryProps) {
  if (!error) return null;
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-xl border border-red-500/20 bg-red-500/5 px-6 py-8 text-center",
        className,
      )}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-500/10">
        <svg className="h-6 w-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
      </div>
      <p className="text-sm text-red-300">{error}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="rounded-lg border border-red-500/30 px-4 py-1.5 text-xs font-medium text-red-300 hover:bg-red-500/10 transition-colors"
        >
          Retry
        </button>
      )}
    </div>
  );
}
