"use client";

import dynamic from "next/dynamic";
import { useUIStore } from "@/store/ui-store";

const SideNav = dynamic(() => import("@/components/layout/SideNav").then((m) => ({ default: m.SideNav })), { ssr: false });
const TopNav = dynamic(() => import("@/components/layout/TopNav").then((m) => ({ default: m.TopNav })), { ssr: false });
const Footer = dynamic(() => import("@/components/layout/Footer").then((m) => ({ default: m.Footer })), { ssr: false });

const SECTION_LABELS: Record<string, string> = {
  commandCenter: "Command Center",
  pipeline: "Content Pipeline",
  history: "Pipeline History",
  analytics: "Analytics",
  workspace: "Workspace",
  settings: "Settings",
  agents: "Agent Monitor",
  orchestration: "Orchestration",
  metrics: "System Metrics",
  skills: "Skills Engine",
  operations: "Operations",
  projects: "Projects",
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const section = useUIStore((s) => s.section);
  const mobileMenuOpen = useUIStore((s) => s.mobileMenuOpen);

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <SideNav />
      <div className="flex flex-1 flex-col min-w-0 relative">
        <TopNav>
          <div className="hidden sm:flex items-center gap-2 min-w-0">
            <span className="text-xs text-muted-foreground/50">/</span>
            <span className="text-xs font-semibold text-foreground truncate">{SECTION_LABELS[section] ?? section}</span>
          </div>
        </TopNav>
        <main className="flex-1 overflow-y-auto p-4 md:p-6 page-enter">
          {children}
        </main>
        <div className="hidden md:block">
          <Footer />
        </div>
      </div>
    </div>
  );
}