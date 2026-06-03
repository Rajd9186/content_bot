"use client";

import { useEffect } from "react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/store/ui-store";
import type { SectionName } from "@/types/api";

interface NavItem {
  id: SectionName;
  icon: string;
  label: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: "commandCenter", icon: "◈", label: "Command Center" },
  { id: "pipeline", icon: "⊞", label: "Content Pipeline" },
  { id: "history", icon: "≡", label: "Pipeline History" },
  { id: "projects", icon: "📁", label: "Projects" },
  { id: "analytics", icon: "⬡", label: "Analytics" },
  { id: "workspace", icon: "◰", label: "Workspace" },
  { id: "settings", icon: "⚙", label: "Settings" },
  { id: "agents", icon: "◈", label: "Agent Monitor" },
  { id: "orchestration", icon: "⇄", label: "Orchestration" },
  { id: "metrics", icon: "◆", label: "System Metrics" },
  { id: "skills", icon: "◇", label: "Skills Engine" },
  { id: "operations", icon: "◉", label: "Operations" },
];

export function SideNav() {
  const section = useUIStore((s) => s.section);
  const setSection = useUIStore((s) => s.setSection);
  const sidebarOpen = useUIStore((s) => s.sidebarOpen);
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);
  const mobileMenuOpen = useUIStore((s) => s.mobileMenuOpen);
  const setMobileMenuOpen = useUIStore((s) => s.setMobileMenuOpen);

  const handleNav = (id: SectionName) => {
    setSection(id);
    setMobileMenuOpen(false);
  };

  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => { document.body.style.overflow = ""; };
  }, [mobileMenuOpen]);

  const navContent = (
    <>
      <div className="flex h-header items-center gap-3 border-b border-border px-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-violet-700 text-sm font-bold text-white shadow-lg shadow-violet-500/25 shrink-0">
          A
        </div>
        <div className="overflow-hidden">
          <div className="text-sm font-bold text-foreground whitespace-nowrap tracking-tight">ACIP</div>
          <div className="text-[10px] text-muted-foreground whitespace-nowrap">Content Intelligence</div>
        </div>
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto p-2">
        {NAV_ITEMS.map((item, i) => (
          <button
            key={item.id}
            onClick={() => handleNav(item.id)}
            className={cn(
              "nav-item flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium",
              "transition-all duration-200 ease-smooth",
              section === item.id
                ? "bg-gradient-to-r from-violet-500/10 to-violet-600/5 text-violet-400 shadow-sm border border-violet-500/10"
                : "text-muted-foreground hover:bg-secondary hover:text-foreground border border-transparent",
              !sidebarOpen && "justify-center px-2",
            )}
            style={{ animationDelay: `${i * 30}ms` }}
            title={!sidebarOpen ? item.label : undefined}
          >
            <span className="w-5 text-center text-base leading-none shrink-0">{item.icon}</span>
            {sidebarOpen && <span className="whitespace-nowrap font-medium">{item.label}</span>}
          </button>
        ))}
      </nav>

      <div className="border-t border-border p-3">
        <div className="flex items-center gap-2.5">
          <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.5)] animate-pulse-soft" />
          {sidebarOpen && (
            <div className="flex flex-col">
              <span className="text-xs font-medium text-foreground">System Online</span>
              <span className="text-[10px] text-muted-foreground">All services operational</span>
            </div>
          )}
        </div>
      </div>
    </>
  );

  return (
    <>
      <aside
        className={cn(
          "flex flex-shrink-0 flex-col border-r border-border bg-card/80 backdrop-blur-xl transition-all duration-300 h-full",
          "hidden md:flex",
          sidebarOpen ? "w-sidebar" : "w-[72px]",
        )}
      >
        {navContent}
      </aside>

      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 md:hidden"
          onClick={() => setMobileMenuOpen(false)}
        >
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm animate-fade-in" />
          <aside
            className={cn(
              "relative flex flex-shrink-0 flex-col bg-card/95 backdrop-blur-xl border-r border-border h-full w-[280px] animate-slide-in-left shadow-2xl",
            )}
            onClick={(e) => e.stopPropagation()}
          >
            {navContent}
          </aside>
        </div>
      )}
    </>
  );
}