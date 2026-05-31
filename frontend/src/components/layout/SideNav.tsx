"use client";

import { cn } from "@/lib/utils";
import { useUIStore } from "@/store/ui-store";
import type { SectionName } from "@/types/api";

interface NavItem {
  id: SectionName;
  icon: string;
  label: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: "pipeline", icon: "⊞", label: "Content Pipeline" },
  { id: "history", icon: "≡", label: "Pipeline History" },
  { id: "projects", icon: "📁", label: "Projects" },
  { id: "analytics", icon: "⬡", label: "Analytics" },
  { id: "workspace", icon: "◰", label: "Workspace" },
  { id: "settings", icon: "⚙", label: "Settings" },
  { id: "agents", icon: "◈", label: "Agent Monitor" },
  { id: "orchestration", icon: "⇄", label: "Orchestration" },
  { id: "metrics", icon: "◆", label: "System Metrics" },
];

export function SideNav() {
  const section = useUIStore((s) => s.section);
  const setSection = useUIStore((s) => s.setSection);
  const sidebarOpen = useUIStore((s) => s.sidebarOpen);

  return (
    <aside
      className={cn(
        "flex flex-shrink-0 flex-col border-r border-border bg-card/40 backdrop-blur-2xl transition-all duration-300",
        sidebarOpen ? "w-sidebar" : "w-[64px]",
      )}
    >
      <div className="flex h-header items-center gap-3 border-b border-border px-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500 text-sm font-bold text-white shadow-lg shadow-emerald-500/20 shrink-0">
          A
        </div>
        {sidebarOpen && (
          <div className="overflow-hidden">
            <div className="text-sm font-semibold text-foreground whitespace-nowrap">ACIP</div>
            <div className="text-[10px] text-muted-foreground whitespace-nowrap">Content Intelligence</div>
          </div>
        )}
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto p-2">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            onClick={() => setSection(item.id)}
            className={cn(
              "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
              section === item.id
                ? "bg-emerald-500/10 text-emerald-400 shadow-sm"
                : "text-muted-foreground hover:bg-white/5 hover:text-foreground",
              !sidebarOpen && "justify-center px-2",
            )}
            title={!sidebarOpen ? item.label : undefined}
          >
            <span className="w-5 text-center text-base shrink-0">{item.icon}</span>
            {sidebarOpen && <span className="whitespace-nowrap">{item.label}</span>}
          </button>
        ))}
      </nav>

      <div className="border-t border-border p-3">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
          {sidebarOpen && <span className="text-xs text-muted-foreground whitespace-nowrap">System Online</span>}
        </div>
      </div>
    </aside>
  );
}
