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
  const mobileMenuOpen = useUIStore((s) => s.mobileMenuOpen);
  const setMobileMenuOpen = useUIStore((s) => s.setMobileMenuOpen);
  const currentId = usePipelineStore((s) => s.currentId);
  const status = usePipelineStore((s) => s.status);

  const handleNew = onNewPipeline ?? (() => openModal("pipeline-create"));

  return (
    <header className="flex h-header flex-shrink-0 items-center gap-3 border-b border-border bg-background/80 backdrop-blur-xl px-4 md:px-6">
      <button
        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        className="md:hidden rounded-xl p-2 text-muted-foreground hover:bg-secondary hover:text-foreground transition-all btn-press"
        aria-label="Toggle menu"
      >
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          {mobileMenuOpen ? (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          ) : (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          )}
        </svg>
      </button>

      <button
        onClick={toggleSidebar}
        className="hidden md:flex rounded-xl p-2 text-muted-foreground hover:bg-secondary hover:text-foreground transition-all btn-press"
        aria-label="Toggle sidebar"
      >
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <button
        onClick={handleNew}
        className="rounded-xl bg-gradient-to-r from-violet-600 to-violet-700 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-violet-500/20 hover:from-violet-500 hover:to-violet-600 hover:shadow-violet-500/30 active:scale-[0.97] transition-all duration-200"
      >
        <span className="hidden sm:inline">+ New Pipeline</span>
        <span className="sm:hidden">+ New</span>
      </button>

      <div className="flex-1 min-w-0">
        {children}
      </div>

      <div className="flex items-center gap-2">
        {currentId && status && (
          <div className="hidden sm:flex items-center gap-2 rounded-xl border border-border bg-secondary/50 px-3 py-1.5">
            <span
              className={cn(
                "h-2 w-2 rounded-full",
                status.status === "completed" ? "bg-emerald-400" :
                status.status === "running" ? "bg-blue-400 animate-pulse-soft" :
                "bg-slate-400",
              )}
            />
            <span className="text-xs text-muted-foreground capitalize font-medium">{status.status}</span>
          </div>
        )}

        <button
          onClick={toggleTheme}
          className="rounded-xl p-2 text-muted-foreground hover:bg-secondary hover:text-foreground transition-all btn-press"
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