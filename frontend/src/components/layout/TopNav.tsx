"use client";

import { cn } from "@/lib/utils";
import { useUIStore } from "@/store/ui-store";
import { usePipelineStore } from "@/store/pipeline-store";

interface TopNavProps {
  onNewPipeline?: () => void;
  children?: React.ReactNode;
}

export function TopNav({ onNewPipeline, children }: TopNavProps) {
  const openModal = useUIStore((s) => s.openModal);
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);
  const toggleTheme = useUIStore((s) => s.toggleTheme);
  const theme = useUIStore((s) => s.theme);
  const currentId = usePipelineStore((s) => s.currentId);
  const status = usePipelineStore((s) => s.status);

  const handleNew = onNewPipeline ?? (() => openModal("pipeline-create"));

  return (
    <header className="flex h-header flex-shrink-0 items-center gap-4 border-b border-border bg-card/30 px-4 backdrop-blur-2xl">
      <button
        onClick={toggleSidebar}
        className="rounded-lg p-2 text-muted-foreground hover:bg-white/5 hover:text-foreground transition-colors"
        aria-label="Toggle sidebar"
      >
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <button
        onClick={handleNew}
        className="rounded-lg bg-emerald-500 px-4 py-1.5 text-xs font-medium text-white shadow-lg shadow-emerald-500/20 hover:bg-emerald-600 hover:shadow-emerald-500/40 transition-all"
      >
        + New Pipeline
      </button>

      {children}

      <div className="flex items-center gap-2 ml-auto">
        {currentId && status && (
          <div className="flex items-center gap-2 rounded-lg border border-border bg-black/20 px-3 py-1.5">
            <span
              className={cn(
                "h-2 w-2 rounded-full",
                status.status === "completed" ? "bg-emerald-400" :
                status.status === "running" ? "bg-blue-400 animate-pulse-soft" :
                "bg-slate-500",
              )}
            />
            <span className="text-xs text-muted-foreground capitalize">{status.status}</span>
          </div>
        )}

        <button
          onClick={toggleTheme}
          className="rounded-lg p-2 text-muted-foreground hover:bg-white/5 hover:text-foreground transition-colors"
          aria-label="Toggle theme"
        >
          {theme === "dark" ? (
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          ) : (
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          )}
        </button>
      </div>
    </header>
  );
}
